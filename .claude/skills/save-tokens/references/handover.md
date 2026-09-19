# Handover file protocol

A handover file is the bridge across a `/clear`. Everything else in the session
dies; this file is what the next session reads to pick up work without paying
for the history again.

## When to write one

Write it **before**, never after:

- the user types or mentions `/clear` or `/compact`
- the user says context is full, the session is slow, or they are starting fresh
- a work block ends (feature shipped, bug fixed, day over)
- the user asks for a handoff, a summary to continue from, or a status file
- you are about to run out of room mid-task

If a clear is imminent and no handover exists, write it first and say so.

## What goes in

Optimize for the question "what does a session with zero memory need to keep
going?" That is roughly five things:

1. **Goal** - what is being built or fixed, in one or two sentences.
2. **State** - what is done, what is in flight, what is untouched.
3. **Decisions** - choices already made and the reason, so they are not
   relitigated. This is the highest-value section; a reopened decision costs far
   more than the line it takes to record it.
4. **Next step** - the exact next action, concrete enough to start on.
5. **Traps** - failures already hit, dead ends already explored, commands that
   must be run a specific way, environment quirks.

## What stays out

- transcript, conversation replay, or a narrative of what happened when
- terminal output, build logs, stack traces (record the one-line conclusion)
- file contents the next session can read itself (record the path and line
  range instead)
- anything already in git history, the README, or CLAUDE.md
- speculative future work nobody asked for

Cap it around 150 lines. A handover that needs skimming has already failed.

## Template

```markdown
# Handover - <project> - <YYYY-MM-DD>

## Goal
<One or two sentences: what this work is for.>

## State
- Done: <shipped and verified>
- In flight: <started, not finished, and exactly how far it got>
- Not started: <known remaining scope>

## Key decisions
- <Decision> because <reason>. (do not revisit)
- <Decision> because <reason>.

## Files that matter
- `path/to/file.ts:120-160` - <why this range matters>
- `path/to/other.py` - <role in the change>

## Next step
<The single concrete next action. Command, file, and expected outcome.>

## Traps
- <Failure already hit and the fix or workaround.>
- <Dead end already explored, so it is not tried again.>

## Verify
```bash
<the exact command that proves the work is good>
```

## Resume from
Commit `<sha>` on branch `<branch>`. Start with: "Read HANDOVER.md and continue
from Next step."
```

## Procedure

1. Run `scripts/handover.sh [dir]` for the objective state (branch, status,
   recent commits, changed files, diff stat). Paste its output into the file
   rather than reconstructing git state from memory.
2. Fill the template from the live session context, which is the only place the
   decisions and traps exist.
3. Write `HANDOVER.md` in the project root. If one exists, read it first and
   either update it in place or append a new dated section; never silently
   overwrite work another session left behind.
4. Report: file written, and the one-line instruction for the next session.

## Reusing it

The next session starts with one small read instead of a large inherited
summary:

```
Read HANDOVER.md and continue from Next step.
```

Once that work is done, the handover is updated, not appended to forever. Stale
sections cost tokens on every future read, so prune what is no longer live.
