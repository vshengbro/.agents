#!/usr/bin/env python3
"""
Verify no panicking lombok accessor is called on a bare `Option<T>` field.

rust-standards: `#[derive(Data)]` on a field of type `Option<T>` generates

    pub fn get_x(&self) -> T { self.x.clone().unwrap() }   // panics on None
    pub fn try_get_x(&self) -> T { self.x.clone() }        // safe

Rule: any `Option<T>` field that is allowed to be `None` MUST be read through
`try_get_*`. `get_*` is only legal on non-`Option` fields (or when the caller
has already proven the value is `Some`).

Why a static scan is not enough: field names collide across unrelated types.
`get_min()` exists on both `Counter` (`min: Option<i32>`, panics) and `AABB3D`
(`min: Vector3D`, safe). Name-based matching reports ~180 false hits. So this
verifier does NOT do name matching — it parses the actual struct declarations
and only reports a call when BOTH the declaring type and the call-site receiver
can be resolved.

Usage:
    python3 verify_no_panicking_option_getter.py <repo>

Exit 0 = clean, 1 = violations found.
"""

import re
import sys
from pathlib import Path
from typing import Optional

STRUCT_RE = re.compile(
    r"#\[derive\((?P<derives>[^)]*Data[^)]*)\)\]\s*\n"
    r"(?:#\[[^\]]*\]\s*\n)*"
    r"pub struct (?P<name>\w+)\s*\{(?P<body>.*?)\n\}",
    re.S,
)
FIELD_RE = re.compile(
    r"pub(?:\(crate\))? (?P<fld>\w+): (?P<ty>Option<[^;\n]+?>),"
)
# `impl Foo {` at column 0, or `impl<...> Foo {`
IMPL_RE = re.compile(r"^impl(?:<[^>]*>)? ([\w:]+) \{", re.M)
CALL_RE = re.compile(r"(?<![a-zA-Z_])get_(\w+)\(\)")


def collect_option_fields(repo: Path) -> dict[str, tuple[str, str]]:
    """field name -> (owning struct, declared type) for bare Option fields."""
    out: dict[str, tuple[str, str]] = {}
    for path in repo.rglob("*.rs"):
        if "/target/" in str(path):
            continue
        text = path.read_text(errors="ignore")
        for m in STRUCT_RE.finditer(text):
            for f in FIELD_RE.finditer(m.group("body")):
                fld, ty = f.group("fld"), f.group("ty")
                # `Option<Signal<T>>` and friends are still bare Option and
                # still panic; only `Signal<Option<T>>` (a Signal wrapping an
                # Option) is safe, and that never matches `Option<...>` here.
                out[fld] = (m.group("name"), ty)
    return out


def enclosing_impl(lines, idx) -> Optional[str]:
    for i in range(idx, -1, -1):
        m = IMPL_RE.match(lines[i])
        if m:
            return m.group(1)
        if re.match(r"^\}", lines[i]) and i != idx:
            return None
    return None


def receiver_type(lines, idx) -> Optional[str]:
    """Best-effort receiver type for `X.get_y()` on line `idx`."""
    line = lines[idx]
    m = re.search(r"(\w+)\.get_(\w+)\(\)", line)
    if not m:
        return None
    recv, getter = m.group(1), m.group(2)
    if recv == "self":
        return enclosing_impl(lines, idx)
    # `let <recv>: <Type> = ...` anywhere above
    pat = re.compile(rf"\blet\s+{re.escape(recv)}\s*:\s*&?([\w:]+)")
    for i in range(idx, -1, -1):
        pm = pat.search(lines[i])
        if pm:
            return pm.group(1)
    # `let <recv> = <Type> {`
    pat2 = re.compile(rf"\blet\s+{re.escape(recv)}\s*=\s*([\w:]+)\s*\{{")
    for i in range(idx, -1, -1):
        pm = pat2.search(lines[i])
        if pm:
            return pm.group(1)
    # A function parameter `fn f(&self_, or x: &Type)` on the enclosing line
    # or any line up to the enclosing `fn` — covers `fn p(s: &SceneManager)`.
    fn_pat = re.compile(
        rf"(?:^|\(|,)\s*&?(?:mut\s+)?{re.escape(recv)}\s*:\s*&?([\w:]+)"
    )
    for i in range(idx, -1, -1):
        if re.match(r"^\s*(pub(\([^)]*\))?\s+)?fn\s", lines[i]):
            pm = fn_pat.search(lines[i])
            if pm:
                return pm.group(1)
            return None
    return None


PRIMITIVE_COPY = {"i8", "i16", "i32", "i64", "i128", "isize",
                  "u8", "u16", "u32", "u64", "u128", "usize",
                  "f32", "f64", "bool", "char"}

