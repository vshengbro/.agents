"""
suitcase -- a hard-shell cabin suitcase: a rounded shell with a zip line down
the middle, four spinner wheels, a telescopic handle and a side grab handle.

Wheels are what make a suitcase read as a suitcase in a product render, and
they are the reason the body cannot simply be a rounded box sitting on the
floor: the shell is lifted onto the wheel height so the whole assembly has the
real standing height.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=550.0,              # along X, the broad face
    depth=230.0,               # along Y, the narrow face
    shell_height=225.0,
    wheel_diameter=54.0,
    wheel_height=30.0,
    overall_height=262.0,
    handle_reach=95.0,         # telescopic handle above the shell
    corner_radius=26.0,
)

L = SPEC["length"]
D = SPEC["depth"]
SH = SPEC["shell_height"]
WD = SPEC["wheel_diameter"]
R = SPEC["corner_radius"]

# Materials belong inside build(): run_model.py calls bkit.reset() after import,
# and reset() is a factory-settings read that deletes anything made before it.


def build():
    shell_mat = bkit.pbr("SuitcaseShell", base=(0.16, 0.17, 0.20), rough=0.34)
    shell_zip = bkit.pbr("SuitcaseZip", base=(0.55, 0.57, 0.60), metal=0.8,
                         rough=0.30)
    rubber = bkit.preset("rubber")
    trim = bkit.preset("anodized")

    # ---- shell ---------------------------------------------------------------
    body_z = SPEC["wheel_height"] + SH / 2.0
    shell = bkit.rounded_box("SuitcaseShell", L, D, SH, r=R, segments=6,
                              centre=(0.0, 0.0, body_z), mat=shell_mat)

    # ---- zip line: a shallow band right around the parting plane ------------
    zip_band = bkit.rounded_box("SuitcaseZipLine", L - 3.0, D - 3.0, 9.0,
                                r=R, segments=6,
                                centre=(0.0, 0.0, body_z + SH * 0.22),
                                mat=shell_zip)

    # ---- four spinner wheels, positioned from the shell footprint ----------
    wx = L / 2.0 - 52.0
    wy = D / 2.0 - 34.0
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        bkit.cylinder("SuitcaseWheel%d" % (i + 1), WD / 2.0, 26.0,
                      segments=32, axis="Y",
                      centre=(sx * wx, sy * wy, WD / 2.0), mat=rubber)
        # the hub, so the wheel is not a black disc in the render
        bkit.cylinder("SuitcaseHub%d" % (i + 1), 12.0, 28.0, segments=24,
                      axis="Y", centre=(sx * wx, sy * wy, WD / 2.0),
                      mat=trim)

    # ---- telescopic handle: two rails and a grip ---------------------------
    top_z = body_z + SH / 2.0
    rail_x = 90.0
    for i, sx in enumerate((-1.0, 1.0)):
        bkit.rounded_box("SuitcaseHandleRail%d" % (i + 1), 16.0, 22.0,
                         SPEC["handle_reach"], r=4.0, segments=3,
                         centre=(sx * rail_x, -D / 2.0 + 46.0,
                                 top_z + SPEC["handle_reach"] / 2.0 - 6.0),
                         mat=trim)
    grip = bkit.rounded_box("SuitcaseHandleGrip", 2 * rail_x + 34.0, 30.0,
                            26.0, r=9.0, segments=4,
                            centre=(0.0, -D / 2.0 + 46.0,
                                    top_z + SPEC["handle_reach"] - 12.0),
                            mat=rubber)

    # ---- side grab handle, bulging +X off the narrow end --------------------
    # Anchors at (+-a in Z) on the end face, standing `rise` proud of it.
    # A circle of radius Rm centred u inside the face satisfies
    #     u^2 + a^2 = (u + rise)^2  =>  u = (a^2 - rise^2) / (2 * rise)
    # and the sweep runs -phi -> +phi about the +X axis of the XZ plane.
    import math
    a, rise = 62.0, 24.0
    u = (a * a - rise * rise) / (2.0 * rise)
    rmaj = u + rise
    ang = math.degrees(math.asin(a / rmaj))
    grab = bkit.arc_torus("SuitcaseGrab", rmaj, 11.0, -ang, ang,
                          centre=(L / 2.0 - u, 0.0, body_z), plane="XZ",
                          seg_major=36, mat=rubber, caps=True)

    # ---- a luggage tag, because a plain shell is a featureless slab ---------
    tag = bkit.rounded_box("SuitcaseTag", 52.0, 6.0, 78.0, r=6.0, segments=3,
                           centre=(-L / 2.0 + 34.0, -D / 2.0 - 2.0,
                                   body_z + 20.0),
                           mat=bkit.pbr("SuitcaseTagMat",
                                        base=(0.86, 0.72, 0.20), rough=0.40))

    return dict(spec=SPEC, parts=14)


CHECKS = [
    dict(name="length", mm=550.0, tol=0.6, how="bbox_x", part="SuitcaseShell"),
    dict(name="depth", mm=230.0, tol=0.6, how="bbox_y", part="SuitcaseShell"),
    dict(name="overall_height", mm=352.0, tol=2.0, how="bbox_z"),
]
