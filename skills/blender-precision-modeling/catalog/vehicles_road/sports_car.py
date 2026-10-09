"""
sports_car -- mid-engined two-seat sports car, 4450 x 1900 x 1230 mm.

The proportions that matter, all measured off real wedge-shaped sports cars:

  * height/length = 1230/4450 = 0.276. A saloon is 0.305, an SUV 0.38. Below
    about 0.29 the greenhouse has to be low AND the wheel arches have to cut
    deep, or it just reads as a small saloon;
  * front 660 mm / rear 690 mm wheels on a 265 / 310 mm tyre. The rear tyre is
    17 % wider than the front; that stagger is the single clearest cue;
  * sill at 175 mm and 1900 mm of track: a sports car's shoulder is wider than
    its roof, the opposite of a hatchback;
  * 70 mm of ground clearance under the splitter, not the 235 mm a saloon has.

Front and rear wheels are DIFFERENT, so they are built separately and placed
separately -- never one wheel repeated four times.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=4450.0,
    width=1900.0,
    height=1230.0,
    wheelbase=2600.0,
    front_track=1620.0,
    rear_track=1650.0,
    front_wheel_diameter=660.0,
    rear_wheel_diameter=690.0,
    front_tyre_width=265.0,
    rear_tyre_width=310.0,
    ground_clearance=175.0,
)

CHECKS = [
    dict(name="length", mm=4450.0, tol=2.0, how="bbox_x", part=None),
    dict(name="width", mm=1900.0, tol=2.0, how="bbox_y", part="SportsBody"),
    dict(name="height", mm=1230.0, tol=2.0, how="bbox_z", part=None),
    dict(name="front_wheel_diameter", mm=660.0, tol=1.0, how="diameter",
         part="Wheel0"),
    dict(name="rear_wheel_diameter", mm=690.0, tol=1.0, how="diameter",
         part="Wheel2"),
    dict(name="rear_tyre_width", mm=310.0, tol=1.0, how="bbox_y", part="Wheel2"),
]

STATIONS = [
    (2225.0, 780.0, 250.0, 640.0, 3.0),
    (2120.0, 860.0, 215.0, 700.0, 3.4),
    (1950.0, 908.0, 196.0, 782.0, 3.6),
    (1700.0, 932.0, 185.0, 862.0, 3.7),
    (1400.0, 942.0, 180.0, 918.0, 3.7),
    (1150.0, 946.0, 178.0, 958.0, 3.6),
    (900.0, 936.0, 176.0, 1010.0, 3.5),
    (600.0, 918.0, 175.0, 1180.0, 3.4),
    (380.0, 906.0, 174.0, 1230.0, 3.2),
    (-100.0, 906.0, 173.0, 1230.0, 3.2),
    (-700.0, 918.0, 174.0, 1226.0, 3.2),
    (-1050.0, 942.0, 180.0, 1190.0, 3.3),
    (-1350.0, 950.0, 192.0, 1120.0, 3.4),
    (-1750.0, 950.0, 202.0, 1092.0, 3.5),
    (-2050.0, 932.0, 224.0, 1082.0, 3.6),
    (-2225.0, 866.0, 282.0, 1032.0, 3.5),
]


def build():
    paint = bkit.pbr("SportsPaint", base=(0.72, 0.30, 0.02), rough=0.13,
                     metal=0.35, coat=0.9)
    glass = bkit.pbr("SportsGlass", base=(0.040, 0.044, 0.050), rough=0.04)
    carbon = bkit.pbr("Carbon", base=(0.055, 0.055, 0.060), rough=0.32)
    lamp_r = bkit.pbr("SportsTaillamp", base=(0.40, 0.025, 0.022), rough=0.09,
                      emission=(0.5, 0.03, 0.02), emission_strength=0.6)

    body = V.shell("SportsBody", STATIONS, mat=paint, steps=64)
    V.arch_cut(body, 1300.0, 200.0, 1015.0, 330.0, 372.0)
    V.arch_cut(body, -1300.0, 200.0, 1015.0, 345.0, 392.0)
    bkit.recalc(body)
    V.glass_band(body, 780.0, 1170.0, glass, max_nz=0.92)

    # rear wing: the single cue that says "this one is fast"
    bkit.rounded_box("SportsWing", 300.0, 1560.0, 46.0, r=18.0, segments=3,
                     centre=(-1880.0, 0.0, 1140.0), mat=carbon)
    V.mirror_y(bkit.rounded_box("SportsWingPost", 110.0, 44.0, 190.0, r=12.0,
                                segments=2, centre=(-1880.0, 250.0, 1040.0),
                                mat=carbon))
    V.mirror_y(bkit.rounded_box("SportsSplitter", 460.0, 1760.0, 44.0, r=16.0,
                                segments=2, centre=(1990.0, 0.0, 190.0),
                                mat=carbon))
    V.mirror_y(bkit.rounded_box("SportsSkirt", 900.0, 120.0, 150.0, r=30.0,
                                segments=3, centre=(500.0, 890.0, 250.0),
                                mat=carbon))
    V.mirror_y(V.box_lamp("SportsTaillamps", 90.0, 380.0, 110.0,
                          (-2180.0, 600.0, 830.0), lamp_r, r=18.0))
    V.mirror_y(V.box_lamp("SportsHeadlamps", 110.0, 300.0, 120.0,
                          (2110.0, 640.0, 660.0),
                          bkit.pbr("SportsHeadlamp", base=(0.85, 0.86, 0.90),
                                   rough=0.06, transmission=0.6), r=20.0))
    bkit.rounded_box("SportsDiffuser", 460.0, 1500.0, 160.0, r=30.0, segments=3,
                     centre=(-1990.0, 0.0, 250.0), mat=carbon)

    rf = SPEC["front_wheel_diameter"] / 2.0
    rr = SPEC["rear_wheel_diameter"] / 2.0
    wf = V.wheel("SportsWheelF", SPEC["front_wheel_diameter"],
                 SPEC["front_tyre_width"], 457.0, spokes=10, seg=48)
    V.place_wheels(wf, [(1300.0, -SPEC["front_track"] / 2.0, rf),
                        (1300.0, SPEC["front_track"] / 2.0, rf)],
                   names=["Wheel0", "Wheel1"])
    wr = V.wheel("SportsWheelR", SPEC["rear_wheel_diameter"],
                 SPEC["rear_tyre_width"], 464.0, spokes=10, seg=48)
    V.place_wheels(wr, [(-1300.0, -SPEC["rear_track"] / 2.0, rr),
                        (-1300.0, SPEC["rear_track"] / 2.0, rr)],
                   names=["Wheel2", "Wheel3"])

    return dict(spec=SPEC, parts=13)