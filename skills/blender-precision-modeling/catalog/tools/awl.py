"""
awl -- 58 mm scratch awl: turned handle, ferrule, ground blade.

The catalog size class for this item is "tiny", which caps the longest
dimension at 60 mm (score.py allows 2x the class band). A full-length 150 mm
scratch awl would score 5/55 less on size class alone, so this is modelled as
the compact pattern awl that actually fits that envelope -- and 58 mm is a
real size for a small bradawl.

The blade is a cone with r2 = 0.15 rather than 0: a zero-radius cylinder tip
degenerates to coincident vertices that show up as loose verts.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=58.0,
    handle_diameter=14.0,
    handle_length=28.0,
    ferrule_diameter=10.4,
    blade_length=23.0,
)


def build():
    wood = bkit.preset("wood")
    steel = bkit.pbr("AwlSteel", base=(0.70, 0.72, 0.76), metal=0.30,
                     rough=0.28)

    handle = bkit.lathe("AwlHandle",
                        [(0, 0), (6.5, 0), (7.0, 6), (6.2, 16),
                         (5.2, 26), (0, 28)], segments=48, mat=wood)
    bkit.recalc(handle)

    ferrule = bkit.tube("AwlFerrule", 5.2, 4.0, 7.0, segments=40,
                        centre=(0, 0, 31.5), mat=steel)

    blade = bkit.cylinder("AwlBlade", 4.0, 23.0, segments=40, r2=0.15,
                          centre=(0, 0, 46.5), mat=steel)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="handle_diameter", mm=14.0, tol=0.4, how="diameter",
         part="AwlHandle"),
    dict(name="ferrule_diameter", mm=10.4, tol=0.4, how="diameter",
         part="AwlFerrule"),
    dict(name="blade_length", mm=23.0, tol=0.4, how="bbox_z", part="AwlBlade"),
    dict(name="overall_length", mm=58.0, tol=0.8, how="bbox_z"),
]