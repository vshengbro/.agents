"""
airship -- a 36 m non-rigid airship: 11 m envelope, cruciform fins, 2 cars.

An airship is a fat cigar with a CONTROL SURFACE cruciform at the tail and a
gondola slung under it. The fins are the repeated feature: four of them at 90
deg, arrayed about the longitudinal X axis, so the array hub is the tail
station on the centreline and is passed explicitly -- orbiting the world origin
would fling them off the tail.

The envelope is a lathe about X with a rounded ogive nose and a drawn-out tail,
and it is deliberately NOT a body of revolution's default proportions: the
fineness ratio (36/11 = 3.3) is what makes it an airship rather than a cigar.

Real non-rigid airship: 36000 mm long, 11000 mm maximum diameter, four fins on
a 6800 mm span, 6000 x 2200 x 2600 mm gondola, two engine cars.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _craft as C

SPEC = dict(
    length=36000.0,
    max_dia=11000.0,
    nose_dia=4000.0,
    envelope_z=9000.0,
    fins=4,
    fin_span=6800.0,
    fin_root_chord=6000.0,
    gondola_length=6000.0,
    gondola_width=2200.0,
    gondola_height=2600.0,
    cars=2,
    prop_dia=3400.0,
    prop_blades=4,
)

R = SPEC["max_dia"] / 2.0
ZC = SPEC["envelope_z"]
TAIL = -SPEC["length"] / 2.0 + 2600.0        # the fin station on the axis

CHECKS = [
    dict(name="length", mm=36000.0, tol=30.0, how="bbox_x",
         part="AirshipEnvelope"),
    dict(name="max_dia", mm=11000.0, tol=20.0, how="bbox_y",
         part="AirshipEnvelope"),
    dict(name="nose_max_dia", mm=10450.0, tol=20.0, how="bbox_y",
         part="AirshipNose"),
    dict(name="fin_span", mm=6800.0, tol=20.0, how="bbox_z",
         part="AirshipFins"),
    dict(name="gondola_length", mm=6000.0, tol=8.0, how="bbox_x",
         part="AirshipGondola"),
    dict(name="gondola_height", mm=2600.0, tol=8.0, how="bbox_z",
         part="AirshipGondola"),
    dict(name="prop_dia", mm=3300.0, tol=12.0, how="bbox_max",
         part="AirshipProp0"),
    dict(name="gondola_slung", mm=0.0, tol=6.0, how="z_min",
         part="AirshipGondola"),
]


def build():
    skin = bkit.pbr("AirshipSkin", base=(0.80, 0.78, 0.72), rough=0.58)
    accent = bkit.pbr("AirshipAccent", base=(0.66, 0.12, 0.10), rough=0.52)
    hull = bkit.pbr("AirshipHull", base=(0.24, 0.26, 0.30), rough=0.44)
    steel = bkit.preset("brushed_metal")
    glass = bkit.pbr("AirshipGlass", base=(0.14, 0.18, 0.22), rough=0.05)

    # ---- the envelope: a lathe about X, nose to tail ----------------
    L = SPEC["length"]
    prof = []
    for (t, r) in ((0.00, 0.0), (0.03, R * 0.36), (0.08, R * 0.72),
                   (0.16, R * 0.95), (0.28, R), (0.62, R), (0.78, R * 0.92),
                   (0.90, R * 0.62), (0.97, R * 0.26), (1.00, 0.0)):
        prof.append((r, -L / 2.0 + t * L))
    env = bkit.lathe("AirshipEnvelope", prof, segments=56, mat=skin)
    bkit.place(env, (0.0, 0.0, ZC), "X")
    bkit.assign_faces_by(env, accent,
                         lambda c, n: c.x / bkit.MM > 9000.0)

    # the nose cone is its own object so the nose diameter is measurable
    nose = bkit.lathe("AirshipNose",
                      [(0.0, -L / 2.0), (SPEC["nose_dia"] / 2.0, -L / 2.0),
                       (R * 0.95, -L / 2.0 + 0.16 * L)], segments=56, mat=skin)
    bkit.place(nose, (0.0, 0.0, ZC), "X")

    # ---- longitudinal batten seams: real load paths, real gore angles -
    seam = bkit.rounded_box("AirshipSeams", L * 0.90, 70.0, 70.0, r=30.0,
                            segments=3,
                            centre=(L * 0.02, 0.0, R * 0.99), mat=accent)
    C.place_in_mesh(seam, 0.0, 0.0, ZC)
    bpy.context.view_layer.update()
    bkit.array_radial(seam, 12, axis="X", centre=(0.0, 0.0, ZC))

    # ---- four cruciform fins, arrayed about the X axis at the tail ---
    # the fin root starts ON the axis and the tip is at fin_span/2, so the
    # tip-to-tip span is exactly `fin_span`; centred at the half-span
    # instead, the tips land at 3/4 of it and the check measures wrong.
    fin = bkit.rounded_box("AirshipFins", SPEC["fin_root_chord"], 150.0,
                           SPEC["fin_span"] / 2.0, r=60.0,
                           segments=3,
                           centre=(TAIL + SPEC["fin_root_chord"] / 2.0, 0.0,
                                   SPEC["fin_span"] / 4.0), mat=hull)
    C.place_in_mesh(fin, 0.0, 0.0, ZC)
    bpy.context.view_layer.update()
    bkit.array_radial(fin, SPEC["fins"], axis="X", centre=(0.0, 0.0, ZC))

    # ---- the gondola, slung on four cables, with a window band -------
    gz = SPEC["envelope_z"] - R * 0.92
    bkit.rounded_box("AirshipGondola", SPEC["gondola_length"],
                     SPEC["gondola_width"], SPEC["gondola_height"], r=180.0,
                     segments=4, centre=(1500.0, 0.0,
                                         gz - SPEC["gondola_height"] / 2.0),
                     mat=hull)
    bkit.assign_faces_by(bpy.data.objects["AirshipGondola"], glass,
                         lambda c, n: abs(n.y) < 0.6
                         and -2600.0 < c.x / bkit.MM < 4500.0
                         and abs(n.z) < 0.6)
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        C.strut("AirshipCable%d" % i,
                (1500.0 + sx * 2400.0, sy * 700.0, gz),
                (1500.0 + sx * 3000.0, sy * 1400.0, ZC - R * 0.80),
                55.0, mat=steel)

    # ---- two engine cars with four-blade pusher props ----------------
    for i, sx in enumerate((-1, 1)):
        cx = 5200.0 * sx
        bkit.rounded_box("AirshipCar%d" % i, 2600.0, 1200.0, 1400.0,
                         r=160.0, segments=3,
                         centre=(cx, 0.0, ZC - R * 0.55), mat=hull)
        C.strut("AirshipCarPylon%d" % i, (cx, 0.0, ZC - R * 0.55),
                (cx, 0.0, ZC - R * 0.95), 90.0, mat=steel)
        prop = C.rotor("AirshipProp%d" % i, SPEC["prop_dia"] + 400.0,
                       SPEC["prop_blades"], 500.0, steel, chord=430.0,
                       thick=40.0, twist=30.0)
        # a pusher prop turns about the X axis, so `place(..., "X")` lays the
        # rotor over instead of rotating a mesh that is already offset --
        # which would swing it out of the car entirely.
        bkit.place(prop, (cx, 0.0, ZC - R * 0.55), "X")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 + 1 + 1 + 1 + 4 + 4,
                note="Fins, seams and props are arrayed about the "
                     "longitudinal axis at the station each belongs to.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
