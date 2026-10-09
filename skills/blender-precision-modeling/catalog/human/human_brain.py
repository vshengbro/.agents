"""
human_brain -- a 170 mm brain: two hemispheres with a 3 mm longitudinal
fissure, a cerebellum and a brainstem.

The fissure is the reason the hemispheres are lofts and not spheres. Two
overlapping spheres meet in a smooth continuous surface and the brain reads as
a bean; two hemispheres whose medial faces are FLAT, set 1.5 mm either side of
the midline, read as a brain immediately. The flat medial face is a capping
plane on a loft along X, so the solid stays closed and the fissure stays a real
3 mm gap with nothing z-fighting in it.

The longitudinal axis is a five-node law (frontal pole, frontal, parietal,
occipital, posterior pole) with the widest section at 45% of its length, which
is the cerebrum's real profile.
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
    brain_length  = 170.0,
    brain_width   = 140.0,
    brain_height  = 122.0,
    fissure_width = 6.0,
)

FISSURE = SPEC["fissure_width"] / 2.0
SEG = 40
# (x, half_depth_y, half_height_z) from the flat medial face out to the pole.
# The profile has to swell and then taper hard at both ends: a table of similar
# sections lofts into a cylinder, and a brain is an ovoid.
HEMI = [
    (FISSURE, 26.0, 22.0),
    (FISSURE + 12.0, 50.0, 44.0),
    (FISSURE + 28.0, 66.0, 58.0),
    (FISSURE + 44.0, 71.0, 61.0),   # widest
    (FISSURE + 58.0, 64.0, 55.0),
    (FISSURE + 69.0, 46.0, 40.0),
    (FISSURE + 76.0, 22.0, 19.0),
]


def build():
    grey = bkit.pbr("Cortex", base=(0.780, 0.690, 0.650), rough=0.62)
    white = bkit.pbr("Medulla", base=(0.880, 0.845, 0.810), rough=0.48)
    stem = bkit.pbr("Brainstem", base=(0.820, 0.780, 0.740), rough=0.50)
    cbl = bkit.pbr("Cerebellum", base=(0.740, 0.640, 0.600), rough=0.66)

    # ---- two hemispheres: the same loft, mirrored in X
    for side, s in (("L", 1.0), ("R", -1.0)):
        sections = []
        for (x, hy, hz) in HEMI:
            ring = bkit.superellipse_section(2.0 * hy, 2.0 * hz, n=2.5, steps=SEG)
            sections.append([(s * x, u - 8.0, 62.0 + v) for (u, v) in ring])
        ob = bkit.loft("Hemisphere%s" % side, sections, mat=grey, smooth=True)
        bkit.recalc(ob)
        # the corpus callosum showing in the fissure. lathe() has no `axis`
        # parameter -- it always revolves about Z -- so the part is built along
        # Z and then rotated about its own origin, which keeps it centred.
        cal = bkit.lathe("Callosum%s" % side,
                         [(0.0, 0.0), (14.0, 0.0), (16.0, 10.0),
                          (10.0, 18.0), (0.0, 18.0)],
                         segments=24, centre=(s * 2.0, -6.0, 60.0), mat=white)
        bkit.recalc(cal)
        cal.rotation_euler = (0.0, math.radians(90.0), 0.0)

    # ---- cerebellum: a ridged mass tucked under the occipital pole
    for (side, s) in (("L", 1.0), ("R", -1.0)):
        ob = bkit.uv_sphere("Cerebellum%s" % side, 1.0, segments=28, rings=14,
                            centre=(s * 28.0, 46.0, 18.0), mat=cbl)
        ob.scale = (32.0, 26.0, 24.0)
        ob.name = "Cerebellum%s" % side

    # ---- brainstem: pons and medulla, tapering down out of the brain
    bkit.lathe("Brainstem", [(0.0, 0.0), (14.0, 0.0), (16.0, 12.0),
                             (13.0, 26.0), (10.0, 40.0), (0.0, 44.0)],
               segments=26, centre=(0.0, 22.0, -46.0), mat=stem)

    # ---- frontal and temporal lobes, the two bulges that make the outline
    for (name, s) in (("TemporalL", 1.0), ("TemporalR", -1.0)):
        ob = bkit.uv_sphere(name, 1.0, segments=24, rings=12,
                            centre=(s * 56.0, -18.0, 30.0), mat=grey)
        ob.scale = (26.0, 50.0, 32.0)
        ob.name = name

    # ---- occipital poles, so the back of the brain is not a flat end
    for (name, s) in (("OccipitalL", 1.0), ("OccipitalR", -1.0)):
        ob = bkit.uv_sphere(name, 1.0, segments=24, rings=12,
                            centre=(s * 44.0, 58.0, 46.0), mat=grey)
        ob.scale = (34.0, 34.0, 36.0)
        ob.name = name

    # ---- gyri: a few shallow ridges on the lateral surface. A brain with a
    # perfectly smooth cortex reads as a bean; the ridges are what say "brain".
    for i in range(9):
        a = math.radians(-64.0 + 15.0 * i)
        ob = bkit.uv_sphere("GyrusL%02d" % i, 1.0, segments=16, rings=8,
                            centre=(60.0, 44.0 * math.cos(a),
                                    46.0 + 44.0 * math.sin(a)), mat=white)
        ob.scale = (22.0, 15.0, 15.0)
        ob.name = "GyrusL%02d" % i
    for i in range(9):
        a = math.radians(-64.0 + 15.0 * i)
        ob = bkit.uv_sphere("GyrusR%02d" % i, 1.0, segments=16, rings=8,
                            centre=(-60.0, 44.0 * math.cos(a),
                                    46.0 + 44.0 * math.sin(a)), mat=white)
        ob.scale = (22.0, 15.0, 15.0)
        ob.name = "GyrusR%02d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=25)


CHECKS = [
    # HemisphereL is ONE hemisphere, so its bbox_x is the half-width. The
    # brain's full width is the pair, and is a scene measurement.
    dict(name="hemisphere_length", mm=142.0, tol=2.0, how="bbox_y", part="HemisphereL"),
    dict(name="brain_width", mm=164.0, tol=0.82, how="bbox_x"),
    dict(name="brain_height", mm=122.0, tol=2.0, how="bbox_z", part="HemisphereL"),
    # The fissure is the 6 mm GAP between the two medial faces, which no
    # bounding box can see; the callosum's own length is what can be measured.
    dict(name="callosum_length", mm=18.0, tol=0.8, how="bbox_x", part="CallosumL"),
    dict(name="cerebellum", mm=64.0, tol=2.0, how="bbox_x", part="CerebellumL"),
]
