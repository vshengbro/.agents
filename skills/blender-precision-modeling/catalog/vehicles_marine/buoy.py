"""
buoy -- 1.18 m pillar navigation buoy, 1180 tall x 620 wide.

A cardinal mark is three stacked systems and the render reads them in that
order: a 560 mm body with a flared skirt and a lifting shackle, a four-leg
lantern cage carrying the light, and the topmark -- a single black cone -- above
it. The cone is the point of the object: a topmark is how a mariner identifies
a mark at night, so it stands 200 mm clear of the lantern and nothing else on
the buoy is cone-shaped. The waterline band is a second material on the one
revolved body, not a second object -- a shell around a shell z-fights.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    height=1180.0,
    body_diameter=560.0,
    body_height=640.0,
    cage_height=240.0,
    light_diameter=180.0,
    topmark_height=160.0,
    mooring_eye_diameter=110.0,
)

CHECKS = [
    dict(name="height", mm=1180.0, tol=4.0, how="bbox_z", part=None),
    dict(name="body_diameter", mm=560.0, tol=3.0, how="diameter",
         part="BuoyBody"),
    dict(name="body_height", mm=640.0, tol=3.0, how="bbox_z", part="BuoyBody"),
    dict(name="topmark_height", mm=160.0, tol=3.0, how="bbox_z",
         part="BuoyTopmark"),
    dict(name="mooring_eye", mm=110.0, tol=3.0, how="diameter",
         part="BuoyMooringEye"),
]

# (radius, height) of the revolved body: flared skirt, parallel middle, domed
# shoulder. Revolved rather than lofted because every station is circular.
BODY_PROFILE = [
    (0.0, 0.0),
    (250.0, 0.0),
    (280.0, 40.0),
    (280.0, 470.0),
    (258.0, 580.0),
    (196.0, 640.0),
    (0.0, 640.0),
]

CAGE_R = 212.0          # leg circle radius: the square's corner, 150*sqrt(2)
CAGE_TOP_R = 130.0


def build():
    body_mat = bkit.pbr("BuoyBodyMat", base=(0.72, 0.06, 0.05), rough=0.34,
                        coat=0.3)
    black = bkit.pbr("BuoyBlack", base=(0.05, 0.05, 0.055), rough=0.42)
    steel = bkit.preset("brushed_metal")
    lens = bkit.pbr("BuoyLens", base=(0.90, 0.86, 0.62), rough=0.08,
                    transmission=0.5, emission=(0.95, 0.88, 0.55),
                    emission_strength=2.0)
    mark = bkit.pbr("BuoyTopmarkMat", base=(0.04, 0.30, 0.08), rough=0.30)

    body = bkit.lathe("BuoyBody", BODY_PROFILE, segments=56, mat=body_mat)
    # waterline band as a second material on the one solid
    bkit.assign_faces_by(body, black,
                         lambda c, n: 230.0 <= c.z / bkit.MM <= 360.0)

    bkit.torus("BuoyMooringEye", 40.0, 15.0, seg_major=36, seg_minor=14,
               centre=(0.0, 276.0, 210.0), axis="Y", mat=steel)
    bkit.rounded_box("BuoyEyePad", 150.0, 40.0, 150.0, r=30.0, segments=2,
                     centre=(0.0, 268.0, 210.0), mat=steel)

    # lantern cage: four legs on a 212 mm circle, drawn in by 62 mm at the top
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=300.0,
                                                   pitch_y=300.0)):
        V.strut("BuoyCageLeg%d" % i, (x, y, 600.0),
                (x * CAGE_TOP_R / CAGE_R, y * CAGE_TOP_R / CAGE_R, 880.0),
                17.0, steel, 10)
    bkit.torus("BuoyCageHoop", CAGE_TOP_R - 17.0, 12.0, seg_major=40,
               seg_minor=10, centre=(0.0, 0.0, 880.0), axis="Z", mat=steel)
    bkit.lathe("BuoyLanternBase", [(0.0, 876.0), (110.0, 876.0),
                                   (110.0, 920.0), (0.0, 920.0)],
               segments=32, mat=black)
    bkit.lathe("BuoyLight", [(0.0, 920.0), (90.0, 920.0), (90.0, 1020.0),
                             (0.0, 1020.0)], segments=32, mat=lens)

    # topmark: one cone, 180 mm of it, standing clear of the lantern
    bkit.lathe("BuoyTopmark", [(90.0, 1020.0), (90.0, 1050.0), (0.0, 1180.0)],
               segments=32, mat=mark)

    return dict(spec=SPEC, parts=9)
