"""
impact_driver -- 18 V impact driver, 250 mm over the hex anvil and 232 mm tall.

An impact driver is a drill with a HEAT-GUN RIG underneath, so the proportion
that separates it from `cordless_drill` is the front third: a 54 mm hammer case
and a 12.7 mm (1/2 inch) square anvil instead of a 48 mm three-jaw chuck, and a
body 20 mm shorter. That comparison is the whole model.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    hammer_diameter=54.0,
    hammer_length=44.0,
    anvil_across_flats=12.7,
    shell_length=128.0,
    shell_width=62.0,
    battery_width=100.0,
    battery_height=58.0,
    axis_z=176.0,
    overall_height=216.0,
    overall_length=250.0,
)

CHECKS = [
    dict(name="hammer_diameter", mm=54.0, tol=0.8, how="diameter",
         part="DriverHammer"),
    dict(name="hammer_length", mm=44.0, tol=0.8, how="bbox_x",
         part="DriverHammer"),
    dict(name="anvil_across_flats", mm=12.7, tol=0.5, how="bbox_y",
         part="DriverAnvil"),
    dict(name="shell_length", mm=128.0, tol=0.8, how="bbox_x",
         part="DriverShell"),
    dict(name="battery_width", mm=100.0, tol=0.8, how="bbox_x",
         part="DriverBattery"),
    dict(name="battery_height", mm=58.0, tol=0.8, how="bbox_z",
         part="DriverBattery"),
    dict(name="overall_height", mm=216.0, tol=1.5, how="top_z",
         part="DriverShell"),
]

AZ = SPEC["axis_z"]
HX = 92.0                 # rear face of the hammer case


def build():
    orange = bkit.preset("yellow_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    grip_mat = bkit.pbr("DriverGripRubber", base=(0.07, 0.07, 0.08),
                        rough=0.62)

    shell = T.shell("DriverShell", SPEC["shell_length"], SPEC["shell_width"],
                    80.0, centre=(18.0, 0.0, AZ), r=13.0, mat=orange)
    hammer = bkit.lathe("DriverHammer",
                        [(0.0, 0.0), (27.0, 0.0), (27.0, 32.0),
                         (22.0, 44.0), (0.0, 44.0)],
                        segments=36, centre=(0, 0, 0), mat=steel)
    bkit.place(hammer, (HX, 0.0, AZ), "X")
    # a 1/2 inch square drive: two intersecting slabs read as an anvil and stay
    # a closed solid without a boolean
    bkit.rounded_box("DriverAnvil", 46.0, 12.7, 12.7, r=1.2, segments=1,
                     centre=(HX + 44.0 + 23.0, 0.0, AZ), mat=steel)
    bkit.rounded_box("DriverAnvilRib", 20.0, 20.0, 20.0, r=3.0, segments=2,
                     centre=(HX + 48.0, 0.0, AZ), mat=steel)

    T.grip("DriverGrip", (-12.0, 0.0, 144.0), (-28.0, 0.0, 56.0),
           54.0, 48.0, 48.0, 44.0, mat=grip_mat, bow=7.0)
    T.trigger("DriverTrigger", (6.0, 0.0, 142.0), (8.0, 0.0, 124.0),
              26.0, 14.0, mat=dark)
    T.shell("DriverLed", 16.0, 22.0, 12.0, centre=(66.0, 0.0, AZ - 42.0),
            r=4.0, mat=bkit.pbr("DriverLed", base=(0.9, 0.85, 0.5),
                                rough=0.2,
                                emission=(0.9, 0.85, 0.5),
                                emission_strength=2.0))
    for i, s in enumerate((1, -1)):
        T.vent_panel("DriverVent%d" % i, 3, 2, 15.0, 20.0, 4.2,
                     42.0, 40.0, 5.0, centre=(20.0, s * 30.0, AZ),
                     axis="Y", mat=dark)

    T.battery("DriverBattery", SPEC["battery_width"], 74.0,
              SPEC["battery_height"], centre=(-24.0, 0.0,
                                              SPEC["battery_height"] / 2.0),
              mat=dark)

    bkit.recalc(shell)
    return dict(spec=SPEC, parts=12)