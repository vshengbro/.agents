#!/usr/bin/env python3
"""Route gate: does this commit's staging match what classify_change decides?

`classify_change.py` computes the route (DIRECT_PUSH vs NEEDS_PR) but nothing
consumed it — the rule existed in prose in four skills and in a script nobody
ran, which is why a one-line CSS deletion in euv went out as PR #300 when the
user's rule says presentation direct-pushes. This gate closes that loop at
commit time.

What it enforces, and why each part is a real failure mode:

  * NEEDS_PR staged while committing to the default branch  -> the bypass the
    whole rule exists to prevent.
  * DIRECT_PUSH staged while on a feature branch            -> the mirror image;
    a docs/config/presentation change dragged through a PR anyway.
  * a commit on the default branch whose own subject says `type(scope):` while
    the classifier says DIRECT_PUSH is *not* checked here — the classifier
    decides the route, not the wording.

Exit 0 = route matches. Exit 1 = mismatch, commit blocked. Exit 2 = the
classifier could not run, which is treated as BLOCKED (从严): an unanswerable
question must never become a free pass.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_classifier() -> Path:
    for candidate in (
        HERE / "classify_change.py",
        HERE.parent / "scripts" / "classify_change.py",
    ):
        if candidate.is_file():
            return candidate
    for root in (Path.home() / ".agents/skills", Path.home() / ".hermes/skills"):
        candidate = root / "git-standards/scripts/classify_change.py"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("classify_change.py not found")


def run_classifier(repo: Path, base: str) -> dict:
    script = _find_classifier()
    proc = subprocess.run(
        [sys.executable, str(script), "--repo", str(repo), "--base", base, "--staged", "--json"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out = proc.stdout.decode("utf-8", "replace")
    if not out.strip():
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or "no output")
    data = json.loads(out)
    data["_exit"] = proc.returncode
    return data


def current_branch(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return proc.stdout.decode("utf-8", "replace").strip() or "HEAD"


def default_branch(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    ref = proc.stdout.decode("utf-8", "replace").strip()
    if ref:
        return ref.rsplit("/", 1)[-1]
    return "master" if subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", "master"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0 else "main"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", default=None, help="base ref (default: origin/<default-branch>)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    repo = Path(args.repo).expanduser().resolve()
    if not (repo / ".git").exists():
        sys.stderr.write("error: %s is not a git repository\n" % repo)
        return 2

    branch = current_branch(repo)
    base = args.base or ("origin/" + default_branch(repo))
    default_name = base.rsplit("/", 1)[-1]

    try:
        data = run_classifier(repo, base)
    except (RuntimeError, FileNotFoundError, json.JSONDecodeError) as exc:
        sys.stderr.write("route gate: could not classify the staged diff: %s\n" % exc)
        sys.stderr.write("route gate: BLOCKED (从严 — treat an unanswerable question as "
                         "ENFORCED, never as a free pass)\n")
        return 2

    verdict = data.get("verdict", "NEEDS_PR")
    on_default = branch in ("master", "main", default_name)

    problems = []
    if verdict == "NEEDS_PR" and on_default:
        code_files = [f["path"] for f in data.get("files", []) if f.get("route") == "NEEDS_PR"]
        problems.append(
            "staged diff is NEEDS_PR (executable code) but you are committing directly to "
            "'%s'. Branch first, push, and open a PR (git-standards §3.3a): %s"
            % (branch, ", ".join(code_files[:6]) or "see classify_change.py output"))
    elif verdict == "DIRECT_PUSH" and not on_default:
        pres = [f["path"] for f in data.get("files", []) if f.get("route") == "DIRECT_PUSH"]
        problems.append(
            "staged diff is DIRECT_PUSH (docs / config / presentation / comment-only) but you "
            "are on branch '%s'. Such changes commit straight to the default branch with no PR "
            "(git-standards §3.3a): %s" % (branch, ", ".join(pres[:6]) or "no files listed"))

    payload = {
        "branch": branch,
        "base": base,
        "verdict": verdict,
        "on_default_branch": on_default,
        "problems": problems,
        "files": [{"path": f["path"], "route": f.get("route"), "category": f.get("category")}
                  for f in data.get("files", [])],
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("=" * 70)
        print("route gate (git-standards §3.3a): branch=%s base=%s" % (branch, base))
        print("  classifier verdict: %s" % verdict)
        for f in payload["files"]:
            print("    %-11s %s" % (f["route"] or "-", f["path"]))
        print("=" * 70)
        if not problems:
            print("  route matches the staging — commit allowed")
        else:
            for p in problems:
                print("  BLOCK: %s" % p)
        print("=" * 70)

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())