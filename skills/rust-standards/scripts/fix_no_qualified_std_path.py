#!/usr/bin/env python3
"""
Auto-fixer for verify_no_qualified_std_path.py (R6.3 std, audit check 47).

A sub-file must not consume a `std::`-rooted qualified path; the import lives
in the crate root (`src/lib.rs`) or, for a tests/ tree, the outermost
`tests/mod.rs`, and reaches sub-files through the `use super::*;` glob chain
(§92). This fixer performs exactly that transformation:

    std::fs::create_dir_all(p)   ->  create_dir_all(p)   + root `use std::fs::create_dir_all;`
    std::time::Duration::from_secs(x) -> Duration::from_secs(x) + root `use std::time::Duration;`

Transformation rules:

  * import path = up to and including the FIRST uppercase-leading segment
    (`std::net::IpAddr::V4` imports `std::net::IpAddr`, tail `IpAddr::V4`);
    when no segment is uppercase the whole path is a module fn and is imported
    whole (`std::thread::sleep` -> tail `sleep`).
  * leaf-name collisions within one root fall back to the module-namespace
    form: two different paths ending in `Error` keep `std::error::Error` bare
    and demote the other to `use std::io;` + `io::Error` at the use site
    (§6.5 — shortest distinguishing namespace at the use site; `as` renames
    are banned).
  * prelude-hostile leaves (`Result` — `std::thread::Result` has a different
    arity from the prelude's two-parameter `Result`) always take the module
    form (`use std::thread;` + `thread::Result<()>`), never the bare name.

Replacement is string-span aware per pitfalls §93 lesson 1: the whole file is
scanned once, string/char literals are blanked to spaces (length-preserving),
and only matches OUTSIDE literals are rewritten, at their exact offsets.

Insertion at the root follows §6.1: new private `use` lines join the trailing
private-use group (created at EOF when absent). src/lib.rs and tests/mod.rs
share that shape — tests/mod.rs is the integration-test crate root and ends
in `use <crate>::*;`, not `use super::*;`.

This fixer is NOT registered in rust_pre_commit.py AUTO_FIXERS: it rewrites
imports, and a genuinely new collision (a descendant glob chain already
carrying the leaf) must be resolved from rustc's coordinates, not guessed.
Run it deliberately:

    python3 <path>/fix_no_qualified_std_path.py <repo>            # dry-run plan
    python3 <path>/fix_no_qualified_std_path.py <repo> --write    # apply
    cargo check --workspace --all-targets                         # then prove it
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Keep these regexes in sync with verify_no_qualified_std_path.py — the fixer
# must see exactly the set of hits the verifier reports, no more.
QUALIFIED = re.compile(r"(?<![\w:])std::[a-z_]\w*(::\w+)+")
USE_LINE = re.compile(r"^\s*(pub(\([^)]*\))?\s+)?use\b")
TRAIT_FMT_RETURN = re.compile(
    r"fn\s+fmt\s*\(\s*&\s*self\s*,\s*\w+\s*:\s*&\s*mut\s+[\w:]*Formatter\s*<'_\s*>\s*\)"
    r"\s*->\s*std::fmt::Result"
)
TOP_LEVEL = {"lib.rs", "main.rs", "build.rs"}
SKIP_DIRS = {"target", ".git"}
# Char literals match EXACTLY one character or escape: a `*` quantifier pairs
# a lifetime apostrophe (`'a`, `'_`) with the next quote far away and blanks
# real code in between (pitfalls §93 lesson 1's span rule, measured 27 of 203
# hits silently dropped on ctares before this was tightened, 2026-10-09).
# Raw strings need a backreference: content runs until a quote followed by the
# SAME number of `#` (`r#"{"a":1}"#`); without it the closing inner quote
# opens a phantom string that swallows the following real code lines.
STRING_LITERAL = re.compile(
    r'b?r(#*)"(?:.*?)"\1'  # raw string / raw byte string
    r"|b?\"(?:\\.|[^\"\\])*\""  # normal / byte string
    r"|b?'(?:\\.|[^'\\])'",  # char / byte literal: exactly one char or escape
    re.S,
)

# Leaves that must never be imported bare because the prelude owns a different
# generic of the same name (arity or semantics differ).
PRELUDE_HOSTILE = {"std::thread::Result"}


def split_path(path: str) -> tuple[str, str]:
    """(import_path, use-site tail) for one matched std:: path."""
    segments = path.split("::")[1:]
    for i, seg in enumerate(segments):
        if seg[0].isupper():
            return "std::" + "::".join(segments[: i + 1]), "::".join(segments[i:])
    return path, segments[-1]


def crate_root_of(root: Path, path: Path) -> Path:
    """Nearest ancestor directory containing Cargo.toml."""
    for parent in path.parents:
        if (parent / "Cargo.toml").is_file() and parent != path:
            return parent
    return root


def import_root_for(root: Path, path: Path) -> Path:
    """The file that receives the import: src/lib.rs, or tests/mod.rs."""
    crate = crate_root_of(root, path)
    rel = path.relative_to(crate)
    if rel.parts[0] == "tests":
        return crate / "tests" / "mod.rs"
    return crate / "src" / "lib.rs"


def _blank_macro_token_bodies(blanked: str) -> str:
    """Blank `macro_rules!` / `quote!` / `quote_spanned!` bodies.

    Runs on text whose string/char literals are ALREADY blanked, so a `quote!`
    mentioned inside a string is invisible here, and braces inside macro-body
    strings no longer exist to disturb the balanced scan. The tokens inside
    these bodies are emitted into the downstream crate at expansion — they are
    exempt for the same reason string literals are.
    """
    spans: list[tuple[int, int]] = []
    pairs = {"(": ")", "{": "}", "[": "]"}
    for m in re.finditer(r"(?:macro_rules!\s*\w+|quote!|quote_spanned!)\s*([({\[])", blanked):
        stack: list[str] = []
        i = m.end(1) - 1
        while i < len(blanked):
            c = blanked[i]
            if c in pairs:
                stack.append(pairs[c])
            elif stack and c == stack[-1]:
                stack.pop()
                if not stack:
                    spans.append((m.end(1) - 1, i + 1))
                    break
            elif c in ")}]":
                break  # malformed: bail without a span
            i += 1
    if not spans:
        return blanked
    chars = list(blanked)
    for s, e in spans:
        for i in range(s, e):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def find_hits(path: Path) -> list[tuple[int, int, int, str]]:
    """(start, end, line_number, matched_path) for consumed std:: paths,
    string literals already excluded. Offsets are into the ORIGINAL text."""
    text = path.read_text(errors="ignore")
    # Newline-preserving blanking: multi-line strings keep their `\n` so the
    # per-line filters below stay aligned with the original line numbers AND
    # all offsets remain 1:1 with the original text.
    blanked = STRING_LITERAL.sub(lambda s: re.sub(r"[^\n]", " ", s.group(0)), text)
    blanked = _blank_macro_token_bodies(blanked)
    hits: list[tuple[int, int, int, str]] = []
    offset = 0
    for number, (line_orig, line_blank) in enumerate(
        zip(text.splitlines(keepends=True), blanked.splitlines(keepends=True)), 1
    ):
        if USE_LINE.match(line_orig):
            offset += len(line_orig)
            continue
        code = line_blank.split("//", 1)[0]
        if TRAIT_FMT_RETURN.search(code):
            offset += len(line_orig)
            continue
        for m in QUALIFIED.finditer(code):
            hits.append((offset + m.start(), offset + m.end(), number, m.group(0)))
        offset += len(line_orig)
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()

    files = [
        p
        for p in sorted(root.rglob("*.rs"))
        if not any(part in SKIP_DIRS for part in p.parts) and p.name not in TOP_LEVEL
    ]
    # file -> hits; root -> {import_path}; rewrite map: file -> [(start, end, tail)]
    per_file: dict[Path, list[tuple[int, int, int, str]]] = {}
    for path in files:
        hits = find_hits(path)
        if hits:
            per_file[path] = hits
    if not per_file:
        print("Nothing to do (no qualified std:: path consumed in sub-files)")
        return 0

    # Resolve the (import, tail) per root, applying collision fallbacks.
    # Pass 1: claim every leaf per root; when two different std paths want the
    # same leaf, the lexicographically smaller import path stays bare
    # (`std::error::Error` beats `std::io::Error`) and the loser is demoted to
    # the module-namespace form (§6.5 shortest distinguishing namespace).
    # root -> leaf -> set of candidate import paths
    claims: dict[Path, dict[str, set[str]]] = {}
    for path, hits in per_file.items():
        iroot = import_root_for(root, path)
        leaves = claims.setdefault(iroot, {})
        for _s, _e, _ln, matched in hits:
            import_path, _tail = split_path(matched)
            if matched in PRELUDE_HOSTILE:
                import_path = matched.rsplit("::", 1)[0]
            leaves.setdefault(import_path.split("::")[-1], set()).add(import_path)

    winners: dict[Path, dict[str, str]] = {}
    for iroot, leaves in claims.items():
        winners[iroot] = {leaf: sorted(paths)[0] for leaf, paths in leaves.items()}

    # Pass 2: final plan per hit.
    planned: dict[tuple[Path, int, int], tuple[str, str]] = {}
    for path, hits in per_file.items():
        iroot = import_root_for(root, path)
        for start, end, _ln, matched in hits:
            import_path, tail = split_path(matched)
            if matched in PRELUDE_HOSTILE:
                # std::thread::Result -> root `use std::thread;`, site
                # `thread::Result<()>`: the prelude's Result has a different
                # arity, so the bare name is never safe.
                import_path = matched.rsplit("::", 1)[0]
                tail = f"{import_path.split('::')[-1]}::{matched.split('::')[-1]}"
            leaf = import_path.split("::")[-1]
            if winners[iroot][leaf] != import_path:
                # Lost the leaf: demote to module form, e.g. `use std::io;`
                # at the root and `io::Error` at the use site.
                import_path = matched.rsplit("::", 1)[0]
                tail = matched[len("std::"):]
            planned[(path, start, end)] = (import_path, tail)

    root_imports: dict[Path, set[str]] = {}
    for (path, _s, _e), (import_path, _tail) in planned.items():
        root_imports.setdefault(import_root_for(root, path), set()).add(import_path)

    # Report / apply sub-file rewrites (bottom-up so offsets stay valid).
    rewritten = 0
    for path, hits in sorted(per_file.items()):
        text = path.read_text(errors="ignore")
        for start, end, _ln, matched in sorted(hits, key=lambda h: h[0], reverse=True):
            _imp, tail = planned[(path, start, end)]
            if not args.write:
                continue
            text = text[:start] + tail + text[end:]
            rewritten += 1
        if args.write:
            path.write_text(text)

    # Report / apply root imports.
    imports_added = 0
    for iroot, imps in sorted(root_imports.items()):
        new_lines = sorted({f"use {imp};" for imp in imps})
        if not args.write:
            for line in new_lines:
                print(f"{iroot}: + {line}")
            continue
        text = iroot.read_text()
        existing = set(re.findall(r"^use\s+([^;]+);", text, re.M))
        new_lines = [l for l in new_lines if l[4:-1] not in existing]
        if not new_lines:
            continue
        lines = text.splitlines()
        # Every root (src/lib.rs or tests/mod.rs) gets the same treatment:
        # extend the trailing single-line private-use group, else append a
        # new group at EOF. tests/mod.rs files are the root of the
        # integration-test crate and end in `use <crate>::*;`, not
        # `use super::*;` — there is no mod.rs-specific shape to honour.
        insert_at = None
        for i in range(len(lines) - 1, -1, -1):
            s = lines[i].strip()
            if s.startswith("use ") and s.endswith(";"):
                insert_at = i + 1
                break
            if s == "};":
                # end of a multi-line use block; keep scanning upward
                continue
            if s == "":
                continue
            break
        if insert_at is None:
            if lines and lines[-1].strip() != "":
                lines.append("")
            lines.extend(new_lines)
        else:
            lines[insert_at:insert_at] = new_lines
        iroot.write_text("\n".join(lines) + "\n")
        imports_added += len(new_lines)

    mode = "applied" if args.write else "dry-run"
    total = sum(len(h) for h in per_file.values())
    print(
        f"=== qualified-std-path-fixer ({mode}): {total} site(s) across "
        f"{len(per_file)} file(s), {imports_added if args.write else sum(len(v) for v in root_imports.values())} "
        f"root import(s) in {len(root_imports)} root(s) ==="
    )
    if args.write:
        verify = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("verify_no_qualified_std_path.py")), str(root)],
            capture_output=True,
            text=True,
        )
        remaining = [l for l in verify.stdout.splitlines() if l.startswith(" ")]
        print(f"=== re-verify: {len(remaining)} violation(s) remaining ===")
        if remaining:
            print("\n".join(remaining[:10]))
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
