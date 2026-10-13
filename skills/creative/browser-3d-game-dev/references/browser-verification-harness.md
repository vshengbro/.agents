# Browser Verification Harness for Real-Time Simulations

Assertion patterns for driving a running game/simulation in a live browser and proving a
feature works. Every snippet here is meant to be pasted into a `js()` probe and read as
data — not eyeballed from a screenshot.

## Why measure instead of look

A screenshot proves *something rendered*. It cannot distinguish "working" from "working
at the one angle I looked from". These bugs are invisible in a still and obvious to a
number:

- forward vector 180° inverted (correct at yaw 0, backwards at yaw 90)
- horizontal velocity never integrated in one movement mode
- collision snap using the pre-move position (entity creeps up every frame)
- fluid spread gated on a condition that is never true
- sun sprite below the horizon at noon
- one material scrolling a texture atlas shared with every other block
- a noise threshold centred on the noise mean, silently making half the world ocean

Each has a probe below. When a user reports a class of bug ("everything is moving",
"terrain is bad"), the first job is to find the number that distinguishes the two
hypotheses, not to pick one and test it.

## Preconditions

1. Expose the instance: `window.__game = game` in the entry module.
2. Put the tab in the foreground before probing: `cdp("Page.bringToFront")`.
   Background tabs throttle rAF and the render loop barely advances.
3. Serve with no-cache headers. Verify before trusting any browser result:
   `curl -s http://127.0.0.1:PORT/js/player.js | wc -c` == on-disk size.

## Movement-basis sweep

The highest-value probe in this class. Assert that pressing forward moves along the
camera's looking direction, at many angles.

```js
(() => {
  const p = window.__game.player;
  const idle = {fwd:0,right:0,jump:false,sneak:false,sprint:false};
  const out = [];
  for (const yaw of [0, Math.PI/4, Math.PI/2, Math.PI, -Math.PI/2, 2.4]) {
    p.flying = true;            // ignore terrain, isolate the movement basis
    p.vel.set(0,0,0);
    p.yaw = yaw; p.pitch = 0;
    p.pos.set(0.5, 60, 0.5);    // known-empty airspace
    for (let i=0;i<15;i++) p.update(idle, 1/60);
    const d = p.lookDirection();          // intent
    p.vel.set(0,0,0);
    const x0 = p.pos.x, z0 = p.pos.z;
    for (let i=0;i<25;i++) p.update({...idle, fwd:1}, 1/60);
    const mx = p.pos.x-x0, mz = p.pos.z-z0, L = Math.hypot(mx,mz)||1;
    out.push(+(((mx/L)*d.x + (mz/L)*d.z)).toFixed(2));  // want 1.0 everywhere
  }
  return JSON.stringify(out);
})()
```

Pass = every value is `1`. A `-1` means the basis is inverted; a mixed set means the
basis is not derived from the same source as the camera.

Mirror it for strafe: expect the right vector to be forward rotated −90° in XZ, i.e.
`(mx,mz) ∝ (d.z, -d.x)`.

## Per-mode movement integration

Assert each movement mode actually integrates every axis it claims to.

```js
(() => {
  const p = window.__game.player;
  const idle = {fwd:0,right:0,jump:false,sneak:false,sprint:false};
  const probe = (label, input, n=60) => {
    p.flying = true; p.vel.set(0,0,0); p.yaw = 0; p.pitch = 0;
    p.pos.set(0.5, 60, 0.5);
    for (let i=0;i<15;i++) p.update(idle,1/60);
    p.vel.set(0,0,0);
    const s = p.pos.clone();
    for (let i=0;i<n;i++) p.update(input, 1/60);
    return {[label]: [+ (p.pos.x-s.x).toFixed(2),
                     + (p.pos.y-s.y).toFixed(2),
                     + (p.pos.z-s.z).toFixed(2)]};
  };
  return JSON.stringify({
    ...probe('flyFwd',  {...idle, fwd:1}),
    ...probe('flyUp',   {...idle, jump:true}),
    ...probe('flyDown', {...idle, sneak:true}),
    ...probe('flyRight',{...idle, right:1}),
  });
})()
```

