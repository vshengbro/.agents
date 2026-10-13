---
name: chrome-devtools-protocol
description: "Drive headless Chromium via raw CDP from terminal scripts."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, cdp, websocket, headless-chrome, automation, scraping, screenshots]
    related_skills: [blocked-page-recovery, inspecting-hermes-desktop-dom, node-inspect-debugger]
---

# Chrome DevTools Protocol (raw CDP)

## Overview

Drive any Chromium-class browser — Chrome, Edge, Brave, headless Chrome for
Testing — by speaking the Chrome DevTools Protocol over a WebSocket. No
Playwright, no Puppeteer, no project install. Useful when you want full
control from a terminal agent loop, need to script many CDP domains in one
session, or need something `npx playwright` is overkill for.

This skill is for **page automation on arbitrary web content**. For Node.js
process debugging (`node --inspect`), use `node-inspect-debugger`. For
inspecting the Hermes desktop Electron window, use
`inspecting-hermes-desktop-dom`. CDP is the same protocol all three speak,
but the targets, the meaningful domains, and the failure modes are different.

## When to Use

- Script Page/DOM/Runtime/Network/Emulation/Console/Performance operations
  on real websites (navigate, evaluate JS, screenshot, intercept requests,
  fake viewport, capture console, dump metrics).
- You have an existing headless Chrome (or Electron) already exposing a
  debugging port and want to attach from Python / Node / a script.
- You need to do something Playwright would force into async/await page
  objects (e.g. dump the full AX tree, hand-crafted `Network.route`,
  `Page.setDownloadBehavior`).
- You want to drive Chrome from inside `execute_code` / a kernel that
  proxies everything through a corporate proxy except `localhost`.

**Don't use for:** quick screenshots of a single URL (use `browser_exec`'s
`capture_screenshot`), reading page text (use `web_extract` or `read`),
or anything where a Playwright one-liner suffices.

## Step 1 — Make sure Chromium is installed

On macOS with the Hermes-managed browser:

```bash
npx -y agent-browser install chromium    # installs Chrome for Testing
npx -y agent-browser doctor             # verifies
```

If a different Chrome is already running on a debugging port, skip this.
Always close the previous session before reusing port 9222:

```bash
npx -y agent-browser close --all
```

## Step 2 — Launch headless Chrome with a CDP port

```bash
CHROME="/Users/sqs/.agent-browser/browsers/chrome-<ver>/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
"$CHROME" \
  --headless=new --no-sandbox --disable-gpu \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/cdp-demo/profile \
  --hide-scrollbars --window-size=1280,800 \
  about:blank > /tmp/cdp-demo/chrome.log 2>&1 &
```

Verify it bound (not crashed):

```bash
curl -s http://127.0.0.1:9222/json/version
```

Enumerate page targets:

```bash
curl -s http://127.0.0.1:9222/json | jq '.[] | select(.type=="page") | {id, url, webSocketDebuggerUrl}'
```

Each `page` target gets its own WebSocket at
`ws://127.0.0.1:9222/devtools/page/<targetId>`. The `browser` target — for
cross-target commands like `Target.createTarget` — is at
`ws://127.0.0.1:9222/devtools/browser/<uuid>` (one per Chrome instance).

## Step 3 — The Python websocket driver (the part that actually matters)

`execute_code` and other Hermes kernels route HTTP through a proxy that
ignores `127.0.0.1`. urllib will return 502/empty. Two fixes:

1. Set `NO_PROXY=localhost,127.0.0.1` BEFORE importing urllib.
2. Use a no-proxy opener explicitly:
   `urllib.request.build_opener(urllib.request.ProxyHandler({}))`.

The websocket itself isn't HTTP so the proxy is fine; only the discovery
calls hit it.

The core driver — copy/paste, then add domain-specific commands:

```python
import asyncio, json, base64, os
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['no_proxy'] = 'localhost,127.0.0.1'
import websockets

WS = "ws://127.0.0.1:9222/devtools/page/<targetId>"

async def main():
    async with websockets.connect(WS, max_size=8*1024*1024) as ws:
        pending, events = {}, []
        # Background reader: every frame is either an id-tagged response
        # (store in pending) or an event (append to events log). Mixing
        # the two without separation is the #1 source of "got the wrong
        # message" bugs.
        async def reader():
            async for raw in ws:
                m = json.loads(raw)
                if "id" in m: pending[m["id"]] = m
                else:         events.append(m["method"])
        rt = asyncio.create_task(reader())

        mid = 0
        async def call(method, params=None, timeout=10):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": method, **({"params": params} if params else {})}))
            for _ in range(int(timeout*100)):
                if mid in pending: return pending.pop(mid)
                await asyncio.sleep(0.01)
            return {"error": "timeout"}

        # ...your commands here...

        rt.cancel()

asyncio.run(main())
```

### Useful commands in one screen

| Domain | Method | What it does |
|---|---|---|
| `Page` | `Page.enable` | Required once before navigate/screenshot |
| `Page` | `Page.navigate` `{"url":...}` | Navigate; fire `Page.loadEventFired` when done |
| `Page` | `Page.captureScreenshot` `{"format":"png"}` | Returns `data` (base64 PNG); decode and write |
| `Page` | `Page.setDownloadBehavior` | Drive `downloads/` instead of asking for a path |
| `Runtime` | `Runtime.evaluate` `{"expression":"...","returnByValue":true}` | Run JS, get JSON-able value back |
| `Runtime` | `Runtime.callFunctionOn` | Call a function on an existing `objectId` |
| `DOM` | `DOM.getDocument` → `DOM.querySelector(nodeId,"sel")` → `DOM.getOuterHTML(nodeId)` | Read DOM nodes |
| `Network` | `Network.enable` → watch `Network.requestWillBeSent`/`responseReceived`/`loadingFinished` | Capture traffic |
| `Network` | `Network.setRequestInterception` + `Network.continueInterceptedRequest` | Stub / mock requests |
| `Emulation` | `Emulation.setDeviceMetricsOverride` `{"width":393,"height":852,"deviceScaleFactor":3,"mobile":true}` | Fake iPhone viewport |
| `Emulation` | `Emulation.setUserAgentOverride` | Spoof UA |
| `Console` | `Console.enable` → `Console.messageAdded` | Capture `console.log` / errors |
| `Performance` | `Performance.enable` → `Performance.getMetrics` | DOM count, frame count, task duration |
| `Target` | `Target.createTarget` `{"url":"about:blank"}` | Open a new tab (browser target only) |
| `Accessibility.getFullAXTree` | n/a | Walk every node's role/name for accessibility-driven automation |
| `CSS` | `CSS.enable` then `CSS.forcePseudoState` `{"nodeId":N,"forcedPseudoClasses":["hover","focus","active"]}` | Pin a node into a pseudo-class state — the only reliable way to screenshot `:hover`/`:focus`/`:active` styles headless |
| `DOM` | `DOM.querySelectorAll` `{"nodeId":rootNodeId,"selector":"..."}` | Get every matching backend node id in one call — use this when you need to act on the *Nth* match, not just the first |

### Loading state, the right way

`Page.navigate` returns immediately — it doesn't wait for the page. Either:

- Subscribe to `Page.loadEventFired`, OR
- Poll `Runtime.evaluate('document.readyState')` until it's `interactive`/`complete`.

`wait_for_load` semantics in agents is typically the polling form. The CDP
spec has no `Page.waitForLoad`; agents fake it with that poll.

### Verify before claiming done

Real bugs here are silent: a call returns `{"id":N,"result":{}}` even when the
page state is wrong.

- `Runtime.evaluate` returning `undefined` ≠ "command failed"; print `result.exceptionDetails` if present.
- Screenshots of `about:blank` are valid PNGs of an empty viewport — check bytes and dimensions:
  `file /tmp/cdp_demo/shot1.png` → expect `PNG image data, W x H`.
- `Network.loadingFinished` fires even when the response was an error;
  check `Network.responseReceived.response.status`.
- Headless Chrome's `--disable-gpu` is mandatory on macOS when launched
  from a non-GUI process or you'll get black screenshots / Canvas failures.
