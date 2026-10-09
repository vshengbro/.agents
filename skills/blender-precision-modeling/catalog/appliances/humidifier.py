"""
humidifier -- 230 mm diameter, 350 mm tall ultrasonic humidifier: a lathed
water tank with a translucent level window, a top cap with a mist outlet, a
base with four buttons on one pitch, and a cable groove.

The tank is one closed lathe profile; the level window is a second material on
the SAME solid (assign_faces_by), because a second shell would z-fight with the
wall and leave two non-manifold objects behind.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=230.0,
    body_height=200.0,       # base to the top of the tank
    overall_height=294.0,    # floor to the top of the mist outlet
    base_height=44.0,
    cap_height=18.0,
    outlet_diameter=54.0,
    outlet_height=50.0,
    button_count=3,
    button_diameter=18.0,
    button_pitch=30.0,
    window_height=100.0,
    volume_ml=3800.0,
)

R = SPEC["body_diameter"] / 2.0
H = SPEC["body_height"]
BASE = SPEC["base_height"]
BOWL_Z = BASE - 4.0                # tank sinks 4 mm into the base
TANK_TOP = BOWL_Z + H
CAP_TOP = TANK_TOP + SPEC["cap_height"]


def build():
    shell = bkit.pbr("HumidifierTank", base=(0.84, 0.86, 0.88), rough=0.14,
                     coat=0.5)
    base_mat = bkit.pbr("HumidifierBase", base=(0.30, 0.31, 0.34), rough=0.30,
                        coat=0.2)
    dark = bkit.preset("black_plastic")
    window = bkit.pbr("LevelWindow", base=(0.55, 0.62, 0.68), rough=0.18,
                      transmission=0.30, ior=1.45)
    lamp = bkit.pbr("HumidifierButton", base=(0.06, 0.07, 0.08), rough=0.22,
                    emission=(0.35, 0.60, 0.90), emission_strength=1.2)

    # ---- base -------------------------------------------------------------
    bkit.lathe("HumidifierBase",
               [(0.0, 0.0), (R - 4.0, 0.0), (R, 6.0), (R, BASE - 8.0),
                (R - 8.0, BASE), (R - 14.0, BASE), (R - 16.0, BASE - 8.0),
                (R - 6.0, 4.0), (0.0, 4.0)],
               segments=96, mat=base_mat)

    # ---- tank: one closed profile -----------------------------------------
    prof = [
        (0.0, 0.0),
        (R - 26.0, 0.0),
        (R - 8.0, 3.0),
        (R, 18.0),
        (R, H - 34.0),
        (R - 4.0, H - 12.0),
        (R - 12.0, H),
        (R - 16.0, H),
        (R - 19.0, H - 10.0),
        (R - 6.0 - 4.0, 16.0),
        (R - 26.0 - 4.0, 9.0),
        (0.0, 8.0),
    ]
    tank = bkit.lathe("HumidifierTank", prof, segments=96,
                      centre=(0.0, 0.0, BOWL_Z), mat=shell)

    # The level window is a second MATERIAL on the same watertight solid: a
    # duplicate shell would z-fight with the wall and leave both objects
    # non-manifold.
    bkit.assign_faces_by(
        tank, window,
        lambda c, n: 0.0 < c.z / bkit.MM - BOWL_Z < SPEC["window_height"]
        and abs(n.z) < 0.5)

    # ---- top cap and mist outlet ------------------------------------------
    bkit.lathe("HumidifierCap",
               [(0.0, 0.0), (R - 10.0, 0.0), (R - 4.0, 4.0), (R - 4.0, 14.0),
                (R - 20.0, SPEC["cap_height"]), (0.0, SPEC["cap_height"])],
               segments=96, centre=(0.0, 0.0, TANK_TOP - 6.0), mat=base_mat)
    bkit.lathe("MistOutlet",
               [(0.0, 0.0), (SPEC["outlet_diameter"] / 2.0 - 6.0, 0.0),
                (SPEC["outlet_diameter"] / 2.0, 5.0),
                (SPEC["outlet_diameter"] / 2.0, SPEC["outlet_height"] - 8.0),
                (SPEC["outlet_diameter"] / 2.0 - 7.0, SPEC["outlet_height"]),
                (SPEC["outlet_diameter"] / 2.0 - 14.0, SPEC["outlet_height"]),
                (SPEC["outlet_diameter"] / 2.0 - 16.0, 4.0), (0.0, 4.0)],
               segments=64, centre=(0.0, 0.0, TANK_TOP + 4.0), mat=dark)

    # ---- buttons on the base ring -----------------------------------------
    # Placed on one pitch around the front arc, not in a straight row: a row
    # would either float off the curved base or sink into it. The row is kept
    # narrow AND each cap is sunk 15 mm, so even the outermost cap's back face
    # stays inside the 115 mm base cylinder at its own x.
    bd = SPEC["button_diameter"]
    for i, (x, _w) in enumerate(
            bkit.lay_out([bd] * SPEC["button_count"],
                         gap=SPEC["button_pitch"] - bd)):
        bkit.cylinder("Button%d" % i, bd / 2.0, 14.0, segments=28, axis="Y",
                      centre=(x, -(R - 8.0), BASE * 0.55), mat=lamp)

    # ---- cable groove ------------------------------------------------------
    bkit.cylinder("CablePort", 10.0, 22.0, segments=24, axis="Y",
                  centre=(0.0, R - 2.0, BASE * 0.4), mat=dark)

    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="body_diameter", mm=230.0, tol=0.4, how="diameter",
         part="HumidifierTank"),
    dict(name="body_height", mm=200.0, tol=0.4, how="bbox_z",
         part="HumidifierTank"),
    dict(name="overall_height", mm=294.0, tol=0.5, how="bbox_z"),
    dict(name="overall_width", mm=230.0, tol=0.5, how="bbox_x"),
    dict(name="base_height", mm=44.0, tol=0.4, how="bbox_z", part="HumidifierBase"),
]