A zero in any slot is an axis that branch never writes.

## Physics settle / jump / damage

Find solid ground first rather than assuming a coordinate, then assert each property
independently — a single combined probe hides which one broke.

```js
(() => {
  const g = window.__game, p = g.player, w = g.world;
  const idle = {fwd:0,right:0,jump:false,sneak:false,sprint:false};

  // locate real ground near origin
  let sx=0, sz=0, sh=0;
  outer: for (let r=1;r<40;r++) for (let a=0;a<16;a++) {
    const ang=a*Math.PI/8, x=Math.round(Math.cos(ang)*r*4), z=Math.round(Math.sin(ang)*r*4);
    for (let y=40;y>2;y--) if (w.getBlock(x,y,z)!==0 && y<30) { sx=x;sz=z;sh=y; break outer; }
  }

  const o = {};
  // settle: must come to rest ON the surface, not above/below it, and stay there
  p.flying=false; p.vel.set(0,0,0); p.health=20; p.fallStart=null;
  p.pos.set(sx+0.5, sh+12, sz+0.5);
  for (let i=0;i<400;i++) p.update(idle,1/60);
  o.settle = {y:+p.pos.y.toFixed(2), onGround:p.onGround, landedY:sh+1};

  // jump: measure peak rise over a full arc
  p.health=20; p.fallStart=null; p.vel.set(0,0,0);
  p.pos.set(sx+0.5, sh+1.05, sz+0.5);
  const y0 = p.pos.y;
  for (let i=0;i<10;i++) p.update(idle,1/60);
  p.update({...idle, jump:true}, 1/60);
  let peak = y0;
  for (let i=0;i<120;i++){ p.update(idle,1/60); peak = Math.max(peak, p.pos.y); }
  o.jumpHeight = +(peak-y0).toFixed(2);

  // fall damage: big drop damages, small drop and jump do not
  p.health=20; p.fallStart=null; p.vel.set(0,0,0);
  p.pos.set(sx+0.5, sh+12, sz+0.5);
  for (let i=0;i<400;i++) p.update(idle,1/60);
  o.bigFallDamage = 20 - p.health;      // want > 0
  p.health=20; p.fallStart=null; p.vel.set(0,0,0);
  p.pos.set(sx+0.5, sh+2, sz+0.5);
  for (let i=0;i<300;i++) p.update(idle,1/60);
  o.smallDropDamage = 20 - p.health;    // want 0
  return JSON.stringify(o, null, 1);
})()
```

A ratchet bug shows up as `settle.y` drifting upward over successive runs, and
`onGround` false at rest. Landing detection reads stale state when the check is placed
before the integration step instead of after.

## Fluid convergence

Assert both that fluid MOVES and that the sim TERMINATES. A sim that only moves is
usually a runaway flood.

```js
(() => {
  const g = window.__game, w = g.world, p = g.player;
  p.flying = true; p.vel.set(0,0,0);
  const bx=0, bz=0, by=30, R=4, H=6;
  // sealed basin: floor + walls
  for (let dx=-R;dx<=R;dx++) for (let dz=-R;dz<=R;dz++) {
    for (let dy=0;dy<3;dy++) w.setBlock(bx+dx,by+dy,bz+dz, 3);
    for (let dy=3;dy<3+H;dy++) w.setBlock(bx+dx,by+dy,bz+dz, 0);
  }
  for (let i=-R;i<=R;i++) for (let dy=3;dy<3+H;dy++) {
    w.setBlock(bx+i,by+dy,bz-R,3); w.setBlock(bx+i,by+dy,bz+R,3);
    w.setBlock(bx-R,by+dy,bz+i,3); w.setBlock(bx+R,by+dy,bz+i,3);
  }
  w.setBlock(bx,by+3,bz, 9);              // one source
  w.touchWater(bx,by+3,bz);
  const count = () => { let n=0;
    for (let dx=-R;dx<=R;dx++) for (let dz=-R;dz<=R;dz++)
      for (let dy=3;dy<3+H;dy++) if (w.getBlock(bx+dx,by+dy,bz+dz)===9) n++;
    return n; };
  const marks = [{tick:0, water:count(), q:(w._waterSrc||[]).length}];
  for (let t=0;t<40;t++) {
    w.flowWater(500);
    if (t%8===7) marks.push({tick:t+1, water:count(), q:(w._waterSrc||[]).length});
  }
  return JSON.stringify({basinFloor:(2*R+1)*(2*R+1), marks});
})()
```

