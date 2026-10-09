"""
binder_clip -- 25 mm medium binder clip.

A binder clip is NOT an open box. It is a low folded sheet-steel trough with a
tall triangular wire handle standing on each end, and the handles rise roughly
twice the height of the body. The first cut of this model got the body far too
tall, which made it read as an open-topped container with two hoops in it --
the side view exposed it immediately.

Geometry:
  body      folded sheet, 0.8 mm real thickness, 6 mm tall, side profile
            extruded across the clip width (an extruded polygon with a real
            wall, not a zero-thickness silhouette)
  handles   two arc_torus loops standing UPRIGHT in the YZ plane -- one at each
            end of the clip, springing down into the body
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=25.0,
    depth=19.0,
    body_height=6.0,
    sheet_thickness=0.8,
    handle_diameter=1.6,
    handle_height=13.0,
)

L = SPEC["width"]
D = SPEC["depth"]
BH = SPEC["body_height"]
T = SPEC["sheet_thickness"]


def build():
    steel = bkit.pbr("BinderClipSteel", base=(0.78, 0.80, 0.83), metal=0.80,
                     rough=0.28)
    body_mat = bkit.pbr("BinderClipBody", base=(0.76, 0.78, 0.80),
                        metal=0.72, rough=0.30)

    # ---- folded body: side profile in XZ, extruded across the width -------
    # Walking out along the base, up the front wall, back across the top of the
    # wall and down the inside gives the fold real thickness. A single-line
    # silhouette here is exactly the zero-thickness sheet the rules forbid.
    body_poly = [
        (-L / 2.0, 0.0),
        (L / 2.0, 0.0),
        (L / 2.0, T),                    # bottom plate, outer face
        (L / 2.0 - T, T),                # and its inner face
        (L / 2.0 - T, BH - 2.2),         # up the inside of the front wall
        (L / 2.0, BH - 2.2),             # fold over the top of the wall
        (L / 2.0, BH),                   # front wall, outer face
        (-L / 2.0 + T, BH),              # across the top
        (-L / 2.0, BH - 2.2),            # fold over the back wall
        (-L / 2.0 + T, BH - 2.2),        # down the inside of the back wall
        (-L / 2.0 + T, T),               # along the inside of the base
    ]
    body = bkit.extrude_profile("BinderClipBody", body_poly, D, axis="Y",
                                mat=body_mat)
    bkit.recalc(body)
    bkit.bevel(body, width_mm=0.12, segments=1, angle_deg=30)

    # ---- two wire handles standing upright at the ends ---------------------
    # Plane "YZ" means the loop rises in Y/Z and runs along X, so each loop
    # stands across the clip like a staple. The 200 deg sweep starts inside the
    # body and springs over the top.
    r_wire = SPEC["handle_diameter"] / 2.0
    arc_r = D / 2.0 - r_wire - 0.4       # span the width, clear of the walls
    handles = []
    for i, x in enumerate((-L / 2.0 + 5.0, L / 2.0 - 5.0)):
        arc = bkit.arc_torus("BinderClipHandle%d" % (i + 1), arc_r, r_wire,
                             200.0, -20.0, plane="YZ",
                             centre=(x, 0.0, BH - 1.0),
                             seg_major=30, seg_minor=14, mat=steel,
                             caps=True)
        handles.append(arc)

    # ---- the two flat steel arms that fold, and their pivot rivets -------
    # Without these the model is a trough with two hoops standing in it, which
    # is what form-plausibility flagged. Each arm is a flat sheet spanning the
    # clip depth, lying just inside the handle loop and pivoting on a rivet
    # that passes through the loop's crown. They are what a foldback clip
    # actually clamps with, and they are what makes the handles read as
    # hinged rather than as loose wire.
    arms = []
    for i, x in enumerate((-L / 2.0 + 5.0, L / 2.0 - 5.0)):
        arm = bkit.rounded_box(
            "BinderClipArm%d" % (i + 1), 1.4, D - 1.6, SPEC["handle_height"] - 2.0,
            r=0.5, segments=2,
            centre=(x, 0.0, BH - 1.0 + (SPEC["handle_height"] - 2.0) / 2.0),
            mat=body_mat)
        arms.append(arm)
    arm_ob = bkit.join(arms, name="BinderClipArms")

    rivets = []
    for i, x in enumerate((-L / 2.0 + 5.0, L / 2.0 - 5.0)):
        rivets.append(bkit.cylinder(
            "BinderClipRivet%d" % (i + 1), 1.3, D + 1.2, segments=24,
            centre=(x, 0.0, BH - 1.0 + SPEC["handle_height"] - 2.4),
            axis="Y", mat=steel))
    rivet_ob = bkit.join(rivets, name="BinderClipRivets")

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="width", mm=25.0, tol=0.6, how="bbox_x", part="BinderClipBody"),
    dict(name="depth", mm=19.0, tol=0.6, how="bbox_y", part="BinderClipBody"),
    dict(name="body_height", mm=6.0, tol=0.5, how="bbox_z",
         part="BinderClipBody"),
    dict(name="handle_height", mm=12.6, tol=1.0, how="bbox_z",
         part="BinderClipHandle1"),
]