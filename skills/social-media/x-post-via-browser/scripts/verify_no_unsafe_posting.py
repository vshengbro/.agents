#!/usr/bin/env python3
"""Block a commit that would break one of X's non-negotiable rules.

Each rule here exists because breaking it had a concrete, measured cost.
They are not style preferences.

  no mouse/keys     the user's pointer and OS focus are never taken from
                    them, whatever browser the script drives
  no clipboard      paste hangs in this environment and bypasses Draft's
                    own input path, which is the only path that works
  no open IME       imeSetComposition STARTS a composition; uncommitted it
                    makes Chrome treat the page as holding unsaved input
  no clearing       clearing a composer raises Chrome's unsaved-changes
                    dialog, and that modal then blocks every later CDP
                    call until a human dismisses it
  verify            CLICKED is not evidence a post happened

WHAT CHANGED FROM THE OLD GUARD, AND WHY

The old guard banned every page load and every tab spawn, because the
scripts drove the USER'S OWN browser and every load made that person
confirm it in their UI. The scripts now drive a DEDICATED headless Chrome
over a private copy of the profile, so a load is invisible to the user and
the rule no longer describes a real cost. A guard that blocks the working
architecture is a guard that gets removed.

The rules that survived the change are the ones that cost something
regardless of which browser is driven, and the new guard adds the two
that the dedicated browser made possible:

  no daily browser  a script must never drive the user's DAILY Chrome --
                    the one holding their real session. Only the dedicated
                    instance is ours to drive.
  no profile write  the user's real Chrome profile is READ-ONLY input: the
                    session cookies are copied out of it, never written
                    back into it.

The check is syntactic on purpose. A behavioural check would have to run
the publisher against the live site, which is exactly what must not happen
on a commit. Syntactic rules can be defeated by a determined editor, but
they hold against the ordinary failure mode -- a new script written months
from now by someone who does not remember why the rule exists -- and every
rule in this file was broken by exactly that.

Usage:
    verify_no_unsafe_posting.py --staged     check the staged diff
    verify_no_unsafe_posting.py PATH ...      check the given files/dirs
    verify_no_unsafe_posting.py --self-test   prove each rule fires

Exit codes: 0 clean, 1 violations, 2 self-test failed.
"""
from __future__ import annotations

import argparse
import ast
import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

# Each entry: (id, what is banned, why, how to spot it).
#
# The pattern is matched against the source with comments and docstrings
# removed first, so prose that MENTIONS a banned call (the skill's own notes
# do) is not a violation while an actual call is.
RULES: list[tuple[str, str, str, str]] = [
    (
        "no-mouse-keyboard",
        "taking the mouse or the OS keyboard",
        "the user's pointer and focus are never taken from them",
        r"""\bsend\s*\(\s*["']Page\.bringToFront["']|"""
        r"""\bsend\s*\(\s*["']Input\.dispatchMouseEvent["']|"""
        r"""\bsend\s*\(\s*["']Input\.dispatchKeyEvent["']|"""
        r"""\bbring_to_front\b|\bclick_at_xy\b|"""
        r"""\bosascript\b|\bpyautogui\b|"""
        r"""\bcliclick\b|\bkeyboard\.post\b""",
    ),
    (
        "no-clipboard",
        "the clipboard",
        "paste hangs in this environment and bypasses the only input path "
        "that works",
        r"\bpbcopy\b|\bpbpaste\b|"
        r"""\bsend\s*\([^\)]{0,400}?["']paste["']""",
    ),
    (
        "no-open-ime",
        "imeSetComposition without a commit",
        "an uncommitted IME composition makes Chrome claim the page holds "
        "unsaved input, and Escape discards the whole post",
        r"\bimeSetComposition\b",
    ),
    (
        "no-clearing",
        "emptying a composer (select-all + delete, Backspace loop)",
        "raises Chrome's unsaved-changes dialog, which then blocks every "
        "later CDP call",
        r"""\bexecCommand\s*\(\s*["'](delete|selectAll)["']\s*\)|"""
        r"""\bsend\s*\([^\)]{0,400}?Backspace""",
    ),
]