Pass = water reaches the full floor area (e.g. 49 for a 7×7) and the queue length
reaches 0. If the count freezes below the floor area, lateral spread is gated wrongly.
If the queue keeps growing, there is no per-tick work cap.

Test falling separately: a source over a hole must fill the column top-to-bottom.

## Terrain distribution probe

"Terrain looks bad" is not actionable. Measure the shape of the height field and the
biome mix over a wide sample before touching the generator.

```js
(() => {
  const w = window.__game.world;
  const hs=[];
  for (let z=-2000;z<2000;z+=23) for (let x=-2000;x<2000;x+=23) hs.push(w.heightAtTerrain(x,z));
  hs.sort((a,b)=>a-b);
  const n=hs.length, q=f=>+hs[Math.min(n-1,Math.max(0,Math.floor(n*f)))].toFixed(1);

  let flat=0, mid=0, steep=0;                    // local relief over a 2-block step
  for (let z=-1000;z<1000;z+=37) for (let x=-1000;x<1000;x+=37) {
    const c = w.heightAtTerrain(x,z);
    const d = Math.abs(w.heightAtTerrain(x+2,z)-c) + Math.abs(w.heightAtTerrain(x,z+2)-c);
    if (d <= 1) flat++; else if (d >= 4) steep++; else mid++;
  }
  const t = flat+mid+steep;
  const biomes = {};
  for (let z=-2000;z<2000;z+=61) for (let x=-2000;x<2000;x+=61) {
    const b = w.biomeAt(x,z); biomes[b] = (biomes[b]||0)+1;
  }
  return JSON.stringify({
    min:q(0), p25:q(.25), median:q(.5), p75:q(.75), max:q(1),
    relief:+(q(1)-q(0)).toFixed(1),               // THE number to move
    pctFlat:+(100*flat/t).toFixed(1), pctSteep:+(100*steep/t).toFixed(1),
    biomes,
  });
})()
```

Guard the percentile helper: `hs[Math.floor(n*f)]` returns `undefined` for `f = 1` and
throws on `.toFixed` — clamp the index or the whole probe dies before it reports.

Pass criteria: `relief` should be several times the world height you'd consider
"interesting", `pctFlat` well under 100 for anything but an ocean-heavy seed, and no
biome at 0 while others saturate.

## Noise-layer distribution probe

When remapping a noise layer through `smoothstep`, check what the remap actually did.

```js
(() => {
  const w = window.__game.world;
  const noise2=(x,y,s)=>{const xi=Math.floor(x),yi=Math.floor(y),sm=t=>t*t*(3-2*t);
    const h=(a,b)=>{let n=a*374761393+b*668265263+s*2147483647;n=(n^(n>>>13))*1274126177;
      return ((n^(n>>>16))>>>0)/4294967295;};
    const xf=sm(x-xi),yf=sm(y-yi);
    const a=h(xi,yi),b=h(xi+1,yi),c=h(xi,yi+1),d=h(xi+1,yi+1);
    return (a*(1-xf)+b*xf)*(1-yf)+(c*(1-xf)+d*xf)*yf;};
  const fbm2=(x,y,s,o=5)=>{let f=1,a=1,su=0,no=0;for(let i=0;i<o;i++){su+=noise2(x*f,y*f,s+i*101)*a;no+=a;f*=2;a*=.5;}return su/no;};
  const smoothstep=(e0,e1,x)=>{const t=Math.max(0,Math.min(1,(x-e0)/(e1-e0)));return t*t*(3-2*t);};

  const cont=[], mask=[];
  for (let z=-1500;z<1500;z+=61) for (let x=-1500;x<1500;x+=61) {
    cont.push(smoothstep(0.30, 0.72, fbm2(x/340, z/340, w.seed)));
    mask.push(smoothstep(0.55, 0.95, fbm2(x/260, z/260, w.seed+202, 3)));
  }
  const st=a=>{a.sort((x,y)=>x-y);const n=a.length;return {p5:+a[Math.floor(n*.05)].toFixed(2),
    p50:+a[Math.floor(n*.5)].toFixed(2), p95:+a[Math.floor(n*.95)].toFixed(2),
    belowHalf:+(100*a.filter(v=>v<0.5).length/n).toFixed(1)};};
  return JSON.stringify({continent:st(cont), mountainMask:st(mask)});
})()
```

