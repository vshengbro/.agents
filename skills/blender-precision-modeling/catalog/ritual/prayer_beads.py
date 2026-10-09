"""
prayer_beads -- 27-bead mala with a guru bead and a silk tassel, 56 mm across.

A mala is a LOOP, so the 27 beads are one bead placed at the loop radius and
repeated with `array_radial(count=27, centre=...)` about the loop's own centre.
Hand-placing 27 beads is how you get two of them in the same place.

The loop is 48 mm inside diameter with 8 mm beads, which is the real proportion
of a wooden mala; the guru bead and the tassel sit INSIDE the loop's footprint
so the beads' own bounding circle is the model's silhouette.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _ritual as R

SPEC = dict(
    bead_diameter=8.0,
    bead_count=27,
    loop_diameter=48.0,
    guru_diameter=12.0,
    tassel_length=22.0,
    overall_width=56.0,
)

CHECKS = [
    dict(name="bead_diameter", mm=8.0, tol=0.4, how="bbox_x",
         part="BeadLoop"),
    dict(name="bead_count_span", mm=56.0, tol=1.0, how="bbox_x",
         part="BeadLoop"),
    dict(name="guru_diameter", mm=12.0, tol=0.4, how="bbox_x",
         part="BeadGuru"),
    dict(name="tassel_length", mm=22.0, tol=1.0, how="bbox_z",
         part="BeadTassel"),
    dict(name="overall_width", mm=56.0, tol=1.0, how="bbox_x", part=None),
]

BEAD_R = SPEC["bead_diameter"] / 2.0
LOOP_R = SPEC["loop_diameter"] / 2.0


def build():
    wood = R.cedar("BeadWood", base=(0.38, 0.20, 0.09), rough=0.40)
    silk = bkit.pbr("BeadSilk", base=(0.58, 0.10, 0.10), rough=0.86)
    gold = R.gild("BeadGold", base=(0.88, 0.72, 0.34))

    # ---- the loop: one bead, arrayed about the loop's own centre ---------
    b = R.bead("BeadLoop", BEAD_R, (LOOP_R, 0.0, BEAD_R), mat=wood)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = b
    b.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    b.select_set(False)
    b.location = bkit.v(LOOP_R, 0.0, BEAD_R)
    bpy.context.view_layer.update()
    bkit.array_radial(b, SPEC["bead_count"], axis="Z",
                      centre=(0.0, 0.0, BEAD_R))

    # ---- guru bead + tassel, both inside the loop's footprint ------------
    R.bead("BeadGuru", SPEC["guru_diameter"] / 2.0, (0.0, 0.0, 6.0),
           mat=gold, segments=24, rings=14)
    R.turned_leg("BeadTassel", SPEC["tassel_length"], 7.0, 2.4, 5.0,
                 segments=20, mat=silk)
    bkit.move(bpy.data.objects["BeadTassel"], 0.0, 0.0, 0.0)

    # ---- the cord that runs through the beads ---------------------------
    ring = bkit.torus("BeadCord", LOOP_R, 1.1, seg_major=72, seg_minor=10,
                      centre=(0.0, 0.0, BEAD_R),
                      mat=bkit.preset("fabric"))
    return dict(spec=SPEC, parts=4)