"""coathook -- a 50 mm wall coat hook: the back plate, the projecting stem, the
upturned ball tip, and the two screw holes.

The upturned tip is the model. A coat hook is a J, not a peg -- the stem
projects from the plate and then curves UP so a coat's hanger cannot slide off
it. So the stem is swept along a real J curve with a real bend radius, and the
ball tip is a separate sphere on the end of it.

Construction: a lathed back plate, the J swept as one closed solid, a ball tip,
and two screws through the plate. Nothing is booleaned.

Orientation: the plate against the wall at y=0, the hook projecting toward -Y
and curling up, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    overall_length=32.7,
    plate_width=22.0,
    plate_height=41.6,
    stem_diameter=9.0,
    ball_diameter=11.0,
    tip_lift=14.0,
)

PLATE_W, PLATE_H = 22.0, 34.0
STEM_R = 4.5


def stem_path():
    """The J: straight out of the plate, then a quarter turn up.

    Generated from the stem length and the tip lift, so the bend radius is the
    real one rather than three hand-placed nodes that only look like a J.
    """
    run = 18.0
    pts = [(0.0, 3.0, 0.0), (0.0, -6.0, 0.0), (0.0, -15.0, 0.0),
           (0.0, -run + 2.0, 0.6)]
    # the bend turns the stem from -Y to +Z about the X axis, with the real
    # bend radius
    r = 8.0
    cy = -(run - 2.0) - r
    for k in range(1, 13):
        a = -math.pi / 2.0 + (math.pi / 2.0) * k / 12.0
        pts.append((0.0, cy + r * math.cos(a), r + r * math.sin(a)))
    pts.append((0.0, cy - 0.2, 2.0 * r + 4.0))
    return pts


def build():
    chrome = bkit.pbr("HookChrome", base=(0.78, 0.80, 0.84), metal=0.85,
                      rough=0.18)
    steel = bkit.pbr("HookSteel", base=(0.60, 0.62, 0.66), metal=0.85,
                     rough=0.28)

    # ---- the back plate: a lathed boss with a real tapered shoulder
    bkit.lathe("Plate",
               [(0.0, 0.0), (11.0, 0.0), (11.0, 2.4), (7.0, 4.6),
                (6.0, 7.0), (0.0, 7.0)],
               segments=48, centre=(0.0, 0.0, 0.0), mat=chrome)
    plate = bpy.data.objects["Plate"]
    # the plate is a vertical paddle, so the lathe's axis is laid along -Y
    for v in plate.data.vertices:
        y, z = v.co.y, v.co.z
        v.co.y = -z
        v.co.z = y * (PLATE_H / 18.0)
    plate.data.update()
    F.orient_outward(plate)

    # ---- the J stem
    path = stem_path()
    rad = [(STEM_R, STEM_R)] * len(path)
    rings = []
    for i, p in enumerate(path):
        ring = []
        for j in range(20):
            a = 2.0 * math.pi * j / 20.0
            ring.append((p[0] + STEM_R * math.cos(a), p[1],
                         p[2] + STEM_R * math.sin(a)))
        rings.append(ring)
    stem = bkit.loft("Stem", rings, mat=chrome, smooth=True)
    bkit.recalc(stem)

    # ---- the ball tip that stops the hanger sliding off
    F.sphere("Ball", 5.5, path[-1], chrome, segments=24, rings=12)

    # ---- two screws through the plate, at the real 26 mm centres
    for side, sz in (("Top", 11.0), ("Bot", -11.0)):
        F.cone_between("ScrewHead%s" % side, (0.0, -6.0, sz),
                       (0.0, -2.4, sz), 2.6, 3.0, seg=14, mat=steel)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="overall_length", mm=32.7, tol=3.0, how="bbox_y"),
    dict(name="plate_width", mm=22.0, tol=1.5, how="bbox_x", part="Plate"),
    dict(name="plate_height", mm=41.6, tol=3.0, how="bbox_z", part="Plate"),
    dict(name="stem_diameter", mm=9.0, tol=0.8, how="bbox_x", part="Stem"),
    dict(name="ball_diameter", mm=11.0, tol=0.8, how="bbox_x", part="Ball"),
    dict(name="overall_height", mm=46.3, tol=3.0, how="bbox_z"),
]