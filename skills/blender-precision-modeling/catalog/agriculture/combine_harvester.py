"""
combine_harvester -- a self-propelled combine harvester: 6 m header, 9.8 m long.

A combine is a machine with TWO DIFFERENT WHEELS, and getting that wrong is the
whole silhouette. The front pair are the big driven wheels (1450 mm) that carry
the engine and the threshing drum; the rear pair are small steering wheels
(1050 mm). Both pairs are built from their own diameter, so both treads land on
z=0 by construction and `sit_on_floor()` is a no-op.

The header is the wide part: a 6000 mm cutterbar with a reel above it. The reel
is a SIX-BAT drum whose bats are arrayed about the REEL AXLE, not the world
origin -- orbit the world origin and every bat lands 575 mm out from its own
hub.

Real Lexion-class machine: 6.0 m header, 1450 mm drive wheels, 1050 mm steering
wheels, 3000 mm to the top of the grain tank.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _agri as A

SPEC = dict(
    header_width=6000.0,
    header_reel_dia=1150.0,
    overall_length=9830.0,
    body_length=8600.0,
    body_width=2100.0,
    drive_wheel_dia=1450.0,
    steer_wheel_dia=1050.0,
    drive_track=2500.0,
    steer_track=2000.0,
    grain_tank_top=3000.0,
    cab_height=1900.0,
)

HEADER_W = SPEC["header_width"]
REEL_D = SPEC["header_reel_dia"]
REEL_C = (4600.0, 0.0, 1180.0)     # the reel axle the bats orbit about

CHECKS = [
    dict(name="header_width", mm=6000.0, tol=6.0, how="bbox_y",
         part="CombineReelBats"),
    dict(name="body_length", mm=8600.0, tol=8.0, how="bbox_x",
         part="CombineChassis"),
    dict(name="body_width", mm=2100.0, tol=8.0, how="bbox_y",
         part="CombineChassis"),
    dict(name="drive_wheel_dia", mm=1450.0, tol=4.0, how="diameter",
         part="Wheel0"),
    dict(name="steer_wheel_dia", mm=1050.0, tol=4.0, how="diameter",
         part="Wheel2"),
    dict(name="grain_tank_top", mm=3000.0, tol=8.0, how="top_z",
         part="CombineGrainTank"),
    dict(name="cab_height", mm=1900.0, tol=8.0, how="bbox_z",
         part="CombineCab"),
    dict(name="drive_tread_on_floor", mm=0.0, tol=2.0, how="z_min",
         part="Wheel0"),
]


def build():
    paint = bkit.pbr("CombinePaint", base=(0.72, 0.16, 0.04), metal=0.25,
                     rough=0.34)
    steel = bkit.preset("dark_metal")
    edge = bkit.preset("brushed_metal")
    rubber = bkit.preset("rubber")
    glass = bkit.pbr("CombineGlass", base=(0.16, 0.20, 0.24), rough=0.06,
                     metal=0.2)
    olive = bkit.pbr("CombineOlive", base=(0.30, 0.33, 0.10), rough=0.55)

    # ---- wheels: two DIFFERENT pairs, both treads on z=0 --------------
    fd = SPEC["drive_wheel_dia"]
    fs = SPEC["steer_wheel_dia"]
    tdr = SPEC["drive_track"] / 2.0
    tsr = SPEC["steer_track"] / 2.0
    w0 = A.ground_wheel("Wheel0", fd, 780.0, rim_dia=760.0, mat_tyre=rubber)
    A.place_wheels(w0, [(1700.0, -tdr, fd / 2.0), (1700.0, tdr, fd / 2.0)],
                   names=["Wheel0", "Wheel1"])
    w2 = A.ground_wheel("Wheel2", fs, 520.0, rim_dia=560.0, mat_tyre=rubber)
    A.place_wheels(w2, [(-3200.0, -tsr, fs / 2.0), (-3200.0, tsr, fs / 2.0)],
                   names=["Wheel2", "Wheel3"])

    # ---- chassis -------------------------------------------------------
    bkit.rounded_box("CombineChassis", SPEC["body_length"], SPEC["body_width"],
                     900.0, r=30.0, segments=3, centre=(0.0, 0.0, 1150.0),
                     mat=paint)
    # the deck the tank sits on, slightly narrower than the chassis
    bkit.rounded_box("CombineDeck", 5200.0, 2050.0, 140.0, r=14.0,
                     segments=2, centre=(-400.0, 0.0, 1650.0), mat=steel)

    # ---- grain tank: a loft, because the tank tapers inward at the top ---
    tanks = []
    for (z, sx, sy) in ((1720.0, 4400.0, 2100.0), (2600.0, 4300.0, 1960.0),
                        (3000.0, 3900.0, 1620.0)):
        ring = bkit.rounded_rect_section(sx, sy, 90.0, per_corner=4,
                                         centre=(-400.0, 0.0))
        tanks.append([(-400.0 + x, y, z) for (x, y) in ring])
    tank = bkit.loft("CombineGrainTank", tanks, mat=paint)
    bkit.recalc(tank)
    # an extension lid, folded open to one side -- the giveaway of a combine
    bkit.rounded_box("CombineTankLid", 3600.0, 1540.0, 90.0, r=20.0,
                     segments=2, centre=(-400.0, -420.0, 3040.0), mat=paint)

    # ---- cab, with a real glass band -----------------------------------
    cab = bkit.rounded_box("CombineCab", 1800.0, 1700.0, SPEC["cab_height"],
                           r=60.0, segments=3, centre=(2700.0, 0.0, 2540.0),
                           mat=paint)
    A.freeze(cab)
    bkit.assign_faces_by(cab, glass, lambda c, n: c.x / bkit.MM > 3100.0
                         and abs(n.x) > 0.45 and c.z / bkit.MM > 1900.0)
    bkit.rounded_box("CombineRoof", 1700.0, 1620.0, 120.0, r=40.0,
                     segments=2, centre=(2700.0, 0.0, 3540.0), mat=paint)
    bkit.cylinder("CombineBeacon", 70.0, 220.0, segments=16,
                  centre=(3150.0, 0.0, 3700.0), mat=bkit.preset("yellow_paint"))

    # ---- unloading auger: the long tube that reaches over the trailer ---
    bkit.cylinder("CombineAuger", 170.0, 6000.0, segments=28, axis="X",
                  centre=(1100.0, 1280.0, 2400.0), mat=paint)
    bkit.cylinder("CombineAugerFold", 170.0, 1500.0, segments=28, axis="Z",
                  centre=(4050.0, 1280.0, 1700.0), mat=paint)
    bkit.cylinder("CombineAugerSpout", 190.0, 420.0, segments=28, axis="Y",
                  centre=(4050.0, 1420.0, 1010.0), mat=steel)

    # ---- feeder house between the body and the header -------------------
    bkit.rounded_box("CombineFeeder", 1400.0, 1700.0, 1500.0, r=50.0,
                     segments=3, centre=(3900.0, 0.0, 1250.0), mat=paint)

    # ---- header: platform, cutterbar, reel ------------------------------
    bkit.rounded_box("CombineHeaderFloor", 1300.0, HEADER_W, 260.0, r=16.0,
                     segments=2, centre=(4400.0, 0.0, 620.0), mat=paint)
    bkit.rounded_box("CombineHeaderBack", 300.0, HEADER_W, 900.0, r=16.0,
                     segments=2, centre=(3880.0, 0.0, 1050.0), mat=paint)
    bkit.cylinder("CombineCutterbar", 40.0, HEADER_W, segments=24, axis="Y",
                  centre=(5010.0, 0.0, 420.0), mat=edge)
    # knife sections on a computed pitch along the bar
    for (y, _w) in bkit.lay_out([150.0] * 20, gap=150.0):
        bkit.extrude_profile("CombineKnife",
                             [(-140.0, 0.0), (140.0, 0.0), (60.0, 240.0),
                              (-60.0, 240.0)], 14.0,
                             centre=(5010.0, y, 300.0), axis="Z", mat=edge)

    # reel: six bats arrayed about the REEL AXLE, both ends on real arms
    bkit.cylinder("CombineReelHub", 95.0, HEADER_W - 60.0, segments=24,
                  axis="Y", centre=REEL_C, mat=olive)
    # The bat carries its 535 mm orbit radius in the MESH, not in
    # `obj.location`: the array modifier orbits local coordinates, so a bat
    # placed by `location` collapses the reel into one spoke.
    bat = bkit.rounded_box("CombineReelBats", 70.0, HEADER_W, 70.0, r=18.0,
                           segments=2,
                           centre=(REEL_C[0] + REEL_D / 2.0 - 40.0, 0.0,
                                   REEL_C[2]), mat=olive)
    bpy_view_update()
    bkit.array_radial(bat, 6, axis="Y", centre=REEL_C)
    for s in (1, -1):
        A.tube_between("CombineReelArm%d" % (s if s > 0 else 1),
                       (4300.0, s * (HEADER_W / 2.0 - 60.0), 700.0),
                       (REEL_C[0], s * (HEADER_W / 2.0 - 60.0), REEL_C[2]),
                       55.0, mat=olive)

    # ---- rear straw chopper and spout ------------------------------------
    bkit.rounded_box("CombineChopper", 700.0, 2600.0, 800.0, r=20.0,
                     segments=2, centre=(-4450.0, 0.0, 1450.0), mat=olive)
    for i in range(10):
        y = (i - 4.5) * 250.0
        bkit.rounded_box("CombineChopperKnife%d" % i, 180.0, 120.0, 560.0,
                         r=20.0, segments=2,
                         centre=(-4650.0, y, 1450.0), mat=edge)

    bpy_view_update()
    return dict(spec=SPEC, parts=14, note=A.AGRI_NOTE)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()


def bpy_view_update():
    import bpy
    bpy.context.view_layer.update()
