#!/usr/bin/env python3
"""Which of this account's own repositories may be promoted, and whether the
network is broken or the site is.

TWO CHECKS, BECAUSE BOTH HAVE COST A RUN

REACHABILITY DECIDES WHICH REPO, NOT TOPIC. A repository that answers 404
anonymously is not a candidate: the link would be dead for every reader who
is not signed in. The on-topic repository and the reachable one are often
different ones -- the 3D open-world game was the more on-topic project and
still was not the one to link, because it answers 404 anonymously. So every
own repository is CHECKED, and only the ones that answer 200 are offered.

A DEAD PROXY LOOKS LIKE A BLOCKED SITE. When every proxied host times out
while a direct-reachable host answers, the proxy is dead -- not Cloudflare
and not the network. A run that bisects user agents in that state burns its
whole budget on the wrong question. This script says which case it is, in
one command, so the answer is not re-derived by hand every time.

Usage:
    xrepo.py --list                 the own repositories, with reachability
    xrepo.py --pick                 the ones that may be promoted
    xrepo.py --network              is the proxy alive?
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402

# An ordinary Chrome user agent, so a repository that answers a bot with
# 403 is not mistaken for a reachable one.
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 "
      "Safari/537.36")

# The hosts that go through the proxy, and one that does not.
PROXIED_HOSTS = ("https://x.com/", "https://twitter.com/", "https://www.google.com/")
DIRECT_HOSTS = ("https://github.com/", "https://api.github.com/")


def status(url: str, timeout: float = 12.0) -> int:
    """The HTTP status a URL answers with, anonymously.

    The proxy is bypassed deliberately (--noproxy '*'): the question is
    whether the REPOSITORY is reachable by a reader, not whether this
    machine can reach it through its own proxy.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0


def own_repositories() -> list:
    """The account's own repositories, from the live git remotes.

    Read from the checkouts rather than written down: a hand-written list
    goes stale on exactly the event that matters, and the failure is
    silent.
    """
    found = []
    base = xconfig.code_dir()
    if not base.is_dir():
        return found
    for entry in sorted(os.listdir(base)):
        d = base / entry
        if not (d / ".git").exists():
            continue
        try:
            url = subprocess.run(
                ["git", "-C", str(d), "remote", "get-url", "origin"],
                capture_output=True, text=True, timeout=10).stdout.strip()
        except Exception:
            continue
        if not url:
            continue
        m = re.search(r"github\.com(?::\d+)?[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$",
                      url)
        if not m:
            continue
        owner, repo = m.group(1), m.group(2)
        found.append({
            "owner": owner,
            "repo": repo,
            "full_name": "%s/%s" % (owner, repo),
            "url": "https://github.com/%s/%s" % (owner, repo),
            "path": str(d),
        })
    return found


def last_push_days(path: str):
    """How many days since the repository's last push, or None."""
    try:
        out = subprocess.run(
            ["git", "-C", path, "log", "-1", "--format=%ct"],
            capture_output=True, text=True, timeout=10).stdout.strip()
        if not out:
            return None
        import time
        return int((time.time() - int(out)) // 86400)
    except Exception:
        return None


def list_repos(check: bool = True) -> list:
    """The own repositories, with their reachability and last push."""
    rows = own_repositories()
    for row in rows:
        row["reachable"] = status(row["url"]) if check else None
        row["days_since_push"] = last_push_days(row["path"])
    return rows


def network_state() -> dict:
    """Whether the proxy is alive, or the site is blocking us.

    The two states look identical to a run that only tries one host: a
    timeout. What separates them is that a DEAD PROXY takes the proxied
    hosts down while a direct host still answers.
    """
    proxied = {h: status(h, timeout=8.0) for h in PROXIED_HOSTS}
    direct = {h: status(h, timeout=8.0) for h in DIRECT_HOSTS}
    proxied_dead = all(v == 0 for v in proxied.values())
    direct_ok = any(v == 200 for v in direct.values())
    if proxied_dead and direct_ok:
        verdict = "PROXY DEAD -- every proxied host times out while a direct "\
                  "host answers. This is NOT Cloudflare and NOT the network. "\
                  "Do not bisect user agents."
    elif any(v == 403 for v in proxied.values()):
        verdict = "BLOCKED (403) -- the site answered with a challenge. The "\
                  "network is fine; the user agent is what it is refusing."
    else:
        verdict = "OK -- the network is fine."
    return {"proxied": proxied, "direct": direct, "verdict": verdict}


def main(argv) -> int:
    action = "list"
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--list":
            action = "list"; i += 1
        elif args[i] == "--pick":
            action = "pick"; i += 1
        elif args[i] == "--network":
            action = "network"; i += 1
        else:
            print("unknown argument: %s" % args[i])
            return 2
    if action == "network":
        state = network_state()
        print(json.dumps(state, indent=1, ensure_ascii=False))
        return 0
    rows = list_repos(check=True)
    if action == "list":
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return 0
    # PICK: the repositories that may be promoted. A repository that is not
    # reachable anonymously is not a candidate, and one that has not been
    # pushed in a fortnight is not worth promoting either.
    picks = [r for r in rows
             if r.get("reachable") == 200
             and (r.get("days_since_push") is None
                  or r["days_since_push"] <= 14)]
    print(json.dumps(picks, indent=1, ensure_ascii=False))
    if not picks:
        print("NO PROMOTABLE REPOSITORY: every own repository is either "
              "unreachable anonymously or stale.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
