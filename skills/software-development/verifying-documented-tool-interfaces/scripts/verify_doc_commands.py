#!/usr/bin/env python3
"""Probe every `<tool> <resource> [<command>]` reference in a markdown file.

Existence is decided by OUTPUT SIGNATURE, not exit code: several CLIs treat an
unknown subcommand as a legal top-level query, print the root help, and exit 0.
A real command's help carries its own `Usage: <tool> <resource> <command>` line
and omits the resource table; a root fallback shows BOTH the generic usage line
and the full resource list. Seeing both means the command does not exist.

Usage
-----
    python3 verify_doc_commands.py <doc.md> <tool> [<tool> ...]
    python3 verify_doc_commands.py skills/mmx-cli/SKILL.md mmx

Exit codes
----------
    0  every probed command is real
    1  at least one reference fell back to root help (review each by hand --
       prose that deliberately quotes a non-existent command also matches)
    2  usage / environment error
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# `tool resource [command]` with lowercase kebab/snake identifiers only, so
# English prose ("mmx to generate ...") is filtered by the whitelist below
# rather than by guessing at sentence context.
REF = re.compile(r"\b([a-z][a-z0-9-]*)\s+([a-z][a-z0-9-]*)(?:\s+([a-z][a-z0-9-]*))?")

GENERIC_USAGE = re.compile(r"^Usage:\s*\S+\s*<\S+>\s*<\S+>", re.M)
RESOURCE_TABLE = re.compile(r"^\s*(Resources|Commands|Subcommands):\s*$", re.M)


def root_help(text: str) -> bool:
    """True when the output is the top-level help rather than a command's own."""
    return bool(GENERIC_USAGE.search(text)) and bool(RESOURCE_TABLE.search(text))


def probe(tool: str, words: list[str]) -> tuple[int, str]:
    cmd = [tool, *words, "--help"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except FileNotFoundError:
        return 127, f"{tool} not found on PATH"
    except subprocess.TimeoutExpired:
        return 124, "timed out"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    doc = Path(sys.argv[1])
    tools = set(sys.argv[2:])
    if not doc.is_file():
        print(f"ERROR: {doc} not found", file=sys.stderr)
        return 2

    text = doc.read_text(encoding="utf-8", errors="ignore")

    # 1) candidates from the tool names the caller named
    seen: list[tuple[str, list[str]]] = []
    for tool, a, b in REF.findall(text):
        if tool not in tools:
            continue
        for words in ([tool, a], [tool, a, b]):
            key = tuple(words[1:])
            if (tool, words) not in seen and key not in {k for _, k in seen}:
                seen.append((tool, words))

    # 2) every resource/command pair named anywhere (tables included)
    for tool, a, b in REF.findall(text):
        if tool in tools and (tool, [a]) not in seen:
            seen.append((tool, [a]))

    if not seen:
        print(f"no `{sorted(tools)}` command references found in {doc}")
        return 0

    print(f"probing {len(seen)} reference(s) in {doc}\n")
    bad: list[tuple[str, list[str]]] = []
    for tool, words in seen:
        code, out = probe(tool, words)
        if root_help(out):
            bad.append((tool, words))
            status = "ROOT-FALLBACK (does not exist)"
        elif code == 127:
            status = "TOOL-NOT-FOUND"
        else:
            status = "ok"
        print(f"  {' '.join(words):<40} exit={code:<4} {status}")

    print()
    if bad:
        print(f"NEEDS REVIEW ({len(bad)}):")
        for tool, words in bad:
            print(f"  {' '.join(words)}")
        print(
            "\nEach hit is either a fabrication to remove, or prose that "
            "deliberately quotes a non-existent command. Read the line before "
            "acting."
        )
        return 1

    print(f"OK: all {len(seen)} reference(s) resolve to real commands")
    return 0


if __name__ == "__main__":
    sys.exit(main())
