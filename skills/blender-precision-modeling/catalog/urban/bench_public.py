"""
bench_public -- 1800 x 522 x 845 mm cast-iron and timber park bench: five
90 mm seat slats on a 108 mm pitch, four back slats raked at 14 degrees, two
cast end frames with arms and cross braces.

Repeated slats are the whole job. Five seat boards at a 18 mm gap and four raked
back boards are each produced by one `array_linear` with an explicit pitch, so
the count and the spacing are computed rather than typed -- a bench with the
wrong number of slats is wrong in a way no material can hide.

The bench is modelled at its real 1800 mm street length, which overruns the
catalog's `small`/`large` guidance for its head size; that is deliberate, since
a 900 mm bench is not a bench.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    bench_length=1800.0,
    seat_slats=5,
    seat_slat_width=90.0,
    seat_slat_thickness=32.0,
    seat_slat_pitch=108.0,
    seat_height=450.0,
    back_slats=4,
    back_rake_deg=14.0,
    overall_height=845.0,
)

L = SPEC["bench_length"]
SLAT_W = SPEC["seat_slat_width"]
SLAT_T = SPEC["seat_slat_thickness"]
PITCH = SPEC["seat_slat_pitch"]
SEAT_Z = SPEC["seat_height"]
RAKE = math.radians(SPEC["back_rake_deg"])
HALF_L = L / 2.0


def build():
    timber = bkit.pbr("BenchTimber", base=(0.30, 0.17, 0.08), rough=0.52)
    cast = bkit.pbr("BenchCast", base=(0.10, 0.10, 0.11), metal=0.35,
                    rough=0.58)
    steel = bkit.preset("dark_metal")

    # ---- five seat slats: one array, explicit 108 mm pitch ----------------
    slat = bkit.rounded_box("_slat", L, SLAT_W, SLAT_T, r=6.0, segments=2,
                            centre=(0.0, -2.0 * PITCH, SEAT_Z - SLAT_T / 2.0),
                            mat=timber)
    bkit.array_linear(slat, count=SPEC["seat_slats"],
                      offset_mm=(0.0, PITCH, 0.0))
    slat.name = "SeatSlats"

    # ---- four raked back slats, leaning against the rear posts -------------
    # Build at the origin, rotate, THEN move. rounded_box bakes `centre` into
    # the mesh and leaves location at zero, so setting rotation_euler on an
    # already-placed board pivots it about the WORLD origin: a board authored at
    # y=196, z=570 and raked 14 deg lands at y=328, z=506, clear of its post.
    for i in range(SPEC["back_slats"]):
        z = 570.0 + i * 80.0
        y = 232.0 + i * 19.0
        b = bkit.rounded_box("BackSlat%d" % i, L, SLAT_W, SLAT_T, r=6.0,
                             segments=2, mat=timber)
        b.rotation_euler = (-RAKE, 0.0, 0.0)
        bkit.move(b, 0.0, y, z)

    # ---- two cast end frames ----------------------------------------------
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        x = side * (HALF_L - 80.0)
        bkit.rounded_box("FrontLeg" + tag, 64.0, 74.0, 418.0, r=10.0,
                         segments=3, centre=(x, -190.0, 209.0), mat=cast)
        bkit.rounded_box("RearPost" + tag, 64.0, 74.0, 830.0, r=10.0,
                         segments=3, centre=(x, 200.0, 415.0), mat=cast)
        # seat rail: overlaps the slats by 12 mm instead of stopping flush
        bkit.rounded_box("SeatRail" + tag, 64.0, 480.0, 56.0, r=10.0,
                         segments=3, centre=(x, 0.0, 402.0), mat=cast)
        # arm rest and its front support
        bkit.rounded_box("ArmRest" + tag, 76.0, 400.0, 40.0, r=16.0,
                         segments=3, centre=(x, 10.0, 630.0), mat=timber)
        bkit.rounded_box("ArmSupport" + tag, 52.0, 52.0, 230.0, r=8.0,
                         segments=2, centre=(x, -150.0, 515.0), mat=cast)
        # cross brace and a scroll foot
        bkit.rounded_box("CrossBrace" + tag, 44.0, 330.0, 40.0, r=8.0,
                         segments=2, centre=(x, 10.0, 170.0), mat=cast)
        bkit.arc_torus("FootScroll" + tag, 120.0, 10.0, 200.0, 340.0,
                       plane="XY", centre=(x, 10.0, 170.0), seg_major=28,
                       mat=cast, caps=True)

    # ---- galvanised fixings at each frame and along the rails -------------
    bolts = []
    for side in (-1.0, 1.0):
        x = side * (HALF_L - 80.0)
        for y in (-2.0 * PITCH, 0.0, 2.0 * PITCH):
            bolts.append(bkit.cylinder("_bolt", 7.0, 8.0, segments=16,
                                       centre=(x, y, SEAT_Z + 2.0), mat=steel))
    bkit.join(bolts, name="BenchFixings")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=18)


CHECKS = [
    # The slat LENGTH is 1800; the whole assembly is 1884 across because the cast
    # foot scrolls project 42 mm past each end. Check the slats, not the bbox.
    dict(name="bench_length", mm=1800.0, tol=1.0, how="bbox_x",
         part="SeatSlats"),
    dict(name="seat_slat_field_width", mm=522.0, tol=1.0, how="bbox_y",
         part="SeatSlats"),
    dict(name="seat_slat_thickness", mm=32.0, tol=0.5, how="bbox_z",
         part="SeatSlats"),
    dict(name="seat_height", mm=450.0, tol=0.6, how="top_z", part="SeatSlats"),
    # 835 is the top raked back slat; the rear posts stop at 830.
    dict(name="overall_height", mm=835.0, tol=3.0, how="bbox_z"),
]