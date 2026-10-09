"""
dumbbell -- 5 kg hex dumbbell, 280 mm overall: knurled 28 mm grip between two
chamfered hexagonal heads.

A dumbbell is three turned parts and two prisms. The grip profile is generated
as a knurl (a real periodic relief, not a smooth cylinder), the heads are
hexagonal because that is what stops a dumbbell rolling on a gym floor, and
the head position comes from the head length plus the exposed grip length --
not from two hand-typed x coordinates.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=280.0,
    head_length=100.0,
    head_across_flats=100.0,
    head_across_corners=115.5,
    grip_diameter=28.0,
    grip_knurl_diameter=29.8,   # the knurl stands 0.9 mm proud of the bar
    grip_length=80.0,          # exposed bar between the heads
    grip_turns=19,
)

HL = SPEC["head_length"]            # 100
HALF_TOTAL = SPEC["overall_length"] / 2.0    # 140
X_HEAD = HALF_TOTAL - HL / 2.0      # 90
R_HEAD = (SPEC["head_across_flats"] / 2.0) / math.cos(math.radians(30.0))
# the bar is the exposed grip plus 30 mm of overlap into each head
BAR_LEN = SPEC["grip_length"] + 60.0            # 140 -> +/-70

CHECKS = [
    dict(name="overall_length", mm=280.0, tol=0.5, how="bbox_x", part="Dumbbell"),
    # the hex prism is laid out so its FLATS face +/-z and its CORNERS face
    # +/-y, which makes both across-flats and across-corners directly
    # measurable from the bounding box
    dict(name="head_across_flats", mm=100.0, tol=0.5, how="bbox_z",
         part="Dumbbell"),
    dict(name="head_across_corners", mm=114.1, tol=0.5, how="bbox_y",
         part="Dumbbell"),
]


def build():
    steel = bkit.preset("brushed_metal")
    knurl = bkit.pbr("KnurledBar", base=(0.55, 0.56, 0.58), rough=0.42)
    paint = bkit.pbr("DumbbellCoat", base=(0.16, 0.17, 0.19), rough=0.44)

    # ---- grip: a turned bar with a real knurl period ----------------------
    # four samples per knurl turn, so the crests land on the samples exactly.
    # the profile is centred on the lathe axis: bkit.lathe builds from z = 0
    # outward, and place(..., "X") only rotates, so an off-centre profile ends
    # up half inside one head with its pole tangent to the other's face.
    rg = SPEC["grip_diameter"] / 2.0
    n = 4 * SPEC["grip_turns"]
    hz = BAR_LEN / 2.0
    prof = [(0.0, -hz), (rg, -hz)]
    for i in range(n + 1):
        z = -hz + 8.0 + (BAR_LEN - 16.0) * i / n
        prof.append((rg + 0.9 * math.sin(2.0 * math.pi * SPEC["grip_turns"]
                                         * i / n), z))
    prof += [(rg, hz), (0.0, hz)]
    grip = bkit.lathe("DumbbellGrip", prof, segments=64, mat=knurl)
    bkit.place(grip, (0.0, 0.0, 0.0), axis="X")

    # ---- two hexagonal heads, chamfered so the flats read as cast --------
    hex_pts = [(R_HEAD * math.cos(math.radians(30.0 + 60.0 * i)),
                R_HEAD * math.sin(math.radians(30.0 + 60.0 * i)))
               for i in range(6)]
    head = bkit.extrude_profile("DumbbellHead", hex_pts, HL,
                                centre=(X_HEAD, 0.0, 0.0), axis="X", mat=paint)
    bkit.bevel(head, width_mm=2.6, segments=2, angle_deg=25)
    # duplicate() sets an ABSOLUTE location AND resets rotation_euler to
    # identity unless rot_deg is given, so the head's axis has to be restated
    # or the copy stands up on end like a coin.
    head2 = bkit.duplicate(head, "DumbbellHeadB",
                           offset_mm=(-X_HEAD, 0.0, 0.0),
                           rot_deg=(0.0, 90.0, 0.0))
    bkit.bevel(head2, width_mm=2.6, segments=2, angle_deg=25)

    dumbbell = bkit.join([grip, head, head2], name="Dumbbell")
    return dict(spec=SPEC, parts=1)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
