"""
tractor -- 100 hp farm tractor with ROPS cab, 4200 x 2100 x 2600 mm.

The proportion that makes a tractor is the rear wheel: a 1400 mm diameter on a
480 mm tyre, against a 700 mm front wheel on a 300 mm tyre. That 2:1 diameter
ratio and the rear track being 20 % wider than the front track is the entire
read -- everything else on a tractor is secondary.

Real figures: 2400 mm wheelbase, rear axle 880 mm from the centreline (so the
tyres clear the transmission housing), a bonnet top at 1600 mm and an exhaust
that ends 200 mm above the ROPS roof at 2600 mm.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=4200.0,
    width=2100.0,
    height=2600.0,
    wheelbase=2400.0,
    rear_track=1600.0,
    front_track=1520.0,
    rear_wheel_diameter=1400.0,
    front_wheel_diameter=700.0,
    rear_tyre_width=480.0,
    front_tyre_width=300.0,
    bonnet_height=1600.0,
)

CHECKS = [
    dict(name="length", mm=4200.0, tol=6.0, how="bbox_x", part=None),
    dict(name="width", mm=2100.0, tol=6.0, how="bbox_y", part=None),
    dict(name="height", mm=2600.0, tol=6.0, how="bbox_z", part=None),
    dict(name="rear_wheel_diameter", mm=1400.0, tol=3.0, how="diameter",
         part="Wheel0"),
    dict(name="front_wheel_diameter", mm=700.0, tol=3.0, how="diameter",
         part="Wheel2"),
    dict(name="bonnet_length", mm=1600.0, tol=6.0, how="bbox_x",
         part="TractorHood"),
]

AX_R = -800.0
AX_F = 1600.0


def build():
    paint = bkit.pbr("TractorPaint", base=(0.62, 0.14, 0.05), rough=0.24,
                     coat=0.5)
    dark = bkit.preset("dark_metal")
    glass = bkit.pbr("TractorGlass", base=(0.055, 0.060, 0.068), rough=0.06)
    seat = bkit.pbr("TractorSeat", base=(0.08, 0.08, 0.09), rough=0.6)

    rr = SPEC["rear_wheel_diameter"] / 2.0
    rf = SPEC["front_wheel_diameter"] / 2.0

    bkit.rounded_box("TractorHood", 1600.0, 1100.0, 900.0, r=90.0, segments=3,
                     centre=(1400.0, 0.0, 1150.0), mat=paint)
    bkit.rounded_box("TractorTransmission", 1900.0, 900.0, 700.0, r=60.0,
                     segments=3, centre=(-200.0, 0.0, 850.0), mat=paint)
    bkit.rounded_box("TractorRearHousing", 1300.0, 1000.0, 800.0, r=80.0,
                     segments=3, centre=(-750.0, 0.0, 900.0), mat=paint)

    # ROPS: four posts and a roof, which is what sets the 2600 mm height
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=900.0,
                                                   pitch_y=1800.0)):
        bkit.rounded_box("TractorRops%02d" % i, 90.0, 90.0, 1750.0, r=25.0,
                         segments=2, centre=(x - 250.0, y, 1625.0), mat=dark)
    bkit.rounded_box("TractorRoof", 1200.0, 2100.0, 110.0, r=50.0, segments=3,
                     centre=(-250.0, 0.0, 2545.0), mat=paint)
    V.mirror_y(bkit.rounded_box("TractorCabSide", 900.0, 40.0, 900.0, r=18.0,
                                segments=2, centre=(-250.0, 905.0, 1900.0),
                                mat=glass))

    bkit.rounded_box("TractorSeat", 480.0, 520.0, 120.0, r=50.0, segments=3,
                     centre=(-250.0, 0.0, 1250.0), mat=seat)
    bkit.rounded_box("TractorFenders", 1400.0, 2100.0, 90.0, r=40.0,
                     segments=3, centre=(-800.0, 0.0, 1780.0), mat=paint)
    bkit.cylinder("TractorExhaust", 55.0, 1100.0, segments=18, axis="Z",
                  centre=(900.0, 420.0, 1950.0), mat=dark)
    bkit.rounded_box("TractorGrille", 90.0, 900.0, 520.0, r=40.0, segments=3,
                     centre=(2255.0, 0.0, 900.0), mat=dark)
    V.mirror_y(V.box_lamp("TractorHeadlamps", 90.0, 200.0, 190.0,
                          (2230.0, 380.0, 1400.0),
                          bkit.pbr("TractorLens", base=(0.86, 0.86, 0.90),
                                   rough=0.08, transmission=0.5), r=24.0))
    # rear linkage and drawbar: the equipment end of a tractor
    bkit.rounded_box("TractorLinkage", 260.0, 900.0, 700.0, r=40.0, segments=2,
                     centre=(-1750.0, 0.0, 600.0), mat=dark)
    bkit.rounded_box("TractorDrawbar", 500.0, 180.0, 120.0, r=30.0, segments=2,
                     centre=(-1650.0, 0.0, 520.0), mat=dark)
    bkit.rounded_box("TractorFrontWeight", 260.0, 900.0, 500.0, r=40.0,
                     segments=2, centre=(2050.0, 0.0, 700.0), mat=dark)
    V.mirror_y(bkit.rounded_box("TractorStep", 380.0, 160.0, 60.0, r=16.0,
                                segments=2, centre=(500.0, 560.0, 700.0),
                                mat=dark))

    wr = V.wheel("TractorWheelR", SPEC["rear_wheel_diameter"],
                 SPEC["rear_tyre_width"], 700.0, spokes=8, seg=56)
    V.place_wheels(wr, [(AX_R, -800.0, rr), (AX_R, 800.0, rr)],
                   names=["Wheel0", "Wheel1"])
    wf = V.wheel("TractorWheelF", SPEC["front_wheel_diameter"],
                 SPEC["front_tyre_width"], 380.0, spokes=6, seg=44)
    V.place_wheels(wf, [(AX_F, -760.0, rf), (AX_F, 760.0, rf)],
                   names=["Wheel2", "Wheel3"])

    return dict(spec=SPEC, parts=17)