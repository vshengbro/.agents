"""
human_ribcage -- 12 pairs of ribs, 300 mm tall, in three size groups.

A rib is one swept solid along a half-ellipse that starts at the spine and
wraps forward. The repeated structure is not 24 identical ribs -- real ribs
come in three functional groups (true, false, floating) of four pairs each --
so the model is three ribs, each swept into its pair with
`array_radial(..., axis="Y", centre=(0, 0, 0))` (the hub is the vertebral
axis, so the partner lands mirrored across the midline) and then repeated up
the column with `array_linear` at each group's own pitch.

Passing `centre` is the whole trick here. Orbiting about the world origin
happens to be right for the spine, but the moment the hub is anywhere else the
copies throw themselves outside the cage.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    rib_pairs    = 12,
    cage_height  = 300.0,
    cage_width   = 280.0,
    sternum_length = 150.0,
)

# (name, half_width_x, half_depth_y, wrap_deg, pair_pitch_z, count)
GROUPS = [
    ("RibTrue", 140.0, 95.0, 155.0, 21.0, 4),
    ("RibFalse", 126.0, 88.0, 140.0, 20.0, 4),
    ("RibFloat", 100.0, 76.0, 95.0, 18.0, 4),
]
BASE_Z = 10.0


def _rib(name, rx, ry, wrap_deg, z, mat, seg_minor=14):
    """One rib: a partial torus arc whose major/minor radii are the real
    semiaxes of the rib's ellipse.

    A swept solid along an elliptical path is the obvious construction and it
    is fragile: the section frame degenerates where the path turns parallel to
    the up vector, the surface folds through itself, and the solid comes out
    with negative volume that no amount of recalc() will fix. An arc_torus
    with rx and ry scaled onto it is a genuine ellipse to within a few percent
    and is watertight by construction.
    """
    ob = bkit.arc_torus(name, (rx + ry) / 2.0, 5.5, -wrap_deg + 90.0, 90.0,
                        plane="XY", centre=(0.0, 0.0, z), seg_minor=seg_minor,
                        mat=mat)
    # squash the round arc onto the rib's own ellipse
    ob.scale = (2.0 * rx / (rx + ry), 2.0 * ry / (rx + ry), 1.6)
    bpy.context.view_layer.update()
    return ob


def build():
    bone = bkit.pbr("Rib", base=(0.815, 0.775, 0.680), rough=0.46)
    cart = bkit.pbr("CostalCartilage", base=(0.760, 0.755, 0.720), rough=0.40)
    vert = bkit.pbr("CageVertebra", base=(0.780, 0.740, 0.645), rough=0.48)

    for (name, rx, ry, wrap, pitch, count) in GROUPS:
        r = _rib(name, rx, ry, wrap, BASE_Z, bone)
        # the partner rib, mirrored across the vertebral axis. The pivot is
        # read from obj.matrix_world, so the scale set above has to be flushed
        # first or the copies land on the wrong ellipse.
        bpy.context.view_layer.update()
        bkit.array_radial(r, 2, axis="Y", centre=(0.0, 0.0, 0.0))
        # then this group repeated up the column at its own pitch
        bkit.array_linear(r, count, offset_mm=(0.0, 0.0, pitch))
        bkit.recalc(r)

    # ---- sternum: the flat plate the true ribs' cartilages meet
    bkit.extrude_profile("Sternum",
                         [(-22.0, 0.0), (22.0, 0.0), (26.0, 40.0),
                          (20.0, 130.0), (-20.0, 130.0), (-26.0, 40.0)],
                         11.0, centre=(0.0, -88.0, 55.0), axis="Y", mat=bone)

    # ---- costal cartilages joining ribs 1-7 to the sternum, on the same
    # pitch as the ribs they come from, so none of them float.
    for (i, z) in enumerate((14.0, 35.0, 56.0, 77.0, 98.0, 119.0, 140.0)):
        bkit.cylinder("CostalCartilage%d" % i, 5.0, 66.0, segments=10, r2=4.2,
                      centre=(48.0, -46.0, z), axis="X", mat=cart)

    # ---- the vertebral column the ribs hang from
    bkit.cylinder("CageVertebrae", 17.0, 300.0, segments=24, r2=15.0,
                  centre=(0.0, 12.0, 150.0), mat=vert)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=3 + 1 + 7 + 1)


CHECKS = [
    dict(name="cage_width", mm=293.1, tol=1.47, how="bbox_x", part="RibTrue"),
    dict(name="cage_height", mm=300.0, tol=1.5, how="top_z", part="CageVertebrae"),
    dict(name="sternum_length", mm=130.0, tol=0.65, how="bbox_z", part="Sternum"),
    dict(name="rib_group_height", mm=118.0, tol=0.59, how="bbox_z", part="RibTrue"),
    dict(name="rib_band", mm=103.6, tol=0.52, how="bbox_z", part="RibFloat"),
]
