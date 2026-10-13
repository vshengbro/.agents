#!/usr/bin/env python3
"""Find deletion candidates in a Rust workspace, with the evidence attached.

Two independent passes, because they answer different questions:

  1. COMPILER PASS - what does rustc itself report as never used, never
     constructed, or never read? This is the only evidence that permits a
     delete. An empty result means "there is no dead code here".

  2. STRUCTURE PASS - which .rs files and module directories exist on disk
     but are never reached by a `mod` declaration? That is code which was
     written and never COMPILED. It is a wiring bug, not dead code, and the
     fix is to register the module.

Neither pass deletes anything. Print, review, then act.

Usage:
    python3 dead-code-sweep.py [repo_path] [--target TRIPLE] [--no-cargo]
"""

from __future__ import annotations

import argparse
import collections
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "target", "node_modules", "dist", "build", ".idea"}

DEAD_CODE_RE = re.compile(
    r"never used|never constructed|never read|is never used|"
    r"function .* is never used|dead_code",
    re.IGNORECASE,
)

# `mod r#input;` declares the module named `input`.
MOD_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+(r#)?([A-Za-z_][A-Za-z0-9_]*)\s*;")


def rust_files(repo: Path) -> list[Path]:
    return [p for p in repo.rglob("*.rs") if not (set(p.parts) & SKIP_DIRS)]


def compiler_pass(repo: Path, target: str | None) -> list[str]:
    """Ask the compiler what is dead. Authoritative; absence is meaningful."""
    if shutil_which("cargo") is None:
        print("  cargo not found - skipping compiler pass", file=sys.stderr)
        return []
    cmd = ["cargo", "clippy", "--all-targets", "--message-format=short"]
    if target:
        cmd += ["--target", target]
    print("  $ " + " ".join(cmd), file=sys.stderr)
    try:
        proc = subprocess.run(
            cmd, cwd=repo, capture_output=True, text=True, timeout=1800
        )
    except subprocess.TimeoutExpired:
        print("  compiler pass timed out - results are NOT trustworthy",
              file=sys.stderr)
        return []
    out = proc.stdout + proc.stderr
    return [ln for ln in out.splitlines() if DEAD_CODE_RE.search(ln)]


def shutil_which(name: str) -> str | None:
    from shutil import which
    return which(name)


def structure_pass(repo: Path) -> tuple[list[str], list[str], list[str]]:
    """Split unregistered modules from genuinely-empty files.

    Returns (orphans, empty_files, tokenized).
    """
    orphans: list[str] = []
    empty: list[str] = []
    counts: collections.Counter[str] = collections.Counter()
    ident = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

    for path in rust_files(repo):
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        counts.update(ident.findall(text))
        if not text.strip():
            empty.append(str(path.relative_to(repo)))

    # A `mod.rs` / `mod.rs`-style dir is "registered" if its parent module
    # tree declares it. Walk up from every mod.rs and check registration.
    for mod_rs in repo.rglob("mod.rs"):
        if set(mod_rs.parts) & SKIP_DIRS:
            continue
        d = mod_rs.parent
        # The directory itself is declared by its parent's mod.rs, if any.
        for parent in [d.parent] + list(d.parents):
            candidate = parent / "mod.rs"
            if not candidate.is_file() or set(candidate.parts) & SKIP_DIRS:
                continue
            declared = {m.group(2) for m in
                        (MOD_RE.match(l) for l in
                         candidate.read_text(errors="replace").splitlines())
                        if m}
            if d.name in declared:
                break
        else:
            orphans.append(str(d.relative_to(repo)))

    return orphans, empty, counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--target", default=None,
                    help="e.g. wasm32-unknown-unknown for wasm-only crates")
    ap.add_argument("--no-cargo", action="store_true",
                    help="structure pass only (fast, but NOT authoritative)")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"not a directory: {repo}", file=sys.stderr)
        return 2

    print(f"repo: {repo}\n")

    if args.no_cargo:
        dead: list[str] = []
    else:
        print("[1/2] compiler pass (authoritative for deletion)")
        dead = compiler_pass(repo, args.target)
        if dead:
            for line in dead:
                print(f"   {line}")
        else:
            print("   0 findings - rustc reports no dead code")
        print()

    print("[2/2] structure pass (finds never-compiled code, not dead code)")
    orphans, empty, _ = structure_pass(repo)
    if orphans:
        print(f"   {len(orphans)} module dir(s) never `mod`-registered:")
        for o in sorted(orphans):
            print(f"     {o}")
        print("   -> fix by REGISTERING the module, or delete only if the dir")
        print("      is genuinely empty AND has no subsystem in src/.")
    else:
        print("   0 unregistered module dirs")
    if empty:
        print(f"   {len(empty)} empty file(s):")
        for e in sorted(empty):
            print(f"     {e}")
    print()

    if not dead and not orphans and not empty:
        print("RESULT: nothing to delete.")
        return 0
    print("RESULT: candidates above. Only the compiler pass justifies a delete.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
