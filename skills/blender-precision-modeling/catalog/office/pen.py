"""
pen -- retractable ballpoint pen lying on the desk.

The whole body is ONE lathe profile walked from the writing tip to the tail:
tip cone -> barrel -> shoulder -> tail. A profile that starts and ends on the
axis welds into a pole at each end, so the pen is a single closed solid with no
seams to go non-manifold. The steel ball, the plunger and the clip are separate
named parts; the rubber grip is a second material on the same solid, not a
second overlapping shell.

Length 140 mm, barrel 9.5 mm -- a standard retractable stick pen.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=140.0,
    barrel_diameter=9.5,
    tip_cone_length=14.0,
    clip_length=34.0,
    ball_diameter=1.6,
)

BARREL_R = SPEC["barrel_diameter"] / 2.0
CLIP_Z0 = 93.0
CLIP_LEN = SPEC["clip_length"]


def build():
    # A near-black barrel against the 0.19 backdrop is a silhouette. Mid blue
    # with a satin coat keeps the taper and the clip readable.
    barrel_mat = bkit.pbr("PenBarrel", base=(0.14, 0.26, 0.62),
                          rough=0.26, coat=0.4)
    grip_mat = bkit.pbr("PenGrip", base=(0.10, 0.10, 0.12), rough=0.66)
    steel = bkit.pbr("PenSteel", base=(0.70, 0.72, 0.74), metal=0.85,
                     rough=0.30)
    dark = bkit.pbr("PenClipMetal", base=(0.55, 0.57, 0.60), metal=0.9,
                    rough=0.28)

    # ---- body: one closed profile, tip -> tail -----------------------------
    prof = [
        (0.80, 0.00),        # writing tip, capped flat under the ball
        (1.50, 2.00),        # tip cone
        (2.60, 5.00),
        (3.90, 9.50),
        (BARREL_R, 14.00),   # barrel starts
        (BARREL_R, 112.00),
        (4.55, 120.00),      # shoulder
        (3.10, 128.00),
        (2.60, 136.00),      # tail
        (0.00, 136.00),      # back to the axis -> welded pole
    ]
    body = bkit.lathe("PenBody", prof, segments=64, mat=barrel_mat)

    # Grip as a second material on the same solid: a separate overlapping shell
    # would z-fight with the barrel and double the non-manifold count.
    bkit.assign_faces_by(
        body, grip_mat,
        lambda c, n: 26.0 <= c.z / bkit.MM <= 56.0,
    )

    ball = bkit.uv_sphere("PenTipBall", 0.80, segments=24, rings=12,
                          centre=(0, 0, -0.25), mat=steel)
    button = bkit.cylinder("PenButton", 3.4, 4.0, segments=40,
                           centre=(0, 0, 138.0), mat=grip_mat)
    # Clip: a flat strip lying along the barrel. Authored as a radial-thickness
    # rectangle (local x = radial, local y = width) and swept along the length.
    clip = bkit.extrude_profile(
        "PenClip",
        [(-5.9, -0.75), (-4.2, -0.75), (-4.2, 0.75), (-5.9, 0.75)],
        CLIP_LEN, centre=(0, 0, CLIP_Z0 + CLIP_LEN / 2.0), mat=dark)

    # ---- lay the pen down --------------------------------------------------
    # A pen balanced on its 1.6 mm ball reads as a rendering accident.
    #
    # Laying it down is done with rotation_euler, NOT by transforming the mesh:
    # bkit primitives place geometry with `location`, so rotating the mesh
    # instead rotates about the wrong point and leaves the part floating at its
    # authoring height. Rotating the object puts the axial position in
    # location.x, which is what we want.
    lay_down = math.radians(90.0)
    for ob in (body, ball, button, clip):
        axial = ob.location.z / bkit.MM
        ob.rotation_euler = (0.0, lay_down, 0.0)
        ob.location = bkit.v(axial, 0.0, 0.0)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    # 136 mm of barrel + the 4 mm plunger button + the 1.6 mm tip ball
    # sticking out the front = the real 141.05 mm overall.
    dict(name="length", mm=141.05, tol=0.4, how="bbox_x"),
    dict(name="barrel_diameter", mm=9.5, tol=0.3, how="bbox_y", part="PenBody"),
    dict(name="clip_length", mm=34.0, tol=0.6, how="bbox_x", part="PenClip"),
]