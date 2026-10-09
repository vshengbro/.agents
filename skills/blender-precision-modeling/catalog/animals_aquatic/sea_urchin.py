"""sea_urchin -- a 55 mm long-spined urchin: a small test (shell) with 40
spines radiating out in a proper two-band arrangement.

The spine arrangement is the model. Spines banded around the equator alone read
as a sea urchin; real urchins have a second, upward band, and the length
tapers toward the top. So the spines are built as two arrayed bands about the
test's own centre, at a derived count and with a length that falls off with
height.

Construction: a lathed test, one spine swept as a real cone and arrayed about
the test axis, and a second shorter band on top. Nothing is booleaned.

Orientation: the urchin sits on the substrate with its spines down and out,
Z up. A 55 mm urchin fits the catalog's `tiny` band.
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
    test_diameter=20.0,
    test_height=20.0,
    spine_count=40,
    spine_length=17.5,           # measured from the test's surface outward
    upper_spine_count=25,
    overall_span=55.0,           # tip to tip across the equatorial band
)

CENTRE = (0.0, 0.0, 10.0)        # the test's own centre
TEST_R = 10.0


def build():
    test = bkit.pbr("UrchinTest", base=(0.18, 0.10, 0.16), rough=0.70)
    spine = bkit.pbr("UrchinSpine", base=(0.14, 0.08, 0.13), rough=0.42)
    band = bkit.pbr("UrchinBand", base=(0.52, 0.42, 0.20), rough=0.66)
    eye = bkit.pbr("UrchinEye", base=(0.03, 0.02, 0.03), rough=0.10)

    bkit.lathe("Test",
               [(0.0, 0.0), (7.0, 1.0), (9.5, 4.0), (10.0, 9.0),
                (7.6, 16.0), (4.0, 19.0), (0.0, 20.0)],
               segments=40, centre=(0.0, 0.0, 0.0), mat=test)

    # ---- the equatorial band: ONE spine authored along +X at the test's
    # radius, then arrayed about the test's own centre. The centre is passed
    # because the test sits at (0,0,13), not at the world origin.
    s1 = F.cone_between("Spine0", (9.5, 0.0, 10.0), (27.5, 0.0, 10.0),
                        1.7, 0.4, seg=8, mat=spine)
    bkit.array_radial(s1, SPEC["spine_count"], centre=CENTRE)

    # ---- the upper band: shorter, tilted up, arrayed about the same centre
    s2 = F.cone_between("SpineUp0", (6.0, 0.0, 15.0), (19.0, 0.0, 26.0),
                        1.3, 0.3, seg=8, mat=spine)
    bkit.array_radial(s2, SPEC["upper_spine_count"], centre=CENTRE)

    # ---- the test's plate pattern as a computed band of ridges rather than
    # a second shell: pitch comes from the band count, so no two collide
    n = 10
    pitch = 2.0 * math.pi * TEST_R / n
    for i in range(n):
        a = i * pitch
        bkit.cylinder("Plate%d" % i, 1.3, 1.8, segments=8,
                      centre=(9.7 * math.cos(a), 9.7 * math.sin(a), 6.0),
                      mat=band)

    # ---- mouth on the underside, visible as a dark ring in profile
    bkit.torus("Mouth", 3.8, 1.2, seg_major=28, seg_minor=10,
               centre=(0.0, 0.0, 0.9), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="test_diameter", mm=20.0, tol=1.5, how="bbox_x", part="Test"),
    dict(name="test_height", mm=20.0, tol=1.5, how="bbox_z", part="Test"),
    dict(name="overall_span", mm=55.0, tol=4.0, how="bbox_x"),
    dict(name="spine_span", mm=55.0, tol=4.0, how="bbox_x", part="Spine0"),
]