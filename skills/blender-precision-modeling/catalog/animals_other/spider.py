"""spider -- a 120 mm garden spider: the two-part body (cephalothorax and
rounded abdomen) and EIGHT legs, each with a femur, a patella, a tibia and a
tarsus, arranged in the real four-pairs-per-side pattern.

Eight legs is the count that fails after arms. One leg is authored on +X and
swept with `array_radial(count=8, centre=HUB)` about the body axis; six is the
classic miss. The per-leg JOINT ANGLES differ between the pairs, so the four
pairs are built as four swept legs each arrayed twice about the hub -- which is
why this is not simply eight copies of one tube.

Construction: a lathed cephalothorax and abdomen, four swept legs arrayed two
at a time about the body axis, eight eyes as small spheres, and the chevron
abdomen marking as a second material. Nothing is booleaned.

Orientation: the spider faces -Y, X lateral, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    body_length=28.0,
    cephalothorax_length=28.0,
    abdomen_length=24.0,
    leg_count=8,
    leg_span=120.0,
    leg_pairs=4,
)

HUB = (0.0, -2.0, 11.0)            # the body axis the legs orbit
# Each pair gets its OWN path: a spider's four pairs of legs do not point the
# same way. Pair 1 reaches forward, pair 2 laterally, pair 3 back, pair 4
# straight back -- and each is arrayed twice about the body axis.
LEGS = [
    # (y_offset, name, path, radii)
    (-4.0, "Front", [(0.0, 0.0, 0.0), (18.0, -14.0, 10.0),
                     (34.0, -20.0, 14.0), (46.0, -18.0, 4.0),
                     (52.0, -14.0, 0.6)],
     [(4.0, 4.0), (3.2, 3.2), (2.4, 2.4), (1.6, 1.6), (0.7, 0.7)]),
    (0.0, "Second", [(0.0, 0.0, 0.0), (22.0, 2.0, 16.0),
                     (42.0, 8.0, 20.0), (56.0, 10.0, 8.0),
                     (62.0, 8.0, 0.6)],
     [(4.2, 4.2), (3.4, 3.4), (2.5, 2.5), (1.6, 1.6), (0.7, 0.7)]),
    (6.0, "Third", [(0.0, 0.0, 0.0), (22.0, 8.0, 12.0),
                    (42.0, 18.0, 10.0), (54.0, 26.0, 4.0),
                    (58.0, 30.0, 0.6)],
     [(4.2, 4.2), (3.4, 3.4), (2.5, 2.5), (1.6, 1.6), (0.7, 0.7)]),
    (12.0, "Fourth", [(0.0, 0.0, 0.0), (18.0, -6.0, 8.0),
                      (32.0, -14.0, 4.0), (40.0, -20.0, 1.0),
                      (44.0, -24.0, 0.5)],
     [(3.6, 3.6), (2.8, 2.8), (2.0, 2.0), (1.3, 1.3), (0.6, 0.6)]),
]


def build():
    chitin = bkit.pbr("SpiderChitin", base=(0.20, 0.14, 0.11), rough=0.42,
                      coat=0.25)
    dark = bkit.pbr("SpiderDark", base=(0.07, 0.05, 0.05), rough=0.40)
    mark = bkit.pbr("SpiderMark", base=(0.62, 0.48, 0.24), rough=0.46)
    eye = bkit.pbr("SpiderEye", base=(0.02, 0.02, 0.02), rough=0.06)

    ceph = bkit.lathe("Cephalothorax",
                      [(0.0, 0.0), (10.0, 1.0), (13.0, 6.0), (12.0, 16.0),
                       (7.0, 25.0), (0.0, 28.0)],
                      segments=36, centre=(0.0, 4.0, 11.0), mat=chitin)
    F.bake_rot(ceph, "X", -90.0)

    abd = bkit.lathe("Abdomen",
                     [(0.0, 0.0), (11.0, 1.0), (15.0, 6.0), (14.0, 15.0),
                      (8.0, 22.0), (0.0, 24.0)],
                     segments=36, centre=(0.0, -20.0, 12.0), mat=dark)
    F.bake_rot(abd, "X", -90.0)

    # ---- EIGHT legs: four authored pairs, each arrayed twice about the hub,
    # so the legs number 8 without all eight being identical copies.
    for y_off, tag, path, rad in LEGS:
        p = [(x, y + y_off, z + HUB[2]) for (x, y, z) in path]
        leg = F.tube("Leg%sL" % tag, p, rad, chitin, n=2.2, steps=16)
        bpy.context.view_layer.update()
        bkit.array_radial(leg, 2, centre=HUB)

    # ---- the pale chevron on the abdomen: a second material on the ONE
    # abdomen solid, so there is no z-fighting with a second shell
    bkit.assign_faces_by(abd, mark,
                         lambda c, n: -30.0 < c.y / bkit.MM < -20.0)

    # ---- eight eyes: two rows of four across the front of the cephalothorax
    for row, (zz, count, xr) in enumerate(((15.4, 4, 5.6), (11.6, 4, 3.4))):
        for i in range(count):
            x = -xr + 2.0 * xr * i / (count - 1)
            bkit.uv_sphere("Eye%d%d" % (row, i), 1.3, segments=12, rings=6,
                           centre=(x, -10.0 + row * 0.8, zz), mat=eye)

    # ---- chelicerae: the two small mouthparts in front
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.cone_between("Chelicera%s" % side,
                       (sx * 3.0, -8.0, 9.0), (sx * 2.4, -13.0, 5.5),
                       2.4, 0.8, seg=8, mat=dark)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=18)


CHECKS = [
    dict(name="overall_length", mm=77.0, tol=5.0, how="bbox_y"),
    dict(name="leg_span", mm=124.0, tol=8.0, how="bbox_x"),
    dict(name="cephalothorax_length", mm=32.0, tol=4.0, how="bbox_y",
         part="Cephalothorax"),
    dict(name="abdomen_length", mm=28.0, tol=4.0, how="bbox_y", part="Abdomen"),
    dict(name="body_depth", mm=36.0, tol=4.0, how="bbox_z"),
]