# `#[derive(...)]` immediately above a `pub struct`, doc lines skipped.
_STRUCT_LINE = re.compile(r"pub struct (?P<name>\w+)\s*\{")
_DERIVE_LINE = re.compile(r"#\[derive\((?P<d>[^)]*)\)\]")
_BARE_OPT = re.compile(r"pub(?:\([^)]*\))?\s+(?P<fld>\w+)\s*:\s*Option<(?P<t>\w+)>")
_ATTR_LINE = re.compile(r"^\s*#!?\[")


def _copy_types(repo: Path) -> set[str]:
    """Every struct declared with `Copy`, plus the Copy primitives."""
    out = set(PRIMITIVE_COPY)
    for path in repo.rglob("*.rs"):
        if "/target/" in str(path):
            continue
        lines = path.read_text(errors="ignore").split("\n")
        for i, line in enumerate(lines):
            m = _STRUCT_LINE.search(line)
            if not m:
                continue
            j = i - 1
            while j >= 0 and lines[j].strip().startswith("///"):
                j -= 1
            if j >= 0:
                d = _DERIVE_LINE.search(lines[j])
                if d and "Copy" in d.group("d"):
                    out.add(m.group("name"))
    return out


def declaration_violations(repo: Path, only: Path = None) -> list[str]:
    """Report `Option<T>` fields whose public `get_*` would unwrap.

    The call-site scan above cannot see this class: a public panicking
    getter is reachable from outside the crate and panics even when the
    engine itself never calls it. Two real cases shipped that way —
    `GlRenderState::scissor` and `Counter::min`/`max`, both documented as
    "None means off / unbounded".

    Lombok only emits the unwrapping form for a `Copy` inner type (a
    non-Copy payload keeps `get_x() -> Option<T>`); `Option<Rc<dyn Fn>>`
    has 46 working call sites and must not be reported. The remedy is the
    annotation the rest of the codebase already uses:
    `#[get(type(copy))]`, which makes the getter return the Option.
    """
    copy_names = _copy_types(repo)
    found: list[str] = []
    # `only` restricts WHICH FILE the field scan reads, while the
    # Data-derive / Copy knowledge still comes from the whole repo. The
    # gate needs that split: it materialises a staged file beside the real
    # one to get a HEAD baseline, so re-scanning the working tree would make
    # before == after and the delta would always be 0.
    if only is not None:
        # `only` may arrive relative (hand-rolled call) or absolute (the
        # gate). Resolving against `repo` keeps the reported path in the
        # same `rel:line:` shape `audit_one` filters on — otherwise a
        # relative path degrades to its basename and every filter misses,
        # turning a real finding into a silent zero.
        if not only.is_absolute():
            only = (repo / only).resolve()
        candidates = [only]
    else:
        candidates = [p for p in sorted(repo.rglob("*.rs")) if "/target/" not in str(p)]
    for path in candidates:
        try:
            rel = path.relative_to(repo)
        except ValueError:
            rel = Path(path.name)
        try:
            lines = path.read_text(errors="ignore").split("\n")
        except OSError:
            continue
        owner, has_data = None, False
        for i, line in enumerate(lines):
            m = _STRUCT_LINE.search(line)
            if m:
                owner = m.group("name")
                # Each struct owns its own derive line. Carrying the flag over
                # from the previous struct would report `#[derive(Getter)]`
                # types as if they were lombok `Data` ones.
                has_data = False
                j = i - 1
                while j >= 0 and lines[j].strip().startswith("///"):
                    j -= 1
                if j >= 0:
                    d = _DERIVE_LINE.search(lines[j])
                    has_data = bool(d and "Data" in d.group("d"))
                continue
            f = _BARE_OPT.search(line)
            if not f or not has_data or owner is None:
                continue
            j = i - 1
            attrs = []
            while j >= 0 and (_ATTR_LINE.match(lines[j])
                              or lines[j].strip().startswith("///")):
                if _ATTR_LINE.match(lines[j]):
                    attrs.append(lines[j].strip())
                j -= 1
            if any(a.startswith("#[get") for a in attrs):
                continue
            if f.group("t") not in copy_names:
                continue
            found.append(
                f"{rel}:{i + 1}: {owner}::{f.group('fld')} is a public "
                f"Option<{f.group('t')}> with no #[get(...)] — the generated "
                f"get_{f.group('fld')}() unwraps and panics on None; add "
                f"#[get(type(copy))]"
            )
    return found


# The gate suffix staged_file_gate.py appends when it materialises the HEAD
# version of a staged file, so the baseline copy's name differs from the real
# one by exactly this.
GATE_SUFFIX = ".head-baseline"

