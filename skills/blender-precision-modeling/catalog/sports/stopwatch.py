"""
stopwatch -- 45 mm analogue case, 18 mm deep, with a 12-mark dial, two hands, a
side crown and a lanyard bow.

The dial is the whole read, so it gets real geometry: 12 tick marks produced by
array_radial about the dial's own axis, and two hands of different lengths and
rotations. Note the unit trap this model walks straight into: bkit.lathe
revolves about +Z, and place(..., "Y") sends that axis to world -Y, so every
profile station in this file is written in LATHE coordinates and only becomes
"toward the dial" after the rotation.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    case_diameter=45.0,
    case_depth=18.0,
    bezel_outer=43.2,
    bezel_inner=34.0,
    bezel_depth=3.4,
    dial_diameter=33.4,
    marks=12,
    crown_diameter=9.0,
    crown_projection=4.0,
    lanyard_bow=15.0,
)

CR = SPEC["case_diameter"] / 2.0        # 22.5
R_IN = SPEC["bezel_inner"] / 2.0        # 17.0
BEZEL_Y = -(9.0 - SPEC["bezel_depth"] / 2.0)   # -8.3

# Case profile in LATHE coordinates: +z is the dial side, which place("Y")
# turns into world -y. Both ends close on the axis, so this is a solid.
CASE = [
    (0.0, 9.0), (18.0, 9.0), (21.6, 8.2), (CR, 6.4),
    (CR, -3.0), (21.0, -7.2), (12.0, -8.6), (0.0, -9.0),
]

CHECKS = [
    dict(name="case_diameter", mm=45.0, tol=0.4, how="diameter",
         part="StopwatchCase"),
    dict(name="case_depth", mm=18.0, tol=0.4, how="bbox_y", part="StopwatchCase"),
    dict(name="overall_width", mm=49.0, tol=0.5, how="bbox_x"),
]


def build():
    chrome = bkit.preset("brushed_metal")
    case_mat = bkit.preset("dark_metal")
    dial = bkit.pbr("DialFace", base=(0.93, 0.93, 0.90), rough=0.30)
    ink = bkit.preset("black_plastic")

    # ---- case: a turned barrel, dial toward -y --------------------------
    # lathe() does not recalc, and a profile that runs dial-end first comes
    # out with inward normals, so the solid is re-oriented explicitly.
    case = bkit.lathe("StopwatchCase", CASE, segments=72, mat=case_mat)
    bkit.recalc(case)
    bkit.place(case, (0.0, 0.0, 0.0), "Y")

    # ---- bezel: bkit.tube, NOT a lathe. lathe() caps a profile whose end
    # ---- radii are non-zero with a FULL disc, so a ring profile revolved by
    # ---- lathe comes out with a solid disc across the hole -- coplanar with
    # ---- the dial, and the two z-fight into a faceted mess.
    bezel = bkit.tube("Bezel", SPEC["bezel_outer"] / 2.0, R_IN,
                     SPEC["bezel_depth"], segments=72,
                     centre=(0.0, BEZEL_Y, 0.0), axis="Y", mat=chrome)

    # ---- dial disc: tucked under the bezel's inner wall, not flush with it
    face = bkit.cylinder("DialFace", 16.7, 1.2, segments=64,
                         centre=(0.0, -9.4, 0.0), axis="Y", mat=dial,
                         smooth=False)

    # ---- 12 dial marks, arrayed radially about the dial axis -------------
    # array_radial's offset is empty.matrix_world.inverted() @ obj.matrix_world
    # and Blender applies it CUMULATIVELY, so a rotation and a translation in
    # the same matrix make the copies spiral outwards. The radius therefore
    # has to live in the MESH with the object origin on the array centre --
    # placing the mark with centre=() or bkit.move() instead scatters it.
    tick = bkit.mesh_from("DialMark", [
        (12.0, -10.35, -0.65), (16.0, -10.35, -0.65),
        (16.0, -9.85, -0.65), (12.0, -9.85, -0.65),
        (12.0, -10.35, 0.65), (16.0, -10.35, 0.65),
        (16.0, -9.85, 0.65), (12.0, -9.85, 0.65),
    ], [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], mat=ink)
    bkit.array_radial(tick, SPEC["marks"], axis="Y")

    # ---- hands: long second hand, short minute hand, both about the pin ---
    second = bkit.rounded_box("SecondHand", 2.0, 0.5, 34.0, r=0.2, segments=2,
                              centre=(0.0, -10.6, 0.0), mat=ink)
    second.rotation_euler = (0.0, math.radians(28.0), 0.0)
    bkit.move(second, 0.0, 0.0, 0.0)          # also refreshes matrix_world
    minute = bkit.rounded_box("MinuteHand", 3.0, 0.5, 24.0, r=0.2,
                              segments=2, centre=(0.0, -10.2, 0.0), mat=ink)
    minute.rotation_euler = (0.0, math.radians(-52.0), 0.0)
    bkit.move(minute, 0.0, 0.0, 0.0)
    pin = bkit.cylinder("HandPin", 1.8, 1.6, segments=16,
                        centre=(0.0, -9.5, 0.0), axis="Y", mat=chrome)

    # ---- crown and lanyard bow, both dimensioned off the case radius ------
    crown = bkit.cylinder("Crown", SPEC["crown_diameter"] / 2.0,
                          SPEC["crown_projection"] + 2.0, segments=28,
                          centre=(CR + SPEC["crown_projection"] / 2.0 - 1.0,
                                  1.0, 0.0), axis="X", mat=chrome)
    bow = bkit.torus("LanyardBow", 7.0, 1.6, seg_major=40, seg_minor=12,
                     centre=(0.0, 2.0, 24.0), axis="X", mat=chrome)
    return dict(spec=SPEC, parts=8)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