- **Select the live page by URL, not by list position.** Repeated
  `Page.navigate` / `location.reload` leaves several `type:"page"` targets alive and
  `json | head -1` routinely hands you a stale one that still reports the previous
  build's counters — so a "still broken" reading is often a probe aimed at a dead tab.
  Filter for the target whose `url` matches and keep exactly one, e.g.
  `curl -s .../json | jq -r '.[]|select(.type=="page" and (.url|test("8765")))|.webSocketDebuggerUrl'`,
  then assert the page you attached to is the one you are reading (check a frame
  counter monotonically increases across two reads). Make screenshot capture
  best-effort so a capture timeout cannot mask the numeric evidence you came for.
- **A reused `--user-data-dir` leaves dead targets that accept a WebSocket and
  then drop it.** A tab whose renderer was killed with the browser still appears
  in `/json/list`; `websockets.connect` succeeds and the next `recv` raises
  `ConnectionClosedError: no close frame received or sent` with no server-side
  diagnostic, which reads as a harness bug. The robust form is to **open a fresh
  target per run and use that one's URL**, never a positional pick from a list:

  ```python
  made = subprocess.run(["curl","-s","--noproxy","*","-X","PUT",
                         f"{CDP}/json/new?about:blank"],
                        capture_output=True, text=True, timeout=30).stdout
  target = json.loads(made) if made.strip().startswith("{") else <fallback>
  ```

  If `/json/new` returns empty while `/json/version` still answers, Chrome is in
  the state described above — a restart with `--remote-allow-origins='*'` is the
  fix, not more retries.
- **Assert the bundle you loaded is the bundle you just built** — compare the
  served `.wasm` mtime or a build-stamped string against disk before concluding
  any browser behaviour is current.

## Common pitfalls

1. **`Chromium browser is missing` from `browser_exec`** — and `npx -y
   agent-browser install chromium` says "already installed" without fixing it.
   The `browser_exec` tool maintains its own internal browser cache lookup that
   is independent of `~/.agent-browser/browsers/` and `~/.cache/ms-playwright/`.
   When `browser_exec` reports missing despite chromium being on disk, do NOT
   retry the install — drop down to `agent-browser` CLI driven from `terminal`:

   ```bash
   export AGENT_BROWSER_SESSION="$(npx -y agent-browser session id --scope worktree --prefix <task-name>)"
   npx -y agent-browser open "http://localhost:8765/"        # navigate
   npx -y agent-browser snapshot -i                         # AX refs for @eN
   npx -y agent-browser screenshot /tmp/x.png                # PNG screenshot
   npx -y agent-browser set viewport 375 667                # mobile viewport
   npx -y agent-browser set media dark                       # dark color scheme
   npx -y agent-browser mouse move 140 238                   # hover at coords
   npx -y agent-browser click "<css-selector>"               # or @eN ref
   npx -y agent-browser eval "JSON.stringify({x: ..., y: ...})"  # JS readback
   npx -y agent-browser close                                # tear down
   ```

   Treat the named session as the variable you set above — `agent-browser` keeps
   the browser alive across commands within one session, so the worktree scope
   prevents two agents on the same machine from hijacking each other's tab.
   `mouse move` (not `hover` selector) is what triggers real `:hover` CSS state
   for visual verification; `click "<selector>"` is the right way to click
   elements that the AX snapshot doesn't surface as interactive refs.

   Two `agent-browser` gotchas that cost real time:
   - **`eval` does not isolate JS state across calls.** Top-level `let x = ...`
     in one call collides on the next call with
     `SyntaxError: Identifier 'x' has already been declared`. Wrap the body in
     an IIFE — `eval '(() => { const x = ...; return JSON.stringify({x}); })()'`
     — or use a uniquely-prefixed variable each time.
   - **Responsive drawers / hamburger menus are hidden below the mobile
     breakpoint.** After `set viewport 375 667`, a screenshot of the page shows
     only the closed top bar. Probe the menu button via `eval` to find its
     selector (often `c_mobile_menu_button` / `c_hamburger` / `data-testid`),
     then `click` it before screenshotting the sidebar or nav drawer contents.

2. **Hover/active state is invisible when a design token equals the
   background.** `var(--accent-muted)` resolving to `#ffffff` on a `#ffffff`
   surface is common in monochrome / theme-token-driven libraries — `:hover {
   background: var(--accent-muted) }` then has zero visual effect. Diagnose
   by reading `getComputedStyle(el).backgroundColor` on the hovered element:
   if it returns `rgba(0, 0, 0, 0)` and you expected a fill, the token is the
   problem. Fix with literal `rgba(0, 0, 0, 0.08)` (light) /
   `rgba(255, 255, 255, 0.10)` (dark) rather than chasing a token swap.

3. **`urllib` returns 502 to `127.0.0.1` inside `execute_code`.** The kernel
   routes through a proxy. Always set `NO_PROXY=localhost,127.0.0.1` AND
   use `urllib.request.build_opener(urllib.request.ProxyHandler({}))`. One
   of those alone is not enough.

3. **Reading responses and events on the same socket without separation.**
   You'll silently mismatch ids and "lose" commands. Always background a
   reader that splits on `"id" in m`.

4. **`Page.navigate` doesn't wait for load.** Add your own readyState poll
   or listen for `Page.loadEventFired` before screenshotting / scraping.

5. **`headless=new` vs legacy `--headless`.** New headless is the only one
   that ships a full Chromium with proper screenshot/Canvas support.
   Legacy `--headless` produces stub screenshots for many pages.

6. **Port 9222 already taken.** Either reuse the existing Chrome (find
   targets via `/json`) or pass `--remote-debugging-port=9223` to a fresh
   instance and update `WS`.

7. **`Target.createTarget` from a page target fails.** Target management
   lives on the browser-level target. Open a second websocket to the
   `browser` ws URL.

8. **`Page.captureScreenshot` with `clip` is silently clipped to wrong
   region if scrollbars are visible.** Always pass
   `--hide-scrollbars` to Chrome and `captureBeyondViewport:false` unless
   you specifically want the full page.

9. **Re-using `chrome --remote-debugging-port` after a `Ctrl-C`.** The
   Chrome process keeps running and the port stays bound. Either kill
   the parent explicitly (`pkill -f 'remote-debugging-port'`) or pass
   `--user-data-dir` to a fresh profile.

10. **Stopping `chrome` with `terminal` and `&` errors out.** The CLI
    refuses `&` backgrounding with a hint to use `background=true`. Use
    the `terminal(background=true)` tool call instead of inline `&`.

11. **`mouseover`/`mouseenter` from `Runtime.evaluate` do NOT trigger CSS
    `:hover` rules in headless Chrome** — synthetic events dispatch into
    JS but the layout engine keeps the cursor at (0,0) and never enters
    the hit-test region, so the selector never sees the cursor and
    `:hover` never applies. The reliable way to screenshot or assert
    `:hover` / `:focus` / `:active` styles is `CSS.forcePseudoState`:
    ```python
    await c("CSS.enable")
    # nodeIds are returned by DOM.querySelectorAll, NOT the runtime
    # backendNodeId you sometimes see in other CDP outputs.
    node_ids = (await c("DOM.querySelectorAll",
                       {"nodeId": root, "selector": ".nav-item"}))["nodeIds"]
    await c("CSS.forcePseudoState",
            {"nodeId": node_ids[1], "forcedPseudoClasses": ["hover"]})
    # Now screenshot/inspect — the rule applies without a real mouse.
    await c("Page.captureScreenshot", {"format":"png"})
    ```

    Pass multiple pseudo-classes in one call (`["hover","focus"]`) to
    compose states. The forced state sticks for the page lifetime or
    until you call `forcePseudoState` again with an empty list.

12. **`Emulation.setDeviceMetricsOverride` resets on every navigation.**
    After `Page.navigate` (or `Runtime.evaluate('location.reload()')`),
    the viewport snaps back to the launch defaults — your carefully
    tuned `width:420 height:800 mobile:true` is gone, and screenshots
    silently come out at 1280x577 desktop size even though the call
    returned `{"result":{}}`. Re-apply the override AFTER every
    navigate/redirect, then poll `window.innerWidth` in the next
    `Runtime.evaluate` to confirm. The browser-harness `browser_exec`
    helper hits this every time you call `new_tab()` — pass the
    metrics override and a short sleep in the SAME code block as the
    navigation, not in the block before it.

