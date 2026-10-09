"""
propeller -- a 1160 mm two-blade fixed-pitch propeller for a light aircraft.

A propeller is a SPINNER, a HUB and two blades, and the blades are the object:
each is a tapered, twisted aerofoil section stacked from root to tip, lofted,
with the twist set by rotating every section a little further than the one
below it. Twenty-two degrees of twist root to tip is what stops it reading as
a flat paddle.

The second blade is a 180 deg copy, which `array_radial` does with the orbit
radius in the mesh -- a prototype placed by `obj.location` sweeps no ring at
all, which is the single most common way a two-blade prop arrives with both
blades on the same side.

Real Rotax 912 S2 propeller: 1160 mm diameter, two blades, 90 mm hub,
120 mm root chord, 780 mm blade length.
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
    diameter=1160.0,
    blades=2,
    hub_dia=90.0,
    hub_shoulder_dia=104.0,
    hub_length=190.0,
    spinner_length=190.0,
    root_chord=120.0,
    tip_chord=62.0,
    blade_length=535.0,
    twist_root_deg=20.0,
    thickness_ratio=0.09,
    bolt_dia=32.0,
)

BL = SPEC["blade_length"]

CHECKS = [
    dict(name="diameter", mm=1160.0, tol=10.0, how="bbox_x",
         part="PropBlades"),
    dict(name="blade_chord_span", mm=225.5, tol=8.0, how="bbox_y",
         part="PropBlades"),
    dict(name="hub_shoulder_dia", mm=104.0, tol=3.0, how="bbox_y",
         part="PropHub"),
    dict(name="spinner_length", mm=190.0, tol=3.0, how="bbox_z",
         part="PropHub"),
    dict(name="bolt_dia", mm=32.0, tol=1.5, how="bbox_y", part="PropBolt"),
    dict(name="blade_tip_reaches", mm=580.0, tol=8.0, how="x_max",
         part="PropBlades"),
]


def build():
    blade_mat = bkit.pbr("PropBlade", base=(0.10, 0.10, 0.11), rough=0.28)
    tip = bkit.pbr("PropTip", base=(0.86, 0.80, 0.18), rough=0.34)
    hub_mat = bkit.preset("polished_metal")

    # ---- one blade, built at the origin with its orbit radius in the
    #      MESH: sections run from the hub out to the tip ---------------
    secs = []
    n = 16
    for i in range(n + 1):
        t = i / float(n)
        r = SPEC["hub_dia"] / 2.0 + t * BL
        chord = SPEC["root_chord"] + (SPEC["tip_chord"] - SPEC["root_chord"]) * t
        th = chord * SPEC["thickness_ratio"] * (1.0 - 0.55 * t)
        a = math.radians(SPEC["twist_root_deg"] * (1.0 - t) ** 1.3)
        ring = []
        for (px, pz) in C.foil(chord, th, camber=0.03):
            ring.append((r, px * math.cos(a) - pz * math.sin(a),
                         px * math.sin(a) + pz * math.cos(a)))
        secs.append(ring)
    blade = bkit.loft("PropBlades", secs, mat=blade_mat)
    bkit.recalc(blade)
    bkit.shade_smooth(blade, 34.0)
    # the painted tip band: faces beyond 92 per cent of the span, so the
    # marking follows the twist instead of being a separate band that has
    # to be positioned on the blade by hand
    bkit.assign_faces_by(blade, tip,
                         lambda c, n: abs(c.x / bkit.MM) > 0.92 * (
                             SPEC["hub_dia"] / 2.0 + BL))
    bpy.context.view_layer.update()
    bkit.array_radial(blade, SPEC["blades"], axis="Z", centre=(0.0, 0.0, 0.0))

    # ---- the spinner and hub the blades come out of ------------------
    bkit.lathe("PropHub",
               [(0.0, -SPEC["hub_length"] / 2.0), (38.0, -95.0),
                (45.0, -50.0), (45.0, 60.0), (52.0, 80.0),
                (48.0, SPEC["hub_length"] / 2.0), (0.0,
                                                   SPEC["hub_length"] / 2.0)],
               segments=40, mat=hub_mat)
    bkit.cylinder("PropBolt", 16.0, SPEC["hub_length"] + 20.0, segments=20,
                  mat=hub_mat)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=3,
                note="Two blades, arrayed about the hub axis with the orbit "
                     "radius carried in the mesh.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
