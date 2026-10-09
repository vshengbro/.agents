#!/usr/bin/env python3
"""§2.5 — no comments in TOML files or mod.rs files (absolute, 2026-10-09).

Rule (2026-10-09 user directive, tightening §2.5 to an absolute bar):

    - every `*.toml` file in the repo carries ZERO `#` comments
    - every `mod.rs` in the repo carries ZERO comments of any form:
      `//`, `///`, `//!`, `/* ... */`, and trailing comments after code

The rule text existed since 2026-09-12 ("mod.rs 不加任何注释; Cargo.toml 不加
任何注释") but enforcement was partial: audit check 5 was diff-scoped and its
regex `^\\s*//[^/!]` caught only plain `//` (not `///`, not `//!`, not block
comments, not trailing), and no check covered TOML at all. This verifier is
the comprehensive, tree-wide owner of the rule. Audit check 5 is DEPRECATED
in favour of check 51 (this script).

String awareness (false-positive guards):

  - TOML: a `#` inside a basic / literal / multi-line string is DATA, not a
    comment (`description = "a # b"`, `colour = "#ff0000"`). The scanner is a
    four-state machine (normal / basic / literal / multi-line) so only a `#`
    in normal state is reported.
  - Rust: `//` inside a string or char literal (`"http://x"`, `'/'`) is not a
    comment. Raw strings `r"..."` / `r#"..."#` and nested block comments are
    handled; lifetimes (`'a`) are not char literals.

Scope:

  - `audit_one(path)` decides from the file NAME: `mod.rs` -> rust scan,
    `*.toml` -> toml scan, anything else -> []. The gate's baseline suffixes
    (`.head-baseline.rs` / `.head-baseline.toml`) are stripped first, so the
    staged-vs-HEAD diff works for both file kinds.
  - `main()` scans the whole repo: `find` for `*.toml` + `mod.rs`, skipping
    `target/` / `.git/` / `node_modules/` / `.cargo/`, then drops
    git-ignored paths (a `.gitignore`d file is not part of the project —
    crate-cli's `tmp/` scratch crates are covered HERE, not by name, so a
    repo checked out under /tmp still scans correctly).

Output contract: one violation per comment span, then a summary line
beginning `=== no-toml-mod-comments:`. Exit 0 = compliant, 1 = violations,
2 = usage error.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# A comment span: (start_offset, end_offset, start_line). end_offset is the
# first offset NOT part of the comment (newline excluded for line comments).
Span = tuple[int, int, int]

BASELINE_SUFFIXES = (".head-baseline.rs", ".head-baseline.toml")

# Deliberately NO "tmp" here: an earlier draft excluded `*/tmp/*` (crate-cli
# scratch crates), which silently blanked the verifier for ANY repo checked
# out under a path containing a `tmp` component — including /tmp itself.
# crate-cli's `tmp/` scratch is git-ignored, so `_drop_git_ignored` already
# covers it by mechanism rather than by name.
SKIP_PARTS = {"target", ".git", "node_modules", ".cargo"}


# ---------------------------------------------------------------------------
# TOML scanner
# ---------------------------------------------------------------------------

def find_toml_comments(text: str) -> list[Span]:
    """Return spans of every `#` comment outside TOML strings."""
    spans: list[Span] = []
    i = 0
    line = 1
    n = len(text)
    state = "normal"  # normal | basic | literal | ml_basic | ml_literal
    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
            # single-line strings cannot span a newline (TOML spec); an
            # unterminated one is invalid TOML, and whatever follows the
            # newline is scanned as normal text — a `#` there IS reported
            # (better a false positive on broken TOML than a hidden comment)
            if state in ("basic", "literal"):
                state = "normal"
            continue
        if state == "normal":
            if ch == "#":
                start = i
                while i < n and text[i] != "\n":
                    i += 1
                spans.append((start, i, line))
                continue
            if ch == '"':
                if text.startswith('"""', i):
                    state = "ml_basic"
                    i += 3
                    continue
                state = "basic"
                i += 1
                continue
            if ch == "'":
                if text.startswith("'''", i):
                    state = "ml_literal"
                    i += 3
                    continue
                state = "literal"
                i += 1
                continue
            i += 1
            continue
        if state == "basic":
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                state = "normal"
            i += 1
            continue
        if state == "literal":
            if ch == "'":
                state = "normal"
            i += 1
            continue
        # multi-line forms: the first run of >= 3 quote chars closes
        if state == "ml_basic":
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                run = 1
                while i + run < n and text[i + run] == '"':
                    run += 1
                if run >= 3:
                    state = "normal"
                    i += 3
                    continue
                i += run
                continue
            i += 1
            continue
        if state == "ml_literal":
            if ch == "'":
                run = 1
                while i + run < n and text[i + run] == "'":
                    run += 1
                if run >= 3:
                    state = "normal"
                    i += 3
                    continue
                i += run
                continue
            i += 1
            continue
    return spans


# ---------------------------------------------------------------------------
# Rust scanner
# ---------------------------------------------------------------------------

