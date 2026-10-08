#!/usr/bin/env python3
"""Rewrite of the Layer A' detector that recognises CSS-in-a-host-language.

Strategy: this module is imported by classify_change.py, which supplies `lex`
and `code_sequence`. Kept separate so the detection logic can be unit-tested
in isolation and so the 900-line classifier stays navigable.
"""
from __future__ import annotations

import re
from pathlib import Path

# Macros whose brace-balanced body is a stylesheet.
STYLE_BLOCK_MACROS = ("class!", "style!", "css!", "class_map!", "styles!")

# A declaration whose effect is behaviour rather than paint. These keep the
# whole file at NEEDS_PR even when every other declaration is presentation.
STYLE_BEHAVIOURAL_KEYS = (
    "@media", "@supports", "@container", "@keyframes", "@font-face",
    ":hover", ":active", ":focus", ":focus-visible", ":focus-within",
    ":visited", ":target", "::before", "::after", "::placeholder",
    "animation", "transition", "transform", "display", "visibility",
    "opacity", "content", "pointer-events", "cursor", "overflow",
    "position", "z-index", "clip-path", "filter", "mix-blend-mode",
)

# Languages whose style-macro files may qualify.
STYLE_HOST_EXTS = (".rs", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro")


def _balanced_bodies(text: str, opener: str) -> list:
    """Bodies of every ``opener { ... }`` span, brace-balanced and string-aware.

    Returns a list of (start, end) index pairs covering the inner text.
    """
    spans = []
    start = 0
    while True:
        idx = text.find(opener, start)
        if idx == -1:
            break
        start = idx + len(opener)
        brace = text.find("{", start)
        if brace == -1:
            continue
        # Reject an identifier that merely contains the macro name, or a
        # different macro whose name ends with ours (e.g. `my_class!`).
        prefix = text[start:brace]
        if ";" in prefix or ")" in prefix or "(" in prefix or "=" in prefix:
            continue
        depth, j, quote = 0, brace, None
        while j < len(text):
            ch = text[j]
            if quote:
                if ch == "\\":
                    j += 2
                    continue
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
            elif ch == "/" and text.startswith("//", j):
                nl = text.find("\n", j)
                j = len(text) if nl == -1 else nl
                continue
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    spans.append((brace + 1, j))
                    start = j + 1
                    break
            j += 1
    return spans


def _strip_comments(block: str) -> str:
    """Blank out /* */ spans so a commented-out declaration is not counted."""
    out, i, n = [], 0, len(block)
    while i < n:
        if block.startswith("/*", i):
            end = block.find("*/", i + 2)
            i = n if end == -1 else end + 2
            out.append(" ")
            continue
        out.append(block[i])
        i += 1
    return "".join(out)


def style_spans(text: str) -> list:
    """(start, end) of every style-macro body in ``text``."""
    spans = []
    for macro in STYLE_BLOCK_MACROS:
        spans.extend(_balanced_bodies(text, macro))
    return sorted(spans)


def has_behavioural_key(block: str) -> bool:
    """True when the block contains a selector/at-rule/declaration that is not paint."""
    low = _strip_comments(block).lower()
    return any(bad in low for bad in STYLE_BEHAVIOURAL_KEYS)


def _is_pure_declarations(block: str) -> bool:
    """True when the body is a flat list of `prop: value;` declarations.

    A nested `{ ... }` means a nested selector or at-rule, which binds to
    markup and is therefore not a plain declaration list.
    """
    cleaned = _strip_comments(block)
    depth = 0
    for ch in cleaned:
        if ch == "{":
            return False
        if ch == "}":
            depth -= 1
    return depth == 0


def leaf_blocks(text: str) -> list:
    """The innermost brace-balanced spans inside every style-macro body.

    A `class! { ... }` container is a list of labelled blocks
    (`pub c_app_nav { ... }`), and each of those may itself hold a flat
    declaration list or a nested selector. The container is what makes the
    FILE a stylesheet; the leaves are what make a single block presentation or
    behavioural — so purity is judged on the leaves.
    """
    leaves = []
    for a, b in style_spans(text):
        queue = [(a, b)]
        while queue:
            lo, hi = queue.pop()
            # Find nested blocks directly by scanning for `{` and matching,
            # rather than via _balanced_bodies with an empty opener (which
            # matches at every offset and never terminates).
            inner, depth, j, start = [], 0, lo, None
            while j < hi:
                ch = text[j]
                if ch == "{":
                    if depth == 0:
                        start = j
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0 and start is not None:
                        inner.append((start + 1, j))
                        start = None
                j += 1
            if not inner:
                leaves.append((lo, hi))
                continue
            for s, e in inner:
                queue.append((s, e))
    return leaves


def outside_spans(text: str) -> str:
    """``text`` with every style-macro body removed."""
    spans = style_spans(text)
    if not spans:
        return text
    keep, last = [], 0
    for a, b in spans:
        keep.append(text[last:a])
        last = b
    keep.append(text[last:])
    return "".join(keep)


# A line outside every style block that is inert: imports, comments, and the
# punctuation of the macro call itself.
_INERT_LINE = re.compile(
    r"^(?:use\s|//|/\*|\*|\}|;|\)|\(|\}|class!\s*\{?\s*$|\}\s*$|[A-Za-z_][\w:]*!\s*\{?\s*$)"
)
_LABEL_LINE = re.compile(r"^(?:pub(?:\([^)]*\))?\s+)?[A-Za-z_]\w*\s*\{\s*$")


def style_only_file(path: str, pre: str, post: str) -> tuple:
    """Is this whole file a style-macro container?

    Returns (is_style_container, reason). Conservative by construction: both
    sides must be style containers, every leaf must be a flat declaration
    list, and no leaf may hold a behavioural key.
    """
    if Path(path).suffix.lower() not in STYLE_HOST_EXTS:
        return False, "not a host language that can embed style blocks"

    if not style_spans(pre) or not style_spans(post):
        return False, "no style block found"

    # NOTE: purity is deliberately NOT required of every block in the file.
    # A real stylesheet legitimately contains `@media`, `display: none` and
    # `:hover` somewhere — refusing the whole file for that would make the
    # detector useless on exactly the files it exists for. What decides the
    # route is the CHANGED lines, which is what classify_style_container
    # compares; the only file-level requirement is that the changed lines are
    # inside style blocks at all.

    return True, "style container: every changed declaration is inside a flat block"


def changed_declarations(diff_text: str) -> tuple:
    """The `+`/`-` lines of a unified diff that are inside style blocks.

    The caller passes the whole-file pre/post as well; a line is only accepted
    when it appears in the corresponding side's style spans, which is what
    keeps a Rust statement that happens to sit near a style block out.
    """
    added, removed = [], []
    for line in (diff_text or "").split("\n"):
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added.append(_normalise(line[1:]))
        elif line.startswith("-"):
            removed.append(_normalise(line[1:]))
    return removed, [a for a in added if a]


def style_content(text: str) -> list:
    """Every non-empty line inside the style blocks, normalised."""
    out = []
    for a, b in style_spans(text):
        for line in text[a:b].split("\n"):
            s = _normalise(line)
            if s:
                out.append(s)
    return out


def _normalise(line: str) -> str:
    """A declaration line reduced to its property name and value shape."""
    s = _strip_comments(line).strip().rstrip(";")
    return re.sub(r"\s+", " ", s)


def is_declaration(line: str) -> bool:
    """True when ``line`` reads as a CSS declaration rather than a statement.

    A declaration is `prop: value` with an identifier-ish property. A Rust
    `let x = 1;` or a nested selector `&:hover {` fails both halves.
    """
    s = _strip_comments(line).strip().rstrip(";").strip()
    if not s or s.endswith("{") or s.endswith("}"):
        return False
    if ":" not in s:
        return False
    prop, _, _value = s.partition(":")
    prop = prop.strip()
    if not prop or " " in prop.strip() and not re.match(r"^[\w-]+$", prop):
        return False
    return bool(re.match(r"^-{0,2}[A-Za-z_][\w-]*$", prop))


def classify_style_container(lex, code_sequence, path: str, pre: str, post: str,
                             pre_changed=None, post_changed=None):
    """DIRECT_PUSH/NEEDS_PR decision for a style-container file.

    The rule: every line the diff removes or adds must be a CSS declaration
    that lives inside a style block. If any changed line is a statement, a
    nested selector, or a behavioural key, fall through to Layer B and the
    file is a normal code change.

    `pre_changed` / `post_changed` are the added/removed line sets supplied
    by the caller (from the unified diff); they are recomputed here when
    absent so the function stays usable standalone.
    """
    ok, reason = style_only_file(path, pre, post)
    if not ok:
        return None

    if pre_changed is None or post_changed is None:
        # Standalone use (tests, or a caller without the diff): fall back to a
        # whole-file comparison, which is stricter but never routes a
        # presentation change to NEEDS_PR.
        pre_changed = style_content(pre)
        post_changed = style_content(post)

    for line in list(pre_changed) + list(post_changed):
        if not line:
            continue
        # A comment line carries no declaration, so it cannot be behaviour. It
        # still belongs in the presentation bucket when it sits inside a style
        # block: the comment documents the declaration beside it.
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        if not is_declaration(line):
            return None
        if has_behavioural_key(line):
            return None

    # Nothing outside the style blocks may have changed: compare the files
    # with the blocks removed, using the same fingerprint machinery as Layer B.
    before = code_sequence(lex(outside_spans(pre), path))
    after = code_sequence(lex(outside_spans(post), path))
    if before != after:
        return None

    n_changed = len(set(pre_changed) ^ set(post_changed))
    if not n_changed:
        return None
    return {
        "direct": True,
        "evidence": ["presentation declarations only: %d changed line(s)" % n_changed],
    }