"""
human_ear -- a 58 mm pinna: 9 mm shell, concha bowl, helix rim, tragus and lobe.

The shell is an `extrude_profile` of a deformed superellipse, extruded 9 mm
along Z and then stood up by a 90 deg X rotation. Building the outline by
deforming a ring rather than by typing 30 coordinates is what makes the three
ear features a real ear needs -- a narrowed lower third, the intertragic notch
and the widened helix -- readable as an ear rather than as a shell.

The helix is an `arc_torus` that runs most of the way round the outline. It is
a separate closed solid, overlapping the shell, so no boolean is involved.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    ear_height    = 54.0,
    ear_width     = 30.0,
    shell_thick   = 8.0,
    helix_diameter = 6.4,
)

W, H = SPEC["ear_width"], SPEC["ear_height"]
T = SPEC["shell_thick"]


def _outline():
    """A pinna outline: narrowed lobe, intertragic notch, widened helix.

    Rows are (a, b) where a is HEIGHT and b is DEPTH, because the plate's
    normal ends up along X: the fixed shot list puts the camera on +X for the
    SIDE view, and a pinna's plane faces laterally, so the side view has to see
    the ear face-on rather than edge-on.
    """
    pts = []
    for (a, b) in bkit.superellipse_section(H, W, n=2.7, steps=48):
        # lower third narrows into the lobe
        f = 1.0 if a > 0 else (0.74 if a < -0.35 * H / 2.0 else 0.92)
        bb = b * f
        # the front edge is pulled in for the tragus notch
        if bb < 0.0 and a < -0.10 * H:
            bb *= 0.70
        # the helix flares out at the top rear
        if bb > 0.0 and a > 0.20 * H:
            bb *= 1.14
        pts.append((a, bb + W / 2.0 - 3.0))
    return pts


def build():
    skin = bkit.pbr("Skin", base=(0.700, 0.500, 0.400), rough=0.56)
    skin_d = bkit.pbr("SkinShade", base=(0.560, 0.360, 0.280), rough=0.58)
    concha = bkit.pbr("Concha", base=(0.300, 0.150, 0.130), rough=0.70)

    # ---- shell: the outline extruded through its own thickness, then stood
    # up so the plate lies in the Y-Z plane with its normal along X.
    shell = bkit.extrude_profile("Shell", _outline(), T, centre=(0.0, 0.0, 0.0),
                                 axis="Z", mat=skin)
    shell.rotation_euler = (0.0, math.radians(-90.0), 0.0)
    bpy.context.view_layer.update()

    # ---- concha: the bowl, pressed into the front face
    bkit.uv_sphere("Concha", 1.0, segments=28, rings=14,
                   centre=(5.0, 0.0, 4.0), mat=concha).scale = (5.0, 10.0, 14.0)

    # ---- helix: the rolled rim, a C that hugs the upper and rear edge. A
    # near-complete circle reads as a bracelet, not as an ear.
    bkit.arc_torus("Helix", 15.0, 3.2, 40.0, 300.0, plane="YZ",
                   centre=(-3.0, 0.0, 3.0), seg_minor=14, mat=skin)

    # ---- antihelix: the inner Y-shaped ridge
    bkit.arc_torus("Antihelix", 8.5, 2.4, 60.0, 290.0, plane="YZ",
                   centre=(-4.0, 0.0, 1.0), seg_minor=12, mat=skin_d)

    # ---- tragus and lobe
    bkit.uv_sphere("Tragus", 1.0, segments=20, rings=10,
                   centre=(4.0, -7.0, -4.0), mat=skin).scale = \
        (4.0, 5.0, 6.0)
    bkit.uv_sphere("Lobe", 1.0, segments=20, rings=10,
                   centre=(-2.0, 0.0, -19.0), mat=skin).scale = \
        (4.5, 7.0, 8.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="ear_height", mm=54.0, tol=1.0, how="top_z",  part="Shell"),
    dict(name="ear_width", mm=31.0, tol=0.5, how="bbox_y", part="Shell"),
    dict(name="shell_thick", mm=8.0, tol=0.4, how="bbox_x", part="Shell"),
    dict(name="helix_diameter", mm=6.4, tol=0.4, how="bbox_x", part="Helix"),
]
