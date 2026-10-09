"""
desk_lamp -- compact articulated task lamp: weighted base, upright column, raked
upper arm and a conical shade with a real wall thickness.

The silhouette is the whole job here: without a wide weighted base and an arm
that visibly *reaches*, a cone on a stick reads as a table ornament rather than a
desk lamp. Every dimension below is a real millimetre measurement of a typical
LED task lamp; the shade is a closed-loop lathe (outside up, across the rim,
inside down, back to the start) rather than a zero-thickness cone, because a
paper-thin rim reads as plastic and fails the volume check.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit
from mathutils import Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    base_diameter=150.0,     # weighted cast base
    base_height=21.0,
    column_diameter=16.0,    # top of column
    column_length=130.0,
    arm_reach=95.0,          # horizontal reach of the raked upper arm
    shade_diameter=110.0,    # rim diameter at the shade mouth
    shade_height=80.0,
    overall_height=246.0,
)

SHELL_LOOP = True          # shade is a walled shell, not a single surface


def _rod(name, p0, p1, radius, mat, segments=24):
    """Solid rod between two arbitrary 3D mm points.

    bkit has no slanted-axis primitive, and rotating a cylinder with a raw
    rotation_euler leaves matrix_world stale for the next bbox() call. Building
    the two end rings directly and lofting between them avoids both problems
    and keeps the rod a single watertight solid.
    """
    ax = Vector((p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]))
    length = ax.length or 1.0
    ax = ax / length
    ref = Vector((0.0, 0.0, 1.0))
    if abs(ax.dot(ref)) > 0.95:
        ref = Vector((1.0, 0.0, 0.0))
    u = ax.cross(ref).normalized()
    v = ax.cross(u).normalized()

    def ring(p):
        out = []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ca, sa = math.cos(a), math.sin(a)
            out.append((p[0] + radius * (u.x * ca + v.x * sa),
                        p[1] + radius * (u.y * ca + v.y * sa),
                        p[2] + radius * (u.z * ca + v.z * sa)))
        return out

    ob = bkit.loft(name, [ring(p0), ring(p1)], closed_loop=True,
                   cap_start=True, cap_end=True, mat=mat)
    bkit.recalc(ob)
    return ob


def _shell(name, loop_profile, centre, mat, segments=96):
    """Lathe a CLOSED profile loop into a walled shell.

    `lathe` does not close the profile itself, so the caller repeats the first
    point as the last one and cap_ends stays off. lathe's own weld() then merges
    the duplicated seam ring and the surface becomes watertight -- a real
    3 mm shade wall instead of a zero-thickness cone that renders as a hole.
    """
    prof = list(loop_profile) + [loop_profile[0]]
    ob = bkit.lathe(name, prof, segments=segments, centre=centre,
                    mat=mat, cap_ends=False)
    bkit.recalc(ob)
    return ob


def build():
    metal = bkit.preset("brushed_metal")
    cast = bkit.preset("dark_metal")
    plastic = bkit.preset("black_plastic")
    paint = bkit.preset("yellow_paint")
    inner = bkit.pbr("ShadeLining", base=(0.93, 0.92, 0.89), rough=0.24)
    glow = bkit.pbr("BulbGlow", base=(1.0, 0.94, 0.80), rough=0.30,
                    emission=(1.0, 0.90, 0.72), emission_strength=6.0)

    base_h = SPEC["base_height"]
    col_len = SPEC["column_length"]
    reach = SPEC["arm_reach"]

    # ---- weighted base: broad, flat-bottomed, slightly domed -------------
    base = bkit.lathe("LampBase", [
        (0.0, 0.0),
        (70.0, 0.0),               # flat footprint, sits on the desk
        (74.0, 1.5),
        (75.0, 5.0),
        (75.0, 14.0),
        (72.0, 18.0),
        (60.0, 20.0),
        (24.0, 21.0),
        (0.0, 21.0),
    ], segments=96, mat=cast)

    # ---- upright column, tapering upward --------------------------------
    column = bkit.cylinder("LampColumn", 8.0, col_len, r2=6.5, segments=32,
                           centre=(0.0, 0.0, base_h + col_len / 2.0), mat=metal)

    # ---- the arm that makes it a desk lamp ------------------------------
    elbow_z = base_h + col_len
    elbow = bkit.uv_sphere("LampElbow", 9.0, segments=32, rings=16,
                           centre=(0.0, 0.0, elbow_z), mat=plastic)
    head_z = elbow_z + 87.0
    arm = _rod("LampArm", (0.0, 0.0, elbow_z), (0.0, -reach, head_z), 6.0, metal)
    head = bkit.uv_sphere("LampHead", 8.0, segments=32, rings=16,
                          centre=(0.0, -reach, head_z), mat=plastic)

    # ---- conical shade: walled shell hanging from the head joint -------
    shade_h = SPEC["shade_height"]
    r_in, r_out_in, r_out_out = 52.0, 29.0, 32.0
    rim_r = SPEC["shade_diameter"] / 2.0
    # The shade hangs BELOW the head joint rather than straddling it: with the
    # shell top at the joint centre the raked arm passes straight through the
    # shade wall and the silhouette reads as a mistake.
    hang = 14.0
    shade = _shell("LampShade", [
        (rim_r - 3.0, 0.0),        # inside of the rim
        (r_out_in, shade_h),       # up the inside
        (r_out_out, shade_h),      # across the top rim
        (rim_r, 0.0),              # down the outside to the rim
    ], centre=(0.0, -reach, head_z - shade_h - hang), mat=paint)

    # the lining is a second material on the SAME solid, never a second shell
    bkit.assign_faces_by(shade, inner,
                         lambda c, n: (c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM
                         < rim_r - 1.6)

    bulb = bkit.uv_sphere("LampBulb", 15.0, segments=32, rings=16,
                          centre=(0.0, -reach, head_z - shade_h - hang + 22.0),
                          mat=glow)

    switch = bkit.rounded_box("LampSwitch", 30.0, 16.0, 6.0, r=2.0, segments=3,
                              centre=(38.0, 0.0, base_h), mat=plastic)

    return dict(spec=SPEC, parts=8, shade_walled=bool(SHELL_LOOP))


# How each SPEC dimension is measured. The harness measures the geometry; the
# model only declares the intent, so a claim cannot be satisfied by asserting it.
CHECKS = [
    dict(name="base_diameter", mm=150.0, tol=0.5, how="diameter", part="LampBase"),
    dict(name="base_height", mm=21.0, tol=0.4, how="bbox_z", part="LampBase"),
    dict(name="column_length", mm=130.0, tol=0.4, how="bbox_z", part="LampColumn"),
    dict(name="shade_diameter", mm=110.0, tol=0.5, how="diameter", part="LampShade"),
    dict(name="shade_height", mm=80.0, tol=0.4, how="bbox_z", part="LampShade"),
]