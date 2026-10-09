"""
meteor -- a meteoroid ablating in entry: a 90 mm rock with an ablation wake.

Size class `small` (30..150 mm band). Stated at 1:3 scale: a real
meteoroid is about 90 mm, so this is a 30 mm body with a 115 mm wake.
A meteor is a rock, a glowing sheath and a
trail, and the ordering matters: the sheath is hottest at the FRONT of the
rock and trails off behind, and the wake is widest just behind the body then
narrows. Get the taper backwards and it reads as a comet -- which is the
mistake this model exists to avoid, because comet and meteor look similar in
thumbnail and are not the same object.

The rock is a faceted lump, flat shaded. The sheath and wake are emissive at a
modest strength, plus one bright bow-shock cap at the leading face.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    meteoroid_diameter=30.0,
    wake_length=115.0,
    wake_max_diameter=70.0,
    sheath_diameter=52.0,
)

ND = SPEC["meteoroid_diameter"]
WL = SPEC["wake_length"]
WD = SPEC["wake_max_diameter"]


def _lump(seed, jitter, rings=6, segs=11):
    rnd = random.Random(seed)
    pts = [(0.0, 0.0, 1.0)]
    for j in range(1, rings):
        phi = math.pi * j / rings
        for i in range(segs):
            a = 2.0 * math.pi * i / segs
            r = 1.0 + rnd.uniform(-jitter, jitter)
            pts.append((r * math.sin(phi) * math.cos(a),
                        r * math.sin(phi) * math.sin(a),
                        r * math.cos(phi)))
    bottom = len(pts)
    pts.append((0.0, 0.0, -1.0))
    faces = []
    for i in range(segs):
        k = (i + 1) % segs
        faces.append((0, 1 + k, 1 + i))
    for ring in range(rings - 2):
        b0, b1 = 1 + ring * segs, 1 + (ring + 1) * segs
        for i in range(segs):
            k = (i + 1) % segs
            faces.append((b0 + i, b0 + k, b1 + k, b1 + i))
    base = 1 + (rings - 2) * segs
    for i in range(segs):
        k = (i + 1) % segs
        faces.append((bottom, base + i, base + k))
    return pts, faces


def _fit(pts, size):
    """Scale a unit lattice so its ACTUAL extent equals size exactly.

    Jitter is asymmetric, so multiplying by half the target overshoots -- a
    declared 30 mm body came out 33.6 mm. Measuring the lattice's own
    extents is what makes the declared and rendered envelopes agree.
    """
    xs, ys, zs = ([p[i] for p in pts] for i in range(3))
    f = [size[k] / (max(v) - min(v)) for k, v in enumerate((xs, ys, zs))]
    c = [(max(v) + min(v)) / 2.0 for v in (xs, ys, zs)]
    return [tuple((p[k] - c[k]) * f[k] for k in range(3)) for p in pts]


def build():
    rock = bkit.pbr("MeteoroidRock", base=(0.14, 0.13, 0.12), rough=0.80)
    ablation = bkit.pbr("AblationSheath", base=(0.03, 0.02, 0.02), rough=0.4,
                        emission=(1.00, 0.52, 0.18), emission_strength=1.5)
    shock = bkit.pbr("BowShock", base=(0.04, 0.04, 0.05), rough=0.3,
                     emission=(0.80, 0.86, 1.00), emission_strength=1.5)
    wake = bkit.pbr("WakePlasma", base=(0.03, 0.02, 0.02), rough=0.5,
                    emission=(0.95, 0.44, 0.20), emission_strength=1.5)

    # ---- the meteoroid: faceted, leading face toward -X -----------------
    pts, faces = _lump(31, 0.24)
    verts = _fit(pts, (ND, ND * 0.92, ND * 0.84))
    body = bkit.mesh_from("Meteoroid", verts, faces, mat=rock, smooth=False)
    bkit.recalc(body)

    # ---- ablation sheath: hugs the rock, thickest at the front -----------
    prof = [(ND * 0.52, -ND * 0.56),          # leading cap, just off the rock
            (ND * 0.86, -ND * 0.30),
            (ND * 0.78, 0.0),
            (ND * 0.40, ND * 0.40),
            (ND * 0.22, ND * 0.60),
            (0.0, ND * 0.72)]
    sheath = bkit.lathe("AblationSheath", prof, segments=28, mat=ablation,
                        smooth=True)
    bkit.recalc(sheath)
    sheath.rotation_euler = (0.0, math.radians(90.0), 0.0)

    # ---- bow shock: a bright cap standing off the leading face -----------
    shock_cap = bkit.uv_sphere("BowShock", ND * 0.62, segments=28, rings=14,
                               centre=(0.0, 0.0, 0.0), mat=shock)
    shock_cap.scale = (0.30, 0.95, 0.95)
    bkit.apply_mods(shock_cap)
    bkit.move(shock_cap, -ND * 0.62, 0.0, 0.0)

    # ---- the wake: widest just behind the rock, then tapering to nothing --
    # The taper direction is the whole difference between a meteor and a
    # comet: a meteor's wake comes OFF the rock and fades. It does not flare
    # outward the way a comet's tail does.
    # The profile starts at z=0 so that, after the +90 deg rotation about Y (which
    # maps profile +Z onto world +X), the wake's measured length IS the
    # declared length. Starting the profile at the body's radius makes every
    # length check come up short by that offset.
    wake_prof = [
        (WD * 0.44, 0.0),
        (WD * 0.50, ND * 0.45),           # peak width, just behind the body
        (WD * 0.42, WL * 0.40),
        (WD * 0.26, WL * 0.68),
        (WD * 0.11, WL * 0.90),
        (0.0, WL),
    ]
    tail = bkit.lathe("Wake", wake_prof, segments=28, mat=wake, smooth=True)
    bkit.recalc(tail)
    tail.rotation_euler = (0.0, math.radians(90.0), 0.0)

    # ---- shock diamonds: the bright nodes along the wake -----------------
    # A real meteor's wake is beaded, not smooth. Five of them, on a computed
    # pitch down the wake axis, sized from their distance along it.
    for i in range(5):
        t = (i + 0.6) / 5.4
        x = ND * 0.30 + WL * t
        d = WD * (0.42 - 0.30 * t)
        dia = bkit.uv_sphere("ShockDiamond%d" % (i + 1), d * 0.5, segments=20,
                             rings=10, centre=(0.0, 0.0, 0.0), mat=shock)
        # elongated ALONG the wake axis, which is +X after this rotation
        dia.scale = (1.35, 1.0, 1.0)
        dia.rotation_euler = (0.0, math.radians(90.0), 0.0)
        bkit.move(dia, x, 0.0, 0.0)

    return dict(spec=SPEC, parts=3 + 5)


CHECKS = [
    dict(name="meteoroid_diameter", mm=30.0, tol=1.0,
         how="diameter", part="Meteoroid"),
    # The wake lathe is rotated 90 deg about Y, so its bbox_x is its LENGTH.
    # The width is bbox_y.
    dict(name="wake_max_diameter", mm=70.0, tol=3.0, how="bbox_y", part="Wake"),
    dict(name="wake_length", mm=115.0, tol=4.0, how="bbox_x", part="Wake"),
    dict(name="sheath_length", mm=38.4, tol=1.5,
         how="bbox_x", part="AblationSheath"),
    dict(name="overall_length", mm=139.2, tol=4.0, how="bbox_x"),
    dict(name="overall_height", mm=70.0, tol=4.0, how="bbox_z"),
]