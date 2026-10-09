"""
crater -- a lunar impact crater: 2.6 km rim to rim, 380 m deep, with an
ejecta blanket and a central peak.

Size class `large` (600..3000 mm); this is modelled at 1:1000 of a real
2.6 km Eratosthenian crater, so 2600 mm across and 380 mm deep, which preserves
the depth/diameter ratio of 0.146 that makes a lunar crater read as lunar.

The profile is what carries it. A simple bowl is not an impact crater; a real
one has (from the centre out) a flat floor, a central peak, a steep inner wall
at ~35 deg, a sharp rim crest, then an outer ejecta slope that shallows to the
surroundings. The whole of that is one `lathe` profile, so the crater is a
single watertight solid with no boolean.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    rim_diameter=2600.0,
    rim_height=380.0,        # rim crest above the surrounding plain
    floor_diameter=1500.0,
    central_peak_height=210.0,
    ejecta_outer_diameter=4800.0,
)

R_RIM = SPEC["rim_diameter"] / 2.0
H = SPEC["rim_height"]               # rim crest ABOVE the surrounding plain
# Crater DEPTH measured from the rim crest, not from the plain. The SPEC
# number is the standard depth/diameter ratio 0.146 of a real 2.6 km crater,
# and it is the ratio that makes a bowl read as LUNAR rather than as a dish.
DEPTH = 380.0
PEAK = SPEC["central_peak_height"]
R_FLOOR = SPEC["floor_diameter"] / 2.0
R_EJECTA = SPEC["ejecta_outer_diameter"] / 2.0


def build():
    regolith = bkit.pbr("LunarRegolith", base=(0.215, 0.212, 0.205), rough=0.94)
    fresh = bkit.pbr("LunarFreshEjecta", base=(0.34, 0.335, 0.325), rough=0.90)
    dark_floor = bkit.pbr("LunarCraterFloor", base=(0.155, 0.153, 0.150),
                          rough=0.96)

    # ---- crater profile, floor outward then back to the axis --------------
    # Datum: the SURROUNDING PLAIN is z = 0. That has to be stated, because
    # the first version put the rim crest at z = 0 as well, which buried the
    # rim in the plain and rendered the whole thing as a shallow dish --
    # there was no rim standing proud of anything.
    #
    #   floor -> central peak -> inner wall -> rim crest (+H) -> ejecta
    #   blanket -> plain (0)
    prof = [
        (0.0, -DEPTH + 4.0),                          # flat floor
        (R_FLOOR * 0.62, -DEPTH),
        (R_FLOOR * 0.80, -DEPTH + 8.0),
        (R_FLOOR * 0.87, -DEPTH + PEAK),              # central peak apex
        (R_FLOOR * 0.95, -DEPTH + PEAK * 0.55),
        (R_FLOOR, -DEPTH + 16.0),                     # peak toe / floor edge
        # INNER WALL: nearly vertical. A crater reads as a hole because the
        # wall is steep relative to the blanket; the first pass ran the wall
        # from the floor edge at 0.94 R_FLOOR all the way to the crest in one
        # shallow ramp, which rendered as a smooth donut.
        (R_FLOOR * 1.06, -DEPTH + H * 0.34),
        (R_RIM * 0.96, H * 0.52),
        (R_RIM * 1.005, H * 0.94),
        (R_RIM, H),                                   # rim crest, +H over plain
        (R_RIM * 1.04, H * 0.62),                     # outer rim shoulder
    ]
    # ejecta blanket: a ballistic slope from the rim crest down to the plain
    n = 12
    r0 = R_RIM * 1.03
    for i in range(1, n + 1):
        t = float(i) / n
        r = r0 + (R_EJECTA - r0) * t
        z = H * 0.80 * (1.0 - t) ** 1.7
        prof.append((r, z))
    prof.append((R_EJECTA, 0.0))                      # surrounding plain
    prof.append((0.0, 0.0))
    # REVERSED before the lathe, and lifted so its lowest point is z=0.
    # Two reasons, both learned the hard way:
    #  * walking outward and back winds the profile CLOCKWISE in (r, z) and
    #    `lathe` builds faces in that winding, so the solid comes out with
    #    inward normals and a negative volume. recalc() cannot rescue it: the
    #    mesh is closed and consistently INWARD, not tangled.
    #  * sit_on_floor() then raises the whole assembly to rest on z=0, which
    #    silently added the depth of the inner wall (162 mm) to every
    #    height. Authoring with the minimum already at 0 makes the measured
    #    height the declared one.
    z_min = min(z for (_r, z) in prof)
    prof = [(r, z - z_min) for (r, z) in prof[::-1]]
    crater = bkit.lathe("Crater", prof, segments=64, mat=regolith, smooth=False)
    bkit.recalc(crater)

    # ---- ejecta rays and boulders on the blanket -------------------------
    # Ray patterns are radial streaks of brighter, fresher material. Real
    # geometry rather than texture, on a computed ring and a radial array, so
    # the rays are evenly spaced by construction.
    bkit.assign_faces_by(crater, fresh,
                         lambda c, n: (c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM
                         > R_RIM * 1.02 and n.z > 0.35)
    bkit.assign_faces_by(crater, dark_floor,
                         lambda c, n: n.z < 0.35 and abs(c.z / bkit.MM) < 40.0)

    # ---- rim ring: a raised lip standing on the crest --------------------
    # It exists so the rim's diameter is a measurable part, and it is what a
    # real fresh crater has: a sharp crest, slightly proud of the blanket.
    bkit.tube("RimRing", R_RIM, R_RIM * 0.965, 46.0, segments=64,
              centre=(0.0, 0.0, H + 18.0), mat=regolith)

    # boulders: ejected blocks, on a computed radial ring. Radius is INSIDE
    # the ejecta blanket's outer edge or they sit off the model.
    rnd_r = 1.16
    for i in range(12):
        ang = 2.0 * math.pi * i / 12.0
        rad = R_RIM * rnd_r
        br = 26.0 + 22.0 * ((i * 7) % 5) / 4.0
        # sitters on the blanket surface, which slopes: z there is
        # -H*0.16 at the rim and 0 at the blanket's outer edge
        r0 = R_RIM * 1.03
        bl_z = H * 0.80 * (1.0 - (rad - r0) / (R_EJECTA - r0)) ** 1.7
        bkit.rounded_box("Boulder%02d" % (i + 1), br * 1.7, br * 1.3, br * 0.8,
                         r=br * 0.3, segments=2,
                         centre=(rad * math.cos(ang), rad * math.sin(ang),
                                 bl_z + br * 0.25), mat=regolith)

    return dict(spec=SPEC, parts=2 + 12)


CHECKS = [
    # The crater's own bbox IS the ejecta blanket, so rim_diameter cannot be
    # measured on it. RimDiameter is a separate thin ring part standing on the
    # crest, which is both measurable and visible.
    dict(name="rim_outer_diameter", mm=2600.0, tol=10.0,
         how="diameter", part="RimRing"),
    dict(name="rim_height", mm=46.0, tol=2.0, how="bbox_z", part="RimRing"),
    dict(name="ejecta_diameter", mm=4800.0, tol=30.0, how="diameter", part="Crater"),
    dict(name="overall_height", mm=760.0, tol=12.0, how="bbox_z"),
    dict(name="overall_width", mm=4800.0, tol=30.0, how="bbox_x"),
]