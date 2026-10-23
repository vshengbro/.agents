#!/usr/bin/env python3
"""Accessor-derive shape rules (rust-standards §17.16 and §17.16.1).

Two rules live here because they are the two ends of the same question —
"which accessor derive does THIS struct actually need?" — and they share one
parser. Both bind their verdict to an exact item: the derive list is read off
the attribute run that sits directly in front of the `struct` keyword, and the
field attributes are read off the run that sits directly in front of each
field. A struct's derive list can never leak into its neighbour.

RULE 1 — the spelled-out trio (§17.16, user-ratified 2026-10-14)
-------------------------------------------------------------
When a struct needs all three accessor kinds, `Data` IS the trio — one derive
instead of three. From lombok-macros 10.2.7 `src/lib.rs`:

    #[proc_macro_derive(Getter,    attributes(get))]       -> inner_lombok_data(input, true,  false, false)
    #[proc_macro_derive(GetterMut, attributes(get_mut))]  -> inner_lombok_data(input, false, true,  false)
    #[proc_macro_derive(Setter,    attributes(set))]      -> inner_lombok_data(input, false, false, true )
    #[proc_macro_derive(Data,      attributes(get, get_mut, set))]
                                                          -> inner_lombok_data(input, true,  true,  true )

Same generator, same three booleans, and `Data` declares the union of the
three helper attributes, so every `#[get(..)]` / `#[get_mut(..)]` /
`#[set(..)]` on the fields keeps working unchanged:

    #[derive(Clone, CustomDebug, Getter, GetterMut, Setter)]   <-- drop
    #[derive(Clone, CustomDebug, Data)]                        <-- keep

Two of the three are NOT a violation: `Getter + Setter` and
`GetterMut + Setter` have no combined derive, so those stay as they are.

Scoping:
  - struct items only. Enums and unions are rejected by the generator itself
    (`_ => panic!(UNSUPPORTED_DATA_DERIVE)` in `inner_lombok_data`), so no
    compilable code can carry the trio on them.
  - a derive list that ALREADY contains `Data` next to the trio is the same
    redundancy from the other side (and does not compile — duplicate
    methods); the message says to delete the individual derives instead.
  - comments, string literals, and doc comments never count.

RULE 2 — `Data` that generates no mutable accessor is a `Getter` (§17.16.1)
---------------------------------------------------------------------------
`Data` = Getter + GetterMut + Setter, but the three halves are switched off
per field, and the two switches are independent attributes:

    #[get_mut(skip)]   suppresses get_mut_<field>   (lombok parse/fn.rs:
    #[set(skip)]                                    config.skip_flags
                                                     .insert(FuncType::GetMut / Set))

So a struct can carry `Data` and generate nothing mutable at all. When EVERY
field skips BOTH, and at least one field still gets a plain getter, the derive
that says what the struct actually does is `Getter`:

    // violation: Data promises mutators that no field ever gets
    #[derive(Clone, Debug, Data)]
    pub struct RayTraceScene {
        #[get(pub(crate), type(copy))]
        #[get_mut(skip)]
        #[set(skip)]
        pub(crate) sample_count: u32,
    }

    // correct — and the get_mut / set attributes must GO with it
    #[derive(Clone, Debug, Getter)]
    pub struct RayTraceScene { #[get(pub(crate), type(copy))] pub(crate) sample_count: u32 }

The attributes must be deleted, not just the derive swapped: `Getter` is
declared `#[proc_macro_derive(Getter, attributes(get))]`, so a surviving
`#[get_mut(..)]` / `#[set(..)]` is rejected by rustc as an unknown helper
attribute ("cannot find attribute"). Verified against lombok-macros 10.2.7
(real `cargo check`, both shapes).

What is deliberately NOT reported, because shrinking the API is not this
rule's call:
  - a struct where ANY field still has a live `get_mut` or `set` — the derive
    is genuinely `Data` and stays, however few call sites use the mutable half;
  - a struct where every field also skips `get` (no accessor at all);
  - empty / unit structs (no field to read a skip off). Tuple structs ARE
    scanned: the generator emits the same accessors for `Fields::Unnamed`,
    indexed by position, so `#[get_mut(skip)]` means there what it means on a
    named field;
  - any field whose accessors are `cfg_attr`-conditional or `cfg`-gated — the
    unconditional shape cannot be proven, so the struct is exempt rather than
    guessed at;
  - struct-shaped tokens inside a function-like macro invocation (`m!([ ... ])
    is not an item, so no derive ever reaches it);
  - strings, raw strings, char literals, line and (nested) block comments.

Read-only. Exits non-zero when any violation is present. `--rule` narrows the
output to one rule so the audit can register them as two independent checks
without double-counting the shared summary line.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP_DIRS = {"target", ".git", "node_modules", ".cargo", "dist", "www"}

# The trio `Data` replaces, and the derive that replaces it.
TRIO = {"Getter", "GetterMut", "Setter"}
DATA = "Data"

# Rule identifiers, accepted by `--rule`.
RULE_TRIO = "trio"
RULE_GETTER_ONLY = "getter-only"
RULE_ALL = "all"
RULES = (RULE_TRIO, RULE_GETTER_ONLY)

DERIVE_ATTR_RE = re.compile(r"#\[\s*derive\s*\(")
# The SAME attribute as one complete token. `DERIVE_ATTR_RE` stops at the
# opening paren, so it cannot `fullmatch` a `#[...]` span; this one does,
# which is what binds a derive list to the exact item in front of it.
DERIVE_ATTR_FULL_RE = re.compile(r"#\[\s*derive\s*\([^()]*\)\s*\]")
STRUCT_AFTER_RE = re.compile(r"\b(?:struct|enum|union|trait|fn|impl|mod)\b")


# ---------------------------------------------------------------------------
# Lexical masking
# ---------------------------------------------------------------------------

def strip_comments(text: str) -> str:
    """Blank out comments and string/char literal bodies, preserving offsets.

    Offset preservation matters: violations are reported at the original
    line number. Blanking is what keeps prose (`/// see #[derive(..)]` in a
    doc comment, a raw string holding sample code) from being read as code.

    Raw-string prefix note (deliberate, tested in the self-test): the `r`
    branch accepts a raw string even when the `r` is the tail of a longer
    identifier. `bar"x"` is not valid Rust, so that can only over-blank
    (safe) and never un-mask real code; requiring a word boundary instead
    would risk leaving a genuine raw string's body live. What MUST stay
    correct — and is asserted — are `r".."`, `r#".."#`, `br#".."#`,
    `b".."`, escaped quotes, nested block comments, and the raw IDENTIFIER
    `r#type`, which is code and is left alone.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        two = text[i : i + 2]
        if two == "//":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
        elif two == "/*":
            depth = 1
            out.append("  ")
            i += 2
            while i < n and depth:
                if text[i : i + 2] == "/*":
                    depth += 1
                    out.append("  ")
                    i += 2
                elif text[i : i + 2] == "*/":
                    depth -= 1
                    out.append("  ")
                    i += 2
                else:
                    out.append("\n" if text[i] == "\n" else " ")
                    i += 1
        elif c in "rb" and re.match(r"r(#*)\"", text[i:]):
            m = re.match(r"r(#*)\"", text[i:])
            assert m
            hashes = m.group(1)
            end = text.find('"' + hashes, i + m.end())
            end = n if end == -1 else end + 1 + len(hashes)
            for ch in text[i:end]:
                out.append("\n" if ch == "\n" else " ")
            i = end
        elif c == '"':
            out.append(" ")
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\":
                    out.append(" ")
                    i += 1
                    if i < n:
                        out.append("\n" if text[i] == "\n" else " ")
                        i += 1
                    continue
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append(" ")
                i += 1
        elif c == "'" and re.match(r"'(?:\\.|[^\\'])'", text[i:]):
            m = re.match(r"'(?:\\.|[^\\'])'", text[i:])
            assert m
            for ch in m.group(0):
                out.append("\n" if ch == "\n" else " ")
            i += m.end()
        else:
            out.append(c)
            i += 1
    return "".join(out)


