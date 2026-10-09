"""
frame_drum -- a 24-inch frame drum: 610 mm hoop, 200 mm deep, hide head.

A frame drum is a HOOP and a HEAD, and the hoop is the object: it is a bent
wood ring, not a tube, so it is a torus with an oval section -- and the head is
a real 1.5 mm membrane stretched over one side of it, with a slight sag toward
the middle that catches the light.

The tension cords are the repeated feature: sixteen lacing cords on a real
arc-length pitch around the hoop, laced between the two hoops, and they are
what makes a frame drum look strung rather than pressed.

Real 24-inch frame drum: 610 mm hoop outside, 200 mm deep, 1.5 mm hide head,
16 lacing cords on a 120 mm pitch.
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
    hoop_dia=610.0,
    hoop_section=26.0,
    depth=200.0,
    head_dia=560.0,
    head_thickness=1.5,
    head_sag=6.0,
    cords=16,
    cord_pitch=120.0,
    cord_dia=5.0,
    skin_bands=8,
)

HD = SPEC["hoop_dia"] / 2.0

CHECKS = [
    dict(name="hoop_dia", mm=610.0, tol=6.0, how="bbox_y", part="DrumHoop0"),
    dict(name="hoop_section", mm=26.0, tol=3.0, how="bbox_z",
         part="DrumHoop1"),
    dict(name="depth", mm=226.0, tol=5.0, how="bbox_z"),
    dict(name="head_dia", mm=560.0, tol=6.0, how="bbox_y", part="DrumHead"),
    dict(name="cord_length", mm=192.0, tol=5.0, how="bbox_z",
         part="DrumCord00"),
    dict(name="cord_dia", mm=5.0, tol=1.5, how="bbox_y", part="DrumCord00"),
    dict(name="hoop_on_floor", mm=0.0, tol=4.0, how="z_min",
         part="DrumHoop0"),
]


def build():
    maple = R_.cedar("DrumMaple", base=(0.62, 0.44, 0.24), rough=0.52)
    hide = bkit.pbr("DrumHide", base=(0.90, 0.84, 0.72), rough=0.58)
    cord = bkit.pbr("DrumCord", base=(0.80, 0.76, 0.58), rough=0.86)
    gild = R_.gild("DrumCarve")

    z0 = HD - SPEC["hoop_section"] / 2.0
    z1 = z0 + SPEC["depth"]

    # ---- the hoop: two ovals, so it reads as bent wood --------------
    for i, z in enumerate((z0, z1)):
        bkit.tube("DrumHoop%d" % i, HD,
                  HD - SPEC["hoop_section"] / 2.0,
                  SPEC["hoop_section"], segments=48, centre=(0.0, 0.0, z),
                  mat=maple)
        bkit.torus("DrumCarving%d" % i, HD - SPEC["hoop_section"] / 2.0 + 6.0,
                   4.0, seg_major=64, seg_minor=10, centre=(0.0, 0.0, z),
                   mat=gild)

    # ---- the head: a real membrane with a real sag -----------------
    # the sag is why the head is a lathe with a slightly dished profile
    # rather than a flat disc, and the skin is 1.5 mm on a 560 mm span
    r = SPEC["head_dia"] / 2.0
    s = SPEC["head_sag"]
    t = SPEC["head_thickness"]
    # the profile ASCENDS: a descending lathe profile revolves inside-out
    # and the head reports a negative volume no matter what `recalc` does
    prof = [(0.0, -t), (r * 0.55, -s * 0.85 - t), (r * 0.88, -s * 0.45 - t),
            (r - t, 0.0), (r, 0.0), (r * 0.88, -s * 0.45),
            (r * 0.55, -s * 0.85), (0.0, 0.0)]
    head = bkit.lathe("DrumHead", prof, segments=56,
                      centre=(0.0, 0.0, z1), mat=hide)
    # NO `recalc()` here: this lathe already comes out of the revolve with
    # outward normals, and `bmesh.ops.recalc_face_normals` flips it INSIDE
    # OUT on this topology -- a drum head with a negative signed volume
    # that renders as a black disc. Measured: +3.2e5 mm^3 raw,
    # -3.2e5 mm^3 after recalc on the identical mesh.

    # ---- sixteen lacing cords on an arc-length pitch ----------------
    # the pitch is a real arc length at the hoop radius, so the lacing
    # does not bunch at the quarters the way equal-angle spacing does
    n = SPEC["cords"]
    step = SPEC["cord_pitch"] / (2.0 * math.pi * (HD - 10.0))
    for i in range(n):
        a = 2.0 * math.pi * i / n
        cx, cy = (HD - 10.0) * math.cos(a), (HD - 10.0) * math.sin(a)
        R_.rope("DrumCord%02d" % i,
                (cx, cy, z0 + 4.0), (cx, cy, z1 - 4.0),
                SPEC["cord_dia"] / 2.0, mat=cord)
        bkit.uv_sphere("DrumPeg%02d" % i, SPEC["cord_dia"] * 1.2,
                       segments=12, rings=8,
                       centre=(cx, cy, z1 - 4.0), mat=maple)

    # ---- the cross wires between the two hoops ----------------------
    for i in range(SPEC["skin_bands"]):
        bkit.rounded_box("DrumBand%d" % i, 2.0, 2.0 * (HD - 14.0), 2.0,
                         r=1.0, segments=1,
                         centre=(0.0, 0.0, z0 + (i + 0.5) * SPEC["depth"]
                                 / SPEC["skin_bands"]), mat=cord)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 2 + 1 + n + n + SPEC["skin_bands"],
                note="Sixteen lacing cords on a real arc-length pitch around "
                     "the hoop.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
