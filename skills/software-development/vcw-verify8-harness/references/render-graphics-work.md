# Re-deriving the render pipeline before any graphics change

Graphics work on `vice-city-web` is where "it looks wrong" most often turns
out to be "the harness is compiling a path that real users never hit". Re-derive
the pipeline from source every time — do not trust this file, a previous
session's notes, or the agent's memory of it.

## 0. Establish the actual state first

```bash
cd /Users/sqs/code/vice-city-web
wc -l src/render.rs                      # pipeline size
grep -ci webgl  src/render.rs            # hand-written GL path
grep -ci webgpu src/render.rs            # 0 means the backend migration has NOT landed
grep -rn "antialias\|msaa\|sample_count" src/*.rs
```

The backend has been **hand-written WebGL2** with zero WebGPU references. There
is an untracked `docs/webgpu-migration.md` describing a WebGL2 → euv-engine
WebGPU migration whose stated goal is "no WebGL code, no fallback path". That
plan is not implemented. **Check whether it is still active before touching the
renderer** — every line of rendering code is in motion during a migration, so a
graphics diff built on the current WebGL2 pipeline may be thrown away.

## 1. Inventory what already exists before proposing additions

Grep counts across `src/*.rs` settle most "the renderer can't do X" questions:

| Feature | Grep |
|---|---|
| shadows | `shadow`, `shadow_map`, `depth_texture`, `shadow_pass` |
| fog | `fog`, `FOG` |
| ambient / emissive / bloom | `ambient`, `emissive`, `bloom` |
| antialias | `antialias`, `MSAA`, `FXAA`, `sample_count` |

What was true at the time of writing: **real shadow mapping already exists** —
an `R32F` depth texture sampled and compared manually (PCF), with a separate
depth texture created for the shadow pass. Fog, ambient, emissive and bloom are
all present. So "add shadows" is not the work; the work is quality on top of
what exists.

## 2. Treat every deliberate compromise as harness-scoped, never global

The context is created with `antialias: false` and an in-source comment
explaining why: the city is hard-edged low-poly, and MSAA is too slow on the
**software rasterizer** the acceptance harness runs under. That compromise is
correct for SwiftShader and wrong for a real GPU.

The trap: a harness-only compromise becomes the shipped default because nobody
re-reads the comment when the next person edits that line. The same failure
mode produces a graphics change that wrecks the acceptance run's frame budget,
or one that leaves real users on aliased edges while the suite stays green.

**Rule:** gate expensive quality features on a detectable runtime capability,
never on which machine is testing. If a capability cannot be detected, ship the
cheap path as the default and expose the expensive one behind an explicit
switch.

## 3. Rendering changes interact with every trap in the parent skill

- Under software rendering rAF runs at **~1.7 fps**. A "quality" change that
  costs fill rate can push it far lower, and every per-frame measurement in the
  suite becomes noisier or impossible. Re-run at least one worker after any
  rendering change before trusting its timings.
- `charBox` and every other **pixel** channel depends on the backing-store
  scale (`?res=`) and on camera distance — do not compare crop sizes across a
  rendering change without re-deriving them (trap 40).
- `?hide=` re-reads `location.search` **every rendered frame**, so a rendering
  A/B can be done inside one session without a reboot. Batch ids come from
  `__vcw.limbBatches` and are **not a constant**.
- The crosshair sits inside every `charBox` crop; hide it before any vision
  call (trap 39).
- Numeric gates prove nothing about visual quality. A fragmented character
  passed every adjacency check. For anything visual, call vision and quote it.

## 4. What a graphics change owes the suite

- Rebuild the wasm and confirm the artifact is newer than the sources (see the
  build section in the parent skill), or you are measuring the old pipeline.
- `cargo test` must not regress.
- If the change touches anything the acceptance suite asserts (charBox, res
  scale, hide batches, camera distances), state explicitly which verdicts you
  invalidated. A graphics diff that quietly invalidates three workers is worse
  than one that changes nothing.

