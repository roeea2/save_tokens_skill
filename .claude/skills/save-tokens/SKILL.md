---
name: save-tokens
description: >-
  Cut Claude Code token and context burn, and write a handover file before a
  session is cleared. Use when the user mentions tokens, context window, cost,
  usage limits, running out of context, compacting, or clearing; before any
  /clear, /compact, or session restart; when scoping a large or file-heavy task;
  or when asked to audit what burned tokens, tune settings for efficiency, or
  hand work off to a fresh session. Its read/search/edit discipline applies on
  any long task, whether or not the user asked about tokens.
---

# Save tokens

Two jobs:

1. **Operating discipline** - how to work so the context window fills slowly.
2. **Handover before clear** - never let a session be cleared or compacted
   without a written handover file. This is the hard rule of this skill.

The skill itself is built to be cheap: this file is the whole runtime contract.
Load a reference only when the task actually calls for it.

## 1. Default discipline (apply without being asked)

These are the rules Claude controls directly. They cost nothing to follow.

| Rule | Do this |
|---|---|
| Grep before read | Locate the symbol, error string, or signature first (`grep -rn "handlePaymentWebhook" ./src`), then open only the matching files. Never open a file to find out whether it is relevant. |
| Read with offsets | On any file over ~300 lines, read the slice (`sed -n '120,160p'`, or Read with offset/limit). Whole-file reads are a last resort, not a default. |
| Edit diffs, not rewrites | Patch with targeted search/replace. Never regenerate a whole file to change a few lines. A 400-line rewrite to fix one null check is the single most common avoidable burn. |
| Cap bash output | Pipe through `tail -n 25`, `head -n 50`, `wc -l`, or `--tail 20`. Never stream a full test run, build log, `ls -R`, or `git log` without a limit. |
| No polling loops | Never `while ! curl ...; do sleep 1; done`. Check once, or inspect the specific log (`docker logs api --tail 20`). Repeated identical failures are pure waste. |
| Skip vendor trees | Never read or search `node_modules/`, `venv/`, `target/`, `dist/`, `.git/`, lockfiles, `build/`. Exclude them in every grep and find. |
| Plan before edit | On any multi-file change, state the files and the rationale first, get a nod, then write. Hallucinated edits cost twice: the write and the rollback. |
| Scale effort down | Reserve deep reasoning for architecture and hard debugging. Formatting, renaming, boilerplate, and JSON reshaping get minimum effort. |
| Delegate bulk work | Hand high-volume mechanical execution (boilerplate, test writing, wide file sweeps) to a Sonnet subagent. Keep the expensive model on the plan, not the typing. |
| Resume, do not re-explain | Continuing paused work? Reference the commit hash, checkpoint, or handover file. Do not repost background the session can read. |
| Answer, do not tour | Do not re-read files already in context, re-derive settled facts, or narrate options you will not pursue. |

If a task is about to pull in something big (a large file, a wide search, a full
log), say what it will cost and propose the narrow version first.

## 2. Handover before clear (mandatory)

**Any time a session is about to be cleared, compacted, restarted, or handed
off, write a handover file first.** Triggers: the user types or mentions
`/clear` or `/compact`, says the context is full, says they are starting fresh,
ends a work block, or asks for a handoff. If a clear is imminent and no handover
exists, write it and say so before anything else.

Procedure:

1. Run `scripts/handover.sh` (optionally with a target directory) to collect
   objective state: git branch, status, recent commits, changed files.
2. Read `references/handover.md` for the template and the rules about what to
   keep and what to drop.
3. Write `HANDOVER.md` in the project root (or append a dated section if one
   exists). Keep it under roughly 150 lines: decisions, current state, next
   step, traps. No transcript, no logs, no rehashed file contents.
4. Tell the user the file is written and that the next session should start with
   "Read HANDOVER.md and continue from Next step."

A handover file is worth far more than a compacted transcript: it is the only
artifact that survives a clear intact, and it lets the next session start at a
few thousand tokens instead of inheriting a bloated summary.

## 3. Session hygiene

- **Clear between tasks.** One feature or bug per session. After it ships:
  handover, then `/clear`. Do not carry a finished task's context into the next.
- **Compact with focus.** Never bare `/compact`. Name what survives:
  `/compact Keep the schema changes and the failing auth tests; drop all
  terminal logs.`
- **Check usage before a big push.** `/usage` for burn rate and remaining
  limits, then size the task to fit.
- **Resume by reference.** `claude --resume`, or point at the commit or
  handover file rather than re-pasting context.

## 4. Configuration work

When the user wants the setup itself tuned (nested CLAUDE.md, permission denies
for vendor directories, auto-compact threshold, status line context percentage,
headless `--max-turns`, moving procedures out of CLAUDE.md into skills), read
`references/config.md` and apply from there. It carries the exact settings.json
shapes and warns about the read-modify-write on an existing config.

## 5. Auditing what actually burned

`python3 scripts/token_audit.py` reads the local session logs under
`~/.claude/projects/` and ranks sessions, tools, and individual tool results by
context cost.

```bash
python3 scripts/token_audit.py                 # all projects, recent sessions
python3 scripts/token_audit.py --project .     # this project only
python3 scripts/token_audit.py --top 15        # widen the offender list
```

Run it before prescribing changes. The top offenders are usually specific and
fixable (one unbounded log, one vendor-tree grep, one whole-file read) rather
than a general need to "be more efficient".

## Full rule reference

`references/playbook.md` holds all 20 rules with explanations and examples. Read
it only when the user wants the complete list, is deciding which levers to pull,
or asks about a rule not covered above.