# ---------------------------------------------------------------------------
# Balanced-delimiter reader (shared by both rules)
# ---------------------------------------------------------------------------

PAIRS = {"(": ")", "[": "]", "{": "}", "<": ">"}

# `>` is only a CLOSER in an angle-bracket group, and only when it cannot be
# read as part of an operator. Two cases break a naive depth counter:
#   Box<dyn Fn() -> u32>  — the `->` arrow: its `>` would close the `<`
#                          early, truncating the struct body right there and
#                          silently "losing" every field after it;
#   HashMap<K, V>>         — the `>>` closing two generics at once.
ARROW_RE = re.compile(r"->")


def _match_forward(code: str, opener_at: int) -> int | None:
    """`code[opener_at]` opens a group; return the index past its closer.

    Depth counts the delimiter kinds at once. That is what makes field
    splitting safe for `HashMap<String, Vec<u32>>` (the inner commas and the
    `>>`) and for `Box<dyn Fn(u32) -> u32>` (the arrow contributes nothing,
    the parens balance themselves) without ever splitting on a comma regex.

    Angle brackets are matched only against other angle brackets, and a `>`
    that reads as an operator is never a closer:
      Box<dyn Fn() -> u32>   the `->` arrow must not close the `<`;
      HashMap<K, V>>         the `>>` closes two groups at once.
    A `<` that is a COMPARISON (`if a < b`) is likewise not tracked; nothing
    in this file parses conditions, and a stray `<` there would otherwise
    swallow the rest of the file looking for a `>`.
    """
    opener = code[opener_at]
    if opener not in PAIRS:
        return None
    # Angle depth is tracked SEPARATELY from brace/bracket/paren depth, and
    # only while inside an angle group. Counting them in one number is what
    # let a field type's `<` swallow the struct's closing `}`.
    round_depth = 0
    angle_depth = 0
    i = opener_at
    n = len(code)
    while i < n:
        c = code[i]
        if opener == "<":
            if c == "<":
                angle_depth += 1
            elif c == ">":
                if _angle_close_is_operator(code, i):
                    if code[i - 1] == "-":
                        # `->` arrow: it closes nothing, just consume it.
                        i += 1
                        continue
                    # `>>`: the first `>` closes the INNERMOST generic. Fall
                    # through to the normal decrement so this one is counted,
                    # and the loop re-examines the second `>` for the outer.
                    angle_depth -= 1
                    if angle_depth == 0:
                        # This `>` closed the group we started in AND the
                        # nested one that was already closed — nothing left.
                        return i + 1
                    i += 1
                    continue
                angle_depth -= 1
                if angle_depth == 0:
                    return i + 1
        else:
            if c == "(" or c == "[" or c == "{":
                round_depth += 1
            elif c == ")" or c == "]" or c == "}":
                round_depth -= 1
                if round_depth == 0:
                    return i + 1
            elif c == "<":
                # Consume the nested generic whole, so its commas and `>>`
                # are consumed with it rather than counted against this
                # group. A COMPARISON `<` finds no matching `>` and falls
                # through one character at a time.
                angle_end = _match_forward(code, i)
                if angle_end is not None:
                    i = angle_end - 1
        i += 1
    return None


