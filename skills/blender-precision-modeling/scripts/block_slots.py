#!/usr/bin/env python3
"""Fill a blrun slot directory to its cap with slots that look alive.

Used to retire runaway runner processes when the host forbids signalling them
(`kill` returns EPERM and `ps`/`pgrep` cannot enumerate, so a stuck batch cannot
be stopped the normal way).

SlotPool.acquire() admits a new job only while fewer than `cap` slot files hold
a LIVE pid, checked with os.kill(pid, 0). Writing `cap` slots that all name a pid
which always survives that check therefore blocks admission without touching any
process. Blocked runners raise TimeoutError after their acquire timeout and exit
on their own, which is the only available shutdown path on such a host.

The pid written is 0 by default. That is not a typo: os.kill(0, 0) signals the
caller's own process group and always succeeds, so the slot always reads as live.
Naming a real pid such as 1 is WRONG on a host that forbids signalling -- it
returns EPERM, and a liveness check that reads EPERM as "dead" (which is exactly
what older SlotPool._alive did) reports the slot as free and blocks nothing.

The slot directory is per-output-directory, so blocking one render root does not
affect a sweep running into a different one.
"""
import os
import sys
import time


def main():
    if len(sys.argv) < 3:
        print("usage: block_slots.py <render_root> <cap> [pid]")
        return 2
    root, cap = sys.argv[1], int(sys.argv[2])
    pid = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    d = os.path.join(root, ".slots")
    os.makedirs(d, exist_ok=True)
    now = time.time()
    for i in range(cap):
        with open(os.path.join(d, "block-%02d" % i), "w") as fh:
            fh.write("%d %f\n" % (pid, now))
    print("wrote %d blocking slots (pid %d) into %s" % (cap, pid, d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
