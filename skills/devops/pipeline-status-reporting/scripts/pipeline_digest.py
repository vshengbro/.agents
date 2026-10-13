#!/usr/bin/env python3
"""Aggregate GitHub pipeline status for every repo the account owns into one table.

The per-repo `gh run list` output is a stream of near-identical lines that must
be read one at a time and reconciled by hand. This collapses the same data into a
single Markdown table so a multi-repo pipeline report is one artifact, not N.

Every value is fetched live from the REST API. Nothing is cached, and a repo the
API cannot answer for is reported as a visible ERROR row rather than omitted: a
silent gap in a status table reads as "fine", which is the one direction this
must never fail in.

Usage:
    pipeline_digest.py [--repos owner/name ...] [--runs N] [--format md|text]
                       [--include-quiet]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
CRED = "/tmp/hermes/git-cred"


def token() -> str:
    """Resolve a token from the environment, else the git credential store.

    Prefers the git credential store over `gh` because `gh` reads its token
    from the OS keyring, which a headless session cannot reach, and its
    GraphQL transport fails outright when a TLS-intercepting proxy is in the
    path (the proxy certificate does not cover api.github.com). Plain HTTPS
    through urllib still succeeds in that environment.
    """
    env = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if env:
        return env
    try:
        with open(CRED, encoding="utf8") as handle:
            match = re.search(r"https://x-access-token:([^@]+)@github\.com", handle.read())
    except OSError:
        match = None
    if not match:
        sys.exit("no GitHub token: set GH_TOKEN or populate " + CRED)
    return match.group(1)


def api(path: str, tok: str) -> object:
    """GET a REST path. Returns the decoded body, or {"__err__": detail}."""
    request = urllib.request.Request(
        API + path,
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "hermes-pipeline-digest",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        return {"__err__": error.code}
    except urllib.error.URLError as error:
        return {"__err__": str(error.reason)}


def failed(payload: object) -> bool:
    """Distinguish an error response from a successful dict-shaped body.

    Testing `isinstance(payload, dict)` is wrong: a successful API response is
    also a dict, so every success would be reported as an error and the table
    would read as uniformly broken rather than "this check is wrong".
    """
    return not isinstance(payload, dict) or "__err__" in payload


def repos_from_account(tok: str) -> list[str]:
    """Enumerate every repo the account can push to: personal plus each org.

    Uses /user/orgs, not /users/<account>/orgs: the latter returns only orgs
    with public membership, silently dropping private orgs that this report
    exists to cover.
    """
    found: list[str] = []
    personal = api("/user/repos?per_page=100&affiliation=owner", tok)
    if isinstance(personal, list):
        found += [r["full_name"] for r in personal]
    orgs = api("/user/orgs", tok)
    if isinstance(orgs, list):
        for org in orgs:
            listed = api(f"/orgs/{org['login']}/repos?per_page=100", tok)
            if isinstance(listed, list):
                found += [r["full_name"] for r in listed]
    seen: set[str] = set()
    unique: list[str] = []
    for name in found:
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


def collect(repo: str, tok: str, runs: int) -> dict:
    runs_api = api(f"/repos/{repo}/actions/runs?per_page={runs}", tok)
    if failed(runs_api):
        return {"repo": repo, "error": str(runs_api.get("__err__", "unknown"))}
    entries = runs_api.get("workflow_runs", [])
    if not entries:
        return {"repo": repo, "empty": True}
    latest = entries[0]
    return {
        "repo": repo,
        "workflow": latest.get("name") or "?",
        "event": latest.get("event") or "?",
        "status": latest.get("status") or "?",
        "conclusion": latest.get("conclusion") or "-",
        "branch": (latest.get("head_branch") or "?").replace("refs/heads/", ""),
        "sha": (latest.get("head_sha") or "")[:8],
        "url": latest.get("html_url") or "",
    }


def render(rows: list[dict], fmt: str) -> str:
    if fmt == "text":
        out = []
        for row in rows:
            if row.get("error"):
                out.append(f"{row['repo']:26} ERROR {row['error']}")
            elif row.get("empty"):
                out.append(f"{row['repo']:26} (no workflow runs)")
            else:
                out.append(
                    f"{row['repo']:26} {row['workflow'][:26]:26} "
                    f"{row['status']}/{row['conclusion']} "
                    f"{row['branch'][:26]:26} {row['sha']}"
                )
        return "\n".join(out)

    head = (
        "| 仓库 | Workflow | 触发 | 分支 | SHA | 状态 | 结论 | 运行链接 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    body = []
    for row in rows:
        if row.get("error"):
            body.append(
                f"| `{row['repo']}` | - | - | - | - | ERROR | {row['error']} | - |"
            )
        elif row.get("empty"):
            body.append(f"| `{row['repo']}` | - | - | - | - | - | 无运行记录 | - |")
        else:
            body.append(
                f"| `{row['repo']}` | {row['workflow']} | {row['event']} "
                f"| `{row['branch']}` | `{row['sha']}` | {row['status']} "
                f"| {row['conclusion']} | [run]({row['url']}) |"
            )
    return head + "\n" + "\n".join(body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos", nargs="*", default=None, help="owner/name list")
    parser.add_argument("--runs", type=int, default=1, help="runs to consider per repo")
    parser.add_argument("--format", choices=["md", "text"], default="md")
    parser.add_argument(
        "--include-quiet",
        action="store_true",
        help="keep repos that have never run a workflow",
    )
    args = parser.parse_args()

    tok = token()
    repos = args.repos or repos_from_account(tok)
    rows = [collect(repo, tok, args.runs) for repo in repos]
    if not args.include_quiet:
        # The account owns 100+ repos, most of them forks of upstream projects
        # that never run CI. Those rows are pure noise in a status table, so
        # default to the repos that actually have a pipeline to report on.
        active = [r for r in rows if not r.get("empty")]
        if active:
            rows = active
    rows.sort(key=lambda r: r["repo"].lower())
    print(render(rows, args.format))


if __name__ == "__main__":
    main()
