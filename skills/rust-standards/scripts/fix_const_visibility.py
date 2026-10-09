#!/usr/bin/env python3
"""Reduce `pub const` / `pub static` items with zero external readers to
`pub(crate)` (§18, constants clause).

Companion fixer for verify_const_visibility.py: it reuses the verifier's
repo-wide analysis, then rewrites the visibility prefix on each flagged
declaration line. Unwired items (zero readers anywhere) are NOT touched -
keep-vs-delete is a human decision.

Safety contract (rust-standards fixer rules):

  * default is --dry-run: report what would change, write NOTHING
  * --write applies, then re-verifies and prints the remaining count
  * idempotent: a second --write run reports 0 changed
  * a declaration line whose text drifted from the analysis is skipped,
    never guessed at

Usage:
    python3 fix_const_visibility.py ROOT [--write]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from verify_const_visibility import PUB_CONST_RE, analyze

FINDING_RE = re.compile(r"^(?P<rel>.+):(?P<lineno>\d+): 'pub (?P<kind>const|static) (?P<name>[A-Za-z_]\w*)'")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="repo root to scan")
    parser.add_argument("--write", action="store_true", help="apply fixes (default: dry-run)")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    violations, _unwired = analyze(root)
    planned: dict[Path, list[tuple[int, str]]] = {}
    for finding in violations:
        m = FINDING_RE.match(finding)
        if not m:
            continue
        planned.setdefault(root / m.group("rel"), []).append(
            (int(m.group("lineno")), m.group("name"))
        )
    changed: list[str] = []
    skipped = 0
    for path, sites in sorted(planned.items()):
        try:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        except (OSError, UnicodeDecodeError):
            skipped += len(sites)
            continue
        touched = False
        for lineno, name in sites:
            idx = lineno - 1
            if idx >= len(lines):
                skipped += 1
                continue
            m = PUB_CONST_RE.match(lines[idx])
            if not m or m.group("name") != name:
                skipped += 1
                continue
            lines[idx] = re.sub(r"^pub\s+", "pub(crate) ", lines[idx], count=1)
            touched = True
        if touched:
            changed.append(str(path.relative_to(root)))
            if args.write:
                path.write_text("".join(lines), encoding="utf-8")
    mode = "reduced" if args.write else "would-reduce"
    for rel in changed:
        print(f"  {mode}: {rel}")
    total = sum(1 for _ in violations)
    print(
        f"=== const-visibility-fixer: {total} item(s) {mode} in {len(changed)} file(s), "
        f"{skipped} skipped (drifted) ==="
    )
    if args.write and changed:
        remaining, _ = analyze(root)
        print(f"=== const-visibility-fixer: re-verify {len(remaining)} violation(s) remaining ===")
        return 1 if remaining else 0
    return 1 if (changed and not args.write) else 0


if __name__ == "__main__":
    sys.exit(main())
