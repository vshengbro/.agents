#!/usr/bin/env python3
"""Audit pub-API test coverage for a Rust crate: which public items are
never referenced by any test in the crate's tests/ tree.

Heuristic by design: "covered" means the item NAME appears somewhere under
tests/. That is a lower bound on coverage, so the uncovered list is a
superset of the truly untested items. Good enough to drive triage; not a
substitute for reading the tests.

Usage: pub_api_coverage.py <crate-root> [--all] [--json]
  <crate-root>  e.g. /Users/sqs/code/euv/engine
  --all         also report items covered only by their own name in a
                sibling non-test file (off by default: strictly test-only)
  --json        emit machine-readable output
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Declaration patterns. Only column-0 or single-indent `pub` items matter:
# nested `pub` inside a fn body is not API surface.
DECL = re.compile(
    r"^(?P<indent>[ ]{0,4})"
    r"pub(?P<vis>\((?:crate|super|in [^)]*)\))?\s+"
    r"(?:async\s+|const\s+|unsafe\s+|extern\s+\"[^\"]*\"\s+)*"
    r"(?P<kind>fn|struct|enum|trait|type|const|static|mod|union)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
)
ATTR_BLOCK = re.compile(r"^\s*(#\[|#!\[)")
CFG_TEST = re.compile(r"#\[cfg\s*\(\s*test\s*\)\]|\[cfg\(test\)\]")
DOC_HIDDEN = re.compile(r"#\[doc\(hidden\)\]")
MODULE_DOC = re.compile(r"^\s*(///|//!|//)")

# Module declarations and re-exports decide whether a `pub` item is reachable
# from outside the crate. `pub mod x;` exposes the whole subtree; `mod x;`
# followed by `pub use x::*;` exposes only x's own public items. Anything else
# (a bare `mod x;`, or `pub(crate) use x::*;`) stays crate-internal no matter
# how many `pub` keywords its leaf files contain.
MOD_DECL = re.compile(
    r"^(?P<vis>pub(?:\([^)]*\))?)?\s*mod\s+(?:r#)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*;"
)
# `pub use { a::*, b::* };` routinely spans several lines, so the glob has to be
# matched against the whole file with re.S. A per-line match silently misses
# the entire re-export block, which is how a whole crate's API can disappear.
PUB_USE_GLOB = re.compile(r"^[ \t]*pub(?![ \t]*\()\s+use\s+(?P<body>.*?);", re.M | re.S)
GLOB_TARGET = re.compile(r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*::\s*\*")
# The leading segment of a path inside a `pub use` body: `r#fn::item`,
# `module::Child`, ... Raw identifiers keep their `r#` prefix in the
# text, so the optional prefix is part of the pattern.
USE_PATH_SEGMENT = re.compile(r"(?:r#)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*::\s*(?!\*)")


def _module_files(src: Path) -> dict[str, Path]:
    """Map a module's directory-relative name to its mod.rs / .rs file."""
    out: dict[str, Path] = {}
    for path in src.rglob("*.rs"):
        rel = path.relative_to(src)
        parts = list(rel.parts)
        if parts[-1] == "mod.rs":
            out["/".join(parts[:-1])] = path
        elif len(parts) == 1:
            # Several root files share the root module (lib.rs, main.rs,
            # build.rs). lib.rs owns the module graph, so it must win rather
            # than whichever name rglob happened to visit last.
            if parts[-1] == "lib.rs" or "" not in out:
                out[""] = path
    return out


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def public_modules(src: Path) -> set[str]:
    """Relative names of the modules whose public items reach the crate root.

    Start at lib.rs and walk outward. A child is public when the parent
    declares it `pub mod` OR re-exports it with `pub use child::*;` /
    `pub use {child::*, ..};`. A `pub(crate)` re-export does not count, and a
    child reachable only through one of those is dropped along with its
    subtree.
    """
    files = _module_files(src)
    root = files.get("")
    if root is None:
        return set()
    reachable = {""}
    frontier = [""]
    while frontier:
        current = frontier.pop()
        path = files.get(current)
        if path is None:
            continue
        body = _text(path)
        children: set[str] = set()
        for raw in body.splitlines():
            decl = MOD_DECL.match(raw)
            if decl:
                prefix = f"{current}/" if current else ""
                name = f"{prefix}{decl.group('name')}"
                if decl.group("vis") == "pub":
                    children.add(name)
        for use in PUB_USE_GLOB.finditer(body):
            for target in GLOB_TARGET.finditer(use.group("body")):
                prefix = f"{current}/" if current else ""
                name = f"{prefix}{target.group('name')}"
                # A child module is backed either by a directory (mod.rs) or by
                # a single file (`struct.rs`, `trait.rs`, ...). Checking only
                # the directory map drops every file-backed submodule, which is
                # most of the keyword files.
                if (
                    name in files
                    or (src / f"{name}.rs").is_file()
                    or (src / name / "mod.rs").is_file()
                ):
                    children.add(name)
            # A `pub use module::item;` names the module just as surely as a
            # glob does, and without this the module is dropped with its
            # subtree even though the item it re-exports is public. Only
            # `pub use` reaches here (PUB_USE_GLOB rejects `pub(crate) use`),
            # so a crate-private re-export still does not count. Names that
            # are not modules of this crate fail the existence check below
            # and are filtered out, which is what keeps `std` and external
            # crates from being mistaken for local modules.
            for segment in USE_PATH_SEGMENT.finditer(use.group("body")):
                prefix = f"{current}/" if current else ""
                candidate = f"{prefix}{segment.group('name')}"
                if (
                    candidate in files
                    or (src / f"{candidate}.rs").is_file()
                    or (src / candidate / "mod.rs").is_file()
                ):
                    children.add(candidate)
        for child in children:
            if child not in reachable:
                reachable.add(child)
                frontier.append(child)
    return reachable


