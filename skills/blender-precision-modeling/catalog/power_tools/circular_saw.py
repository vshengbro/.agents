"""
circular_saw -- 185 mm corded circular saw, 300 mm shoe, 272 mm to the top of
the D-handle.

The proportion that makes a circular saw read is the guard against the shoe: a
185 mm blade wears a shroud about 206 mm across, and that shroud has to sit on
a shoe that is nearly as wide. A guard narrower than the base plate is the
single most common way a circular saw comes out wrong, so both numbers are
declared and the guard is built with `shroud()` -- a real annular half-cowl,
because a lathe cannot revolve less than a full turn.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    blade_diameter=185.0,
    blade_width=1.8,
    guard_diameter=206.0,
    guard_width=100.0,
    shoe_length=300.0,
    shoe_width=168.0,
    shoe_thickness=9.0,
    motor_diameter=104.0,
    handle_height=272.0,
    blade_axis_z=105.0,
)

CHECKS = [
    dict(name="blade_diameter", mm=185.0, tol=1.0, how="diameter",
         part="SawBlade"),
    dict(name="guard_diameter", mm=206.0, tol=1.0, how="diameter",
         part="SawGuard"),
    dict(name="guard_width", mm=100.0, tol=1.0, how="bbox_y", part="SawGuard"),
    dict(name="shoe_length", mm=300.0, tol=1.0, how="bbox_x", part="SawShoe"),
    dict(name="shoe_width", mm=168.0, tol=1.0, how="bbox_y", part="SawShoe"),
    dict(name="motor_diameter", mm=104.0, tol=1.5, how="bbox_x",
         part="SawMotor"),
    dict(name="handle_height", mm=272.0, tol=2.0, how="top_z",
         part="SawHandle"),
]

BX, BZ = 10.0, SPEC["blade_axis_z"]


def build():
    orange = bkit.preset("red_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    cast = bkit.pbr("SawCast", base=(0.55, 0.56, 0.58), metal=0.80, rough=0.44)
    grip_mat = bkit.pbr("SawGripRubber", base=(0.07, 0.07, 0.08), rough=0.62)

    # ---- sole plate: the floor datum, underside at z = 0 --------------------
    T.shell("SawShoe", SPEC["shoe_length"], SPEC["shoe_width"],
            SPEC["shoe_thickness"], centre=(0.0, 0.0,
                                            SPEC["shoe_thickness"] / 2.0),
            r=3.0, mat=steel, segments=2)
    bkit.rounded_box("SawSlot", 26.0, 104.0, 6.0, r=2.0, segments=1,
                     centre=(BX, 0.0, 6.0), mat=dark)

    # ---- blade + arbor ------------------------------------------------------
    blade = T.saw_blade("SawBlade", SPEC["blade_diameter"],
                        SPEC["blade_width"], 9.5, teeth=24, mat=steel)
    blade.name = "SawBlade"          # gear() names its body "<name>_body"
    bkit.place(blade, (BX, 0.0, BZ), "Y")
    bkit.cylinder("SawArbor", 22.0, 40.0, segments=32,
                  centre=(BX, 0.0, BZ), axis="Y", mat=dark)

    # ---- upper blade guard: a real half-cowl, wider than the blade ----------
    guard = T.shroud("SawGuard", 95.0, 103.0, SPEC["guard_width"],
                     -8.0, 188.0, centre=(BX, 0.0, BZ), axis="Y", mat=cast)
    bkit.move(guard, 0.0, 0.0, 0.0)

    # ---- gearbox + motor ---------------------------------------------------
    T.shell("SawGearbox", 96.0, 104.0, 74.0, centre=(BX, 0.0, 152.0),
            r=20.0, mat=cast)
    motor = bkit.lathe("SawMotor",
                       [(0.0, -50.0), (46.0, -50.0), (52.0, -34.0),
                        (52.0, 34.0), (46.0, 50.0), (0.0, 50.0)],
                       segments=40, centre=(0, 0, 0), mat=orange)
    bkit.place(motor, (-40.0, 0.0, 172.0), "Y")
    T.vent_panel("SawVent", 5, 2, 14.0, 18.0, 4.0, 66.0, 34.0, 5.0,
                 centre=(-70.0, 0.0, 172.0), axis="X", mat=dark)

    # ---- D-handle ----------------------------------------------------------
    bkit.arc_torus("SawHandle", 55.0, 12.0, -12.0, 192.0, centre=(58.0, 0.0,
                                                                   205.0),
                   plane="XZ", seg_major=32, mat=grip_mat)
    T.strut("SawHandleLeg", (58.0, 0.0, 205.0), (16.0, 0.0, 178.0),
            26.0, 34.0, mat=grip_mat)
    T.grip("SawRearGrip", (-84.0, 0.0, 190.0), (-70.0, 0.0, 132.0),
           40.0, 46.0, 38.0, 44.0, mat=grip_mat, bow=6.0)
    T.trigger("SawTrigger", (-58.0, 0.0, 196.0), (-60.0, 0.0, 180.0),
              24.0, 12.0, mat=dark)

    # ---- adjustments -------------------------------------------------------
    T.knob("SawBevelKnob", 21.0, 30.0, (-6.0, 0.0, 200.0), mat=dark)
    T.knob("SawDepthKnob", 18.0, 26.0, (-150.0, 0.0, 34.0), mat=dark)
    T.rod("SawDepthArm", (-150.0, 0.0, 34.0), (-90.0, 0.0, 34.0), 7.0,
          mat=cast)

    return dict(spec=SPEC, parts=14)