"""
bearing -- 6202 deep-groove ball bearing: 15 mm bore, 35 mm OD, 11 mm wide.

The ISO 15 series is what makes this instantly recognisable: for a given bore
the OD grows with the series number, and 6202 (the general-purpose 02 series)
is 35 x 11. Bore and OD are therefore genuinely 2 : 4.7 rather than a plausible
looking guess, and both raceway grooves are cut in the profile instead of being
suggested by a shading trick.

Each ball is a separate watertight solid on the pitch circle, which is what
lets CHECKS measure a ball's diameter directly instead of guessing at it from
the assembly bounding box.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BORE = 15.0             # d
OUTSIDE_D = 35.0        # D
WIDTH = 11.0            # B
BALL_D = 6.0            # ball diameter
BALL_COUNT = 8
PITCH_R = 12.0          # pitch-circle radius of the ball set
GROOVE_HALF = 2.6       # half-depth of the raceway groove in each ring

SPEC = dict(bore_diameter=BORE,
            outside_diameter=OUTSIDE_D,
            width=WIDTH,
            ball_diameter=BALL_D,
            ball_count=BALL_COUNT)


def ring(name, r_inner, r_outer, width, groove_at_inner, mat):
    """Closed cross-section: flat faces, chamfered corners, raceway groove.

    `groove_at_inner` puts the raceway on the inner face (outer ring) or the
    outer face (inner ring), which is the only thing that differs between them.
    """
    h = width / 2.0
    g = min(GROOVE_HALF, (r_outer - r_inner) * 0.45)
    profile = [(r_inner, -h), (r_outer, -h), (r_outer, h),
               (r_inner, h)]
    if groove_at_inner:
        profile += [(r_inner, h - g), (r_inner + g * 0.9, 0.0),
                    (r_inner, -h + g)]
    else:
        profile += [(r_outer, h - g), (r_outer - g * 0.9, 0.0),
                    (r_outer, -h + g)]
    profile.append((r_inner, -h))          # close the loop
    return bkit.lathe(name, profile, segments=96, cap_ends=False, mat=mat)


def build():
    steel = bkit.pbr("BearingSteel", base=(0.80, 0.81, 0.84), metal=0.78,
                     rough=0.18)
    chrome = bkit.pbr("BearingChrome", base=(0.88, 0.89, 0.92), metal=0.82,
                      rough=0.10)

    outer = ring("OuterRing", OUTSIDE_D / 2.0 - 2.4, OUTSIDE_D / 2.0, WIDTH,
                 True, steel)
    inner = ring("InnerRing", BORE / 2.0, BORE / 2.0 + 2.4, WIDTH, False, steel)

    # Ball centres on the pitch circle, spaced by a computed step angle.
    step = 2.0 * math.pi / BALL_COUNT
    for i in range(BALL_COUNT):
        a = i * step
        bkit.uv_sphere("Ball%02d" % i, BALL_D / 2.0, segments=32, rings=16,
                       centre=(PITCH_R * math.cos(a), PITCH_R * math.sin(a), 0.0),
                       mat=chrome)
    return dict(spec=SPEC, parts=2 + BALL_COUNT)


CHECKS = [
    dict(name="outside_diameter", mm=35.0, tol=0.05, how="bbox_x", part="OuterRing"),
    dict(name="bearing_width", mm=11.0, tol=0.05, how="bbox_z", part="OuterRing"),
    dict(name="inner_ring_od", mm=19.8, tol=0.05, how="bbox_x", part="InnerRing"),
    dict(name="ball_diameter", mm=6.0, tol=0.05, how="bbox_x", part="Ball00"),
]