def _declared_submodules(files: dict[str, Path]) -> dict[str, set[str]]:
    """For each module, the submodule names its mod.rs declares via `mod x;`."""
    out: dict[str, set[str]] = {}
    for module, path in files.items():
        names: set[str] = set()
        for raw in _text(path).splitlines():
            decl = MOD_DECL.match(raw)
            if decl:
                names.add(decl.group("name"))
        out[module] = names
    return out


def _file_module(path: Path, src: Path, submodules: dict[str, set[str]]) -> str | None:
    """Module that owns `path`, or None when the file is never compiled.

    `src/lib.rs` and `src/foo.rs` belong to the root module. Inside a module
    directory there are two kinds of file and they belong to DIFFERENT
    modules:
      - `mod.rs` and the keyword files beside it (`impl.rs`, `struct.rs`, ...)
        belong to the directory's module;
      - a file whose stem matches a `mod <stem>;` declaration is a submodule
        of that directory, so `reactive/signal/static.rs` is module
        `reactive/signal/static`, not a keyword file of `reactive/signal`.
    Collapsing the two is how a `pub(crate)` static ends up reported as API.

    A file whose stem matches NO declaration is an orphan: rustc never loads
    it, so nothing it declares is API no matter how many `pub` items it
    contains. Attributing it to its parent directory instead is what let
    `checkbox/view/const.rs` (never named by any `mod.rs`) report
    `pub const INPUT_TYPE_CHECKBOX` as public API of a reachable module.
    """
    rel = path.relative_to(src)
    parts = list(rel.parts)
    if len(parts) == 1:
        return ""
    parent = "/".join(parts[:-1])
    stem = parts[-1][: -len(".rs")]
    if stem == "mod":
        return parent
    if stem in submodules.get(parent, set()):
        return f"{parent}/{stem}"
    return None


def strip_cfg_test_regions(lines: list[str]) -> list[bool]:
    """Return a per-line mask: True when the line is inside a #[cfg(test)] mod."""
    mask = [False] * len(lines)
    depth = 0
    armed = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if CFG_TEST.search(line):
            armed = True
        if depth > 0:
            mask[i] = True
            depth += line.count("{") - line.count("}")
            if depth <= 0:
                depth = 0
                armed = False
            continue
        if armed and "{" in line:
            depth = line.count("{") - line.count("}")
            mask[i] = depth > 0 or True
            if depth <= 0:
                depth = 0
                armed = False
    return mask


IMPL_OPEN = re.compile(r"^\s*(?:#\[[^\]]*\]\s*)*impl\b")


