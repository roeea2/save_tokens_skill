#!/usr/bin/env bash
# Collect objective project state to seed a HANDOVER.md before clearing a session.
#
# Read-only. Prints a markdown block; it never writes or commits anything.
# The agent fills in goal, decisions, next step, and traps from live context.
#
# Usage: ./handover.sh [project-dir]

set -uo pipefail
DIR="${1:-$PWD}"
cd "$DIR" 2>/dev/null || { echo "No such directory: $DIR" >&2; exit 1; }

echo "## Objective state ($(date '+%Y-%m-%d %H:%M'))"
echo
echo "Project: \`$(pwd)\`"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Branch: \`$(git rev-parse --abbrev-ref HEAD)\` at \`$(git rev-parse --short HEAD 2>/dev/null || echo 'no commits')\`"
  echo
  echo "### Recent commits"
  echo '```'
  git log --oneline -8 2>/dev/null || echo "(none)"
  echo '```'
  echo
  echo "### Uncommitted changes"
  echo '```'
  git status --short | head -n 30
  CHANGED=$(git status --porcelain | wc -l | tr -d ' ')
  [ "$CHANGED" -gt 30 ] && echo "... and $((CHANGED - 30)) more"
  echo '```'
  echo
  echo "### Diff size"
  echo '```'
  git diff --stat HEAD 2>/dev/null | tail -n 12 || echo "(no diff)"
  echo '```'
  UP=$(git log --oneline @{u}..HEAD 2>/dev/null | wc -l | tr -d ' ')
  [ "${UP:-0}" -gt 0 ] && echo && echo "Unpushed commits: $UP"
  STASH=$(git stash list 2>/dev/null | wc -l | tr -d ' ')
  [ "${STASH:-0}" -gt 0 ] && echo "Stashes: $STASH"
else
  echo "Not a git repository."
  echo
  echo "### Recently modified files"
  echo '```'
  find . -type f -mtime -2 \
    -not -path '*/node_modules/*' -not -path '*/.git/*' \
    -not -path '*/dist/*' -not -path '*/venv/*' -not -path '*/.next/*' \
    2>/dev/null | head -n 20
  echo '```'
fi

echo
echo "_Fill in Goal, State, Key decisions, Next step, and Traps from session context._"
