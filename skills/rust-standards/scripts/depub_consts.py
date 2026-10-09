#!/usr/bin/env python3
"""De-publish constants (2026-10-07 user: "常量是肯定不需要pub的").

For every column-0 `pub const` / `pub static` in src/, classify its readers
and converge mechanically:

  readers = none                       -> DELETE the declaration
  readers subset same-crate tests/     -> inline the value at test use sites
                                          (small literals) or copy the decl
                                          into tests/<sub>/const.rs (big),
                                          decl -> pub(crate)
  readers += own-crate src/main.rs     -> additionally copy a private decl
                                          into main.rs, decl -> pub(crate)
  readers include other-crate src      -> report only (manual list)

Substitution is position-aware: string/char literals in each line are
blanked before matching, so `"EUV_ARGS"` inside an assert message is never
rewritten. Whole-word matches only. A declaration file that re-declares the
same constant name is a shadow, not a consumer.

Default dry-run; --write applies. Idempotent.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PUBC = re.compile(
    r"^pub\s+(?P<kind>const|static)\s+(?P<name>[A-Za-z_]\w*)\s*:\s*(?P<ty>[^=]+)=\s*(?P<val>.+?);?\s*$"
)
DECL_ANY = re.compile(r"^(?:pub(?:\(crate\))?\s+)?(?:const|static)\s+([A-Za-z_]\w*)")
STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
CHAR_RE = re.compile(r"'(?:\\.|[^'\\])'")
SKIP_DIRS = {"target", ".git", "node_modules"}
SMALL_VAL = re.compile(
    r"^(?:b?'[^']*'|b?\"[^\"]*\"|r#*\".*\"#*|-?[\d._a-zA-Z]+(?:::consts::[A-Z]+)?|true|false)$"
)
MAX_SMALL = 40


def _blank(line: str) -> str:
    line = STRING_RE.sub(lambda m: " " * len(m.group(0)), line)
    return CHAR_RE.sub(lambda m: " " * len(m.group(0)), line)


def _iter_rs(root: Path):
    for p in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def _crate_of(path: Path, crates: list[Path]) -> Path | None:
    best = None
    for c in crates:
        try:
            path.relative_to(c)
        except ValueError:
            continue
        if best is None or len(c.parts) > len(best.parts):
            best = c
    return best


def _is_tests(path: Path, crate: Path) -> bool:
    try:
        rel = path.relative_to(crate)
    except ValueError:
        return False
    return bool(rel.parts) and rel.parts[0] == "tests"


def _is_internal_src(path: Path, crate: Path) -> bool:
    try:
        rel = path.relative_to(crate)
    except ValueError:
        return False
    if not rel.parts or rel.parts[0] != "src":
        return rel.parts == ("build.rs",)
    if len(rel.parts) >= 2 and rel.parts[1] == "bin":
        return False
    if rel == Path("src/main.rs") and (crate / "src/lib.rs").is_file():
        return False
    return True


def substitute(path: Path, name: str, value: str) -> int:
    """Replace whole-word uses of `name` with `value`, skipping literals."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    n = 0
    word = re.compile(rf"\b{re.escape(name)}\b")
    for i, line in enumerate(lines):
        blanked = _blank(line)
        hits = list(word.finditer(blanked))
        if not hits:
            continue
        for m in reversed(hits):
            line = line[: m.start()] + value + line[m.end() :]
            n += 1
        lines[i] = line
    if n:
        path.write_text("".join(lines), encoding="utf-8")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    crates = [p.parent for p in sorted(root.rglob("Cargo.toml"))
              if not any(part in SKIP_DIRS for part in p.parts)]
    texts = {}
    for p in _iter_rs(root):
        try:
            texts[p] = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            pass
    crate_of = {p: _crate_of(p, crates) for p in texts}
    file_idents = {}
    for p, t in texts.items():
        stripped = "\n".join(re.sub(r"//[^\n]*", "", _blank(l)) for l in t.splitlines())
        file_idents[p] = set(re.findall(r"[A-Za-z_]\w*", stripped))

    deleted: list[str] = []
    inlined: list[str] = []
    copied_main: list[str] = []
    depubed: list[str] = []
    manual: list[str] = []
    skipped_val: list[str] = []

    for decl, text in sorted(texts.items()):
        crate = crate_of[decl]
        if crate is None or not _is_internal_src(decl, crate):
            continue
        lines = text.splitlines(keepends=True)
        for idx, line in enumerate(lines):
            m = PUBC.match(line)
            if not m:
                continue
            name = m.group("name")
            val = m.group("val").rstrip(";").strip()
            readers = []
            for q, idents in file_idents.items():
                if q is decl or name not in idents:
                    continue
                # a file that declares the same name is a shadow, not a reader
                if any(DECL_ANY.match(l) and DECL_ANY.match(l).group(1) == name
                       for l in texts[q].splitlines()):
                    continue
                readers.append(q)
            same_tests = [q for q in readers if _is_tests(q, crate_of[q]) and crate_of[q] == crate]
            own_main = [q for q in readers if q == crate / "src/main.rs" and not _is_internal_src(q, crate)]
            foreign = [q for q in readers if crate_of[q] != crate]
            rel = decl.relative_to(root)
            if not readers:
                deleted.append(f"{rel}:{idx + 1} {name}")
                if args.write:
                    del lines[idx]
                    texts[decl] = "".join(lines)
                    decl.write_text(texts[decl], encoding="utf-8")
                continue
            if foreign:
                manual.append(
                    f"{rel}:{idx + 1} {name} <- "
                    f"{[str(q.relative_to(root)) for q in foreign][:4]}"
                )
                continue
            small = len(val) <= MAX_SMALL and SMALL_VAL.match(val) and name not in val
            if not small:
                skipped_val.append(f"{rel}:{idx + 1} {name} (value too big to inline: {len(val)} chars)")
                continue
            if args.write:
                total = 0
                for q in same_tests:
                    total += substitute(q, name, val)
                if own_main:
                    main_text = (crate / "src/main.rs").read_text(encoding="utf-8")
                    decl_line = f"{m.group('kind')} {name}: {m.group('ty').strip()} = {val};\n"
                    if name not in main_text.split(" = ", 1)[0] or decl_line not in main_text:
                        # insert after the last use line block
                        main_lines = main_text.splitlines(keepends=True)
                        insert_at = 0
                        for k, ml in enumerate(main_lines):
                            if ml.startswith("use ") or ml.startswith("#!"):
                                insert_at = k + 1
                        main_lines.insert(insert_at, "\n" + decl_line)
                        (crate / "src/main.rs").write_text("".join(main_lines), encoding="utf-8")
                        copied_main.append(f"{name} -> {crate.name}/src/main.rs")
                lines[idx] = re.sub(r"^pub\s+", "pub(crate) ", line, count=1)
                texts[decl] = "".join(lines)
                decl.write_text(texts[decl], encoding="utf-8")
                inlined.append(f"{rel}:{idx + 1} {name} (tests sites: {len(same_tests)})")
                depubed.append(name)
            else:
                inlined.append(f"{rel}:{idx + 1} {name} (would inline into {len(same_tests)} tests files)")

    for tag, bucket in (("deleted", deleted), ("inlined+depubed", inlined),
                        ("copied-to-main", copied_main), ("manual-cross-src", manual),
                        ("skipped-big-value", skipped_val)):
        for line in bucket:
            print(f"  {tag}: {line}")
        if bucket:
            print(f"=== {tag}: {len(bucket)} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
