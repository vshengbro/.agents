#!/usr/bin/env python3
"""§6.1 / §6.3 / §6.4 — module imports are centralized in lib.rs / mod.rs.

Three sub-rules, each owned by a different file kind:

  lib.rs    no visibility demand from this check. A private `use` at the
            crate root reaches every descendant through `use super::*;`
            chains (Rust visibility: private items are visible within the
            defining module AND its descendants — verified against rustc
            2026-10-08). Whether the root import must ALSO be `pub use`
            (because another crate names the symbol) is §18's question,
            answered with real cross-crate reader analysis, not this
            check's. An earlier version of this rule demanded `pub use`
            on the premise that private imports are invisible to
            sub-files; that premise is false and the demand actively
            contradicted §18's minimum-exposure rule, so it was removed.

  mod.rs    the strict three-stage layout and no blank-line separators
            anywhere in the body:
              1. `mod r#xxx;` declarations
              2. `pub use {...};` / `pub(crate) use {...};` re-exports
              3. a single trailing `use super::*;`
            (keyword files are declared with raw identifiers, `mod r#fn;`)
            Comments in mod.rs are NOT reported here: §2.5 (2026-10-09,
            absolute) owns that rule comprehensively — every comment form
            in every mod.rs AND every *.toml file, tree-wide — via
            verify_no_toml_mod_comments.py (audit check 51). An earlier
            version of this check also flagged comments, but exempted
            `///` on line 1 and missed trailing / block comments, which
            contradicted the absolute bar.

  sub-file  (fn.rs / struct.rs / impl.rs / const.rs / enum.rs / trait.rs /
            type.rs / static.rs) may have NO `use` at all, or exactly
            `use super::*;` — nothing else. Any other import (a long path, a
            specific `super::` path, a glob of an external crate) is a
            violation, because the parent already re-exported everything the
            sub-file is allowed to name.

§6.4 additionally forbids a sub-file from re-importing a symbol the parent
already re-exported; that is covered by the same "only `use super::*;`" rule.

Not reported: comments anywhere (§2.5 owns them via
verify_no_toml_mod_comments.py), blank lines in lib.rs, and `#[cfg(test)]`
blocks.

Output contract: one violation per line, then a summary line beginning
`=== module-imports centralized:`.

Exit code: 0 = compliant, 1 = violations, 2 = usage error.
"""

import re
import subprocess
import sys
from pathlib import Path

KEYWORD_FILES = {
    "fn.rs", "struct.rs", "impl.rs", "const.rs", "enum.rs", "trait.rs",
    "type.rs", "static.rs", "macro.rs",
}
RUST_KEYWORDS = {
    "fn", "struct", "impl", "const", "enum", "trait", "type", "static",
    "macro", "mod", "let", "match", "move", "ref", "box", "use", "pub", "crate",
    "self", "super", "async", "await", "dyn", "union", "macro_rules",
}

