---
name: browser-app-self-verification
description: "Use when verifying a browser app actually runs and works."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, verification, canvas, webgl, game, screenshot, debugging, headless]
    related_skills: [systematic-debugging, chrome-devtools-protocol, vision-analysis, dogfood]
---

# Browser App Self-Verification

## Overview

Building an interactive browser app is not done when the file is written — it is
done when a real browser has run it, its internal state has been read back, and
a screenshot has been checked. This skill is the procedure for that loop, plus
the specific ways it goes wrong.

The failure mode this exists to prevent: **declaring a browser app "working" on
the strength of code that reads correctly.** In a voxel game the code looked
perfect and the player fell through the world, because a collision predicate
returned `false` for every block. Only executing it found that.

## When to Use

Building or changing anything that must be *proven* by running in a real
browser rather than by reading the code: canvas/WebGL apps, games, interactive
demos, single-page tools. Also use it when such an app is being shipped to a
public URL — the deployed origin has its own failure modes, and the local proof
does not transfer (see steps 8-9 and
`references/static-site-single-origin-deploy.md`).

## Core principle

**Instrument, assert, then look.** A screenshot proves pixels exist; it does not
prove state. Read the app's internal state back through `Runtime.evaluate` and
assert on it — that is the primary evidence. Vision is the secondary check that
the pixels mean what you think they mean.

## Procedure

### 1. Make the app inspectable from the start

Expose a handle and a readiness flag on `window` before you need them. Without
these, every later check degenerates into sleeping and hoping.

```js
window.__app = game;
game.ready = false;                 // flipped true at the end of init
```

