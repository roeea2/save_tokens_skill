#!/usr/bin/env python3
"""Audit local Claude Code session logs for what actually burned context.

Reads the JSONL transcripts under ~/.claude/projects/ and ranks sessions,
tools, and individual tool results by cost. Read-only: it never modifies or
uploads anything.

Usage:
    python3 token_audit.py                    # all projects, 10 recent sessions
    python3 token_audit.py --project .        # only the given project directory
    python3 token_audit.py --sessions 20      # widen the session window
    python3 token_audit.py --top 15           # widen the offender lists
    python3 token_audit.py --days 7           # only sessions touched this week
"""

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

CHARS_PER_TOKEN = 4  # rough, good enough for ranking


def project_slug(path: Path) -> str:
    """Claude Code encodes a project path as a slug directory name.

    Separators, spaces, underscores and dots all collapse to a hyphen, so
    /path/to/my_app.v2 becomes -path-to-my-app-v2.
    """
    slug = str(path.resolve()).strip("/")
    for ch in ("/", "\\", " ", "_", "."):
        slug = slug.replace(ch, "-")
    return "-" + slug


def human(n: int) -> str:
    for unit, div in (("B", 1_000_000_000), ("M", 1_000_000), ("k", 1_000)):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return str(n)


def block_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for b in content:
            if isinstance(b, dict):
                out.append(b.get("text") or b.get("content") or "")
            elif isinstance(b, str):
                out.append(b)
        return "".join(x if isinstance(x, str) else json.dumps(x) for x in out)
    if content is None:
        return ""
    return json.dumps(content)


