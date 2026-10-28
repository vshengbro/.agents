#!/usr/bin/env python3
"""Check that rust-standards markdown carries no historical-debt narration.

The rule set must state only the current, complete rules. Historical debt in
these documents shows up as:

  * dated provenance markers  — ``2026-09-26``
  * iteration labels          — ``第二轮``, ``round 4``, ``third iteration``
  * pull-request references   — ``PR #202``
  * withdrawn rule markers    — ``已废弃``, ``DEPRECATED``, ``REMOVED``
  * superseded-rule catalogues — a table or list of previous rule versions

Inline code spans and fenced blocks are skipped: a checker that names the
markers it rejects must be able to write them down.

Exit codes
  0  no debt markers found
  1  at least one marker found (one line per hit)
  2  the checker itself failed

Usage
  python3 scripts/verify_no_history_debt.py [skill_dir]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")
ROUND = re.compile(
    r"第[一二三四五六七八九十0-9]+轮|round[-\s]?[0-9]+|"
    r"\b(first|second|third|fourth|fifth|sixth|seventh) iteration\b",
    re.IGNORECASE,
)
PR = re.compile(r"\bPR\s*#\d+")
WITHDRAWN = re.compile(r"已废弃|DEPRECATED|REMOVED|已过时|已撤回")
SUPERSEDED_TABLE = re.compile(r"修订历史|版本历史|变更历史")


def scan(path: Path) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        prose = re.sub(r"`[^`]*`", "", line)
        for label, pattern in (
            ("date", DATE),
            ("round", ROUND),
            ("pr", PR),
            ("withdrawn", WITHDRAWN),
            ("superseded-table", SUPERSEDED_TABLE),
        ):
            if pattern.search(prose):
                hits.append((number, label, line.strip()[:160]))
                break
    return hits


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent
    if not root.is_dir():
        print(f"ERROR: not a directory: {root}", file=sys.stderr)
        return 2
    total = 0
    for path in sorted(root.rglob("*.md")):
        for number, label, text in scan(path):
            rel = path.relative_to(root)
            print(f"{rel}:{number}: [{label}] {text}")
            total += 1
    if total:
        print(f"\nFAIL: {total} history-debt marker(s) in {root}")
        return 1
    print(f"OK: no history-debt markers in {root}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
