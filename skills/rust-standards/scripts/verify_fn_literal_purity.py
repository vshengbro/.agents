#!/usr/bin/env python3
"""Verify §1.3c literal purity for `fn.rs` / `impl.rs` — byte and char literals.

A byte or multi-byte-char literal in a function body is program data
written where a named `const` belongs: `b"<!--"`, `b'<'`, `b'\x00'`. The
rule targets that, not ordinary string literals (which carry their own
exemption set) and not `let`/`const`/`static` bindings, which are exactly
where a one-shot local is fine.

Skipped: doc comments (`///`, `//!`, `/** */`), raw strings, and
`#[cfg(test)]` / `#[test]` blocks.

Extracted from an inline `python3 - <<'PY'` heredoc in
audit_rust_standards.py. A heredoc needs a temp file, which restricted
sandboxes refuse to create, so the check never actually ran.

Usage:  python3 verify_fn_literal_purity.py [ROOT]
Exit 0 clean, 1 violations found, 2 usage error.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAW_OPEN = re.compile(r'r(#+)"')
BYTE_STRING = re.compile(r'b"([^"\n]{2,})"')
BYTE_CHAR = re.compile(r"b'([^'\n])'")
SKIP_PREFIX = re.compile(r"^\s*(let|const|static)\s+")
# Pure escapes carry no semantic token, so they are not worth extracting.
TRIVIAL = {" ", "\t", "\n", "\r", "\0"}


def _git(root: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=root,
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout if r.returncode == 0 else ""


def changed_files(root: Path) -> list[str]:
    out = _git(root, "diff", "--name-only", "origin/master", "HEAD", "--", "*.rs")
    keep = []
    for f in out.strip().split("\n"):
        if not f or "/tests/" in f or "/target/" in f:
            continue
        if f.endswith(("/mod.rs", "/const.rs", "/static.rs", "/lib.rs", "/main.rs")):
            continue
        if f.endswith(("/fn.rs", "/impl.rs")):
            keep.append(f)
    return keep


def audit_file(root: Path, rel: str) -> list[str]:
    path = root / rel
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    hits: list[str] = []
    in_raw = False
    in_block_doc = False
    in_test = False
    raw_delim = ""
    for number, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("///") or stripped.startswith("//!"):
            continue
        if not in_block_doc and stripped.startswith("/**"):
            in_block_doc = True
            if "*/" in line[line.index("/**") + 3:]:
                in_block_doc = False
            continue
        if in_block_doc:
            if "*/" in line:
                in_block_doc = False
            continue
        if in_raw:
            if raw_delim in line:
                in_raw = False
                raw_delim = ""
            continue
        raw = RAW_OPEN.search(line)
        if raw:
            raw_delim = '"' + raw.group(1)
            if raw_delim not in line[raw.end():]:
                in_raw = True
            continue
        if "#[cfg(test)]" in line or "#[cfg(all(test" in line or "#[test]" in line:
            in_test = True
        if in_test:
            if stripped.startswith("}") and line.count("}") > line.count("{"):
                in_test = False
            continue
        if SKIP_PREFIX.match(line):
            continue
        byte_strings = BYTE_STRING.findall(line)
        byte_chars = BYTE_CHAR.findall(line)
        if not byte_strings and not byte_chars:
            continue
        if "as_bytes()" in line and re.search(r'\.as_bytes\(\)\s*\.last\(\)', line):
            continue
        meaningful = any(c not in TRIVIAL for c in byte_chars)
        if byte_strings or meaningful:
            hits.append(f"{rel}:{number}: {line.strip()[:120]}")
    return hits


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    files = changed_files(root)
    hits: list[str] = []
    for rel in files:
        hits.extend(audit_file(root, rel))
    for h in hits:
        print(h)
    print(f"\n=== fn-literal-purity (R1.3c): {len(hits)} violation(s) "
          f"in {len(files)} file(s) ===")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
