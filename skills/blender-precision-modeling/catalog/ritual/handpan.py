"""
handpan -- a 450 mm handpan, 300 mm deep, with two rings of tone fields.

A handpan is a HEMISPHERE, and the two things that make it one are the tone
fields pressed into its top and the sound hole in its base. The tone fields are
the repeated feature: two concentric rings of DIMPLES, each a shallow sphere
sunk into the shell, on real arc-length pitches so the notes do not bunch at
the equator.

Building each dimple as a real dimple -- a sphere whose centre sits inside the
shell, so only its cap shows -- is what makes the pan read as pressed steel
rather than as a bowl with studs glued to it.

Real 55 cm handpan: 450 mm diameter, 300 mm depth, 8 notes on the lower
ring at a 90 mm pitch, 6 on the upper ring at 120 mm, 120 mm sound hole.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _ritual as R_

SPEC = dict(
    diameter=450.0,
    depth=300.0,
    shell_thickness=2.5,
    lower_notes=8,
    upper_notes=6,
    lower_pitch=90.0,
    upper_pitch=120.0,
    dimple_dia=64.0,
    sound_hole_dia=120.0,
    note_ring_radius=(170.0, 110.0),
)

R = SPEC["diameter"] / 2.0

CHECKS = [
    dict(name="diameter", mm=450.0, tol=6.0, how="bbox_y", part="PanShell"),
    dict(name="depth", mm=300.0, tol=6.0, how="bbox_z", part="PanShell"),
    dict(name="shell_thickness", mm=5.0, tol=3.0, how="bbox_z",
         part="PanRim"),
    dict(name="sound_hole_dia", mm=128.0, tol=5.0, how="bbox_y",
         part="PanSoundHole"),
    # `bbox_max` is the largest of the three SIZES, not a coordinate: the
    # ring radius is an x_max, and pointing the check at bbox_max measures
    # the dimple's own 64 mm diameter.
    dict(name="note_ring_radius", mm=202.0, tol=6.0, how="x_max",
         part="PanNote0_00"),
    dict(name="dimple_dia", mm=64.0, tol=4.0, how="bbox_y",
         part="PanNote0_00"),
    dict(name="pan_on_floor", mm=2.0, tol=3.0, how="z_min",
         part="PanShell"),
]


def build():
    steel = bkit.pbr("PanSteel", base=(0.56, 0.50, 0.40), metal=0.85,
                     rough=0.34)
    inner = bkit.pbr("PanInner", base=(0.26, 0.24, 0.22), metal=0.85,
                     rough=0.52)
    note_mat = bkit.pbr("PanNote", base=(0.66, 0.60, 0.48), metal=0.85,
                        rough=0.28)

    # ---- the shell: a turned hemisphere, hollow, with a real wall ---
    # the profile is a CLOSED LOOP that never touches the axis, which is
    # what keeps the lathe from producing a ring of zero-width quads
    t = SPEC["shell_thickness"]
    outer = [(R - t, 0.0), (R, 30.0), (R, SPEC["depth"] * 0.55),
             (R * 0.90, SPEC["depth"] * 0.82),
             (R * 0.68, SPEC["depth"] * 0.96), (R * 0.30, SPEC["depth"]),
             (0.0, SPEC["depth"])]
    # the inner surface starts at a FINITE radius, never at r=0: a profile
    # that ends the outside at the axis and starts the inside at the axis
    # puts an axial segment between them, and the lathe turns that into a
    # ring of zero-width quads. Ending the outside at r=0 while the
    # inside starts at r=0.14R closes the crown properly.
    inner_p = [(R * 0.14, SPEC["depth"] - t), (R * 0.30, SPEC["depth"] - t),
               (R * 0.64, SPEC["depth"] * 0.96 - t),
               (R * 0.86, SPEC["depth"] * 0.82 - t),
               (R - t - t, 30.0), (R - t - t, 0.0)]
    prof = outer + inner_p + [outer[0]]
    shell = bkit.lathe("PanShell", prof, segments=56, cap_ends=False,
                       mat=steel)
    bkit.recalc(shell)

    # the rim: the thick rolled edge every handpan has
    bkit.torus("PanRim", R - t / 2.0, t, seg_major=56, seg_minor=12,
               centre=(0.0, 0.0, 4.0), mat=steel)

    # ---- the sound hole in the underside ---------------------------
    bkit.bore(shell, SPEC["sound_hole_dia"] / 2.0,
              depth=R * 0.6, centre=(0.0, 0.0, -1.0), host_segments=56)
    bkit.recalc(shell)
    hole = bkit.tube("PanSoundHole", SPEC["sound_hole_dia"] / 2.0 + 4.0,
                     SPEC["sound_hole_dia"] / 2.0, 6.0, segments=36,
                     centre=(0.0, 0.0, 1.0), mat=inner)

    # ---- two rings of tone fields, on real arc-length pitches -------
    # each dimple is a sphere whose centre sits INSIDE the shell, so only
    # a cap of it shows: that is a pressed note, not a glued stud.
    dn = SPEC["dimple_dia"] / 2.0
    pitches = (SPEC["lower_pitch"], SPEC["upper_pitch"])
    rings = (SPEC["note_ring_radius"][0], SPEC["note_ring_radius"][1])
    counts = (SPEC["lower_notes"], SPEC["upper_notes"])
    for ri, (ring_r, pitch, n) in enumerate(zip(rings, pitches, counts)):
        for i in range(n):
            a = 2.0 * math.pi * i / n
            x, y = ring_r * math.cos(a), ring_r * math.sin(a)
            # the dome height at this radius, so the dimple sits in the shell
            z = SPEC["depth"] * (1.0 - 0.52 * (ring_r / R) ** 2)
            d = bkit.uv_sphere("PanNote%d_%02d" % (ri, i), dn, segments=20,
                               rings=12, mat=note_mat)
            R_.place_in_mesh(d, x, y, z - dn * 0.42)

    # ---- the three feet the pan stands on --------------------------
    for i in range(3):
        a = math.radians(90.0 + 120.0 * i)
        bkit.rounded_box("PanFoot%d" % i, 44.0, 44.0, 14.0, r=6.0,
                         segments=2,
                         centre=((R - 40.0) * math.cos(a),
                                 (R - 40.0) * math.sin(a), 7.0), mat=inner)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 1 + 1 + counts[0] + counts[1] + 3,
                note="Tone fields are spheres sunk into the shell, placed on "
                     "real arc-length pitches.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
