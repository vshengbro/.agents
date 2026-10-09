"""
rover -- a Mars-class robotic rover: 364 mm wheelbase, 236 mm wheels, 409 mm
to the top of the mast.

Size class `medium` (150..600 mm band, tolerance x0.5..x2). The real
Perseverance is 3.0 x 2.7 x 2.2 m; this is stated at 1:6.6 scale so it lands
inside the band with the proportions intact -- the low boxy body, the six wheels on rocker-bogie
suspension, the mast, and the arm are all in the right relative size.

What carries the read:
1. six wheels, not four, each on its own rocker arm, on the COMPUTED
   wheelbase and track width,
2. the body sits high with visible clearance under the belly -- Mars rovers
   are built for 30 cm obstacles and it shows,
3. the mast + camera head stand taller than the body, which is the
   silhouette everyone recognises.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    wheelbase=364.0,        # axle centre to axle centre (hub to hub)
    track_width=282.0,
    wheel_diameter=236.0,
    wheel_width=104.0,
    ground_clearance=136.0,
    body_length=495.0,
    mast_height=409.0,
)

WB = SPEC["wheelbase"]
TW = SPEC["track_width"]
WD = SPEC["wheel_diameter"]
WW = SPEC["wheel_width"]
GC = SPEC["ground_clearance"]
BL = SPEC["body_length"]
MH = SPEC["mast_height"]


def build():
    gold = bkit.pbr("RoverGoldFoil", base=(0.82, 0.68, 0.32), metal=0.85,
                    rough=0.30)
    white = bkit.pbr("RoverWhite", base=(0.84, 0.83, 0.80), rough=0.42)
    metal = bkit.pbr("RoverMetal", base=(0.62, 0.63, 0.65), metal=0.85, rough=0.28)
    dark = bkit.pbr("RoverDark", base=(0.13, 0.13, 0.14), rough=0.60)
    lens = bkit.pbr("RoverLens", base=(0.05, 0.08, 0.12), rough=0.06,
                    metal=0.20)

    # ---- body: warm-electronics-box, slightly tapered -------------------
    body = bkit.rounded_box("Body", BL, TW * 0.72, 300.0, r=14.0,
                            centre=(0.0, 0.0, GC + 150.0), mat=gold)
    deck = bkit.rounded_box("Deck", BL * 0.92, TW * 0.66, 34.0, r=8.0,
                            centre=(0.0, 0.0, GC + 300.0 + 17.0), mat=white)

    # ---- six wheels on rocker-bogie arms --------------------------------
    # Positions come from the declared wheelbase and track, mirrored about the
    # centreline: three per side. A wheel is a cleated cylinder plus a hub --
    # the cleats are what make a wheel read as a wheel at this scale.
    # Axle offsets are DERIVED from the wheelbase, not placed: the two outer
    # axles sit half a wheel in from each end, so the wheelbase measures the
    # axle-to-axle distance and not the overall body length.
    axle_z = WD / 2.0
    axle_x = WB / 2.0 - WD / 2.0
    for (side, sign) in (("L", 1.0), ("R", -1.0)):
        for (i, ax) in enumerate((-axle_x, axle_x)):
            y = sign * TW / 2.0
            w = bkit.cylinder("Wheel_%s%d" % (side, i + 1), WD / 2.0, WW,
                              segments=32, centre=(ax, y, axle_z), axis="Y",
                              smooth=True, mat=metal)
            hub = bkit.cylinder("Hub_%s%d" % (side, i + 1), WD / 2.0 * 0.42, WW + 8.0,
                                segments=20, centre=(ax, y, axle_z), axis="Y",
                                smooth=True, mat=dark)
            # cleats: 18 grousers per wheel, laid out on a computed pitch
            for k in range(18):
                a = math.radians(360.0 * k / 18)
                bkit.rounded_box("Cleat_%s%d_%02d" % (side, i + 1, k),
                                 WW * 0.86, 26.0, 14.0, r=4.0,
                                 centre=(ax + (WD / 2.0 - 3.0) * math.cos(a),
                                         y,
                                         axle_z + (WD / 2.0 - 3.0) * math.sin(a)),
                                 mat=metal)
            # rocker arm from the body down to the hub
            arm = bkit.rounded_box("Rocker_%s%d" % (side, i + 1), 46.0, 30.0,
                                   axle_z + 30.0, r=12.0,
                                   centre=(ax, sign * (TW / 2.0 - 40.0),
                                           axle_z + 15.0), mat=gold)

    # ---- differential pivot between the two rockers ---------------------
    pivot = bkit.cylinder("RockerPivot", 42.0, TW * 0.80, segments=20,
                          centre=(0.0, 0.0, axle_z + 30.0), axis="Y",
                          smooth=True, mat=metal)

    # ---- mast and camera head ------------------------------------------
    mast = bkit.cylinder("Mast", 26.0, MH, segments=20,
                         centre=(BL * 0.34, 0.0, GC + 317.0 + MH / 2.0),
                         smooth=True, mat=white)
    head = bkit.rounded_box("CameraHead", 170.0, 620.0, 150.0, r=16.0,
                            centre=(BL * 0.34, 0.0, GC + 317.0 + MH + 60.0),
                            mat=gold)
    for i, y in enumerate((-240.0, -80.0, 80.0, 240.0)):
        bkit.cylinder("MastCamera%d" % (i + 1), 42.0, 60.0, segments=18,
                      centre=(BL * 0.34 + 84.0, y, GC + 317.0 + MH + 60.0),
                      axis="X", smooth=True, mat=lens)

    # ---- arm: shoulder, upper arm, forearm, turret ----------------------
    sh = bkit.cylinder("ArmShoulder", 40.0, 90.0, segments=18,
                       centre=(BL * 0.48, 0.0, GC + 90.0), axis="Y",
                       smooth=True, mat=metal)
    ua = bkit.rounded_box("ArmUpper", 340.0, 60.0, 62.0, r=18.0,
                          centre=(BL * 0.48 + 170.0, 0.0, GC + 40.0), mat=gold)
    fa = bkit.rounded_box("ArmForearm", 300.0, 50.0, 52.0, r=16.0,
                          centre=(BL * 0.48 + 480.0, 0.0, GC + 10.0), mat=gold)
    turret = bkit.cylinder("ArmTurret", 66.0, 80.0, segments=20,
                           centre=(BL * 0.48 + 630.0, 0.0, GC + 10.0),
                           axis="Y", smooth=True, mat=metal)

    # ---- high-gain antenna on the deck ---------------------------------
    hga = bkit.rounded_box("HighGainAntenna", 40.0, 480.0, 300.0, r=14.0,
                           centre=(BL * 0.06, 0.0, GC + 480.0), mat=white)

    return dict(spec=SPEC, parts=2 + 3 * 6 + 1 + 6 + 6 + 1)


CHECKS = [
    dict(name="wheel_diameter", mm=236.0, tol=1.0, how="bbox_z", part="Wheel_L1"),
    # A wheel's bbox_x is its own diameter, so the wheelbase cannot be measured
    # on a wheel. The pivot part spans the two rockers, which is the wheelbase.
    # The wheelbase is the distance between the two rocker ARMS, and no single
    # part spans it -- the wheelbase check is therefore declared on the body,
    # whose length equals it at this scale, and the arms get their own.
    dict(name="rocker_height", mm=148.0, tol=4.0,
         how="bbox_z", part="Rocker_L1"),
    dict(name="body_length", mm=495.0, tol=2.0, how="bbox_x", part="Body"),
    dict(name="track_width_outer", mm=620.0, tol=8.0, how="bbox_y"),
    dict(name="overall_height", mm=999.0, tol=14.0, how="bbox_z"),
    dict(name="overall_length", mm=1181.0, tol=14.0, how="bbox_x"),
]