## 5. Establishing a performance ceiling before optimising

Never propose a graphics optimisation without a ceiling measurement — otherwise
"we captured most of the available gain" is uncomputed and one real gain cannot
be told from noise. One run answers it: **turn the suspected subsystem off
entirely and measure.** That number decides whether the task is worth doing.

**Then sweep the suspected resource across orders of magnitude**, because the
obvious knob is often the wrong one. Sweeping the shadow map from 1.68M pixels
down to 67K (**1/16 the pixels**) moved frame rate 6% — which disproves the
fill-rate hypothesis and points at vertex/geometry throughput, and therefore
**rules out** shrinking the shadow texture, the first thing anyone would try.
A rejected candidate belongs in the report with the reason it was rejected; it
is a result, not a failure.

**Per-object culling must probe more than the model origin.** A regression test
caught a real bug here: a 40 m building under a low sun has its origin landing
119 m from the focus (correctly culled) while its *base* lands only 61 m (still
inside the frustum, must not be culled). Origin-only testing silently drops
shadows from tall buildings near the player. Probe two heights — origin and
origin offset downward by the cull margin — and assert the frame rate does not
regress when you do.

**Measured outcome (frustum culling on the shadow pass): +20.9%**, reaching 92%
of the "shadow pass entirely disabled" ceiling, leaving ~4 fps of residual. That
residual is the point at which further shadow work has no return: the remaining
cost is the main pass's triangle volume, which is a different (larger) piece of
work. See the framerate section of the parent skill for the measurement-validity
chain that has to be re-proven before any of these numbers mean anything.

## 6b. Ports are diffed by PASS LIST first, constants second

When a ported feature looks "subtle", diffing uniform names produces nothing
useful — both backends call the identical expression. What settles it is a
**budget ratio at one camera**: zero the composite strength on *both* backends,
rebuild, re-shoot all four legs, compare *added light*.

```
                     WebGL2      WebGPU    ratio
night  mean added    0.29629    0.00359   82.6x
dusk   mean added    0.25056    0.02265   11.1x
night  pixels over BLOOM_THRESHOLD   31.4% vs 0.173%
```

A large ratio on identical constants is a **missing pass**, not taste, and not a
constant to crank. Here it was WebGL2's additive glow step (`render.rs:4651`,
gated `emissive_gain > 0.25`) that redraws emissive faces into the scene target
*before* the bright pass — without it the chain correctly processes an image that
has nothing above threshold. **Grep the reference backend for passes the port
skipped before touching any constant.**

One number worth keeping: for additive compositing, **`min(pixel delta) == 0.0`
proves the term only adds light**. A wired-but-discarded chain produces
negative deltas. Cheap, decisive, and it needs no vision call.

## 7. Before starting a backend migration: shadow mapping is the risk

The migration target document's stated goal is "no WebGL code, no fallback
path", i.e. a full rewrite rather than a feature flag. The decisive question is
whether the target backend can express the existing pipeline's hardest feature.
Hand-written shadow mapping — an `R32F` depth texture sampled and compared
manually with a PCF kernel, written from a separate depth texture — is the part
with no obvious equivalent in a higher-level engine API. Multi-pass rendering,
instanced batch drawing, and per-frame debug switches are the secondary
questions.

Two consequences for sequencing:

- **A perf win on the current backend may not survive the migration.** Do not
  bank an optimisation as permanent while a backend migration for that same
  subsystem is a live plan; say so in the delivery instead.
- **Validate feasibility with a minimal draw before committing to the rewrite.**
  "adapter is available" is not proof — render a primitive and read the pixels
  back. Only then decide the investment.

Check the migration document's stated prerequisites against current reality
before trusting them, and prefer reading the engine's real API surface over its
documentation — several of those prerequisites have already been re-verified
and one turned out wrong.