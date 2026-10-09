# Materials

`bkit.preset(name)` returns a named PBR material. Using presets instead of
inline nodes keeps a catalog visually coherent — 717 objects that each invented
their own grey look like 717 unrelated objects.

| Preset | For |
|---|---|
| `polished_metal` `brushed_metal` `anodized` `dark_metal` `gold` `copper` `steel` | metal |
| `white_plastic` `black_plastic` `red_paint` `blue_paint` `yellow_paint` | shells and housings |
| `wood` `fabric` `rubber` `ceramic` `glass` `soil` `leaf` | everything else |

## Metal base tone is the strongest single lever

Under this rig a metal preset authored at `base ≈ 0.82` renders a **near-white
sheet with no tonal range** — it reads as paper, not steel. Measured on a knife
blade with the lighting held completely fixed and only the material changed:

| base | metal | result |
|---|---|---|
| 0.82 | 0.85 | near-white, no gradient, reads as paper |
| 0.58 | 0.85 | grey, but speckled |
| **0.48** | **0.90** | **reads as steel**, visible tonal gradient |

So the presets now sit with relative luminance around 0.45–0.62. This is not a
matter of taste and it is worth the whole catalog: **509 of 731 models take
their metal from a preset**, so a base that is too high washes out two thirds of
the catalog at once.

Judge a base colour by **relative luminance**, not by its largest channel.
Gold and copper are chromatic and their red channel is legitimately high, but
their luminance is moderate — a max-channel rule would flag them as washed out
and invite someone to "fix" them into grey. Both invariants are pinned by
regression tests.

## A metal gets its variation from reflection, not roughness jitter

The auto-derived micro-detail in `pbr()` deliberately branches on metalness,
and the metal branch stays **small** (`rough_var ≈ 0.04`, `bump ≈ 0.00016`).

Widening the metal swing to `rough_var 0.13` was tried, on the reasoning that a
±0.11 swing was too subtle to break up a flat face. It does break the face up —
with visible dark speckle across the whole blade, which reads as dirt rather
than as brushing. A polished metal already varies through what it reflects;
adding roughness jitter on top fights that instead of helping it.

The wide swing is right for the *dielectrics* — fabric, soil, stone — where
reflection carries nothing and the roughness variation is the only tooth
available. A regression test asserts both ends of that split, so the two
families cannot drift into each other again.

## Two material facts that decide whether a render works

**Metals have no diffuse.** With `metallic = 1.0` the surface only reflects. In
a dark studio it renders black no matter how much light you add — the fix is a
bright world gradient, not more lamps. See `staging.md`.

**Roughness sells the material more than colour does.** A glossy dielectric at
`roughness 0.12` reads as glazed ceramic; the same colour at `0.45` reads as
matte clay. Be suspicious of a render that looks like plastic — usually the
roughness is too high and there are no specular highlights.

## Metals are deliberately below metal=1.0 in this preset set

A perfectly metallic surface has **no diffuse term at all** — it is pure
reflection. In this dark studio that means a `metal=1.0` object mirrors the
backdrop and renders black, no matter how many lamps you add.

The presets therefore sit at **metal ≈ 0.85**: enough diffuse to hold form under
this rig, still unmistakably metallic. Every wave-2 model that reached for
`metal=1.0` needed a local override before it could be read at all.

Reach for `bkit.pbr(..., metal=1.0)` only for genuine mirrors, and check the
render. If a metal still reads black, the problem is the environment, not the
lamp count.


## Socket names move between versions

Blender 4.x renamed several Principled inputs. `bkit.pbr()` sets them through a
safe setter that tries each known name, so the toolkit works across versions:

| Old | Current |
|---|---|
| `Clearcoat` | `Coat Weight` |
| `Clearcoat Roughness` | `Coat Roughness` |
| `Transmission` | `Transmission Weight` |
| `Emission` | `Emission Color` |

## Two materials on one solid

```python
bkit.assign_faces_by(
    body, glaze,
    lambda c, n: (c.x**2 + c.y**2)**0.5 / bkit.MM < (BODY_R - WALL) and c.z / bkit.MM < H - 0.5,
)
```

The predicate receives the face centre in world coordinates (metres) and the
face normal. Divide by `bkit.MM` when comparing against millimetre limits.

Do **not** build a second object to represent an interior surface. It z-fights
with the wall it sits inside, and it makes both objects non-manifold — the
single most common way a model that looks fine still fails the mesh check.

## Custom materials

`bkit.pbr(name, base=…, rough=…, metal=…, transmission=…, ior=…,
emission=…, emission_strength=…, coat=…)` covers anything the presets do not.
Keep emission strength modest: values above ~2 blow out in Cycles previews.
