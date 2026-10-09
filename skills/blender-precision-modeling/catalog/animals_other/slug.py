"""slug -- a 55 mm land slug: the shell-less body, the broad muscular foot, the
mantle shield behind the head, two eyestalks, and the pneumostome (breathing
hole) on the mantle.

A slug IS a snail without the shell, so the diagnostic parts are the mantle
shield over the shoulders and the retracted eyestalks. A smooth featureless
tube reads as a worm; the mantle hump is what makes it a slug.

Construction: one swept body along a real resting curve, a broad flat foot
underneath, a mantle shield, two eyestalks, and the pneumostome as a small
ring. Nothing is booleaned.

Orientation: the head reaches toward -Y, X lateral, Z up.
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
    overall_length=45.0,
    back_width=49.0,
    body_height=13.5,
    mantle_length=20.7,
    eyestalk_length=9.3,
)

# the resting curve: slugs do not lie straight, they meander
BACK = [(-22.0, 0.0, 6.4), (-14.0, 0.0, 8.6), (-6.0, 0.4, 9.6),
        (2.0, 0.8, 9.4), (10.0, 1.0, 8.6), (18.0, 0.8, 7.4),
        (26.0, 0.4, 6.4)]
BACK_RAD = [(4.2, 3.6), (7.6, 6.4), (8.0, 7.2), (7.4, 6.4), (6.0, 5.0),
            (4.2, 3.6), (1.8, 1.6)]
FOOT = [(-24.0, 0.0, 2.6), (-12.0, 0.1, 2.4), (2.0, 0.5, 2.4),
        (14.0, 0.7, 2.4), (26.0, 0.4, 2.6)]
FOOT_RAD = [(5.4, 2.6), (8.2, 2.6), (8.2, 2.6), (6.4, 2.6), (3.0, 2.4)]
# the mantle: the shield over the shoulders, where the shell used to be
MANTLE = [(0.0, -9.0, 12.0), (0.0, -3.0, 13.4), (0.0, 3.0, 12.8),
          (0.0, 9.0, 10.6)]
MANTLE_RAD = [(4.6, 5.2), (8.2, 6.6), (7.8, 6.0), (4.0, 4.4)]
HEAD = [(0.0, -21.0, 6.2), (0.0, -25.0, 6.6), (0.0, -28.5, 6.2)]
HEAD_RAD = [(3.6, 3.0), (4.4, 3.6), (3.0, 2.6)]


def build():
    skin = bkit.pbr("SlugSkin", base=(0.52, 0.44, 0.34), rough=0.44,
                    coat=0.2)
    dark = bkit.pbr("SlugDark", base=(0.30, 0.25, 0.19), rough=0.48)
    pale = bkit.pbr("SlugPale", base=(0.70, 0.62, 0.50), rough=0.50)
    eye = bkit.pbr("SlugEye", base=(0.02, 0.02, 0.02), rough=0.08)

    F.tube("Back", BACK, BACK_RAD, skin, n=2.4, steps=20)
    F.tube("Foot", FOOT, FOOT_RAD, dark, n=3.0, steps=18)
    F.tube("Mantle", MANTLE, MANTLE_RAD, skin, n=2.4, steps=18)
    F.tube("Head", HEAD, HEAD_RAD, skin, n=2.4, steps=16)

    # ---- the pneumostome: the breathing hole on the right side of the mantle
    bkit.torus("Pneumostome", 1.6, 0.5, seg_major=18, seg_minor=8,
               centre=(7.6, -1.0, 12.4), axis="X", mat=dark)

    # ---- two eyestalks, the slugs' most recognisable feature
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.tube("Eyestalk%s" % side,
               [(sx * 2.4, -25.0, 8.4), (sx * 4.0, -29.0, 12.0),
                (sx * 5.0, -32.0, 15.0)],
               [(2.0, 2.0), (1.5, 1.5), (1.1, 1.1)], skin, n=2.2, steps=10)
        F.sphere("Eye%s" % side, 1.6,
                 (sx * 5.2, -32.4, 15.4), eye, segments=16, rings=8)
        # the two feeler-like lip tentacles, much shorter
        F.cone_between("LipTentacle%s" % side,
                       (sx * 3.0, -27.0, 5.4), (sx * 4.2, -31.0, 4.6),
                       1.1, 0.3, seg=8, mat=pale)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="overall_length", mm=44.5, tol=4.0, how="bbox_y"),
    dict(name="back_width", mm=49.0, tol=4.0, how="bbox_x", part="Back"),
    dict(name="body_height", mm=13.5, tol=2.5, how="bbox_z", part="Mantle"),
    dict(name="mantle_length", mm=20.7, tol=2.5, how="bbox_y", part="Mantle"),
    dict(name="eyestalk_length", mm=9.3, tol=2.5, how="longest",
         part="EyestalkL"),
]