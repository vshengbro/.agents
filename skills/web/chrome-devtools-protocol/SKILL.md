---
name: chrome-devtools-protocol
description: "Drive a Chromium browser with raw CDP from terminal/Python scripts. Use when the browser tool isn't enough: custom CDP domains, AX dumps, request interception, viewport emulation, or attaching to a port."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, cdp, websocket, headless-chrome, automation]
    related_skills: [blocked-page-recovery, computer-use]
---

# Chrome DevTools Protocol (raw CDP)

Speak CDP over a WebSocket to a Chromium-class browser from a terminal script — no Playwright, no project install. (`node --inspect` is a different surface.)

**Use when:** Page/DOM/Runtime/Network/Emulation/Console scripting, an AX dump, request interception, a fake viewport, pinned `:hover`, or driving Chromium from a kernel whose proxy covers everything except `localhost`.
**Not for:** a screenshot or page text (`browser_exec`, `web_extract`) or anything a Playwright one-liner covers. Signed-in browsing goes through `browser_exec`; writes into a real account need `references/real-account-automation.md`.
## Index

§1 — Baseline, launch, drive · §2 — Verify before claiming done · §3 — Tear down (per target, by exact id)


## Resource lifecycle gate (mandatory — read before launching)

A CDP run is finished when every browser resource it created is gone, on success **and** on failure, timeout, Ctrl-C or cancellation. Full policy: [`agent-skills-source-sync`](../../agent-skills-source-sync/SKILL.md#临时验证资源生命周期硬规则-3-细则). Condensed:

- **Baseline first:** `pgrep -fl 'remote-debugging-port'` and `lsof -nP -iTCP -sTCP:LISTEN | grep -E ':92[0-9][0-9]'`. Those PIDs and ports are not yours.
- **Register at launch:** record PID / port / profile / targetId as you create them and register teardown immediately (`finally`, context manager, `trap`) — the failure path needs those handles before anything else has run.
- **Tear down by exact id, then read back:** `Target.closeTarget` (browser socket) or `/json/close/<id>` per recorded targetId; read `/json/list` back **while the browser is alive** and assert each owned id is absent — a matching count is not proof.
- **Borrowed vs owned:** disconnect a browser you did not launch; `Browser.close` on someone else's Chrome closes their window. Never `pkill` / `killall` / `killall chrome` — SIGTERM the exact recorded PID (check command + start time first, to dodge PID reuse), bounded wait, SIGKILL only that PID; an owned PID's children are owned too.
- **Done means ports free relative to baseline** and the user's open browser still running with its tabs. Only an explicit user request to keep something overrides teardown.

## 1 — Baseline, launch, drive

Set `$CHROME` to the actual executable reported by `agent-browser doctor`; reuse this task's existing instance before launching another. Record its PID, start time and child-process identities. Never attach to an unrelated debug port.

```bash
pgrep -fl 'remote-debugging-port'; lsof -nP -iTCP -sTCP:LISTEN | grep -E ':92[0-9][0-9]'   # baseline
agent-browser doctor                                     # is Chrome for Testing there?
SCRATCH="$HOME/.hermes/cache/scratch"; PROFILE="$SCRATCH/cdp-profile-$$"; PORT=9278
mkdir -p "$PROFILE"; : "${CHROME:?set the verified Chrome executable first}"
"$CHROME" --headless=new --remote-debugging-port="$PORT" \
  --user-data-dir="$PROFILE" --hide-scrollbars --window-size=1280,800 about:blank > "$PROFILE/chrome.log" 2>&1 &
echo $! > "$PROFILE/chrome.pid"                # the ONLY pid you may kill later
curl -s "http://127.0.0.1:$PORT/json/version"            # bound, not crashed
```

Register failure cleanup before waiting for readiness; the example is the launch step, not a complete lifecycle script. Read `/json/list` and record the exact owned targetId and its socket URL. Use the browser-level socket for target-management calls. Use `terminal(background=true)` when required by the runner.

Try the bundled driver before hand-rolling a client — it does the whole handshake for one-shot work (needs `websockets`; flags `--port`, `--ws` (explicit socket, skips discovery), `--url`, `--js`, `--screenshot`, `--iphone`, `--wait`):

```bash
python3 scripts/cdp_eval.py --ws "$OWNED_WS" --url https://example.com --js "document.title" --screenshot "$SCRATCH/shot.png" --iphone
```

Set `$OWNED_WS` from that recorded target, never the first page in a borrowed instance. `--port` discovery selects the first page and is safe only in your isolated single-page instance. The helper never creates/closes tabs, and can print CDP errors with exit 0: inspect every `error`/`exception`, then verify rendered content. For localhost proxy trouble, use `NO_PROXY=localhost,127.0.0.1` and the helper's proxy-free discovery opener; diagnose the actual WebSocket client's proxy behavior separately.

## Domains worth knowing

| Domain | Method | Does |
|---|---|---|
| `Page` | `enable` / `navigate` / `captureScreenshot` | navigation and base64 PNG |
| `Runtime` | `evaluate {"expression","returnByValue":true}` / `callFunctionOn` | JSON-able value back; call on an `objectId` |
| `DOM` | `getDocument` → `querySelector` → `getOuterHTML`; `querySelectorAll` | inspect exact matched nodes; distinguish nodeId and backendNodeId |
| `Network` | `enable` → `requestWillBeSent`/`responseReceived`/`loadingFinished`; `setRequestInterception` | traffic; stub / mock |
| `Emulation` | `setDeviceMetricsOverride` / `setUserAgentOverride` | fake iPhone viewport; UA (per target) |
| `Console` / `Performance` | `enable` → `messageAdded` / `getMetrics` | console payloads (keep raw frames); DOM/frame/task counts |
| `Target` | `createTarget` / `closeTarget` via browser socket | open/close an owned tab |
| `Accessibility` | `getFullAXTree` | role/name per node for a11y-driven automation |
| `CSS` | `enable` + `forcePseudoState` | pin `:hover`/`:focus`/`:active` for a screenshot |

`Page.navigate` returns immediately — there is no CDP `waitForLoad`. Subscribe to `Page.loadEventFired` or poll `document.readyState`. **Gate on rendered content, not the URL:** a changed URL with nothing rendered is a load failure, and a `None` read after it is a load-state failure, never "not found".

## 2 — Verify before claiming done

- `Runtime.evaluate` returning `undefined` ≠ failure — print `result.exceptionDetails`; a screenshot of `about:blank` is a valid empty PNG, so check bytes *and* dimensions (`file shot.png`); `Network.loadingFinished` fires on error responses too, so check `responseReceived.response.status`.
- **Select the recorded targetId**, then confirm URL and content; an earlier tab or identical URL is not proof of ownership. A failed socket needs transport/target diagnosis, not unlimited extra tabs or browser relaunches.
- **Verify loaded build identity**, using actual asset hashes or a build marker. A cache-busted/cache-cleared check tests only that path; check the user's ordinary URL as well before claiming CDN delivery.
- Software-rendering flags, throttled headless loops, WebGL readback: `references/headless-performance.md`.

## Pitfalls

1. **`browser_exec` says Chromium is missing but `agent-browser install` says "already installed"** — its cache lookup is independent of `~/.agent-browser/browsers/`. Drop to the CLI instead of retrying: one scoped session (`agent-browser session id --scope worktree --prefix <task>`) then `open` / `snapshot` / `eval` / `mouse` / `click` / `close` — the scoped name is the isolation and `close` tears down only that session.
2. **`:hover` invisible when a token equals the background** — a `rgba(0, 0, 0, 0)` where you expected a fill means the token, not the page. Use `CSS.forcePseudoState` with `nodeIds` from `DOM.querySelectorAll` (not `backendNodeId`); `Runtime.evaluate`-dispatched `mouseover` never triggers CSS `:hover` headless — the layout cursor stays at (0,0).
3. **Port taken** — identify its owner; reuse only this task's authorized instance or choose a free port. A new profile/port is not a substitute for cleanup, nor authority to restart another task's process.
4. **Protocol mechanics that look like a dead browser:** `/json/new` needs `PUT` (GET → 405) and returns the new target `id` — record it; a socket carrying a devtools `Origin` is rejected unless the browser was launched with `--remote-allow-origins='*'` (handshake 403s while `/json/version` answers).
5. **A client returning `None` on every failure turns conclusions into guesses.** Control frames carry no JSON — surface `__timeout`/`__js_error` markers. And `JSON.stringify(...)` returns a *string*: a caller reading fields sees every one absent, so a working interaction reports as a refusal.
6. **Suspected editor failure** — identify the real editable node and read back its current value before retrying; a display decoy's stale text is not the editor's state. Detailed account/editor safeguards are in `references/real-account-automation.md`.

## 3 — Tear down (per target, by exact id)

1. Close every recorded targetId, close the page sockets, read `/json/list` back and assert each owned id is absent. Pre-existing tabs stay.
2. Borrowed instance → disconnect and stop; its PID, tabs and port are expected to remain.
3. Instance you launched → `Browser.close` on the browser socket, bounded wait (≤10 s) for the recorded PID **and its children**, identity-checked before any signal. A dead parent alone is not proof renderers exited.
4. Only after owned PIDs are gone and listeners are free versus baseline: remove this task's temp profile. Never remove a borrowed or shared profile.

## Logged-in browsers

Signed-in browsing goes through `browser_exec`, not `computer_use`. In Hermes the supported real-profile route is the `browser` toolset with consent (`hermes config set browser.use_real_profile true`): it snapshots the default-Chromium profile into a Hermes-owned copy and launches the real system browser on it — it does **not** attach to the user's daily Chrome window.

Attaching to a remote-debugging endpoint you did not launch is not automatically authorised: reuse one only when it is this task's own instance or a tool-owned browser for this task, stay inside your own targets, and never close another lane's tabs. A profile that will not open can be a TCC privacy denial or a real lock — probe before telling the user to quit their browser: `python3 scripts/diagnose_chrome_profile_access.py [chrome|chromium|brave|edge]` → `0` readable/absent, `1` TCC privacy grant, `2` real lock. The grant belongs to the *ancestor* app the probe names, and `tccutil` can only reset entries, never add one — remediation is a user action. Depth: `references/profile-access-and-tcc.md`.

## Related

`references/headless-performance.md` (throttled loops, polling predicates, SwiftShader flags) · `references/real-account-automation.md` (logged-in accounts, gates before any write) · `scripts/cdp_eval.py` (step 1 driver) · `scripts/diagnose_chrome_profile_access.py` (TCC vs lock) · `blocked-page-recovery` (the page itself 403s) · `computer-use` (native desktop GUI, background-first).