def collect_items(crate_root: Path) -> list[dict]:
    items: list[dict] = []
    src = crate_root / "src"
    public = public_modules(src)
    submodules = _declared_submodules(_module_files(src))
    for path in sorted(src.rglob("*.rs")):
        module = _file_module(path, src, submodules)
        if module is None:
            continue
        exact_ok = module in public
        # An inherent `impl` block contributes PUBLIC methods even when the
        # file holding it is a private submodule: Rust privacy gates the path
        # to the TYPE, not to its methods, so `HookContext::use_hook` stays
        # callable from outside even though `reactive/hook/impl.rs` is
        # declared as a private `mod`. Relax the gate to the parent directory
        # for those lines only. A top-level `pub static` gets no such
        # exemption, which is what keeps `reactive/signal/static.rs` out.
        dir_ok = ("/" + module).rsplit("/", 1)[0].lstrip("/") if "/" in module else ""
        dir_ok = module.rsplit("/", 1)[0] if "/" in module else ""
        if not exact_ok and dir_ok not in public:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        mask = strip_cfg_test_regions(lines)
        hidden_depth = 0
        depth = 0
        impl_depth = 0
        impl_stack: list[list[int]] = []
        for i, line in enumerate(lines):
            if mask[i]:
                depth += line.count("{") - line.count("}")
                continue
            if hidden_depth > 0:
                if DOC_HIDDEN.search(line):
                    hidden_depth = 3  # a few lines of attribute follow
                hidden_depth = max(0, hidden_depth - 1)
                depth += line.count("{") - line.count("}")
                continue
            if DOC_HIDDEN.search(line):
                hidden_depth = 3
                continue
            m = DECL.match(line)
            if m and m.group("kind") == "fn" and m.group("name") == "main":
                # `pub fn main` is the crate entry point — in a lib crate it is
                # the `#[wasm_bindgen]` wasm entry, mounted into a page and never
                # called by a consumer. Counting it reports a permanent
                # "untested" gap on every wasm crate, which is noise, not signal.
                depth += line.count("{") - line.count("}")
                continue
            if m and not MODULE_DOC.match(line):
                # pub(crate) / pub(super) / pub(in ..) are NOT public API and
                # are deliberately not counted: the goal is covering the
                # crate's published surface, not every internal helper.
                if m.group("vis"):
                    depth += line.count("{") - line.count("}")
                    continue
                if not exact_ok and impl_depth <= 0:
                    depth += line.count("{") - line.count("}")
                    continue
                items.append(
                    {
                        "name": m.group("name"),
                        "kind": m.group("kind"),
                        "file": str(path.relative_to(crate_root)),
                        "line": i + 1,
                    }
                )
            if IMPL_OPEN.match(line):
                # Remember the brace depth this block will return to, plus
                # whether its opening brace has actually been seen. A header
                # that spans several lines has no brace on its first line,
                # and closing a not-yet-open block is what used to reset
                # impl_depth and hide the methods inside it.
                impl_stack.append([depth, 0])
            depth += line.count("{") - line.count("}")
            for entry in impl_stack:
                if not entry[1] and depth > entry[0]:
                    entry[1] = 1
            impl_depth = sum(entry[1] for entry in impl_stack)
            while impl_stack and impl_stack[-1][1] and depth <= impl_stack[-1][0]:
                impl_stack.pop()
                impl_depth = sum(entry[1] for entry in impl_stack)
    return items


def test_corpus(crate_root: Path) -> str:
    chunks: list[str] = []
    for tests_dir in (crate_root / "tests", crate_root / "src"):
        if not tests_dir.exists():
            continue
        for path in tests_dir.rglob("*.rs"):
            if "tests" not in path.parts and "src" not in path.parts:
                continue
            if path.parts[-2:-1] and "tests" in path.parts:
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    crate_root = Path(argv[0]).resolve()
    want_json = "--json" in argv

    items = collect_items(crate_root)
    tests_text = test_corpus(crate_root)
    tests_files_text = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in (crate_root / "tests").rglob("*.rs")
    ) if (crate_root / "tests").exists() else ""

    covered: list[dict] = []
    uncovered: list[dict] = []
    for item in items:
        # `_` is a word character, so `\bname\b` fails to match a test named
        # `profiler_handle_measure_pushes_entry` for the method `measure`.
        # Treat `_` as a separator instead: only alphanumerics block a match.
        pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(item["name"]) + r"(?![A-Za-z0-9])")
        if pat.search(tests_files_text):
            covered.append(item)
        else:
            # referenced in src (e.g. by another module) but never in tests
            item["referenced_in_src"] = bool(pat.search(tests_text))
            uncovered.append(item)

    if want_json:
        print(json.dumps({"uncovered": uncovered, "covered_count": len(covered)},
                         indent=2))
        return 0

    by_kind: dict[str, int] = {}
    for item in uncovered:
        by_kind[item["kind"]] = by_kind.get(item["kind"], 0) + 1
    total = len(items)
    print(f"=== {crate_root.name}: {total} pub items, "
          f"{len(covered)} referenced in tests, {len(uncovered)} NOT referenced")
    print("uncovered by kind: " + ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())))
    print()
    for item in sorted(uncovered, key=lambda x: (x["file"], x["line"])):
        flag = " (used in src)" if item.get("referenced_in_src") else ""
        print(f"  {item['file']}:{item['line']}: pub {item['kind']} {item['name']}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