`belowHalf: 51.7` on a continent mask means half the world is ocean — a threshold
accidentally centred on the noise mean. `p50: 0` on a mountain mask means mountains
essentially do not exist. Both look like "the generator is bad" until you measure.

## Shared-resource animation probe

Animate-one-consumer bugs on shared engine resources show up as the WHOLE world moving.
Assert the shared resource is untouched and the intended one advances.

```js
(() => {
  const g = window.__game;
  return JSON.stringify({
    atlasOffset:   +g.atlasTex.offset.x.toFixed(4),   // must stay 0
    waterTexExists: !!g.waterTex,                    // water must own its texture
    sharesAtlas:   g.waterMat.map === g.atlasTex,    // must be false
  });
})()
```

Read it twice across ~1s to see the one that moves and the one that must not.

## Entity stability probe

Distinguish "bouncing forever" (physics bug) from "walked off a cliff" (correct). The
discriminator is direction reversals, not total range.

```js
(() => {
  const g = window.__game, w = g.world;
  const out = [];
  for (const c of g.creatures.list) {
    for (let i=0;i<80;i++) c.update(1/60, w);          // settle past any spawn drop
    const ys = [];
    for (let i=0;i<120;i++){ c.update(1/60, w); ys.push(+c.pos.y.toFixed(3)); }
    let rev = 0;                                        // direction reversals = oscillation
    for (let i=2;i<ys.length;i++){ const a=ys[i-1]-ys[i-2], b=ys[i]-ys[i-1]; if (a*b < 0) rev++; }
    const mn=Math.min(...ys), mx=Math.max(...ys);
    out.push({ k:c.def.name, range:+(mx-mn).toFixed(3), reversals:rev,
               netDrift:+(ys[ys.length-1]-ys[0]).toFixed(2), onGround:c.onGround });
  }
  return JSON.stringify({ entities: out.length, unstable: out.filter(r => r.reversals > 2) });
})()
```

- `reversals` high, `netDrift` ~0 → infinite bounce; the ground snap is wrong.
- `reversals` 1, `netDrift` negative → it walked off a ledge once. Not a bug — say so
  rather than "fixing" correct locomotion.
- Large `netDrift` with a water column below → the ground scan is finding a sea floor.

## Sky / lighting shared-phase consistency

When several systems read a day-cycle angle, assert they agree.

```js
(() => {
  const g = window.__game, c = g.camera.position;
  const s = g.celestial.sun.position;
  return JSON.stringify({
    sunRelativeY: +(s.y - c.y).toFixed(1),   // must be POSITIVE at noon
    daylight: +g.daylight.toFixed(2),
    sunOpacity: +g.celestial.sunMat.opacity.toFixed(2),
  });
})()
```

If `daylight === 1` (full noon) but `sunRelativeY` is negative, one consumer negated the
phase scalar. Drive every consumer from one shared value per frame.

## Structural integrity scan

Replaces trusting a vision model's "floating geometry" claim with a number. Scan for
voxels that have no support.