13. **The browser caches static assets aggressively across rebuilds.**
    When verifying UI changes against a long-running local HTTP server
    (Python `http.server`, `vite preview`, a `file://` build), the
    `.css` / `.wasm` / `.js` artifacts stay cached by URL — even
    though disk has the new bytes, the rendered DOM still reflects
    the old ones. Two fixes that work together: send a cache-buster
    on the URL (`http://localhost:8765/?_=fresh#/path`), and call
    `Network.clearBrowserCache` once before the verify pass. Hard
    reload alone (`Ctrl-Shift-R`) is not enough when CDP is driving
    the page; the cache-buster URL is the reliable lever. Symptom:
    you patched `c_euv_footer { margin-top: 80px → 24px }`, the build
    succeeded, the wasm contains the new rule, but
    `getComputedStyle(footer).marginTop` still reads `"80px"`.

    14. **Games read `KeyboardEvent.code`, and only a real `Input.dispatchKeyEvent`
     populates it.** A handler bound to `e.code === "KeyW"` is unreachable from
     `Runtime.evaluate`-dispatched `KeyboardEvent`s — a `code: "a"` value is a
     character, not a key code, so the player stands still and a working feature reads
     as unimplemented. Use `Input.dispatchKeyEvent` with
     `{"type":"keyDown","key":"w","code":"KeyW","windowsVirtualKeyCode":87}`, then a
     tick, then `keyUp`, and assert a numeric position delta. Before blaming the app,
     search the source for what it actually reads: `.code` vs `.key` vs `.keyCode`.

    15. **Movement is usually camera-relative, so a fixed WASD script steers into
    walls.** `W` moves along the *camera's* forward vector, not world `-Z`. Close the
    loop on observed state instead of assuming a mapping: run once, read the actual
    delta, derive `forward = (dx, dz)/|Δ|`, then steer by that vector. Recalibrate
    whenever the camera yaw changes, and budget a calibration run before the path
    test means anything.

    **Calibrate the sign by measurement, never by algebra.** A closed-loop steering
    controller needs to know whether increasing yaw turns toward or away from the
    target; that is a property of the engine, not something to derive from the
    camera math. Derive it, get it wrong, spend rounds re-deriving it. Emit one
    scripted calibration that holds one turn key, samples the position delta, and
    prints the sign it measured, then bake that into the loop. I got this backwards
    twice in one session from algebra; the measurement takes one run.

    **A stall has two indistinguishable causes; rule one out before tuning the
    other.** "The player stopped moving" reads identically for a wrong steering
    sign and for a wall the player is pressed against. Before touching the control
    law, check whether the world actually blocks that position — query the
    collision set, the nearby geometry, or just whether the coordinate that stopped
    increasing is a known obstacle boundary. A controller sign error and a
    building's wall face produce the same trace, and tuning a sign while the real
    cause is a wall burns the whole budget.

    **Decide which evidence settles the claim, and say so when one kind is
    missing.** For world-generation work, a unit test that builds geometry around
    a far coordinate and asserts its extent is the proof; a browser walk is a
    bonus that additionally shows the streaming path fires. When the unit test
    passes and the walk stalls on a wall, report both plainly — the walk's failure
    is a harness limitation, not evidence against the generator, and leaving the
    split unstated is what makes a session's end state unreadable.

    16. **Iterating a CDP harness by string-replacement destroys it.** Long
    scripted verify runs get tuned in place — swap a key, change a leg count, fix
    a threshold — and each `s.replace(old, new)` on a multi-line block silently
    reflows indentation, so after a few rounds the script is a syntax error with
    balanced-looking content. Replacements that matched nothing also return
    silently, so a "fix" that did not land looks identical to one that did.

    Rewrite the changed block by line index rather than by substring, assert the
    match count before replacing, and re-parse (`ast.parse` / `python3 -m py_compile`)
    after every edit rather than at the end. Keep the harness in version control
    or a scratch copy — a broken harness that took ten rounds to build is worse
    than a wrong one. The general rule: **a test harness is a program, so it gets
    the same edit discipline as the code it exercises.** A harness that no longer
    parses produces a traceback, not a result, and the traceback gets read as a
    finding about the app.

17. **Against a throttled game loop, both fixed sleeps and frame counts race
    the app — poll a state predicate instead.** Headless Chrome can hold
    `requestAnimationFrame` near 1 fps, so a request that mutates state takes
    seconds of wall time to become observable. Two tempting waits are both
    wrong, for different reasons:

    ```python
    # WRONG: the loop may not have ticked at all in 2 s
    await asyncio.sleep(2.0); st = await d.st()
    # WRONG, and worse: `frames` is read AFTER the request already landed,
    # so start+n is satisfied on the first poll and you sample pre-rebuild state
    start = (await d.st())["frames"]; await asyncio.sleep(1)
    ```

    Poll the predicate you actually care about, with a generous cap:

    ```python
    async def until(d, pred, cap=40, step=0.3):
        for _ in range(cap):
            await asyncio.sleep(step)
            st = await d.st()
            if st and pred(st):
                return st
        return await d.st()
    ```

    Pick a predicate that can only be true *after* the work completed, not
    merely after the request was sent: "the world-generation centre is now a
    multiple of the tile pitch" proves a rebuild ran; "the frame counter
    advanced" proves only that time passed.

18. **A state-mutating request that also sets the flag the system uses to
    decide whether to do work permanently suppresses that work.** This reads as
    "the feature is broken" because the call succeeds and nothing happens:

    ```rust
    // teleports the player, then "helpfully" snaps the generation centre to
    // the destination — so next frame |player - centre| == 0, the rebuild
    // threshold is never crossed, and the terrain never regenerates
    game.player.set_position([x, y, z]);
    game.streamed_center = [x, z];   // <- deletes the behaviour under test
    ```

    Move the player; let the app's own threshold notice and act. A test seam
    that also keeps the world consistent is convenient, and is also the thing
    that removes the behaviour you were sent to observe.

19. **Before probing position or state, assert the app is in the mode you
    think it is.** A mounted/driven/attached mode swallows position writes:
    setting the entity's position moves the *vehicle* while the player stays
    glued to the seat, so every teleport is silently ignored and downstream
    checks read stale spawn values. Drive it back to the default *before* the
    probe:

    ```python
    for _ in range(4):
        if not (await d.st() or {}).get("veh"): break
        await key_tap(d, "KeyF")
    ```

    The tell is a state probe whose value never moves no matter what you send,
    while unrelated counters advance normally.

