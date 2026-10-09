"""
spinning_top -- a 52 mm wooden spinning top: turned profile, painted bands,
real metal tip.

A spinning top is a solid of REVOLUTION, so it is a single lathe whose profile
is the turned shape: a small flat tip, a concave sweep out to the fat shoulder,
a rounded crown, and then a tapered stem. Writing the profile from the axis out
along the bottom, up the flank, over the shoulder and in along the top is what
gives the top its silhouette; a stack of cylinders does not.

Two details sell it. The tip is a separate hardened-steel pin, because a
wooden top that touches the floor on wood looks unfinished. And the painted
bands are a second MATERIAL on the one solid, selected by radius and height --
a stack of thin coloured rings would z-fight and double the non-manifold count.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    overall_height=52.0,
    max_diameter=34.0,       # widest point, at the shoulder
    tip_diameter=2.4,        # the hardened steel point
    tip_height=5.0,
    shoulder_height=28.0,    # where the profile is widest
    body_height=40.0,        # turned body below the stem
    stem_diameter=9.0,
    stem_height=12.0,
    band_count=3,
)

H = SPEC["overall_height"]
R = SPEC["max_diameter"] / 2.0
TIP_R = SPEC["tip_diameter"] / 2.0
TIP_H = SPEC["tip_height"]
SH_H = SPEC["shoulder_height"]
STEM_R = SPEC["stem_diameter"] / 2.0
STEM_H = SPEC["stem_height"]


def build():
    wood = bkit.pbr("TopWood", base=(0.72, 0.55, 0.28), rough=0.30, coat=0.35)
    red = bkit.preset("red_paint")
    cream = bkit.preset("white_plastic")
    blue = bkit.preset("blue_paint")
    steel = bkit.preset("polished_metal")

    # ---- the turned body. Radius as a function of height, walked from the
    # axis at the bottom of the tip, out along the concave flank, over the
    # shoulder, and in to the axis at the top of the crown. Every radius below
    # is <= R, because R *is* the widest radius on a real top -- a profile
    # that overshoots it makes the declared max_diameter a lie.
    body_top = H - STEM_H
    prof = [
        (0.0, 0.0),
        (TIP_R + 0.4, 0.2),
        (TIP_R + 1.0, 2.4),
        (3.6, 5.0),
        (6.4, 8.4),
        (9.6, 12.4),
        (12.6, 16.6),
        (15.2, 21.0),
        (R - 1.0, SH_H - 3.0),
        (R, SH_H),                     # the widest point: the shoulder
        (R - 0.7, SH_H + 1.8),
        (13.0, SH_H + 3.4),
        (9.0, SH_H + 4.4),
        (5.0, body_top - 0.6),
        (0.0, body_top),
    ]
    body = bkit.lathe("TopBody", prof, segments=64, mat=wood)
    bkit.recalc(body)
    bkit.shade_smooth(body, 30)

    # ---- painted bands. The bands are balanced across the VISIBLE height,
    # not the profile height: the lower cone is what the camera sees in
    # silhouette, so a band that only covers the top of the shoulder reads as
    # an all-blue top with a stripe of something else near the tip.
    bkit.assign_faces_by(body, red,
                         lambda c, n: 0.0 <= c.z / bkit.MM < 17.0)
    bkit.assign_faces_by(body, cream,
                         lambda c, n: 17.0 <= c.z / bkit.MM < 25.0)
    bkit.assign_faces_by(body, blue,
                         lambda c, n: c.z / bkit.MM >= 25.0)

    # ---- the hardened steel tip: a real pin, seated 1.2 mm up into the
    # turned body so the two solids overlap instead of meeting on a face. Its
    # bottom face is exactly at z=0, so the top's 52 mm is its real height
    # rather than 52.6 mm of which 0.6 mm is buried in the table.
    bkit.cylinder("TopTip", TIP_R, TIP_H + 1.2, segments=20,
                  centre=(0.0, 0.0, (TIP_H + 1.2) / 2.0), mat=steel)

    # ---- the stem you hold between finger and thumb
    bkit.cylinder("TopStem", STEM_R, STEM_H, segments=28, r2=STEM_R * 0.72,
                  centre=(0.0, 0.0, H - STEM_H / 2.0), mat=wood)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="overall_height", mm=52.0, tol=0.4, how="bbox_z"),
    dict(name="max_diameter", mm=34.0, tol=0.4, how="diameter", part="TopBody"),
    dict(name="tip_diameter", mm=2.4, tol=0.15, how="diameter", part="TopTip"),
    dict(name="body_height", mm=40.0, tol=0.4, how="bbox_z", part="TopBody"),
    dict(name="stem_height", mm=12.0, tol=0.4, how="bbox_z", part="TopStem"),
    dict(name="stem_diameter", mm=9.0, tol=0.3, how="diameter", part="TopStem"),
]
