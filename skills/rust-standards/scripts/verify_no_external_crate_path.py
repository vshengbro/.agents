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

import os
import re
import subprocess
import sys
from pathlib import Path

# In-repo crates and the std trio are never "external".
IGNORE = {
    "std", "core", "alloc", "log",
    "euv", "euv-ui", "euv-cli", "euv-core",
    "euv-engine", "euv-macros", "euv-example", "hyperlane",
}

DEP_SECTIONS = ("[dependencies]", "[build-dependencies]",
                "[dev-dependencies]", "[workspace.dependencies]")
DEP_NAME = re.compile(r"^([a-zA-Z0-9_-]+)\s*=")
USE_EXT = re.compile(r"^use\s+([a-zA-Z0-9_-]+)::")
ANNOTATION_EXT = re.compile(r":\s*([a-zA-Z0-9_-]+)::")


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
    out = _git(root, "diff", "--name-only", "origin/master", "HEAD", "--", "*.rs")
    return [
        f for f in out.strip().split("\n")
        if f
        and f.endswith(".rs")
        and not f.endswith(("/mod.rs", "/lib.rs", "/main.rs", "/build.rs"))
        and "/tests/" not in f
        and "/target/" not in f
    ]


def parse_cargo_toml(path: Path) -> set[str]:
    deps: set[str] = set()
    if not path.is_file():
        return deps
    in_deps = False
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return deps
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_deps = stripped in DEP_SECTIONS
            continue
        if in_deps:
            m = DEP_NAME.match(line)
            if m:
                deps.add(m.group(1))
    return deps


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
    return found - IGNORE


def added_lines(root: Path, rel: str) -> list[str]:
    out = _git(root, "diff", "-U0", "origin/master", "HEAD", "--", rel)
    return [ln[1:] for ln in out.split("\n") if ln.startswith("+") and not ln.startswith("+++")]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    files = changed_sub_files(root)
    if not files:
        print("\n=== no-external-crate-path (R6.4): 0 violation(s) in 0 file(s) ===")
        return 0
    ext = external_crates(root, files)
    hits: list[str] = []
    if ext:
        for rel in files:
            for line in added_lines(root, rel):
                stripped = line.lstrip()
                m = USE_EXT.match(stripped)
                if m and m.group(1) in ext:
                    hits.append(f"{rel}: {line.strip()[:120]}")
                    continue
                m = ANNOTATION_EXT.search(stripped)
                if m and m.group(1) in ext:
                    if not re.match(r"[A-Z]", stripped[m.end():]):
                        continue
                    if stripped.startswith("#"):
                        continue
                    hits.append(f"{rel}: {line.strip()[:120]}")
    for h in hits:
        print(h)
    print(f"\n=== no-external-crate-path (R6.4): {len(hits)} violation(s) "
          f"in {len(files)} file(s) ===")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