def _angle_close_is_operator(code: str, at: int) -> bool:
    """True when `code[at]` is a `>` that does NOT close an angle group.

    Two shapes, both confirmed against real Rust:
      `- >`      the return-type arrow of a trait object or fn pointer;
      `> >`      two generics closing together, e.g. `HashMap<K, V>>`.
    """
    prev = code[at - 1] if at > 0 else ""
    return prev == "-" or prev == ">"


def _skip_ws(code: str, i: int) -> int:
    n = len(code)
    while i < n and code[i].isspace():
        i += 1
    return i


def _skip_ws_back(code: str, i: int) -> int:
    while i > 0 and code[i - 1].isspace():
        i -= 1
    return i


# ---------------------------------------------------------------------------
# Rule 1: the spelled-out trio
# ---------------------------------------------------------------------------

def _derive_names(code: str, open_paren: int) -> tuple[list[str], int]:
    """Read one derive list, starting at its `(`. Returns (names, end)."""
    depth = 0
    i = open_paren
    n = len(code)
    while i < n:
        c = code[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return _split_names(code[open_paren + 1 : i]), i + 1
        i += 1
    return [], n


def _split_names(body: str) -> list[str]:
    """Split a derive list on top-level commas, returning bare macro names.

    Path-qualified derives count by their last segment, which is how a crate
    that re-exports the macros spells them (`lombok_macros::Data`).
    """
    names: list[str] = []
    depth = 0
    current = ""
    for ch in body:
        if ch in "<([{":
            depth += 1
        elif ch in ">)]}":
            depth -= 1
        if ch == "," and depth == 0:
            names.append(current)
            current = ""
            continue
        current += ch
    names.append(current)
    out: list[str] = []
    for raw in names:
        name = raw.strip().split("::")[-1].strip()
        if name:
            out.append(name)
    return out


def _trio_hits(code: str) -> list[tuple[int, str, str]]:
    """Return [(line_no, derive_list, item_kind)] for redundant trios."""
    blocked = _macro_invocation_spans(code)
    hits: list[tuple[int, str, str]] = []
    for match in DERIVE_ATTR_RE.finditer(code):
        if any(start <= match.start() < end for start, end in blocked):
            # Inside `m!( ... )`: a token blob, not an item.
            continue
        names, end = _derive_names(code, match.end() - 1)
        if not TRIO.issubset(names):
            continue
        # The item the derive list decorates decides whether the trio can
        # even compile: only a struct is supported by the generator.
        tail = code[end : end + 200]
        kind_match = STRUCT_AFTER_RE.search(tail)
        if kind_match is None or kind_match.group(0) != "struct":
            continue
        line_no = code.count("\n", 0, match.start()) + 1
        hits.append((line_no, ", ".join(names), kind_match.group(0)))
    return hits


# ---------------------------------------------------------------------------
# Rule 2: `Data` that generates no mutable accessor is a `Getter`
# ---------------------------------------------------------------------------

IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
STRUCT_KW_RE = re.compile(r"\bstruct\b")

# `pub`, `pub(crate)`, `pub(in path)`, plus the modifiers that can legally sit
# between an attribute run and the item it decorates.
VIS_BEFORE_ITEM_RE = re.compile(
    r"(?:pub(?:\s*\([^()]*(?:\([^()]*\)[^()]*)*\))?|(?:default|const|async|unsafe)\b)\s*$"
)

# `vis name: Type` — the head of a named field.
FIELD_HEAD_RE = re.compile(
    r"^(?:pub(?:\s*\([^()]*\))?\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*:"
)

# `#[get(..)]` / `#[get_mut(..)]` / `#[set(..)]`, anchored on the whole token.
ACCESSOR_ATTR_RE = re.compile(r"^\s*(get|get_mut|set)\b(.*)$", re.S)
# `type(...)` config must be removed before looking for a `skip` identifier, so
# `#[set(type(skip_alias))]` cannot be misread as `#[set(skip)]`.
TYPE_GROUP_RE = re.compile(r"\btype\s*\([^()]*\)")
SKIP_IDENT_RE = re.compile(r"\bskip\b")
CONDITIONAL_ATTR_RE = re.compile(r"^\s*(?:cfg|cfg_attr)\b")

# A function-like macro invocation: `name!( ... )` / `name![...]` / `name!{...}`.
# `macro_rules!` is excluded on purpose — its transcriber holds REAL items.
MACRO_INVOKE_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*!\s*([(\[{])")


def _macro_invocation_spans(code: str) -> list[tuple[int, int]]:
    """Byte spans a derive can never legitimately live in.

    `m!(#[derive(Data)] struct Ghost { .. })` is a token blob, not an item:
    the derive reaches no proc macro, so reporting it would be a false
    positive. A `macro_rules!` transcriber is different — those items are
    compiled when the macro expands — so it is deliberately NOT skipped.
    """
    spans: list[tuple[int, int]] = []
    for match in MACRO_INVOKE_RE.finditer(code):
        if match.group(1) == "macro_rules":
            continue
        end = _match_forward(code, match.end() - 1)
        if end is not None:
            spans.append((match.end() - 1, end))
    return spans


def _attrs_before(code: str, pos: int) -> list[tuple[int, int]]:
    """The contiguous `#[...]` run directly in front of `pos`, left to right."""
    spans: list[tuple[int, int]] = []
    cursor = pos
    while True:
        j = _skip_ws_back(code, cursor)
        if j <= 0:
            break
        vis = VIS_BEFORE_ITEM_RE.search(code[:j])
        if vis is not None and vis.end() == j:
            j = _skip_ws_back(code, vis.start())
        if j <= 0 or code[j - 1] != "]":
            break
        # Walk back to the matching `[`. A naive backward scan stops on the
        # first `]`, which is the inner closer of a multi-line
        # `#[derive(\n  A,\n  B,\n)]`.
        depth = 0
        k = j
        while k > 0:
            k -= 1
            if code[k] == "]":
                depth += 1
            elif code[k] == "[":
                depth -= 1
                if depth == 0:
                    break
        if k <= 0 or code[k] != "[":
            break
        start = k
        if start > 0 and code[start - 1] == "#":
            start -= 1
        spans.append((start, j))
        cursor = start
    return list(reversed(spans))


def _attr_text(code: str, span: tuple[int, int]) -> str:
    text = code[span[0] : span[1]]
    text = text.lstrip()
    if text.startswith("#"):
        text = text[1:].lstrip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    return text


def _derives_of(code: str, spans: list[tuple[int, int]]) -> set[str]:
    derives: set[str] = set()
    for span in spans:
        raw = code[span[0] : span[1]]
        if DERIVE_ATTR_FULL_RE.fullmatch(raw) is None:
            continue
        # `_derive_names` wants the index of the LIST's `(`, not the `]` that
        # ends the whole attribute token, so re-find it inside this span.
        opener = DERIVE_ATTR_RE.match(raw)
        if opener is None:
            continue
        names, _end = _derive_names(code, span[0] + opener.end() - 1)
        derives.update(names)
    return derives


def _braced_structs(code: str) -> list[tuple[int, str, int, int]]:
    """Every braced struct as (struct-keyword index, name, body start, end).

    Tuple structs (`struct S(u32);`) are INCLUDED: the attribute run sits
    directly in front of the field either way, and the macro generates the
    same accessors for `Fields::Unnamed` (indexed by position, not name — see
    the note on the body-opener scan below). Only unit (`struct S;`) and
    empty (`struct S {}`) bodies are skipped, having no field at all.
    """
    found: list[tuple[int, str, int, int]] = []
    for match in STRUCT_KW_RE.finditer(code):
        i = _skip_ws(code, match.end())
        name_match = IDENT_RE.match(code, i)
        if name_match is None:
            continue
        name = name_match.group(0)
        i = name_match.end()
        i = _skip_ws(code, i)
        if i < len(code) and code[i] == "<":
            generics_end = _match_forward(code, i)
            if generics_end is None:
                continue
            i = _skip_ws(code, generics_end)
        # Skip any `where` clause / const defaults to the body opener. A
        # tuple struct's body opens with `(`, and it is NOT exempt: the macro
        # generates the same accessors for `Fields::Unnamed`, indexed by
        # position (`generate/fn.rs`: `generate_getter_setter(field,
        # Some(index), ...)`), so `#[get_mut(skip)]` on a tuple field means
        # exactly what it means on a named one.
        angle = 0
        j = i
        opener = None
        while j < len(code):
            c = code[j]
            if c == "<":
                angle += 1
            elif c == ">":
                angle = max(0, angle - 1)
            elif angle == 0 and c == "{":
                opener = c
                break
            elif angle == 0 and c in ";(":
                opener = c
                break
            j += 1
        if opener not in {"{", "("}:
            continue
        body_end = _match_forward(code, j)
        if body_end is None:
            continue
        found.append((match.start(), name, j, body_end - 1))
    return found


def _named_fields(code: str, body_start: int, body_end: int):
    """Yield ([attr spans], field head) for each field of a body.

    Splits on top-level commas only — every delimiter kind is tracked, so
    `HashMap<String, Vec<u32>>` stays one field and a multi-line generic type
    never splits into phantom fields. Angle groups are consumed whole (see
    `_match_forward`), so neither their commas nor their `>>` count.
    """
    depth = 0
    chunk_start = body_start + 1
    spans: list[tuple[int, int]] = []
    i = body_start + 1
    while i < body_end:
        c = code[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth = max(0, depth - 1)
        elif c == "<":
            angle_end = _match_forward(code, i)
            if angle_end is None or angle_end > body_end:
                angle_end = i + 1
            i = angle_end - 1
        elif c == "," and depth == 0:
            field = _field_of_chunk(code, chunk_start, i, spans)
            if field is not None:
                yield field
            spans = []
            chunk_start = i + 1
        i += 1
    field = _field_of_chunk(code, chunk_start, body_end, spans)
    if field is not None:
        yield field


def _field_of_chunk(
    code: str, start: int, end: int, spans: list[tuple[int, int]]
) -> tuple[list[tuple[int, int]], str] | None:
    """Strip the leading attribute run off one field chunk and read its head."""
    cursor = start
    field_spans = list(spans)
    while True:
        j = _skip_ws(code, cursor)
        if j >= end or code[j] != "#":
            break
        k = _skip_ws(code, j + 1)
        if k >= end or code[k] != "[":
            break
        attr_end = _match_forward(code, k)
        if attr_end is None or attr_end > end:
            break
        field_spans.append((j, attr_end))
        cursor = attr_end
    head = code[cursor:end].strip()
    if not head:
        return None
    return (field_spans, head)


def _field_accessor_state(
    code: str, spans: list[tuple[int, int]]
) -> tuple[bool, bool, bool] | None:
    """Return (get_skipped, get_mut_skipped, set_skipped) for one field.

    A kind is SKIPPED as soon as ONE attribute of that kind says skip — a
    union over duplicates, not an intersection, and not "first non-skipping
    wins". Proven against lombok-macros 10.2.7, by reading
    `generate/fn.rs` and by a real `cargo check` of all three orderings:

        #[get_mut(pub(crate))] #[get_mut(skip)]
        #[get_mut(skip)]     #[get_mut(pub(crate))]
        #[set(pub(crate))]   #[set(skip)]

    `generate_named_getter_setter` makes TWO passes over the field's
    attributes. The FIRST pass (`generate/fn.rs` 866-874) reads every
    attribute up front and inserts each of its skip flags into BOTH
    `shared_config.skip_flags` AND `shared_config.added_flags`. Only the
    SECOND pass (875-940) generates code, and each emission is guarded by
    `!shared_config.added_flags.contains(&FuncType::Get | GetMut | Set)`
    (891-893, 913-915, 926-928), with the same guard again in the
    trailing fallback block (942-983). Because `added_flags` was already
    marked during the first pass, one `skip` of that kind disables the
    accessor for the whole field no matter where it sits in the run, and no
    sibling non-skipping attribute can bring it back.

    All three orderings compile to NO mutator: each `cargo check` exits 101
    with `error[E0599]: no method named get_mut_value / set_value`, so the
    struct is genuinely `Getter` and MUST be reported.

    None means "cannot be decided unconditionally" (a `cfg` / `cfg_attr` in
    the run), which exempts the whole struct.

    A field with NO accessor attribute at all is NOT skipped — the derives
    emit every accessor by default, which is exactly why `#[get(skip)]` has
    to be written down. Each kind is "generated" unless an attribute of that
    kind says otherwise, so a bare field yields (False, False, False).
    """
    # kind -> True once ANY attribute of that kind opts out. Duplicates do
    # not dilute the skip (see the docstring), so a second non-skipping
    # attribute of the same kind cannot clear it.
    skipped: set[str] = set()
    for span in spans:
        text = _attr_text(code, span)
        if CONDITIONAL_ATTR_RE.match(text):
            return None
        match = ACCESSOR_ATTR_RE.match(text)
        if match is None:
            continue
        args = TYPE_GROUP_RE.sub(" ", match.group(2))
        if not SKIP_IDENT_RE.search(args):
            continue
        skipped.add(match.group(1))
    # A kind never mentioned is absent, and an absent kind is GENERATED (not
    # skipped) — the derives emit it by default.
    return ("get" in skipped, "get_mut" in skipped, "set" in skipped)


def _getter_only_hits(code: str) -> list[tuple[int, str, str]]:
    """Return [(line_no, struct_name, why)] for `Data` structs with no mutator."""
    blocked = _macro_invocation_spans(code)
    hits: list[tuple[int, str, str]] = []
    for kw_start, name, body_start, body_end in _braced_structs(code):
        if any(start <= kw_start < end for start, end in blocked):
            continue
        derives = _derives_of(code, _attrs_before(code, kw_start))
        if DATA not in derives:
            continue
        fields = [field for field in _named_fields(code, body_start, body_end) if field]
        if not fields:
            # Empty struct: no field to read a skip off.
            continue
        live_getters = 0
        any_mutable = False
        conditional = False
        for spans, _head in fields:
            state = _field_accessor_state(code, spans)
            if state is None:
                conditional = True
                break
            get_skipped, get_mut_skipped, set_skipped = state
            if not get_skipped:
                live_getters += 1
            if not (get_mut_skipped and set_skipped):
                any_mutable = True
                break
        if conditional or any_mutable:
            continue
        if live_getters == 0:
            # Nothing at all is generated; `Getter` would not describe it
            # either. Out of scope for this rule.
            continue
        why = (
            f"all {len(fields)} field(s) skip both `#[get_mut(skip)]` and "
            f"`#[set(skip)]`, and {live_getters} still get a plain getter"
        )
        hits.append((code.count("\n", 0, kw_start) + 1, name, why))
    return hits


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def check_text(text: str, rule: str = RULE_ALL) -> list[tuple]:
    """Return [(line_no, detail, item, rule)] for every violation found."""
    if rule not in (*RULES, RULE_ALL):
        raise ValueError(f"unknown rule {rule!r}")
    code = strip_comments(text)
    hits: list[tuple] = []
    if rule in (RULE_TRIO, RULE_ALL):
        hits.extend((line, names, kind, RULE_TRIO) for line, names, kind in _trio_hits(code))
    if rule in (RULE_GETTER_ONLY, RULE_ALL):
        hits.extend(
            (line, name, why, RULE_GETTER_ONLY) for line, name, why in _getter_only_hits(code)
        )
    hits.sort(key=lambda hit: (hit[0], hit[3]))
    return hits


def iter_rust_files(root: Path):
    for path in sorted(root.rglob("*.rs")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _trio_message(where: str, names: list[str]) -> str:
    shown = ", ".join(names)
    if DATA in names:
        return (
            f"{where}: derive list `#[derive({shown})]` already contains "
            f"`{DATA}` — delete the individual `Getter` / `GetterMut` / "
            f"`Setter` entries (rust-standards §17.16)"
        )
    return (
        f"{where}: derive list `#[derive({shown})]` spells out the full "
        f"accessor trio — write `#[derive({DATA})]` instead; it is exactly "
        f"`Getter + GetterMut + Setter` (rust-standards §17.16)"
    )


def _getter_only_message(where: str, name: str, why: str) -> str:
    return (
        f"{where}: `struct {name}` derives `{DATA}` but {why} — `Data` is "
        f"`Getter + GetterMut + Setter`, so it promises mutators the struct "
        f"never generates; write `#[derive(Getter)]` and delete the "
        f"`#[get_mut(...)]` / `#[set(...)]` attributes, which `Getter` "
        f"(`attributes(get)`) no longer accepts and rustc rejects "
        f"(rust-standards §17.16.1)"
    )


def _format(where: str, hit: tuple) -> str:
    # hit = (line_no, detail, item, rule); for rule 2 `detail` is the struct
    # NAME and `item` is the reason string.
    line, detail, item, rule = hit
    if rule == RULE_TRIO:
        return _trio_message(where, detail.split(", "))
    return _getter_only_message(where, detail, item)


def _read(path: Path) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _relpath(path: Path, root: Path | None) -> str:
    base = Path(root) if root is not None else Path(path).parent
    try:
        return str(Path(path).relative_to(base))
    except ValueError:
        return Path(path).name


def check_file(path: Path, rule: str = RULE_ALL) -> list[str]:
    text = _read(Path(path))
    if text is None:
        return []
    return [_format(f"{path}:{hit[0]}", hit) for hit in check_text(text, rule)]


def audit_one(path: Path, root: Path | None = None) -> list[str]:
    """Per-file entry point used by `staged_file_gate.py`.

    The gate imports this module and calls `audit_one` directly instead of
    shelling out, so a verifier without it is silently skipped (it returns
    an empty list, which reads as "0 violations"). Keep this name.

    The optional `root` gives repo-relative prefixes; the gate calls it with
    a single argument, which falls back to the file's own directory as the
    base and yields the bare file name.
    """
    text = _read(Path(path))
    if text is None:
        return []
    where = _relpath(Path(path), root)
    return [_format(f"{where}:{hit[0]}", hit) for hit in check_text(text)]


def main() -> int:
    args = [a for a in sys.argv[1:]]
    rule = RULE_ALL
    if "--rule" in args:
        idx = args.index("--rule")
        if idx + 1 >= len(args):
            print("usage: ... --rule trio|getter-only|all", file=sys.stderr)
            return 2
        rule = args[idx + 1]
        del args[idx : idx + 2]
    if rule not in (*RULES, RULE_ALL):
        print(f"unknown rule {rule!r}; expected one of {(*RULES, RULE_ALL)}",
              file=sys.stderr)
        return 2
    if not args:
        print("usage: verify_no_redundant_accessor_derive.py <repo_root> [--rule RULE]",
              file=sys.stderr)
        return 2
    root = Path(args[0]).resolve()
    if not root.exists():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    files = list(iter_rust_files(root))
    violations: list[str] = []
    for path in files:
        text = _read(path)
        if text is None:
            continue
        violations.extend(_format(f"{path}:{hit[0]}", hit) for hit in check_text(text, rule))

    for line in violations:
        print(line)

    print(f"{len(files)} files checked, {len(violations)} violations")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
