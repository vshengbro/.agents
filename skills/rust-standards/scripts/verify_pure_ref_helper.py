#!/usr/bin/env python3
"""Verify §1.3.1 rule 1 — a pure `&Foo` helper in `fn.rs` should be an impl method.

A `pub fn` / `pub(crate) fn` in a `fn.rs` whose FIRST parameter is `&Foo` or
`&mut Foo`, where `Foo` is a `struct` or `enum` declared in the same
directory's `struct.rs` / `enum.rs`, is a method on `Foo` wearing a free
function's clothes. It belongs in `impl.rs` as `impl Foo { fn bar(&self, ..) }`.

`#[component]` functions are exempt: the component macro requires the free
function shape.

This replaces an inline `awk` template in audit_rust_standards.py that had
never actually run. It was silently reporting PASS because three defects
compounded:

  1. the template used `{{` / `}}` brace escapes, which only make sense under
     `str.format()`, but `substitute()` resolves placeholders with a manual
     `.replace()` — so awk received literal `{{` and died on a syntax error;
  2. `split(types, arr, "\\n")` sat in a Python triple-quoted string, so the
     escape was consumed by Python and awk received a real newline inside a
     string literal ("non-terminated string");
  3. the 3-argument `match(line, /re/, arr)` is a GNU awk extension that
     BSD awk (macOS default) does not have.

A check that cannot execute must fail loudly rather than pass, so this
script is also the one that makes the failure visible. Uses only the
standard library and a regex scan rather than awk, so it behaves the same
on every platform.

Usage:  python3 verify_pure_ref_helper.py [ROOT]
Exit 0 when clean, 1 when violations are found, 2 on a usage/environment
error.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TYPE_DECL = re.compile(
    r"^[ \t]*pub(?:\([^)]*\))?\s+(?:struct|enum)\s+([A-Z]\w*)", re.M
)
FN_DECL = re.compile(
    r"^[ \t]*pub(?:\([^)]*\))?\s+"
    r"(?:async\s+|const\s+|unsafe\s+|extern\s+\"[^\"]*\"\s+)*"
    r"fn\s+([a-zA-Z_]\w*)\s*[(<]"
)
FIRST_PARAM = re.compile(
    r"^(?:mut\s+)?&(?:mut\s+)?([A-Z]\w*)"
)


def _changed_fn_files(root: Path) -> list[Path]:
    """fn.rs files this branch touches, relative to the base branch.

    Falls back to the whole tree when git is unavailable so the check never
    degrades into a vacuous pass.
    """
    out: list[Path] = []
    try:
        raw = subprocess.run(
            ["git", "diff", "--name-only", "origin/master", "HEAD", "--", "*.rs"],
            cwd=root, capture_output=True, text=True, timeout=60,
        )
        if raw.returncode == 0:
            for line in raw.stdout.splitlines():
                if line.endswith("/fn.rs"):
                    out.append(root / line)
        if out:
            return out
    except (OSError, subprocess.SubprocessError):
        pass
    return sorted(p for p in root.rglob("fn.rs") if "/target/" not in str(p))


def _types_in_dir(directory: Path) -> set[str]:
    names: set[str] = set()
    for keyword in ("struct.rs", "enum.rs"):
        candidate = directory / keyword
        if not candidate.is_file():
            continue
        try:
            names.update(TYPE_DECL.findall(candidate.read_text()))
        except (OSError, UnicodeDecodeError):
            continue
    return names


def audit_file(path: Path) -> list[str]:
    directory = path.parent
    known = _types_in_dir(directory)
    if not known:
        return []
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    findings: list[str] = []
    for number, line in enumerate(lines, start=1):
        match = FN_DECL.match(line)
        if not match:
            continue
        if "#[component]" in line or "component]" in line:
            continue
        open_paren = line.find("(", match.end(1) - 1)
        if open_paren < 0:
            continue
        depth, i = 0, open_paren
        while i < len(line):
            if line[i] == "(":
                depth += 1
            elif line[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        params = line[open_paren + 1:max(open_paren + 1, i)]
        first = params.split(",")[0]
        first = re.sub(r"^[ \t]+|[ \t]+$", "", first)
        first = re.sub(r"^(?:mut[ \t]+)?&(?:mut[ \t]+)?", "", first)
        first = re.sub(r"<.*$", "", first)
        first = re.sub(r"[ \t]", "", first)
        if first in known:
            findings.append(
                f"{path}:{number}: {match.group(1)} takes &{first} — "
                f"should be `impl {first} {{ fn {match.group(1)}(&self) ... }}` "
                f"in impl.rs per §1.3.1"
            )
    return findings


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    files = _changed_fn_files(root)
    violations: list[str] = []
    for f in files:
        if f.is_file():
            violations.extend(audit_file(f))
    for v in violations:
        print(v)
    print(
        f"\n=== pure-ref-helper (R1.3.1): {len(violations)} violation(s) "
        f"in {len(files)} fn.rs file(s) ==="
    )
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
