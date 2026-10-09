"""
truck_tractor -- road tractor unit (no trailer), 6600 x 2500 x 3800 mm.

A tractor unit is a cab on a chassis, not a body: the loft builds the cab, and
everything behind it is frame rails, a fifth wheel and tanks. That separation
is what the catalog needs, because a tractor unit without a trailer is a very
distinctive silhouette -- long flat deck, sleeper-cab mass at the front, and
nothing above the deck behind it.

Real figures:
  * steer axle at +2600, drive tandem at -1150 and -1950: wheelbase to the
    first drive axle is 3800, and the tandem's 800 mm spread is what carries
    the kingpin load;
  * 1050 mm wheels on 315 mm tyres under a 3800 mm cab: 3.6 wheel diameters;
  * deck top at 1300 mm, which is the trailer kingpin height.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=6600.0,
    width=2500.0,
    height=3800.0,
    wheelbase=3800.0,
    track=2100.0,
    wheel_diameter=1050.0,
    rim_diameter=508.0,
    tyre_width=315.0,
    deck_height=1300.0,
    tandem_spacing=800.0,
)

CHECKS = [
    dict(name="length", mm=6600.0, tol=5.0, how="bbox_x", part=None),
    dict(name="width", mm=2500.0, tol=5.0, how="bbox_y", part="TruckCab"),
    dict(name="height", mm=3800.0, tol=5.0, how="bbox_z", part=None),
    dict(name="cab_sill_to_roof", mm=2990.0, tol=6.0, how="bbox_z",
         part="TruckCab"),
    dict(name="deck_length", mm=6300.0, tol=5.0, how="bbox_x",
         part="TruckDeck"),
    dict(name="wheel_diameter", mm=1050.0, tol=2.0, how="diameter", part="Wheel0"),
]

CAB = [
    (3300.0, 940.0, 900.0, 1900.0, 5.0),
    (3180.0, 1120.0, 860.0, 2350.0, 5.6),
    (2950.0, 1230.0, 830.0, 2900.0, 6.2),
    (2700.0, 1250.0, 820.0, 3400.0, 6.6),
    (2350.0, 1250.0, 815.0, 3760.0, 7.0),
    (1900.0, 1250.0, 812.0, 3800.0, 7.2),
    (1200.0, 1250.0, 810.0, 3800.0, 7.2),
    (760.0, 1230.0, 810.0, 3780.0, 6.8),
    (500.0, 1150.0, 812.0, 3700.0, 6.0),
    (420.0, 1000.0, 830.0, 3560.0, 5.4),
]


def build():
    paint = bkit.pbr("TruckCabPaint", base=(0.09, 0.30, 0.46), rough=0.20,
                     metal=0.30, coat=0.7)
    glass = bkit.pbr("TruckCabGlass", base=(0.045, 0.050, 0.058), rough=0.05)
    steel = bkit.preset("dark_metal")
    frame = bkit.pbr("TruckFrame", base=(0.20, 0.21, 0.23), rough=0.45)
    rubber = bkit.preset("rubber")
    chrome = bkit.preset("polished_metal")
    lamp_w = bkit.pbr("TractorHeadlamp", base=(0.86, 0.86, 0.90), rough=0.08,
                      transmission=0.5)

    cab = V.shell("TruckCab", CAB, mat=paint, steps=64)
    r_wheel = SPEC["wheel_diameter"] / 2.0
    V.arch_cut(cab, 2600.0, 240.0, 1330.0, r_wheel, 610.0)
    bkit.recalc(cab)
    V.glass_band(cab, 2400.0, 3600.0, glass, max_nz=0.95, x_lo=1800.0)

    # chassis: two rails plus the flat deck that carries the kingpin
    V.mirror_y(bkit.rounded_box("TruckFrameRail", 6300.0, 160.0, 380.0, r=30.0,
                                segments=2, centre=(-150.0, 520.0, 1010.0),
                                mat=frame))
    bkit.rounded_box("TruckDeck", 6300.0, 2200.0, 120.0, r=25.0, segments=2,
                     centre=(-150.0, 0.0, 1240.0), mat=frame)
    bkit.cylinder("FifthWheel", 500.0, 90.0, segments=48, centre=(-1050.0, 0.0,
                                                                 1345.0),
                  mat=steel)
    V.mirror_y(bkit.cylinder("FuelTank", 340.0, 1000.0, segments=32,
                             axis="X", centre=(250.0, 900.0, 880.0),
                             mat=chrome))
    bkit.rounded_box("TractorBumper", 220.0, 2500.0, 520.0, r=70.0, segments=3,
                     centre=(3190.0, 0.0, 700.0), mat=steel)
    bkit.rounded_box("TractorGrille", 120.0, 1700.0, 700.0, r=40.0, segments=3,
                     centre=(3240.0, 0.0, 1750.0), mat=chrome)
    V.mirror_y(V.box_lamp("TractorHeadlamps", 110.0, 460.0, 260.0,
                          (3245.0, 950.0, 1030.0), lamp_w, r=34.0))
    V.mirror_y(bkit.rounded_box("TractorSteps", 420.0, 220.0, 90.0, r=16.0,
                                segments=2, centre=(2470.0, 1230.0, 700.0),
                                mat=steel))
    V.mirror_y(bkit.cylinder("Exhaust", 70.0, 2700.0, segments=20, axis="Z",
                             centre=(2300.0, 1300.0, 2450.0), mat=chrome))
    bkit.rounded_box("TractorMudflap", 40.0, 700.0, 700.0, r=15.0, segments=2,
                     centre=(-2250.0, 0.0, 400.0), mat=rubber)

    w = V.wheel("TractorWheel", SPEC["wheel_diameter"], SPEC["tyre_width"],
                SPEC["rim_diameter"], spokes=8, seg=56)
    r = SPEC["wheel_diameter"] / 2.0
    V.place_wheels(w, [(2600.0, -1050.0, r), (2600.0, 1050.0, r),
                       (-1150.0, -1050.0, r), (-1150.0, 1050.0, r),
                       (-1950.0, -1050.0, r), (-1950.0, 1050.0, r)],
                   names=["Wheel0", "Wheel1", "Wheel2", "Wheel3",
                          "Wheel4", "Wheel5"])

    return dict(spec=SPEC, parts=15)