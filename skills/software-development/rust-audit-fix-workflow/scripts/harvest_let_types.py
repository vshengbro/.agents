#!/usr/bin/env python3
"""Harvest the real type of every un-annotated `let` binding a §5.1 check reports.

WHY THIS EXISTS
    §5.1 requires every `let` binding to carry an explicit type annotation. A
    whole-repo verifier can report hundreds of them, and no fixer ships for it.
    Inferring the type by reading the RHS is the expensive path: the RHS is
    usually a multi-line chain whose type you would be guessing, and a wrong
    guess costs a compile cycle per site.

METHOD
    For each site, rewrite `let <pat> = <expr>` to
    `let <pat>: std::convert::Infallible = <expr>` and let rustc report the
    type it actually wanted. E0308's span label reads

        expected `Infallible`, found `Result<bool, JsValue>`
                                    ^^^^^^^^^^^^^^^^^^^  <- this is the answer

    Note what a CLOSURE binding reports instead, because it decides whether
    this script can help you at all:

        let on_clear_click: Infallible = move |_: Event| { .. };
        // error[E0308]: expected `Infallible`, found `closure`
        //                                  ^^^^^^^^  not a type

    `closure` is the end of the road for that site: there is no type text to
    harvest, and the annotation has to be written by hand from the
    surrounding context. Sites whose value is a generic iterator report
    nothing usable either. A third group is a long generic type that rustc
    ELIDES:

        expected `Infallible`, found `Result<RwLockWriteGuard<'_, ...>, ...>`

    The `...` is rustc's truncation, not an expandable placeholder -- writing
    it into source is a syntax error, so those are dropped here and surface
    as hand-annotate. Count all three groups up front -- they are the real
    shape of the work, and the compiler-harvestable remainder is usually the
    minority.

    Four details make the difference between this working and silently
    returning nothing; all four were found the hard way:

    1. The probe type must EXIST in scope. An invented name
       (`EuvTypeProbe`) fails name resolution with E0425 and rustc never
       reaches type checking, so you get zero answers and no error pointing
       at why. `std::convert::Infallible` is in the prelude everywhere.
    2. Use `--message-format=json`, not `short`. `short` renders the type as
       the bare word `None`; only the JSON `spans[].label` carries the full
       type text.
    3. Read the `found` side, not `expected`. `expected` is the probe you
       just injected.
    4. rustc stops emitting after roughly 8 errors per crate, so sites are
       probed in small batches and the loop repeats until the set drains.
       A batch that reports fewer entries than it attempted is NORMAL, not a
       failure -- the remainder is picked up by the next round. What is not
       normal is a per-package counter that claims sites resolved when they
       did not, so the totals below are computed from `resolved`, never from
       the size of the drained set.

SAFETY
    A probe run mutates real source files, so this must be interruptible
    without leaving the tree in a broken state. Every batch restores the
    files it touched in a `finally`, results are written after each round so
    a kill loses no work, and a completed run leaves the tree byte-identical.
    Run it as a BACKGROUND command: a foreground call that hits the tool
    timeout is killed mid-batch, and the tree is left holding probe types.

USAGE
    python3 harvest_let_types.py <repo> [--out types.json]
                                 [--verifier <path-to-verify_let_type_annotations.py>]
                                 [--batch 6]
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

# Mirrors the pattern in verify_let_type_annotations.py: a `let` binding whose
# pattern carries no `: T`. If you change one, change both.
LET_NO_ANNOT = re.compile(
    r"^\s*let\s+(?:mut\s+)?"
    r"(?P<pat>(?:\([^)]*\))?(?:_[a-zA-Z0-9_]*|[a-zA-Z_][a-zA-Z0-9_]*)"
    r"(?:\s*:\s*[^=]+?)?)\s*=\s*"
)

PROBE = "std::convert::Infallible"

# Crates that build for the host. Probing them with --target wasm32 will not
# compile for reasons unrelated to the probe, so the target is per-package.
HOST_CRATES = {"euv-docs", "euv-macros"}
WASM_TARGET = "wasm32-unknown-unknown"

# Resolves a file path to the workspace member that owns it, by walking up to
# the nearest Cargo.toml that declares [package] name. Hardcoding a
# prefix -> package map silently mis-attributes every file it misses.
_PKG_RE = re.compile(r'^\[package\]\s*\nname\s*=\s*"([^"]+)"', re.M)


def owning_package(repo: pathlib.Path, rel: str) -> str | None:
    parts = pathlib.Path(rel).parts
    for i in range(len(parts) - 1, 0, -1):
        toml = repo.joinpath(*parts[:i], "Cargo.toml")
        if toml.exists():
            m = _PKG_RE.search(toml.read_text())
            if m:
                return m.group(1)
    return None


def parse_sites(verifier: pathlib.Path, repo: pathlib.Path) -> list[tuple[str, int]]:
    r = subprocess.run(
        [sys.executable, str(verifier), str(repo)],
        capture_output=True, text=True,
    )
    sites: list[tuple[str, int]] = []
    for line in r.stdout.splitlines():
        m = re.match(rf"^{re.escape(str(repo))}/?(\S+\.rs):(\d+):", line)
        if m:
            sites.append((m.group(1), int(m.group(2))))
    return sites


def probe_batch(
    repo: pathlib.Path,
    env: dict[str, str],
    package: str,
    batch: list[tuple[str, int]],
    originals: dict[str, str],
) -> dict[tuple[str, int], str]:
    """Probe one batch. Returns {(file, line): real_type}. Always restores."""
    touched: dict[str, str] = {}
    attempted: list[tuple[str, int]] = []
    for f, _ in batch:
        touched.setdefault(f, originals[f])

    for f, n in batch:
        lines = touched[f].split("\n")
        if n - 1 >= len(lines):
            continue
        m = LET_NO_ANNOT.match(lines[n - 1])
        if not m:
            # The verifier's line moved (a prior batch's edit changed line
            # counts) or the regex disagrees. Skip rather than corrupt.
            continue
        pos = m.end("pat")
        lines[n - 1] = lines[n - 1][:pos] + ": " + PROBE + lines[n - 1][pos:]
        touched[f] = "\n".join(lines)
        attempted.append((f, n))

    for f, txt in touched.items():
        (repo / f).write_text(txt)
    try:
        cmd = [
            "cargo", "check", "-p", package, "--lib", "--offline",
            "--message-format=json",
        ]
        if package not in HOST_CRATES:
            cmd += ["--target", WASM_TARGET]
        r = subprocess.run(
            cmd, capture_output=True, text=True, cwd=repo, env=env,
        )
        raw = r.stdout
    finally:
        for f, txt in touched.items():
            (repo / f).write_text(txt)

    found: dict[tuple[str, int], str] = {}
    seen = set(attempted)
    for line in raw.splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("reason") != "compiler-message":
            continue
        msg = d.get("message", {})
        if (msg.get("code") or {}).get("code") != "E0308":
            continue
        for sp in msg.get("spans", []):
            if not sp.get("is_primary"):
                continue
            key = (sp["file_name"], sp["line_start"])
            m = re.match(r"expected `.+?`, found `(.+?)`$", sp.get("label") or "")
            if not (m and key in seen):
                continue
            typ = m.group(1)
            # rustc ELIDES long generic types to a literal `...`:
            #   Result<RwLockWriteGuard<'_, ...>, ...>
            # Writing that into source is a syntax error
            # (E0586 inclusive range with no end), and the `...` is not a
            # placeholder an apply pass can expand. Drop it so the caller
            # falls through to the bisect path, which records the site as
            # hand-annotate -- the honest outcome, since the elided
            # arguments are exactly the part a human must supply.
            if "..." in typ:
                continue
            # `expected` is our own probe; `found` is the binding's real type.
            found[key] = typ
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, default=None,
                    help="where to write the harvested types (default: "
                         "<repo>/.let_types.json)")
    ap.add_argument("--verifier", type=pathlib.Path, default=None,
                    help="path to verify_let_type_annotations.py")
    ap.add_argument("--batch", type=int, default=6,
                    help="sites per cargo invocation; keep low because rustc "
                         "stops emitting after ~8 errors")
    args = ap.parse_args()

    repo = args.repo.resolve()
    if not repo.is_dir():
        print(f"not a directory: {repo}", file=sys.stderr)
        return 2

    here = pathlib.Path(__file__).resolve().parent
    verifier = args.verifier or (here / "verify_let_type_annotations.py")
    if not verifier.exists():
        print(f"verifier not found: {verifier}\n"
              f"pass --verifier <path>", file=sys.stderr)
        return 2

    out = args.out or (repo / ".let_types.json")
    env = dict(os.environ)
    env["PATH"] = str(pathlib.Path.home() / ".cargo" / "bin") + os.pathsep + env["PATH"]

    sites = parse_sites(verifier, repo)
    if not sites:
        print("no sites reported by the verifier")
        return 0

    # Snapshot every file we may touch, so restoration is exact and a killed
    # run leaves nothing behind.
    originals = {f: (repo / f).read_text() for f in {f for f, _ in sites}}

    by_pkg: dict[str, list[tuple[str, int]]] = {}
    unattributed: list[tuple[str, int]] = []
    for f, n in sites:
        pkg = owning_package(repo, f)
        if pkg is None:
            unattributed.append((f, n))
        else:
            by_pkg.setdefault(pkg, []).append((f, n))
    if unattributed:
        print(f"WARNING: {len(unattributed)} site(s) in files with no "
              f"resolvable package, skipped: "
              f"{sorted({f for f, _ in unattributed})}", file=sys.stderr)

    resolved: dict[tuple[str, int], str] = {}
    # Sites proven un-harvestable (closures, generic inference). Tracked
    # separately from `unresolved` -- which is merely "not yet tried" -- so the
    # final report can tell "annotate by hand" from "still to do".
    unresolvable: set[tuple[str, int]] = set()
    if out.exists():
        for k, v in json.loads(out.read_text()).items():
            f, n = k.split("|", 1)
            resolved[(f, int(n))] = v
        print(f"resuming, {len(resolved)} already harvested")

    for pkg, pkg_sites in sorted(by_pkg.items()):
        pkg_set = set(pkg_sites)
        todo = pkg_set - set(resolved)
        while todo:
            chunk = list(todo)[: args.batch]
            got = probe_batch(repo, env, pkg, chunk, originals)
            resolved.update(got)
            todo -= set(got)
            out.write_text(json.dumps(
                {f"{f}|{n}": t for (f, n), t in resolved.items()}, indent=1,
            ))
            if not got:
                # Bisect: one site alone tells you whether it is annotatable
                # at all, or whether the enclosing fn is unreachable/typo'd.
                # This site is UNRESOLVABLE, not done -- it must be recorded
                # as such, because a site that leaves the todo set without an
                # entry in `resolved` has no other way to be reported.
                solo = chunk[:1]
                got1 = probe_batch(repo, env, pkg, solo, originals)
                resolved.update(got1)
                unresolvable.update(set(solo) - set(got1))
                todo -= set(solo)
        # Count from `resolved`, NOT from the drained todo set. The bisect
        # path removes sites from todo without resolving them, so
        # `len(pkg_sites) - len(todo)` reports a site as harvested when it was
        # in fact abandoned -- which is how a crate can print "31/31" while
        # contributing zero entries.
        done = len(pkg_set & set(resolved))
        print(f"{pkg:16s} {done:4d}/{len(pkg_sites)}"
              f"  (hand-annotate: {len(pkg_set) - done})")

    never_tried = sorted(set(sites) - set(resolved) - unresolvable)
    by_hand = sorted(unresolvable & set(sites))
    print(f"\nharvested {len(resolved)}/{len(sites)}  ->  {out}")
    if by_hand:
        print(f"{len(by_hand)} site(s) yielded no usable type (closures report "
              f"`closure`, generic inference reports nothing). These are the "
              f"ones to annotate by hand:")
        for f, n in by_hand:
            print(f"  {f}:{n}")
    if never_tried:
        print(f"{len(never_tried)} site(s) never probed (interrupted run? "
              f"re-run to resume):")
        for f, n in never_tried:
            print(f"  {f}:{n}")
    print("\napply with a read-modify-write pass; do NOT regex the raw text "
          "(raw strings and byte literals defeat naive tokenizers).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
