"""
lighthouse -- a 30 m tower: a lathed conical shaft with a concave (hyperbolic)
taper, a corbelled gallery, a glazed lantern room, and a domed cap with a
finial.

The taper is the object. A lighthouse shaft is not a straight cone: it follows
a hyperbola so the silhouette stays slender at the top while the base carries
the mass. Sampling that curve is what makes this read as a lighthouse rather
than as a bollard.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_height=30000.0,
    base_diameter=7000.0,
    shaft_top_diameter=3200.0,
    shaft_height=24000.0,
    plinth_height=800.0,
    gallery_height=1400.0,
    gallery_diameter=5200.0,
    lantern_height=3000.0,
    lantern_diameter=2600.0,
    cap_height=1600.0,
    finial_height=1000.0,
    lantern_bays=12,
)

BH = SPEC["base_diameter"] / 2.0
ST = SPEC["shaft_top_diameter"] / 2.0
SH = SPEC["shaft_height"]
PL = SPEC["plinth_height"]
GH = SPEC["gallery_height"]
GD = SPEC["gallery_diameter"] / 2.0
LH = SPEC["lantern_height"]
LD = SPEC["lantern_diameter"] / 2.0
CH = SPEC["cap_height"]


def _lathe(name, profile, **kw):
    """`bkit.lathe` followed by a re-weld that works at this model's scale.

    `bkit.weld` defaults to dist_mm=0.0005 (5e-7 m), which is finer than the
    float32 precision of Blender's weld hash once a mesh sits more than about
    12 m up. The `segments` vertices a lathe emits at its pole then fail to
    merge, and the solid reports 40-90 non-manifold edges at the apex. Welding
    again at 0.1 mm collapses the pole properly; 0.1 mm is three orders of
    magnitude below the smallest feature in this model.
    """
    ob = bkit.lathe(name, profile, **kw)
    bkit.weld(ob, 0.1)
    bkit.recalc(ob)
    return ob


def build():
    masonry = bkit.preset("ceramic")
    # Painted bands: the daymark is what makes a lighthouse instantly legible.
    band_red = bkit.pbr("LighthouseBand", base=(0.55, 0.13, 0.11), rough=0.42)
    gallery_metal = bkit.preset("anodized")
    glazing = bkit.pbr("LanternGlass", base=(0.86, 0.90, 0.94), rough=0.06,
                       transmission=0.55)
    cap_mat = bkit.pbr("LighthouseCap", base=(0.16, 0.17, 0.19), metal=0.85,
                       rough=0.42)

    # ---- plinth -----------------------------------------------------------
    plinth = _lathe("LighthousePlinth", [
        (0.0, 0.0), (BH + 400.0, 0.0), (BH + 400.0, PL * 0.55),
        (BH + 120.0, PL), (0.0, PL),
    ], segments=96, mat=masonry)

    # ---- shaft: the hyperbolic taper -------------------------------------
    # r(f) blends from the plinth to the top along a concave curve. Sampling
    # it in 14 steps gives the profile its continuous sweep.
    prof = [(0.0, PL)]
    steps = 14
    for i in range(steps + 1):
        f = i / float(steps)
        r = (BH + 120.0) + (ST - BH - 120.0) * (f ** 1.55)
        prof.append((r, PL + SH * f))
    prof.append((0.0, PL + SH))
    shaft = _lathe("LighthouseShaft", prof, segments=96, mat=masonry)

    # ---- the daymark band: a second material on the same solid -----------
    # assign_faces_by, not a second object: a duplicate shell would z-fight
    # with the shaft and double the non-manifold count.
    bkit.assign_faces_by(
        shaft, band_red,
        lambda c, n: (PL + SH * 0.52) < c.z / bkit.MM < (PL + SH * 0.76),
    )

    # ---- gallery: corbelled out on a ring of brackets -------------------
    zg = PL + SH
    gallery = _lathe("LighthouseGallery", [
        (ST, zg - 60.0),
        (ST + 200.0, zg + 120.0),             # corbel flare
        (GD, zg + 300.0),
        (GD, zg + GH - 120.0),
        (GD - 140.0, zg + GH),
        (ST - 60.0, zg + GH),
        (0.0, zg + GH),
    ], segments=96, mat=gallery_metal)

    # ---- lantern room: real glazing between 12 mullions ------------------
    # The mullions are the read: a lantern is a glass drum in a cage.
    zl = zg + GH
    for i in range(SPEC["lantern_bays"]):
        a = 2.0 * math.pi * i / SPEC["lantern_bays"]
        bkit.rounded_box("LanternMullion%d" % (i + 1), 90.0, 150.0, LH,
                         r=10.0, segments=2,
                         centre=(LD * math.cos(a), LD * math.sin(a),
                                 zl + LH / 2.0), mat=gallery_metal)
    drum = bkit.tube("LanternGlass", LD - 40.0, LD - 70.0, LH, segments=96,
                     centre=(0.0, 0.0, zl + LH / 2.0), mat=glazing)

    # ---- cap: a dome with a vent ball and a finial ----------------------
    zc = zl + LH
    cap = _lathe("LighthouseCap", [
        (0.0, zc),
        (LD + 120.0, zc),
        (LD + 40.0, zc + CH * 0.30),
        (LD * 0.72, zc + CH * 0.62),
        (LD * 0.40, zc + CH * 0.85),
        (LD * 0.16, zc + CH),
        (0.0, zc + CH + 180.0),
    ], segments=72, mat=cap_mat)

    finial = _lathe("LighthouseFinial", [
        (0.0, zc + CH + 160.0),
        (90.0, zc + CH + 240.0),
        (150.0, zc + CH + 330.0),
        (60.0, zc + CH + 430.0),
        (0.0, zc + CH + SPEC["finial_height"]),
    ], segments=32, mat=cap_mat)

    return dict(spec=SPEC, parts=5 + SPEC["lantern_bays"],
                bays=SPEC["lantern_bays"])


CHECKS = [
    dict(name="overall_height", mm=31800.0, tol=60.0, how="bbox_z"),
    dict(name="plinth_diameter", mm=7800.0, tol=40.0, how="diameter",
         part="LighthousePlinth"),
    dict(name="shaft_height", mm=24000.0, tol=40.0, how="bbox_z",
         part="LighthouseShaft"),
    dict(name="gallery_diameter", mm=5200.0, tol=40.0, how="diameter",
         part="LighthouseGallery"),
    dict(name="lantern_height", mm=3000.0, tol=30.0, how="bbox_z", part="LanternGlass"),
]
