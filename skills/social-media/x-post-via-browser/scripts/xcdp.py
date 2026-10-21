#!/usr/bin/env python3
"""The one connector to the browser: raw CDP over a websocket.

Every script in this skill drives the browser through this module and nothing
else, so the transport has exactly one behaviour to reason about.

TWO SUBSTITUTION RULES, and both of them exist because a wrong one cost a
run:

1. EVERY PLACEHOLDER IS A JS EXPRESSION AND EVERY VALUE IS json.dumps'D.
   There is one mode, not two. A placeholder inside a JS string literal is a
   quote-injection bug; a bare 19-digit id is a number literal, which loses
   precision (2112408066843148459 -> 2112408066843148500) and then matches
   nothing while the page visibly holds the target. Templates therefore build
   selectors by CONCATENATION and pass the value as an expression:

       "a[href*='/status/" + __SID__ + "']"

   json.dumps supplies the quotes, so a handle stays a string and a status id
   stays an exact string.

2. EVERY TEMPLATE IS RENDERED BEFORE IT IS USED, AND A LEFTOVER PLACEHOLDER
   IS AN ERROR. A script that renders a template with a missing value would
   otherwise send malformed JavaScript, and a malformed expression comes back
   as an exception that reads like "the target is not on the page".
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import xconfig                                            # noqa: E402

xconfig.ensure_runtime("websockets")

import websockets                                         # noqa: E402

# A placeholder left unsubstituted in a rendered template.
LEFTOVER = re.compile(r"__[A-Z][A-Z0-9_]*__")


def J(value) -> str:
    """Render a Python value as a JavaScript expression."""
    return json.dumps(value, ensure_ascii=False)


def sub(template: str, **values) -> str:
    """Fill a template's placeholders with JSON-quoted values.

    Every placeholder is a JS expression slot, so every value is dumped as a
    JS literal. `sub(t, SID=sid)` turns `__SID__` into `"2112...459"` -- a
    string, exact, safe to concatenate and safe to compare.
    """
    out = template
    for name, value in values.items():
        out = out.replace("__%s__" % name.upper(), J(value))
    leftover = sorted(set(LEFTOVER.findall(out)))
    if leftover:
        raise ValueError("unsubstituted placeholders in template: %s" % leftover)
    return out


def maybe_json(raw):
    """Decode a JSON payload, but pass anything else through unchanged."""
    if not isinstance(raw, str):
        return raw
    try:
        return json.loads(raw)
    except ValueError:
        return raw


class Browser:
    """A browser-level CDP connection.

    Usage:

        async with Browser() as b:
            tid, sess = await b.new_tab("https://x.com/home")
            value = await b.ev(sess, "document.title")
            await b.close_tab(tid)
    """

    def __init__(self, ws_url: str | None = None, timeout: float = 45.0):
        self._explicit_ws = ws_url
        self.timeout = timeout
        self._ws: "websockets.ClientConnection | None" = None
        self._id = 0

    async def __aenter__(self) -> "Browser":
        url = self._explicit_ws or xconfig.ws_url()
        self._ws = await websockets.connect(
            url, origin=None, max_size=64 * 1024 * 1024)
        return self

    async def __aexit__(self, *exc) -> None:
        try:
            await self._ws.close()
        except Exception:
            pass

    async def call(self, method: str, params=None, session_id=None,
                   timeout: float | None = None):
        """One CDP round trip."""
        self._id += 1
        mid = self._id
        msg = {"id": mid, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id
        await self._ws.send(json.dumps(msg))
        deadline = asyncio.get_event_loop().time() + (timeout or self.timeout)
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                raise TimeoutError("%s did not answer in time" % method)
            raw = await asyncio.wait_for(self._ws.recv(), timeout=remaining)
            data = json.loads(raw)
            if data.get("id") != mid:
                continue
            if "error" in data:
                raise RuntimeError("%s: %s" % (method, json.dumps(data["error"])[:300]))
            return data.get("result", {})

    async def ev(self, session_id: str, expression: str,
                 await_promise: bool = False, timeout: float | None = None):
        """Evaluate an expression in a page.

        A JavaScript exception comes back as {"__exc": ...} rather than as an
        exception here, because a thrown expression and a missing element look
        identical otherwise, and the difference decides whether a run reports
        "the target is gone" or "my selector is wrong".
        """
        result = await self.call("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": await_promise,
        }, session_id=session_id, timeout=timeout)
        if result.get("exceptionDetails"):
            return {"__exc": json.dumps(result["exceptionDetails"])[:400]}
        return (result.get("result") or {}).get("value")

    async def new_tab(self, url: str):
        """Open a tab and return (target_id, session_id).

        The focus emulation and the lifecycle state are set BEFORE the
        navigation: a tab that is not focused never hydrates, and a tab that
        never hydrates reads as an empty feed.
        """
        created = await self.call("Target.createTarget", {"url": "about:blank"})
        tid = created["targetId"]
        attached = await self.call("Target.attachToTarget",
                                   {"targetId": tid, "flatten": True})
        sess = attached["sessionId"]
        await self.call("Page.enable", {}, session_id=sess)
        await self.call("Runtime.enable", {}, session_id=sess)
        await self.call("Emulation.setFocusEmulationEnabled",
                        {"enabled": True}, session_id=sess)
        await self.call("Page.setWebLifecycleState",
                        {"state": "active"}, session_id=sess)
        await self.call("Page.navigate", {"url": url}, session_id=sess)
        return tid, sess

    async def close_tab(self, target_id: str) -> None:
        try:
            await self.call("Target.closeTarget", {"targetId": target_id})
        except Exception:
            pass

    async def wait_for(self, session_id: str, expression: str,
                       timeout: float = 45.0, interval: float = 1.5):
        """Poll an expression until it returns something truthy.

        Returns the last value seen, or None on timeout. A single read of a
        freshly navigated page is not evidence: the page mounts late.
        """
        deadline = asyncio.get_event_loop().time() + timeout
        last = None
        while asyncio.get_event_loop().time() < deadline:
            last = await self.ev(session_id, expression)
            if last:
                return last
            await asyncio.sleep(interval)
        return last
