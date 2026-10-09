"""
wood_router -- 710 W plunge router, 290 mm tall on a 102 mm base.

A router is judged on its base and its collet. The base is a 102 mm disc with a
REAL central bore -- the bit has to reach through it -- and the base's underside
is z = 0, so the router stands on its own sole rather than on its bit. The
model is built with the collet retracted, which is why the bit tip sits at
z = 6 and nothing pokes below the base.

The two side handles and the top D-handle are the ergonomic signature; they are
all `grip()` lofts so they share one language with the drill.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    base_diameter=102.0,
    base_thickness=18.0,
    bore_diameter=28.0,
    motor_diameter=90.0,
    motor_height=160.0,
    collet_diameter=36.0,
    bit_diameter=12.0,
    bit_length=70.0,
    overall_height=293.0,
    handle_span=150.0,
)

CHECKS = [
    dict(name="base_diameter", mm=102.0, tol=0.8, how="diameter",
         part="RouterBase"),
    dict(name="base_thickness", mm=18.0, tol=0.6, how="bbox_z",
         part="RouterBase"),
    dict(name="motor_diameter", mm=90.0, tol=0.8, how="diameter",
         part="RouterMotor"),
    dict(name="motor_height", mm=160.0, tol=1.0, how="bbox_z",
         part="RouterMotor"),
    dict(name="collet_diameter", mm=36.0, tol=0.8, how="diameter",
         part="RouterCollet"),
    dict(name="bit_diameter", mm=12.0, tol=0.6, how="diameter",
         part="RouterBit"),
    dict(name="bit_length", mm=70.0, tol=0.8, how="bbox_z", part="RouterBit"),
    dict(name="handle_span", mm=150.0, tol=1.5, how="bbox_x",
         part="RouterTopHandle"),
    dict(name="overall_height", mm=293.0, tol=2.0, how="top_z",
         part="RouterTopHandle"),
]


def build():
    teal = bkit.preset("blue_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    cast = bkit.pbr("RouterCast", base=(0.52, 0.53, 0.55), metal=0.80,
                    rough=0.44)
    grip_mat = bkit.pbr("RouterGripRubber", base=(0.07, 0.07, 0.08),
                        rough=0.62)
    acrylic = bkit.pbr("RouterAcrylic", base=(0.80, 0.84, 0.86),
                       rough=0.10, transmission=0.55)

    # ---- base: a real bore, and the sole at z = 0 --------------------------
    bkit.tube("RouterBase", 51.0, 14.0, SPEC["base_thickness"], segments=64,
              centre=(0.0, 0.0, SPEC["base_thickness"] / 2.0), mat=cast)
    bkit.tube("RouterSole", 54.0, 46.0, 6.0, segments=64,
              centre=(0.0, 0.0, 3.0), mat=acrylic)
    bkit.tube("RouterBore", 26.0, 14.0, 18.0, segments=48,
              centre=(0.0, 0.0, SPEC["base_thickness"] / 2.0), mat=dark)

    # ---- motor: a 90 mm barrel in a cast turret ---------------------------
    motor = bkit.lathe("RouterMotor",
                       [(0.0, 0.0), (45.0, 0.0), (45.0, 146.0),
                        (40.0, 160.0), (0.0, 160.0)],
                       segments=44, centre=(0, 0, 0), mat=teal)
    bkit.place(motor, (0.0, 0.0, 20.0))
    bkit.lathe("RouterTurret",
               [(46.0, 0.0), (58.0, 0.0), (58.0, 54.0), (46.0, 54.0),
                (46.0, 0.0)],
               segments=44, cap_ends=False, centre=(0.0, 0.0, 62.0), mat=cast)
    T.vent_panel("RouterVent", 5, 3, 15.0, 14.0, 4.0, 70.0, 40.0, 5.0,
                 centre=(0.0, 44.0, 130.0), axis="Y", mat=dark)

    # ---- collet + bit, retracted into the base bore -----------------------
    bkit.lathe("RouterCollet",
               [(0.0, 0.0), (18.0, 0.0), (18.0, 20.0), (14.0, 26.0),
                (7.0, 26.0), (7.0, 0.0), (0.0, 0.0)],
               segments=32, cap_ends=False, centre=(0.0, 0.0, 22.0),
               mat=steel)
    bit = bkit.lathe("RouterBit",
                     [(0.0, 0.0), (6.0, 0.0), (6.0, 52.0), (3.2, 58.0),
                      (3.2, 70.0), (0.0, 70.0)],
                     segments=28, centre=(0.0, 0.0, 0.0), mat=steel)
    bkit.move(bit, 0.0, 0.0, 6.0)

    # ---- speed dial + plunge lock -----------------------------------------
    T.knob("RouterSpeedDial", 24.0, 26.0, (0.0, 0.0, 196.0), mat=dark)
    T.shell("RouterLock", 46.0, 30.0, 26.0, centre=(0.0, -56.0, 88.0),
            r=8.0, mat=dark)

    # ---- the three handles -------------------------------------------------
    for i, s in enumerate((1, -1)):
        T.rod("RouterHandleStem%d" % i, (0.0, s * 48.0, 88.0),
              (0.0, s * 96.0, 96.0), 9.0, mat=cast)
        T.grip("RouterSideHandle%d" % i, (0.0, s * 92.0, 96.0),
               (0.0, s * 178.0, 106.0), 44.0, 44.0, 40.0, 40.0,
               mat=grip_mat, bow=5.0)
    bkit.arc_torus("RouterTopHandle", 62.0, 13.0, -14.0, 194.0,
                   centre=(0.0, 0.0, 218.0), plane="XZ", seg_major=32,
                   mat=grip_mat)

    return dict(spec=SPEC, parts=12)