def find_rust_comments(text: str) -> list[Span]:
    """Return spans of every Rust comment outside string / char literals."""
    spans: list[Span] = []
    i = 0
    line = 1
    n = len(text)
    state = "normal"  # normal | string | raw | line | block
    raw_terminator = ""
    block_depth = 0
    block_start = 0
    block_line = 1
    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
            if state == "line":
                state = "normal"
            continue
        if state == "line":
            i += 1
            continue
        if state == "block":
            if ch == "/" and i + 1 < n and text[i + 1] == "*":
                block_depth += 1
                i += 2
                continue
            if ch == "*" and i + 1 < n and text[i + 1] == "/":
                block_depth -= 1
                i += 2
                if block_depth == 0:
                    spans.append((block_start, i, block_line))
                    state = "normal"
                continue
            i += 1
            continue
        if state == "string":
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                state = "normal"
            i += 1
            continue
        if state == "raw":
            if ch == '"' and text.startswith(raw_terminator, i):
                i += len(raw_terminator)
                state = "normal"
                continue
            i += 1
            continue
        # state == normal
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            start = i
            while i < n and text[i] != "\n":
                i += 1
            spans.append((start, i, line))
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            block_start = i
            block_line = line
            block_depth = 1
            state = "block"
            i += 2
            continue
        if ch == '"':
            state = "string"
            i += 1
            continue
        if ch == "r" and i + 1 < n and text[i + 1] in "#\"":
            # possible raw string: r"..." / r#"..."# / r##"..."## ...
            cursor = i + 1
            hashes = 0
            while cursor < n and text[cursor] == "#":
                hashes += 1
                cursor += 1
            if cursor < n and text[cursor] == '"':
                raw_terminator = '"' + "#" * hashes
                state = "raw"
                i = cursor + 1
                continue
            i += 1
            continue
        if ch == "'":
            # char literal ('a', '\n', '\'', '\u{1F600}') or lifetime ('a).
            cursor = i + 1
            if cursor < n and text[cursor] == "\\":
                cursor += 1
                if cursor < n and text[cursor] == "u":
                    # '\u{...}' form
                    close = text.find("}'", cursor)
                    if close != -1:
                        i = close + 2
                        continue
                elif cursor + 1 < n and text[cursor + 1] == "'":
                    i = cursor + 2
                    continue
            elif cursor + 1 < n and text[cursor + 1] == "'":
                i = cursor + 2
                continue
            # lifetime or label — not a literal, keep scanning normally
            i += 1
            continue
        i += 1
    return spans


# ---------------------------------------------------------------------------
# Scope + audit_one (gate contract)
# ---------------------------------------------------------------------------

def scope_of(path: Path) -> str | None:
    """'rust' for mod.rs, 'toml' for *.toml, None otherwise.

    Gate baselines (`<name>.head-baseline.rs` / `<name>.head-baseline.toml`)
    resolve to the original name first, so HEAD-vs-worktree diffs work.
    """
    name = path.name
    for suffix in BASELINE_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    if name == "mod.rs":
        return "rust"
    if name.endswith(".toml"):
        return "toml"
    return None


def audit_one(path: Path) -> list[str]:
    scope = scope_of(path)
    if scope is None:
        return []
    parts = {part.lower() for part in path.parts}
    if parts & SKIP_PARTS:
        return []
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []
    spans = (
        find_rust_comments(text) if scope == "rust" else find_toml_comments(text)
    )
    label = "mod.rs" if scope == "rust" else "TOML file"
    violations: list[str] = []
    for start, _end, lineno in spans:
        preview = text[start : start + 60].split("\n", 1)[0]
        violations.append(
            f"{path}:{lineno}: comment in a {label} is forbidden (§2.5); "
            f"strip it (no //, ///, //!, /* */ or # comments): {preview!r}"
        )
    return violations


# ---------------------------------------------------------------------------
# Repo scan (CLI contract)
# ---------------------------------------------------------------------------

def list_target_files(root: Path) -> list[Path]:
    result = subprocess.run(
        [
            "find",
            str(root),
            "(",
            "-name",
            "*.toml",
            "-o",
            "-name",
            "mod.rs",
            ")",
            "-not",
            "-path",
            "*/target/*",
            "-not",
            "-path",
            "*/.git/*",
            "-not",
            "-path",
            "*/node_modules/*",
            "-not",
            "-path",
            "*/.cargo/*",
        ],
        capture_output=True,
        text=True,
    )
    candidates = [
        Path(line) for line in result.stdout.splitlines() if line.strip()
    ]
    return _drop_git_ignored(candidates, root)


def _drop_git_ignored(paths: list[Path], root: Path) -> list[Path]:
    """A path listed in .gitignore is not part of the project: findings on
    it could never land in any commit (e.g. a local `.cargo/config.toml`)."""
    if not paths or not (root / ".git").exists():
        return paths
    try:
        rels = [str(p.relative_to(root)) for p in paths]
    except ValueError:
        return paths
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "--stdin"],
            input="\n".join(rels) + "\n",
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return paths
    if result.returncode not in (0, 1):
        return paths
    ignored = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return [
        p for p, rel in zip(paths, rels) if rel not in ignored
    ]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    all_violations: list[str] = []
    file_count = 0
    for path in list_target_files(root):
        found = audit_one(path)
        if found:
            file_count += 1
            all_violations.extend(found)
    for violation in all_violations:
        print(violation)
    print(
        f"\n=== no-toml-mod-comments: {len(all_violations)} violation(s) "
        f"in {file_count} file(s) ==="
    )
    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
