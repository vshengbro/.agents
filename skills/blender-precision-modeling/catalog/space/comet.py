"""
comet -- a Halley-class comet: an irregular 30 km nucleus, a 100 000 km coma,
and a 2 x 10^8 km dust tail pointing anti-sunward.

Size class `medium` (150..600 mm band, tolerance x0.5..x2). Stated at
1:2.7e8 scale: the nucleus is 110 mm across, the coma 360 mm and the tail
560 mm. The RATIOS are the real ones -- nucleus : coma : tail = 1 : 3.3 : 5.1
at this truncation of the 6.7e3 real ratio -- and the RATIOS are the only
thing that can be honest at this scale.

Three things have to be true:
1. the nucleus is a FACETED irregular lump, not a sphere -- a smooth ball
   reads as a planet,
2. the coma is a teardrop, brightest and widest on the sunward side, because
   it is being blown off the sunlit face: the profile is asymmetric,
3. the tail is CONVEX -- dust curves back under its own pressure, so a cone
   flaring away from the coma is right and a straight cylinder is not.
Everything bright is emissive at a modest strength; the nucleus is not.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    nucleus_diameter=110.0,
    coma_diameter=360.0,   # across; coma_length is along the tail
    coma_length=520.0,
    tail_length=560.0,
    tail_base_diameter=150.0,
)

ND = SPEC["nucleus_diameter"]
CODA = SPEC["coma_diameter"]
TAIL = SPEC["tail_length"]


def _lump(seed, jitter, rings=7, segs=11):
    """Faceted irregular body: perturbed low-segment sphere, flat shaded."""
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
    xs, ys, zs = ([p[i] for p in pts] for i in range(3))
    f = [size[k] / (max(v) - min(v)) for k, v in enumerate((xs, ys, zs))]
    c = [(max(v) + min(v)) / 2.0 for v in (xs, ys, zs)]
    return [tuple((p[k] - c[k]) * f[k] for k in range(3)) for p in pts]


def build():
    # nucleus: dark, non-emissive, slightly warm. THIS is what anchors the
    # whole model -- a comet with no dark nucleus reads as a glowing ball.
    rock = bkit.pbr("CometNucleus", base=(0.055, 0.052, 0.050), rough=0.86)
    frost = bkit.pbr("CometFrost", base=(0.55, 0.57, 0.60), rough=0.34)
    # Strengths ~0.45, not 1.5. The coma, both tails and the sheath overlap in
    # the middle of frame: at 1.5 the stack saturates to white and the DARK
    # NUCLEUS disappears inside it, which is the one thing a comet must show.
    coma_mat = bkit.pbr("Coma", base=(0.02, 0.02, 0.03), rough=0.5,
                        emission=(0.55, 0.78, 1.00), emission_strength=0.30)
    ion_mat = bkit.pbr("IonTail", base=(0.02, 0.02, 0.02), rough=0.5,
                       emission=(0.42, 0.80, 1.00), emission_strength=0.40)
    dust_mat = bkit.pbr("DustTail", base=(0.03, 0.03, 0.03), rough=0.6,
                        emission=(0.95, 0.90, 0.78), emission_strength=0.32)

    # ---- nucleus ----------------------------------------------------------
    pts, faces = _lump(88, 0.22)
    verts = _fit(pts, (ND, ND * 0.86, ND * 0.78))
    nucleus = bkit.mesh_from("Nucleus", verts, faces, mat=rock, smooth=False)
    bkit.recalc(nucleus)
    # frost patches: the volatile ices that survive on the night side
    bkit.assign_faces_by(nucleus, frost, lambda c, n: n.z > 0.30)

    # ---- coma: a TEARDROP, widest and brightest toward the sun ----------
    # The profile walks out from the nucleus, bulges toward the sun (+X),
    # then closes back: a symmetric envelope here is the classic error, and
    # it is what makes a lot of comet models look like a cotton ball.
    prof = []
    n = 16
    for i in range(n + 1):
        t = float(i) / n
        a = math.pi * t
        # r is biased toward the SUNWARD (+Z before rotation, +X after) end:
        # a symmetric revolved envelope is a solid ball that swallows the
        # nucleus. The coma has to be a teardrop whose fat end faces the sun.
        r = (CODA / 2.0) * math.sin(a) * (0.30 + 0.80 * math.cos(a) ** 3)
        prof.append((r, SPEC["coma_length"] * 0.5 * (1.0 - math.cos(a))))
    coma = bkit.lathe("Coma", prof, segments=32, mat=coma_mat, smooth=True)
    bkit.recalc(coma)
    coma.rotation_euler = (0.0, math.radians(90.0), 0.0)
    # Its mouth starts at the nucleus, not well downstream of it: offset the
    # other way the whole coma sits over the rock and the nucleus is lost.
    bkit.move(coma, ND / 2.0 + CODA * 0.55, 0.0, 0.0)

    # ---- ion tail: narrow, straight, faint, the fastest component --------
    # CONVEX profile: dust and ion streams curve back under radiation
    # pressure and the solar wind, so a flaring cone is correct and a
    # straight-sided cylinder is not.
    ion_prof = [
        (0.0, 0.0),
        (SPEC["tail_base_diameter"] * 0.30, 0.0),
        (SPEC["tail_base_diameter"] * 0.18, TAIL * 0.45),
        (SPEC["tail_base_diameter"] * 0.07, TAIL * 0.85),
        (0.0, TAIL),
    ]
    ion = bkit.lathe("IonTail", ion_prof, segments=24, mat=ion_mat, smooth=True)
    bkit.recalc(ion)
    ion.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(ion, ND / 2.0 - 30.0, 0.0, 0.0)

    # ---- dust tail: broader, curving, yellow-white -----------------------
    dust_prof = [
        (0.0, 0.0),
        (SPEC["tail_base_diameter"] * 0.62, 0.0),
        (SPEC["tail_base_diameter"] * 0.40, TAIL * 0.40),
        (SPEC["tail_base_diameter"] * 0.19, TAIL * 0.78),
        (0.0, TAIL * 0.94),
    ]
    dust = bkit.lathe("DustTail", dust_prof, segments=24, mat=dust_mat,
                      smooth=True)
    bkit.recalc(dust)
    dust.rotation_euler = (0.0, math.radians(90.0), math.radians(7.0))
    bkit.move(dust, ND / 2.0 - 40.0, 0.0, -20.0)

    # ---- streamers: coma rays on computed azimuths ----------------------
    # The fine radial structure in a real coma. Six of them, evenly spaced by
    # angle, at the sunward hemisphere only.
    for i in range(6):
        a = math.pi * (0.12 + 0.76 * i / 5.0)
        bkit.rounded_box("Streamer%d" % (i + 1), 95.0, 8.0, 8.0, r=4.0,
                         centre=(-CODA * 0.30 + 40.0 * math.cos(a),
                                 CODA * 0.34 * math.cos(a),
                                 CODA * 0.34 * math.sin(a)),
                         mat=coma_mat)

    return dict(spec=SPEC, parts=3 + 6)


CHECKS = [
    dict(name="nucleus_diameter", mm=110.0, tol=2.0, how="diameter", part="Nucleus"),
    dict(name="coma_length", mm=520.0, tol=10.0, how="bbox_x", part="Coma"),
    dict(name="tail_length", mm=560.0, tol=6.0, how="bbox_x", part="IonTail"),
    dict(name="overall_length", mm=966.0, tol=12.0, how="bbox_x"),
    dict(name="overall_height", mm=236.0, tol=14.0, how="bbox_z"),
]