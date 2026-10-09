"""beetle -- a 32 mm stag beetle: the hard elytra split down the back, the six
spiky legs, the elbowed antennae with clubbed tips, and the male's enormous
mandibles.

Two cues carry it. The elytra are two separate shells meeting at a straight
central suture -- one smooth dome is a woodlouse. And the mandibles are the
species' whole silhouette: a stag beetle's jaws are longer than its head.

Construction: a lathed pronotum, two mirrored elytron shells with a real gap
at the suture, a wedge head, two long mandibles built from a tapered sweep, six
arrayed legs, and two clubbed antennae. Nothing is booleaned.

Orientation: the beetle faces -Y, X lateral, Z up.
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
    overall_length=46.5,
    elytron_width=6.2,
    elytra_length=21.4,
    pronotum_length=6.0,
    leg_count=6,
    mandible_length=14.0,
)

HUB = (0.0, 2.0, 7.0)             # the thorax axis the legs orbit
PRONOTUM = [(0.0, -9.0, 7.0), (0.0, -7.0, 7.5), (0.0, -5.0, 7.2),
            (0.0, -3.6, 6.8)]
PRONOTUM_RAD = [(5.0, 3.0), (6.4, 3.6), (6.2, 3.4), (5.0, 2.8)]
# The head's rear node sits at y = -8.6, INSIDE the pronotum's own span
# (-9.0 .. -3.6). The old y = -10.0 left a 0.27 mm air gap between the two and
# the beetle read as three detached segments rather than one animal.
HEAD = [(0.0, -8.6, 6.6), (0.0, -13.0, 6.6), (0.0, -15.5, 6.4)]
HEAD_RAD = [(3.2, 2.8), (4.0, 3.4), (2.6, 2.2)]
# One wing case, as a dome the loft can actually sweep: (y, outer_x, top_z).
# The dome rises from the suture edge out to its crown, which is what makes two
# mirrored shells read as a split pair rather than one smooth dome.
ELYT_STATIONS = [(-5.0, 2.2, 7.2), (-4.0, 4.6, 8.6), (-2.0, 6.6, 9.4),
                 (6.0, 6.8, 9.4), (13.0, 5.6, 8.0), (16.0, 3.4, 6.6),
                 (16.4, 1.4, 6.0)]
ELYT_X = 0.6          # the suture edge: mirrored, this leaves a 1.2 mm gap
ELYT_ZB = 5.2         # the flat underside both shells share, level with the
                      # pronotum's belly so the body reads as one mass
ELYT_K = 10           # dome samples per section (constant: loft needs equal
                      # ring lengths)
# The mandibles start at y = -14.9, buried in the head (which now ends at
# -15.5). The old y = -16.0 floated them 0.5 mm clear of the face.
LEG = [(0.0, 0.0, 0.0), (3.6, 2.4, -2.6), (6.2, 5.0, -5.6),
       (7.8, 7.6, -6.8)]
LEG_RAD = [(1.1, 1.0), (0.9, 0.8), (0.7, 0.6), (0.35, 0.3)]
MANDIBLE = [(2.6, -14.9, 5.8), (4.6, -22.0, 5.4), (6.4, -27.0, 5.6),
            (6.8, -30.0, 6.4)]
MANDIBLE_RAD = [(1.8, 1.5), (1.4, 1.1), (0.9, 0.7), (0.25, 0.25)]


def _elytron(name, mat):
    """One domed wing case, lofted along the body and closed at both ends.

    `F.plate_xy()` cannot build this: it reads only (x, y) from an outline and
    discards the dome's z, so the shell came out as a flat slab extruded at
    z = 0 -- 5 mm below the pronotum, which is why head, thorax and abdomen
    rendered as three separate objects lying at different heights.
    """
    sections = []
    for (y, xo, zt) in ELYT_STATIONS:
        zs = ELYT_ZB + (zt - ELYT_ZB) * 0.55      # suture edge, below the crown
        ring = []
        for i in range(ELYT_K):
            t = i / float(ELYT_K - 1)
            ring.append((ELYT_X + (xo - ELYT_X) * t, y,
                         zs + (zt - zs) * (t ** 0.7)))
        ring.append((xo, y, ELYT_ZB))              # down the outer wall
        ring.append((ELYT_X, y, ELYT_ZB))          # flat underside, inward
        sections.append(ring)
    ob = bkit.loft(name, sections, mat=mat)
    F.orient_outward(ob)
    bpy.context.view_layer.update()
    return ob


def build():
    shell = bkit.pbr("BeetleShell", base=(0.11, 0.06, 0.03), rough=0.26,
                     coat=0.4)
    seam = bkit.pbr("BeetleSeam", base=(0.05, 0.03, 0.02), rough=0.40)
    legm = bkit.pbr("BeetleLeg", base=(0.08, 0.05, 0.03), rough=0.40)
    eye = bkit.pbr("BeetleEye", base=(0.02, 0.015, 0.01), rough=0.06)

    F.tube("Pronotum", PRONOTUM, PRONOTUM_RAD, shell, n=2.4, steps=18)
    F.tube("Head", HEAD, HEAD_RAD, shell, n=2.6, steps=16)

    # ---- the two elytra: mirrored domes with a real suture gap, so the
    # shell reads as a beetle's split wing cases rather than one smooth dome.
    # The suture is darkened ON the shells rather than by a separate ridge
    # block: a block spanning x=0 has no fixed height, so it pokes above the
    # shell at the tail and vanishes inside it at the shoulders -- the same
    # detached-part failure this model is being fixed for.
    ely = _elytron("ElytronL", shell)
    F.mirror_copy(ely, "ElytronR")
    for side in ("ElytronL", "ElytronR"):
        bkit.assign_faces_by(bpy.data.objects[side], seam,
                             lambda c, n: abs(c.x) / bkit.MM < 0.8)

    leg = F.tube("Leg0", [(p[0], p[1] + 2.0, p[2] + 7.0) for p in LEG],
                 LEG_RAD, legm, n=2.2, steps=12)
    bkit.array_radial(leg, SPEC["leg_count"], centre=HUB)

    # ---- the stag beetle's jaws: longer than the head, curved, with an inner
    # tine. Built from a swept taper, not a box.
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.tube("Mandible%s" % side,
               [(sx * p[0], p[1], p[2]) for p in MANDIBLE],
               MANDIBLE_RAD, shell, n=2.4, steps=14)
        F.cone_between("MandibleTine%s" % side,
                       (sx * 5.2, -24.0, 5.5), (sx * 3.4, -28.0, 5.0),
                       1.0, 0.2, seg=8, mat=shell)
        F.sphere("Eye%s" % side, 1.0, (sx * 3.4, -13.2, 7.9), eye,
                 segments=14, rings=8)

        # ---- elbowed antenna with a three-segment club
        F.tube("AntennaScape%s" % side,
               [(sx * 2.6, -15.0, 7.6), (sx * 5.4, -17.6, 8.8)],
               [(0.55, 0.5), (0.45, 0.4)], legm, n=2.2, steps=10)
        for j in range(3):
            t0 = j / 3.0
            t1 = (j + 1) / 3.0
            a0 = (sx * (5.4 + 5.2 * t0), -17.6 - 4.0 * t0, 8.8 + 0.6 * t0)
            a1 = (sx * (5.4 + 5.2 * t1), -17.6 - 4.0 * t1, 8.8 + 0.6 * t1)
            F.cone_between("Club%s%d" % (side, j), a0, a1, 0.8, 1.1,
                           seg=8, mat=shell)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=32)


CHECKS = [
    dict(name="overall_length", mm=46.5, tol=2.5, how="bbox_y"),
    dict(name="elytron_width", mm=6.2, tol=0.8, how="bbox_x", part="ElytronL"),
    dict(name="elytra_length", mm=21.0, tol=2.0, how="bbox_y", part="ElytronL"),
    dict(name="pronotum_length", mm=6.0, tol=1.0, how="bbox_y",
         part="Pronotum"),
    dict(name="mandible_length", mm=14.4, tol=2.0, how="bbox_y",
         part="MandibleL"),
]