# Rules checked over the WHOLE FILE rather than over one expression.
#
# The daily-browser rule is one of these because a token-local pattern
# cannot see it: a script that assigns the real profile path to a variable
# and then builds the argument from that variable defeats any pattern that
# expects the two to sit side by side. What is catchable is the FILE
# holding both the real profile's location AND a --user-data-dir
# argument -- because putting those two in one file is the mistake, whether
# the path is spelled inline or through a variable.
#
# The scripts that READ the real profile are fine: xconfig.py holds its
# location and no file both reads it and launches a browser against it.
FILE_RULES: list[tuple[str, str, str, str, str]] = [
    (
        "no-daily-browser",
        "launching a browser against the user's daily Chrome",
        "that browser holds their real session and their real window; only "
        "the dedicated instance is ours to drive",
        r"Application\s+Support",
        r"--user-data-dir",
    ),
    (
        "no-profile-write",
        "writing into the user's real Chrome profile",
        "the real profile is READ-ONLY input: the session cookies are copied "
        "out of it, never written back into it",
        r"Application\s+Support",
        r"shutil\s*\.\s*(copy2|copyfile|move|rmtree)\s*\(|"
        r"sqlite3\s*\.\s*connect\s*\(\s*[\"']",
    ),
]

# imeSetComposition is legal ONLY when the same file also closes the
# composition. An explicit insertText right after the composition counts too.
COMMIT_EVIDENCE = re.compile(
    r"close_composition|commitText|insertText", re.IGNORECASE)


def _docstring_lines(src: str) -> list[tuple[int, int]]:
    """Line ranges covered by module/class/function docstrings."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    spans: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef,
                                 ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", [])
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            d = body[0]
            spans.append((d.lineno, getattr(d, "end_lineno", d.lineno)))
    return spans


def code_tokens(src: str):
    """(line_number, text) for every real token, with its true position.

    Comments, indentation and NEWLINE are dropped. String literals are KEPT:
    the banned CDP method names and the "paste" command are string ARGUMENTS,
    so dropping them would drop the evidence. Docstrings are excluded by line
    range instead -- the AST knows exactly which strings are docstrings, and
    the skill's own notes mention banned calls in prose that must not count.

    ast.unparse() is the wrong tool here: it rebuilds the source from the
    AST, so a match's line number points at a line unrelated to the
    original. That reported a clean file as violating at lines 382/574/789.
    """
    doc_lines = _docstring_lines(src)
    skip = (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
            tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER)
    out: list[tuple[int, str]] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in skip:
                continue
            if tok.type == tokenize.STRING:
                line = tok.start[0]
                if any(lo <= line <= hi for lo, hi in doc_lines):
                    continue
            out.append((tok.start[0], tok.string))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return [(n + 1, line) for n, line in enumerate(src.splitlines())]
    return out


def _is_string_literal(tok: str) -> bool:
    """Whether a token is a Python string literal.

    The quote may be repeated (''' or \"\"\"), so the check is on the
    quote CHARACTER, not on the length.
    """
    return bool(tok) and tok[0] in "\"'"


def strip_js_comments(tok: str) -> str:
    """Remove the // and /* */ comments from a string literal's CONTENT.

    A JS template in this skill carries its own explanatory notes, and a
    note that names a banned call reads to a pattern matcher as a call:
    "execCommand('delete') is a banned call" is prose, and the guard
    reported it as a violation. A real call is code, and code is what is
    left after the comments are gone.

    The CONTENT is what is stripped, not the Python quoting: the content
    of a Python string literal in this skill IS JavaScript, so the
    comments inside it are JavaScript comments. The quoting is put back
    afterwards, unchanged, so the token still reads as the literal it was.
    """
    m = re.match(r"([rRbBuUfF]*)(\"\"\"|'''|\"|')", tok)
    if not m:
        return tok
    prefix, quote = m.group(1), m.group(2)
    body = tok[len(prefix) + len(quote):]
    if body.endswith(quote):
        body = body[:-len(quote)]
    return prefix + quote + _strip_js_comments_js(body) + quote


def _strip_js_comments_js(text: str) -> str:
    """Remove the // and /* */ comments from a JavaScript source string.

    The string literals inside the JavaScript are NOT touched -- the banned
    CDP method names are string ARGUMENTS, and dropping them would drop
    the evidence.
    """
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if ch in "\"'`":
            quote = ch
            out.append(ch)
            i += 1
            while i < n:
                if text[i] == "\\" and i + 1 < n:
                    out.append(text[i:i + 2])
                    i += 2
                    continue
                out.append(text[i])
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def check_syntax(path: Path) -> list[str]:
    try:
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        return [f"{path}: does not parse ({exc.msg} line {exc.lineno})"]
    return []