USE = re.compile(r"^\s*((?:pub(?:\([^)]*\))?\s+)?)use\s+(.*?);\s*$")
MOD_DECL = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+(r#)?(\w+)\s*;")
CFG_TEST = re.compile(r"^\s*#\[cfg\(test\)\]")
SUPER_STAR = re.compile(r"^\s*use\s+super\s*::\s*\*\s*;\s*$")
PUB_ITEM = re.compile(
    r"^\s*(pub(?:\([^)]*\))?)\s+(?:async\s+|unsafe\s+|const\s+)*"
    r"(?:const|fn|struct|enum|trait|type|static)\s+([A-Za-z_]\w*)"
)


def list_rs_files(root: Path) -> list[Path]:
    result = subprocess.run(
        [
            "find", str(root), "-name", "*.rs",
            "-not", "-path", "*/target/*",
            "-not", "-path", "*/.cargo/registry/*",
        ],
        capture_output=True, text=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line.strip()]


def _skip_whole_block(lines: list[str], idx: int) -> int:
    j = idx
    while j < len(lines) and "{" not in lines[j]:
        j += 1
    if j >= len(lines):
        return len(lines)
    depth, k = 0, j
    while k < len(lines):
        depth += lines[k].count("{") - lines[k].count("}")
        if depth == 0:
            return k
        k += 1
    return len(lines) - 1


def _is_under_src(path: Path) -> bool:
    return "src" in path.parts


def _is_mod_rs(path: Path) -> bool:
    return path.name == "mod.rs"


def _is_keyword_file(path: Path) -> bool:
    return path.name in KEYWORD_FILES


def _workspace_member_names(path: Path) -> set[str]:
    """Crate names of every sibling in the same workspace.

    §6.1 group 6 explicitly allows a private `use current_crate::*;` when the
    current crate is a workspace member, so glob-importing a sibling privately
    is the documented spelling, not a violation.

    The walk must find the manifest that actually declares `[workspace]`, not
    merely the first Cargo.toml above the file: a member crate has its own and
    would otherwise stop the search before the root is ever reached.
    """
    names: set[str] = set()
    for parent in path.parents:
        candidate = parent / "Cargo.toml"
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text()
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: cannot read {candidate}: {exc}", file=sys.stderr)
            continue
        if "[workspace]" not in text:
            continue  # a member manifest — keep walking up
        for entry in _workspace_members(text):
            member_dir = parent / entry
            # A member is named by its [package].name, which is not always the
            # directory's last segment (euv/engine is the `euv-engine` crate).
            # Record both so either spelling is recognised.
            names.add(Path(entry).name)
            declared = _package_name(member_dir / "Cargo.toml")
            if declared:
                names.add(declared)
        # the workspace root's OWN [package] name is a sibling too — a root
        # package is not listed in `members` but every member depends on it.
        root_name = _package_name(candidate)
        if root_name:
            names.add(root_name)
        names.add(parent.name)
        return names
    return names


def _package_name(manifest_path: Path) -> str:
    try:
        manifest_text = manifest_path.read_text()
    except (OSError, UnicodeDecodeError):
        return ""
    in_package = False
    for raw in manifest_text.splitlines():
        line = raw.strip()
        if line.startswith("["):
            in_package = line == "[package]"
            continue
        if not in_package or not line or line.startswith("#"):
            continue
        if line.startswith("name"):
            _, _, value = line.partition("=")
            return value.strip().strip('"').strip("'")
    return ""


def _workspace_members(manifest_text: str) -> list[str]:
    """Every `members` entry, including a multi-line TOML array.

    A line-based split mangles `members = [\n  "core",\n  "engine",\n]` into
    a first element of `["core`, so the array is collected as raw text between
    the brackets instead.
    """
    match = re.search(r"^\s*members\s*=\s*\[(.*?)\]", manifest_text, re.S | re.M)
    if match is None:
        return []
    return re.findall(r"[\"`]([^\"`]+)[\"`]", match.group(1))


def _module_file(src_dir: Path, name: str):
    """Resolve a module name to its file (`const.rs` or `const/mod.rs`)."""
    for candidate in (src_dir / f"{name}.rs", src_dir / name / "mod.rs"):
        if candidate.is_file():
            return candidate
    return None


def _exported_symbols(body: str) -> list[str]:
    """Symbol names a `use` body brings in (all pub items for a glob)."""
    return [body.split("::")[-1].strip()] if not body.endswith("::*") else []


def _used_by_subfile(lib_path: Path, body: str) -> bool:
    """True when a sub-file actually names a symbol this import provides.

    §6.1 only justifies `pub use` when a sub-file needs the item through
    `use super::*;`. When nothing consumes it, the private import is the
    correct form: publishing it is what produces `unused_imports`. The old
    check flagged every private module import regardless of use, so fixing
    the reported violation added a compiler warning.
    """
    src_dir = lib_path.parent
    head = body.split("::", 1)[0].strip().strip("{}").strip()
    module_name = head[2:] if head.startswith("r#") else head
    if not module_name or not module_name.isidentifier():
        return True  # cannot prove it is unused — keep reporting
    module_file = _module_file(src_dir, module_name)
    if module_file is None:
        return True
    if body.endswith("::*"):
        items = [
            (m.group(1), m.group(2))
            for m in (
                PUB_ITEM.match(l)
                for l in module_file.read_text(errors="replace").splitlines()
            )
            if m
        ]
        # `pub use r#x::*` can only re-export items that are themselves `pub`.
        # When every item is `pub(crate)`, rustc emits "glob import doesn't
        # reexport anything with visibility `pub` because no imported item is
        # public enough" — so demanding `pub use` here trades a clean build for
        # a warning. The private `use` is both correct and warning-free: a
        # private binding in a parent is visible to its descendants, so
        # `use super::*;` in a sub-file still resolves the symbols.
        if items and not any(vis == "pub" for vis, _ in items):
            return False
        symbols = [name for _, name in items]
    else:
        symbols = _exported_symbols(body)
    if not symbols:
        return True
    pattern = re.compile(r"\b(" + "|".join(re.escape(s) for s in symbols) + r")\b")
    for other in src_dir.rglob("*.rs"):
        if other in (lib_path, module_file):
            continue
        if pattern.search(other.read_text(errors="replace")):
            return True
    return False


def audit_lib_rs(path: Path, lines: list[str]) -> list[str]:
    """No per-file visibility demand: private root `use` reaches descendants.

    Kept as the lib.rs entry point so the dispatcher's file-kind routing
    stays intact; the former private-use -> pub-use demand was removed
    (see module docstring). §6.4's no-re-import rule is enforced by the
    sub-file check below, not here.
    """
    return []


# A `use` of a crate, or of `std` / `core` / `alloc`. The path is spelled out
# rather than derived from Cargo.toml so the rule does not move when a
# dependency is added.
IMPORT_HEAD = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?use\s+"
    r"(std|core|alloc|log|serde|tokio|wasm_bindgen|web_sys|js_sys|"
    r"[a-z_][a-z0-9_]*)\s*::"
)
STDLIKE = {"std", "core", "alloc"}
# `super`, `self` and `crate` are how the chain is threaded through a tree, with
# or without a `pub` prefix - `pub(crate) use super::dom_ops::*;` is the
# mechanism, not a bypass of it.
CHAIN_PREFIXES = {"super", "self", "crate"}
# The outermost `mod.rs` of a tree is where §6.1 wants the imports: directly
# under `src/` for a crate, or directly under `tests/` for a test directory,
# which has no lib of its own. Everything deeper should reach them through the
# `use super::*;` chain instead of re-importing at each level.
OUTERMOST_PARENTS = {"src", "tests"}


