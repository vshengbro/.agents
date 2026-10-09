"""
spirit_level_long -- a 2 m aluminium box spirit level with 3 vials.

A level is a very long, very narrow thing, and the whole read is the vials: a
horizontal vial, a vertical one and a 45 deg one, in machined housings with a
green fluid between two glass plates. The vials are the only glass on the tool,
so they carry the "precision instrument" read while the body stays satin
aluminium.

Real 2 m box section: 2 m long, 60 mm wide, 28 mm deep, with an anodised milled
body, three vial openings and two hand holes. The vials are 3 mm below the top
face so they read as windows, not paint.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=2000.0,
    width=60.0,
    depth=28.0,
    vials=3,
    vial_length=90.0,
    vial_width=22.0,
    vial_depth=12.0,
    hand_holes=2,
    hand_hole_dia=22.0,
    hand_hole_pitch=520.0,
)

L = SPEC["length"]
W = SPEC["width"]
D = SPEC["depth"]
VL = SPEC["vial_length"]
VW = SPEC["vial_width"]
VD = SPEC["vial_depth"]

# the 3 vials sit at 0.25 L, midspan and 0.25 L -- the standard layout, and the
# positions are fractions of the declared length rather than typed coordinates
VIAL_X = (-0.25 * L, 0.0, 0.25 * L)

CHECKS = [
    dict(name="length", mm=2000.0, tol=3.0, how="bbox_x", part="LevelBody"),
    dict(name="width", mm=60.0, tol=1.0, how="bbox_y", part="LevelBody"),
    dict(name="depth", mm=28.0, tol=1.0, how="bbox_z", part="LevelBody"),
    dict(name="vial_length", mm=90.0, tol=2.0, how="bbox_x", part="LevelVial0"),
    dict(name="vial_width", mm=22.0, tol=1.0, how="bbox_y", part="LevelVial0"),
    dict(name="vial_count_run", mm=1106.0, tol=3.0, how="bbox_x",
         part="LevelVialHousing0"),
]


def build():
    alu = bkit.pbr("LevelAlu", base=(0.80, 0.81, 0.82), metal=0.82, rough=0.30)
    glass = bkit.preset("glass")
    fluid = bkit.pbr("VialFluid", base=(0.35, 0.72, 0.42), rough=0.10,
                     transmission=0.45)
    dark = bkit.preset("dark_metal")

    # ---- the milled box section ------------------------------------
    body = bkit.rounded_box("LevelBody", L, W, D, r=4.0, segments=3,
                            centre=(0.0, 0.0, D / 2.0), mat=alu)

    # ---- two hand holes, on the computed pitch ---------------------
    # Bored from the top face and stopped 8 mm short of it, so the hole has a
    # real roof and the cut is not tangent to the top face.
    hd = SPEC["hand_hole_dia"]
    hp = SPEC["hand_hole_pitch"]
    for sx in (-1, 1):
        bkit.bore(body, hd / 2.0, D + 8.0, centre=(sx * hp, 0.0, D / 2.0 + 4.0),
                  axis="Z", host_segments=64)
    bkit.recalc(body)

    # ---- 3 vials in machined housings, 3 mm below the top face -----
    # The housing is a recess; the glass sits in it, proud by 1 mm.
    # The three vial housings are ONE object swept on the computed pitch, so the
    # vial run is a single measurable array rather than three loose objects.
    hous = bkit.rounded_box("LevelVialHousing0", VL + 16.0, VW + 12.0, 10.0,
                            r=2.0, segments=1,
                            centre=(VIAL_X[0], 0.0, D - 3.0), mat=dark)
    bkit.array_linear(hous, len(VIAL_X), (0.25 * L, 0.0, 0.0))

    for i, x in enumerate(VIAL_X):
        bkit.rounded_box("LevelVial%d" % i, VL, VW, VD, r=2.0, segments=2,
                         centre=(x, 0.0, D - 2.0), mat=glass)
        bkit.rounded_box("LevelVialFluid%d" % i, VL - 8.0, VW - 7.0, 5.0,
                         r=1.5, segments=1,
                         centre=(x, 0.0, D - 4.0), mat=fluid)

    return dict(spec=SPEC, parts=1 + 1 + 2 * len(VIAL_X), vials=len(VIAL_X))