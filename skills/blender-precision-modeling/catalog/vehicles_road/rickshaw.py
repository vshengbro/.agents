"""
rickshaw -- auto rickshaw (tuk-tuk), 2600 x 1400 x 1700 mm.

Three wheels, one up front: a 480 mm steered wheel on a single-track nose and a
pair of 560 mm rear wheels. That asymmetric wheel layout, plus a canopy that is
narrower than the rear body and set back behind the driver, is the whole
silhouette -- a three-wheeler with a roof reads as a rickshaw immediately, and
no amount of body detail rescues it if the wheels are the wrong size.

Real proportions: 1400 mm of width carried by a 560 mm wheel pair, a 1700 mm
canopy over a 380 mm seat, and a front cowl that stops at chest height so the
driver is in the open.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=2600.0,
    width=1400.0,
    height=1700.0,
    front_wheel_diameter=480.0,
    rear_wheel_diameter=560.0,
    rear_track=1120.0,
    canopy_height=1700.0,
    floor_height=330.0,
)

CHECKS = [
    dict(name="length", mm=2600.0, tol=5.0, how="bbox_x", part=None),
    dict(name="width", mm=1400.0, tol=5.0, how="bbox_y", part=None),
    dict(name="height", mm=1700.0, tol=5.0, how="bbox_z", part=None),
    dict(name="front_wheel_diameter", mm=480.0, tol=2.0, how="diameter",
         part="Wheel0"),
    dict(name="rear_wheel_diameter", mm=560.0, tol=2.0, how="diameter",
         part="Wheel1"),
    dict(name="canopy_length", mm=1500.0, tol=5.0, how="bbox_x",
         part="RickshawCanopy"),
]

# front cowl / nose: short, narrow, chest height
NOSE = [
    (1300.0, 300.0, 300.0, 900.0, 4.0),
    (1180.0, 400.0, 280.0, 1020.0, 4.4),
    (1000.0, 440.0, 270.0, 1080.0, 4.6),
    (800.0, 450.0, 265.0, 1085.0, 4.6),
]

# cabin: a rounded tub, narrow at the waist where the driver's knees go
CABIN = [
    (780.0, 430.0, 265.0, 1120.0, 4.4),
    (400.0, 480.0, 265.0, 1180.0, 4.8),
    (-100.0, 485.0, 270.0, 1200.0, 4.8),
    (-600.0, 480.0, 280.0, 1180.0, 4.6),
    (-900.0, 450.0, 300.0, 1100.0, 4.2),
    (-1200.0, 370.0, 340.0, 980.0, 3.8),
]


def build():
    paint = bkit.pbr("RickshawPaint", base=(0.88, 0.72, 0.05), rough=0.26,
                     coat=0.5)
    roof = bkit.pbr("RickshawRoof", base=(0.80, 0.13, 0.11), rough=0.35)
    glass = bkit.pbr("RickshawGlass", base=(0.050, 0.056, 0.064), rough=0.06)
    trim = bkit.preset("black_plastic")
    seat = bkit.pbr("RickshawSeat", base=(0.10, 0.11, 0.13), rough=0.6)

    nose = V.shell("RickshawNose", NOSE, mat=paint, steps=56)
    cabin = V.shell("RickshawCabin", CABIN, mat=paint, steps=56)
    bkit.recalc(nose)
    bkit.recalc(cabin)
    V.glass_band(nose, 820.0, 1010.0, glass, max_nz=0.95, x_lo=1100.0)

    # canopy on four pillars -- open sides are what make it a rickshaw
    bkit.rounded_box("RickshawCanopy", 1500.0, 1400.0, 90.0, r=45.0, segments=3,
                     centre=(-120.0, 0.0, 1655.0), mat=roof)
    for (x, y, tag) in ((560.0, 640.0, "FL"), (560.0, -640.0, "FR"),
                        (-700.0, 640.0, "RL"), (-700.0, -640.0, "RR")):
        bkit.rounded_box("RickshawPillar_" + tag, 70.0, 70.0, 560.0, r=20.0,
                         segments=2, centre=(x, y, 1350.0), mat=trim)
    bkit.rounded_box("RickshawSeat", 380.0, 900.0, 110.0, r=40.0, segments=3,
                     centre=(-560.0, 0.0, 560.0), mat=seat)
    bkit.rounded_box("RickshawBackrest", 100.0, 900.0, 480.0, r=40.0,
                     segments=3, centre=(-720.0, 0.0, 800.0), mat=seat)
    bkit.rounded_box("RickshawFloor", 1500.0, 800.0, 70.0, r=25.0, segments=2,
                     centre=(-100.0, 0.0, 330.0), mat=trim)
    V.mirror_y(V.box_lamp("RickshawHeadlamps", 90.0, 180.0, 130.0,
                          (1280.0, 190.0, 560.0),
                          bkit.pbr("RickshawLens", base=(0.86, 0.86, 0.90),
                                   rough=0.08, transmission=0.5), r=24.0))
    V.mirror_y(V.box_lamp("RickshawTaillamps", 80.0, 150.0, 150.0,
                          (-1235.0, 300.0, 620.0),
                          bkit.pbr("RickshawTailLens", base=(0.46, 0.03, 0.03),
                                   rough=0.11, transmission=0.3), r=22.0))

    wf = V.wheel("RickshawWheelF", SPEC["front_wheel_diameter"], 120.0, 240.0,
                 spokes=6, seg=44)
    V.place_wheels(wf, [(900.0, 0.0, 240.0)], names=["Wheel0"])
    wr = V.wheel("RickshawWheelR", SPEC["rear_wheel_diameter"], 140.0, 280.0,
                 spokes=6, seg=44)
    V.place_wheels(wr, [(-750.0, -560.0, 280.0), (-750.0, 560.0, 280.0)],
                   names=["Wheel1", "Wheel2"])

    return dict(spec=SPEC, parts=14)