"""lizard -- a 58 mm anole: a flattened body, four splayed legs with the elbows
out, a long tapering tail over half the animal's length, and a dorsal crest.

Proportion is the cue. A lizard's tail is longer than its head-and-body, its
belly is flat against the substrate with the legs splayed sideways, and the
head is a wedge rather than a rounded skull.

Construction: one lofted body from a proportion table, four legs each authored
once and mirrored, a tail swept along the body axis, and the dorsal crest as a
thin blade plus a dewlap flap at the throat. Nothing is booleaned.

Orientation: nose at -Y, X lateral, Z up, so side.png shows the full profile.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    overall_length=58.0,
    body_length=27.0,
    body_depth=9.0,
    body_width=8.0,
    tail_length=31.0,
    leg_span=22.0,
    head_length=8.0,
)

# (y, half_height, half_width, z_centre) -- snout -29, hips +2
BODY = [
    (-29.0, 1.2, 1.0, 4.0),
    (-27.0, 2.6, 2.2, 4.2),
    (-24.0, 3.4, 3.0, 4.4),
    (-20.0, 4.2, 3.8, 4.6),
    (-14.0, 4.5, 4.0, 4.6),
    (-7.0, 4.4, 3.9, 4.6),
    (0.0, 3.8, 3.4, 4.4),
    (2.0, 3.0, 2.6, 4.2),
]
FRONT_LEG = [(3.4, -8.0, 4.0), (5.6, -7.0, 3.0), (7.4, -8.4, 1.4),
             (8.4, -10.2, 0.5)]
FRONT_RAD = [(2.0, 1.8), (1.6, 1.5), (1.1, 1.0), (0.5, 0.5)]
HIND_LEG = [(3.4, -1.0, 4.2), (6.4, 0.6, 3.2), (9.0, 2.6, 1.4),
            (10.6, 4.4, 0.5)]
HIND_RAD = [(2.4, 2.2), (1.9, 1.8), (1.3, 1.2), (0.6, 0.6)]
TAIL = [(0.0, 2.0, 4.2), (0.0, 10.0, 4.0), (0.0, 18.0, 3.2),
        (0.0, 25.0, 2.2), (0.0, 29.0, 1.2)]
TAIL_RAD = [(2.6, 2.4), (2.0, 1.9), (1.4, 1.3), (0.8, 0.7), (0.35, 0.35)]
# the dorsal crest: a low sawtooth ridge along the back
CREST = [(-18.0, 9.0), (-14.0, 10.6), (-10.0, 10.0), (-6.0, 10.8),
         (-2.0, 10.0), (2.0, 8.6)]


def build():
    hide = bkit.pbr("LizardHide", base=(0.28, 0.36, 0.20), rough=0.52)
    belly = bkit.pbr("LizardBelly", base=(0.72, 0.72, 0.56), rough=0.56)
    crest = bkit.pbr("LizardCrest", base=(0.42, 0.52, 0.26), rough=0.50)
    eye = bkit.pbr("LizardEye", base=(0.02, 0.02, 0.025), rough=0.08)
    dewlap = bkit.pbr("LizardDewlap", base=(0.70, 0.26, 0.20), rough=0.44,
                      alpha=0.9)

    torso = F.body("Body", BODY, hide, n=2.6, steps=28)
    bkit.assign_faces_by(torso, belly, lambda c, n: c.z / bkit.MM < 4.0)

    F.tube("Tail", TAIL, TAIL_RAD, hide, n=2.2, steps=18)

    # the crest rides on the body's own dorsal line, so it follows the table
    F.plate_yz("Crest", CREST, 1.2, x=0.0, mat=crest)

    # four legs: front pair mirrored, hind pair mirrored
    for tag, path, rad in (("Front", FRONT_LEG, FRONT_RAD),
                           ("Hind", HIND_LEG, HIND_RAD)):
        leg = F.tube("Leg%sL" % tag, path, rad, hide, n=2.2, steps=14)
        F.mirror_copy(leg, "Leg%sR" % tag)

    # ---- the dewlap: the throat fan an anole drops, a thin blade under the
    # head rather than a second shell
    F.plate_yz("Dewlap", [(-24.0, 4.0), (-20.0, 0.8), (-14.0, 3.6),
                          (-20.0, 5.0)], 1.0, x=0.0, mat=dewlap)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 1.7, segments=14, rings=8,
                       centre=(sx * 2.6, -25.4, 5.4), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="overall_length", mm=58.0, tol=2.0, how="bbox_y"),
    dict(name="body_length", mm=31.0, tol=2.0, how="bbox_y", part="Body"),
    dict(name="body_depth", mm=9.0, tol=1.0, how="bbox_z", part="Body"),
    dict(name="body_width", mm=8.0, tol=1.0, how="bbox_x", part="Body"),
    dict(name="leg_span", mm=22.0, tol=3.0, how="bbox_x"),
]