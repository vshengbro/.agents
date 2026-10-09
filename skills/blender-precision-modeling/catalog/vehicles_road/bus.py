"""
bus -- 12 m low-floor city bus, 12000 x 2500 x 3200 mm.

A bus is a van scaled and squared-off: the same single loft, with n pushed to
6.5-7 so the slab has genuinely flat sides and a domed roof, and with the
glazing running the whole length in one band. What separates it from the van in
the catalog is the ratio set: 4.8 wheel diameters of body height, a 6000 mm
wheelbase at 0.50 of the length, and 2500 mm of width on a 2100 mm track, so
the wheels tuck well inside the body and there is no visible arch flare.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=12000.0,
    width=2500.0,
    height=3200.0,
    wheelbase=6000.0,
    track=2100.0,
    wheel_diameter=1050.0,
    rim_diameter=508.0,
    tyre_width=295.0,
    floor_height=340.0,
    door_count=2,
)

CHECKS = [
    dict(name="length", mm=12000.0, tol=5.0, how="bbox_x", part=None),
    dict(name="width", mm=2500.0, tol=5.0, how="bbox_y", part="BusBody"),
    dict(name="height", mm=3200.0, tol=5.0, how="bbox_z", part=None),
    dict(name="sill_to_roof", mm=2860.0, tol=5.0, how="bbox_z", part="BusBody"),
    dict(name="wheel_diameter", mm=1050.0, tol=2.0, how="diameter", part="Wheel0"),
]

STATIONS = [
    (6000.0, 980.0, 470.0, 2700.0, 6.6),
    (5900.0, 1120.0, 450.0, 2860.0, 7.0),
    (5600.0, 1200.0, 410.0, 3020.0, 7.0),
    (5100.0, 1240.0, 370.0, 3150.0, 7.2),
    (4600.0, 1250.0, 345.0, 3200.0, 7.4),
    (4200.0, 1250.0, 340.0, 3200.0, 7.4),
    (2500.0, 1250.0, 340.0, 3200.0, 7.4),
    (0.0, 1250.0, 340.0, 3200.0, 7.4),
    (-2500.0, 1250.0, 340.0, 3200.0, 7.4),
    (-4200.0, 1250.0, 340.0, 3200.0, 7.4),
    (-4700.0, 1250.0, 345.0, 3200.0, 7.4),
    (-5200.0, 1240.0, 365.0, 3160.0, 7.2),
    (-5600.0, 1190.0, 395.0, 3060.0, 6.8),
    (-5900.0, 1110.0, 430.0, 2880.0, 6.2),
    (-6000.0, 980.0, 470.0, 2720.0, 6.0),
]


def build():
    paint = bkit.pbr("BusPaint", base=(0.72, 0.14, 0.10), rough=0.26, coat=0.5)
    glass = bkit.pbr("BusGlass", base=(0.045, 0.050, 0.058), rough=0.05)
    trim = bkit.pbr("BusTrim", base=(0.16, 0.17, 0.19), rough=0.38)
    rubber = bkit.preset("rubber")
    lamp_w = bkit.pbr("BusHeadlamp", base=(0.86, 0.86, 0.90), rough=0.08,
                      transmission=0.5)
    lamp_r = bkit.pbr("BusTaillamp", base=(0.50, 0.035, 0.030), rough=0.10,
                      transmission=0.3)

    body = V.shell("BusBody", STATIONS, mat=paint, steps=64)
    r_wheel = SPEC["wheel_diameter"] / 2.0
    V.arch_cut(body, SPEC["wheelbase"] / 2.0, 260.0, 1330.0, r_wheel, 612.0)
    V.arch_cut(body, -SPEC["wheelbase"] / 2.0, 260.0, 1330.0, r_wheel, 612.0)
    bkit.recalc(body)
    V.glass_band(body, 1950.0, 2620.0, glass, max_nz=0.95, x_lo=-5200.0)

    bkit.rounded_box("BusDestination", 44.0, 1700.0, 300.0, r=18.0, segments=2,
                     centre=(5978.0, 0.0, 2500.0), mat=trim)
    bkit.rounded_box("BusBumper", 140.0, 2300.0, 420.0, r=60.0, segments=3,
                     centre=(5920.0, 0.0, 700.0), mat=rubber)
    bkit.rounded_box("BusRearBumper", 140.0, 2300.0, 420.0, r=60.0,
                     segments=3, centre=(-5920.0, 0.0, 700.0), mat=rubber)
    V.mirror_y(V.box_lamp("BusHeadlamps", 120.0, 420.0, 300.0,
                          (5900.0, 820.0, 1100.0), lamp_w, r=34.0))
    V.mirror_y(V.box_lamp("BusTaillamps", 100.0, 340.0, 620.0,
                          (-5940.0, 880.0, 1600.0), lamp_r, r=22.0))
    # two door leaves ahead of the front axle, laid out with a real gap between
    for i, (x, _w) in enumerate(bkit.lay_out([1150.0, 1150.0], gap=300.0,
                                              centre=True)):
        bkit.rounded_box("BusDoor%02d" % i, 1150.0, 40.0, 1900.0, r=15.0,
                         segments=2, centre=(x + 3900.0, 1245.0, 1250.0),
                         mat=trim)
    bkit.rounded_box("BusSideSkirt", 9600.0, 60.0, 320.0, r=24.0, segments=2,
                     centre=(0.0, 1250.0, 700.0), mat=trim)
    bkit.rounded_box("BusRoofVent", 1400.0, 900.0, 70.0, r=30.0, segments=2,
                     centre=(500.0, 0.0, 3165.0), mat=trim)
    V.mirror_y(bkit.rounded_box("BusMirrors", 220.0, 110.0, 340.0, r=45.0,
                                segments=3, centre=(4950.0, 1340.0, 2700.0),
                                mat=trim))

    w = V.wheel("BusWheel", SPEC["wheel_diameter"], SPEC["tyre_width"],
                SPEC["rim_diameter"], spokes=8, seg=56)
    V.place_wheels(w, [(3000.0, -1050.0, r_wheel), (3000.0, 1050.0, r_wheel),
                       (-3000.0, -1050.0, r_wheel), (-3000.0, 1050.0, r_wheel)])

    return dict(spec=SPEC, parts=12)