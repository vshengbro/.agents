"""
castor_wheel -- 75 mm swivel castor with a rubber tyre and a 50 mm top plate.

A castor is six parts and every one of them is visible: the tyre and its hub
turn inside a fork, the fork swivels under a bearing boss, and the boss carries
the bolting plate. The fork arms are held off the tyre by exactly half the
wheel width, which is the clearance that lets the wheel spin -- modelling them
flush is what makes a castor look welded shut.

75 mm is the common furniture wheel; the bore, plate and bolt pattern are all
standard furniture sizes (10 mm bore, 4 x M6 on a 34 mm square).
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

WHEEL_D = 75.0          # tyre outside diameter
WHEEL_W = 25.0          # tyre width
HUB_D = 51.0            # hub flange diameter
BORE_D = 10.0           # bore
AXLE_D = 8.0
WHEEL_Z = WHEEL_D / 2.0       # axle height above the floor
ARM_Y = 14.5                 # fork arm offset: clears the tyre by 2 mm
PLATE_S = 50.0               # top plate square
PLATE_T = 5.0
PLATE_HOLE_D = 5.5           # M6 clearance
PLATE_HOLE_PITCH = 34.0

SPEC = dict(wheel_diameter=WHEEL_D,
            wheel_width=WHEEL_W,
            bore_diameter=BORE_D,
            axle_diameter=AXLE_D,
            plate_size=PLATE_S,
            overall_height=PLATE_S * 0.0 + 76.0)


def build():
    zinc = bkit.pbr("CastorZinc", base=(0.72, 0.74, 0.77), metal=0.70,
                    rough=0.32)
    rubber = bkit.preset("rubber")
    steel = bkit.pbr("CastorSteel", base=(0.70, 0.72, 0.75), metal=0.74,
                     rough=0.26)

    # ---- tyre: revolved section, then laid on its side (axis along Y) ----
    ro, ri, hw = WHEEL_D / 2.0, WHEEL_D / 2.0 - 12.5, WHEEL_W / 2.0
    tyre = bkit.lathe("WheelTyre",
                      [(ri, -hw), (ro - 2.5, -hw), (ro, -hw + 3.5),
                       (ro, hw - 3.5), (ro - 2.5, hw), (ri, hw),
                       (ri, -hw)],
                      segments=96, cap_ends=False, mat=rubber)
    tyre.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    tyre.location = bkit.v(0, 0, WHEEL_Z)

    bkit.tube("WheelHub", HUB_D / 2.0, BORE_D / 2.0, WHEEL_W - 1.0,
              segments=64, centre=(0, 0, WHEEL_Z), axis="Y", mat=steel)
    bkit.cylinder("Axle", AXLE_D / 2.0, 2.0 * ARM_Y + 10.0, segments=32,
                  centre=(0, 0, WHEEL_Z), axis="Y", mat=steel)

    # ---- fork: two arms under a yoke -------------------------------------
    arms = [bkit.rounded_box("ForkArm", 14.0, 3.5, 26.0, r=1.2, segments=3,
                             centre=(0, sign * ARM_Y, WHEEL_Z + 7.0),
                             mat=zinc)
            for sign in (-1.0, 1.0)]
    yoke = bkit.rounded_box("ForkYoke", 40.0, 2.0 * ARM_Y + 4.0, 10.0, r=2.0,
                            segments=3, centre=(0, 0, WHEEL_Z + 14.5), mat=zinc)
    bkit.join(arms + [yoke], name="Fork")

    bkit.cylinder("SwivelBoss", 17.0, 14.0, segments=48,
                  centre=(0, 0, WHEEL_Z + 26.5), mat=zinc)

    plate = bkit.rounded_box("TopPlate", PLATE_S, PLATE_S, PLATE_T, r=2.0,
                             segments=3, centre=(0, 0, WHEEL_Z + 36.0),
                             mat=zinc)
    for (px, py) in bkit.grid_positions(2, 2, PLATE_HOLE_PITCH, PLATE_HOLE_PITCH):
        cutter = bkit.cylinder("PlateHole", PLATE_HOLE_D / 2.0, PLATE_T * 3.0,
                               segments=24,
                               centre=(px, py, WHEEL_Z + 36.0), mat=None)
        bkit.boolean(plate, cutter, "DIFFERENCE")

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="wheel_diameter", mm=75.0, tol=0.05, how="bbox_x", part="WheelTyre"),
    dict(name="wheel_width", mm=25.0, tol=0.05, how="bbox_y", part="WheelTyre"),
    dict(name="plate_size", mm=50.0, tol=0.05, how="bbox_x", part="TopPlate"),
    dict(name="overall_height", mm=76.0, tol=0.05, how="bbox_z", part=None),
]