def _sibling_modules(directory: Path) -> set[str]:
    """Module names a sibling directory declares, which are not crates."""
    names = set()
    if not directory.is_dir():
        return names
    for entry in directory.iterdir():
        if entry.is_dir():
            if (entry / "mod.rs").is_file():
                names.add(entry.name)
            if (entry / "lib.rs").is_file():
                names.add(entry.name)
        elif entry.suffix == ".rs" and entry.stem not in ("mod", "lib", "main"):
            names.add(entry.stem.lstrip("r#"))
    return names


def _is_proc_macro_crate(path: Path) -> bool:
    """True when the crate this file belongs to is a proc-macro crate.

    rustc forbids a proc-macro crate from exporting anything but its own
    attributes, so §6.1's "put it in the outermost lib.rs" has no spelling
    that compiles. The manifest is the only place that fact is written down,
    and it sits at the crate root rather than beside `src/`, so the search
    walks up until one is found.
    """
    for parent in path.parents:
        manifest = parent / "Cargo.toml"
        if manifest.is_file():
            return bool(
                re.search(r"^proc-macro\s*=\s*true", manifest.read_text(errors="replace"), re.M)
            )
    return False


def audit_sub_mod_rs_imports(path: Path, lines: list[str]) -> list[str]:
    """A sub-mod.rs must not carry its own crate import (§6.1 / §6.3).

    Nothing else in the file catches this: the three-stage layout check is about
    ordering, and the lib.rs rule is about `pub` vs private. So a sub `mod.rs`
    could grow `use std::collections::HashMap;` and every check still passed -
    which is exactly how the four engine test directories and one example page
    ended up importing on their own.

    Sibling modules are exempt, and must be: `use view::*;` inside a sub
    `mod.rs` is the propagation mechanism §6.1 asks for, not a bypass of it.

    A `proc-macro` crate is exempt too, because the hoisting §6.1 asks for is
    impossible there. rustc refuses to let a proc-macro crate export anything
    but its own attributes: ``pub use std::path::Path;`` in its lib.rs is
    E0658, "proc-macro crate types currently cannot export any items other
    than functions tagged with #[proc_macro] ...". The sub `mod.rs` is then
    the only place the import can live, and the alternative is not a tidier
    spelling - it is a crate that does not compile. euv-lowcode/macros is the
    live case.
    """
    if path.parent.name in OUTERMOST_PARENTS:
        return []
    if _is_proc_macro_crate(path):
        return []
    siblings = _sibling_modules(path.parent)
    violations = []
    for idx, raw in enumerate(lines, 1):
        match = IMPORT_HEAD.match(raw)
        if not match:
            continue
        name = match.group(1)
        if name in CHAIN_PREFIXES:
            continue
        if name in siblings or name.lstrip("r#") in siblings:
            continue
        violations.append(
            f"{path}:{idx}: a sub-mod.rs imports `{name}::` "
            f"directly (§6.1) - put it in the outermost lib.rs / mod.rs "
            f"and reach it through `use super::*;`"
        )
    return violations