def scan_session(path: Path):
    """Return a dict of stats for one session transcript."""
    usage = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    seen_msgs = set()
    tool_names = {}          # tool_use_id -> (tool, detail)
    tool_calls = defaultdict(int)
    tool_bytes = defaultdict(int)
    results = []             # (bytes, tool, detail)
    turns = 0

    with path.open(errors="ignore") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            rtype = rec.get("type")
            msg = rec.get("message") or {}

            if rtype == "assistant":
                mid = msg.get("id")
                u = msg.get("usage") or {}
                if u and (mid is None or mid not in seen_msgs):
                    if mid:
                        seen_msgs.add(mid)
                    usage["input"] += u.get("input_tokens", 0) or 0
                    usage["cache_write"] += u.get("cache_creation_input_tokens", 0) or 0
                    usage["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
                    usage["output"] += u.get("output_tokens", 0) or 0
                for b in msg.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        tool = b.get("name", "?")
                        inp = b.get("input") or {}
                        detail = (
                            inp.get("command")
                            or inp.get("file_path")
                            or inp.get("pattern")
                            or inp.get("path")
                            or inp.get("skill")
                            or ""
                        )
                        detail = " ".join(str(detail).split())[:90]
                        tool_names[b.get("id")] = (tool, detail)
                        tool_calls[tool] += 1

            elif rtype == "user":
                content = msg.get("content")
                if isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "tool_result":
                            tool, detail = tool_names.get(b.get("tool_use_id"), ("?", ""))
                            size = len(block_text(b.get("content")))
                            tool_bytes[tool] += size
                            results.append((size, tool, detail))
                        elif isinstance(b, dict) and b.get("type") == "text":
                            turns += 1
                elif isinstance(content, str):
                    turns += 1

    return {
        "path": path,
        "session": path.stem,
        "project": path.parent.name,
        "mtime": path.stat().st_mtime,
        "usage": usage,
        "tool_calls": tool_calls,
        "tool_bytes": tool_bytes,
        "results": results,
        "turns": turns,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit Claude Code token burn.")
    ap.add_argument("--project", help="project directory to scope to (default: all)")
    ap.add_argument("--sessions", type=int, default=10, help="sessions to scan (default 10)")
    ap.add_argument("--top", type=int, default=10, help="rows per offender list (default 10)")
    ap.add_argument("--days", type=float, help="only sessions modified in the last N days")
    ap.add_argument("--root", default=str(Path.home() / ".claude" / "projects"))
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"No session logs at {root}", file=sys.stderr)
        return 1

    if args.project:
        target = Path(args.project)
        slug = project_slug(target)
        all_dirs = [d for d in root.iterdir() if d.is_dir()]
        dirs = [d for d in all_dirs if d.name == slug]
        if not dirs:  # case differences between the path and the slug
            dirs = [d for d in all_dirs if d.name.lower() == slug.lower()]
        if not dirs:  # last resort: match on the project folder name alone
            leaf = project_slug(target).rsplit("-", 1)[-1].lower()
            dirs = [d for d in all_dirs if leaf and d.name.lower().endswith("-" + leaf)]
        if not dirs:
            print(f"No logs for project slug {slug}\n"
                  f"Available slugs live in {root}", file=sys.stderr)
            return 1
        files = [f for d in dirs for f in d.glob("*.jsonl")]
    else:
        files = list(root.glob("*/*.jsonl"))

    if args.days:
        cutoff = time.time() - args.days * 86400
        files = [f for f in files if f.stat().st_mtime >= cutoff]

    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    files = files[: args.sessions]
    if not files:
        print("No sessions matched.", file=sys.stderr)
        return 1

    stats = [scan_session(f) for f in files]

    tot_calls = defaultdict(int)
    tot_bytes = defaultdict(int)
    all_results = []
    for s in stats:
        for k, v in s["tool_calls"].items():
            tot_calls[k] += v
        for k, v in s["tool_bytes"].items():
            tot_bytes[k] += v
        all_results.extend(s["results"])

    print()
    print("=" * 78)
    print(f"TOKEN AUDIT  ({len(files)} session(s) under {root})")
    print("=" * 78)

    print("\nSESSIONS (newest first)")
    print(f"{'when':<17}{'project':<34}{'out':>8}{'cache wr':>10}{'cache rd':>10}")
    for s in sorted(stats, key=lambda x: x["mtime"], reverse=True):
        u = s["usage"]
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(s["mtime"]))
        proj = s["project"][:33]
        print(f"{when:<17}{proj:<34}{human(u['output']):>8}"
              f"{human(u['cache_write']):>10}{human(u['cache_read']):>10}")

    grand = defaultdict(int)
    for s in stats:
        for k, v in s["usage"].items():
            grand[k] += v
    billable = grand["input"] + grand["cache_write"] + grand["output"]
    print(f"\nTotals: output {human(grand['output'])} | cache writes "
          f"{human(grand['cache_write'])} | cache reads {human(grand['cache_read'])} "
          f"| new-token spend ~{human(billable)}")
    print("(cache reads are the cheap path; large cache writes mean context kept "
          "changing shape)")

    print(f"\nTOOL RESULT VOLUME (what entered the context, est. tokens)")
    print(f"{'tool':<22}{'calls':>8}{'result bytes':>15}{'~tokens':>10}")
    ranked = sorted(tot_bytes.items(), key=lambda kv: kv[1], reverse=True)[: args.top]
    for tool, nbytes in ranked:
        print(f"{tool:<22}{tot_calls.get(tool, 0):>8}{human(nbytes):>15}"
              f"{human(nbytes // CHARS_PER_TOKEN):>10}")

    print(f"\nHEAVIEST INDIVIDUAL RESULTS")
    all_results.sort(reverse=True)
    for size, tool, detail in all_results[: args.top]:
        print(f"  ~{human(size // CHARS_PER_TOKEN):>6} tok  {tool:<12} {detail}")

    print("\nWHAT TO FIX")
    tips = []
    heaviest = ranked[0][0] if ranked else None
    if heaviest == "Bash":
        tips.append("Bash dominates. Expected if the session runs file work through "
                    "the shell; the fix is per command: pipe through `tail -n 25` / "
                    "`head -n 50`, use `sed -n` ranges, and stop streaming full logs. "
                    "Check the heaviest results below for the real offenders.")
    if heaviest == "Read":
        tips.append("Read dominates: grep for the symbol first, then read only the "
                    "matching line range with offset/limit.")
    if any("node_modules" in d or "/.git/" in d or "dist/" in d
           for _, _, d in all_results[:40]):
        tips.append("Vendor or build directories were read: add permission denies "
                    "(see references/config.md section 1).")
    big = [r for r in all_results if r[0] > 40_000]
    if big:
        tips.append(f"{len(big)} single result(s) over ~10k tokens: bound those "
                    "commands or read narrower slices.")
    if grand["cache_write"] > grand["cache_read"] and grand["cache_write"] > 200_000:
        tips.append("Cache writes exceed reads: context is being reshaped often. "
                    "Clear between tasks (with a handover) instead of accumulating.")
    if not tips:
        tips.append("Nothing pathological in this window. Keep clearing between "
                    "tasks and writing handovers.")
    for t in tips:
        print(f"  - {t}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
