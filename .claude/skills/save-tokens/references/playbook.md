# The 20 rules

Full reference. The ones Claude applies on its own are marked **auto**; the rest
are setup or user actions.

## Session hygiene

### 1. Clear between tasks
Reset context once a feature, fix, or sub-task is done, so finished work stops
inflating every later prompt. Write the handover first.
```
/clear
```

### 2. Compact with focus
A generic auto-summary keeps a little of everything, including logs. Name what
survives.
```
/compact Keep only the database schema changes and the failing auth test cases; drop all terminal logs.
```

### 19. Resume, do not re-explain **auto**
Continuing paused work means pointing at the checkpoint, not restating it.
```
Resume from commit 4f2a1b. Proceed directly to Step 3 of the plan.
```

### 6. Check usage first
Know the burn rate and remaining limit before launching something large, then
size the task to fit.
```
/usage
```

### 20. Run a usage audit
Find which sessions, tools, and results actually consumed the context instead of
guessing.
```bash
python3 scripts/token_audit.py --top 15
```

## Context hygiene

### 3. Split CLAUDE.md into nested files
Per-scope rules load only in their scope. See `config.md` section 2.

### 10. Skills over CLAUDE.md
Procedural workflows load on demand as skills instead of riding along on every
turn. See `config.md` section 3.

### 9. Deny vendor directories
Block `node_modules/`, `.git/`, `dist/`, `venv/`, lockfiles at the permission
layer. Tens of thousands of tokens, one accidental read. See `config.md`
section 1.

### 7. Shrink the auto-compact window
Compress nearer 55-60% than 80-90% so intermediate turns are not carrying a
near-full window. See `config.md` section 5.

### 15. Status line context percentage
A live `[Context: 38% | 76k/200k]` indicator turns compacting into a decision
instead of an interruption. See `config.md` section 4.

## Tool discipline

### 13. Grep before you read **auto**
Find the exact location first, then open only what matched.
```bash
grep -rn "handlePaymentWebhook" ./src
```

### 12. Read with offsets **auto**
Read the slice, not the file.
```bash
sed -n '120,160p' src/services/auth.ts
```

### 14. Edit diffs, not rewrites **auto**
Patch the lines that change. Regenerating a whole file to fix one line is the
most common avoidable burn there is.
```
Patch line 45 of server.py to handle the null case. Do not regenerate the file.
```

### 11. Cap bash output **auto**
Truncate anything that can grow: test runs, builds, logs, directory trees.
```bash
npm test 2>&1 | tail -n 25
```

### 8. Kill polling loops **auto**
Tight retry and poll loops burn context on identical failure text.
```bash
# Wasteful
while ! curl -s http://localhost:3000; do sleep 1; done

# Better
docker logs api-container --tail 20
```

### 17. Plan mode before edit **auto**
Confirm the file list and rationale before writing. A wrong edit costs the write
and the rollback.
```
Outline the files you plan to modify and why. Do not write code yet.
```

## Model and run economics

### 4. Plan on the strongest model
Use the deepest reasoning where it compounds: architecture, task breakdown, hard
debugging.
```
Create an architectural execution plan for migrating the session store to Redis.
```

### 5. Execute on Sonnet subagents
Delegate boilerplate, test writing, and wide file inspection to faster, cheaper
workers.
```
Use a Sonnet subagent to write unit tests for the endpoints in the plan.
```

### 18. Stop maximum effort everywhere
Extended thinking on a formatting task is pure cost.
```
Thinking budget: low. Convert this JSON schema to snake_case.
```

### 16. Set max turns in headless runs
Bound autonomous loops that have no human to stop them.
```bash
claude -p "Fix lint errors across src/" --max-turns 5
```

## The rule that is not in the list

Write a handover file before every clear. Without it, the choice at the end of a
session is between paying to carry stale context or losing the decisions that
made the work correct. See `handover.md`.