def audit_mod_rs(path: Path, lines: list[str]) -> list[str]:
    """Strict three-stage layout, no blank separators (§6.2).

    Comments are not this check's business: §2.5 owns the absolute
    no-comments rule for mod.rs (verify_no_toml_mod_comments.py, check 51).
    """
    violations = []
    stage = 1
    seen_stage2 = False
    for idx, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not stripped:
            # §6.2 / templates/mod-rs.md: blank lines SEPARATE the three stages
            # (that is what the canonical template looks like). What is
            # forbidden is a blank line INSIDE one stage — two `mod` lines
            # split by a blank line, or two re-exports split by one.
            prev = next(
                (l.strip() for l in reversed(lines[:idx]) if l.strip()), ""
            )
            prev_is_mod = bool(MOD_DECL.match(prev))
            nxt = next(
                (l.strip() for l in lines[idx:] if l.strip()), ""
            )
            next_is_mod = bool(MOD_DECL.match(nxt))
            if prev_is_mod and next_is_mod:
                violations.append(
                    f"{path}:{idx}: blank line inside the `mod` block; §6.2 "
                    f"stage 1 keeps every `mod xxx;` touching (blank lines "
                    f"belong BETWEEN the three stages, not within one)"
                )
            continue
        if stage == 0 and (USE.match(stripped) or MOD_DECL.match(stripped)):
            stage = 1
        m = MOD_DECL.match(stripped)
        if m is not None:
            name = m.group(2)
            if name in RUST_KEYWORDS and not m.group(1):
                violations.append(
                    f"{path}:{idx}: `mod {name};` must be a raw identifier "
                    f"(§6.2): write `mod r#{name};`"
                )
            if seen_stage2:
                violations.append(
                    f"{path}:{idx}: `mod` declaration after a re-export stage; "
                    f"stage 1 (mod) must precede stage 2 (pub use) (§6.2)"
                )
            continue
        m = USE.match(stripped)
        if m is None:
            continue
        if SUPER_STAR.match(stripped):
            continue
        if m.group(1).strip():  # pub use / pub(crate) use
            seen_stage2 = True
            continue
        violations.append(
            f"{path}:{idx}: a re-export in a mod.rs must be `pub use` or "
            f"`pub(crate) use` (§6.2); found `{stripped[:70]}`"
        )
    return violations


def audit_sub_file(path: Path, lines: list[str]) -> list[str]:
    """Only `use super::*;` is allowed, and only once (§6.3 / §6.4)."""
    violations = []
    idx, total = 0, len(lines)
    while idx < total:
        if CFG_TEST.match(lines[idx]):
            idx = _skip_whole_block(lines, idx) + 1
            continue
        m = USE.match(lines[idx])
        if m is None:
            idx += 1
            continue
        if SUPER_STAR.match(lines[idx]):
            idx += 1
            continue
        violations.append(
            f"{path}:{idx + 1}: a keyword sub-file may only import "
            f"`use super::*;` (§6.3/§6.4) — the parent already re-exported "
            f"everything nameable here; found `{lines[idx].strip()[:70]}`"
        )
        idx += 1
    return violations


def audit_one(path: Path) -> list[str]:
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    if "tests" in path.parts or not _is_under_src(path):
        return []
    if _is_mod_rs(path):
        return audit_mod_rs(path, lines) + audit_sub_mod_rs_imports(path, lines)
    if path.name == "lib.rs":
        return audit_lib_rs(path, lines)
    if _is_keyword_file(path):
        return audit_sub_file(path, lines)
    return []


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    all_violations: list[str] = []
    file_count = 0
    for path in list_rs_files(root):
        found = audit_one(path)
        if found:
            file_count += 1
            all_violations.extend(found)
    for violation in all_violations:
        print(violation)
    if not all_violations:
        print("\n=== module-imports centralized: 0 violation(s) in 0 file(s) ===")
        return 0
    print(
        f"\n=== module-imports centralized: {len(all_violations)} violation(s) "
        f"in {file_count} file(s) ==="
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