def check_file(path: Path) -> list[str]:
    """Report every banned call in one file, with its real line number.

    Matches run over the joined token text (so a banned name split across lines
    is still found) and each hit is mapped back to the line its FIRST token
    starts on -- which is why line numbers are trustworthy here.

    A JS TEMPLATE IS A STRING, AND A STRING IS EVIDENCE. The skill's own
    notes live inside the templates as comments, and a note that says
    "execCommand('delete') is a banned call" reads to a pattern matcher as
    a call. So the banned-call patterns are checked against the string
    LITERALS only, with the notes inside them removed: a template's own
    explanatory text is prose, and a real call is code.
    """
    problems: list[str] = []
    src = path.read_text(encoding="utf-8", errors="replace")
    toks = code_tokens(src)
    # A JS template carries its own notes, and a note naming a banned call
    # is prose, not a call. The notes are stripped from the string literals
    # before the patterns run; the literals themselves are kept, because
    # the banned CDP method names ARE string arguments.
    toks = [(ln, strip_js_comments(tok) if _is_string_literal(tok) else tok)
            for ln, tok in toks]
    # Join with a space: a newline between tokens would split `send(` from
    # `"Page.reload"` and most patterns would stop matching.
    code = " ".join(tok for _, tok in toks)
    tok_line = [ln for ln, _ in toks]

    for rid, banned, why, pattern in RULES:
        rx = re.compile(pattern, re.IGNORECASE | re.DOTALL)
        lines: set[int] = set()
        # Map each match back to the line its first token starts on. A space
        # separator means one token per "word", so walk the code alongside the
        # token list rather than counting newlines.
        starts = []
        pos = 0
        for tok in toks:
            starts.append(pos)
            pos += len(tok[1]) + 1
        for m in rx.finditer(code):
            i = max((j for j, s in enumerate(starts) if s <= m.start()),
                    default=None)
            if i is not None and i < len(tok_line):
                lines.add(tok_line[i])
        if not lines:
            continue
        if rid == "no-open-ime" and COMMIT_EVIDENCE.search(code):
            continue                      # committed, therefore fine
        shown = sorted(lines)[:6]
        problems.append(
            f"{path}: [{rid}] {banned} — {why}"
            f" (line{'s' if len(shown) > 1 else ''} "
            f"{', '.join(str(n) for n in shown)})")

    # The file-level rules. The source is read with docstrings stripped, so
    # a note MENTIONING the real profile's location does not count.
    stripped = "\n".join(
        line for n, line in enumerate(src.splitlines(), 1)
        if not any(lo <= n <= hi for lo, hi in _docstring_lines(src)))
    for rid, banned, why, first_pat, second_pat in FILE_RULES:
        if not (re.search(first_pat, stripped)
                and re.search(second_pat, stripped)):
            continue
        problems.append(
            f"{path}: [{rid}] {banned} — {why}")
    return problems


def staged_files(repo: str | None) -> list[Path]:
    root = Path(repo or subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True).stdout.strip() or ".")
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=root, capture_output=True, text=True).stdout
    files = []
    for line in out.splitlines():
        line = line.strip()
        if not line or line.endswith(".lock"):
            continue
        p = root / line
        # Only the browser-driving scripts can break these rules; prose and
        # copy files cannot.
        if p.suffix == ".py" and ("scripts" in p.parts or "hooks" in p.parts):
            files.append(p)
    return files


