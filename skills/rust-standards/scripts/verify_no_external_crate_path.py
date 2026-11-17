#!/usr/bin/env python3
"""Verify §6.3 / §6.4 — sub-file bodies must not name external crates.

Imports are centralised in `lib.rs` and reach sub-files through
`use super::*;`. A sub-file that says `use tokio::fs;` or annotates
`let x: serde_json::Value` has bypassed that, so both shapes are reported.

External crates are read from the nearest `Cargo.toml` dependency blocks
plus the workspace root's `[workspace.dependencies]`, minus the in-repo
crates and the std/core/alloc trio.

Macro calls (`log::warn!`) and qualified path calls (`tokio::fs::read`)
are deliberately NOT flagged: they resolve through the call site and do
not create a second import, so routing them through lib.rs would be churn
without a rule behind it. Type annotations ARE flagged, because a
`ext::Type` in a signature is exactly the kind of name that should be
`Type` after the re-export.

Extracted from an inline `python3 - <<'PY'` heredoc in
audit_rust_standards.py. A heredoc needs a temp file, which restricted
sandboxes refuse to create, so the check died before it could run; a
standalone file has no such dependency.

Usage:  python3 verify_no_external_crate_path.py [ROOT]
Exit 0 clean, 1 violations found, 2 usage error.
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path

from verify_fn_body_blank_lines import rust_syntax

# In-repo crates and the std trio are never "external".
IGNORE = {
    "std", "core", "alloc", "log",
    "euv", "euv-ui", "euv-cli", "euv-core",
    "euv-engine", "euv-macros", "euv-example", "hyperlane",
}


def _git(root: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=root,
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout if r.returncode == 0 else ""


def changed_sub_files(root: Path) -> list[str]:
    """Changed files that are SUB-FILES (i.e. keyword files).

    The old filter required `"/src/" in f`, which is the cargo default
    layout.  This repo's crates are FLAT (`application/service/...`,
    `plugin/...`), so that test matched nothing and the check reported
    "0 violation(s) in 0 file(s)" forever -- a silent false NEGATIVE: it
    could not catch anything at all while still reporting PASS.

    "Is a sub-file" is decided structurally instead: a .rs file that is
    not a module entry point (mod.rs / lib.rs / main.rs) and is not a
    test.  That works for both layouts.
    """
    out = ""
    has_head = bool(_git(root, "rev-parse", "--verify", "--quiet", "HEAD^{commit}"))
    if has_head and _git(root, "rev-parse", "--verify", "--quiet", "origin/master^{commit}"):
        out += _git(root, "diff", "--name-only", "origin/master", "--", "*.rs")
        out += "\n" + _git(root, "diff", "--cached", "--name-only", "origin/master", "--", "*.rs")
    elif has_head:
        out += "\n" + _git(root, "diff", "--name-only", "HEAD", "--", "*.rs")
        out += "\n" + _git(root, "diff", "--cached", "--name-only", "HEAD", "--", "*.rs")
    else:
        out += "\n" + _git(root, "diff", "--cached", "--name-only", "--", "*.rs")
    out += "\n" + _git(root, "ls-files", "--others", "--exclude-standard", "--", "*.rs")
    return [
        f for f in out.strip().split("\n")
        if f
        and f.endswith(".rs")
        and not f.endswith(("/mod.rs", "/lib.rs", "/main.rs", "/build.rs"))
        and "/tests/" not in f
        and "/target/" not in f
    ]


def load_cargo_toml(path: Path) -> dict:
    """Read actual Cargo tables rather than matching header spelling."""
    try:
        tomllib = importlib.import_module('tomllib')
    except ImportError:
        try:
            tomllib = importlib.import_module('tomli')
        except ImportError as error:
            raise RuntimeError('Python <3.11 requires tomli to read Cargo manifests') from error
    with path.open('rb') as handle:
        return tomllib.load(handle)


def parse_cargo_toml(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    cargo = load_cargo_toml(path)
    sections = ('dependencies', 'build-dependencies', 'dev-dependencies')
    tables = [cargo.get(section, {}) for section in sections]
    tables.append(cargo.get('workspace', {}).get('dependencies', {}))
    for target in cargo.get('target', {}).values():
        tables.extend(target.get(section, {}) for section in sections)
    return {name.replace('-', '_') for table in tables for name in table}


def external_crates(root: Path, files: list[str]) -> set[str]:
    found: set[str] = set()
    for f in files:
        cur = os.path.dirname(os.path.join(str(root), f))
        while cur and cur != "/":
            manifest = Path(cur) / "Cargo.toml"
            if manifest.is_file():
                found |= parse_cargo_toml(manifest)
                break
            cur = os.path.dirname(cur)
    found |= parse_cargo_toml(root / "Cargo.toml")
    return found - {name.replace('-', '_') for name in IGNORE}


def added_lines(root: Path, rel: str) -> list[str]:
    has_head = bool(_git(root, "rev-parse", "--verify", "--quiet", "HEAD^{commit}"))
    out = ""
    if has_head and _git(root, "rev-parse", "--verify", "--quiet", "origin/master^{commit}"):
        out += _git(root, "diff", "-U0", "origin/master", "--", rel)
        out += "\n" + _git(root, "diff", "--cached", "-U0", "origin/master", "--", rel)
    elif has_head:
        out += "\n" + _git(root, "diff", "-U0", "HEAD", "--", rel)
        out += "\n" + _git(root, "diff", "--cached", "-U0", "HEAD", "--", rel)
    else:
        out += "\n" + _git(root, "diff", "--cached", "-U0", "--", rel)
    lines = [ln[1:] for ln in out.split("\n") if ln.startswith("+") and not ln.startswith("+++")]
    if _git(root, "ls-files", "--others", "--exclude-standard", "--", rel).strip():
        try:
            lines.extend((root / rel).read_text().splitlines())
        except (OSError, UnicodeDecodeError):
            pass
    try:
        current = (root / rel).read_text()
    except (OSError, UnicodeDecodeError):
        current = ""
    return list(dict.fromkeys(line for line in lines if line in current))


def root_imports(root: Path, rel: str) -> dict[str, set[tuple[str, ...]]]:
    """Only explicit, unconditional crate-root imports can prove a collision."""
    directory = (root / rel).parent
    while directory != directory.parent and not (directory / 'Cargo.toml').is_file():
        directory = directory.parent
    candidates = [directory / 'src/lib.rs', directory / 'lib.rs']
    # Cargo permits a non-default [lib].path; do not guess a different root.
    manifest = directory / 'Cargo.toml'
    if manifest.is_file():
        cargo = load_cargo_toml(manifest)
        library = cargo.get('lib', {})
        if 'path' in library:
            candidates = [directory / library['path']]
        elif directory.joinpath('src/lib.rs').is_file():
            candidates = [directory / 'src/lib.rs']
        else:
            # Cargo does not auto-discover a flat lib.rs without [lib].path.
            candidates = []
    entry = next((path for path in candidates if path.is_file()), None)
    if entry is None:
        return {}
    result: dict[str, set[tuple[str, ...]]] = {}
    for _, name, path in rust_syntax(entry.read_text())['root_imports']:
        if name != '*':
            result.setdefault(name, set()).add(tuple(path))
    return result


def qualified_findings(text: str, ext: set[str], imports=None) -> list[tuple[int, str]]:
    """Classify Rust type nodes, not colon-adjacent patterns or expressions."""
    syntax = rust_syntax(text)
    imports = imports or {}
    findings = set()
    for line, _, path in syntax['imports']:
        if path and path[0] in ext:
            findings.add((line, 'import'))
    for start, end, parts in syntax['paths']:
        path = tuple(parts)
        if path[0] not in ext:
            continue
        # §6.5: importing this short name must actually collide with a
        # different explicit crate-root binding. Textual mentions prove nothing.
        short = path[-1]
        collisions = imports.get(short, set())
        if collisions and all(binding != path for binding in collisions):
            continue
        for line in range(start, end + 1):
            findings.add((line, 'type'))
    return sorted(findings)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    files = list(dict.fromkeys(changed_sub_files(root)))
    if not files:
        print("\n=== no-external-crate-path (R6.4): 0 violation(s) in 0 file(s) ===")
        return 0
    ext = external_crates(root, files)
    hits: list[str] = []
    if ext:
        try:
            for rel in files:
                if not (root / rel).exists():
                    continue  # A deleted path has no current source to inspect.
                text = (root / rel).read_text()
                lines = text.splitlines()
                added = set(added_lines(root, rel))
                imports = root_imports(root, rel)
                for number, _ in qualified_findings(text, ext, imports):
                    line = lines[number - 1]
                    if line in added:
                        hits.append(f"{rel}:{number}: {line.strip()[:120]}")
        except (OSError, UnicodeDecodeError, RuntimeError, ValueError, TypeError) as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
    for h in hits:
        print(h)
    print(f"\n=== no-external-crate-path (R6.4): {len(hits)} violation(s) "
          f"in {len(files)} file(s) ===")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