Prefer a flag the app itself controls over inferring readiness from the DOM
(a loader's `gone` class is a decent fallback when you cannot touch the source).

### 2. Serve it with caching disabled

A plain static file server answers conditional GETs with `304 Not Modified`, so
an edited JS file keeps executing its **previous** version. `python3 -m
http.server` has no no-cache switch; write a ~15-line handler:

```python
class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

ThreadingHTTPServer(('127.0.0.1', port), NoCacheHandler).serve_forever()
```

Vendor any third-party library into a local `lib/` so the app runs with no
network at test time — a CDN hiccup then can't masquerade as an app bug.

### 3. Bring the tab to the front, then poll readiness

```python
goto_url("http://127.0.0.1:PORT/index.html")
wait_for_load()
cdp("Page.bringToFront")            # BEFORE polling — see pitfalls
for _ in range(25):
    time.sleep(2)
    if js("window.__app && window.__app.ready"): break
```

A backgrounded tab throttles `requestAnimationFrame` to near zero. Any app
whose init awaits rAF (progress bars, chunked loaders) then never finishes and
`ready` stays false forever. `Page.bringToFront` first, and only conclude "the
app is broken" after it has been issued.

On the app side, never gate startup on rAF alone — race it against a timer so a
throttled tab cannot deadlock it:

```js
function frame() {
  return new Promise(res => {
    let done = false;
    const fin = () => { if (!done) { done = true; res(); } };
    requestAnimationFrame(fin);
    setTimeout(fin, 32);
  });
}
```

Measure the throttle before compensating for it: read
`document.visibilityState` and run a one-second rAF counter
(`window.__n=0;(function f(){__n++;requestAnimationFrame(f)})()`). In a
hidden tab the counter stays at **zero**, and `Page.bringToFront` does not
always change that in a headless session. When rAF provably does not run,
do not gate verification on rAF-driven behaviour at all — drive state
directly (set `scrollTop`, call the handler) and assert the DOM that
results.

### 3b. Control-run the harness on a known-good build before trusting its verdict

A harness that has never produced a pass cannot distinguish "the app is broken"
from "my harness is broken." Build the **pre-change revision** (or any revision
known to work), serve it on a second port, and load both. Same server script,
same browser session, same assertions.

```bash
# control build, on its own port, from a second checkout — never by reverting
# the working tree (see the destructive-git pitfall in systematic-debugging)
git worktree add /tmp/base HEAD
cd /tmp/base && <build> && wasm-bindgen --target web --out-dir /tmp/base/www/pkg --out-name app target/wasm32-unknown-unknown/release/*.wasm
# then: new build on :8931, control build on :8932, assert both
```

The control settles three things at once: the build pipeline is sound, the
served bytes are the ones on disk, and any difference in the verdict is
attributable to the code change rather than to the harness. Without it,
"the app rendered nothing" is ambiguous and the debugging effort goes into the
wrong half of the system.

**Byte-compare what you serve against what you built** — a stale artifact is
indistinguishable from a regression:

```bash
echo "served: $(curl -s http://127.0.0.1:8931/pkg/app_bg.wasm | wc -c)  disk: $(wc -c < www/pkg/app_bg.wasm) bytes"
```

### 4. Assert internal state, not vibes

Drive the app's own methods and read the resulting data back. This is the tight
feedback loop that makes a fix provable:

```js
JSON.stringify({
  pos: [p.pos.x.toFixed(1), p.pos.y.toFixed(1), p.pos.z.toFixed(1)],
  onGround: p.onGround,          // the boolean the bug was about
  health: p.health, chunks: g.chunkMeshes.size,
})
```

Test the specific value the bug touched, **and** its non-triggering counterpart.
A physics fix that reports "fall damage now works" is unproven until a 2-block
drop and a jump both still report zero damage.

Dispatch real input events where it matters (`Input.dispatchKeyEvent`,
`Input.dispatchMouseEvent`, synthetic `WheelEvent`) and read the state delta
afterwards — calling the handler directly proves less than the full event path.
**Match the event to the code path, though: a trigger bound to a canvas
`mousedown` is untouched by a synthetic key code**, so the action reads
`false` forever and every shot "fired" with no effect.

**An anomalous reading is a claim about the channel before it is a claim about
the app.** Before filing a defect from one odd number, prove the number could
have meant something: that the field you read is written on every frame and not
throttled, that the value you set reaches the code that consumes it, and that
the field is *read* anywhere at all. A field assigned in three places and read
in none is a write-only debug field — injecting a value for it changes
nothing, and any "the effect is broken" verdict drawn from it is fabricated.
The same check applies to the precondition: "enter the vehicle" fails for an
actor 12 m from the nearest vehicle, and that is the feature working.

   A claim about generated geometry is proven by a **unit test that builds
   around a far coordinate and asserts its extent**, not by a browser walk. The
   browser bonus is that it shows the *streaming path* fires — a different
   claim. When the unit test passes and the walk stalls, report both: the
   walk's failure is a harness limitation, not evidence against the generator.

   **Separate the three claims a world-streaming feature makes, and test each
   on its own.** They fail independently and a single number hides which:

   | Claim | What proves it |
   |---|---|
   | The *generator* is position-independent | unit test building geometry around a far coordinate, asserting bounded extent |
   | The *generator* does not leak the origin | same test, but assert every vertex is within the requested block — a whole-axis min that matches the other axis's origin is the signature of one axis's value shadowing the other's |
   | The *streaming path* fires at runtime | teleport, then read back the value the app derives (the new generation centre), not the one you asked for |

   The third is the one a browser walk is actually for, and the reason it must
   read a derived value: the centre is written by the rebuild itself, on a
   tile-aligned lattice, so "centre is now a multiple of the pitch" cannot be
   true until the rebuild ran.

   **A scene that swaps only its terrain is not a streamed world.** If the
   ground and water regenerate around the player but buildings, props and
   colliders were placed once at spawn, the player at 600 m sees fresh ground
   under the original skyline. A cheap tell: the triangle count is *byte-identical*
   at every far position. To fix it, static content must be re-placed with the
   terrain — and because the batch table is append-only, record the static
   section's length and truncate-then-rebuild it, so the dynamic tail
   (player skeleton, vehicles, pickups) keeps its indices:

   ```rust
   // truncate to the recorded static length, re-place, dynamic tail untouched
   scene.batches.truncate(static_batch_count);
   ```

   **Debug seams should publish the coordinates, not let the script re-derive
   them.** When a script hard-codes a literal copied from the source (a door
   at `z = 6.4`), an interior-wall tweak silently invalidates the test and the
   failure reads as "navigation is broken". Expose the value the app computes —
   door approach point, walk route waypoints, spawn centre — and have the
   script read it. One number in the source beats two in the source and the
   script.

   **Publish the waypoint route the app's own end-to-end test uses.** For
   anything position-continuous (stairs, ramps, narrow gaps), teleporting to
   each waypoint cannot work: the behaviour under test is the *integration*
   across consecutive positions, and a jump onto the top landing just falls
   back to the ground. If the engine already has a verified route for its own
   test, expose that same route and have the harness walk the legs — every
   metre between waypoints still goes through the real movement and vertical
   integration.

   **Derive the route from the rotation once, and assert its geometry.**
   A waypoint authored by hand against a rotating asset is a guess with a
   long feedback loop; inverting the transform makes it arithmetic. Two bug
   classes then have cheap machine checks — adjacent waypoints further apart
   than one body width (two points differing only in a local axis that maps
   to a constant world axis rotate onto the *same* position and the route
   spins in place), and every leg moving on exactly one axis (a diagonal
   inside a walled interior always jams, and a "further in" edit that crosses
   a wall at that very local coordinate is invisible until it does). An
   end-to-end test written entirely in local coordinates sees neither, because
   it never touches the transform — assert after the transform, ideally via a
   helper that inverts it rather than by re-deriving the trig.

   **Log every sub-sample of a leg, not just its endpoints.** Endpoints alone
   cannot separate "cannot get there" from "overshoots and is thrown back" —
   and that second reading points at a specific obstacle, so it is the
   diagnostic that ends the search. Relatedly, **an endpoint that repeats
   across several time scales is a fixed face, not a tuning problem**: vary
   the scale once before touching arrival radii, and if the endpoint does not
   move, no threshold change will reach it.

   **When the harness cannot steer, change what the script is given, not what
   it fakes.** Movement in these engines is usually camera-relative, so blind
   key-holding walks into walls, and if synthetic mouse events cannot reach the
   drag handler the camera cannot be aimed at all. Expose a
   world-direction walk intent alongside the position seam: the script then
   commands "head this way in world coordinates" and the movement integration
   underneath is unchanged. A synthetic drag that deadlocks the canvas is worse
   than useless — it leaves the page in a held-button state and the run stops
   advancing with no error to explain it.

   **"The actor did not move" is a three-way ambiguity — read velocity and
   intent, not just position.** A headless tab can hold
   `requestAnimationFrame` at a few fps and most engines clamp the per-frame
   delta on top of that, so the simulation runs at a fraction of wall-clock
   speed: a correct `vel = [2.8, 0]` with 0.19 m of displacement over 1.5 s is
   the signature of a slow clock, not of broken movement code. The same empty
   reading also means "the actor is in a vehicle, where the intent is throttle"
   or "the intent never reached the sim". Publish velocity and the intent
   beside position so one probe separates all three, and **poll on measured
   displacement rather than sleeping** — a wall-clock wait is wrong by exactly
   the throttle factor, and the factor is not guessable. A harness field you
   added to the app but not to its projection map reads `None` every time,
   which looks identical to a field the app never sets.

   **Establish the real frame rate before compensating for a slow clock.** The
   throttle is usually a broken browser session — a dead tab, a readback stall,
   a missing launch flag — and it is removable, at which point every
   compensation for it is wrong and a time-scale multiplier actively tunnels the
   agent through walls. Measure frames *and* whether the app advanced, since a
   browser that spins without yielding is not a fast browser.

   **Two different starts landing on the same coordinate proves a destination,
   not a collision.** Collision resolution never converges two unrelated starts
   onto one point to within centimetres; a spawn, respawn, hospital or
   checkpoint anchor does, every time. When a position jump repeats an endpoint,
   stop reading it as navigation and go look for a teleport destination in the
   app — and note that restoring health does not cancel a respawn that has
   already latched, so invulnerability must clear the pending timer, not just
   the gauge.

   **A browser probe and the unit tests disagreeing about geometry means the
   tests are reading one side of the seam.** When a doorway, walkable region or
   interior route is declared in both the collision world and the floor world,
   tests that import both from the same side stay self-consistent while the
   browser — the only side that sees both — disagrees. Derive the value once,
   make the collision derive from it, and pin it with a test that inverts the
   transform for *every* instance.

   The `step_until` polling recipe, the arrival-radius vs recovery-threshold
   ratio trap, bidirectional bounded slide, the "fix the browser before you
   compensate for it in the app" rule, deriving and asserting route geometry,
   the fixed-face-vs-overshoot time-scale test, scoped recovery, the
   before-you-need-it invulnerability ordering, and the stale-artifact check
   after an incremental build are in
   `references/headless-sim-time-and-movement-probes.md`.

   **A slow harness is usually protocol cost, not simulation cost.** Measure
   one `Runtime.evaluate` before diagnosing anything: on a busy page it is
   ~670 ms, so a loop spending five round trips per stride pays 3.4 s of
   protocol to advance 0.7 m. Batch the aim/step/sample loop into one async
   IIFE that returns a sample array, keep every decision (arrival, stall
   counting, recovery) in Python, and pass thresholds in so each predicate
   keeps one owner. Then count diagnostic tokens before and after — a token
   that drops to zero is a branch that stopped running, which no pass/fail
   verdict will show you. The round-trip budget, the silent traps
   (`JSON.stringify` on a promise, one `rAF` not being one frame, a
   threshold re-tuned for a different sample rate), the offline node-stub
   verification, and shared-machine baseline hygiene are in
   `references/cdp-round-trip-cost.md`.

5. **Screenshot, and treat vision as a hypothesis.**

   `capture_screenshot()` then `vision_analyze`. When vision reports a defect,
   **verify it against ground truth before acting on it** — read the DOM text, or
   count the offending structures in the page's data. Vision models both invent
   defects that aren't there and describe real ones imprecisely; treat every
   finding as a claim to be checked, and say so in your report when you disprove one.

   The same discipline applies to **pixel-level measurements** taken from the
   screenshot itself. Scanning the raster for "the first column containing ink"
   to assert an alignment will report false misalignment, because ink extent is
   not the layout box:

   | What you scanned | What it actually measures |
   |---|---|
   | the active/highlighted nav item | its **full-bleed background**, which touches the edge by design |
   | a glyph (`✕`, `☰`) inside a padded button | the **glyph advance width**, narrower than and centred in its box |
   | uppercase label text | the first letter's **side bearing**, ~1px of built-in whitespace |

   For any alignment or spacing claim, assert on
   `getBoundingClientRect()` plus `getComputedStyle()` — the browser's own
   layout numbers — and assert on the *relationship* between elements (do these
   two insets match?) rather than on an absolute pixel value. Screenshots and
   vision remain the confirmation that the overall look is right; they are never
   the source of truth for a number.

   When a raster measurement contradicts a computed-style reading, **the
   computed style wins** — then go look for the real bug, which is usually in
   a sibling or pseudo-element that the raster pass never covered.

   **GPU canvases must be read inside `requestAnimationFrame`.** A WebGL/WebGPU
   context defaults to `preserveDrawingBuffer: false`, so once the frame is
   composited the drawing buffer is cleared: `readPixels` and `drawImage` then
   return all zeros and the canvas *looks* blank while rendering perfectly.
   Headless screenshots have the same blind spot — they capture the composited
   result, not the render target, so a GPU canvas photographs as empty.

   ```python
   js("new Promise(resolve => { requestAnimationFrame(() => {"
      " const c=document.getElementById('xxx-canvas');"
      " const gl=c.getContext('webgl2');"
      " const px=new Uint8Array(c.width*c.height*4);"
      " gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,px);"
      " resolve(JSON.stringify({nonBlack:countNonBlack(px)})); }); })")
   ```

   To prove a GPU path is *alive* without readback, instrument the prototype
   before switching to that view and count real calls — this beats both
   screenshot and readPixels:

   ```js
   const P = WebGL2RenderingContext.prototype;
   window.__draws = 0;
   for (const m of ['drawElements','drawArrays','drawElementsInstanced']) {
     const orig = P[m]; P[m] = function(...a){ window.__draws++; return orig.apply(this,a); };
   }
   ```

   A non-zero draw count at the expected frame rate is the evidence. When a
   zero-pixel reading contradicts a healthy draw count, **the read is the
   thing that is wrong** — re-take it inside rAF before reporting a regression.

### 6. Write a short README with the run command

State the exact command and URL, the controls, and what is deliberately not
implemented. A delivered app that the user cannot start is not delivered.

### 7. When the user says "let me see it", open their real browser

A screenshot is a *proof for you*, not a deliverable for them. When the ask means
"I want to look at it myself" — "open the browser first, I want to see the effect"
— the artifact to produce is a live window on the user's own screen. Not a PNG, and
not a description of a PNG.

```bash
open -a "Google Chrome" "http://127.0.0.1:PORT/"   # macOS; name the user's real browser
```

`open` returns immediately and reports success whether or not the page booted, so
confirm it separately — read the **window title back through the accessibility tree**,
no headless browser and no screenshot round trip:

```
computer_use list_windows     # → pid, window_id, title
```

When the app puts runtime status in the document title, that one call is stronger
evidence than a screenshot: a title reading `NEON BAY · third-person · ON FOOT`
proves the module booted, assets parsed, and the game loop is ticking — three
assertions in one round trip. Otherwise, escalate to `computer_use capture` and
read the in-page HUD.

Run the staleness pre-flight in pitfall 1 **before** opening anything. A user
watching a stale build is worse than no build, because they end up judging the fix
you *meant* to ship.

**Disclose known defects in the same message as the "look at this".** Silently
handing over a partially finished artifact reads as a finished deliverable. If the
camera framing is wrong, a color pass hasn't landed, or a subsystem is still a
stub, spend one line on it and name the control that works around it — then let
them look. Their verdict is about what they can see, so tell them what that is.

### 8. When the request implies shipping, finish the loop yourself

If the user asked for the app *and* named a delivery target ("deploy it to
X"), treat build → verify → deploy as one turn: do not stop after local
verification to ask where it should go, and do not report a URL you have not
loaded. Verify the **deployed** URL the same way you verified the local one —
app state read back through the console, one real input event, one screenshot.
The local proof does not transfer: a broken rewrite path or a wrong reference
only shows up on the live origin.

Autonomy carries through to failures: fix and re-verify rather than handing
back a partially working build, and state plainly what is not implemented
(save/load, mobs, crafting) instead of letting the user discover it.

### 9. Deploy it with `scripts/deploy-site.js`

Publishing to a per-file CDN is a distinct step, not a formality: each file
gets its own URL on a hashed path, so every relative reference in the site
dies unless it is rewritten to an absolute one. References can only be rewritten
after their targets have URLs, which fixes the order — leaves first, entry last.

```bash
node <skill_dir>/scripts/deploy-site.js /path/to/site
```

It scans the graph (including ES-module `importmap` specifiers, which is the
one edge a naive scanner misses and the usual cause of a blank deployed page),
sorts topologically, rewrites each file into a temp dir, uploads, and prints
`{ entry_url, files }`. Do not hand-roll this loop. Full reasoning and the
remaining traps are in
`references/static-site-single-origin-deploy.md`.

**A wasm artifact URL that never changes is the stale-artifact trap's worst
   case, and a query string will not catch it.** `pkg/app_bg.wasm` has the same
   URL before and after every rebuild, so appending `?cb=<ts>` to *`index.html`*
   busts only the HTML — the wasm still comes from the HTTP cache and the page
   silently runs the previous build. The symptom is a fix that provably changed
   nothing, which reads as "the fix is wrong" and sends you back to the source.

   Disable the cache **and re-navigate**, because the first load has already
   been served before the override takes effect:

   ```python
   await tab.call("Network.enable")
   await tab.call("Network.setCacheDisabled", {"cacheDisabled": True})
   await tab.nav(url)          # the reload is the part that matters
   ```

   Confirm which build you are actually running before re-deriving anything —
   grep the artifact for a string only the new build emits:

   ```bash
   strings www/pkg/app_bg.wasm | grep -c 'the-new-literal'
   ```

   Non-zero proves the disk artifact is current; zero means the rebuild did not
   take, which is a different bug from the one you are chasing. The
   served-vs-disk byte compare in pitfall 1 does **not** detect this: both sides
   are the stale-but-identical cached copy.
   ```bash
   echo "served: $(curl -s http://127.0.0.1:PORT/app.js | wc -c)  disk: $(wc -c < app.js) bytes"
   ```
   In-page: `await fetch(url + '?x=' + Date.now())` then substring-match for the
   new code. If it's absent at runtime, every test result since is invalid.

   **Compare the name, not just the size.** A bundler names its output after
   the crate/package, so a page importing the wrong stem keeps loading an old
   file forever while a second, correct file sits next to it. A byte-compare
   against the *intended* path then passes or fails for the wrong reason. After
   every WASM/Rust change, confirm the import in the page and the artifact on
   disk are the same stem, and delete the orphaned one so it cannot be picked
   up again:
   ```bash
   ls -la <out_dir>/                 # exactly one set of artifacts, fresh mtimes
   grep -n "<out_dir>/" index.html   # import stem == artifact stem
   ```
   The tell-tale sign that you have this bug: a source fix changes nothing in
   the browser **down to the same `file:line:col` in any stack trace** — the
   artifact is provably not yours, so suspect the environment before you touch
   the code again.

2. **Fixed `sleep` silently under-waits** on a slow machine or throttled tab.
   Poll an app-owned readiness flag instead.

3. **`js()` takes no `timeout_s` argument** — it is a top-level parameter of
   `browser_exec`. Passing it to `js()` is a `TypeError` that reads like a
   mysterious harness failure.

4. **Multi-line JS strings in the Python wrapper break.** A triple-quoted
   `js("... \n ...")` with a raw newline is a Python `SyntaxError`. Put the JS
   on one line, or keep the newlines inside a proper `"""` block.

5. **A failed `js()` call may mean the tab was hijacked or reloaded**, not that
   your code is wrong. Check `location.href` and `typeof window.__app` before
   debugging anything else — a tab that silently moved to an unrelated page will
   waste several rounds. Give the page its own named browser session for
   long-running verification.

6. **Heavy in-page loops can exceed the IPC timeout and reset the page.** A
   probe that walks every block of every loaded chunk may take the whole session
   with it. Scope probes to a few chunks and keep per-call work small.

7. **Verify the build is registered correctly before trusting a census.** A
   "generated" chunk flag set without populating the blocks makes every
   downstream check (height, collision, rendering) read a void. Assert on
   non-zero block counts, not on flags.

8. **A lookup returning `undefined` mid-expression** is a wrong-receiver bug in
   your test, not the app: e.g. calling a UI method on the model object instead
   of the controller. Read the actual class members before asserting.

9. **An empty mount is silent — assert on rendered content, not on absence of
   errors.** The shape: the root element exists and the framework's entry point
   ran, but it produced zero children, zero body text, and **no console output
   at all** — no exception, no unhandled rejection, no driver diagnostic. A
   green "no errors" capture here is not weak evidence, it is *no* evidence,
   because the failure produced nothing to log.

   The trap is concluding "the page is fine, the feature under test is just
   absent" and then verifying a deeper route. Check the *shallowest* possible
   state first:

   ```js
   document.querySelector('#app').children.length   // must be >= 1
   document.body.innerText.trim().length            // must be > 0
   ```

   A healthy page mounts one child and yields hundreds of characters of text
   within a few seconds. Treat `children === 0` as a hard failure regardless of
   what the console said, and **never** let a source-level gate stand in for
   this check: a full test suite, a clean clippy run, and a passing lint hook
   have all coexisted with a completely blank app. Those gates read the source;
   only a load reads the artifact.

10. **Deleting files is a refactor, so a file-scoped diff gate is blind to
    where the content went.** When a large file is split across several new
    paths, each new path has no counterpart in the base revision, so every
    pre-existing violation inside it is reported as newly introduced — the gate
    can report thousands of findings for a change that introduced none. Before
    treating a large "new violations" count as a finding, establish the real
    delta: total the same check over the whole tree in both revisions.

    ```bash
    # both revisions, same verifier, whole tree
    <verifier> /tmp/base            # pre-change total
    <verifier> "$PWD"               # post-change total
    ```

    A per-file gate is normally the stronger instrument, but not when the files
    themselves moved.

11. **Piled-up tabs kill synthetic input while everything else still works.**
    `Input.dispatchTouchEvent`, `Input.dispatchMouseEvent` and click helpers
    begin timing out against the daemon, yet `Runtime.evaluate`, `Emulation.*`
    and rendering stay healthy — which reads like "this harness cannot inject
    events" and invites hand-rolled `dispatchEvent` workarounds that test less
    than the real input path. The cause is queued page targets, not a missing
    feature: parallel workers each open tabs and none close them.

    ```python
    pages = [t for t in cdp("Target.getTargets")["targetInfos"]
             if t.get("type") == "page"]
    keep = next((t["targetId"] for t in pages if "<your route>" in t.get("url","")), None)
    for t in pages:
        if t["targetId"] != keep:
            cdp("Target.closeTarget", targetId=t["targetId"])
    ```

    Close the tabs you opened when you are done, and before reading state
    confirm you are looking at the document you think you are — otherwise you
    will happily report a previous run's leftover value as a fresh result.

12. **Headless viewport clips input coordinates.** The default headless
    viewport is far shorter than it is wide, so touch/mouse coordinates taken
    from an element that extends below the fold land off-screen and the handler
    never fires — the symptom is "the gesture does nothing", not an error.
    Take the target's real box with `getBoundingClientRect()` and derive points
    from that, keeping them inside the viewport.

13. **A readback boundary must enforce the *type*, not just the error
    sentinel.** The common shape is a helper that evaluates, stringifies, and
    returns `dict | None` — and whose only non-dict check is the sentinel the
    page raises on a caught throw. Every other non-dict then passes: a page
    expression that legitimately evaluates to an array or a scalar, or the
    CDP-level `description` string that `Runtime.evaluate` returns for an
    unserialisable result. Callers do `st.get("px")`, a truthiness guard like
    `if not st: continue` does **not** catch a non-empty string, and the crash
    surfaces two frames away in the movement code — so a page that failed to
    evaluate is reported as a movement bug. Enforce the type where the
    contract is declared, and use `isinstance` rather than truthiness at the
    use site so a future path that bypasses the boundary cannot defeat it:

    ```python
    # boundary: one owner for the "callers call .get() on this" contract
    if isinstance(out, dict) and "__appErr" in out:
        print(f"[page error] {out['__appErr']}"); return None
    return out if isinstance(out, dict) else None

    # use site
    st = await d.st()
    if not isinstance(st, dict):   # not: `if not st`
        continue
    ```

    The tell-tale is an `AttributeError` naming a *builtin* type
    (`'str' object has no attribute 'get'`) inside code that only ever
    expected your own structure: the frame that raised is not the frame at
    fault.

14. **The verification runner must execute the canonical source, and must
    outlive the browsers it starts.** Two failures with the same shape — a
    green-looking run that measured nothing.

    *Stale copies.* A runner that `cd`s into a scratch directory and invokes
    `./p1.py` there executes hand-copied duplicates, so edits to the tracked
    source under `tools/` have no effect and every log looks plausible. Run
    probes from the repo path and send only *logs* to scratch; if scratch
    copies exist, verify them with a byte compare before trusting a run.

    *Orphaned browsers.* Headless browsers started as children of the runner
    are killed when it exits — and a run that is interrupted, killed, or
    piped through a short-lived wrapper takes 5 of 6 instances with it. The
    survivors still answer `/json/version`, so a "port is open" pre-flight
    passes on a later run while the earlier half of the suite silently
    produced nothing. Hold the browsers in a separate long-lived process and
    have the runner connect to them.

    Both surface as a group reporting no output at all. **A group that wrote
    zero bytes is a runner problem, never an app result** — check the launch
    loop's own trace (`bash -x`) before touching the code under test.

15. **Every static check passes on a function you deleted but that is still
    called.** Removing a block by cutting from one anchor string to the next
    takes whatever sits between the anchors — including helpers that were
    never named in the request. The page then throws `X is not defined` on
    load, or on the first frame, and the three checks that "prove" the edit is
    clean all pass anyway:

    | check | why it passes |
    |---|---|
    | `node --check` / parser | only parses; a deleted function is a *runtime* failure |
    | DOM-target existence | misses it when the removed function never touches the DOM |
    | "no reference names a removed identifier" | misses it when the removed name is still *called* |

    The check that catches it is serving the directory and loading the page —
    and it is one call, not a new harness:

    ```python
    # served copy, not the working tree, and not the deployed origin
    goto_url("http://127.0.0.1:PORT/index.html"); wait_for_load()
    print(js("({ready: !!window.__app, err: window.__lastError || null,"
             " loading: document.getElementById('loading')?.textContent})"))
    ```

    Run it in the same pass as any static check, on a served copy of the output
    directory. Adding it to the pre-push loop is the whole fix.

    Related: **when deleting UI, delete the control's whole data path.** A
    checkbox that hides a part is a feature toggle keyed on a name pattern, and
    if the feature has since become real geometry rather than a separate
    object, the toggle now removes a piece of the body. Tearing out the HTML
    and leaving the classification branch is how a later edit re-introduces a
    dead `parts.grille` nobody remembers.

16. **“All my checks pass but the user says it is broken” means the checks
    cannot see it — go look, do not re-run them.** The disagreement
    is the finding. Restating a passing check adds nothing and costs a turn;
    opening the artifact is usually one call. Every time this bit, the local
    gates were green and the user was describing something structurally outside
    their reach: a model feature that was never cut, a control that throws on
    load, a face drawn on solid material. Corollary for the report: **when local
    evidence and user evidence conflict, say which one you checked and what
    you did about it** — silently believing either one is the failure.

    **Corollary — a gate that is permanently red hides the next bug.** A static
    gate left asserting a preset table that a later commit deliberately deleted
    had been failing for commits, and precisely *because* it was always red
    nobody ran it, so the two real defects underneath it shipped unnoticed. When
    a gate fails on something a product decision deliberately removed, fix the
    gate in the same commit that removed the feature. Then **mutation-test the
    repaired gate**: inject the exact bug it exists to catch and confirm it
    fails, then revert and confirm it passes. A check that has never been
    observed failing is not evidence of anything — and scanning *code* rather
    than whole-file text matters, or a comment describing the bug trips the
    gate while the bug is back.

17. **A harness that measured nothing must not print PASS — fail closed on
    three distinct conditions.** The empty-success shape: an in-page probe
    throws a `ReferenceError`, the results array comes back empty, and a
    `judge()` with no samples has nothing to complain about — so the run
    reports success. A check that reports success without measuring is worse
    than no check, because it gets believed. Three conditions, each fatal and
    each reported *separately* so the diagnosis is not lost:

    | condition | verdict |
    |---|---|
    | page/app never reached its own ready state | INCONCLUSIVE |
    | the in-page probe threw, or returned an `error` field | INCONCLUSIVE |
    | the probe ran but produced **0 samples** | INCONCLUSIVE |

    Distinguish these from a real `FAIL`. Return a non-zero exit for all three,
    and make the pass condition require a **minimum sample count** so a probe
    that silently matched nothing cannot be reported as a clean sweep.

    **Prefer a code coordinate you derived, never one a comment asserts.** A
    front-face direction written into a comment (`"+Y = FRONT"`) was backwards
    three separate times across a build's tooling, and every probe built on the
    comment measured the wrong face while returning plausible numbers. Read the
    convention from the artifact itself — the asset's own header, the exporter's
    transform, the page's live scene graph via `window.__` — and if the asset is
    compressed, read its *uncompressed* header chunk, which needs no decoder.

18. **"Pinned in place" is a per-stage attribution problem — record every
    stage's output, and query geometry from the stage that produced it.** A
    final position cannot say what stopped the actor: static resolution, an
    interior/vertical pass, and a dynamic-body pass each write the position,
    and a function whose name says "vertical" can still end in a whole-position
    write that overwrites the horizontal axes. Publish the position after each
    stage and let the probe diff them — the stage whose output first stops
    changing is the one to read. Two traps follow: a boolean "am I inside a
    collider" is `false` while the actor is *pressed against a face*, so
    report the **distance to the nearest surface** as well, not containment;
    and query that distance at the **stage that stopped it**, because a later
    stage can push the query point to the other side of the wall and make the
    neighbourhood come back empty — a self-contradictory report that sends the
    next round looking in the wrong place.

19. **A zero-pixel A/B is a claim about the toggle until you prove otherwise.**
    Before reading "the object never rasterised" out of a pixel diff, show that
    the debug toggle removes pixels at all — run it against something known to
    be on screen — and calibrate the whole-frame noise floor. If hiding the
    suspect and hiding *everything* change the same number of pixels, the
    experiment is void. When the floor is too high, **invert the A/B**: hide
    everything *except* the object, so its own box can only contain its own
    pixels, and zero becomes conclusive. Scope the diff to the box the engine
    reports, not a script constant, and report the three verdicts separately —
    absent from the instance table, present with a wrong transform, present but
    occluded — because they are three different bugs and `visible: true` from a
    projection box proves none of them. The attribution ladder, the
    CPU-asset-count vs GPU-table-length check for a silently-skipped draw, and
    the freeze/flip conditions are in
    `references/actor-visibility-attribution.md`; `scripts/pixel_ab.py` does
    the decode, the boxed diff, and the floor call in one command.

20. **Validate the instrument before you trust its verdict — a defect filed
    from an unvalidated reading costs a whole fix cycle.** The same root cause
    produced five phantom defects across one session, each with precise,
    plausible numbers, and each was retracted:

    | "defect" | why the reading was void |
    |---|---|
    | walk stutters every 3rd frame | sampled a debug object published on a `%3` throttle; frame indices had gaps |
    | sprint slower than walk | both modes clamped by a saturated frame-time cap, so the ratio is ~1.0 by construction |
    | cannot enter vehicle | actor was 12 m from the nearest vehicle; the near-check is the feature |
    | weapon does not fire | trigger bound to a canvas `mousedown`; the harness injected key codes |
    | mouse look is inverted | one snapshot's brightness centroid; a real projection probe gave the opposite sign |

    **The check is three questions, and it is cheap — run it before dispatching
    a fix, not after:**

    1. **Is the channel throttled?** Frame indices in the samples must be
       contiguous. Gaps mean skipped writes were read as unchanged values.
    2. **Does the field you set have any reader?** Grep it. Assigned-but-never-
       read is a write-only seam: no injected value can change behaviour.
    3. **Is the metric monotone by construction?** A centroid, bounding box, or
       whole-frame correlation is not — content entering and leaving the view
       moves it without any camera motion. Check the *analytic* magnitude
       before believing it: a 240 px drag at 0.006 rad/px is 1.44 rad ≈ 82°,
       which on a 1280 px viewport displaces content by ~1100 px, so a
       ±24 px reading is not a small translation of that rotation at all.

    **Then prefer a metric that is not content-dependent.** Project a world-
    anchored probe point through the app's *own* view-projection, and **first
    prove the projection copy is faithful by checking it reproduces a value
    the app itself reports** (its character box, say, digit for digit). This
    shares no code path with a pixel-diffing heuristic, so the two cannot
    agree while both being wrong the same way. Small single-step drags beat
    large ones: 60 px keeps the anchor trackable, 240 px rotates the scene
    past itself and voids the comparison.

    **A hand-transcribed envelope is a hypothesis, not ground truth.** Three
    runs of the same scenario disagreed because each derived its own shell
    bounds — and the "actor escaped the building" reading came from a
    threshold anchored to a waypoint rather than to the wall. Read the
    authoritative bounds out of the source, and when a geometric verdict
    matters, compute it twice by independent paths (manually transcribed vs
    measured) and require them to agree before reporting.

    **Hardcoded verdicts and stale allowlists are the same bug.** A worker
    that carried a `missing = ["Space", "KeyH", ...]` table, and another that
    hardcoded `Verdict(..., False, ...)`, both reported FAILs that the same
    file's own readings contradicted. A gate whose expected values were
    transcribed by hand will keep reporting a feature as missing after it is
    implemented; **make the gate read the implementation, and treat a
    FAIL whose note cites an absence as suspect when the feature plainly
    exists.**

21. **A verdict delivered to the user is a commitment to re-verify it.**
    A retracted finding must be retracted explicitly and in place — naming
    which part was wrong — not quietly reversed, and the retraction has to
    reach the user even if it was only ever said to a subagent. When a fix
    agent's own report contradicts your finding, the agent's measurement wins
    if it is better evidenced; re-run the decisive probe yourself before
    accepting either side, and say which source you checked.

22. **A "fix changed nothing" symptom means you are testing the previous
    build — disable the cache AND re-navigate, then prove which build ran
    before re-deriving anything.** Two failures with the same shape: a
    source edit applied cleanly, the build finished, the served bytes matched
    disk, and the browser behaved identically — which reads as "the fix is
    wrong" and sends you back into the code instead of the artifact.

    The mechanism: a wasm/JS artifact URL is **identical before and after a
    rebuild**, so a cache-busting query string on `index.html` busts only the
    HTML. The artifact still comes from the HTTP cache. And a cache override
    issued *after* the first navigation has no effect on that first load, so
    the override and the reload have to happen together:

    ```python
    await tab.call("Network.enable")
    await tab.call("Network.setCacheDisabled", {"cacheDisabled": True})
    await tab.nav(url)          # the reload is the part that matters
    ```

    **Then prove which build is running, and prove it from inside the page.**
    A byte compare of served-vs-disk does *not* catch this: both sides are the
    stale-but-identical cached copy. Grep the artifact on disk for a literal
    only the new build emits (`strings app_bg.wasm | grep -c 'new-literal'`)
    to prove the *build* is current, then read the **CSSOM** for a rule the
    change should have altered to prove the *page* picked it up:

    ```js
    [...document.styleSheets].flatMap(s => [...s.cssRules])
      .filter(r => (r.selectorText||'').includes('<the-class>'))
      .map(r => r.cssText)
    ```

    Computed style (`getComputedStyle`) proves what resolved; the CSSOM proves
    which rule is in the sheet. When the two disagree with the source, you are
    reading a cached build. A `?cb=<ts>` on the *artifact* URL also works and is
    worth reaching for when the harness controls the fetch.

    **A fix that provably changed nothing is a statement about the artifact,
    never about the code.** The reflex to go re-read the source is wrong until
    the build-identity check has run.

24. **Injected probe CSS outlives the page you injected it into — a hash-only
    navigation does not reload the document, so your "before" measurement is
    your own fix.** `goto_url` to the same page with a different `#fragment`
    performs a same-document navigation: the `<style>` element you appended
    stays in `document.head`. The symptom is an A/B where the *before* arm
    already carries the candidate fix, so a fix that works reads as broken and
    you start re-deriving a correct change.

    Two cheap defences, both needed:

    - **Measure the before/after on the same row, in one page load** — record
      the baseline, click to change state, record again. Never compare two
      separately-navigated loads.
    - **Prove the page is clean before trusting a reading:** assert no element
      carries your marker (`document.querySelectorAll('[data-probe]').length === 0`)
      or serve the build on a fresh port. When a measurement contradicts the
      source, suspect your own harness first — it is far more likely than
      three independent CSS hypotheses all being wrong.

    The tell is a "before" that already matches the fix, or a fix that
    reported the *same* wrong number in both arms.

23. **An instrument that reports the wrong element measures physics, not the
    mapping.** When measuring "does a click land where the pointer went",
    every shortcut contaminates the reading and each one looks like a small
    correction:

    | shortcut | what it actually measures |
|---|---|
    | centroid of *all* non-background ink | every object on screen, so N objects give a centroid N frames wide — check the ink area against one object's expected area |
    | bounding box of all ink | same failure, silently, because the box grows instead of skewing |
    | pause-then-click-then-read | pause freezes one object; objects spawned earlier keep moving, and the click may land on a stale one |
    | click, read after a wall-clock wait | the object drifts for the whole wait, so the offset is drift plus mapping |

    Use **connected-component labelling** and take the single largest blob, so
    the verdict names one object and its area is checkable against the radius
    the draw code uses. Assert the freeze before relying on it — click the
    pause control and confirm its label actually flipped — because a pause that
    silently did nothing contaminates every later sample while looking correct.

    **Difference-of-differences removes the drift.** Click twice at two points
    and subtract: `(blobB - clickB) - (blobA - clickA)`. Physics cancels, so a
    shared drift term cannot masquerade as a constant mapping error. This also
    distinguishes the two defect classes that look identical in one sample: a
    **constant** residual across both points is a fixed offset, while a
    residual that **scales with distance from the origin** is a scale error
    (viewport smaller than the drawing buffer, letterboxing, a wrong backing
    store) — and that ratio is directly actionable, because it equals the
    dimension mismatch.

    Sample unpaused numbers too, but report them separately and exclude them
    from the verdict; when 2D and GPU arms report the *same* unpaused error,
    that is the shared simulation drift, not two coincident bugs.

25. **Scroll-event listeners can stay silent while the container scrolls —
    verify scroll-driven behaviour by setting `scrollTop` and reading DOM,
    never by awaiting the event.** A delegated
    `document.addEventListener('scroll', fn, true)`, and even a listener
    attached directly to the scrolling element, can report zero events after
    programmatic `scrollTop` changes — in the harness, and in app shells
    that swallow propagation. Before concluding the app is broken,
    control-test the channel itself: a synthetic `overflow:auto` div on a
    known-simple page (example.com) with a listener and a `scrollTop`
    assignment. If the control also reports zero, the channel is the
    limitation: set `scrollTop`, wait, and read the resulting DOM state
    instead. Corollary for app code that must be verifiable headlessly (and
    robust under event-eating shells): drive scroll-tracking logic from a
    short `setInterval` poll of `scrollTop` with an early-out when unchanged
    — not from scroll events, and not from rAF, which hidden tabs pause
    entirely while `setInterval` is only throttled to ~1 Hz.

## Domain depth

- `references/refactoring-a-live-page.md` — the deletion-by-anchor class in
  full: cutting by named construct instead of a range, the three layers of a
  control removal (markup / data path / init side effects), the served-page
  smoke test that is the only gate which can see a called-but-deleted name, and
  what to do when the user reports something every gate passed.
- `references/voxel-and-physics-pitfalls.md` — the recurring bug classes when
  implementing voxel/grid worlds and AABB character physics: predicate defaults,
  snap-to-new-position, state-order-of-operations, spawn validation.
- `references/actor-visibility-attribution.md` — when an object's state and
  transform are correct but it is absent from the frame: the elimination
  ladder, the CPU-index-into-GPU-table silent skip, validating a debug toggle
  before trusting its zero, and inverting a pixel A/B when the noise floor is
  too high. Run `scripts/pixel_ab.py` for the diff.
- `references/low-framerate-determinism.md` — when a clamped delta makes a
  60 Hz design fail at 3 Hz: crossing geometry is a timestep test, a world
  built along the walked path must be walked before it is queried, and a
  frame-history state is only visible in the trajectory.
- `references/headless-sim-time-and-movement-probes.md` — driving a real-time
  sim from a headless harness: measuring the throttle factor, polling on
  displacement, separating "did not move" into its three causes, spotting a
  teleport destination from a repeated endpoint, arrival-radius vs recovery
  thresholds, the collision/floor geometry seam tests cannot see, and stale
  artifacts after an incremental build.
- `references/cdp-round-trip-cost.md` — why a harness can be slow while the
  frame rate looks fine: measuring the `Runtime.evaluate` cost, batching the
  walk loop into one in-page IIFE without moving any decision out of Python,
  the silent traps (promise `JSON.stringify`, `rAF` not equalling a frame,
  thresholds re-tuned for a different sample rate), counting diagnostic
  tokens to catch a branch that stopped running, and verifying the page-side
  logic in node against a stub.
- `references/static-site-single-origin-deploy.md` — publishing a multi-file
  site to a per-file CDN: why references must be rewritten leaves-first, and
  the importmap / non-JSON-stdout / partial-run traps.
- `references/token-migration-skips-pseudo-elements.md` — unifying edge
  distances onto one CSS token across a component library: why `::after` and
  absolutely-positioned children silently keep the old value, the greps that
  catch them, and the cross-viewport probe that proves the divider lines up
  with the content it frames. Its sibling case — when the *token's value*
  is untrustworthy rather than merely inconsistent, and one edge was gated
  while the others kept reading `env()` — is in
  `references/env-inset-token-trust-gate.md`.
- `scripts/deploy-site.js` — dependency-aware multi-file deploy: scans the
  graph (importmaps included), topologically sorts leaves-first, rewrites each
  file's local references to the final URL, uploads, prints
  `{ entry_url, files }`. Run it, don't re-derive the loop.
