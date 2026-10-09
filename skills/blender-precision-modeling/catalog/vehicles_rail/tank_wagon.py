"""
tank_wagon -- 14 m bogie tank wagon, 11 m barrel of 2,600 mm diameter.

A tank wagon is a barrel on a railway underframe, and the barrel is the easy
part. What makes it read as a tank wagon rather than a pipe on wheels is the
TOP: a manway dome with a hinged lid, a catwalk down the crown and a handrail
either side of it. Without the catwalk the silhouette is a cylinder.

The barrel sits ON the deck -- barrel bottom at the 1,250 mm deck line, so
barrel axis is at 2,550 and the crown at 3,850 -- and the whole thing stands on
flange tips at z=0.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    length_over_buffers=14000.0,
    barrel_diameter=2600.0,
    barrel_length=11000.0,
    barrel_crown_z=3850.0,
    deck_z=1250.0,
    catwalk_z=3900.0,
    capacity_m3=58.0,
    wheel_diameter=840.0,
    gauge=1435.0,
)

CHECKS = [
    dict(name="length_over_buffers", mm=14000.0, tol=3.0, how="bbox_x",
         part="TankFrame"),
    dict(name="barrel_diameter", mm=2600.0, tol=3.0, how="bbox_y",
         part="TankBarrel"),
    dict(name="barrel_bottom_z", mm=1250.0, tol=3.0, how="bottom_z",
         part="TankBarrel"),
    dict(name="barrel_crown_z", mm=3850.0, tol=3.0, how="top_z",
         part="TankBarrel"),
    dict(name="barrel_length", mm=11000.0, tol=3.0, how="bbox_x",
         part="TankBarrel"),
    dict(name="catwalk_top_z", mm=3960.0, tol=3.0, how="top_z",
         part="TankCatwalk"),
    dict(name="wheel_flange_diameter", mm=896.0, tol=3.0, how="bbox_z",
         part="TankAxles"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min", part="TankAxles"),
]

LENGTH = 14000.0
HALF_W = 1450.0
DECK_Z = 1250.0
BARREL_R = 1300.0
BARREL_L = 11000.0
BARREL_Z = DECK_Z + BARREL_R            # 2550
CROWN_Z = BARREL_Z + BARREL_R           # 3850
WHEEL_D = 840.0
BOGIE_X = 3500.0
BOGIE_WB = 2000.0


def build():
    frame_m = bkit.pbr("TankFramePaint", base=(0.20, 0.20, 0.22), rough=0.52)
    shell_m = bkit.pbr("TankShellMat", base=(0.55, 0.56, 0.58), metal=0.85,
                       rough=0.30)
    steel = bkit.preset("dark_metal")
    yellow = bkit.preset("yellow_paint")

    R.underframe("TankFrame", LENGTH, half_w=HALF_W, z_bot=950.0, depth=300.0,
                 mat=frame_m)

    barrel = bkit.cylinder("TankBarrel", BARREL_R, BARREL_L, segments=72,
                           axis="X", centre=(0.0, 0.0, BARREL_Z), mat=shell_m)
    bkit.recalc(barrel)
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        bkit.cylinder("TankEndCap" + tag, BARREL_R + 40.0, 60.0, segments=72,
                      axis="X",
                      centre=(s * (BARREL_L / 2.0 + 30.0), 0.0, BARREL_Z),
                      mat=frame_m)

    # --- manway dome and hinged lid ----------------------------------------
    dome_x = 2100.0
    bkit.cylinder("TankDome", 480.0, 320.0, segments=40, axis="Z",
                  centre=(dome_x, 0.0, CROWN_Z + 140.0), mat=frame_m)
    lid = R.raked_panel("TankDomeLid", 1100.0, 1100.0, 60.0, -52.0, axis="Y",
                        centre=(dome_x, 0.0, CROWN_Z + 330.0), r=25.0,
                        mat=steel)

    # --- catwalk and handrails down the crown ------------------------------
    catwalk = bkit.rounded_box("TankCatwalk", 7200.0, 700.0, 40.0, r=8.0,
                               segments=2, centre=(0.0, 0.0, 3940.0), mat=steel)
    rib = bkit.rounded_box("TankCatwalkRib", 60.0, 700.0, 120.0, r=8.0,
                           segments=2, centre=(0.0, 0.0, 3870.0), mat=steel)
    bkit.array_linear(rib, 13, (560.0, 0.0, 0.0), world=True)
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        for i, x in enumerate(R.evenly(4, 6600.0)):
            R.strut("TankStanchion%s%d" % (tag, i),
                    (x, s * 350.0, 3960.0), (x, s * 350.0, 4790.0), 30.0,
                    steel, seg=10)
        R.strut("TankHandrail" + tag, (-3300.0, s * 350.0, 4790.0),
                (3300.0, s * 350.0, 4790.0), 30.0, steel, seg=10)
        R.strut("TankMidrail" + tag, (-3300.0, s * 350.0, 4400.0),
                (3300.0, s * 350.0, 4400.0), 24.0, steel, seg=10)

    # --- saddles, end platforms, discharge valve ---------------------------
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        bkit.rounded_box("TankSaddle" + tag, 900.0, 2400.0, 520.0, r=90.0,
                         segments=3,
                         centre=(s * 3600.0, 0.0, DECK_Z - 180.0), mat=frame_m)
        bkit.rounded_box("TankPlatform" + tag, 1700.0, 2700.0, 50.0, r=10.0,
                         segments=2,
                         centre=(s * 6100.0, 0.0, DECK_Z + 25.0), mat=steel)
        for sy, ytag in ((1.0, "L"), (-1.0, "R")):
            R.strut("TankEndPost%s%s" % (tag, ytag),
                    (s * 6950.0, sy * 1300.0, DECK_Z + 50.0),
                    (s * 6950.0, sy * 1300.0, DECK_Z + 1050.0), 28.0, steel,
                    seg=10)
        R.strut("TankEndRail" + tag, (s * 6950.0, -1300.0, DECK_Z + 1050.0),
                (s * 6950.0, 1300.0, DECK_Z + 1050.0), 28.0, steel, seg=10)
    bkit.cylinder("TankDischarge", 300.0, 420.0, segments=28, axis="Z",
                  centre=(0.0, 0.0, 1050.0), mat=frame_m)
    vw = R.spoked_ring("TankValveWheel", 300.0, 5, axis="Z", rim_r=28.0,
                       hub_r=70.0, spoke_w=56.0, spoke_t=56.0, mat=yellow,
                       seg=28)
    bkit.move(vw, 0.0, 1500.0, 1120.0)

    # --- running gear and buffers ------------------------------------------
    R.running_gear("Tank", WHEEL_D, BOGIE_X, BOGIE_WB, mat_frame=steel)
    R.air_reservoir("TankAirRes", -5200.0, 0.0, 820.0, steel, r=215.0,
                    length=1100.0)
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        R.buffers("TankBuffers" + tag, s * (LENGTH / 2.0), z=1065.0,
                  pitch=1750.0, mat_body=frame_m, mat_head=steel)
        for sy, ytag in ((1.0, "L"), (-1.0, "R")):
            R.steps("TankStep%s%s" % (tag, ytag), s * 6600.0, sy * 1300.0,
                    480.0, DECK_Z - 20.0, steel, width=420.0, n=3)

    return dict(spec=SPEC, parts=22)