#!/usr/bin/env python3
"""Structural audit for the skill library (`skills/**/SKILL.md`).

Offline checks only — never touches the network, never invokes an LLM, and
never writes inside the repository. Everything it can prove is a *structural*
property of the files on disk:

  * every real SKILL.md is discovered recursively (categories included);
  * frontmatter parses as a YAML mapping, `name` matches the folder, the
    description is non-empty / bounded / not a keyword dump, and names are
    globally unique;
  * non-protected entries stay inside the line budget;
  * fenced code blocks balance;
  * relative links and heading anchors resolve, with GitHub slug rules
    (percent-decoding, Unicode, duplicate-heading suffixes);
  * the protected subtree matches the baseline fingerprint exactly;
  * skills that vanished from the baseline leave no dangling references.

Route fixtures compare independently supplied selections with expected intent.
No router or model is simulated here; missing results fail rather than pass.

Usage
-----
    python3 scripts/audit_skills.py \
        --baseline /path/baseline.json \
        --protected-prefix skills/rust-standards/ \
        --json /tmp/audit.json

Exit codes
----------
    0  no failures (warnings may still be printed)
    1  at least one failure
    2  usage / IO error
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIRNAME = "skills"
LOCK_FILENAME = ".skill-lock.json"

MAX_DESCRIPTION = 240
MAX_ENTRY_LINES = 160
MAX_DESCRIPTION_WORDS = 60  # a "keyword dump" reads far denser than a trigger

# The Rust subtree is frozen by design (see scripts/README.md and
# `update_skill_lock.py --preserve-prefix`): it is the reference copy of the
# Rust standard and stays long-form on purpose, so the entry-point budget
# does not apply to it. It is protected by default; `--protected-prefix`
# adds further prefixes on top.
DEFAULT_PROTECTED_PREFIXES = ("skills/rust-standards/",)

# Subtrees vendored verbatim from an upstream repository (see
# scripts/sync-mcode-stack.sh and scripts/sync-minimax-skills.sh). Their
# SKILL.md text belongs to the upstream author: we must not rewrite it, so
# the local budgets that assume locally authored text do not apply to them.
# Everything else (frontmatter shape, name/folder match, global name
# uniqueness) is still enforced. Waived for a vendored subtree:
# description length and keyword dump, the entry line budget, and the
# relative-link and anchor checks (upstream links may be broken upstream).
DEFAULT_VENDORED_PREFIXES = (
    "skills/mcode-stack/", "skills/minimax-skills/", "skills/blender-skills/",
    # Installed by `agents-cli setup` from google/agents-cli, byte-identical to
    # upstream (verified file by file). The installer writes each skill flat at
    # `skills/<name>/`, so they cannot be grouped under one vendored folder
    # without breaking the registered skill paths in `.skill-lock.json`.
    "skills/google-agents-cli-adk-code/",
    "skills/google-agents-cli-deploy/",
    "skills/google-agents-cli-eval/",
    "skills/google-agents-cli-observability/",
    "skills/google-agents-cli-publish/",
    "skills/google-agents-cli-scaffold/",
    "skills/google-agents-cli-workflow/",
)

# Relative links carrying any of these are documentation placeholders, not
# claims about a real file. They are reported in `skipped` — never dropped
# silently — so a reviewer can disagree with the classification.
PLACEHOLDER_RE = re.compile(r"[<>{}…]|\.\.\.|path/to|your[-_]|PATH_TO|<name>")

EXTERNAL_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)")
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
INLINE_LINK_RE = re.compile(r"(?<!\!)\[(?:[^\]\\]|\\.)*\]\(\s*([^\s)]+)((?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?)\s*\)")
REF_DEF_RE = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(\S+)")
REF_USE_RE = re.compile(r"(?<!\!)\[(?:[^\]\\]|\\.)*\]\[([^\]]*)\]")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------
# markdown structure
# --------------------------------------------------------------------------
def strip_code_and_scan(text: str) -> tuple[list[tuple[int, int, str]], list[tuple[int, int, str]]]:
    """Return (headings, fenced blocks) with fenced regions excluded.

    Fenced regions are blanked out of the text that is searched for links, so
    a `curl` example or a shell snippet can never be read as a claim about a
    sibling file.
    """
    lines = text.splitlines()
    keep: list[str] = []
    headings: list[tuple[int, int, str]] = []
    fences: list[tuple[int, int, str]] = []
    open_fence: tuple[str, int] | None = None
    open_line = 0
    for idx, line in enumerate(lines, 1):
        m = FENCE_RE.match(line)
        if open_fence is None:
            if m:
                marker, info = m.group(2), m.group(3)
                open_fence, open_line = (marker[0], len(marker)), idx
                keep.append("")
                continue
            hm = HEADING_RE.match(line)
            if hm:
                headings.append((idx, len(hm.group(1)), hm.group(2)))
            keep.append(line)
        else:
            if m and m.group(2)[0] == open_fence[0] and len(m.group(2)) >= open_fence[1]:
                fences.append((open_line, idx, open_fence[0]))
                open_fence = None
                keep.append("")
                continue
            keep.append("")
    if open_fence is not None:
        fences.append((open_line, len(lines), "UNTERMINATED:" + open_fence[0]))
    return headings, fences


def github_slug(text: str) -> str:
    """Approximate GitHub's heading slug.

    Lowercase, strip inline markup, drop punctuation (Unicode aware, so CJK
    survives), spaces -> hyphens. GitHub additionally appends `-1`, `-2` to
    repeated slugs; that disambiguation happens in `anchor_set`.
    """
    s = text.strip()
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]*)\]\[[^\]]*\]", r"\1", s)
    s = re.sub(r"`+([^`]*)`+", r"\1", s)
    s = re.sub(r"(\*\*\*|\*\*|\*|___|__|_)(.+?)\1", r"\2", s)
    s = s.lower()
    out = []
    for ch in s:
        if ch.isalnum() or ch in "-_ " or unicodedata.category(ch).startswith("M"):
            out.append(ch)
        # everything else (punctuation, symbols) is dropped, like GitHub
    s = "".join(out)
    return s.replace(" ", "-")


def anchor_set(headings: list[tuple[int, int, str]]) -> set[str]:
    """All valid `#fragment` values for a document, with `-N` disambiguation."""
    counts: dict[str, int] = {}
    anchors: set[str] = set()
    for _, _, raw in headings:
        base = github_slug(raw)
        if not base:
            continue
        n = counts.get(base, 0)
        counts[base] = n + 1
        anchors.add(base if n == 0 else f"{base}-{n}")
    return anchors


def blank_fenced_code(text: str) -> str:
    """Same length as `text`, with every fenced region replaced by blanks.

    Working line-by-line (rather than reusing `strip_code_and_scan`) keeps
    line numbers aligned so reported findings can be traced back to the file.
    """
    blanked: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if in_fence:
            if m and m.group(2)[0] == fence_marker[0] and len(m.group(2)) >= len(fence_marker):
                in_fence = False
            blanked.append("")
            continue
        if m:
            in_fence, fence_marker = True, m.group(2)
            blanked.append("")
            continue
        blanked.append(line)
    return "\n".join(blanked)


def iter_links(text: str) -> list[tuple[str, str]]:
    """(url, kind) for every link outside fenced code. kind in {inline, ref}."""
    code_free = blank_fenced_code(text)

    found: list[tuple[str, str]] = []
    for m in INLINE_LINK_RE.finditer(code_free):
        found.append((m.group(1), "inline"))
    defs = {m.group(1).lower(): m.group(2) for m in (REF_DEF_RE.match(l) for l in code_free.splitlines()) if m}
    for m in REF_USE_RE.finditer(code_free):
        key = (m.group(1) or "").lower()
        if key in defs:
            found.append((defs[key], "ref"))
    return found


# --------------------------------------------------------------------------
# audit pieces
# --------------------------------------------------------------------------
class Report:
    def __init__(self) -> None:
        self.failures: list[dict] = []
        self.warnings: list[dict] = []
        self.skipped: dict[str, list[str]] = {}
        self.stats: dict[str, object] = {}

    def fail(self, check: str, path: str, detail: str) -> None:
        self.failures.append({"check": check, "path": path, "detail": detail})

    def warn(self, check: str, path: str, detail: str) -> None:
        self.warnings.append({"check": check, "path": path, "detail": detail})

    def skip(self, bucket: str, item: str) -> None:
        self.skipped.setdefault(bucket, []).append(item)


def split_frontmatter(text: str) -> tuple[str | None, str, str | None]:
    """(frontmatter_text_or_None, body, parse_error_or_None)."""
    if not text.startswith("---"):
        return None, text, "no YAML frontmatter (file must start with ---)"
    m = re.match(r"^---\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", text, re.S)
    if not m:
        return None, text, "unterminated YAML frontmatter"
    raw = m.group(1)
    body = text[m.end():]
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return raw, body, f"YAML error: {exc}"
    if not isinstance(data, dict):
        return raw, body, f"frontmatter is {type(data).__name__}, expected a mapping"
    return raw, body, None


def iter_skill_dirs(skills_dir: Path) -> list[Path]:
    """Every directory under skills/ holding a SKILL.md, at any depth.

    Dot-prefixed components and `_pending` are skipped, matching the lock
    reconciler's discovery rule.
    """
    return sorted(
        path.parent
        for path in skills_dir.rglob("SKILL.md")
        if not any(part.startswith(".") or part == "_pending"
                   for part in path.relative_to(skills_dir).parts[:-1])
    )


def under(rel: str, prefixes: tuple[str, ...]) -> bool:
    return any(rel == p.rstrip("/") or rel.startswith(p.rstrip("/") + "/") for p in prefixes)


def check_frontmatter(path: Path, rel: str, rep: Report,
                      enforce_budget: bool = True,
                      waive_description_budget: bool = False) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    raw, _body, err = split_frontmatter(text)
    if err or raw is None:
        rep.fail("frontmatter.parse", rel, err or "unreadable frontmatter")
        return None
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:  # pragma: no cover - already validated
        rep.fail("frontmatter.parse", rel, str(exc))
        return None

    folder = Path(rel).parent.name
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        rep.fail("frontmatter.name_present", rel, "`name` missing or not a string")
        name = None
    elif name != folder:
        rep.fail("frontmatter.name_matches_folder", rel,
                 f"name={name!r} but folder={folder!r}")

    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        rep.fail("description.nonempty", rel, "`description` missing or empty")
    else:
        if enforce_budget and not waive_description_budget and len(desc) > MAX_DESCRIPTION:
            rep.fail("description.length", rel,
                     f"{len(desc)} chars > {MAX_DESCRIPTION} budget")
        words = desc.split()
        if enforce_budget and not waive_description_budget and len(words) > MAX_DESCRIPTION_WORDS:
            rep.fail("description.keyword_dump", rel,
                     f"{len(words)} whitespace tokens > {MAX_DESCRIPTION_WORDS}; "
                     "reads as a keyword dump, not a trigger")
    return data


def check_fences(rel: str, fences, rep: Report) -> None:
    for start, _end, marker in fences:
        if marker.startswith("UNTERMINATED"):
            rep.fail("fence.unterminated", rel,
                     f"fence opened at line {start} is never closed")


def check_links(path: Path, rel: str, rep: Report, skills_root: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    headings, fences = strip_code_and_scan(text)
    check_fences(rel, fences, rep)
    anchors = anchor_set(headings)
    for url, _kind in iter_links(text):
        if EXTERNAL_RE.match(url):
            continue
        if url.startswith("#"):
            frag = unquote(url[1:]).lower()
            if frag and frag not in anchors:
                rep.fail("link.anchor_missing", rel,
                         f"#{url[1:]} has no matching heading in {path.name}")
            continue
        target_raw, _, frag = url.partition("#")
        target_raw = unquote(target_raw)
        if PLACEHOLDER_RE.search(target_raw):
            rep.skip("placeholder_links", f"{rel}: {url}")
            continue
        target = (path.parent / target_raw).resolve()
        try:
            target.relative_to(skills_root.resolve())
        except ValueError:
            rep.skip("out_of_tree_links", f"{rel}: {url}")
            continue
        if not target.exists():
            rep.fail("link.target_missing", rel,
                     f"{url} -> {target} does not exist")
            continue
        if frag:
            t_headings, _ = strip_code_and_scan(
                target.read_text(encoding="utf-8", errors="replace"))
            t_anchors = anchor_set(t_headings)
            f = unquote(frag).lower()
            if f not in t_anchors:
                rep.fail("link.anchor_missing", rel,
                         f"{url} -> anchor #{frag} not in {target.name}")


def audit_history_debt(skills_dir: Path, prefixes: tuple[str, ...],
                       rep: Report) -> dict:
    """Run the rust-standards history-debt checker over the protected subtree.

    The protected skill must state only the current rules: dated provenance,
    iteration labels, PR references and withdrawn-rule markers are historical
    debt. The checker lives with the skill it polices, so the rule and its
    enforcement ship together.
    """
    checker = skills_dir / "rust-standards" / "scripts" / "verify_no_history_debt.py"
    result = {"checker": str(checker.relative_to(skills_dir.parent)),
              "ran": False, "hits": []}
    skill_root = skills_dir / "rust-standards"
    if not skill_root.is_dir():
        # The protected skill is not installed in this tree; there is nothing
        # to police. Absence is not a failure.
        result["skipped"] = "rust-standards skill not present"
        return result
    if not checker.is_file():
        # The checker ships with the skill it polices. A tree that does not
        # install the protected skill (test fixtures, partial checkouts) has
        # nothing to police — that is a skip, not a failure. The real repo
        # asserts the checker exists in its own test suite.
        rep.skip("history_debt", str(checker.relative_to(skills_dir.parent)))
        result["skipped"] = "checker not installed in this tree"
        return result
    try:
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(checker), str(skills_dir / "rust-standards")],
            capture_output=True, text=True, check=False)
    except OSError as exc:
        rep.fail("history_debt.checker_failed",
                 str(checker.relative_to(skills_dir.parent)), str(exc))
        return result
    result["ran"] = True
    if proc.returncode != 0:
        for line in proc.stdout.splitlines():
            if not line.strip() or line.startswith("FAIL:"):
                continue
            result["hits"].append(line)
            rel, _, rest = line.partition(":")
            rep.fail("history_debt.marker", rel, rest.strip()[:200])
    return result


def audit_protected(skills_dir: Path, prefixes: tuple[str, ...],
                    baseline: dict | None, rep: Report) -> dict:
    """Exact set + sha256 comparison against the baseline for protected files.

    Without a baseline there is no reference set to compare against, so the
    fingerprint check is skipped: an empty expected set would otherwise mark
    every file in the protected tree as newly added.
    """
    result: dict = {"prefixes": list(prefixes), "baseline_files": 0, "on_disk": 0,
                    "added": [], "deleted": [], "modified": [], "ok": True,
                    "compared": False}
    if not prefixes:
        return result
    base_files = (baseline or {}).get("files", {})
    if not base_files:
        # No baseline: report the on-disk count only, and compare nothing.
        for pfx in prefixes:
            root = skills_dir.parent / pfx.rstrip("/")
            if not root.exists():
                continue
            result["on_disk"] += sum(1 for p in root.rglob("*") if p.is_file())
        return result
    expected = {k: v for k, v in base_files.items() if under(k, prefixes)}

    actual: dict[str, Path] = {}
    for pfx in prefixes:
        root = skills_dir.parent / pfx.rstrip("/")
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file():
                actual[str(p.relative_to(skills_dir.parent))] = p

    result["baseline_files"] = len(expected)
    result["on_disk"] = len(actual)
    result["compared"] = True
    for rel in sorted(set(expected) - set(actual)):
        result["deleted"].append(rel)
    for rel in sorted(set(actual) - set(expected)):
        result["added"].append(rel)
    for rel in sorted(set(expected) & set(actual)):
        want = expected[rel].get("sha256")
        got = sha256_of(actual[rel])
        if want and want != got:
            result["modified"].append(
                {"path": rel, "baseline_sha256": want, "actual_sha256": got})

    if result["deleted"] or result["added"] or result["modified"]:
        result["ok"] = False
        for rel in result["deleted"]:
            rep.fail("protected.deleted", rel, "baseline file is gone from the protected tree")
        for rel in result["added"]:
            rep.fail("protected.added", rel, "new file inside the protected tree")
        for m in result["modified"]:
            rep.fail("protected.modified", m["path"],
                     f"sha256 {m['baseline_sha256'][:12]}… -> {m['actual_sha256'][:12]}…")
    return result


def dangling_references(skills_dir: Path, lock_path: Path, deleted: list[str],
                        prefixes: tuple[str, ...], rep: Report) -> dict:
    """Find leftover mentions of skills that no longer exist.

    Only high-signal forms are hard failures: literal `skills/<name>/SKILL.md`
    paths, `name:` frontmatter values, and `skill_view`/`skill_manage` call
    arguments. A bare word match is reported separately for review, because a
    bare token may legitimately be an unrelated API string.
    """
    out = {"deleted_skills": deleted, "hard": [], "review": [], "scanned_files": 0}
    if not deleted:
        return out
    names = {Path(p).parent.name: p for p in deleted}
    alt = "|".join(re.escape(n) for n in sorted(names))
    # Any `<...>/<name>/SKILL.md` path form: repo-relative (`skills/x/SKILL.md`)
    # or sibling-relative (`./x/SKILL.md`, `../cat/x/SKILL.md`). Only a literal
    # path is a hard failure — a bare token is reviewed, never assumed.
    hard_pat = re.compile(
        r"(?:[\w.\-]+/)*(?:" + alt + r")/SKILL\.md"
    )
    tool_pat = re.compile(
        r"(?:skill_view|skill_manage|skills_list)\([^)]*?['\"]([A-Za-z0-9._-]+)['\"]",
        re.S,
    )
    name_pat = re.compile(r"^\s*(?:[-*]\s*)?(?:name|skill|skills)\s*:\s*(.+)$", re.M)

    targets: list[tuple[str, str]] = []
    for p in sorted(skills_dir.rglob("*.md")):
        rel = str(p.relative_to(skills_dir.parent))
        if under(rel, prefixes):
            continue
        targets.append((rel, p.read_text(encoding="utf-8", errors="replace")))
    if lock_path.exists():
        targets.append((LOCK_FILENAME, lock_path.read_text(encoding="utf-8", errors="replace")))
    out["scanned_files"] = len(targets)

    for rel, text in targets:
        for m in hard_pat.finditer(text):
            out["hard"].append({"path": rel, "kind": "skill_path", "ref": m.group(0)})
        for m in tool_pat.finditer(text):
            if m.group(1) in names:
                out["hard"].append({"path": rel, "kind": "skill_tool_arg",
                                    "ref": m.group(1)})
        for m in name_pat.finditer(text):
            for tok in re.findall(r"[A-Za-z0-9._-]+", m.group(1)):
                if tok in names:
                    out["hard"].append({"path": rel, "kind": "metadata_name",
                                        "ref": tok})
        for name in names:
            for m in re.finditer(r"`" + re.escape(name) + r"`", text):
                out["review"].append({"path": rel, "kind": "backticked_token",
                                      "ref": name})
    for h in out["hard"]:
        rep.fail("dangling_reference", h["path"],
                 f"{h['kind']} refers to deleted skill {h['ref']!r}")
    for r in dict.fromkeys((x["ref"], x["path"]) for x in out["review"]):
        rep.warn("dangling_reference.review", r[1],
                 f"deleted skill name {r[0]!r} appears as a bare token; "
                 "confirm it is not a stale pointer")
    return out


def route_check(skills_dir: Path, cases_path: Path, rep: Report,
                results_path: Path | None = None) -> dict:
    """Compare independently adjudicated selections; never invent a router."""
    result = {"kind": "independent_intent_fixtures",
              "is_live_routing_measurement": False,
              "note": "no model was invoked by this script; supplied selections are compared exactly",
              "cases": [], "cases_total": 0, "cases_passed": 0}
    try:
        cases = json.loads(cases_path.read_text(encoding="utf-8"))
        cases = cases.get("cases", []) if isinstance(cases, dict) else cases
        if not isinstance(cases, list) or not cases:
            raise ValueError("expected a nonempty case list")
        result["cases_total"] = len(cases)
        if results_path is None:
            raise ValueError("independent --route-results is required; no selections were measured")
        selections = json.loads(results_path.read_text(encoding="utf-8"))
        selections = selections.get("selections", []) if isinstance(selections, dict) else selections
        if not isinstance(selections, list):
            raise ValueError("expected a selection list")
        expected_ids = [case["id"] for case in cases]
        selected_ids = [selection["id"] for selection in selections]
        if len(set(expected_ids)) != len(expected_ids):
            raise ValueError("duplicate fixture IDs")
        if len(set(selected_ids)) != len(selected_ids) or set(selected_ids) != set(expected_ids):
            raise ValueError("selection IDs must match every fixture exactly once")
        by_id = {selection["id"]: selection for selection in selections}
        names = {directory.name for directory in iter_skill_dirs(skills_dir)}
        for case in cases:
            expected = case["expected"]
            selected = by_id[case["id"]]["selected"]
            if expected is not None and expected not in names:
                raise ValueError(f"unknown expected skill: {expected!r}")
            if selected is not None and selected not in names:
                raise ValueError(f"unknown selected skill: {selected!r}")
            passed = selected == expected
            result["cases"].append({"id": case["id"], "expected": expected,
                                    "selected": selected, "pass": passed})
            if not passed:
                rep.fail("route_case.intent_mismatch", str(case["id"]),
                         f"expected {expected!r}, selected {selected!r}")
        result["cases_passed"] = sum(case["pass"] for case in result["cases"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        rep.fail("route_cases.invalid", str(cases_path), str(error))
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Offline structural audit of the skill library.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Exit: 0 clean / 1 failures / 2 usage or IO error.",
    )
    ap.add_argument("--repo", default=str(REPO_ROOT),
                    help="repository root (default: parent of this script)")
    ap.add_argument("--baseline", help="baseline JSON with `files` (sha256) and `skills`")
    ap.add_argument("--protected-prefix", action="append", default=[],
                    help="subtree frozen against the baseline, on top of the "
                         f"default {list(DEFAULT_PROTECTED_PREFIXES)} (repeatable)")
    ap.add_argument("--vendored-prefix", action="append", default=[],
                    help="subtree vendored verbatim from an upstream repo; the "
                         "description-length budget is waived for it, on top of "
                         f"the default {list(DEFAULT_VENDORED_PREFIXES)} (repeatable)")
    ap.add_argument("--route-cases", help="JSON fixture of expected primary-skill selections")
    ap.add_argument("--route-results", help="independent JSON selections; required with --route-cases")
    ap.add_argument("--max-entry-lines", type=int, default=MAX_ENTRY_LINES,
                    help=f"line budget for non-protected SKILL.md (default {MAX_ENTRY_LINES})")
    ap.add_argument("--json", help="also write the machine-readable report here")
    ap.add_argument("--quiet", action="store_true", help="suppress the text summary")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    skills_dir = repo / SKILLS_DIRNAME
    if not skills_dir.is_dir():
        print(f"ERROR: {skills_dir} not found", file=sys.stderr)
        return 2

    baseline = None
    if args.baseline:
        try:
            baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: baseline {args.baseline}: {exc}", file=sys.stderr)
            return 2
    prefixes = tuple(sorted(
        {p if p.endswith("/") else p + "/" for p in
         (*DEFAULT_PROTECTED_PREFIXES, *args.protected_prefix)}))
    vendored = tuple(sorted(
        {p if p.endswith("/") else p + "/" for p in
         (*DEFAULT_VENDORED_PREFIXES, *args.vendored_prefix)}))

    rep = Report()
    skill_dirs = iter_skill_dirs(skills_dir)
    protected_rels = {
        str(d.relative_to(skills_dir.parent)) + "/SKILL.md"
        for d in skill_dirs
        if under(str(d.relative_to(skills_dir.parent)), prefixes)
    }

    # ---- per-SKILL.md checks -------------------------------------------
    seen_names: dict[str, str] = {}
    before = {e["path"]: e for e in (baseline or {}).get("skills", [])}
    now_paths: set[str] = set()
    total_lines = 0
    total_bytes = 0
    protected_lines = protected_bytes = 0
    for d in skill_dirs:
        rel_skill = str((d / "SKILL.md").relative_to(repo))
        rel = str(d.relative_to(skills_dir.parent))
        now_paths.add(f"{rel}/SKILL.md")
        is_protected = rel_skill in protected_rels or under(rel, prefixes)
        is_vendored = under(rel, vendored)
        raw = (d / "SKILL.md").read_bytes()
        # splitlines() semantics (a final newline does not add a line), so
        # counts are directly comparable with the baseline's `lines` field.
        n_lines = len(raw.decode("utf-8", "replace").splitlines())
        total_bytes += len(raw)
        if is_protected:
            protected_lines += n_lines
            protected_bytes += len(raw)
        else:
            total_lines += n_lines

        data = check_frontmatter(d / "SKILL.md", rel_skill, rep,
                                 enforce_budget=not is_protected,
                                 waive_description_budget=is_vendored)
        name = (data or {}).get("name") or d.name
        if name in seen_names:
            rep.fail("name.global_unique", rel_skill,
                     f"duplicate skill name {name!r}, already used by {seen_names[name]}")
        else:
            seen_names[name] = rel_skill
        if not is_protected and not is_vendored and n_lines > args.max_entry_lines:
            rep.fail("entry.line_budget", rel_skill,
                     f"{n_lines} lines > {args.max_entry_lines} budget for a non-protected entry")
        if not is_protected and not is_vendored:
            check_links(d / "SKILL.md", rel_skill, rep, skills_dir)

    # ---- supporting .md: only new/changed vs baseline -------------------
    # A supporting file is link-checked when it is NEW or CHANGED vs the
    # baseline; unchanged files are skipped (their links were already valid).
    base_files = (baseline or {}).get("files", {})
    supporting_scanned = 0
    supporting_skipped = 0
    for md in sorted(skills_dir.rglob("*.md")):
        rel = str(md.relative_to(repo))
        if md.name == "SKILL.md" or under(rel, prefixes) or under(rel, vendored):
            continue
        rec = base_files.get(rel)
        unchanged = bool(rec and rec.get("sha256")) and rec["sha256"] == sha256_of(md)
        if unchanged:
            supporting_skipped += 1
            continue
        supporting_scanned += 1
        check_links(md, rel, rep, skills_dir)

    # ---- protected incoming links (pointing at mutable files) ----------
    for md in sorted(skills_dir.rglob("*.md")):
        rel = str(md.relative_to(repo))
        if not under(rel, prefixes):
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        _h, fences = strip_code_and_scan(text)
        for url, _k in iter_links(text):
            if EXTERNAL_RE.match(url) or url.startswith("#"):
                continue
            target_raw, _, frag = url.partition("#")
            if PLACEHOLDER_RE.search(target_raw):
                continue
            target = (md.parent / unquote(target_raw)).resolve()
            try:
                target_rel = str(target.relative_to(repo))
            except ValueError:
                continue
            if under(target_rel, prefixes):
                continue
            if not target.exists():
                # A frozen file pointing at a deleted entry point is the one
                # kind of incoming link we may not repair by editing rust, so
                # the target entry point must survive. Surface it loudly.
                rep.fail("protected_incoming.target_missing", rel,
                         f"{url} -> {target_rel} does not exist; the linked "
                         "entry point must be kept because a frozen file "
                         "depends on it")
                continue
            th, _ = strip_code_and_scan(target.read_text(encoding="utf-8", errors="replace"))
            if frag and unquote(frag).lower() not in anchor_set(th):
                rep.fail("protected_incoming.anchor_missing", rel,
                         f"{url} -> #{unquote(frag)} missing in {target_rel}")

    # ---- protected fingerprint ----------------------------------------
    fingerprint = audit_protected(skills_dir, prefixes, baseline, rep)

    # ---- history debt in the protected subtree ------------------------
    history_debt = audit_history_debt(skills_dir, prefixes, rep)

    # ---- before/after metrics ------------------------------------------
    old_files = (baseline or {}).get("files", {})
    def entry_changed(path):
        old_file = old_files.get(path, {})
        if old_file.get("sha256"):
            return old_file["sha256"] != sha256_of(repo / path)
        return before[path].get("bytes") != (repo / path).stat().st_size

    deleted = sorted(p for p in before if p not in now_paths and not under(p, prefixes))
    added = sorted(p for p in now_paths if p not in before)
    modified = sorted(p for p in now_paths
                      if p in before and entry_changed(p))
    nonprot_before = [e for p, e in before.items() if not under(p, prefixes)]

    def tot(rows, key):
        return sum(int(r.get(key) or 0) for r in rows)

    rows_now = [{"bytes": (repo / p).stat().st_size,
                 "lines": len((repo / p).read_bytes()
                              .decode("utf-8", "replace").splitlines())}
                for p in sorted(now_paths) if not under(p, prefixes)]
    tree_now = {str(p.relative_to(repo)): p.stat().st_size
                for p in skills_dir.rglob("*") if p.is_file()}
    old_tree_rows = {p: row for p, row in old_files.items() if p.startswith("skills/")}
    tree_sizes_known = bool(old_files) and all("bytes" in row for row in old_tree_rows.values())
    old_tree = {p: row.get("bytes", 0) for p, row in old_tree_rows.items()}
    metrics = {
        "skills_total_now": len(skill_dirs),
        "protected_skills": len(protected_rels),
        "mutable_skills": len(skill_dirs) - len(protected_rels),
        "skills_baseline": len(before),
        "mutable_bytes_before": tot(nonprot_before, "bytes"),
        "mutable_bytes_after": sum(r["bytes"] for r in rows_now),
        "mutable_lines_before": tot(nonprot_before, "lines"),
        "mutable_lines_after": sum(r["lines"] for r in rows_now),
        "mutable_tree_bytes_before": (sum(size for p, size in old_tree.items()
                                           if not under(p, prefixes)) if tree_sizes_known else None),
        "mutable_tree_bytes_after": sum(size for p, size in tree_now.items()
                                        if not under(p, prefixes)),
        "library_tree_bytes_before": sum(old_tree.values()) if tree_sizes_known else None,
        "library_tree_bytes_after": sum(tree_now.values()),
        "protected_bytes_now": protected_bytes,
        "protected_lines_now": protected_lines,
        "total_entry_bytes_now": total_bytes,
        "deleted_skills": deleted,
        "added_skills": added,
        "modified_skills": modified,
        "supporting_md_scanned": supporting_scanned,
        "supporting_md_unchanged_skipped": supporting_skipped,
    }
    mb, ma = metrics["mutable_bytes_before"], metrics["mutable_bytes_after"]
    ml, mla = metrics["mutable_lines_before"], metrics["mutable_lines_after"]
    metrics["mutable_bytes_delta"] = ma - mb
    metrics["mutable_bytes_reduction_pct"] = round((mb - ma) / mb * 100, 2) if mb else 0.0
    metrics["mutable_lines_delta"] = mla - ml
    metrics["mutable_lines_reduction_pct"] = round((ml - mla) / ml * 100, 2) if ml else 0.0

    dangling = dangling_references(skills_dir, repo / LOCK_FILENAME, deleted,
                                   prefixes, rep)

    routes = None
    if args.route_cases:
        routes = route_check(skills_dir, Path(args.route_cases), rep,
                             Path(args.route_results) if args.route_results else None)

    payload = {
        "generated_at": now_iso(),
        "repo": str(repo),
        "baseline": args.baseline,
        "protected_prefixes": list(prefixes),
        "metrics": metrics,
        "protected_fingerprint": fingerprint,
        "history_debt": history_debt,
        "dangling_references": dangling,
        "route_checks": routes,
        "failures": rep.failures,
        "warnings": rep.warnings,
        "skipped": rep.skipped,
        "exit": 1 if rep.failures else 0,
    }

    if args.json:
        try:
            Path(args.json).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: writing {args.json}: {exc}", file=sys.stderr)
            return 2

    if not args.quiet:
        print(f"skills: {metrics['skills_total_now']} total "
              f"({metrics['mutable_skills']} mutable, {metrics['protected_skills']} protected)")
        print(f"mutable SKILL.md: {mb} -> {ma} bytes "
              f"({metrics['mutable_bytes_delta']:+d}, {metrics['mutable_bytes_reduction_pct']}%), "
              f"{ml} -> {mla} lines ({metrics['mutable_lines_delta']:+d}, "
              f"{metrics['mutable_lines_reduction_pct']}%)")
        if deleted:
            print(f"deleted ({len(deleted)}): {', '.join(Path(p).parent.name for p in deleted)}")
        if added:
            print(f"added ({len(added)}): {', '.join(Path(p).parent.name for p in added)}")
        pf = fingerprint
        if prefixes:
            if not pf.get("compared"):
                print(f"protected fingerprint: not compared "
                      f"(no baseline; {pf['on_disk']} file(s) on disk)")
            else:
                state = "OK" if pf["ok"] else "DRIFT"
                print(f"protected fingerprint: {state} "
                      f"(baseline {pf['baseline_files']}, on disk {pf['on_disk']})")
        for w in rep.warnings:
            print(f"WARN  {w['check']} {w['path']}: {w['detail']}")
        for f in rep.failures:
            print(f"FAIL  {f['check']} {f['path']}: {f['detail']}")
        print(f"RESULT: {len(rep.failures)} failure(s), {len(rep.warnings)} warning(s)")

    return 1 if rep.failures else 0


if __name__ == "__main__":
    sys.exit(main())
