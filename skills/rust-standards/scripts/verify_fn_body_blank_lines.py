#!/usr/bin/env python3
"""Verify §9.1 item 10 — no blank line inside a function body.

Only blank lines that fall inside a diff hunk are reported, so the check
never blames a PR for pre-existing formatting.

Brace counting runs on a copy of the line with its string literals masked.
A `format!` template that emits JS carries `{{` / `}}` for literal braces;
counting them drove the depth permanently positive in `cli/src/build/fn.rs`
and every later blank line read as being inside that fn's body — 11 phantom
hits on a file with no new blank line anywhere (audit-pitfalls #33).

Extracted from an inline `python3 - <<'PY'` heredoc in
audit_rust_standards.py. A heredoc needs a temp file, which restricted
sandboxes refuse to create, so the check never actually ran.

Usage:  python3 verify_fn_body_blank_lines.py [ROOT]
Exit 0 clean, 1 violations found, 2 usage error.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SIG = re.compile(r'\bfn\b|\basync\s+fn\b|\bconst\s+fn\b|\bunsafe\s+fn\b')
TEST_CTX = re.compile(r'#\[cfg\s*\(test\)\]|#\[test\]|mod\s+tests')
RAW_OPEN = re.compile(r'r(#+)["\']')
HUNK = re.compile(r'^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,(\d+))?\s+@@')


def mask_string_literals(line: str) -> str:
    out = list(line)
    i, n = 0, len(line)
    while i < n:
        if line[i] == '"':
            out[i] = " "
            i += 1
            while i < n:
                if line[i] == "\\":
                    out[i] = " "
                    if i + 1 < n:
                        out[i + 1] = " "
                    i += 2
                    continue
                if line[i] == '"':
                    out[i] = " "
                    i += 1
                    break
                if line[i] != "\n":
                    out[i] = " "
                i += 1
            continue
        if line[i] == "/" and i + 1 < n and line[i + 1] == "/":
            for k in range(i, n):
                out[k] = " "
            break
        i += 1
    return "".join(out)


def _run(root: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=root,
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout if r.returncode == 0 else ""


def _try(root: Path, *args: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(["git", *args], cwd=root,
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return False, ""
    return r.returncode == 0, r.stdout.strip()


def base_ref(root: Path) -> str:
    ok, url = _try(root, "config", "--get", "remote.upstream.url")
    if ok and url:
        ok2, sha = _try(root, "rev-parse", "upstream/master")
        if ok2 and sha:
            ok3, mb = _try(root, "merge-base", "HEAD", sha)
            if ok3 and mb:
                return mb
    return "origin/master"


def hunk_ranges(root: Path, base: str, rel: str) -> list[tuple[int, int]]:
    ranges = []
    for line in _run(root, "diff", base, "HEAD", "-U0", "--", rel).splitlines():
        m = HUNK.match(line)
        if m:
            start = int(m.group(1))
            length = int(m.group(2)) if m.group(2) else 1
            ranges.append((start, start + length - 1))
    return ranges


def audit_file(root: Path, base: str, rel: str) -> list[str]:
    ranges = hunk_ranges(root, base, rel)
    if not ranges:
        return []
    try:
        lines = (root / rel).read_text().split("\n")
    except (OSError, UnicodeDecodeError):
        return []
    stack: list[str] = []
    in_raw = False
    raw_delim = ""
    in_block_doc = False
    hits: list[str] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if in_block_doc:
            if "*/" in stripped:
                in_block_doc = False
            continue
        if stripped.startswith("/**"):
            in_block_doc = True
            if "*/" in stripped[3:]:
                in_block_doc = False
            continue
        if in_raw:
            if '"' + raw_delim in line:
                in_raw = False
            continue
        raw = RAW_OPEN.search(line)
        if raw:
            in_raw = True
            raw_delim = raw.group(1)
            continue
        masked = mask_string_literals(line)
        opens = masked.count("{")
        closes = masked.count("}")
        if opens > 0:
            brace_at = line.find("{")
            pre = line[:brace_at].rstrip() if brace_at >= 0 else ""
            for _ in range(opens):
                if SIG.search(pre):
                    stack.append("fn")
                elif TEST_CTX.search("\n".join(lines[max(0, i - 3):i])):
                    stack.append("test")
                else:
                    stack.append("other")
        elif closes > 0 and stack and stack[-1] == "other":
            back = [l for l in lines[max(0, i - 4):i]
                    if l.strip() and not l.strip().startswith(("//", "#["))]
            if back and SIG.search(back[-1]):
                stack[-1] = "fn"
        if (stripped == "" and stack and stack[-1] == "fn"
                and any(s <= i <= e for s, e in ranges)):
            hits.append(f"{rel}:{i}: blank line in fn body (in diff hunk)")
        while closes > 0 and stack:
            stack.pop()
            closes -= 1
    return hits


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    base = base_ref(root)
    files = [f for f in _run(root, "diff", "--name-only", base, "HEAD", "--", "*.rs").strip().split("\n")
             if f and "/target/" not in f
             and not f.endswith("/lib.rs") and not f.endswith("/build.rs")]
    hits: list[str] = []
    for rel in files:
        hits.extend(audit_file(root, base, rel))
    for h in hits:
        print(h)
    print(f"\n=== fn-body-blank-lines (R9.1): {len(hits)} violation(s) "
          f"in {len(files)} file(s) ===")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
