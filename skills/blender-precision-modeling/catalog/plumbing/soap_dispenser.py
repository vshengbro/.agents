"""
soap_dispenser -- pump bottle: lathed bottle with a real 2 mm wall, a collar,
a pump stem, and a bent nozzle.

100 x 62 x 168 mm with a 12 ml dose. The parts that sell it as a soap
dispenser and not a bottle: the stepped collar, the exposed 25 mm stem, and the
nozzle that bends 90 degrees out over the sink.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=62.0,
    body_height=104.0,
    wall=2.0,
    neck_diameter=24.0,
    collar_diameter=34.0,
    collar_height=14.0,
    stem_diameter=9.0,
    stem_height=25.0,
    nozzle_diameter=8.0,
    nozzle_length=32.0,
    overall_height=168.0,
)

BR = SPEC["body_diameter"] / 2.0
BH = SPEC["body_height"]
WALL = SPEC["wall"]
COL_H = SPEC["collar_height"]
STEM_H = SPEC["stem_height"]


def build():
    body_mat = bkit.pbr("SoapBottle", base=(0.86, 0.87, 0.86), rough=0.14,
                        coat=0.5)
    pump_mat = bkit.pbr("SoapPump", base=(0.78, 0.79, 0.80), metal=0.85,
                        rough=0.22)

    # ---- bottle: one lathe, wall real, base thick -------------------------
    # Profile walks the underside, up the outside, in over the shoulder, down
    # the neck, and back up the inside to the axis -- the same walk as a mug,
    # so the 2 mm wall and the 5 mm base are actual geometry.
    prof = [
        (0.0, 0.0),
        (BR - 1.5, 0.0),
        (BR, 1.5),                               # rounded base edge
        (BR, BH - 26.0),                         # straight side
        (BR - 5.0, BH - 8.0),                    # shoulder
        (SPEC["neck_diameter"] / 2.0 + 2.0, BH),
        (SPEC["neck_diameter"] / 2.0, BH + 3.0),  # neck
        (SPEC["neck_diameter"] / 2.0, BH + 8.0),
        (SPEC["neck_diameter"] / 2.0 + WALL, BH + 6.0),   # over the neck rim
        (SPEC["neck_diameter"] / 2.0 + WALL, BH + 1.0),   # down the inside
        (BR - 8.0, BH - 12.0),                   # inner shoulder
        (BR - WALL, BH - 30.0),
        (BR - WALL, 5.0),                        # down the inside wall
        (BR - WALL - 1.5, 5.0),
        (0.0, 5.0),                              # across the inner floor
    ]
    bottle = bkit.lathe("SoapBottle", prof, segments=72, mat=body_mat)

    # ---- collar: the screw ring that locks the pump in --------------------
    collar = bkit.lathe("SoapCollar", [
        (0.0, 0.0), (SPEC["collar_diameter"] / 2.0, 0.0),
        (SPEC["collar_diameter"] / 2.0, COL_H - 4.0),
        (SPEC["collar_diameter"] / 2.0 - 5.0, COL_H),
        (0.0, COL_H),
    ], segments=64, mat=pump_mat)
    bkit.move(collar, 0.0, 0.0, BH + 8.0 - 2.0)

    # ---- pump head: the stem, and a nozzle bending forward over the sink --
    z0 = BH + 8.0 + COL_H - 2.0
    stem = bkit.lathe("SoapStem", [
        (0.0, 0.0), (SPEC["stem_diameter"] / 2.0, 0.0),
        (SPEC["stem_diameter"] / 2.0, STEM_H),
        (13.0, STEM_H + 4.0), (13.0, STEM_H + 12.0),
        (0.0, STEM_H + 12.0),
    ], segments=40, mat=pump_mat)
    bkit.move(stem, 0.0, 0.0, z0 - 2.0)

    # A 90 degree bend in the YZ plane: it leaves the head travelling UP along
    # +Z and leaves the arc travelling FORWARD along +Y, so the outlet
    # overhangs the sink. Swept 90 -> 0 rather than mirrored: `mirror` copies
    # the end caps onto the seam and leaks one non-manifold edge per segment.
    R = SPEC["nozzle_length"] - 4.0
    noz = bkit.arc_torus("SoapNozzle", R, 4.0, 90.0, 0.0,
                         centre=(0.0, 0.0, 0.0), plane="YZ",
                         seg_major=20, seg_minor=14, mat=pump_mat, caps=True)
    # The arc's +Z end is at z = +R; drop it so that end meets the stem top.
    top_z = z0 - 2.0 + STEM_H + 12.0
    bkit.move(noz, 0.0, 0.0, top_z - R)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="body_diameter", mm=62.0, tol=0.3, how="diameter", part="SoapBottle"),
    # The lathe runs on to the neck, so bbox_z of the whole bottle includes it:
    # 104 body + 8 neck.
    dict(name="body_height_with_neck", mm=112.0, tol=0.3, how="bbox_z",
         part="SoapBottle"),
    dict(name="collar_diameter", mm=34.0, tol=0.3, how="diameter",
         part="SoapCollar"),
    dict(name="overall_height", mm=163.0, tol=0.6, how="bbox_z"),
    dict(name="nozzle_reach", mm=32.0, tol=0.6, how="bbox_y", part="SoapNozzle"),
]
