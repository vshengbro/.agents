"""
bench_grinder -- 250 mm bench grinder, 380 mm wide, 400 mm to the top of the
wheel guard.

A bench grinder is two wheels on ONE common spindle 180 mm apart, over a cast
column. The number that fixes it is the wheel gauge: 250 mm wheels on a 380 mm
centre distance is the standard 10 inch bench machine, and the guards have to be
as big as the wheels or the silhouette collapses.

The base's underside is z = 0 and the column carries the wheel axis at z = 260,
so every part above the floor sits where a cast-iron stand would.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    wheel_diameter=250.0,
    wheel_width=32.0,
    wheel_centres=380.0,
    base_length=340.0,
    base_width=240.0,
    base_thickness=44.0,
    axis_z=260.0,
    spindle_length=420.0,
    guard_diameter=282.0,
    top_z=401.0,
)

CHECKS = [
    dict(name="wheel_diameter", mm=250.0, tol=1.0, how="bbox_x",
         part="GrindWheelL"),
    dict(name="wheel_width", mm=32.0, tol=0.8, how="bbox_y",
         part="GrindWheelL"),
    dict(name="spindle_length", mm=420.0, tol=1.5, how="bbox_y",
         part="GrindSpindle"),
    dict(name="base_length", mm=340.0, tol=1.0, how="bbox_x",
         part="GrindBase"),
    dict(name="base_width", mm=240.0, tol=1.0, how="bbox_y",
         part="GrindBase"),
    dict(name="guard_diameter", mm=282.0, tol=1.5, how="bbox_x",
         part="GrindGuardL"),
    dict(name="spindle_top_z", mm=279.0, tol=1.5, how="top_z",
         part="GrindSpindle"),
    dict(name="top_z", mm=401.0, tol=3.0, how="top_z", part=None),
]

AZ = SPEC["axis_z"]
BT = SPEC["base_thickness"]
HW = SPEC["wheel_centres"] / 2.0      # 190 mm half gauge


def build():
    cast = bkit.pbr("BenchCast", base=(0.32, 0.33, 0.35), metal=0.75,
                    rough=0.52)
    abrasive = bkit.pbr("BenchAbrasive", base=(0.26, 0.25, 0.24), rough=0.92)
    steel = bkit.preset("steel")
    dark = bkit.preset("dark_metal")
    glass = bkit.pbr("BenchShield", base=(0.72, 0.78, 0.82), rough=0.06,
                     transmission=0.72, alpha=0.6)

    # ---- cast base + column: the floor datum is the base ------------------
    T.shell("GrindBase", SPEC["base_length"], SPEC["base_width"], BT,
            centre=(0.0, 0.0, BT / 2.0), r=8.0, mat=cast)
    T.shell("GrindColumn", 150.0, 116.0, AZ - BT + 40.0,
            centre=(0.0, 0.0, BT + (AZ - BT + 40.0) / 2.0), r=18.0,
            mat=cast)
    T.shell("GrindCollar", 196.0, 150.0, 90.0, centre=(0.0, 0.0, AZ - 40.0),
            r=22.0, mat=cast)

    # ---- one spindle, two wheels -----------------------------------------
    spindle = bkit.cylinder("GrindSpindle", 19.0, 420.0, segments=28,
                            centre=(0.0, 0.0, AZ), axis="Y", mat=steel)
    wheels = []
    for i, s in enumerate((1, -1)):
        tag = "L" if s > 0 else "R"
        w = bkit.lathe("GrindWheel%s" % tag,
                       [(19.0, -16.0), (96.0, -16.0), (125.0, -12.0),
                        (125.0, 12.0), (96.0, 16.0), (19.0, 16.0),
                        (19.0, -16.0)],
                       segments=56, cap_ends=False,
                       centre=(0, 0, 0), mat=abrasive)
        # the wheel's own axis must lie along Y: `place(..., "X")` would stand
        # the disc on its edge, which is a 250 mm tall plate, not a wheel
        bkit.place(w, (0.0, s * HW, AZ), "Y")
        bkit.recalc(w)
        wheels.append(w)
        bkit.cylinder("GrindWheelHub%s" % tag, 34.0, 40.0, segments=28,
                      centre=(0.0, s * HW, AZ), axis="Y", mat=cast)
        # guard: a sheet-steel shroud over the operator's half of the wheel
        g = T.shroud("GrindGuard%s" % tag, 126.0, 141.0, 40.0,
                     0.0, 180.0, centre=(0.0, s * HW, AZ), axis="Y", mat=cast)
        # tool rest: a small cast shelf below each wheel
        bkit.rounded_box("GrindRest%s" % tag, 96.0, 30.0, 12.0, r=3.0,
                         segments=2, centre=(26.0, s * HW, AZ - 116.0),
                         mat=cast)
        bkit.rounded_box("GrindRestArm%s" % tag, 30.0, 34.0, 120.0, r=5.0,
                         segments=2, centre=(26.0, s * HW, AZ - 62.0),
                         mat=cast)
        bkit.rounded_box("GrindShield%s" % tag, 150.0, 5.0, 90.0, r=2.0,
                         segments=1, centre=(-6.0, s * (HW - 62.0),
                                             AZ - 40.0), mat=glass)
    # ---- tool tray + switch ----------------------------------------------
    T.shell("GrindTray", 260.0, 150.0, 14.0, centre=(0.0, 0.0, 78.0),
            r=6.0, mat=cast)
    T.shell("GrindSwitch", 46.0, 60.0, 40.0, centre=(96.0, 0.0, 200.0),
            r=8.0, mat=dark)
    T.knob("GrindAdjust", 26.0, 22.0, (0.0, -HW - 60.0, AZ), mat=dark)
    T.rod("GrindAdjustRod", (0.0, -HW - 60.0, AZ), (0.0, -HW + 10.0, AZ), 8.0,
          mat=steel)

    return dict(spec=SPEC, parts=17)