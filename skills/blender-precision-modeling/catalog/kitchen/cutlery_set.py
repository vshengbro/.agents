"""cutlery_set -- a laid-out three-piece starter set: knife, fork and spoon.

All three lie flat with their long axis along +Y, which is what puts each one's
face in the top view and the full length in the side view. The three X
positions come from `lay_out()` with an explicit 14 mm gap, so the set is
spaced by the width of the widest piece rather than by three typed-in numbers.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    set_length=190.0,       # longest piece, butt to tip
    set_width=91.0,         # across the three, gap included
    gap=14.0,               # clear space between neighbouring pieces
    knife_blade_length=120.0,
    fork_length=176.0,
    spoon_length=109.0,
)

# widest footprint of each piece, in the order they are laid out
WIDTHS = [18.0, 19.0, 26.0]
X_KNIFE, X_FORK, X_SPOON = [c for (c, _w) in bkit.lay_out(WIDTHS, gap=SPEC["gap"])]

KNIFE_BLADE = [
    (-9.0, 0.0), (9.0, 2.0), (9.0, 70.0), (7.0, 104.0),
    (0.0, 120.0), (-6.0, 108.0), (-9.0, 76.0),
]
KNIFE_HANDLE = [
    (-5.5, -70.0), (5.5, -70.0), (5.5, -50.0), (4.5, -10.0),
    (4.0, 2.0), (-4.0, 2.0), (-4.5, -10.0), (-5.5, -50.0),
]

FORK_HANDLE = [
    (-5.5, -68.0), (5.5, -68.0), (5.2, -30.0), (4.2, 4.0), (3.2, 32.0),
    (3.2, 40.0), (-3.2, 40.0), (-3.2, 32.0), (-4.2, 4.0), (-5.2, -30.0),
]
FORK_HEAD = [
    (-3.2, 34.0), (3.2, 34.0), (4.0, 50.0), (9.4, 62.0),
    (9.4, 68.0), (-9.4, 68.0), (-9.4, 62.0), (-4.0, 50.0),
]

SPOON_BOWL = [
    (0.0, 0.0), (6.0, 0.0), (9.5, 0.4), (11.8, 1.4), (13.0, 2.0),
    (13.0, 6.2),                    # rim
    (11.8, 6.4),                    # over the rim
    (11.7, 4.6),                    # down the inside
    (10.4, 2.8), (8.0, 2.0), (5.0, 1.8), (0.0, 1.8),
]
SPOON_STATIONS = [
    (6.0, 8.0, 4.0, 3.0),          # buried in the bowl wall
    (30.0, 9.5, 3.6, 2.6),
    (60.0, 8.5, 3.0, 2.0),
    (85.0, 8.0, 2.6, 1.6),
    (100.0, 7.0, 2.2, 1.2),
]


def build():
    # A mirror metal reflects this dark studio and renders black. Dropping the
    # metallic fraction to 0.65 keeps a diffuse component for the key light to
    # land on, which is what makes cutlery read as steel instead of a silhouette.
    steel = bkit.pbr("CutlerySteel", base=(0.82, 0.83, 0.85), metal=0.65,
                     rough=0.22)

    # ---- knife -------------------------------------------------------------
    blade = bkit.extrude_profile("SetKnifeBlade", KNIFE_BLADE, 1.8,
                                 centre=(X_KNIFE, 0.0, 0.9), axis="Z", mat=steel)
    bkit.extrude_profile("SetKnifeHandle", KNIFE_HANDLE, 7.0,
                         centre=(X_KNIFE, 0.0, 3.5), axis="Z", mat=steel)

    # ---- fork --------------------------------------------------------------
    bkit.extrude_profile("SetForkHandle", FORK_HANDLE, 5.0,
                         centre=(X_FORK, 0.0, 2.5), axis="Z", mat=steel)
    bkit.extrude_profile("SetForkHead", FORK_HEAD, 3.0,
                         centre=(X_FORK, 0.0, 1.5), axis="Z", mat=steel)
    tines = []
    for i, (xc, _w) in enumerate(bkit.lay_out([3.2] * 4, gap=2.0)):
        tines.append(bkit.rounded_box("SetTine%d" % (i + 1), 3.2, 42.0, 1.6,
                                      r=0.6,
                                      centre=(X_FORK + xc, 87.0, 0.8),
                                      mat=steel))
    bkit.join(tines, name="SetForkTines")

    # ---- spoon -------------------------------------------------------------
    bowl = bkit.lathe("SetSpoonBowl", SPOON_BOWL, segments=72, mat=steel)
    bowl.scale.y = 0.70                      # oval bowl: 26 across, 18 deep
    bpy.context.view_layer.update()
    bkit.move(bowl, X_SPOON, 0.0, 0.0)

    sections = []
    for (y, w, t, zc) in SPOON_STATIONS:
        ring = bkit.superellipse_section(w, t, n=4.0, steps=20)
        sections.append([(X_SPOON + px, y, pz + zc) for (px, pz) in ring])
    bkit.loft("SetSpoonHandle", sections, closed_loop=True, cap_start=True,
              cap_end=True, mat=steel, smooth=True)
    # loft() does not orient the winding; recalc makes the signed volume
    # positive so health() stops reporting inverted normals.
    bkit.recalc(bpy.data.objects["SetSpoonHandle"])

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="set_length", mm=190.0, tol=0.3, how="bbox_y"),
    dict(name="set_width", mm=91.0, tol=0.3, how="bbox_x"),
    dict(name="knife_blade_length", mm=120.0, tol=0.3, how="bbox_y",
         part="SetKnifeBlade"),
]
