"""
hatchback -- 5-door compact hatchback, 4200 x 1750 x 1450 mm on a 2600 mm
wheelbase.

The numbers that make it read as a hatchback rather than "a car":

  * wheelbase / length = 2600/4200 = 0.62, which is the compact-car band
    (a sedan sits near 0.59 and a van near 0.63 -- what actually separates
    them is the overhang distribution and the roofline, not this ratio);
  * track 1520 against a 1750 body: the tyres sit 30 mm inboard of the
    widest point, the way a transverse-engined C-segment car does;
  * 620 mm wheels under a 1450 mm roof leaves 840 mm of body between the
    contact patch and the headroom, which is what you see as "not a van";
  * the tailgate drops over 330 mm of run for 390 mm of fall -- about 40 deg
    off vertical, the classic hatch slope.

The whole car is ONE loft along X. That is deliberate: the silhouette (nose
rise, bonnet, screen rake, roof, tailgate) comes from the section heights, and
two separate lofts -- lower body plus greenhouse -- always leave a shoulder
line that fights the roof in a three-quarter view.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    length=4200.0,
    width=1750.0,
    height=1450.0,
    wheelbase=2600.0,
    track=1520.0,
    wheel_diameter=620.0,
    rim_diameter=381.0,
    tyre_width=205.0,
    sill_height=235.0,
    front_overhang=800.0,
    rear_overhang=800.0,
)

CHECKS = [
    dict(name="length", mm=4200.0, tol=2.0, how="bbox_x", part=None),
    dict(name="width", mm=1750.0, tol=2.0, how="bbox_y", part="HatchbackBody"),
    dict(name="height", mm=1450.0, tol=2.0, how="bbox_z", part=None),
    dict(name="width_over_mirrors", mm=1856.0, tol=2.0, how="bbox_y", part=None),
    dict(name="sill_to_roof", mm=1215.0, tol=2.0, how="bbox_z",
         part="HatchbackBody"),
    dict(name="wheel_diameter", mm=620.0, tol=1.0, how="diameter", part="Wheel0"),
]

# (x, half_width, sill_z, roof_z, superellipse_n) -- front (+X) to rear (-X)
STATIONS = [
    (2100.0, 800.0, 330.0, 800.0, 3.8),
    (2020.0, 846.0, 305.0, 828.0, 3.8),
    (1880.0, 866.0, 285.0, 852.0, 3.7),
    (1700.0, 872.0, 268.0, 874.0, 3.7),
    (1420.0, 875.0, 250.0, 918.0, 3.7),
    (1100.0, 875.0, 238.0, 972.0, 3.7),
    (900.0, 875.0, 235.0, 995.0, 3.7),
    (640.0, 871.0, 235.0, 1185.0, 3.6),
    (420.0, 864.0, 235.0, 1352.0, 3.4),
    (250.0, 855.0, 238.0, 1443.0, 3.2),
    (-150.0, 853.0, 240.0, 1450.0, 3.2),
    (-700.0, 858.0, 242.0, 1450.0, 3.3),
    (-1150.0, 858.0, 246.0, 1442.0, 3.4),
    (-1450.0, 850.0, 254.0, 1396.0, 3.4),
    (-1660.0, 836.0, 266.0, 1252.0, 3.3),
    (-1830.0, 826.0, 300.0, 1020.0, 3.4),
    (-1940.0, 800.0, 320.0, 940.0, 3.4),
    (-2040.0, 760.0, 340.0, 880.0, 3.5),
    (-2100.0, 700.0, 370.0, 840.0, 3.5),
]


def build():
    paint = bkit.pbr("HatchPaint", base=(0.10, 0.26, 0.64), rough=0.16,
                     metal=0.30, coat=0.8)
    glass = bkit.pbr("HatchGlass", base=(0.055, 0.062, 0.072), rough=0.05)
    trim = bkit.preset("black_plastic")
    lamp_w = bkit.pbr("HeadlampLens", base=(0.80, 0.80, 0.84), rough=0.09,
                      transmission=0.55, ior=1.45)
    lamp_r = bkit.pbr("TailLens", base=(0.45, 0.035, 0.030), rough=0.10,
                      transmission=0.35)

    body = V.shell("HatchbackBody", STATIONS, mat=paint, steps=64)

    r_wheel = SPEC["wheel_diameter"] / 2.0
    V.arch_cut(body, SPEC["wheelbase"] / 2.0, 180.0, 940.0, r_wheel, 352.0)
    V.arch_cut(body, -SPEC["wheelbase"] / 2.0, 180.0, 940.0, r_wheel, 352.0)
    bkit.recalc(body)
    # belt 1000, headroom 1385; max_nz 0.90 keeps the horizontal roof and bonnet
    # body-coloured while still catching the 35-deg-from-horizontal windscreen.
    V.glass_band(body, 1000.0, 1385.0, glass, max_nz=0.90)

    # lamps: they sit proud of the flank, which is what gives the nose a face
    V.mirror_y(V.box_lamp("Headlights", 120.0, 300.0, 132.0,
                          (2000.0, 600.0, 686.0), lamp_w, r=26.0))
    V.mirror_y(V.box_lamp("Taillights", 96.0, 230.0, 176.0,
                          (-1930.0, 640.0, 792.0), lamp_r, r=22.0))

    bkit.rounded_box("HatchbackGrille", 70.0, 900.0, 150.0, r=18.0, segments=3,
                     centre=(2062.0, 0.0, 560.0), mat=trim)

    V.mirror_y(bkit.rounded_box("HatchbackMirrors", 130.0, 96.0, 78.0, r=24.0,
                                segments=3, centre=(700.0, 880.0, 1035.0),
                                mat=paint))

    w = V.wheel("HatchWheel", SPEC["wheel_diameter"], SPEC["tyre_width"],
                SPEC["rim_diameter"], spokes=5, seg=48)
    V.place_wheels(w, V.corners(SPEC["wheelbase"], SPEC["track"], r_wheel))

    return dict(spec=SPEC, parts=9)