def collect(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.py")))
        elif p.suffix == ".py":
            files.append(p)
    return files


# --- self-test: each rule must actually fire ---------------------------
FIXTURES = {
    "no-mouse-keyboard": 'c.send("Page.bringToFront")',
    "no-mouse-keyboard-2": 'c.send("Input.dispatchMouseEvent", type="mousePressed")',
    "no-mouse-keyboard-3": 'c.send("Input.dispatchKeyEvent", type="keyDown")',
    "no-mouse-keyboard-4": "import pyautogui\npyautogui.click(1, 2)\n",
    "no-clipboard": "subprocess.run(['pbcopy'], input=text)",
    "no-clipboard-2": 'c.send("Input.dispatchKeyEvent", commands=["paste"])',
    "no-open-ime": ('c.send("Input.imeSetComposition", text=u)  # no commit '
                    'follows'),
    "no-clearing": """c.js("document.execCommand('delete')")""",
    "no-clearing-2": ('c.send("Input.dispatchKeyEvent", type="rawKeyDown", '
                      'key="Backspace")'),
    "no-clearing-3": ('TPL = """(() => { document.execCommand("delete"); '
                      'return 1; })()"""\n'),
    "no-daily-browser": ('profile = "/Users/someone/Library/Application '
                         'Support/Google/Chrome"\n'
                         'argv = ["--user-data-dir=" + profile]\n'),
    "no-daily-browser-2": ('argv = ["--user-data-dir=/Users/someone/Library/'
                           'Application Support/Google/Chrome"]'),
    "no-profile-write": ('shutil.copy2("/Users/someone/Library/Application '
                         'Support/Google/Chrome/Default/Cookies", dst)'),
    "no-profile-write-2": ('db = sqlite3.connect("/Users/someone/Library/'
                           'Application Support/Google/Chrome/Default/Cookies")'),
}
# These must NOT fire: prose that mentions a banned call, and a legal IME use.
CLEAN = {
    "prose-mentions-navigation":
        "'''Do not take the mouse: the user keeps it.'''\n"
        "import os\nprint(os.getcwd())\n",
    "ime-with-commit":
        'c.send("Input.imeSetComposition", text=u)\n'
        'c.send("Input.insertText", text=u)\nc.close_composition("")\n',
    "read-only-helpers":
        "import json, re\n"
        "def canon(s):\n    return re.sub(r'\\s+', '', s or '')\n"
        "def show_tabs(port):\n    return [t for t in port]\n",
    "reads-the-real-profile-readonly":
        "src = real_chrome_profile() / 'Default' / 'Cookies'\n"
        "backup_cookies(src, dst)\n",
    "drives-the-dedicated-browser":
        "argv = ['--user-data-dir=%s' % private]\n"
        "await b.new_tab('https://x.com/home')\n"
        "await b.call('Page.navigate', {'url': url})\n",
    "notes-mention-a-banned-call":
        "TPL = '''(() => {\n"
        "  // execCommand('delete') is a banned call: it raises the\n"
        "  // unsaved-changes dialog, which blocks every later CDP call.\n"
        "  // We do not use it; the copy goes in through Input.insertText.\n"
        "  return 1;\n"
        "})()'''\n",
}


def self_test() -> int:
    failures: list[str] = []
    for name, body in FIXTURES.items():
        rid = next(r for r, *_ in RULES + FILE_RULES if name.startswith(r))
        p = Path(f"/tmp/_xguard_{name}.py")
        p.write_text("import time, subprocess, shutil, sqlite3, os\n"
                     + body + "\n", encoding="utf-8")
        hits = check_file(p)
        if not any(f"[{rid}]" in h for h in hits):
            failures.append(
                f"rule {rid} did NOT fire on fixture {name} "
                f"(got: {hits or 'nothing'})")
        p.unlink(missing_ok=True)

    for name, body in CLEAN.items():
        p = Path(f"/tmp/_xguard_clean_{name}.py")
        p.write_text(body, encoding="utf-8")
        got = check_file(p)
        if got:
            failures.append(f"false positive on {name}: {got}")
        p.unlink(missing_ok=True)

    if failures:
        print("SELF-TEST FAILED", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 2
    print(f"self-test ok — {len(FIXTURES)} fixtures fire, "
          f"{len(CLEAN)} clean cases stay clean")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--repo")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    files = staged_files(args.repo) if args.staged else collect(
        [Path(p) for p in args.paths])
    if not files:
        print("x-posting guard: no browser-driving scripts among the changes")
        return 0

    problems: list[str] = []
    me = Path(__file__).resolve()
    for f in files:
        if not f.exists():
            continue
        if f.resolve() == me:
            continue          # the rule table is the checker; do not scan it
        problems.extend(check_syntax(f))
        problems.extend(check_file(f))

    if not problems:
        print(f"x-posting guard: {len(files)} script(s) clean")
        return 0

    print("x-posting guard: BLOCKED", file=sys.stderr)
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    print("", file=sys.stderr)
    print("These are the rules that keep the user's browser and account safe.",
          file=sys.stderr)
    print("Each one was learned from a concrete failure — see the comment on",
          file=sys.stderr)
    print("each rule in verify_no_unsafe_posting.py for what it costs.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
