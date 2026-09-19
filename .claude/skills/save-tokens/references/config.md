# Configuration levers

Setup changes that lower token burn permanently. Apply the ones that fit the
project; do not bulk-apply all of them.

**Before editing any settings file: read it first.** These files usually already
contain hooks, MCP servers, plugins, and a status line. Merge into the existing
JSON with a read-modify-write (the snippets below are fragments, not whole
files). Overwriting someone's settings to add one key is a bad trade.

## 1. Deny vendor directories

The single biggest accidental burn is an agent reading or searching a dependency
tree. Block it at the permission layer so it cannot happen by accident.

In `.claude/settings.json` (project) or `~/.claude/settings.json` (global):

```json
{
  "permissions": {
    "deny": [
      "Read(./node_modules/**)",
      "Read(./.git/**)",
      "Read(./dist/**)",
      "Read(./build/**)",
      "Read(./.next/**)",
      "Read(./venv/**)",
      "Read(./target/**)",
      "Read(./**/*.lock)",
      "Read(./**/package-lock.json)"
    ]
  }
}
```

Project-level `.claude/settings.json` is the better home: the deny list is a
property of the repo layout, not of the machine.

## 2. Split CLAUDE.md into nested files

A monolithic CLAUDE.md loads on every turn, in every directory, for every task.
Frontend rules should not ride along on a database migration.

```
project-root/
├── CLAUDE.md            # conventions and architecture that apply everywhere
├── frontend/CLAUDE.md   # UI and styling rules, loaded for frontend work
└── backend/CLAUDE.md    # API and database rules, loaded for backend work
```

Keep the root file short: what the project is, how to run it, the handful of
conventions that genuinely apply repo-wide. Everything scoped goes down a level.

## 3. Move procedures into skills

CLAUDE.md is always-on context. A skill is loaded only when invoked. Anything
procedural (a migration runbook, a release checklist, a debugging workflow)
belongs in a skill, not in the always-on file.

Rule of thumb: if it reads like "here is how to do X when you need to do X", it
is a skill. If it reads like "this project always does Y", it is CLAUDE.md.

## 4. Status line with context percentage

Seeing context fill is what makes compacting timely instead of forced.
`settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "/absolute/path/to/statusline.sh"
  }
}
```

The script receives session JSON on stdin and prints one line, for example
`[Context: 38% | 76k/200k]`. If a status line is already configured, extend that
script rather than replacing it. `/statusline` sets one up interactively.

## 5. Compact earlier

Auto-compact at 80-90% means many turns carry a near-full window. Triggering
nearer 55-60% keeps the average turn cheaper. Configure it in `/config` if the
installed version exposes the threshold; if it does not, get the same effect by
compacting manually and early, with an explicit focus instruction.

Either way, a handover file beats a compact. Compaction keeps a lossy summary of
everything; a handover keeps a precise record of what matters.

## 6. Cap headless runs

Non-interactive runs have no human to stop a loop. Bound them:

```bash
claude -p "Fix lint errors across src/" --max-turns 5
```

Also bound the scope in the prompt itself (one directory, one rule, one file
type). An unbounded headless agent on a large repo is the worst case for burn.

## 7. Right-size the model and effort

- Plan on the strongest model, then execute on a cheaper one. Architecture and
  hard debugging earn deep reasoning; renaming and formatting do not.
- Delegate mechanical bulk work to Sonnet subagents and keep the expensive model
  reviewing rather than typing.
- If effort level is pinned high globally, it applies to trivial tasks too.
  Check `effortLevel` in settings and lower it for routine work, raising it per
  task when it is actually needed.
