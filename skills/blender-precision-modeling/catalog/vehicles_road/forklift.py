"""
forklift -- counterbalance forklift, 3700 x 1150 x 2200 mm, mast lowered.

A forklift is three separate volumes and the silhouette is the SPACE between
them: the counterweight at the back, the operator cage in the middle, and the
mast plus forks reaching forward. There is no bodywork at all.

Real figures, and two of them run backwards from a car on purpose:
  * 580 mm front wheels on a 900 mm gauge carrying the load, 460 mm rear
    wheels on an 800 mm gauge -- the FRONT track is wider than the rear, which
    is the opposite of a car and reads as "industrial" immediately;
  * the chassis between the wheels is only 700 mm wide, narrower than either
    track, which is why the front wheels stand proud of the body;
  * mast channels 2100 mm tall, upright height 2200 mm, forks 1150 x 130 x 100.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=3700.0,
    body_length=2100.0,
    width=1150.0,
    height=2200.0,
    front_track=900.0,
    rear_track=800.0,
    front_wheel_diameter=580.0,
    rear_wheel_diameter=460.0,
    mast_height=2100.0,
    fork_length=1150.0,
)

CHECKS = [
    dict(name="length", mm=3700.0, tol=6.0, how="bbox_x", part=None),
    dict(name="width", mm=1150.0, tol=6.0, how="bbox_y", part=None),
    dict(name="height", mm=2200.0, tol=6.0, how="bbox_z", part=None),
    dict(name="front_wheel_diameter", mm=580.0, tol=2.0, how="diameter",
         part="Wheel0"),
    dict(name="rear_wheel_diameter", mm=460.0, tol=2.0, how="diameter",
         part="Wheel2"),
    dict(name="fork_length", mm=1150.0, tol=4.0, how="bbox_x",
         part="ForkliftForks"),
]

AX_F = 500.0
AX_R = -800.0


def build():
    paint = bkit.pbr("ForkliftPaint", base=(0.78, 0.55, 0.03), rough=0.26,
                     coat=0.4)
    steel = bkit.preset("dark_metal")
    frame = bkit.pbr("ForkliftFrame", base=(0.22, 0.23, 0.25), rough=0.42)
    seat = bkit.pbr("ForkliftSeat", base=(0.07, 0.07, 0.08), rough=0.6)

    rf = SPEC["front_wheel_diameter"] / 2.0
    rr = SPEC["rear_wheel_diameter"] / 2.0

    # chassis is narrower than the front track on purpose -- the wheels stand
    # proud of it, as they do on every real counterbalance truck
    bkit.rounded_box("ForkliftChassis", 1900.0, 700.0, 420.0, r=60.0,
                     segments=3, centre=(-250.0, 0.0, 480.0), mat=frame)
    bkit.rounded_box("ForkliftCounterweight", 700.0, 1150.0, 760.0, r=110.0,
                     segments=3, centre=(-1050.0, 0.0, 850.0), mat=paint)
    bkit.rounded_box("ForkliftCowl", 700.0, 700.0, 500.0, r=80.0, segments=3,
                     centre=(550.0, 0.0, 1000.0), mat=paint)
    bkit.rounded_box("ForkliftSeat", 460.0, 500.0, 120.0, r=50.0, segments=3,
                     centre=(-380.0, 0.0, 1000.0), mat=seat)
    bkit.rounded_box("ForkliftBackrest", 80.0, 500.0, 420.0, r=30.0,
                     segments=2, centre=(-620.0, 0.0, 1200.0), mat=seat)

    # overhead guard: four posts and a five-bar roof, both from grid_positions
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=1000.0,
                                                   pitch_y=1000.0)):
        bkit.rounded_box("ForkliftGuard%02d" % i, 90.0, 90.0, 1400.0, r=22.0,
                         segments=2, centre=(x - 300.0, y, 1450.0),
                         mat=steel)
    # Roof bars span the centreline OUT to each side post (y * 0.5), so the
    # guard is as wide as the truck. Centring them on the posts instead makes a
    # 2000 mm roof on a 1150 mm truck.
    for i, (x, y) in enumerate(bkit.grid_positions(cols=3, rows=2,
                                                   pitch_x=430.0,
                                                   pitch_y=1000.0)):
        bkit.rounded_box("ForkliftRoofBar%02d" % i, 80.0, 500.0, 60.0,
                         r=20.0, segments=2,
                         centre=(x - 300.0, y * 0.5, 2170.0), mat=steel)
    bkit.rounded_box("ForkliftSteering", 420.0, 420.0, 60.0, r=90.0,
                     segments=3, centre=(350.0, 0.0, 1250.0), mat=frame)
    bkit.cylinder("ForkliftLever", 18.0, 500.0, segments=12, axis="Z",
                  centre=(450.0, 320.0, 1200.0), mat=steel)

    # mast: two channels on a cross tie, then the carriage and the forks
    V.mirror_y(bkit.rounded_box("ForkliftMast", 160.0, 130.0, 2100.0, r=25.0,
                                segments=2, centre=(1000.0, 495.0, 1100.0),
                                mat=steel))
    bkit.rounded_box("ForkliftMastTie", 160.0, 1140.0, 120.0, r=25.0,
                     segments=2, centre=(1000.0, 0.0, 2050.0), mat=steel)
    bkit.rounded_box("ForkliftCarriage", 140.0, 1150.0, 700.0, r=35.0,
                     segments=2, centre=(1130.0, 0.0, 450.0), mat=steel)
    V.mirror_y(bkit.rounded_box("ForkliftForks", SPEC["fork_length"], 130.0,
                                100.0, r=18.0, segments=2,
                                centre=(1725.0, 350.0, 150.0), mat=steel))
    bkit.cylinder("ForkliftHydraulic", 70.0, 1900.0, segments=16, axis="Z",
                  centre=(830.0, 0.0, 1000.0), mat=frame)
    V.mirror_y(bkit.rounded_box("ForkliftBeacon", 120.0, 120.0, 90.0, r=40.0,
                                segments=3, centre=(-300.0, 450.0, 2150.0),
                                mat=bkit.pbr("ForkliftBeaconMat",
                                             base=(0.85, 0.55, 0.03),
                                             rough=0.2)))

    wf = V.wheel("ForkliftWheelF", SPEC["front_wheel_diameter"], 180.0, 290.0,
                 spokes=5, seg=40)
    V.place_wheels(wf, [(AX_F, -450.0, rf), (AX_F, 450.0, rf)],
                   names=["Wheel0", "Wheel1"])
    wr = V.wheel("ForkliftWheelR", SPEC["rear_wheel_diameter"], 160.0, 230.0,
                 spokes=5, seg=36)
    V.place_wheels(wr, [(AX_R, -400.0, rr), (AX_R, 400.0, rr)],
                   names=["Wheel2", "Wheel3"])

    return dict(spec=SPEC, parts=22)