"""spoon -- 175 mm tablespoon: oval bowl with a 1.6 mm wall, tapered handle.

Laid on the table the way a spoon actually rests, bowl up, handle running along
+Y: that puts the bowl's cavity in the top view and the full length in the
side view, which is where the two strongest silhouettes of a spoon live.

The bowl is a lathed dish scaled 0.73 in Y to make it oval. A non-uniform
object scale is a ratio, not a coordinate, so it is the one transform here
that does not go through bkit.move(); the view-layer update afterwards is what
makes the next bbox() see it.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    bowl_width=33.0,        # across the oval bowl, its widest axis
    bowl_length=24.0,       # the other axis of the same bowl
    bowl_depth=8.0,
    handle_length=165.0,
    overall_length=187.0,   # bowl edge to handle tip
    wall=1.6,
)

OVAL = 0.73                # 33 -> 24 across the bowl

BOWL = [
    (0.0, 0.0),            # outside bottom, on the axis
    (9.0, 0.0),
    (14.0, 0.5),
    (16.4, 1.8),
    (16.5, 8.0),           # outer wall up to the rim
    (15.0, 8.2),           # over the rim
    (14.9, 6.0),           # inner wall down
    (13.5, 3.6),
    (11.0, 2.2),
    (7.0, 1.7),
    (0.0, 1.7),            # inside floor on the axis: a real 1.7 mm base
]

# handle stations: y, width, thickness, centre height above the table
STATIONS = [
    (10.0, 11.0, 5.2, 7.2),    # buried in the bowl wall
    (30.0, 12.0, 4.8, 6.6),
    (60.0, 11.0, 4.2, 5.6),
    (95.0, 10.0, 3.6, 4.4),
    (130.0, 9.5, 3.2, 3.2),
    (160.0, 11.0, 3.0, 2.0),
    (175.0, 9.5, 2.8, 1.45),   # tip rests on the table
]


def build():
    # A mirror metal reflects this dark studio and renders black. Dropping the
    # metallic fraction to 0.65 keeps a diffuse component for the key light to
    # land on, which is what makes cutlery read as steel instead of a silhouette.
    steel = bkit.pbr("CutlerySteel", base=(0.82, 0.83, 0.85), metal=0.65,
                     rough=0.22)

    bowl = bkit.lathe("SpoonBowl", BOWL, segments=80, mat=steel)
    bowl.scale.y = OVAL
    bpy.context.view_layer.update()
    bkit.move(bowl, 0.0, 0.0, 0.0)

    sections = []
    for (y, w, t, zc) in STATIONS:
        ring = bkit.superellipse_section(w, t, n=4.0, steps=20)
        sections.append([(px, y, pz + zc) for (px, pz) in ring])
    handle = bkit.loft("SpoonHandle", sections, closed_loop=True,
                       cap_start=True, cap_end=True, mat=steel,
                       smooth=True)
    # loft() does not orient the winding; recalc makes the signed volume
    # positive so health() stops reporting inverted normals.
    bkit.recalc(handle)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="bowl_width", mm=33.0, tol=0.3, how="bbox_x", part="SpoonBowl"),
    dict(name="handle_length", mm=165.0, tol=0.3, how="bbox_y",
         part="SpoonHandle"),
    dict(name="overall_length", mm=187.0, tol=0.3, how="bbox_y"),
]