20. **When synthetic input cannot reach a listener, inject the intent through
    a debug seam that bypasses only the input layer.** If neither
    `Input.dispatchMouseEvent` nor a `new MouseEvent(...)` dispatched on the
    element moves the app's input flag, the listener is unreachable from the
    harness — but the behaviour *behind* it is usually fine and still worth
    testing. Have the app read a request object on `window` each frame and set
    the same flag the real event would set, for one frame only:

    ```rust
    // one frame of injected intent; everything downstream is the real path
    if request.get("hold") { game.input.fire_held = true; game.hold_frames = 1; }
    ```

    This is not a weaker test of the feature — magazine decrement, cooldown,
    hitscan and damage still run the identical code a real click runs. It is
    strictly stronger than declaring the feature unverifiable, and it is honest
    about which layer was skipped. Scope the injection to a single frame: a
    "held" flag that is never released fires forever.

    ### One channel, several sub-commands: whichever branch returns first wins

    A seam that multiplexes every intent onto **one** object on `window` has a
    defect invisible in each sub-command taken alone. The dispatcher inspects
    one request per frame and returns on the first match:

    ```rust
    if request.safe { game.safe_mode = true; return; }        // <- returns here
    if request.walk { game.walk_request = [dx, dz]; return; }  // never reached
    ```

    Sent separately, `{safe: true}` then `{walk: true, ...}` are two frames and
    both work. Sent as one combined object, the first branch matches, returns,
    and the walk is dropped every frame. The symptom is maximally misleading:
    the state flag reads true, so the seam appears to be working, while the
    action never happens at all. Here that presented as *the doorway being
    sealed by geometry*, and sent several rounds of search after a collision
    model that was correct.

    **Rule: a multi-sub-command seam must treat one request as a set of
    independent flags, never as a single winner.** Apply the state-setting
    sub-commands, and return early only for the genuinely exclusive ones:

    ```rust
    let wants_walk = request.get("walk").is_truthy();
    if request.get("safe").is_truthy() {
        game.safe_mode = true;                        // no bare `return` here
        game.player.set_health(PLAYER_MAX_HEALTH);
        if !wants_walk { return; }                     // only when exclusive
    }
    if wants_walk { game.walk_request = [dx, dz]; return; }
    ```

    **Prove the seam composes by sending combined requests, never single
    ones.** A seam exercised one sub-command at a time cannot fail here, so a
    green run is not evidence. Send `{walk, safe}` together and assert the
    *action* happened (position moved) as well as the *state* (flag set) —
    asserting only the state is precisely what let this pass unnoticed.

    The generalisable form: **a harness that reports a state flag is verifying
    the flag, not the behaviour.** When a seam exposes both, assert on the
    behaviour and read the flag only as a diagnostic.

    Two related rules from the same seam:
    - **Make the seam generic** (teleport / aim / walk-direction / one-shot
      intent) rather than one bespoke hook per check; it is the same code path
      every time.
    - **Inject at the top of the frame, not at the end.** A handler placed after
      the simulation step means the frame it ran used the old coordinates, and
      the flag it set is only read on the *next* frame — one frame's worth of
      checks gets skipped in between.

    ### A per-field reader with one shared default corrupts the fields it does not receive

    The branch-wins defect above fails loudly on the action while the state flag
    reads correct. This sibling fails the other way: nothing errors, the state
    flag is right, and the *coordinate* silently becomes a constant.

    ```rust
    let read = |field: &str| -> f32 {
        Reflect::get(&request, &key(field)).ok()
            .and_then(|v| v.as_f64()).map(|v| v as f32)
            .unwrap_or(SPAWN_POINT[0])          // <- one default for every field
    };
    let x: f32 = read("x");
    let z: f32 = read("z");
    ```

    A request carrying `x` but not `z` sets `z` to the spawn's X, not its Z. The
    result reads as "the app teleported to the wrong place" or "the teleport
    silently failed", and it points at the harness when the real defect is a
    default shared across fields that have no default in common. Index the right
    component per field (`SPAWN_POINT[0]` for x, `SPAWN_POINT[2]` for z), or
    return early when a required field is missing so a partial request is a no-op
    instead of a half-teleport.

    **Check the observed value against the default before blaming the app.** A
    landing point that is *near* a spawn constant but not equal to it did not come
    from this path at all. Chasing a defect whose predicted output does not match
    the measurement burns rounds on a coincidence — in this session the constant
    was 33.5 and the observed x was 33.10, which ruled the whole branch out and
    sent the search to the collision solver where the answer was.

    ### Speed up a suite by parallelising instances, and know the ceiling

    A suite whose wall clock is dominated by one slow item parallelises by
    instance, not by tab: one browser serialises the GPU work every group
    contends for. Give each group its own `--user-data-dir` and debugging port,
    parameterise the port through the environment so one script serves all
    groups, and verify every port bound before starting. Split the item list by
    **section marker in the source** and emit one entry point per group over a
    shared library — emitting each group as a self-contained copy works once and
    then becomes six 27 kB files where a 600-line module plus six 70-line entry
    points would do. Re-verify the collapsed form; a harness tested only in its
    duplicated shape has not been tested in the shape you ship.

    Four to five concurrent instances is the useful ceiling on one machine. At six,
    simultaneous Chrome initialisation starved one group into a multi-minute
    stall before it wrote a single line — so **treat an empty log as a startup
    failure, not a slow group.** A group that never opened its tab writes nothing
    and is otherwise indistinguishable from one still working.

    Report per group as each lands rather than only in a final aggregate: the
    fast groups finish long before the slow one, and a summary that appears only
    at the end leaves the finished groups looking unfinished. State explicitly
    that the count is partial until the slow group reports.

    ### Re-verify with the parallel runner after every code change

    Once the suite is parallel, a change to the app invalidates every prior
    result, and the cheapest way to re-run is the same script that produced the
    baseline. Keep it in the repo next to the app (`tools/verify-parallel.sh`
    plus the group entry points) rather than in scratch, or the next session
    rebuilds the fan-out from nothing and re-discovers the port collision.

21. **A rich-text editor is a `contenteditable` DIV, and the selector whose name
    mentions "text" is often a decoy — so prove which node edits before blaming
    the framework.** Draft.js, ProseMirror, Quill, Slate and Lexical all render
    `<div contenteditable>` and carry a `data-testid` naming a textarea. Apps
    frequently *also* render a sibling display node whose testid reads like the
    editor's text. Measured on one composer:

    | selector | `contenteditable` | `role` | holds the text? |
    |---|---|---|---|
    | `[data-testid="tweetText"]` | **`null`** | none | no — display layer, `textContent` goes stale |
    | `[data-testid="tweetTextarea_0"]` | `true` | `textbox` | **yes** |

    Six input techniques were tried and all six "proved" the editor
    undrivable — because every one of them targeted the decoy. **Before
    reporting any rich-text target as undrivable, re-run the node probe
    against the selector you actually used, and re-derive the claim; a
    technique that fails against one node says nothing about another.** A
    "this framework cannot be driven" conclusion reached on the wrong node is
    the most expensive mistake available here, because the user acts on it.
    Identify the editing node instead of trusting the testid name:

    ```js
    (() => {
      const wrap = document.querySelector('[data-testid="tweetTextarea_0"]');
      const ed = [wrap, ...wrap.querySelectorAll('*')].filter(
        e => e.getAttribute('contenteditable') === 'true' || e.isContentEditable);
      return JSON.stringify(ed.map(e => ({
        tag: e.tagName, testid: e.getAttribute('data-testid'),
        role: e.getAttribute('role'), text: e.textContent.slice(0, 40) })));
    })()
    ```

    Two consequences worth internalising:

    - **A decoy's `textContent` goes stale**, so reading through it makes
      *working* input look like a no-op. A real keystroke landed and the decoy
      never reported it. Read the node you wrote to.
    - `execCommand('insertText')` is not a general fix: it returned `false`
      here, on the correct node. Treat it as one attempt, not the answer.

    Setting `.textContent`/`.innerHTML` on a real editor still stores text the
    framework never sees — its state stays empty and submit stays disabled. For
    the working write path see `references/real-account-automation.md`.

22. **Never write into an editor that already holds text — and prove you are
    attached to the tab you opened before you write at all.** On a logged-in
    real account, several tabs of the same app are frequently open at once
    (in-progress drafts). `querySelector` returns the FIRST match in the
    document, which is not necessarily the tab you created, and the SPA may
    restore a prior draft into a fresh compose route. A script that types into
    "the composer" and then clicks publish will happily destroy a draft the
    user has been working on for an hour and post it under their name.

    Three gates, all before the first write:

    ```python
    # 1. the target is the one you created, not one you picked from a list
    tab = http("/json/new?" + quote(url), method="PUT")   # returns the new target
    assert "/compose/post" in tab.get("url", "")
    c = Cdp(tab["webSocketDebuggerUrl"])                   # THIS tab's socket

    # 2. the field is empty, or it is text you put there
    existing = c.js("document.querySelector('[data-testid=\"tweetText\"]')?.textContent")
    if existing and existing.strip():
        raise RuntimeError("composer already holds text that is not ours: "
                           + repr(existing[:200]))

    # 3. read back what landed and compare, before touching submit
    got = c.js("document.querySelector('[data-testid=\"tweetText\"]')?.textContent")
    assert "".join(got.split()) == "".join(MY_TEXT.split())
    ```

    Gate 3 is what actually saved the run: the content mismatched, the script
    raised, and an unrelated draft survived intact. Compare normalised
    whitespace (`"".join(s.split())`) because `innerText` and `textContent`
    disagree about blank lines in a contenteditable block structure. A
    destructive step whose blast radius is a user's unpublished work needs a
    read-back, not a click.

