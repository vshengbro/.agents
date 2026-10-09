"""
drum -- 200 litre steel drum: a straight cylindrical body with two rolled
hoops, top and bottom chimes, and a bung on the lid.

A closed drum is a solid of revolution with *both* ends on the axis, so the
profile never comes back down an inside wall: axis -> base -> hoops -> rim ->
across the lid -> axis. That is watertight without inventing a cavity nobody
can see, and the chimes are what stop it reading as a plain cylinder.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    diameter=572.0,           # over the chimes
    body_diameter=572.0,
    height=880.0,             # standard 200 L / 55 gallon drum
    wall=1.6,
    hoop_diameter=600.0,      # the two rolling hoops stand proud
    chime_diameter=592.0,
    bung_diameter=44.0,
    volume_l=200.0,
)

R = SPEC["body_diameter"] / 2.0
H = SPEC["height"]
HOOP = SPEC["hoop_diameter"] / 2.0
CHIME = SPEC["chime_diameter"] / 2.0


def build():
    steel = bkit.pbr("DrumSteel", base=(0.55, 0.57, 0.60), metal=0.45, rough=0.34)
    # The lid and chimes face the camera with nothing bright to reflect, so at
    # full metalness they mirror the dark backdrop and render as black holes.
    # Backing off metalness keeps them reading as painted steel.
    steel_dark = bkit.pbr("DrumSteelDark", base=(0.42, 0.44, 0.47), metal=0.35,
                          rough=0.42)
    paint = bkit.pbr("DrumPaint", base=(0.16, 0.34, 0.46), metal=0.20, rough=0.38)
    bung = bkit.pbr("DrumBung", base=(0.66, 0.68, 0.70), metal=0.55, rough=0.30)

    # Hoop positions are symmetric about the drum's mid-height, so they are
    # computed from H rather than typed: a typed constant drifts the moment the
    # height changes and the drum stops looking like a drum.
    hoop_h = (HOOP - R)
    z1 = H * 0.135
    z2 = H * 0.315

    prof = [
        (0.0, 0.0),                     # centre of the base
        (240.0, 0.0),
        (266.0, 4.0),
        (CHIME - 2.0, 12.0),            # bottom chime
        (CHIME, 18.0),
        (CHIME, z1 - 30.0),
        (R, z1 - 26.0),                 # step in off the chime
        (R, z1 - 22.0),
        (HOOP, z1 - 18.0),              # first rolling hoop
        (HOOP, z1 + 26.0),
        (R, z1 + 30.0),
        (R, z2 - 30.0),
        (HOOP, z2 - 26.0),              # second rolling hoop
        (HOOP, z2 + 26.0),
        (R, z2 + 30.0),
        (R, H - 42.0),
        (CHIME, H - 34.0),              # top chime
        (CHIME, H - 10.0),
        (CHIME - 12.0, H - 3.0),
        (268.0, H),                     # rolled rim
        (240.0, H),                     # across the lid
        (0.0, H - 1.5),                 # dished lid, back to the axis
    ]
    body = bkit.lathe("DrumBody", prof, segments=96, mat=steel)

    # Painted body between the hoops; bare steel on the chimes and lid, which is
    # exactly how a real drum is finished and keeps the silhouette readable.
    bkit.assign_faces_by(
        body, paint,
        lambda c, n: z1 + 32.0 < c.z / bkit.MM < z2 - 32.0,
    )
    bkit.assign_faces_by(
        body, steel_dark,
        lambda c, n: (c.z / bkit.MM) > H - 44.0,
    )

    # ---- bung in the top lid ------------------------------------------------
    b = SPEC["bung_diameter"] / 2.0
    bung_prof = [
        (0.0, 0.0), (b - 2.0, 0.0), (b, 2.0), (b, 7.0),
        (b - 3.0, 9.0), (0.0, 9.0),
    ]
    bung_obj = bkit.lathe("DrumBung", bung_prof, segments=48,
                          centre=(140.0, 0.0, H - 3.0), mat=bung)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="diameter", mm=600.0, tol=0.5, how="diameter", part="DrumBody"),
    dict(name="height", mm=880.0, tol=1.0, how="bbox_z", part="DrumBody"),
    dict(name="longest", mm=886.0, tol=2.0, how="longest"),
]