```js
(() => {
  const w = window.__game.world; let bad = 0; const samples = [];
  for (const ch of w.chunks.values()) {
    if (!ch.generated) continue;
    for (let lz=0; lz<16; lz++) for (const lx of [0, 15]) for (let y=1; y<40; y++) {
      if (ch.get(lx,y,lz) !== LEAF_ID) continue;      // target class under test
      let sup = false;
      for (let dy=-2; dy<=1; dy++) {                   // column
        const b = ch.get(lx,y+dy,lz);
        if (b === LEAF_ID || b === TRUNK_ID) { sup = true; break; }
      }
      for (const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1]]) {  // neighbours
        const nx=lx+dx, nz=lz+dz;
        if (nx<0||nx>15||nz<0||nz>15) continue;
        for (let dy=-1;dy<=1;dy++) {
          const b = ch.get(nx,y+dy,nz);
          if (b===LEAF_ID||b===TRUNK_ID) { sup=true; break; }
        }
        if (sup) break;
      }
      if (!sup) { bad++; if (samples.length<8) samples.push(`c${ch.cx},${ch.cz} x=${lx} y=${y}`); }
    }
  }
  return JSON.stringify({unsupported: bad, samples});
})()
```

`0` disproves the visual claim. Chunk-border columns (`lx` 0 and 15) are where seam bugs
surface, so scan those specifically.

## Bounded-oscillation probe (gait / spin / orbit)

Any quantity that accumulates every frame (gait phase, orbit angle, spin) must end up
INSIDE a trig function, or it grows without bound and the thing spins at a constant
rate. `scale.sin() * phase` is the classic transposition: the phase multiplies out
instead of oscillating, and the symptom is "limbs are rotating like crazy" rather than
an obviously wrong number. Assert boundedness over time, not a single sample.

```js
(() => {
  const g = window.__game, p = g.player;
  const out = [];
  let phase = 0;                                  // simulate a real accumulating phase
  for (let t = 0; t <= 5; t += 0.5) {
    phase += 2.6 * 4.6 * 0.5;                    // rad/m * m/s * dt
    out.push(+g.limbSwing('leg_l', phase, 1.0).toFixed(3));
  }
  const peak = Math.max(...out.map(Math.abs));
  return JSON.stringify({samples: out, peak,
    bounded: peak <= 1.0,                         // MUST hold for any swing amplitude
    turnPerSec: +(peak * 2.6 * 4.6 / (2*Math.PI)).toFixed(2)});
})()
```

Pass = `bounded: true` and the output repeats with sign changes. `bounded: false` with a
large `turnPerSec` is a transposed trig call: the number of turns per second is exactly
the phase rate times the misapplied constant, which names the mechanism immediately.
Also assert the value returns to 0 when the amplitude envelope fades (`amount = 0`).

## Synthetic input over CDP: focus, then timing

Two independent bugs present identically as "the key does nothing". Fix them in this
order — focus first, because a focus bug makes the timing fix look broken.

```python
# 1. give the listening element focus, then click it
await call("Runtime.evaluate", {"expression":
  "(()=>{const c=document.querySelector('canvas');"
  "if(c){c.tabIndex=0;c.focus();} return document.activeElement.tagName;})()"})
await call("Input.dispatchMouseEvent", {"type":"mousePressed","x":640,"y":400,
                                       "button":"left","clickCount":1})
await call("Input.dispatchMouseEvent", {"type":"mouseReleased","x":640,"y":400,
                                       "button":"left","clickCount":1})

# 2. keydown / tick / keyup as SEPARATE awaited events
await call("Input.dispatchKeyEvent", {"type":"keyDown","key":"w","code":"KeyW",
                                      "windowsVirtualKeyCode":87})
await asyncio.sleep(2.0)                         # let the loop integrate
mid = await ev("JSON.stringify(window.__DEBUG__)")   # assert the delta here
await call("Input.dispatchKeyEvent", {"type":"keyUp","key":"w","code":"KeyW",
                                      "windowsVirtualKeyCode":87})
```

Always assert a **numeric delta** (position moved N metres, a counter advanced) after
the dispatch. If you only check "the dispatch returned without error" you will happily
report a working feature for an element that was never focused.

## Reading the results

- Any value that should be `1` and is not → the invariant is broken; stop and fix.
- `0` where a magnitude is expected → that code path never executes.
- A test that passes locally but the served bytes differ → you are debugging a cache.
- An accumulating value that is not bounded → the phase never reached a trig call.
- Image analysis disagreeing with a numeric probe → trust the probe, and say in the
  report which claims were disproven and how.
