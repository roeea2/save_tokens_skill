#!/usr/bin/env bash
# Install the save-tokens skill into a project or into the global Claude Code
# skills directory.
#
#   ./install.sh                 # into the current project (./.claude/skills)
#   ./install.sh /path/to/repo   # into another project
#   ./install.sh --global        # into ~/.claude/skills (all projects)
#   ./install.sh --force         # overwrite an existing install
#
# Copies files only. It never edits settings, hooks, or anything else.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.claude/skills/save-tokens"
FORCE=0
TARGET=""

for arg in "$@"; do
  case "$arg" in
    --global) TARGET="$HOME/.claude/skills" ;;
    --force)  FORCE=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *)        TARGET="${arg%/}/.claude/skills" ;;
  esac
done
TARGET="${TARGET:-$PWD/.claude/skills}"

[ -f "$SRC/SKILL.md" ] || { echo "Source skill not found at $SRC" >&2; exit 1; }

DEST="$TARGET/save-tokens"
if [ -e "$DEST" ] && [ "$FORCE" -eq 0 ]; then
  echo "Already installed at $DEST" >&2
  echo "Re-run with --force to overwrite." >&2
  exit 1
fi

mkdir -p "$TARGET"
rm -rf "$DEST"
cp -R "$SRC" "$DEST"
chmod +x "$DEST/scripts/"*.sh "$DEST/scripts/"*.py 2>/dev/null || true

echo "Installed: $DEST"
echo
echo "Check it:"
echo "  python3 \"$DEST/scripts/token_audit.py\" --project . --top 5"
echo
echo "Then start Claude Code in the project and ask for a token audit, or a"
echo "handover before you clear."
