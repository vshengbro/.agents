#!/usr/bin/env python3
"""
Verify §14.4: no inline `#[cfg(test)] mod tests { ... }` block in a
production file — unit tests live in `<crate>/tests/`.

Why this exists
---------------
`audit_rust_standards.py` check 8 implements this rule as an inline shell
pipeline over `git diff origin/master HEAD`, which means it only ever sees
lines the branch *adds*.  Two consequences:

  1. The pre-commit hook could not run it at all — `staged_file_gate.py`
     drives per-file verifiers through their `audit_one()` entry point, and
     this rule had no such script.  So a rule the audit enforced and the
     hook did not is a rule that does not hold at commit time.
  2. `git diff` sees the DIFF, not the FILE.  A production file that
     already carried an inline test block was never reported, and an
     unrelated edit to that file left the violation in place while the
     check stayed silent.

The sanctioned shape is the `#[path]` include, which points at the
crate's `tests/` tree and therefore keeps the production/test boundary
expressed by file path (§14.1, §14.4):

    #[cfg(test)]
    #[path = "../tests/mod.rs"]
    mod tests;

That form is NOT a violation.  What §14.4 forbids is an inline module
with a BODY in a production file:

    #[cfg(test)]
    mod tests {
        #[test]
        fn ... { }
    }

The distinction is structural: the include form names an external file
(`#[path = ...]` + `mod name;`), the forbidden form declares a module
block (`mod name { ... }`) in the production file itself.

Usage:
    python3 verify_no_inline_cfg_test.py [ROOT]
    python3 verify_no_inline_cfg_test.py [ROOT] --file PATH   # gate mode

Exit 0 if clean, 1 if any violation, 2 on usage error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

EXEMPT_DIRS = {"target", ".cargo", "node_modules"}

# `#[cfg(test)]` (or `#[cfg(all(test, ...))]`) on a line of its own.
CFG_TEST = re.compile(r"^\s*#\s*\[\s*cfg\s*\(\s*(?:all\s*\(\s*)?test\b")

# A module declaration with a BODY: `mod name {` / `mod name { ... }`.
# The include form ends with `;` and is therefore not matched.
# The name may be a raw identifier (`r#fn`), so the `r#` prefix is
# optional as a UNIT — `r#?` would have made the `r` mandatory.
MOD_BLOCK = re.compile(
    r"^\s*(?:pub\s*\(\s*crate\s*\)\s*)?mod\s+(?:r#)?[A-Za-z_][A-Za-z0-9_]*\s*\{"
)

# `#[path = "..."]` — the include form's marker.
PATH_ATTR = re.compile(r"^\s*#\s*\[\s*path\s*=")


def _infer_root(path: Path) -> Path:
    """Nearest ancestor that reads as a crate root.

    The crate root must stay ABOVE any `tests/` component, otherwise a
    test file loses its `tests` segment in `path.relative_to(root)` and
    every test is misread as production code.
    """
    for candidate in [path.parent, *path.parents]:
        if candidate.name == "src":
            return candidate.parent
        if (candidate / "src").is_dir() or (candidate / "Cargo.toml").is_file():
            return candidate
    return path.parent


def _exempt_path(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    if "tests" in parts:
        return True
    return any(part in EXEMPT_DIRS for part in parts)


def _is_comment(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith(("//", "/*", "*", "*/"))


def audit_one(path: Path, root: Path | None = None) -> list[str]:
    """Report inline `#[cfg(test)] mod ... { }` blocks in one file."""
    path = Path(path)
    root = Path(root) if root is not None else _infer_root(path)
    if path.suffix != ".rs":
        return []
    if _exempt_path(path, root):
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    lines = text.split("\n")
    out: list[str] = []
    for index, line in enumerate(lines):
        if _is_comment(line) or not CFG_TEST.match(line):
            continue
        # Look ahead past further attributes: the module declaration may
        # be separated from the cfg attribute by `#[path = ...]` (the
        # sanctioned include form) or by other attributes.
        cursor = index + 1
        saw_path_attr = False
        mod_line: str | None = None
        while cursor < len(lines) and cursor <= index + 8:
            nxt = lines[cursor]
            stripped = nxt.strip()
            if not stripped:
                cursor += 1
                continue
            if stripped.startswith("#["):
                if PATH_ATTR.match(nxt):
                    saw_path_attr = True
                cursor += 1
                continue
            if stripped.startswith("pub ") or stripped.startswith("//"):
                cursor += 1
                continue
            mod_line = nxt
            break
        if mod_line is None:
            continue
        if not MOD_BLOCK.match(mod_line):
            # `mod name;` — a declaration without a body.  Either the
            # sanctioned `#[path]` include, or a module that lives in its
            # own file.  Neither is an inline test block.
            continue
        if saw_path_attr:
            # `#[path = "..."]` + `mod name {` is contradictory; treat the
            # path attribute as authoritative and stay silent.
            continue
        out.append(
            f"{path.relative_to(root) if _relative_ok(path, root) else path}:"
            f"{index + 1}: inline `#[cfg(test)] mod ... {{ }}` — move the test "
            "to <crate>/tests/ (§14.4)"
        )
    return out


def _relative_ok(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("error: usage: verify_no_inline_cfg_test.py [ROOT] [--file PATH]", file=sys.stderr)
        return 2
    if "--file" in args:
        root = Path(args[0]).resolve()
        path = Path(args[args.index("--file") + 1]).resolve()
        found = audit_one(path, root)
        for line in found:
            print(line)
        return 1 if found else 0
    root = Path(args[0]).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    total: list[str] = []
    for path in sorted(root.rglob("*.rs")):
        if any(part in EXEMPT_DIRS for part in path.parts):
            continue
        total += audit_one(path, root)
    for line in total[:20]:
        print(line)
    print(f"=== inline #[cfg(test)] mod tests in production (§14.4): "
          f"{len(total)} violation(s) ===")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