23. **A CDP client that returns `None` on failure turns every conclusion into a
    guess — and two of its own bugs are silent.** A lost reply, a dropped
    control frame and a genuine "the app did nothing" are indistinguishable if
    the client returns the same falsy value for all three. The consequence is
    not a crash; it is a confident wrong answer, which is worse.

    **WebSocket control frames are not JSON.** Opcodes 8/9/10 (close/ping/pong)
    and 2 (binary) share the wire framing but carry no message. Decoding one as
    JSON raises `UnicodeDecodeError`, and swallowing that as "no reply" makes
    every subsequent command look like it never ran. Check `opcode = b1 & 0x0F`
    before decoding, and handle ping by replying pong. The symptom is
    baffling because it is intermittent and self-healing: two separate rounds
    of a real task concluded "the click did nothing" when the truth was that
    the reply was never parsed.

    **The first few evaluates on a NEW target lose their replies.** While the
    renderer swaps execution contexts the reply never arrives, so a fixed
    per-attempt wait just burns time: measured 33 s of warm-up on a fresh
    target, then ~0.5 s per call. Retry with a *short* wait, not a long one,
    and always with a ceiling — an unbounded poll plus a heavy page turned into
    a 14-minute freeze that read as a hung browser. A `js()` that surfaces
    `__timeout` / `__js_error` markers instead of `None` is what makes the
    difference visible.

    When a probe "returns nothing", the first two questions are always: did the
    command run, and did the reply parse — not "what does the app state look
    like".

    Before trusting a client against a real account, run a self-test that
    asserts the properties rather than a smoke path: falsy-but-valid results
    (`0`, `""`, `false`) survive, a thrown error is marked, the stream survives
    idle time, and open/close genuinely changes the target count. Such a test
    earns its keep immediately — one written here reported a *working*
    `close_tab` as broken (its arithmetic compared a count after a close
    against a base taken before the matching open) and flagged a slow client
    that was only doing target warm-up. Both faults were in the test.

    **Clean up every target you open.** `/json/new` leaves an orphan behind if
    the caller never closes it; a few hundred orphans make the whole browser
    unresponsive while the harness still reports "no error". Wrap open+use in a
    context manager so the two cannot drift apart, and assert the count drops.

24. **Pin the port you are talking to; do not trust a shared-state file.** A
    port recorded by whichever process last started a browser is not
    necessarily the one answering now — another session can start its own in
    parallel. Verified mismatch: the recorded port was 9228 while the live
    instance was on 9231, so every command went somewhere the caller never
    intended. Read the port from the process you just started, or pass it
    explicitly, and have the client take the port as a parameter rather than
    reading global state per call.

    Corollary: when a shared browser stops responding, restart it deliberately
    instead of retrying against it. A wedged instance produces timeouts that
    look like application behaviour, and the retries cost more than a clean
    relaunch.

25. **A template that returns `JSON.stringify(...)` returns a STRING, and a
    caller that expects an object reads every field as absent.** One JS
    template answering `{"opened":true}` as `'{"opened":true}'` — while its
    siblings return bare objects — is enough for a fully working interaction to
    report as a refusal, with no error anywhere:

    ```python
    def js(c, tpl):                      # the trap
        r = c.js(tpl)
        if isinstance(r, dict):
            return r                      # dict -> fields visible
        return {"_raw": str(r)[:160]}     # str  -> every .get() is None
    ```

    Fix it in the parser, not at each call site, so a new template cannot
    reintroduce it:

    ```python
    def js(c, tpl):
        r = c.js(tpl)
        if isinstance(r, str):
            try: r = json.loads(r)        # stringify() output is JSON
            except ValueError: pass
        return r if isinstance(r, dict) else {"_raw": str(r)[:160]}
    ```

    **Keep every template in one file returning one shape.** Mixed styles are
    the defect, and they are invisible until a caller reads a key off the odd
    one out. The signature is a silent total failure: the interaction works,
    the verification fails, and the failure is reported as the *site* refusing
    rather than as a parse. Check the return type of each template the moment
    you add it.

26. **A rich-text editor stores newlines as ELEMENTS, so `textContent` has no
    newline characters and an exact compare can never pass for multi-line
    text.** The editor renders each break as a `<div>` or `<br>`, so walking
    child text nodes returns the lines with nothing between them. A 476-char
    source carrying 6 newlines read back 470 characters — correct text, failed
    check, and the run refused to send. Compare on non-space characters
    (`"".join(got.split()) == "".join(want.split())`), which preserves the
    guarantee that matters: a dropped or mangled character cannot hide behind a
    space.

    **Use the delta as a diagnostic.** `len(got) - len(want)` equal to the
    source's newline count means the editor normalised layout and the text is
    fine; any other delta is a real difference worth reporting. Never "fix" a
    newline mismatch by loosening the comparison to a prefix — see the gates
    in `references/real-account-automation.md`.

27. **A verification step inherits the scroll position the write step left
    behind, so it searches a viewport the result is not in.** Scrolling down to
    reach a target and never returning leaves the page below the item that was
    just created — a new post appears at the TOP of the feed, so the read-back
    finds nothing and reports a failure for a write that succeeded. Re-establish
    the viewport the verification needs (scroll to top, wait for the virtual
    list to settle) inside the verify step itself; do not rely on the state the
    previous step happened to leave. A scroll is not a navigation, so this costs
    nothing against a harness that forbids page loads.

28. **Run a CDP driver from a clean working directory.** Scripts on `sys.path`
    shadow stdlib by filename: a scratch `bisect.py` in the cwd made
    `import random` fail inside `urllib` with a traceback that named a dozen
    unrelated modules. Keep driver scripts out of a shared scratch directory,
    and when an import chain names a module you never wrote, check the cwd
    before the environment.

29. **A reply composer is a dialog you open per target — clearing only the
    obvious ones leaves the previous target's box live, and its header then
    reads as the current target's.** Modal containers accumulate: after several
    targets, the DOM holds a hidden dialog per reply already made. Removing
    dialogs that lack an editor misses exactly the ones still holding a
    half-written body, so the next click is intercepted by a stale overlay
    while a correct click reports `false`. Remove **all** dialogs before
    opening the next one, and always read the identity of the **last** dialog
    in the DOM — the first is the oldest, not the current.

30. **A changed URL is not a loaded page, and a `None` read is a load-state
    failure — never a "not found".** `Page.navigate` returns before render, so
    a URL-only assertion passes while the page is still the previous one. Every
    later step then resolves against stale content: the owner lookup returns
    `None`, and a fallback path acts on whatever dialog was already open.
    Gate navigation on rendered content (`querySelectorAll('article').length >
    0`) and raise when the URL changed but nothing rendered. Treating a `None`
    as "no such element" and falling through is what converts a navigation bug
    into a wrong-target send; treat it as a failed load and stop.

31. **A batch driver's skip list must be persistent, and written only after a
    confirmed send.** An in-memory dedupe set does not survive a restart, so
    the same topic runs in two processes and posts twice — a duplicate to a
    real person, which then has to be located, verified by author **and full
    body**, and deleted. Write the marker after confirmation, never before
    (a pre-write marker turns every transient failure into a permanent skip),
    and key it on content rather than on an author handle — the same person
    posts repeatedly and several posts can share one draft. The same persisted
    set should drive which items a run starts on: walking a completed work
    list from the top on every run costs one full cycle of re-attempts before
    reaching any new work.

32. **Chrome rejects a CDP WebSocket whose `Origin` is the devtools endpoint
    unless it was launched with `--remote-allow-origins`.** The handshake
    fails with `WebSocketBadStatusException: 403 Forbidden` and a body naming
    the flag, while `/json/version` and `/json/list` answer normally — so the
    browser looks healthy and only the socket is affected. Pass
    `suppress_origin=True` to `websocket.create_connection` (the websocket
    handshake does not need the header), or launch Chrome with the flag.
    Either fix; do not conclude the browser is down and relaunch it.

## Probing a WebGL app: read the state that is actually there

A black or wrong-looking canvas is the hardest thing to debug through CDP because
almost every WebGL query returns a plausible value even when you are asking the
wrong question. These are the traps, all of which cost real debugging time.

### Identify the pass before interpreting anything

A deferred renderer binds several framebuffers per frame (shadow 2048², G-buffer
full-res, SSAO/SSR/bloom half-res, scene full-res, then the default framebuffer
for the present). **A probe that does not identify which one it sampled will be
read as a bug when it is correct behaviour.** Two concrete examples that both
looked like root causes and were not:

