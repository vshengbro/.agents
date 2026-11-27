#!/usr/bin/env python3
"""§6.1 — lib.rs / mod.rs / main.rs module and import group order.

The order, as written in references/06-module-imports.md §6.1:

  1.  `mod xxx;`                      — normal sub-modules touching, no blank lines
  1.5 `#[cfg(test)] mod tests;`       — test modules AFTER all normal `mod`s,
                                        separated from normal `mod`s by EXACTLY
                                        one blank line (touching each other if
                                        multiple `#[cfg(test)]` modules exist)
  2.  `pub use {sub_module::*};`      — sub-module globs come FIRST
  3.  `pub use {external_crate::*};`  — then external-crate globs
  4.  `pub(crate) use`
  5.  `pub(super) use`
  6.  `use` (private), and inside it the sub-order is
        current crate -> standard library -> external crates
      a lone `use external::Symbol;` must be folded into the aggregated
      `use {...};` block rather than standing on its own line

Groups are separated by one blank line; within group 1 (normal `mod`) and
within group 1.5 (`#[cfg(test)] mod`) no internal blank line is allowed.
A blank line is MANDATORY whenever the visibility bucket changes
(mod -> cfg_test_mod -> pub -> pub(crate) -> pub(super) -> private): two decl
lines of different buckets touching without a blank line is a violation even
when the order is otherwise correct. Groups 2 and 3 share the `pub` bucket, so
no blank is required there. Between normal `mod` and `#[cfg(test)] mod`,
EXACTLY one blank line is required (0 or >= 2 blank lines are both violations).

Non-test `#[cfg(...)]` attributes (for example `#[cfg(target_os = "linux")]`
or `#[cfg(not(test))]` or `#[cfg(feature = "test")]`) stay in group 1 (normal
`mod`), not group 1.5.

Output contract: one violation per line, then `=== lib-rs import order: ...`
or `OK: 0 lib.rs/mod.rs/main.rs file(s) checked` (the audit's shell template
greps away `^=== ` and `^OK: 0 lib`).

Exit code: 0 = compliant, 1 = violations, 2 = usage error.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

ENTRY_FILENAMES = ("lib.rs", "mod.rs", "main.rs")

MOD_DECL = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+(r#)?\w+\s*;")
PRIV_USE = re.compile(r"^\s*use\s+(?!.*\bpub\b)")
PUB_USE = re.compile(r"^\s*pub\s+use\s+(.*?);\s*$")
PUB_CRATE_USE = re.compile(r"^\s*pub\(crate\)\s+use\b")
PUB_SUPER_USE = re.compile(r"^\s*pub\(super\)\s+use\b")
COMMENT = re.compile(r"^\s*(//|/\*)")
LONE_EXTERNAL = re.compile(r"^\s*use\s+([a-z_][a-z0-9_]*)::[A-Za-z_]")
CFG_HEAD = re.compile(r"^cfg\s*\(")
TEST_PREDICATE = re.compile(r"\btest\b")

GROUP_MOD = 1
GROUP_CFG_TEST_MOD = 1.5
GROUP_PUB_LOCAL = 2
GROUP_PUB_EXTERNAL = 3
GROUP_PUB_CRATE = 4
GROUP_PUB_SUPER = 5
GROUP_PRIVATE = 6

BUCKET_OF: dict[float, str] = {
    GROUP_MOD: "mod",
    GROUP_CFG_TEST_MOD: "cfg_test_mod",
    GROUP_PUB_LOCAL: "pub",
    GROUP_PUB_EXTERNAL: "pub",
    GROUP_PUB_CRATE: "pub(crate)",
    GROUP_PUB_SUPER: "pub(super)",
    GROUP_PRIVATE: "private",
}


def list_entry_files(root: Path) -> list[Path]:
    result = subprocess.run(
        [
            "find",
            str(root),
            "(",
            "-name",
            "lib.rs",
            "-o",
            "-name",
            "mod.rs",
            "-o",
            "-name",
            "main.rs",
            ")",
            "-not",
            "-path",
            "*/target/*",
            "-not",
            "-path",
            "*/.cargo/registry/*",
            "-not",
            "-path",
            "*/.git/*",
            "-not",
            "-path",
            "*/.worktrees/*",
        ],
        capture_output=True,
        text=True,
    )
    return sorted(Path(line) for line in result.stdout.splitlines() if line.strip())


def _dependency_roots(lib_rs: Path) -> set[str]:
    """Crate names declared in the nearest Cargo.toml."""
    roots: set[str] = set()
    manifest: Optional[Path] = None
    for parent in lib_rs.parents:
        candidate = parent / "Cargo.toml"
        if candidate.is_file():
            manifest = candidate
            break
    if manifest is None:
        return roots
    try:
        text = manifest.read_text()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {manifest}: {exc}", file=sys.stderr)
        return roots
    in_deps = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("["):
            in_deps = line in (
                "[dependencies]",
                "[dev-dependencies]",
                "[build-dependencies]",
                "[workspace.dependencies]",
            ) or line.startswith("[target.")
            continue
        if not in_deps or not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        name = line.split("=", 1)[0].strip().strip('"')
        if name and not name.startswith("["):
            roots.add(name)
            roots.add(name.replace("-", "_"))
    roots.update({"std", "core", "alloc"})
    return roots


def _root_segments(body: str) -> set[str]:
    """Leading path segments of every item in a use body."""
    inner = body.strip()
    if inner.startswith("{"):
        inner = inner[1:-1] if inner.endswith("}") else inner[1:]
    segments: set[str] = set()
    for item in inner.split(","):
        item = item.strip().rstrip(";").strip()
        if not item:
            continue
        m = re.match(r"(?:r#)?([A-Za-z_][A-Za-z0-9_]*)", item)
        if m:
            segments.add(m.group(1))
    return segments


def _strip_quotes(text: str) -> str:
    """Replace double-quoted string literals so `feature = "test"` never matches `test`."""
    out: list[str] = []
    in_str = False
    escaped = False
    for ch in text:
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def _strip_not_clauses(expr: str) -> str:
    """Remove balanced `not(...)` sub-expressions from a `cfg(...)` predicate."""
    while True:
        m = re.search(r"\bnot\s*\(", expr)
        if not m:
            return expr
        start = m.start()
        depth = 0
        pos = m.end() - 1
        end = len(expr)
        while pos < len(expr):
            ch = expr[pos]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = pos + 1
                    break
            pos += 1
        expr = expr[:start] + " " + expr[end:]


def _extract_attr_bodies(attr_text: str) -> list[str]:
    """Extract inner texts of balanced outer `#[...]` attributes (skipping `#![...]`)."""
    bodies: list[str] = []
    i = 0
    n = len(attr_text)
    while i < n:
        if attr_text[i : i + 2] == "#[":
            depth = 0
            in_str = False
            escaped = False
            j = i + 1
            while j < n:
                ch = attr_text[j]
                if in_str:
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == '"':
                        in_str = False
                else:
                    if ch == '"':
                        in_str = True
                    elif ch == "[":
                        depth += 1
                    elif ch == "]":
                        depth -= 1
                        if depth == 0:
                            bodies.append(attr_text[i + 2 : j].strip())
                            i = j + 1
                            break
                j += 1
            else:
                break
            continue
        i += 1
    return bodies


def is_cfg_test_attr(attr_text: str) -> bool:
    """Return True iff `attr_text` contains an outer `#[cfg(...)]` gating on `test`."""
    for body in _extract_attr_bodies(attr_text):
        m = CFG_HEAD.match(body)
        if not m:
            continue
        if not body.endswith(")"):
            continue
        payload = body[m.end() : -1]
        cleaned = _strip_not_clauses(_strip_quotes(payload))
        if TEST_PREDICATE.search(cleaned):
            return True
    return False


def split_leading_outer_attrs(stripped: str) -> tuple[list[str], str, int]:
    """Split leading `#[...]` outer attributes from `stripped`.

    Returns `(attrs, remainder, open_bracket_depth)`.
    When `open_bracket_depth > 0`, the final attribute continues onto subsequent lines.
    Inner attributes (`#![...]`) are not treated as outer attributes.
    """
    attrs: list[str] = []
    pos = 0
    n = len(stripped)
    while pos < n:
        while pos < n and stripped[pos].isspace():
            pos += 1
        if not stripped.startswith("#[", pos):
            break
        depth = 0
        in_str = False
        escaped = False
        j = pos + 1
        closed = False
        while j < n:
            ch = stripped[j]
            if in_str:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "[":
                    depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        attrs.append(stripped[pos : j + 1])
                        pos = j + 1
                        closed = True
                        break
            j += 1
        if not closed:
            attrs.append(stripped[pos:])
            return attrs, "", depth
    return attrs, stripped[pos:].strip(), 0


def _strip_comments_and_strings(line: str, in_block_comment: bool) -> tuple[str, bool]:
    """Return code tokens outside comments/strings plus updated block-comment state."""
    out: list[str] = []
    i = 0
    n = len(line)
    in_str = False
    escaped = False
    while i < n:
        if in_block_comment:
            if line[i : i + 2] == "*/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue
        if in_str:
            if escaped:
                escaped = False
            elif line[i] == "\\":
                escaped = True
            elif line[i] == '"':
                in_str = False
            i += 1
            continue
        if line[i : i + 2] == "//":
            break
        if line[i : i + 2] == "/*":
            in_block_comment = True
            i += 2
            continue
        if line[i] == '"':
            in_str = True
            i += 1
            continue
        out.append(line[i])
        i += 1
    return "".join(out), in_block_comment


def _classify(stripped: str, dep_roots: set[str], is_cfg_test: bool) -> Optional[float]:
    """Return the §6.1 group index of one top-level line, or None if not a decl."""
    if MOD_DECL.match(stripped):
        return GROUP_CFG_TEST_MOD if is_cfg_test else GROUP_MOD
    if PUB_CRATE_USE.match(stripped):
        return GROUP_PUB_CRATE
    if PUB_SUPER_USE.match(stripped):
        return GROUP_PUB_SUPER
    m = PUB_USE.match(stripped)
    if m is not None:
        segments = _root_segments(m.group(1))
        if not (segments & dep_roots):
            return GROUP_PUB_LOCAL
        return GROUP_PUB_EXTERNAL
    if PRIV_USE.match(stripped):
        return GROUP_PRIVATE
    return None


def _fmt_group(g: float) -> str:
    if g == GROUP_CFG_TEST_MOD:
        return "`#[cfg(test)]` mod"
    return f"group {int(g)}"


def audit_one(path: Path) -> list[str]:
    if path.name not in ENTRY_FILENAMES:
        return []
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    violations: list[str] = []
    dep_roots = _dependency_roots(path)
    group_counter = 0
    highest: float = 0
    prev_bucket: Optional[str] = None
    consecutive_blanks = 0
    pending_attrs: list[str] = []
    pending_attr_blanks = 0
    attr_bracket_depth = 0
    brace_depth = 0
    in_block_comment = False

    for idx, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if in_block_comment:
            _, in_block_comment = _strip_comments_and_strings(raw, in_block_comment)
            continue
        if not stripped:
            if brace_depth == 0 and attr_bracket_depth == 0:
                group_counter += 1
                consecutive_blanks += 1
            continue
        if COMMENT.match(stripped):
            _, in_block_comment = _strip_comments_and_strings(raw, in_block_comment)
            continue
        if attr_bracket_depth > 0:
            pending_attrs.append(stripped)
            code_part, in_block_comment = _strip_comments_and_strings(raw, in_block_comment)
            attr_bracket_depth += code_part.count("[") - code_part.count("]")
            if attr_bracket_depth < 0:
                attr_bracket_depth = 0
            continue
        if brace_depth > 0:
            code_part, in_block_comment = _strip_comments_and_strings(raw, in_block_comment)
            brace_depth += code_part.count("{") - code_part.count("}")
            if brace_depth < 0:
                brace_depth = 0
            continue
        if stripped.startswith("#!["):
            # Crate-level inner attribute: ignore for outer-attribute attachment.
            pending_attrs = []
            consecutive_blanks = 0
            code_part, in_block_comment = _strip_comments_and_strings(raw, in_block_comment)
            brace_depth += code_part.count("{") - code_part.count("}")
            continue

        inline_attrs, remainder, open_depth = split_leading_outer_attrs(stripped)
        if inline_attrs:
            if not pending_attrs:
                pending_attr_blanks = consecutive_blanks
            pending_attrs.extend(inline_attrs)
            consecutive_blanks = 0
            if open_depth > 0:
                attr_bracket_depth = open_depth
                continue
            if not remainder:
                continue
            decl_text = remainder
            blanks_before = pending_attr_blanks
            attr_blob = "\n".join(pending_attrs)
            pending_attrs = []
            pending_attr_blanks = 0
        else:
            decl_text = stripped
            if pending_attrs:
                blanks_before = pending_attr_blanks
                attr_blob = "\n".join(pending_attrs)
                pending_attrs = []
                pending_attr_blanks = 0
            else:
                blanks_before = consecutive_blanks
                attr_blob = ""
            consecutive_blanks = 0

        is_cfg_test = bool(attr_blob) and is_cfg_test_attr(attr_blob)
        g = _classify(decl_text, dep_roots, is_cfg_test)

        code_part, in_block_comment = _strip_comments_and_strings(raw, in_block_comment)
        brace_depth += code_part.count("{") - code_part.count("}")
        if brace_depth < 0:
            brace_depth = 0

        if g is None:
            m = LONE_EXTERNAL.match(decl_text)
            if m and group_counter >= 6:
                nxt = next(
                    (k for k in range(idx, len(lines)) if lines[k].strip()), None
                )
                if nxt is None or not lines[nxt].strip().startswith("use {"):
                    violations.append(
                        f"{path}:{idx}: a lone `use {m.group(1)}::Symbol;` must be "
                        f"folded into the aggregated `use {{...}};` block (§6.1 "
                        f"group 6): {decl_text[:70]}"
                    )
            continue

        bucket = BUCKET_OF[g]

        if prev_bucket == "mod" and bucket == "mod" and blanks_before > 0:
            violations.append(
                f"{path}:{idx}: blank line inside the `mod` block; "
                f"§6.1 group 1 keeps every `mod xxx;` touching"
            )
        elif prev_bucket == "cfg_test_mod" and bucket == "cfg_test_mod" and blanks_before > 0:
            violations.append(
                f"{path}:{idx}: blank line inside the `#[cfg(test)]` `mod` block; "
                f"keep `#[cfg(test)]` modules touching (§6.1)"
            )
        elif prev_bucket == "mod" and bucket == "cfg_test_mod":
            if blanks_before == 0:
                violations.append(
                    f"{path}:{idx}: `mod` group and `#[cfg(test)]` module touch "
                    f"without a blank line; `#[cfg(test)]` modules must appear after "
                    f"normal `mod` declarations separated by exactly one blank line "
                    f"(§6.1): {decl_text[:70]}"
                )
            elif blanks_before > 1:
                violations.append(
                    f"{path}:{idx}: `#[cfg(test)]` module separated from normal `mod` "
                    f"declarations by {blanks_before} blank lines; must be separated "
                    f"by exactly one blank line (§6.1): {decl_text[:70]}"
                )
        elif prev_bucket is not None and bucket != prev_bucket and blanks_before == 0:
            violations.append(
                f"{path}:{idx}: `{prev_bucket}` group and `{bucket}` group touch "
                f"without a blank line; different visibility levels must be "
                f"separated by one blank line (§6.1): {decl_text[:70]}"
            )

        if g < highest:
            if g == GROUP_MOD and highest == GROUP_CFG_TEST_MOD:
                violations.append(
                    f"{path}:{idx}: normal `mod` appears after `#[cfg(test)]` module; "
                    f"`#[cfg(test)]` modules must appear after all normal `mod` "
                    f"declarations separated by one blank line (§6.1): {decl_text[:70]}"
                )
            elif g == GROUP_CFG_TEST_MOD:
                violations.append(
                    f"{path}:{idx}: `#[cfg(test)]` module appears after "
                    f"{_fmt_group(highest)}; place `#[cfg(test)]` modules after normal "
                    f"`mod` declarations separated by one blank line (§6.1): "
                    f"{decl_text[:70]}"
                )
            else:
                violations.append(
                    f"{path}:{idx}: import {_fmt_group(g)} appears after "
                    f"{_fmt_group(highest)} (§6.1 order is mod -> #[cfg(test)] mod -> "
                    f"pub use local -> pub use external -> pub(crate) -> pub(super) -> "
                    f"private): {decl_text[:70]}"
                )

        highest = max(highest, g)
        prev_bucket = bucket

    return violations


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    libs = list_entry_files(root)
    all_violations: list[str] = []
    for path in libs:
        all_violations.extend(audit_one(path))
    for violation in all_violations:
        print(violation)
    if all_violations:
        print(
            f"\n=== lib-rs import order: {len(all_violations)} violation(s) "
            f"in {len(libs)} lib.rs/mod.rs/main.rs file(s) ==="
        )
        return 1
    print(
        f"\nOK: {len(libs)} lib.rs/mod.rs/main.rs file(s) checked, no group-order violation"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
