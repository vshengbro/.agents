#!/usr/bin/env python3
"""Enforce the two lombok accessor rules that have no script yet.

Background (rust-standards §17.14 / §17.8.1, both user-ratified
2026-10-13 against lombok-macros 10.2.4):

  Rule A — copy
      Lombok's default getter returns `&T`. For Copy primitives that
      means every call site needs `*`. The rule is: a primitive field
      MUST carry `#[get(type(copy))]` so the getter returns `T`.

  Rule B — visibility
      `lombok_macros::Visibility` defaults to `Public`, so a derive
      emits `pub fn get_x()` unless the field says otherwise. A field
      that is NOT `pub` (private / pub(crate) / pub(super)) MUST carry
      an explicit narrowing attribute, otherwise the accessor silently
      widens a crate-internal field into public API.

A field with NO `#[get(...)]` attribute is still checked: the derive
generates the accessor anyway, with all defaults. That is exactly the
case Rule B exists for.

Fields whose getter is opted out (`#[get(skip)]`) are exempt from both
rules — no accessor is generated, so there is nothing to narrow and
nothing to make cheap.

Both rules are per-field and need struct context (the derive list, the
field's own visibility, its type), so this walks items with a small
brace tracker and a pending-attribute buffer.

Read-only. Exits non-zero when any violation is present.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP_DIRS = {"target", ".git", "node_modules", ".cargo", "dist", "www"}

# Derives that generate accessors. Without one of these, `#[get(...)]`
# is the ONLY thing creating the accessor, so it is never redundant.
ACCESSOR_DERIVES = {"Getter", "GetterMut", "Setter", "Data"}

# Primitives where `&T` is pure noise at the call site. Deliberately
# excludes `&'static str` and other reference types — those belong to
# §17.8's `type(copy)`-vs-`type(deref)` discussion, not this rule.
COPY_PRIMITIVES = {
    "bool",
    "u8", "u16", "u32", "u64", "u128", "usize",
    "i8", "i16", "i32", "i64", "i128", "isize",
    "f32", "f64",
    "char",
}

# Every lombok accessor attribute that can own a visibility or type arg.
ACCESSOR_ATTR_RE = re.compile(r"#\[\s*(get|get_mut|set)\b([^\]]*)\]")
GET_ATTR_RE = re.compile(r"#\[\s*get\b([^\]]*)\]")
TYPE_ARG_RE = re.compile(r"\btype\s*\(")
VIS_ARG_RE = re.compile(r"\bpub\s*\(\s*(?:crate|super)\s*\)|\bprivate\b")
SKIP_ARG_RE = re.compile(r"\bskip\b")
DERIVE_RE = re.compile(r"#\[\s*derive\s*\(([^)]*)\)\s*\]", re.S)
STRUCT_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?struct\s+(\w+)\b")
# Matches BOTH `pub struct` and `pub(crate) struct` / `pub(super) struct`.
# The optional paren group must be allowed to match nothing, otherwise
# plain `pub struct` falls through and every struct looks module-private.
STRUCT_PUB_RE = re.compile(r"^\s*pub(?:\s|\()")
FIELD_RE = re.compile(
    r"^(?:(pub(?:\(\s*(?:crate|super)\s*\))?)\s+)?([A-Za-z_]\w*)\s*:\s*([^,]+?),?\s*$"
)


def _bare_type(declared: str) -> str:
    """Strip generics so `Option<T>` / `Vec<T>` compare as text."""
    ty = declared.strip().rstrip(",").strip()
    return re.sub(r"<.*>$", "", ty).strip()


def _derive_has_accessor(names: str) -> bool:
    """True when the derive list contains an accessor-generating derive.

    Tolerates path-qualified derives, which is how a crate that re-exports
    the macros spells them:

        #[derive(Data)]                 -> Data
        #[derive(lombok_macros::Data)]  -> Data
        #[derive(euv::Data, Clone)]     -> Data
    """
    for part in names.split(","):
        ident = part.strip().split("::")[-1].strip()
        if ident in ACCESSOR_DERIVES:
            return True
    return False


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    out: list[str] = []
    last_derive = ""
    in_struct = False
    struct_is_pub = False
    brace_depth = 0
    pending: list[str] = []

    for idx, raw in enumerate(lines):
        line_no = idx + 1
        stripped = raw.strip()

        # Comments can never carry a field or an attribute.
        if stripped.startswith("//"):
            continue

        d = DERIVE_RE.search(stripped)
        if d:
            last_derive = d.group(1)

        sm = STRUCT_RE.match(stripped)
        if sm and not stripped.endswith(";"):
            in_struct = _derive_has_accessor(last_derive)
            struct_is_pub = bool(STRUCT_PUB_RE.match(stripped))
            brace_depth = 0
            pending = []

        if in_struct:
            if stripped.startswith("#["):
                pending.append(stripped)
                continue

            fm = FIELD_RE.match(stripped)
            if fm:
                field_vis = fm.group(1) or "private"
                field_name = fm.group(2)
                field_type = _bare_type(fm.group(3))
                attrs = " ".join(pending)

                get_args = GET_ATTR_RE.search(attrs)
                # All attribute args combined: a field may split its
                # config across lines, e.g.
                #     #[get(type(copy))]
                #     #[get(pub(crate))]
                # either order, either style.
                combined = " ".join(
                    m.group(2) for m in ACCESSOR_ATTR_RE.finditer(attrs)
                )
                # Opt-out only counts when the skip is on THIS field's
                # `get`. (Attrs are only collected directly above the
                # field they belong to.)
                getter_skipped = bool(
                    get_args and SKIP_ARG_RE.search(get_args.group(1))
                )
                # Rule A only applies when a getter is actually
                # generated. `#[derive(Getter)]` without `Data` does
                # generate one, so it still counts; a struct with no
                # accessor derive at all is exempt (nothing generated
                # unless the attribute says otherwise).
                if in_struct and not getter_skipped:
                    # Rule A — Copy primitive must opt into `type(copy)`.
                    if field_type in COPY_PRIMITIVES and not TYPE_ARG_RE.search(combined):
                        out.append(
                            f"{path}:{line_no}: Copy primitive field "
                            f"`{field_name}` has no `#[get(type(copy))]` — "
                            f"lombok emits `fn get_{field_name}(&self) -> &T`, "
                            f"forcing `*` at every call site "
                            f"(rust-standards §17.8.1)"
                        )

                    # Rule B — non-pub field must narrow visibility.
                    #
                    # Only meaningful when the struct itself is `pub`:
                    # an accessor on a module-private struct is already
                    # unreachable from outside, so a `pub` fn there
                    # widens nothing. Flagging those would report the
                    # whole tree for a leak that cannot happen.
                    if (
                        field_vis != "pub"
                        and struct_is_pub
                        and not VIS_ARG_RE.search(combined)
                    ):
                        out.append(
                            f"{path}:{line_no}: field `{field_name}` is "
                            f"`{field_vis}` but its lombok attribute does not "
                            f"narrow visibility — accessors default to `pub`, "
                            f"silently widening the field "
                            f"(rust-standards §17.14)"
                        )

                pending = []
                continue

            if stripped:
                # Any other content ends the attribute run.
                pending = []

        if in_struct:
            brace_depth += stripped.count("{") - stripped.count("}")
            if brace_depth <= 0:
                in_struct = False
                brace_depth = 0
                pending = []

    return out


def iter_rust_files(root: Path):
    for path in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def audit_one(path: Path) -> list[str]:
    """Per-file entry point used by `staged_file_gate.py`.

    The gate imports this module and calls `audit_one` directly instead of
    shelling out, so a verifier without it is silently skipped (it returns
    an empty list, which reads as "0 violations"). Keep this name.
    """
    return check_file(path)


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: verify_lombok_accessor_contract.py <repo_root>", file=sys.stderr
        )
        return 2
    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    files = list(iter_rust_files(root))
    violations: list[str] = []
    for path in files:
        violations.extend(check_file(path))

    for line in violations:
        print(line)

    print(
        f"=== lombok-accessor-contract: {len(files)} files checked, "
        f"{len(violations)} violations"
    )
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())