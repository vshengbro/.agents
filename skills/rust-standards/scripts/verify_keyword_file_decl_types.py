#!/usr/bin/env python3
"""Verify §1.3a — a keyword file may only contain declarations of its own kind.

A `const.rs` may hold `const`/`static`, a `fn.rs` may hold `fn`, and so on.
Finding a `struct` at column 0 of a `fn.rs` (or vice versa) is the violation.

WGSL and GLSL shader source is frequently embedded in raw string literals
(audit-pitfalls §18), and shader code legitimately contains `struct` /
`fn` lines. Anything inside a raw string is therefore skipped, including
the text immediately after a raw string that closes on the same line.

This was an inline `python3 -c` template inside audit_rust_standards.py
and had never run. The outer file stores those templates in Python
triple-quoted strings, so `"\n"` inside them was consumed by the OUTER
parser and turned into a real newline, and `r"r(#+)\""` lost its escape
— the inner script died with a SyntaxError on every invocation. A
standalone file has no such nesting and can be self-tested.

Usage:  python3 verify_keyword_file_decl_types.py [ROOT]
Exit 0 clean, 1 violations found, 2 usage error.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN = {
    "const.rs": r"^(pub |pub\(crate\) )?(fn |struct |enum |trait |impl |type )",
    "static.rs": r"^(pub |pub\(crate\) )?(fn |struct |enum |trait |impl |type )",
    "fn.rs": r"^(pub |pub\(crate\) )?(struct |enum |trait |impl |type )",
    "enum.rs": r"^(pub |pub\(crate\) )?(struct |fn |impl |trait |type )",
    "struct.rs": r"^(pub |pub\(crate\) )?(enum |fn |impl |trait |type )",
    "trait.rs": r"^(pub |pub\(crate\) )?(struct |enum |fn |impl |type )",
    "impl.rs": r"^(pub |pub\(crate\) )?(struct |enum |fn |trait |type )",
    "type.rs": r"^(pub |pub\(crate\) )?(struct |enum |fn |impl |trait )",
}

RAW_OPEN = re.compile(r'r(#+)"')


def changed_rs_files(root: Path) -> list[Path]:
    try:
        raw = subprocess.run(
            ["git", "diff", "--name-only", "origin/master", "HEAD", "--", "*.rs"],
            cwd=root, capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        raw = None
    out: list[Path] = []
    if raw is not None and raw.returncode == 0:
        for line in raw.stdout.splitlines():
            if "/tests/" in line or "/target/" in line:
                continue
            out.append(root / line)
    return [p for p in out if p.is_file()]


def audit_file(path: Path) -> list[str]:
    pattern = FORBIDDEN.get(path.name)
    if pattern is None:
        return []
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    hits: list[str] = []
    in_raw = False
    delim = ""
    for number, line in enumerate(lines, start=1):
        if in_raw:
            marker = '"' + delim
            pos = line.find(marker)
            if pos >= 0:
                in_raw = False
                delim = ""
                after = line[pos + len(marker):]
                if re.match(pattern, after):
                    hits.append(
                        f"{path}:{number}: {after.strip()[:80]} "
                        f"(forbidden in keyword file, after raw-string close)"
                    )
            continue
        raw = RAW_OPEN.search(line)
        if raw:
            delim = raw.group(1)
            marker = '"' + delim
            rest = line[raw.end():]
            close = rest.find(marker)
            if close < 0:
                in_raw = True
            else:
                after = rest[close + len(marker):]
                if re.match(pattern, after):
                    hits.append(
                        f"{path}:{number}: {after.strip()[:80]} "
                        f"(forbidden in keyword file, after raw-string close on same line)"
                    )
            before = line[:raw.start()]
            if re.match(pattern, before):
                hits.append(
                    f"{path}:{number}: {before.strip()[:80]} "
                    f"(forbidden in keyword file, before raw-string)"
                )
            continue
        if re.match(pattern, line):
            hits.append(
                f"{path}:{number}: {line.strip()[:80]} (forbidden in keyword file)"
            )
    return hits


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    files = changed_rs_files(root)
    violations: list[str] = []
    for f in files:
        violations.extend(audit_file(f))
    for v in violations:
        print(v)
    print(f"\n=== keyword-file-decl-types (R1.3a): "
          f"{len(violations)} violation(s) in {len(files)} file(s) ===")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