def _infer_root(path: Path) -> Path:
    """Walk up to the directory holding `.git` (same convention as
    verify_no_production_panic._infer_root)."""
    for candidate in [path, *path.parents]:
        if (candidate / ".git").exists():
            return candidate
    return path.parent


def audit_one(path: Path, root: Optional[Path] = None) -> list[str]:
    """Per-file entry point used by staged_file_gate.

    Without it the gate's `getattr(module, "audit_one", None)` probe returns
    None and this rule is silently skipped at commit time -- exactly the gap
    that let bare `Option<Copy>` fields through the hook while the audit
    caught them.

    The rule cannot be judged from one file alone: whether a field is risky
    depends on the struct deriving lombok's `Data`, which lives in another
    file. So this runs the repo-wide scan and filters to `path`. Results are
    memoised per root because the gate calls it once per staged file.
    """
    if root is None:
        root = _infer_root(path)
    key = str(root)
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return []
    rel_str = str(rel)
    if rel_str.endswith(GATE_SUFFIX):
        rel_str = rel_str[: -len(GATE_SUFFIX)]
    # Read the fields from the GIVEN file (the staged copy or the
    # materialised HEAD baseline), not from the working tree, so the gate
    # sees a real before/after difference.
    found = declaration_violations(root, only=path)
    prefix = f"{rel_str}:"
    return [v for v in found if v.startswith(prefix)]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify_no_panicking_option_getter.py <repo>", file=sys.stderr)
        return 2
    repo = Path(sys.argv[1]).resolve()
    option_fields = collect_option_fields(repo)

    violations: list[str] = []
    # Lombok only emits the panicking form when the accessor's declared return
    # type is the BARE inner type. If an accessor is declared
    # `#[get] pub x: Option<T>` -> `fn get_x(&self) -> Option<T> { self.x.clone() }`
    # it is safe. So a field is only risky if some accessor in the struct
    # returns the unwrapped type; `option_fields` keys on the *getter name*
    # and the declared return type is checked against the field type here.
    for path in repo.rglob("*.rs"):
        if "/target/" in str(path):
            continue
        rel = path.relative_to(repo)
        lines = path.read_text(errors="ignore").split("\n")
        for i, line in enumerate(lines):
            code = line.split("//", 1)[0]
            for m in CALL_RE.finditer(code):
                fld = m.group(1)
                if fld not in option_fields:
                    continue  # different type, not a Data Option field
                owner, ty = option_fields[fld]
                # If the call site immediately binds/patterns the result as an
                # Option (`let x: Option<T> = ...`, `if let Some(..) = ...`,
                # `match .. { Some(..) => .. }`) the getter cannot be the
                # panicking bare-type form.
                if re.search(rf"Option<\s*{re.escape(ty[7:-1] if ty.endswith('>') else ty[7:])}\s*>", code):
                    continue
                # `match self.get_x() { Some(..) => .. None => .. }` and
                # `let x = self.get_x(); if let Some(..) = x { .. }` span lines,
                # so scan a small window around the call, not just its own line.
                window = "\n".join(lines[i : i + 4])
                if re.search(
                    r"Some\(|None\s*=>|is_none\(\)|is_some\(\)|\.as_ref\(\)|"
                    r"\.unwrap_or",
                    window,
                ):
                    continue
                # A bare `Option<` in the WINDOW is not evidence the getter is
                # safe — the enclosing fn's own return type often is
                # `Option<..>`. Only the text BEFORE the call on the same
                # statement counts (`let x: Option<T> = e.get_f()`).
                head = code[: m.start(1)]
                if re.search(r"Option<", head):
                    continue
                recv = receiver_type(lines, i)
                # A call compared against `None` proves the getter returns the
                # Option: `assert_eq!(sampler.get_compare(), None)` only
                # compiles if `get_compare` yields `Option<CompareFunction>`.
                # This is a sound exemption, not a loosened heuristic - the
                # unwrapping form would make the call site a type error.
                tail = code[m.end(1):] + "\n" + "\n".join(lines[i + 1: i + 3])
                if re.search(
                    r"(==|!=)\s*None\b|,\s*None\s*[,)]|None\s*,", tail
                ):
                    continue
                # Only report when we can PROVE the receiver is the owning type.
                if recv is None or recv.split("::")[-1] != owner.split("::")[-1]:
                    continue
                violations.append(
                    f"{rel}:{i + 1}: {recv}::get_{fld}() panics on None "
                    f"(field `{fld}: {ty}`) — use try_get_{fld}()"
                )

    violations.extend(declaration_violations(repo))

    if violations:
        print(
            f"=== panicking-getter-on-Option: {len(violations)} violation(s) ==="
        )
        for v in violations:
            print("  " + v)
        return 1
    print("=== panicking-getter-on-Option: 0 violation(s) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
