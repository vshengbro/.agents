#!/usr/bin/env python3
"""check_freshness.py -- are these renders actually made by the current toolkit?

    python3 scripts/check_freshness.py <render_root> [--sha-only]

A directory of PNGs carries no version, so a render set silently drifts out of
date as soon as the toolkit changes: the images keep being scored, they just no
longer show what the code does. That cost four rounds of vision scoring on
images that predated the fixes being scored. Every report.json now carries the
`bkit_sha` of the toolkit that produced it, and this compares each one against
the live file.

Exit status is 0 only when every report matches the current toolkit, so it can
gate a scoring round. Reports with no `bkit_sha` are counted as `unstamped` and
treated as stale -- a render whose provenance is unknown is not evidence.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def current_sha():
    with open(os.path.join(HERE, "bkit.py"), "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="render root containing <item>/report.json")
    ap.add_argument("--sha-only", action="store_true",
                    help="print just the current hash and exit")
    ap.add_argument("--quiet", action="store_true",
                    help="only print the summary line")
    args = ap.parse_args()

    want = current_sha()
    if args.sha_only:
        print(want)
        return 0

    if not os.path.isdir(args.root):
        print("no such render root: %s" % args.root)
        return 2

    fresh, stale, unstamped, unreadable = [], [], [], []
    for item in sorted(os.listdir(args.root)):
        rp = os.path.join(args.root, item, "report.json")
        if not os.path.isfile(rp):
            continue
        try:
            with open(rp) as fh:
                rep = json.load(fh)
        except Exception:
            unreadable.append(item)
            continue
        got = rep.get("bkit_sha")
        if got is None:
            unstamped.append(item)
        elif got == want:
            fresh.append(item)
        else:
            stale.append((item, got))

    total = len(fresh) + len(stale) + len(unstamped)
    if not args.quiet:
        for item, got in stale[:25]:
            print("  STALE      %-28s made with %s" % (item, got))
        if len(stale) > 25:
            print("  ... and %d more stale" % (len(stale) - 25))
        for item in unstamped[:10]:
            print("  UNSTAMPED  %-28s no bkit_sha in report" % item)
        if len(unstamped) > 10:
            print("  ... and %d more unstamped" % (len(unstamped) - 10))
        for item in unreadable[:10]:
            print("  UNREADABLE %-28s report.json did not parse" % item)

    print("bkit sha %s | %d reports: %d current, %d stale, %d unstamped"
          % (want, total, len(fresh), len(stale), len(unstamped)))
    if stale or unstamped or unreadable or not total:
        print("STALE SET -- these renders do not reflect the current toolkit.")
        return 1
    print("FRESH: every render was made by the current toolkit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
