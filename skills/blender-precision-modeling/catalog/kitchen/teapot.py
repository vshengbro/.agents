"""teapot -- round teapot: lathed body with a real cavity, swept spout and handle.

196 mm across spout-to-handle, 100 mm body. Four parts plus a lid and a knob.
The spout is a tapered lathe rotated about its own origin and then positioned,
so its base disappears into the wall instead of butting against it; the handle
is a partial torus whose tips are buried in the same wall.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    body_diameter=140.0,   # widest point of the belly
    body_height=100.0,     # rim above the table
    overall_height=134.0,  # lid knob finial
    wall=2.5,              # rim thickness
    spout_tip_diameter=12.0,
    handle_reach=23.0,     # outer protrusion from the body wall
    volume_ml=1100.0,
)

R = SPEC["body_diameter"] / 2.0
H = SPEC["body_height"]

# Spout: a taper whose axis leaves the body at `tilt` from vertical. It runs
# along +Y, not +X, because the `side` camera looks straight down -X and a
# spout on +X is a circle in every profile shot.
SPOUT_R0, SPOUT_R1, SPOUT_LEN = 12.5, 5.5, 78.0
SPOUT_TILT = 40.0
SPOUT_BASE = (0.0, 58.0, 52.0)     # centre of the spout's base disc


def build():
    porcelain = bkit.preset("ceramic")

    # ---- body: one closed profile, out along the base and back down inside --
    prof = [
        (0.0, 0.0),
        (46.0, 0.0),
        (58.0, 3.0),
        (65.0, 11.0),
        (69.0, 26.0),
        (R, 46.0),                       # belly
        (68.0, 70.0),
        (62.0, 88.0),
        (56.0, 96.0),                     # shoulder into the neck
        (55.5, H),                        # rim, outside
        (55.5 - SPEC["wall"], H),         # across the rim
        (52.5, 94.0),
        (58.0, 86.0),                     # down the inside
        (64.0, 68.0),
        (66.5, 46.0),
        (65.5, 27.0),
        (60.0, 14.0),
        (48.0, 6.0),
        (0.0, 6.0),
    ]
    body = bkit.lathe("TeapotBody", prof, segments=96, mat=porcelain)

    # ---- lid: a domed shell, pole top and pole underside -------------------
    lid = bkit.lathe("TeapotLid", [
        (0.0, 119.0),
        (14.0, 118.0),
        (30.0, 114.5),
        (43.0, 108.0),
        (52.0, 100.5),
        (56.5, 97.5),                     # flange overhanging the rim
        (56.0, 95.5),
        (50.0, 99.5),                     # underside of the dome
        (40.0, 106.0),
        (26.0, 112.0),
        (10.0, 115.0),
        (0.0, 115.5),
    ], segments=96, mat=porcelain)
    # The lid and knob profiles are written top-down (pole first), which winds
    # the revolve inward; recalc makes the signed volume positive.
    bkit.recalc(lid)

    # ---- knob: turned finial ------------------------------------------------
    knob = bkit.lathe("TeapotKnob", [
        (0.0, 134.0),
        (5.0, 133.5),
        (8.0, 131.0),
        (9.5, 127.0),
        (9.0, 122.0),
        (6.0, 118.5),
        (3.0, 117.5),
        (0.0, 117.5),
    ], segments=64, mat=porcelain)
    bkit.recalc(knob)

    # ---- spout: tapered lathe, rotated about its own origin then moved ------
    # `obj.rotation_euler` is radians, but the translation that follows is
    # millimetres -- bkit.move() is the only place the conversion happens.
    spout = bkit.lathe("TeapotSpout", [
        (SPOUT_R0 - 2.5, 0.0),
        (SPOUT_R0, 0.0),
        (10.5, 26.0),
        (8.5, 46.0),
        (6.5, 66.0),
        (SPOUT_R1, SPOUT_LEN),
    ], segments=48, mat=porcelain)
    # negative rotation about X tips the taper toward +Y; `obj.rotation_euler`
    # is radians, but the translation that follows is millimetres.
    spout.rotation_euler = (math.radians(-SPOUT_TILT), 0.0, 0.0)
    bpy.context.view_layer.update()
    bkit.move(spout, *SPOUT_BASE)

    # ---- handle: partial torus, tips buried in the belly wall --------------
    # Opposite the spout, in the YZ plane so the two read as one silhouette.
    handle = bkit.arc_torus("TeapotHandle", 23.0, 7.0, 94.0, 266.0,
                            centre=(0.0, -63.0, 46.0), plane="YZ",
                            seg_major=40, mat=porcelain, caps=True)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="body_diameter", mm=140.0, tol=0.3, how="diameter",
         part="TeapotBody"),
    dict(name="body_height", mm=100.0, tol=0.3, how="bbox_z", part="TeapotBody"),
    dict(name="overall_height", mm=134.0, tol=0.3, how="bbox_z"),
]
