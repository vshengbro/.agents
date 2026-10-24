#!/usr/bin/env python3
"""Re-point upstream-relative links in a vendored reference page.

The upstream docs-pages tree is nested (`src/euv/macros/class.md`), while
the vendored copies are flat (`skills/euv/references/class.md`). A relative
link that was valid upstream — `../macros/css-vars.md` — therefore points at
a path that does not exist inside the skill tree, and the structural audit
reports it as `link.target_missing`.

This tool resolves every relative link in a page against the page's upstream
source path and re-points it:

  * at the vendored copy of the same upstream page, when the mapping vendors
    it (the link becomes a sibling file name inside `references/`);
  * otherwise at the page's published URL on the docs site, so the reader
    still reaches the content.

Links that are already absolute (http/https/mailto), pure fragments, or
image links are left untouched.

Usage:
    python3 scripts/rewrite_reference_links.py \\
        --mapping scripts/sync-references.mapping \\
        --source src/euv/macros/class.md \\
        --dest skills/euv/references/class.md \\
        --site-base https://ltpp.vip < page.md > page.md

Exit codes: 0 rewritten (or nothing to do) · 2 usage/IO error.
"""
from __future__ import annotations

import argparse
import posixpath
import re
import sys
from pathlib import Path

# Inline markdown links: [text](target). Images are excluded on purpose —
# an image path is a site asset, not a page.
INLINE_LINK_RE = re.compile(r"(?<!!)(\[[^\]]*\]\()([^)\s]+)((?:\s+[^)]*)?\))")

# Reference definitions: [label]: target
REF_DEF_RE = re.compile(r"^(\s{0,3}\[[^\]]+\]:\s*)(\S+)(.*)$")

EXTERNAL_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)")


def load_mapping(path: Path) -> dict[str, list[str]]:
    """upstream source path -> list of vendored destination paths."""
    mapping: dict[str, list[str]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cols = [c.strip() for c in raw.split("\t")
                if c.strip() and not c.strip().startswith("#")]
        if len(cols) < 2:
            continue
        dest, src = cols[0], cols[1]
        mapping.setdefault(src, []).append(dest)
    return mapping


def site_url(src: str, site_base: str) -> str:
    """Published URL of an upstream page.

    Two upstream layouts are in use: the older `src/<area>/<page>.md` and the
    current `docs/<locale>/<area>/<page>.md`. The published site serves
    `/<lang>/<area>/<page>.html`, so the layout prefix is stripped and the
    locale is taken from the source path when it carries one.
    """
    rel = src
    locale = "zh"
    if rel.startswith("docs/"):
        parts = rel.split("/", 2)
        if len(parts) == 3:
            locale, rel = parts[1], parts[2]
    elif rel.startswith("src/"):
        rel = rel[len("src/"):]
    rel = rel[:-3] if rel.endswith(".md") else rel
    if rel.endswith("/README"):
        rel = rel[: -len("/README")]
    return f"{site_base.rstrip('/')}/{locale}/{rel}.html"


def rewrite_target(target: str, src_rel: str, mapping: dict[str, list[str]],
                   dest_rel: str, site_base: str) -> str:
    """Return the re-pointed link target (unchanged when not applicable)."""
    if not target or target.startswith("#"):
        return target
    if EXTERNAL_RE.match(target):
        return target
    if target.startswith("/"):
        return target

    # A reference to the page's own directory index resolves to the
    # directory itself; keep the anchor and re-point the path.
    path, sep, frag = target.partition("#")

    # Already re-pointed at a sibling of this page: leave it alone, so
    # running the rewriter twice does not rewrite the result again.
    if "/" not in path and path.endswith(".md"):
        sibling = posixpath.join(posixpath.dirname(dest_rel), path)
        if any(d == sibling for dests in mapping.values() for d in dests):
            return target

    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(src_rel), path))
    dests = mapping.get(resolved)
    if dests:
        # Prefer a copy vendored in the same skill, so the link stays inside
        # the skill's own references/ directory.
        own = [d for d in dests
               if posixpath.dirname(d) == posixpath.dirname(dest_rel)]
        chosen = (own or dests)[0]
        new_path = posixpath.basename(chosen)
    else:
        new_path = site_url(resolved, site_base)

    return f"{new_path}{sep}{frag}" if sep else new_path


def rewrite_text(text: str, src_rel: str, dest_rel: str,
                 mapping: dict[str, list[str]], site_base: str) -> str:
    out_lines = []
    for line in text.splitlines(keepends=True):
        line = re.sub(
            INLINE_LINK_RE,
            lambda m: (m.group(1)
                       + rewrite_target(m.group(2), src_rel, mapping, dest_rel, site_base)
                       + m.group(3)),
            line,
        )
        line = re.sub(
            REF_DEF_RE,
            lambda m: (m.group(1)
                       + rewrite_target(m.group(2), src_rel, mapping, dest_rel, site_base)
                       + m.group(3)),
            line,
        )
        out_lines.append(line)
    return "".join(out_lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Re-point upstream-relative links in a vendored page.")
    ap.add_argument("--mapping", required=True,
                    help="sync-references.mapping file")
    ap.add_argument("--source", required=True,
                    help="upstream source path of the page (e.g. src/euv/macros/class.md)")
    ap.add_argument("--dest", required=True,
                    help="vendored destination path (e.g. skills/euv/references/class.md)")
    ap.add_argument("--site-base", default="https://ltpp.vip",
                    help="base URL of the published docs site")
    args = ap.parse_args(argv)

    mapping_file = Path(args.mapping)
    if not mapping_file.is_file():
        print(f"ERROR: mapping not found: {mapping_file}", file=sys.stderr)
        return 2

    try:
        mapping = load_mapping(mapping_file)
    except OSError as exc:
        print(f"ERROR: reading {mapping_file}: {exc}", file=sys.stderr)
        return 2

    text = sys.stdin.read()
    sys.stdout.write(
        rewrite_text(text, args.source, args.dest, mapping, args.site_base))
    return 0


if __name__ == "__main__":
    sys.exit(main())