- Reading `COLOR_ATTACHMENT0` on a **depth-only** shadow FBO returns
  `[0,0,0,0]`. That is correct — there is no color attachment. Sampling it
  proves nothing about the main pass.
- Reading `gl.getParameter(COLOR_ATTACHMENT0_BINDING)` mid-frame returned
  `false` while the attachment was in fact present, because the binding was
  queried at a different point in the frame than the draw.

Identify the pass by `gl.getParameter(VIEWPORT)` and log which program is
`CURRENT_PROGRAM` at the same instant. Program identity is the cheapest
discriminator: the shadow program legitimately has exactly one uniform
(`u_view_proj`) and no samplers, so `samplers: []` there is not a finding.

### Trust the authoritative query over the convenience one

For attachment presence use
`gl.getFramebufferAttachmentParameter(target, attachment, FRAMEBUFFER_ATTACHMENT_OBJECT_NAME)`
and `..._OBJECT_TYPE` (expect `5890` = `TEXTURE_2D`). The `*_BINDING` enum
params are snapshots of a moment and are the usual source of false negatives.

### Framebuffer status codes

`gl.FRAMEBUFFER_COMPLETE` is **36053** and `checkFramebufferStatus` returns
36053 for a complete framebuffer. Do not "correct" this to 36054 — a probe that
compares against 36054 will report every healthy framebuffer as broken and send
you hunting a bug that does not exist. (WebGL1 and WebGL2 number some status
codes differently, which is where the confusion starts; Chrome's WebGL2
`checkFramebufferStatus` agrees with the `FRAMEBUFFER_COMPLETE` constant.)

Also: `getTexLevelParameter` **does not exist in WebGL2** (it is WebGL1). To
inspect a bound texture, attach it to a scratch FBO via
`framebufferTexture2d`, check status, and `readPixels` a small region.

### Bisect the attachment format — read pixels, not the status code

A framebuffer can report `FRAMEBUFFER_COMPLETE` while every `glClear` is a no-op and
every draw is discarded, because an attachment exists but is not *renderable*. Status
codes will not tell you this. Build scratch framebuffers in the live context and
compare them — the app's own code is not a variable you can isolate:

```js
(() => {
  const gl = document.getElementById('vcw-canvas').getContext('webgl2');
  const probe = (d) => {
    const col = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, col);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,64,64,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
    let dep=null, rb=null;
    if (d.tex) {
      dep = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, dep);
      gl.texImage2D(gl.TEXTURE_2D,0,d.internal,64,64,0,d.format,d.type,null);
    } else {
      rb = gl.createRenderbuffer();
      gl.bindRenderbuffer(gl.RENDERBUFFER, rb);
      gl.renderbufferStorage(gl.RENDERBUFFER, d.internal, 64, 64);
    }
    const fb = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,col,0);
    if (dep) gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.TEXTURE_2D,dep,0);
    else     gl.framebufferRenderbuffer(gl.FRAMEBUFFER,gl.DEPTH_ATTACHMENT,gl.RENDERBUFFER,rb);
    const status = gl.checkFramebufferStatus(gl.FRAMEBUFFER);
    gl.viewport(0,0,64,64);
    while (gl.getError() !== 0) {}
    gl.clearColor(0.25,0.5,0.75,1); gl.clear(gl.COLOR_BUFFER_BIT);
    const b = new Uint8Array(4);
    gl.readPixels(32,32,1,1,gl.RGBA,gl.UNSIGNED_BYTE,b);
    const err = gl.getError();
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    return {status, pixels:Array.from(b), err};
  };
  return JSON.stringify({
    noDepth:  probe({tex:false, internal:0}),
    r32fTex:  probe({tex:true, internal:gl.R32F, format:gl.RED, type:gl.FLOAT}),
    d24Tex:   probe({tex:true, internal:gl.DEPTH_COMPONENT24,
                     format:gl.DEPTH_COMPONENT, type:gl.UNSIGNED_INT}),
    d24Rb:    probe({tex:false, internal:gl.DEPTH_COMPONENT24}),
  });
})()
```

Read the **`pixels`** field, not the status: a working variant writes the clear colour
back as `[64,128,191,255]`. This is the probe that finds a **non-renderable depth
attachment** — `R32F` is a *colour* format, renderable only with
`EXT_color_buffer_float`, and attaching it to `DEPTH_ATTACHMENT` is rejected outright by
several implementations (SwiftShader among them). The app-level symptom is a healthy
triangle count, a live frame counter, inconsistent `FRAMEBUFFER_COMPLETE` reporting and
a uniformly black canvas. Depth-only shadow maps fail the same way, since they are depth
textures like every other target. When the shadow pass compares depth manually
(`texture(map, uv).r` against fragment depth), switching to `DEPTH_COMPONENT24` needs no
change to the sampling code.

### Exonerate the fragment stage with a constant before touching the pipeline

When a scene renders nothing, the fastest first move is to replace the fragment shader's
final output with an unconditional literal (`out_color = vec4(0,1,0,1);`) and rebuild.
A screen that is **still** black proves the fragment stage never executed or its output
never landed, which eliminates lighting, textures, uniforms and tone mapping in a single
edit. A green screen proves the fault is upstream — vertex transform, instance data,
geometry — and exonerates the lighting maths. Revert the whole experiment afterwards,
including helper edits made while bisecting.

### GL errors are sticky — drain them before probing

`gl.getError()` returns the *first* error since the last call and keeps
returning it until cleared. A `1286 INVALID_FRAMEBUFFER_OPERATION` or
`1280 INVALID_ENUM` seen "every frame" is frequently left over from an earlier
frame, not evidence about the current one. Loop
`while (gl.getError() !== 0) {}` before a measurement, and read `getError()`
*immediately* after the single call you care about.

### Prove your hook fired

