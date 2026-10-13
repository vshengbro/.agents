# Input Axes, Frame Hooks, and Per-Frame Fatal Errors

Probes for the layer between "the simulation is correct" and "the player can
actually drive it". Every bug here renders a perfectly healthy frame.

## The frame hook: test the frame, not the simulation

Input is usually consumed OUTSIDE the sim step — `controls.update()` reads keys
and calls `steer()`, then `game.update()` integrates. A harness that steps only
the sim never reaches the input, and an input test reports "the key does nothing"
for a control that works perfectly.

Expose a hook that mirrors the real loop exactly:

```js
window.__DEBUG__.frame = (n = 1, dt = 1 / 60) => {
  for (let i = 0; i < n; i += 1) {
    if (!game.over) { controls.update(dt); game.update(dt); }
  }
  if (!game.player.dead) chase.snap(game.player, world);
  return window.__DEBUG__.stats();
};
```

Keep the separate sim-only hook too (`settle`) for physics/eat/AI assertions that
should not be perturbed by whatever keys happen to be held. Two hooks, two
purposes: `settle` for world logic, `frame` for anything downstream of input.

Before concluding "the input is broken", confirm the harness reached it: read
`window.__controls.keys` after dispatching keydown. If the key is not in the set,
the bug is in the event plumbing, not the game.

## Per-key steering, asserted in world space

A sign error on a steering axis is invisible to every other test: the fish still
moves, still looks like a fish, still eats. Only a per-key assertion finds it.

```js
(() => {
  const D = window.__DEBUG__, g = window.__game;
  const key = (type, k, code, vk) => window.dispatchEvent(
    new KeyboardEvent(type, {key: k, code: code, keyCode: vk, bubbles: true}));
  const trial = (k, code, vk) => {
    D.clearOthers();
    g.player.pos.set(0, g.world.heightAt(0,0) + 20, 0);
    g.player.vel.set(0,0,0);
    g.player.heading.set(1,0,0);                 // known start heading
    key('keydown', k, code, vk);
    D.frame(45);                                // REAL frame
    // SAMPLE WHILE HELD — after keyup the fish has settled and every trial
    // returns the same value, so the probe cannot discriminate.
    const yaw   = +Math.atan2(g.player.heading.z, g.player.heading.x).toFixed(4);
    const pitch = +g.player.heading.y.toFixed(4);
    key('keyup', k, code, vk);
    return {yaw, pitch};
  };
  return JSON.stringify({
    idle: trial('x','KeyX',88),
    left: trial('a','KeyA',65), right: trial('d','KeyD',68),
    up:   trial('w','KeyW',87), down: trial('s','KeyS',83),
  });
})()
```

Then assert RELATIONSHIPS, never a single sign:

```python
ok = left["yaw"] < -0.2 and right["yaw"] > 0.2 \
      and abs(left["yaw"] + right["yaw"]) < 1e-3     # symmetric: no bias
ok_pitch = up["pitch"] > 0.5 and down["pitch"] < -0.5
```

The symmetry term is what makes the check sign-convention independent: it passes
under either left-handed or right-handed `right = f(heading, up)`, and fails for
any axis that is merely flipped. Asserting "A gives negative yaw" passes when
the whole basis is inverted and fails when it is correct under the other
convention.

To settle the convention once, derive it instead of recalling it:

```
screen-right = heading x up
cross-check:  camera X = up x (camera -Z) = up x (-heading) = heading x up
world dir = heading + right*ax + up*(-ay)
```

`W` conventionally maps to `ay = -0.95` (screen-up is negative), hence the `-ay`
on the vertical term — the same inverted-sign trap one line below the horizontal
one, and the reason both axes should be fixed and tested together.

## Zero-uncaught-exceptions gate

An exception thrown inside a `requestAnimationFrame` callback kills that frame
and nothing else: the entity keeps drifting on its last good velocity, the HUD
keeps updating, triangle counts stay healthy, and screenshots look correct. The
control is dead and the game looks alive. One stale identifier after a rename is
enough — 124 uncaught exceptions in 2 s, zero visible symptoms.

Two cheap gates:

```js
// in-page counter, checked after any run
__DEBUG__.errors = 0;
window.addEventListener('error', () => { __DEBUG__.errors++; });
```

```python
# harness side: assert on the COUNT, and print the list, never just pass/fail
check("no page errors", len(tab.errors) == 0, f"{len(tab.errors)} errors")
if tab.errors: print("PAGE ERRORS:", tab.errors[:10])
```

A list of bare `'Uncaught'` strings with no message is the signature of a throw
inside rAF, where the message is swallowed. After any identifier rename,
`search_files` the old symbol across the module — the write that renames the
declaration is not the write that renames every use.

## Removing an input mode: prove inert AND re-audit coverage

Deleting the mouse handlers is only half the job. The systems the removed mode
implicitly covered must be re-checked, because they were often wired inside a
branch that skipped the player.

```js
// 1. the removed input now does nothing at all
(() => {
  const D = window.__DEBUG__, g = window.__game, c = document.getElementById('view');
  g.player.heading.set(1,0,0); g.player.vel.set(0,0,0);
  const before = g.player.heading.clone();
  for (let i=0;i<12;i++) c.dispatchEvent(new MouseEvent('mousemove', {
    clientX: 100 + i*90, clientY: 300 + i*20, bubbles: true }));
  D.frame(10);
  return JSON.stringify({headingChanged: +before.distanceTo(g.player.heading).toFixed(6)});
})()
// want exactly 0
```

```js
// 2. containment still holds for the player under the SURVIVING controls
(() => {
  const D = window.__DEBUG__, g = window.__game, R = D.worldRadius;
  g.player.pos.set(0, g.world.heightAt(0,0)+20, 0); g.player.heading.set(1,0,0);
  window.dispatchEvent(new KeyboardEvent('keydown', {key:'w', code:'KeyW', keyCode:87}));
  let maxR = 0;
  for (let i=0;i<2400;i++){ D.frame(1); maxR = Math.max(maxR, g.player.pos.length()); }
  window.dispatchEvent(new KeyboardEvent('keyup', {key:'w', code:'KeyW', keyCode:87}));
  return JSON.stringify({worldRadius:R, maxR:+maxR.toFixed(2)});
})()
// want maxR <= worldRadius
```

Also `search_files` the source for the removed mechanism
(`requestPointerLock|mousemove|movement[XY]`) so no dead handler survives, and
check the affordances that referenced it: the cursor (`getComputedStyle(canvas).cursor`)
and every hint string, or the UI keeps instructing the user to use a control that
no longer exists.

## Reading the results

- Every key returns the same value → the harness is not reaching the input; check
  `__controls.keys` before suspecting the game.
- A/D symmetric but the wrong way round → the whole basis is inverted, not one axis;
  re-derive `right` from the camera basis.
- `maxR` past the world radius → containment was only applied to the AI branch.
- Zero motion on a key that the key-set proves was received → look one frame later,
  in the handler that reads it.