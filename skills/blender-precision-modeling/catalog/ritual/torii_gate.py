"""
torii_gate -- Myojin torii, 5540 mm tall across a 5200 mm span.

A torii has four members and three numbers that matter:

  * the uprights TAPER and lean IN, 3 degrees of raked taper;
  * the LOWER lintel (nuki) is straight and sits 3260 mm up, with the tie-beam
    strut above it;
  * the UPPER lintel (kasagi) CURVES UPWARD -- 260 mm of rise over its 5600 mm
    span.  That curve is the whole silhouette, so the kasagi is a loft of
    sections along X with a rising z, not a box, and the flat-topped version is
    the single most common way a torii comes out wrong.

The uprights' feet are z = 0.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _ritual as R

SPEC = dict(
    height=5540.0,
    span=5200.0,
    post_base_width=520.0,
    post_top_width=400.0,
    post_rake_deg=3.0,
    nuki_height=3260.0,
    nuki_length=5400.0,
    kasagi_length=5600.0,
    kasagi_rise=260.0,
    kasagi_depth=480.0,
    gaku_length=1200.0,
    gaku_height=520.0,
    post_height=5540.0,
)

CHECKS = [
    dict(name="height", mm=5540.0, tol=12.0, how="top_z",
         part="ToriiKasagi"),
    dict(name="post_height", mm=5540.0, tol=12.0, how="bbox_z",
         part="ToriiPostR"),
    dict(name="post_base_width", mm=520.0, tol=4.0, how="bbox_x",
         part="ToriiPostR"),
    dict(name="nuki_length", mm=5400.0, tol=10.0, how="bbox_y",
         part="ToriiNuki"),
    dict(name="nuki_top_z", mm=3260.0, tol=10.0, how="top_z",
         part="ToriiNuki"),
    dict(name="kasagi_length", mm=5600.0, tol=12.0, how="bbox_y",
         part="ToriiKasagi"),
    dict(name="gaku_length", mm=1200.0, tol=6.0, how="bbox_y",
         part="ToriiGaku"),
    dict(name="gaku_height", mm=520.0, tol=4.0, how="bbox_z",
         part="ToriiGaku"),
]

SPAN = SPEC["span"] / 2.0        # 2600 mm to the centre of each post
NUKI_Z = SPEC["nuki_height"]
TOP_Z = SPEC["height"]


def post(name, s):
    """One tapered, inward-leaning upright built as a loft along Z."""
    secs = []
    steps = 8
    for i in range(steps + 1):
        t = i / float(steps)
        z = TOP_Z * t
        w = (SPEC["post_base_width"] +
             (SPEC["post_top_width"] - SPEC["post_base_width"]) * t)
        y = s * (SPAN - (SPAN - SPEC["post_top_width"] * 0.52) * t)
        ring = bkit.rounded_rect_section(w, w, w * 0.10, per_corner=3)
        secs.append([(x, yy + y, z) for (x, yy) in ring])
    ob = bkit.loft(name, secs, mat=R.cedar("ToriiCedar", base=(0.48, 0.13, 0.10)))
    bkit.recalc(ob)
    bkit.shade_smooth(ob, 26.0)
    return ob


def build():
    cedar = R.cedar("ToriiCedar", base=(0.48, 0.13, 0.10), rough=0.44)
    stone = R.basalt("ToriiStone", base=(0.26, 0.26, 0.25))
    dark = R.lacquer("ToriiLacquer", base=(0.30, 0.06, 0.05))

    # ---- stone footings: the floor datum is the footing's own underside ---
    for i, s in enumerate((1, -1)):
        bkit.rounded_box("ToriiFooting%d" % i, 780.0, 780.0, 260.0, r=24.0,
                         segments=2,
                         centre=(0.0, s * SPAN, 130.0), mat=stone)
    post("ToriiPostR", 1)
    post("ToriiPostL", -1)

    # ---- the straight lower lintel (nuki) --------------------------------
    bkit.rounded_box("ToriiNuki", 300.0, SPEC["nuki_length"], 380.0,
                     r=10.0, segments=2,
                     centre=(0.0, 0.0, NUKI_Z - 190.0), mat=dark)

    # ---- the upward-curving upper lintel (kasagi + shimaki) --------------
    # Sections along X: the z of each section follows a half sine, so the beam
    # rises `kasagi_rise` from the tips to the centre -- a real curve, not a
    # tilt. The beam is centred on 5040 mm so its crown lands at 5540 mm.
    rise = SPEC["kasagi_rise"]
    length = SPEC["kasagi_length"]
    base_z = 5040.0
    rings, shim = [], []
    steps = 26
    for i in range(steps + 1):
        t = i / float(steps)
        x = -length / 2.0 + length * t
        z = rise * math.sin(math.pi * t)
        # the cross-section lives in YZ, so it is built as a rounded rectangle
        # in XY and the loft's own x is the beam's span
        sec = bkit.rounded_rect_section(560.0, SPEC["kasagi_depth"], 40.0,
                                        per_corner=3)
        rings.append([(x, px, base_z + z + py) for (px, py) in sec])
        sec2 = bkit.rounded_rect_section(480.0, 320.0, 30.0, per_corner=3,
                                         centre=(0.0, -400.0))
        shim.append([(x, px, base_z - 250.0 + z + py) for (px, py) in sec2])
    for nm, rr, mt in (("ToriiKasagi", rings, dark),
                       ("ToriiShimaki", shim, cedar)):
        ob = bkit.loft(nm, rr, mat=mt)
        bkit.recalc(ob)
        bkit.shade_smooth(ob, 26.0)

    # ---- gaku-zuka: the short strut between the two lintels -------------
    bkit.rounded_box("ToriiGaku", 260.0, SPEC["gaku_length"], 520.0, r=10.0,
                     segments=2, centre=(0.0, 0.0, NUKI_Z + 180.0), mat=dark)

    # ---- kasagi end caps, which turn up past the posts -------------------
    for i, s in enumerate((1, -1)):
        bkit.rounded_box("ToriiCap%d" % i, 420.0, 300.0, 620.0, r=14.0,
                         segments=2,
                         centre=(0.0, s * (length / 2.0 - 120.0), 5040.0),
                         mat=dark)

    return dict(spec=SPEC, parts=11)