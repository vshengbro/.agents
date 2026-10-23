#!/usr/bin/env python3
"""The like button's state, and the wait that proves the swap.

THE SWAP IS RENDERED BY THE SITE, AND A SINGLE READ READS IT EARLY.

X re-renders the article when the like request lands, and how long that
takes is not ours to decide. The scripts read the button state once,
three seconds after the click, and called that a proof: when the read
landed before the re-render, the PRE-click state came back, and a like
that had landed was reported as unconfirmed.

Measured on 2026-10-24, in one run of fifty-three replies: eight
refusals of "like did not confirm", every one of them a like that was
actually there -- the account's own liked list held all eight parents.
The like had landed; the proof was early.

So the state is POLLED until the button swaps, and the poll only READS.
It never clicks again, so it cannot toggle a like off, and it never
touches the send path: a like confirmation may be retried, a send may
not.

THE PROOF IS THE SWAP, NOT THE CLICK. A click returns whether the click
was dispatched; the like count moves for other reasons too. What proves
a like landed is `like` gone and `unlike` present. So the read BEFORE
the click decides whether a click is needed at all, which makes the
operation idempotent, and the read AFTER it is what counts.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xcdp import sub                                          # noqa: E402

# The article carrying this status id, with its like button state.
PROBE = """(() => {
  const arts = [...document.querySelectorAll('article')];
  const art = arts.find(a => a.querySelector("a[href*='/status/" + __SID__ + "']"));
  if (!art) return JSON.stringify({err: 'no-article', nArts: arts.length});
  const like = art.querySelector("[data-testid='like']");
  const unlike = art.querySelector("[data-testid='unlike']");
  return JSON.stringify({
    found: true, nArts: arts.length,
    like: !!like, unlike: !!unlike,
    likeAria: like ? like.getAttribute('aria-label') : null,
    unlikeAria: unlike ? unlike.getAttribute('aria-label') : null
  });
})()"""

# The click refuses to touch an already-liked post, so the operation
# stays idempotent even when the pre-read and the click race.
LIKE_CLICK = """(() => {
  const arts = [...document.querySelectorAll('article')];
  const art = arts.find(a => a.querySelector("a[href*='/status/" + __SID__ + "']"));
  if (!art) return 'NO_ARTICLE';
  if (art.querySelector("[data-testid='unlike']")) return 'ALREADY_LIKED';
  const b = art.querySelector("[data-testid='like']");
  if (!b) return 'NO_LIKE_BUTTON';
  b.click();
  return 'CLICKED';
})()"""

# How long the swap is waited for, and how often it is read.
LIKE_TIMEOUT = 25.0
LIKE_INTERVAL = 1.5


async def read_state(b, sess, sid):
    """One read of the article's like state.

    Returns the parsed state, or a state carrying `probe_failed` when the
    read itself could not be made -- a failed read is not a state, and
    the two must not be confused.
    """
    raw = await b.ev(sess, sub(PROBE, SID=sid))
    if not isinstance(raw, str):
        return {"probe_failed": str(raw)[:200]}
    try:
        state = json.loads(raw)
    except ValueError:
        return {"probe_failed": "unreadable probe"}
    if not isinstance(state, dict):
        return {"probe_failed": "unexpected probe shape"}
    return state


async def poll_until(read, timeout=LIKE_TIMEOUT, interval=LIKE_INTERVAL):
    """Read until the state says the like landed, or the budget runs out.

    `read` is an awaitable returning the state dict. The returned state is
    the LAST one read: `unlike` true means the swap was observed, and
    anything else means it was not, inside the budget.

    The poll only READS. It never clicks, so it cannot toggle a like off
    and it cannot publish anything.
    """
    deadline = time.monotonic() + timeout
    state = await read()
    while not (state and state.get("unlike")):
        if time.monotonic() >= deadline:
            return state
        await asyncio.sleep(interval)
        state = await read()
    return state


async def confirm_like(b, sess, sid, timeout=LIKE_TIMEOUT,
                       interval=LIKE_INTERVAL):
    """Wait for the like button to swap, and report the state it swapped to."""
    async def read():
        return await read_state(b, sess, sid)

    return await poll_until(read, timeout=timeout, interval=interval)
