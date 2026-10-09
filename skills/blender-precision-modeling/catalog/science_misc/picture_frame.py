"""picture_frame -- a 200 x 150 mm photo frame: the moulding profile with its
real rebate, the glazing and the backing board behind it.

The moulding profile is the model. A picture frame is not a rectangle: it is an
L-shaped section swept around a rectangle, with a rebate that holds the glass
and the print. So the profile is authored once and swept along a rounded
rectangle path, which is what gives the frame its stepped edge in section.

Construction: the moulding is a swept profile (one closed solid), the glazing
and the backing board are separate thin solids seated in the rebate, and the
hanging tab is a small bracket on the back.

Orientation: the frame stands upright in the X-Z plane, facing -Y, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    width=200.0,
    height=150.0,
    moulding_width=14.0,
    moulding_depth=16.0,
    glazing_width=162.0,
    glass_thickness=2.0,
    rebate_depth=9.0,
)

# the path is the moulding CENTRELINE, so the outer face is path + one
# moulding width: the 200 x 150 mm photo size is the OUTER size
MW, MD = 14.0, 16.0
W, H = 200.0 - MW, 150.0 - MW


def sweep_path(inset, n_corner=6):
    """A rounded-rectangle path in the X-Z plane, `inset` in from the outer
    edge. The computed layout for the moulding: one path, swept once."""
    hw = W / 2.0 - inset
    hh = H / 2.0 - inset
    r = min(6.0, hw, hh)
    pts = []
    corners = ((hw - r, hh - r, 0.0), (-hw + r, hh - r, math.pi / 2),
               (-hw + r, -hh + r, math.pi), (hw - r, -hh + r, 3 * math.pi / 2))
    for (cx, cz, a0) in corners:
        for i in range(n_corner + 1):
            a = a0 + (math.pi / 2) * i / n_corner
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def moulding_profile():
    """The L-section of the moulding, in (across, depth) millimetres.

    The step is the rebate: the back part is set back so the glass and the
    backing board seat against it.
    """
    return [(-MW / 2.0, 0.0), (MW / 2.0, 0.0), (MW / 2.0, MD - 3.0),
            (MW / 2.0 - 3.0, MD), (-MW / 2.0 + 3.0, MD),
            (-MW / 2.0 + 3.0, MD - 3.0), (-MW / 2.0, MD - 3.0)]


def sweep(name, path, profile, y, mat):
    """Sweep a closed 2D profile along a closed path in the X-Z plane."""
    m = len(path)
    n = len(profile)
    verts = []
    for i, (px, pz) in enumerate(path):
        q = path[(i + 1) % m]
        r = path[(i - 1) % m]
        tx, tz = q[0] - r[0], q[1] - r[1]
        tl = math.hypot(tx, tz) or 1.0
        tx, tz = tx / tl, tz / tl
        # in-plane normal to the path
        nx, nz = -tz, tx
        for (u, d) in profile:
            verts.append((px + nx * u, y + d, pz + nz * u))
    faces = []
    for i in range(m):
        i2 = (i + 1) % m
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((i * n + j, i * n + j2, i2 * n + j2, i2 * n + j))
    ob = bkit.mesh_from(name, verts, faces, mat)
    bkit.recalc(ob)
    return ob


def build():
    wood = bkit.pbr("FrameWood", base=(0.28, 0.16, 0.08), rough=0.44,
                    coat=0.25)
    gold = bkit.pbr("FrameGilt", base=(0.72, 0.56, 0.24), metal=0.85,
                    rough=0.30)
    glass = bkit.pbr("FrameGlass", base=(0.86, 0.90, 0.94), rough=0.05,
                     transmission=0.75, ior=1.5)
    board = bkit.pbr("FrameBoard", base=(0.52, 0.46, 0.38), rough=0.70)
    print_ = bkit.pbr("FramePrint", base=(0.30, 0.44, 0.56), rough=0.44)

    outer = sweep("Moulding", sweep_path(0.0), moulding_profile(), 0.0, wood)

    # ---- the inner lip: a narrower band of gilt around the glazing rebate,
    # a second material on a second real sweep so the frame has a two-tone edge
    sweep("Lip", sweep_path(MW - 4.5), moulding_profile(), 2.0, gold)
    del outer

    # ---- glazing, print and backing board, seated in the rebate
    bkit.rounded_box("Glazing", W - 2.0 * MW + 4.0, 2.0,
                     H - 2.0 * MW + 4.0, r=0.4, segments=2,
                     centre=(0.0, 5.5, 0.0), mat=glass)
    bkit.rounded_box("Print", W - 2.0 * MW + 1.0, 0.6,
                     H - 2.0 * MW + 1.0, r=0.3, segments=2,
                     centre=(0.0, 8.2, 0.0), mat=print_)
    bkit.rounded_box("Backing", W - 2.0 * MW + 4.0, 2.4,
                     H - 2.0 * MW + 4.0, r=0.5, segments=2,
                     centre=(0.0, 12.4, 0.0), mat=board)

    # ---- the hanging bracket on the back
    bkit.rounded_box("Hanger", 26.0, 3.0, 12.0, r=1.0, segments=3,
                     centre=(0.0, 15.0, H / 2.0 - 16.0), mat=gold)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="width", mm=200.0, tol=1.5, how="bbox_x", part="Moulding"),
    dict(name="height", mm=150.0, tol=1.5, how="bbox_z", part="Moulding"),
    dict(name="moulding_depth", mm=16.0, tol=1.0, how="bbox_y",
         part="Moulding"),
    dict(name="glazing_width", mm=162.0, tol=2.0, how="bbox_x",
         part="Glazing"),
    dict(name="overall_width", mm=200.0, tol=2.0, how="bbox_x"),
    dict(name="overall_height", mm=150.0, tol=2.0, how="bbox_z"),
    dict(name="glass_thickness", mm=2.0, tol=0.4, how="bbox_y",
         part="Glazing"),
]