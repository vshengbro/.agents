"""
human_tooth -- a 21.5 mm mandibular first molar: 10.5 x 9.5 x 7.5 mm crown,
a neck, and two diverging roots.

The crown is not a smooth dome. It is a superellipse with n = 4 -- a squircle --
so the occlusal surface is a rounded square, and then four cusp spheroids are
placed on it at the corners. That is the difference between a molar and a
pebble, and it is why the crown is a squircle rather than a sphere.

The two root canals are `bkit.bore` calls. They use the helper rather than a
raw `cylinder` for one reason: a cutter sharing the host's exact segment count
puts coincident vertices on the root surface and the EXACT solver answers with
non-manifold edges, so `bkit.bore` deliberately picks `host_segments + 7`.
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
    crown_width  = 10.5,   # buccolingual
    crown_depth  = 9.5,    # mesiodistal
    crown_height = 7.5,
    total_length = 21.5,
)

SEG = 32
# (z, sx, sy) -- the crown rising from the neck, squaring off toward the
# occlusal surface.
CROWN = [
    (0.0, 6.6, 6.0),
    (1.6, 8.6, 7.8),
    (3.4, 10.0, 9.0),
    (5.4, 10.5, 9.5),
    (6.8, 9.4, 8.4),
    (7.5, 6.4, 5.6),
]


def build():
    enamel = bkit.pbr("Enamel", base=(0.905, 0.885, 0.820), rough=0.22)
    dentin = bkit.pbr("Dentin", base=(0.800, 0.720, 0.570), rough=0.40)
    pulp = bkit.pbr("Pulp", base=(0.640, 0.400, 0.400), rough=0.56)
    root_m = bkit.pbr("Cementum", base=(0.690, 0.640, 0.520), rough=0.52)
    caries = bkit.pbr("Cavity", base=(0.200, 0.130, 0.110), rough=0.66)

    # ---- crown: a squircle stack, n = 4, so the occlusal table is a rounded
    # square rather than an ellipse
    sections = []
    for (z, sx, sy) in CROWN:
        ring = bkit.superellipse_section(sx, sy, n=4.0, steps=SEG)
        sections.append([(u, v, z) for (u, v) in ring])
    crown = bkit.loft("Crown", sections, mat=enamel, smooth=True)
    bkit.recalc(crown)

    # ---- four cusps on the occlusal corners
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=5.4, pitch_y=5.0)):
        ob = bkit.uv_sphere("Cusp%d" % i, 1.0, segments=16, rings=8,
                            centre=(x, y, 6.4), mat=enamel)
        ob.scale = (3.0, 2.8, 2.6)
        ob.name = "Cusp%d" % i

    # ---- neck and pulp chamber
    bkit.lathe("Neck", [(0.0, -1.0), (6.4, -1.0), (6.2, 1.0), (0.0, 1.0)],
               segments=SEG, centre=(0.0, 0.0, 0.0), mat=dentin)
    bkit.lathe("PulpChamber", [(0.0, 0.0), (3.4, 0.6), (3.0, 4.2),
                               (1.6, 6.0), (0.0, 6.4)],
               segments=24, centre=(0.0, 0.0, 0.6), mat=pulp)

    # ---- two roots diverging mesially and distally
    for i, sx in enumerate((-1.0, 1.0)):
        path = [(sx * 1.4, 0.0, -1.0), (sx * 2.6, 0.0, -6.0),
                (sx * 3.6, 0.0, -11.0), (sx * 4.2, 0.0, -14.0)]
        sections = []
        for (x, y, z) in path:
            r = 3.4 - 0.55 * (-z / 14.0) * 2.0
            ring = bkit.superellipse_section(2.0 * r, 2.0 * r * 0.86, n=2.4,
                                             steps=SEG)
            sections.append([(x + u, y + v, z) for (u, v) in ring])
        root = bkit.loft("Root%d" % i, sections, mat=root_m, smooth=True)
        bkit.recalc(root)
        # the root canal, drilled with bkit.bore so the cutter's segment count
        # deliberately differs from the root's
        bkit.bore(root, 1.0, depth=16.0, centre=(sx * 2.4, 0.0, -7.5),
                  axis="Z", host_segments=SEG, mat=pulp)
        bkit.recalc(root)

    # ---- an occlusal restoration: a small cavity, so the tooth is not a
    # pristine shape and reads as a real tooth
    bkit.uv_sphere("Cavity", 1.0, segments=16, rings=8,
                   centre=(1.6, 1.2, 6.6), mat=caries).scale = \
        (2.4, 2.2, 1.6)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 4 + 2 + 2 + 1)


CHECKS = [
    dict(name="crown_width", mm=10.5, tol=0.3, how="bbox_x", part="Crown"),
    dict(name="crown_depth", mm=9.5,  tol=0.3, how="bbox_y", part="Crown"),
    dict(name="crown_height", mm=7.5, tol=0.3, how="bbox_z", part="Crown"),
    dict(name="total_length", mm=23.0, tol=0.5, how="top_z"),
]
