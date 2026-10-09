"""
go_kart -- shifter kart, 1800 x 1250 x 700 mm, 1050 mm wheelbase.

The defining ratio in a kart is rear-vs-front WHEEL SIZE, not anything else:
280 mm rear tyres on a 1100 mm rear track against 140 mm front tyres on a 900
mm front track. Get those the wrong way round and it stops being a kart and
starts being a go-kart-shaped thing.

Other real figures: the seat is a moulded shell whose back is level with the
rear axle, the chassis floor is 90 mm off the ground and 1600 mm long, and the
whole machine is only 700 mm tall -- below the driver's shoulders, which is why
a kart reads as open and low even before you see the wheels.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=1800.0,
    width=1250.0,
    height=700.0,
    wheelbase=1050.0,
    rear_track=1100.0,
    front_track=900.0,
    rear_wheel_diameter=280.0,
    front_wheel_diameter=140.0,
    rear_tyre_width=120.0,
    front_tyre_width=90.0,
    floor_height=90.0,
)

CHECKS = [
    dict(name="length", mm=1800.0, tol=5.0, how="bbox_x", part=None),
    dict(name="width", mm=1250.0, tol=5.0, how="bbox_y", part=None),
    dict(name="height", mm=700.0, tol=5.0, how="bbox_z", part=None),
    dict(name="rear_wheel_diameter", mm=280.0, tol=2.0, how="diameter",
         part="Wheel0"),
    dict(name="front_wheel_diameter", mm=140.0, tol=2.0, how="diameter",
         part="Wheel2"),
    dict(name="floor_length", mm=1600.0, tol=5.0, how="bbox_x",
         part="KartFloor"),
]

AX_F = 525.0
AX_R = -525.0


def build():
    frame = bkit.pbr("KartChassis", base=(0.72, 0.16, 0.06), rough=0.24,
                     metal=0.35, coat=0.7)
    seat = bkit.pbr("KartSeat", base=(0.06, 0.06, 0.07), rough=0.55)
    dark = bkit.preset("black_plastic")
    alloy = bkit.preset("brushed_metal")
    rubber = bkit.preset("rubber")

    rf = SPEC["front_wheel_diameter"] / 2.0
    rr = SPEC["rear_wheel_diameter"] / 2.0

    bkit.rounded_box("KartFloor", 1600.0, 1000.0, 60.0, r=25.0, segments=2,
                     centre=(0.0, 0.0, 120.0), mat=frame)
    bkit.rounded_box("KartSeat", 480.0, 480.0, 380.0, r=60.0, segments=3,
                     centre=(-330.0, 0.0, 340.0), mat=seat)
    bkit.rounded_box("KartSidePodL", 680.0, 150.0, 240.0, r=60.0, segments=3,
                     centre=(0.0, 550.0, 230.0), mat=frame)
    V.mirror_y(bkit.rounded_box("KartSidePodR", 680.0, 150.0, 240.0, r=60.0,
                                segments=3, centre=(0.0, -550.0, 230.0),
                                mat=frame))
    bkit.rounded_box("KartNose", 420.0, 380.0, 300.0, r=110.0, segments=3,
                     centre=(700.0, 0.0, 260.0), mat=frame)
    bkit.rounded_box("KartBumper", 120.0, 1250.0, 120.0, r=50.0, segments=3,
                     centre=(890.0, 0.0, 180.0), mat=dark)
    V.mirror_y(bkit.rounded_box("KartBumperRear", 120.0, 1000.0, 110.0,
                                r=45.0, segments=3, centre=(-790.0, 0.0, 180.0),
                                mat=dark))

    # steering: a raked column and a wheel, the one part every kart is missing
    V.strut("KartSteeringColumn", (430.0, 0.0, 200.0), (330.0, 0.0, 560.0),
            16.0, alloy, 12)
    bkit.torus("KartSteeringWheel", 130.0, 14.0, seg_major=32, seg_minor=10,
               centre=(335.0, 0.0, 555.0), axis="Y", mat=dark)

    bkit.rounded_box("KartEngine", 420.0, 420.0, 340.0, r=40.0, segments=3,
                     centre=(-620.0, 200.0, 300.0), mat=alloy)
    V.strut("KartExhaust", (-560.0, 340.0, 320.0), (-150.0, 550.0, 520.0),
            26.0, alloy, 14)
    V.strut("KartAxleFront", (AX_F, -450.0, rf), (AX_F, 450.0, rf), 16.0,
            alloy, 12)
    V.strut("KartAxleRear", (AX_R, -550.0, rr), (AX_R, 550.0, rr), 20.0,
            alloy, 12)

    wr = V.wheel("KartWheelR", SPEC["rear_wheel_diameter"],
                 SPEC["rear_tyre_width"], 130.0, spokes=5, seg=36)
    V.place_wheels(wr, [(AX_R, -550.0, rr), (AX_R, 550.0, rr)],
                   names=["Wheel0", "Wheel1"])
    wf = V.wheel("KartWheelF", SPEC["front_wheel_diameter"],
                 SPEC["front_tyre_width"], 70.0, spokes=4, seg=32)
    V.place_wheels(wf, [(AX_F, -450.0, rf), (AX_F, 450.0, rf)],
                   names=["Wheel2", "Wheel3"])

    return dict(spec=SPEC, parts=15)