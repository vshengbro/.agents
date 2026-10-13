#!/usr/bin/env python3
"""
cdp_eval.py — minimal raw-CDP driver for one-shot scripts.

Connect to a running headless Chromium with --remote-debugging-port=9222
(or any port), evaluate a JS expression, optionally screenshot, print result.

Usage:
  python3 cdp_eval.py [--port 9222] [--url https://example.com] [--js "document.title"] [--screenshot out.png] [--iphone]

Requires: `websockets` Python package; `websocat`/`jq` only if you want to
auto-discover the page ws URL.
"""
import argparse, asyncio, base64, json, os, sys, urllib.request

os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

import websockets


def _no_proxy_opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def discover_page_ws(port: int) -> str:
    targets = json.loads(_no_proxy_opener().open(f"http://127.0.0.1:{port}/json").read())
    for t in targets:
        if t.get("type") == "page":
            return t["webSocketDebuggerUrl"]
    raise RuntimeError(f"no page target found on port {port}")


async def driver(ws_url: str, commands: list, wait_events: float = 0.0):
    """Run a sequence of (method, params|None) tuples; return list of results.
    Optionally wait `wait_events` seconds at the end so trailing events fire.
    """
    results = []
    async with websockets.connect(ws_url, max_size=8 * 1024 * 1024) as ws:
        pending = {}

        async def reader():
            async for raw in ws:
                m = json.loads(raw)
                if "id" in m:
                    pending[m["id"]] = m

        rt = asyncio.create_task(reader())
        try:
            mid = 0

            async def call(method, params=None, timeout=15):
                nonlocal mid
                mid += 1
                req = {"id": mid, "method": method}
                if params is not None:
                    req["params"] = params
                await ws.send(json.dumps(req))
                for _ in range(int(timeout * 100)):
                    if mid in pending:
                        return pending.pop(mid)
                    await asyncio.sleep(0.01)
                return {"error": "timeout"}

            for method, params in commands:
                r = await call(method, params)
                results.append(r)
            if wait_events:
                await asyncio.sleep(wait_events)
        finally:
            rt.cancel()
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--ws", help="explicit ws URL (overrides --port discovery)")
    ap.add_argument("--url", help="navigate to URL first")
    ap.add_argument("--js", help="Runtime.evaluate expression")
    ap.add_argument("--screenshot", help="path to write PNG screenshot")
    ap.add_argument("--iphone", action="store_true",
                    help="emulate iPhone 14 Pro viewport before screenshotting")
    ap.add_argument("--wait", type=float, default=0.0, help="seconds to wait after navigate")
    args = ap.parse_args()

    ws_url = args.ws or discover_page_ws(args.port)
    cmds = [["Page.enable"]]
    if args.url:
        cmds.append(["Page.navigate", {"url": args.url}])
        cmds.append(["Runtime.evaluate", {"expression": "(async()=>{for(let i=0;i<40;i++){if(document.readyState!=='loading')break;await new Promise(r=>setTimeout(r,100));}return document.readyState;})()", "awaitPromise": True, "returnByValue": True}])
    if args.iphone:
        cmds.append(["Emulation.setDeviceMetricsOverride", {
            "width": 393, "height": 852, "deviceScaleFactor": 3, "mobile": True}])
    if args.js:
        cmds.append(["Runtime.evaluate", {"expression": args.js, "returnByValue": True}])
    if args.screenshot:
        cmds.append(["Page.captureScreenshot", {"format": "png"}])

    results = asyncio.run(driver(ws_url, cmds, wait_events=args.wait))

    out = []
    for (method, _), r in zip(cmds, results):
        if method == "Runtime.evaluate" and "result" in r and "result" in r["result"]:
            out.append({"method": method, "value": r["result"]["result"].get("value"),
                        "exception": r["result"].get("exceptionDetails")})
        elif method == "Page.captureScreenshot" and "result" in r:
            data = r["result"].get("data")
            if data:
                with open(args.screenshot, "wb") as f:
                    f.write(base64.b64decode(data))
                out.append({"method": method, "wrote": args.screenshot, "bytes": len(data)})
            else:
                out.append({"method": method, "error": r})
        else:
            out.append({"method": method, "result": r.get("result") or r})
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()