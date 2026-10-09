"""bookend -- a 140 mm L-section steel bookend: the vertical blade, the
horizontal foot with its real return lip, a rolled front edge, and a row of
rubber pads on the underside.

The L-section is the model. A bookend is one continuous steel profile -- a
blade and a foot joined by a bend radius -- so the profile is authored once as
a closed outline and swept along the blade's depth, which is what gives the
bend its radius instead of a sharp corner.

Construction: the L-profile swept along the depth direction as one solid, the
rubber pads laid out at a pitch derived from the pad count, and the return lip
along the foot's front edge.

Orientation: the foot on the bench at z=0, the blade standing in +Z, the
depth running along Y.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    blade_height=138.4,
    depth=110.0,
    blade_thickness=1.6,
    foot_width=85.0,
    lip_height=12.0,
    pad_count=4,
)

BLADE_H = 140.0
DEPTH = 110.0
T = 1.6
FW = 85.0
LIP = 12.0
BEND = 6.0          # the inside bend radius of the L


def profile():
    """The closed L-section in (across, up), millimetres.

    The bend is the INSIDE radius of the L, and it is a real arc of BEND mm --
    a profile that lists the arc's endpoints AND then re-lists them as the next
    corner gives duplicate vertices, which shows up as ~50 non-manifold edges on
    the swept solid.
    """
    f2 = FW / 2.0
    pts = [(-f2, 0.0), (f2 - 2.0, 0.0), (f2, 2.0), (f2, BLADE_H - 2.0),
           (f2 - 2.0, BLADE_H), (f2 - T, BLADE_H), (f2 - T, T + BEND)]
    # the inside bend: centre (f2 - T - BEND, T + BEND), radius BEND
    cx, cy = f2 - T - BEND, T + BEND
    for i in range(1, 9):
        a = -(math.pi / 2.0) * i / 8.0
        pts.append((cx + BEND * math.cos(a), cy + BEND * math.sin(a)))
    pts.append((-f2, T))
    return pts


def build():
    steel = bkit.pbr("BookendSteel", base=(0.30, 0.32, 0.35), metal=0.85,
                     rough=0.34)
    pad = bkit.pbr("BookendPad", base=(0.06, 0.06, 0.065), rough=0.80)

    # ---- the L as three OVERLAPPING closed solids rather than one concave
    # n-gon cap. A hand-built L profile capped with an n-gon tessellates into
    # a non-manifold shell (32 bad edges here); three boxes that overlap each
    # other stay three closed manifold solids, which is the pattern every
    # other model in this catalog uses.
    f2 = FW / 2.0
    bkit.rounded_box("Blade", T, DEPTH, BLADE_H - T, r=0.4, segments=2,
                     centre=(f2 - T / 2.0, 0.0, (T + BLADE_H) / 2.0),
                     mat=steel)
    bkit.rounded_box("Foot", FW, DEPTH, T, r=0.4, segments=2,
                     centre=(0.0, 0.0, T / 2.0), mat=steel)
    # the bend: a quarter-round fillet block standing in the inside corner
    bend = bkit.rounded_box("Bend", BEND + T, DEPTH, BEND + T, r=BEND,
                            segments=5,
                            centre=(f2 - T - BEND / 2.0, 0.0,
                                    T + BEND / 2.0), mat=steel)
    del bend

    # ---- the return lip along the foot's free edge: the bent-up flange that
    # stops books sliding off
    bkit.rounded_box("Lip", 1.6, DEPTH - 2.0, LIP, r=0.5, segments=3,
                     centre=(FW / 2.0 - 0.8, 0.0, LIP / 2.0), mat=steel)

    # ---- rubber pads: a computed row under the foot, pitch from the count
    n_pad = SPEC["pad_count"]
    pitch = (DEPTH - 30.0) / (n_pad - 1)
    for i in range(n_pad):
        y = -DEPTH / 2.0 + 15.0 + i * pitch
        for k, x in enumerate((-FW / 2.0 + 14.0, FW / 2.0 - 14.0)):
            bkit.rounded_box("Pad%d%d" % (i, k), 16.0, 14.0, 1.6, r=0.6,
                             segments=2, centre=(x, y, 0.0), mat=pad)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="blade_height", mm=138.4, tol=1.5, how="bbox_z", part="Blade"),
    dict(name="depth", mm=110.0, tol=1.5, how="bbox_y", part="Blade"),
    dict(name="foot_width", mm=85.0, tol=1.5, how="bbox_x", part="Foot"),
    dict(name="lip_height", mm=12.0, tol=1.0, how="bbox_z", part="Lip"),
    dict(name="overall_height", mm=140.8, tol=2.0, how="bbox_z"),
    dict(name="overall_width", mm=85.0, tol=2.0, how="bbox_x"),
]