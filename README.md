```
 ____                                _      ___
|  _ \     ___     ___     ___      / \    |_ _|
| |_) |   / _ \   / _ \   / _ \    / _ \    | |
|  _ <   | (_) | |  __/  |  __/   / ___ \   | |
|_| \_\   \___/   \___|   \___|  /_/   \_\ |___|
```

# save_tokens_skill

A project-scoped Claude Code skill that cuts token and context burn, and that
refuses to let a session be cleared without leaving a handover file behind.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The problem

Two things quietly drain a Claude Code plan:

1. **Context you never meant to load.** One whole-file read, one unbounded test
   log, one grep through `node_modules/`, and the window is half gone before the
   work starts. Everything after that turn pays for it again.
2. **Context you throw away.** `/clear` recovers the window but destroys the
   decisions, dead ends, and half-finished state that made the work correct. So
   people avoid clearing, carry a bloated session for hours, and pay for stale
   history on every turn.

This skill fixes both: a working discipline that keeps the window filling
slowly, and a handover protocol that makes clearing cheap and safe.

## What it does

**1. Operating discipline, applied without being asked.** Grep before read, read
by line range, patch instead of rewrite, cap shell output, skip vendor trees,
plan before editing, delegate bulk work, scale effort to the task.

**2. A mandatory handover before any clear.** Whenever a `/clear`, `/compact`,
or restart is coming, the skill writes `HANDOVER.md` first: goal, state,
decisions and the reasons behind them, the exact next step, and the traps
already hit. The next session starts from a few thousand tokens instead of
inheriting a lossy summary.

**3. A real audit, not a guess.** `token_audit.py` reads the local session
transcripts under `~/.claude/projects/` and ranks sessions, tools, and
individual tool results by what they actually cost.

```
TOOL RESULT VOLUME (what entered the context, est. tokens)
tool                     calls   result bytes   ~tokens
Bash                      2131           2.3M    580.3k
Edit                        99          18.9k      4.7k

HEAVIEST INDIVIDUAL RESULTS
  ~  7.1k tok  Bash         npm test
  ~  3.8k tok  Read         src/services/billing/reconciler.ts

WHAT TO FIX
  - 4 single result(s) over ~10k tokens: bound those commands or read
    narrower slices.
```

**4. Config levers, with the exact snippets.** Permission denies for dependency
trees, nested `CLAUDE.md` files, moving procedures out of always-on context into
skills, status line context percentage, earlier compaction, bounded headless
runs.

## Install

The skill is project-scoped by design: it lives in the repo, it travels with the
repo, and it costs nothing in projects that do not use it.

```bash
# into an existing project
git clone https://github.com/<owner>/save_tokens_skill.git /tmp/sts
mkdir -p .claude/skills
cp -r /tmp/sts/.claude/skills/save-tokens .claude/skills/
```

Or clone this repo and work inside it directly. Claude Code picks up
`.claude/skills/*/SKILL.md` automatically.

Verify:

```bash
ls .claude/skills/save-tokens/SKILL.md
python3 .claude/skills/save-tokens/scripts/token_audit.py --project . --top 5
```

To make it global instead, copy the same folder to `~/.claude/skills/`. Project
scope is recommended: token discipline is usually a property of a repo's size
and layout.

## Use

The skill triggers on its own when tokens, context, cost, clearing, or
compacting come up, and when a task is about to pull in something large. You can
also call it directly:

```
/save-tokens
```

Typical asks:

| Ask | What happens |
|---|---|
| "Write a handover, I am clearing." | `handover.sh` collects git state, `HANDOVER.md` gets written from session context |
| "What burned my tokens today?" | `token_audit.py --days 1`, ranked offenders, specific fixes |
| "Set this repo up to stop wasting context." | Permission denies, nested CLAUDE.md, status line, compaction threshold |
| "Give me the full list." | All 20 rules with examples from `references/playbook.md` |

## The handover file

The artifact that makes clearing safe. Five sections, capped at about 150 lines,
no transcript and no logs:

```markdown
# Handover - <project> - <date>

## Goal
## State           # done / in flight / not started
## Key decisions   # and why, so they are not relitigated
## Files that matter
## Next step       # one concrete action
## Traps           # failures already hit, dead ends already explored
## Verify          # the command that proves the work is good
## Resume from     # commit and branch
```

Next session:

```
Read HANDOVER.md and continue from Next step.
```

## The 20 rules

| # | Rule | Where |
|---|---|---|
| 1 | Clear between tasks | session hygiene |
| 2 | Compact with focus | session hygiene |
| 3 | Split CLAUDE.md into nested files | `references/config.md` |
| 4 | Plan on the strongest model | model economics |
| 5 | Execute on Sonnet subagents | model economics |
| 6 | Check usage before a big push | session hygiene |
| 7 | Shrink the auto-compact window | `references/config.md` |
| 8 | Kill polling loops | tool discipline |
| 9 | Deny vendor directories | `references/config.md` |
| 10 | Skills over CLAUDE.md | `references/config.md` |
| 11 | Cap bash output | tool discipline |
| 12 | Read with offsets | tool discipline |
| 13 | Grep before you read | tool discipline |
| 14 | Edit diffs, not rewrites | tool discipline |
| 15 | Status line context percentage | `references/config.md` |
| 16 | Set max turns in headless runs | `references/config.md` |
| 17 | Plan mode before edit | tool discipline |
| 18 | Stop maximum effort everywhere | model economics |
| 19 | Resume, do not re-explain | session hygiene |
| 20 | Run a usage audit | `scripts/token_audit.py` |

Plus the rule that is not on the list: write a handover before every clear.

## Layout

```
.claude/skills/save-tokens/
├── SKILL.md                  # the runtime contract, loaded on invoke
├── references/
│   ├── handover.md           # handover protocol and template
│   ├── config.md             # settings.json snippets and setup levers
│   └── playbook.md           # all 20 rules with examples
└── scripts/
    ├── token_audit.py        # rank sessions, tools, results by cost
    └── handover.sh           # collect git state to seed a handover
```

`SKILL.md` is kept deliberately short. References load only when the task calls
for them, because a skill about saving tokens that costs a fortune to load has
argued against itself.

## Notes

- Both scripts are read-only. `token_audit.py` parses local transcripts and
  sends nothing anywhere; `handover.sh` runs `git` read commands and prints
  markdown.
- Token counts from the audit are estimates for ranking, not billing. Use
  `/usage` for real numbers.
- Tested against Claude Code session logs at `~/.claude/projects/*/*.jsonl`.

## License

MIT. See [LICENSE](LICENSE).
