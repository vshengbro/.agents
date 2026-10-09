"""
angle_grinder -- 125 mm angle grinder, 300 mm over the spindle and 250 mm tall.

An angle grinder is a motor barrel, a right-angle gear head and a wheel, and the
proportion that makes it read is the head: a 92 mm gearbox on a 66 mm barrel.
The wheel sits on the spindle at z = 90 with its face parallel to the tool
axis, so the disc is revolved in its own plane and stood on its edge -- an
angle grinder whose disc lies flat is a cut-off saw, not a grinder.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    wheel_diameter=125.0,
    wheel_thickness=6.0,
    guard_diameter=132.0,
    head_diameter=92.0,
    barrel_diameter=66.0,
    overall_length=300.0,
    spindle_diameter=14.0,
    side_handle_diameter=40.0,
    # the top of the switch -- the tallest thing on the tool's own centreline,
    # since the side handle rakes up and carries the assembly to 157.6 mm
    top_z=117.0,
)

CHECKS = [
    dict(name="wheel_diameter", mm=125.0, tol=0.8, how="diameter",
         part="GrindWheel"),
    dict(name="wheel_thickness", mm=6.0, tol=0.5, how="bbox_x",
         part="GrindWheel"),
    dict(name="guard_diameter", mm=132.0, tol=1.0, how="longest",
         part="GrindGuard"),
    dict(name="head_diameter", mm=92.0, tol=1.0, how="bbox_y",
         part="GrindHead"),
    dict(name="barrel_diameter", mm=66.0, tol=0.8, how="bbox_y",
         part="GrindBarrel"),
    dict(name="spindle_diameter", mm=14.0, tol=0.5, how="bbox_y",
         part="GrindSpindle"),
    dict(name="side_handle_diameter", mm=40.0, tol=1.5, how="bbox_x",
         part="GrindSideHandle"),
    dict(name="switch_top_z", mm=117.0, tol=1.5, how="top_z",
         part="GrindSwitch"),
]

# The tool axis sits 66 mm above the floor so the GUARD is what rests on the
# bench -- which is how an angle grinder is actually set down, and it makes the
# guard's lowest point z = 0 so `sit_on_floor()` is a no-op and every `top_z`
# below is the authored number.
WZ = 66.0


def build():
    orange = bkit.preset("red_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    cast = bkit.pbr("GrindCast", base=(0.52, 0.53, 0.55), metal=0.80,
                    rough=0.46)
    abrasive = bkit.pbr("GrindAbrasive", base=(0.22, 0.21, 0.21),
                        rough=0.90)
    grip_mat = bkit.pbr("GrindGripRubber", base=(0.07, 0.07, 0.08),
                        rough=0.62)

    # ---- wheel, revolved flat then stood on its edge ----------------------
    wheel = bkit.lathe("GrindWheel",
                       [(11.0, -3.0), (52.0, -3.0), (62.5, -1.6),
                        (62.5, 1.6), (52.0, 3.0), (11.0, 3.0), (11.0, -3.0)],
                       segments=48, cap_ends=False, mat=abrasive, smooth=False)
    bkit.place(wheel, (18.0, 0.0, WZ), "X")
    bkit.cylinder("GrindWheelLabel", 52.0, 6.4, segments=48,
                  centre=(18.0, 0.0, WZ), axis="X", mat=steel)

    # ---- guard: a half-cowl over the operator's half of the wheel ---------
    # The cowl's own radius (63..66) and sweep (0..186 deg) are what the
    # `guard_diameter` check measures and what puts its lowest point on z=0,
    # so they are unchanged. What was wrong is the WIDTH: at 66 mm the cowl
    # reached from x=-21 to x=45 while the wheel is a 6 mm disc at x=15..21,
    # so 36 mm of unsupported cowl projected ahead of the wheel with nothing
    # inside it and read as two detached blades. A real guard is a narrow
    # cowl on the wheel plus a formed arm that clamps the gear head, and both
    # parts are modelled that way here.
    guard = T.shroud("GrindGuard", 63.0, 66.0, 40.0, 0.0, 186.0,
                     centre=(25.0, 0.0, WZ), axis="X", mat=cast)
    # the arm: bridges the cowl (x 5..45) to the gear-head neck at r=33
    # (x 56..70), so the guard is held by the tool instead of floating on it
    T.shroud("GrindGuardArm", 30.0, 66.0, 23.0, 25.0, 55.0,
             centre=(46.5, 0.0, WZ), axis="X", mat=cast)

    # ---- spindle + right-angle head ---------------------------------------
    bkit.cylinder("GrindSpindle", SPEC["spindle_diameter"] / 2.0, 46.0,
                  segments=24, centre=(30.0, 0.0, WZ), axis="X", mat=steel)
    head = bkit.lathe("GrindHead",
                      [(0.0, -46.0), (46.0, -46.0), (46.0, -6.0),
                       (33.0, 4.0), (33.0, 18.0), (0.0, 18.0)],
                      segments=40, centre=(0, 0, 0), mat=cast)
    bkit.place(head, (74.0, 0.0, WZ), "X")

    # ---- motor barrel ------------------------------------------------------
    barrel = bkit.lathe("GrindBarrel",
                        [(0.0, 0.0), (33.0, 0.0), (33.0, 196.0),
                         (28.0, 214.0), (0.0, 214.0)],
                        segments=40, centre=(0, 0, 0), mat=orange)
    bkit.place(barrel, (85.0, 0.0, WZ), "X")
    T.vent_panel("GrindVent", 5, 2, 14.0, 16.0, 3.6, 60.0, 28.0, 5.0,
                 centre=(250.0, 0.0, WZ), axis="X", mat=dark)

    # ---- spindle lock + switch ---------------------------------------------
    bkit.cylinder("GrindSpindleLock", 16.0, 26.0, segments=20,
                  centre=(76.0, 0.0, WZ + 38.0), mat=dark)
    T.shell("GrindSwitch", 56.0, 40.0, 26.0, centre=(238.0, 0.0, WZ + 38.0),
            r=8.0, mat=dark)

    # ---- side handle: a real auxiliary grip on a threaded stem -------------
    T.rod("GrindHandleStem", (74.0, 34.0, WZ + 20.0),
          (74.0, 62.0, WZ + 44.0), 9.0, mat=steel)
    T.grip("GrindSideHandle", (74.0, 60.0, WZ + 46.0),
           (74.0, 128.0, WZ + 74.0), 40.0, 40.0, 38.0, 38.0,
           mat=grip_mat, bow=4.0)

    # ---- cord --------------------------------------------------------------
    T.coiled_cord("GrindCord", (306.0, 0.0, WZ + 34.0), 26.0, 5.0, 20.0, 340.0)
    T.rod("GrindCordTail", (326.0, 20.0, WZ + 8.0), (352.0, -12.0, WZ - 24.0),
          5.0)

    return dict(spec=SPEC, parts=12)