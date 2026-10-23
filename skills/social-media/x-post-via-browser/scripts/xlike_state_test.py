#!/usr/bin/env python3
"""Fixtures for the like-confirmation poll.

Run directly:

    python3 xlike_state_test.py

THE PROOF IS THE SWAP, AND A SINGLE EARLY READ IS NOT A PROOF.

The site renders the button swap when its own like request lands, and a
read taken three seconds after the click can still see the PRE-click
state. Measured on 2026-10-24, in one run of fifty-three replies, eight
likes landed and were reported as unconfirmed -- all eight parents were
in the account's own liked list afterwards. The like had landed; the
proof was early.

So the proof is POLLED until the swap shows. These cases pin the three
things that must hold for that to be safe:

  * the poll READS AGAIN after a stale state -- one read is not a proof;
  * the poll NEVER clicks -- a second click would toggle the like off,
    and the poll has no business touching the send path either;
  * the poll still GIVES UP -- a like that never lands is refused, so a
    reply is never sent on an unliked post.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import xlike_state                                        # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("ok   " if ok else "FAIL ") + name + ((" -- " + detail) if detail else ""))
    if not ok:
        FAILURES.append(name)


class FakeBrowser:
    """A browser that hands back a scripted sequence of probe states."""

    def __init__(self, states, raw=None):
        self.states = list(states)
        self.raw = raw
        self.reads = 0
        self.clicks = 0

    async def ev(self, sess, expression):
        # The click template is the only one that clicks.
        if "b.click()" in expression:
            self.clicks += 1
            return "CLICKED"
        self.reads += 1
        if self.raw is not None:
            return self.raw
        if self.states:
            self.last = self.states.pop(0)
        return getattr(self, "last", '{"err": "no-article"}')


def test_poll_reads_again_after_a_stale_state():
    """The state that proves the like arrives late -- poll until it does."""
    browser = FakeBrowser([
        '{"like": true, "unlike": false}',   # the pre-click state
        '{"like": true, "unlike": false}',   # still the pre-click state
        '{"like": false, "unlike": true}',   # the swap, finally
    ])

    async def run():
        return await xlike_state.confirm_like(browser, "sess", "123",
                                               timeout=5.0, interval=0.01)

    state = asyncio.run(run())
    check("the poll reads again until the swap shows",
          state.get("unlike") is True, str(state))
    check("the poll made more than one read", browser.reads >= 3,
          "reads=%d" % browser.reads)
    check("the poll never clicked", browser.clicks == 0,
          "clicks=%d" % browser.clicks)


def test_poll_gives_up_when_the_like_never_lands():
    """A like that never lands is refused -- no reply on an unliked post."""
    browser = FakeBrowser(['{"like": true, "unlike": false}'])

    async def run():
        return await xlike_state.confirm_like(browser, "sess", "123",
                                               timeout=0.05, interval=0.01)

    state = asyncio.run(run())
    check("the poll gives up on a like that never lands",
          not state.get("unlike"), str(state))
    check("the refused poll never clicked", browser.clicks == 0,
          "clicks=%d" % browser.clicks)


def test_probe_failure_is_not_a_state():
    """A read that could not be made is not a state, and is not a proof."""
    browser = FakeBrowser([], raw=object())

    async def run():
        return await xlike_state.read_state(browser, "sess", "123")

    state = asyncio.run(run())
    check("a failed read is reported as a failed read",
          "probe_failed" in state, str(state))


def test_already_liked_is_read_not_clicked():
    """An already-liked post reports itself, and the click never runs."""
    browser = FakeBrowser(['{"like": false, "unlike": true}'])

    async def run():
        return await xlike_state.read_state(browser, "sess", "123")

    state = asyncio.run(run())
    check("an already-liked post reads as already liked",
          state.get("unlike") is True, str(state))
    check("reading an already-liked post clicked nothing",
          browser.clicks == 0, "clicks=%d" % browser.clicks)


def test_the_click_refuses_an_already_liked_post():
    """The click itself refuses to touch a liked post, so it cannot unlike."""
    template = xlike_state.LIKE_CLICK
    guard = template.find("[data-testid='unlike']")
    click = template.find("b.click()")
    check("the click template guards the unlike state before it clicks",
          guard != -1 and click != -1 and guard < click,
          "guard=%d click=%d" % (guard, click))


def main() -> int:
    test_poll_reads_again_after_a_stale_state()
    test_poll_gives_up_when_the_like_never_lands()
    test_probe_failure_is_not_a_state()
    test_already_liked_is_read_not_clicked()
    test_the_click_refuses_an_already_liked_post()
    if FAILURES:
        print("FAILURES: %d" % len(FAILURES))
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
