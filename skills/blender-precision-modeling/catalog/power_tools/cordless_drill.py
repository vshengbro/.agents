"""
cordless_drill -- 18 V cordless drill/driver, 296 mm over the bit and 226 mm tall.

Three numbers describe the machine: the chuck, the slide-on pack and the tool
axis they share. The chuck is a 44 mm three-jaw with a real bore (a closed
profile revolved, so the jaws open into a hole rather than onto a disc), the
pack is a 110 x 78 x 64 slide-on case whose UNDERSIDE is z = 0, and the whole
gear train runs on one horizontal axis at z = 185. The pack is the floor
datum: it is what `sit_on_floor()` finds, so every `top_z` in CHECKS is the
number that was authored.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    chuck_diameter=44.0,
    chuck_length=36.0,
    shell_length=140.0,
    shell_width=64.0,
    battery_width=110.0,
    battery_depth=78.0,
    battery_height=64.0,
    bit_diameter=6.0,
    axis_z=185.0,
    overall_height=226.0,
    overall_length=296.0,
)

CHECKS = [
    dict(name="chuck_diameter", mm=44.0, tol=0.6, how="bbox_y",
         part="DrillChuck"),
    dict(name="chuck_length", mm=36.0, tol=0.6, how="bbox_x",
         part="DrillChuck"),
    dict(name="shell_length", mm=140.0, tol=0.8, how="bbox_x",
         part="DrillShell"),
    dict(name="battery_width", mm=110.0, tol=0.8, how="bbox_x",
         part="DrillBattery"),
    dict(name="battery_height", mm=64.0, tol=0.8, how="bbox_z",
         part="DrillBattery"),
    dict(name="bit_diameter", mm=6.0, tol=0.5, how="bbox_y",
         part="DrillBit"),
    dict(name="overall_height", mm=226.0, tol=1.2, how="top_z",
         part="DrillShell"),
]

AZ = SPEC["axis_z"]          # the tool axis height
CB_X = 115.0                 # rear face of the chuck assembly


def build():
    yellow = bkit.preset("yellow_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    grip_mat = bkit.pbr("DrillGripRubber", base=(0.07, 0.07, 0.08),
                        rough=0.62)

    # ---- housing: motor shell over a raked grip -----------------------------
    shell = T.shell("DrillShell", SPEC["shell_length"], SPEC["shell_width"],
                    82.0, centre=(25.0, 0.0, AZ), r=13.0, mat=yellow)
    gearcase = bkit.cylinder("DrillGearcase", 31.0, 40.0, segments=40,
                             centre=(95.0, 0.0, AZ), axis="X", mat=dark)
    T.grip("DrillGrip", (-6.0, 0.0, 152.0), (-22.0, 0.0, 62.0),
           56.0, 48.0, 50.0, 44.0, mat=grip_mat, bow=7.0)
    T.trigger("DrillTrigger", (14.0, 0.0, 150.0), (16.0, 0.0, 132.0),
              26.0, 14.0, mat=dark)

    # vents: one real perforated panel per flank, on a computed hole grid
    for i, s in enumerate((1, -1)):
        T.vent_panel("DrillVent%d" % i, 4, 2, 15.0, 20.0, 4.4,
                     58.0, 40.0, 5.0,
                     centre=(30.0, s * 31.0, AZ + 2.0), axis="Y", mat=dark)

    # ---- chuck: a closed revolved profile, so the jaws open into a bore ----
    chuck = bkit.lathe("DrillChuck",
                       [(9.0, 0.0), (22.0, 0.0), (22.0, 10.0),
                        (20.0, 30.0), (14.0, 36.0), (9.0, 36.0), (9.0, 0.0)],
                       segments=48, cap_ends=False, mat=steel)
    bkit.place(chuck, (CB_X, 0.0, AZ), "X")
    bkit.bore(chuck, 9.0, 40.0, centre=(CB_X + 20.0, 0.0, AZ), axis="X",
              host_segments=48)
    bkit.tube("DrillCollar", 26.0, 21.5, 14.0, segments=40,
              centre=(CB_X - 7.0, 0.0, AZ), axis="X", mat=dark)

    # ---- bit ----------------------------------------------------------------
    bit = bkit.lathe("DrillBit",
                     [(0.0, 0.0), (3.0, 0.0), (3.0, 46.0),
                      (1.6, 62.0), (0.0, 70.0)],
                     segments=32, centre=(0, 0, 0), mat=steel)
    bkit.place(bit, (CB_X + 20.0, 0.0, AZ), "X")

    # ---- pack: the floor datum, underside at z = 0 --------------------------
    T.battery("DrillBattery", SPEC["battery_width"], SPEC["battery_depth"],
              SPEC["battery_height"], centre=(-20.0, 0.0,
                                              SPEC["battery_height"] / 2.0),
              mat=dark)

    bkit.recalc(shell)
    return dict(spec=SPEC, parts=11)