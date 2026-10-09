"""
can -- 330 ml slim drinks can: a lathed aluminium body with the two necked-in
ends a modern drawn can actually has, and a pull tab riveted to the lid.

A drinks can is a *closed* vessel, so the profile ends on the axis rather than
coming back down the inside: base centre -> out along the base -> up the body
-> in over the top seam -> across the lid -> back to the axis. That is one
watertight solid of revolution, and unlike an open profile it has no hole for
the camera to see down.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    diameter=66.0,            # body diameter, outside
    height=115.0,             # base to the top of the end seam
    neck_diameter=57.2,       # the necked-in top end
    base_diameter=55.0,
    tab_diameter=16.0,
    volume_ml=330.0,
)

R = SPEC["diameter"] / 2.0
H = SPEC["height"]
TOP = SPEC["neck_diameter"] / 2.0


def build():
    alu = bkit.pbr("CanAlu", base=(0.78, 0.79, 0.81), metal=0.75, rough=0.24)
    paint = bkit.pbr("CanLivery", base=(0.10, 0.32, 0.62), metal=0.30, rough=0.26)
    # The lid is bare aluminium. At metal=1.0 it mirrors the dark backdrop and
    # renders black, so the lid keeps a diffuse component to catch the key.
    bare = bkit.pbr("CanBareAlu", base=(0.82, 0.83, 0.85), metal=0.35, rough=0.28)

    # ---- one closed cross-section, both ends on the axis --------------------
    prof = [
        (0.0, 0.0),                  # centre of the underside
        (24.0, 0.0),                 # across the base
        (29.5, 2.0),                 # bottom taper out
        (31.8, 5.0),
        (R, 8.0),                    # full body radius
        (R, 30.0),
        (R, 100.0),
        (31.4, 106.0),               # taper in toward the neck
        (TOP + 0.6, 110.0),
        (TOP, 112.5),
        (TOP - 0.4, 114.2),          # the rolled end seam
        (26.0, H),                   # across the seam onto the lid
        (14.0, H - 0.35),            # the lid is dished very slightly
        (0.0, H - 0.7),              # lid centre, back on the axis
    ]
    body = bkit.lathe("CanBody", prof, segments=96, mat=alu)

    # The livery wraps the straight body only; the base, seam and lid stay bare
    # aluminium, which is what stops a can reading as one flat plastic tone.
    bkit.assign_faces_by(
        body, paint,
        lambda c, n: 9.5 < c.z / bkit.MM < 99.0,
    )
    bkit.assign_faces_by(
        body, bare,
        lambda c, n: c.z / bkit.MM >= 99.0,
    )

    # ---- pull tab ring, half embedded in the lid ---------------------------
    tab = bkit.torus("CanPullTab", 6.0, 1.2, seg_major=40, seg_minor=16,
                     centre=(0.0, 0.0, H - 1.6), mat=bare)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="diameter", mm=66.0, tol=0.4, how="diameter", part="CanBody"),
    dict(name="height", mm=115.0, tol=0.4, how="bbox_z", part="CanBody"),
    dict(name="longest", mm=115.0, tol=0.4, how="longest"),
]
