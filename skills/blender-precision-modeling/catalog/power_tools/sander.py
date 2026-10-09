"""
sander -- 125 mm random orbital sander: 250 mm long, 176 mm tall, on a 125 mm
pad.

The proportion that decides a sander is the pad against the motor: a 125 mm
pad under a 92 mm motor barrel, with a 44 mm dust port behind. The pad's
underside is z = 0 and it carries a real perforated extraction plate, because
an orbital sander with no dust holes reads as a polisher.

The body is one `lathe` and the palm grip is a `superellipse_section` loft, so
the whole tool is turned forms rather than boxes.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    pad_diameter=125.0,
    pad_thickness=22.0,
    motor_diameter=92.0,
    motor_length=170.0,
    body_height=157.0,
    dust_port_diameter=62.0,
    dust_bag_diameter=110.0,
    exhaust_holes=8,
)

CHECKS = [
    dict(name="pad_diameter", mm=125.0, tol=0.8, how="diameter",
         part="SanderPad"),
    dict(name="pad_thickness", mm=22.0, tol=0.8, how="bbox_z",
         part="SanderPad"),
    dict(name="motor_diameter", mm=92.0, tol=0.8, how="bbox_z",
         part="SanderMotor"),
    dict(name="motor_length", mm=170.0, tol=1.0, how="bbox_x",
         part="SanderMotor"),
    dict(name="body_height", mm=157.0, tol=2.0, how="top_z", part=None),
    dict(name="dust_port_diameter", mm=62.0, tol=0.8, how="bbox_y",
         part="SanderDustPort"),
    dict(name="dust_bag_diameter", mm=110.0, tol=1.5, how="diameter",
         part="SanderDustBag"),
]

PZ = 16.0                  # pad thickness; the pad's underside is z = 0
MZ = PZ + 56.0             # motor axis height


def build():
    teal = bkit.preset("blue_paint")
    dark = bkit.preset("black_plastic")
    rubber = bkit.preset("rubber")
    grip_mat = bkit.pbr("SanderGripRubber", base=(0.08, 0.08, 0.09),
                        rough=0.66)

    # ---- pad: rubber skirt + a real perforated extraction plate -----------
    bkit.lathe("SanderPad",
               [(0.0, 0.0), (62.5, 0.0), (62.5, PZ), (48.0, PZ + 6.0),
                (0.0, PZ + 6.0)],
               segments=52, centre=(0.0, 0.0, 0.0), mat=rubber)
    T.vent_panel("SanderExtraction", SPEC["exhaust_holes"], 1, 14.0, 14.0,
                 3.6, 96.0, 12.0, 5.0, centre=(0.0, 0.0, PZ + 1.0),
                 mat=dark)

    # ---- motor barrel + head ----------------------------------------------
    motor = bkit.lathe("SanderMotor",
                       [(0.0, 0.0), (46.0, 0.0), (46.0, 152.0),
                        (38.0, 170.0), (0.0, 170.0)],
                       segments=44, centre=(0, 0, 0), mat=teal)
    bkit.place(motor, (18.0, 0.0, MZ), "X")
    T.vent_panel("SanderVent", 5, 2, 14.0, 16.0, 3.6, 60.0, 28.0, 5.0,
                 centre=(-46.0, 0.0, MZ), axis="X", mat=dark)

    # ---- palm grip: a lofted dome over the barrel -------------------------
    rings = []
    for i in range(9):
        t = i / 8.0
        rings.append([(18.0 - 30.0 * t + px, py, MZ + 58.0 + 24.0 * t)
                      for (px, py) in
                      bkit.superellipse_section(104.0 - 58.0 * t,
                                                92.0 - 46.0 * t,
                                                n=2.6, steps=40)])
    dome = bkit.loft("SanderPalmGrip", rings, mat=grip_mat)
    bkit.recalc(dome)
    bkit.shade_smooth(dome, 40.0)

    # ---- switch + dust port + bag ----------------------------------------
    T.shell("SanderSwitch", 34.0, 34.0, 22.0, centre=(58.0, 0.0, MZ + 74.0),
            r=8.0, mat=dark)
    bkit.tube("SanderDustPort", 31.0, 25.0, 40.0, segments=32,
              centre=(-104.0, 0.0, MZ + 6.0), axis="X", mat=dark)
    bag = bkit.lathe("SanderDustBag",
                     [(25.0, 0.0), (55.0, 26.0), (55.0, 54.0),
                      (30.0, 88.0), (26.0, 88.0), (49.0, 52.0),
                      (49.0, 28.0), (25.0, 0.0)],
                     segments=36, cap_ends=False,
                     centre=(0, 0, 0), mat=bkit.pbr("SanderBag",
                                                    base=(0.20, 0.21, 0.23),
                                                    rough=0.88))
    bkit.place(bag, (-124.0, 0.0, MZ + 6.0), "X")

    return dict(spec=SPEC, parts=8)