Monkey-patching `WebGL2RenderingContext.prototype.framebufferTexture2d` can
miss calls entirely if the code holds a bound function reference, producing an
event log with no entries and the wrong conclusion ("the attachments are never
set"). Assert that your hook actually observed the call before believing a
negative result from it. Conversely, hooking `drawArrays`/`drawElementsInstanced`
and keying on `count === 3 && FRAMEBUFFER_BINDING === null` is a reliable way
to catch the present pass.

### Under software rasterization, prefer synchronous readback

With `--use-angle=swiftshader`, a `requestAnimationFrame` promise used to
sequence a probe can never resolve, and `readPixels` on a large region can stall.
Sample a small region, and read synchronously outside rAF. Also note that
`preserveDrawingBuffer: true` in the context attributes is what makes a
`readPixels` of the default framebuffer meaningful after the frame ends.

### The general rule

A measurement is only worth the proof that it sampled the target you intended.
Before reporting a number as a root cause, state which pass/FBO/program it came
from. Three separate wrong-target readings in one session produced three
confident-sounding false root causes.

## Step 5 — Tear down

```bash
pkill -f 'remote-debugging-port=9222'
rm -rf /tmp/cdp-demo/profile
```

Always kill Chrome when done — a long-running headless Chrome accumulates
memory and leaks file descriptors, especially if you opened many targets
with `Target.createTarget`.

## Sharing the user's logged-in Chrome session

### First: check whether the toolchain already has a supported path

Before hand-rolling any profile copy or CDP attach, ask the toolchain what it
supports natively. In Hermes the browser is configured, not improvised, and the
supported setting for "drive the user's real logins, not a throwaway dev
profile" is two config keys:

```bash
hermes config set browser.use_real_profile true   # consent: browse with real logins
hermes config set browser.engine chrome           # Chrome, not lightpanda/other engines
hermes config get browser.use_real_profile        # read back
```

`browser.use_real_profile` does **not** attach to the user's daily Chrome
window (that would fight the running instance for the profile lock). It
snapshots the default-Chromium profile into a Hermes-owned copy
(`~/.hermes/browser-profile/<browser>`), launches the **real system browser
binary** on that copy, and re-syncs the auth databases per fresh session. Two
consequences worth knowing before you promise anything:

- The copy deliberately omits `--use-mock-keychain` / `--password-store=basic`,
  so macOS keychain-encrypted cookies decrypt and the session is genuinely
  signed in. A dev/automation Chrome that *does* pass those flags shares no
  login state at all — that is the usual reason an "already signed in" page
  looks logged out to the agent.
- Turning the key back off deletes `~/.hermes/browser-profile/`, so revoking
  consent also removes the copied credentials. Check that path is gone rather
  than assuming no credential copies remain.

Config changes to tools take effect on a new session (`/reset`), not
mid-conversation.

Only fall through to the manual CDP-attach recipe below when you are driving
Chrome from plain terminal scripts, or when the config path is unavailable.

### Otherwise: attach agent-browser to the running Chrome

agent-browser (the high-level CLI used elsewhere in this skill via
`browser_exec`/the `agent-browser` command) spawns its own Chromium with a
fresh profile by default, so its cookies are NOT inherited from the user's
regular Chrome. When the task needs an already-logged-in GitHub / SaaS session
(you cannot fall back to a token because none is configured, and the user
said "Chrome is already signed in"), the working path is to attach
agent-browser to the user's Chrome via CDP — agent-browser has a `connect`
subcommand for exactly this:

```bash
# 1. Tell the user to fully quit Chrome first (Cmd-Q), then reopen with:
#    open -a "Google Chrome" --args --remote-debugging-port=9222
# 2. Wait ~2 s for Chrome to bind the port.
# 3. Verify the discovery endpoint works WITHOUT auth:
curl -s http://127.0.0.1:9222/json/version
# 4. Have agent-browser attach to it:
npx -y agent-browser connect http://127.0.0.1:9222
# All subsequent agent-browser commands run in that user's existing tabs
# (and share their cookies / sessions) until you `agent-browser close`.
```

Why this beats `--profile Default`: agent-browser's `--profile` flag looks
in `~/Library/Application Support/Google/Chrome/` (read-only / TCC-gated on
recent macOS, returns "No Chrome profiles found" when blocked), AND a
separate profile dir would not share cookies with the running Chrome
instance anyway. CDP attach shares the live Chrome process state directly.

Fallback if Chrome was already running without `--remote-debugging-port`:
the user has to quit and relaunch with the flag, OR you can copy the
Cookies SQLite from Chrome's user-data-dir into a fresh profile dir that
agent-browser points at via `--user-data-dir`. The first path (CDP attach)
is much simpler and is what to try first.

### When you cannot ask the user to relaunch Chrome

If the user is unavailable (away from the keyboard, "I can't operate the
computer") and Chrome is already running without `--remote-debugging-port`,
**do not assume you can start a fresh Chrome with the user's profile from
Hermes**. Two paths both fail on recent macOS:

- **`--user-data-dir=$HOME/Library/Application Support/Google/Chrome
  --profile-directory=Default`**: the child Chrome inherits TCC restrictions
  from the Hermes process tree and exits immediately after launch — no
  `:9222` listener appears. The TCC block is on the user-data-dir itself,
  not on Hermes; child processes inherit it the same way.
- **`launchctl asuser <uid> /Applications/Google Chrome.app/...`**: same
  failure. `asuser` only changes uid context, not TCC inheritance, and the
  user's Chrome processes inherit the same dir restriction from the
  controlling Hermes process.

Verifying the failure (cheap): launch Chrome with the flag, sleep 3-8 s,
then `curl -s --max-time 3 http://localhost:9222/json/version`. An empty
response plus a Chrome process that is alive but not listening means TCC
killed the cookie/profile read; the launch itself succeeded.

When both fail, the only remaining options are (a) the user relaunching
Chrome themselves with the debug flag, (b) a GitHub PAT / token the user
can paste into a non-interactive input, or (c) an unauthenticated fallback
that the task actually permits (e.g. public endpoints via `web_extract`).
Do not loop on chrome launch attempts — each attempt confirms the same
TCC boundary and burns time. Stop after two attempts and tell the user
the wall is real.

### Telling "TCC denied it" apart from "the browser has a lock"

These two look identical in the error text and have opposite fixes, so
never trust the message. The distinction is mechanical: **a real lock has a
`SingletonLock` symlink; a TCC denial does not.** Run the probe before
advising the user to quit their browser — telling someone to close Chrome
when the actual cause is a privacy grant wastes their time and fixes nothing.

```bash
python3 ~/.hermes/skills/web/chrome-devtools-protocol/scripts/diagnose_chrome_profile_access.py
```

The probe decides TCC vs lock, sweeps sibling directories to show the
boundary, and walks the process ancestry to name the app that actually
needs the grant. The short version of what it checks:

- `os.listdir()` on the profile raising `PermissionError` with `errno == 1`
  (EPERM) is **TCC**, not Unix permissions. A Unix denial would surface as
  `errno == 13` (EACCES).
- `stat` shows the profile owned by the invoking user with mode `0700`, and
  the shell can read neighbouring directories fine — TCC is a per-app
  policy, not a filesystem mode.
- The denial is **selective across sibling app-data directories**. If
  browser profiles are denied while `Library/Preferences` is readable, you
  are behind an App Data privacy grant, not a broken browser.
- `os.path.isfile()` on a TCC-denied path returns `False` rather than
  raising. Code that branches on `isfile()` before opening will silently
  treat "denied" as "absent" and report a missing profile.

TCC is evaluated per **responsible application**, and a shell-launched agent
inherits the grant of whatever launched it (a terminal, a GUI terminal
emulator, an IDE). The grant must go to that ancestor app, not to Chrome
and not to a `launchctl asuser` wrapper. The process ancestry is the way to
find the real holder:

```bash
PID=$$; for i in $(seq 8); do
  P=$(ps -o ppid= -p "$PID" 2>/dev/null | tr -d ' '); [ -z "$P" ] && break
  echo "$PID -> $P : $(ps -o comm= -p "$P" 2>/dev/null)"; PID=$P
done
```

The remediation is a user action in System Settings → Privacy & Security →
Full Disk Drive Access, granting the ancestor app, followed by a full quit
and relaunch of that app so the new grant is picked up. A grant cannot be
issued from the terminal — `tccutil` only resets entries, it cannot add
them — so stop and hand this to the user rather than attempting it.

### Reusing agent-browser's already-running Chrome

If you previously launched an `agent-browser open ...` command, that Chrome
for Testing instance is still alive with its own `--remote-debugging-port=0`
(random). Find the port without re-launching:

```bash
PID=$(pgrep -f "agent-browser-chrome" | head -1)
lsof -p $PID 2>/dev/null | awk '/LISTEN/{print $9}'
```

Connect directly to it with raw CDP — its profile is empty, so it has no
user login cookies, but it is a fully functional headless Chromium you can
drive while the agent-browser CLI is busy or unresponsive.

## Fanning a slow verification suite out across several Chrome instances

A suite whose cost is dominated by one long item is a candidate for parallel
fanning-out, but only once the per-item cost is understood. Split by **section
marker in the source**, not by hand-picking: locate the `--- 4. name ---`
comments, cut the list at those line numbers, and emit one script per group.
Each group keeps the shared driver.

```python
lines = src.split("\n")
head    = "\n".join(lines[:main_start])        # Driver + helpers, once
setup   = "\n".join(lines[main_body:first_mark])
SUMMARY = "\n".join(lines[summary_start:summary_end])   # every group prints it
for name, (a, b) in GROUPS.items():
    code = (head + "\n" + "async def main() -> None:\n" + setup
            + "\n".join(lines[a:b]) + "\n" + SUMMARY + "\nasyncio.run(main())\n")
    ast.parse(code)                             # per group, before running any
```

**One instance per group, not one instance with several tabs.** A single browser
serialises the GPU work every group contends for, so the wall clock barely
moves. Each instance needs its own `--user-data-dir` (a shared profile locks on
the second attach) and its own debugging port; parameterise the port through the
environment so one script serves all groups:

```python
CDP = os.environ.get("VCW_CDP", "http://127.0.0.1:9223")
```

Verify every instance bound before starting the fan-out, and treat an empty
log file as a startup failure rather than a slow group — a group that never
opened its tab writes nothing and is indistinguishable from one still working.

**If the user asked for a fixed lane count, keep the count and fix the start.**
When a parallel verification is specified as N lanes, N is a requirement, not
a default to be trimmed for throughput — the user is usually splitting the
suite by a structure they already know (test domain, module, screen) and cares
that all of it is covered. Reducing the count silently substitutes your
judgement about throughput for the coverage decision that is theirs.

The contention is a *startup* problem, so stagger the launches and let each lane
prove it is alive before the next begins:

```bash
for i in $(seq 1 6); do
  port=$((9230 + i)); profile=/tmp/vcw/prof-$i
  "$CHROME" ... --remote-debugging-port=$port --user-data-dir=$profile &
  until curl -sf "http://127.0.0.1:$port/json/version" >/dev/null; do sleep 0.5; done
  VCW_CDP="http://127.0.0.1:$port" python3 tools/sweep/p$i.py &   # next lane now
done
```

Six simultaneous Chrome initialisations starved one lane into a multi-minute
stall before it emitted a line; the same six launched in sequence run
concurrently to the end. Treat an empty log as a startup failure rather than a
slow lane — a lane that never opened its tab writes nothing and is
indistinguishable from one still working.

**Report every lane as it lands, not when the last one ends.** A summary that
only appears at the end leaves the five finished lanes looking unfinished. And
**a lane that changed the code invalidates the whole run** — once a fix lands,
the previous 6-lane result describes a tree that no longer exists and every
lane must be re-run, not just the one covering the change.

**Splitting a single script is a rewrite, so keep the shared half shared.**
Emitting each group as a self-contained copy works exactly once and then
becomes unmaintainable — six 27 kB files where one 600-line library plus six
70-line entry points would do. After verifying the extracted version still
runs, collapse the duplicated preamble into an importable module and re-verify;
a harness that was tested only in its duplicated form has not been tested in
the form you are shipping.

## When a headless page runs at 1-5 fps

Software-rasterized WebGL under `--headless=new` is the normal case, and it is
frequently 60-400x slower than the same page in a real browser. When a harness
that polls a game loop becomes 30-minute-per-run slow, the throttle is the
first suspect — and the whole point of removing it is that it is almost never
the application's `time_scale`.

Read the browser's own log before guessing at flags. A line like
`GL Driver Message (...): GPU stall due to ReadPixels` repeated every frame
identifies the cost: the app is synchronously reading back the drawing buffer
once per frame, and the stall dominates. That is fixed by a launch flag, not
by editing the application.

Three launch flags together are what actually restore 60 Hz, and the middle one
is the one that matters:

```bash
"$CHROME" --headless=new --no-sandbox --disable-gpu \
  --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \
  --disable-accelerated-2d-canvas \        # <- the fix; 2D canvas hits a
                                           #    slow path that stalls on
                                           #    readback under SwiftShader
  --remote-debugging-port=9223 --remote-allow-origins='*' \
  --disable-background-timer-throttling --disable-renderer-backgrounding \
  --user-data-dir=/tmp/cdp/profile --hide-scrollbars --window-size=1280,800 \
  about:blank
```

`--remote-allow-origins='*'` is not optional on recent Chrome: without it the
`/json/version` endpoint can answer while `/json/list` and `/json/new` return
empty, which looks exactly like a crashed browser.

### Never change two things at once when hunting a performance cause

The most expensive mistake available here is bundling a fix with an
experiment. Adding `--disable-frame-rate-limit` *and* keeping an application
time-scale multiplier produced a 403 fps reading that was pure spinning — no
vsync, no work done — and it read as a solved problem. Shrinking the canvas to
1x1 in a second attempt dropped it to 0.0 fps, which was reported as "the
approach is broken" when it was neither of the two things measured.

Rule: **one variable per run, and a measurement that can distinguish "faster"
from "spinning".** Frame count alone is not a performance measurement — a
browser that never yields does not advance the simulation. Sample frames *and*
a value the app only changes by doing work (a position, a simulation tick
counter) across the same interval:

```python
f0 = await ev("String(__app.frames)"); p0 = (await st())["pos"]
await asyncio.sleep(2.0)
f1 = await ev("String(__app.frames)"); p1 = (await st())["pos"]
print(f"fps~{(float(f1)-float(f0))/2:.1f}  work_done={p1 != p0}")
```

A high fps with no work is the spinning case and is worth nothing.

**Corollary: once a real 60 Hz is achieved, delete every compensation for the
throttle.** A `time_scale` multiplier, a `step_until(distance)` wait, and
poll caps sized for 1 fps are all now wrong, and the multiplier is actively
harmful — at 8x a single 16 ms frame advances 8 s of simulation, which is 36 m
of travel at walking speed, enough to tunnel straight through a 0.2 m wall. The
tunneling reads as a collision bug and sends the search after geometry that is
fine. Distance-based waits become correct again only at 60 Hz, and a
fixed-poll-count wait is the unit that stays correct at both.

**`HeadlessExperimental.beginFrame` is the textbook answer and no longer
exists.** Driving frames manually is the right idea for decoupling simulation
time from render throughput, but the domain was removed in Chrome 154, and an
`except: return` around the call makes it fail silently. Verify the domain
exists before building a harness on it:

```python
r = await cmd("HeadlessExperimental.enable")
if "error" in r: ...   # -32601 "wasn't found" means the plan is dead
```

## One-shot recipes

### Screenshot a URL at iPhone resolution

Note: `Emulation.setDeviceMetricsOverride` resets on each `Page.navigate`
(see pitfalls), so apply the override AFTER navigating, not before.

```bash
"$CHROME" --headless=new --no-sandbox --disable-gpu \
  --remote-debugging-port=9222 --user-data-dir=/tmp/cdp \
  about:blank & sleep 2
PAGE_WS=$(curl -s http://127.0.0.1:9222/json | jq -r '.[]|select(.type=="page")|.webSocketDebuggerUrl')
python3 -c "
import asyncio, json, base64, os
os.environ['NO_PROXY']='localhost,127.0.0.1'
import websockets
async def m():
    async with websockets.connect('$PAGE_WS', max_size=8<<20) as ws:
        mid=0; p={}
        async def r():
            async for x in ws:
                m=json.loads(x)
                if 'id' in m: p[m['id']]=m
        asyncio.create_task(r())
        async def c(method, params=None):
            nonlocal mid; mid+=1
            await ws.send(json.dumps({'id':mid,'method':method,'params':params or {}}))
            while mid not in p: await asyncio.sleep(0.01)
            return p.pop(mid)
        await c('Page.enable')
        await c('Page.navigate',{'url':'https://example.com'})
        for _ in range(40):
            r=await c('Runtime.evaluate',{'expression':'document.readyState'})
            if r['result']['result']['value'] in ('interactive','complete'): break
            await asyncio.sleep(0.2)
        # Apply mobile override AFTER the page has loaded; pre-navigation
        # overrides get cleared by Page.navigate.
        await c('Emulation.setDeviceMetricsOverride',{'width':393,'height':852,'deviceScaleFactor':3,'mobile':True})
        s=await c('Page.captureScreenshot',{'format':'png'})
        open('/tmp/cdp/iphone.png','wb').write(base64.b64decode(s['result']['data']))
asyncio.run(m())
"
```

### Capture every console message on a page

```python
await call("Console.enable")
await call("Page.enable")
await call("Page.navigate", {"url": url})
await asyncio.sleep(2)
# events now contains "Console.messageAdded" entries; their payloads
# are sitting in raw frames the reader dropped. To capture them, change
# the reader to also append raw frames when method startswith "Console.".
```

### Stub a specific API endpoint

```python
await call("Network.enable")
await call("Network.setRequestInterception", {"patterns":[{"urlPattern":"*/api/users"}]})
# In reader: on Network.requestIntercepted, call Network.continueInterceptedRequest
# with a synthetic body.
```

## Verification checklist

- [ ] `curl -s http://127.0.0.1:9222/json/version` returns valid JSON
- [ ] `/json` lists at least one `type:page` target
- [ ] `Page.navigate` + readyState poll reaches `complete`
- [ ] Screenshot PNG file is non-zero, has `file`-confirmed dimensions
- [ ] `Runtime.evaluate` returns a `result.value` you expected
- [ ] Chrome process is killed at end of session

## Related

- `references/real-account-automation.md` — driving a logged-in account
  (social, SaaS, mail) through CDP: channel ranking, the read-only tab
  inventory, and the three gates before any write.
- `blocked-page-recovery` — what to do when the page itself 403s.
- `inspecting-hermes-desktop-dom` — CDP against Hermes's own Electron window.
- `node-inspect-debugger` — CDP against a Node.js process (`--inspect`).