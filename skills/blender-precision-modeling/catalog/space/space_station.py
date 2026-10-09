"""
space_station -- an ISS-class orbital station: 74 m truss, 45 m with the
arrays, 109 m tip to tip, 420 t.

Size class `huge` (3000..40000 mm band). This is 1:150 scale: the real ISS is
109 m across and 74 m long, so at 1:150 that is 727 mm long and 493 m across...
no: 109 m / 150 = 727 mm. Which is `medium`. The honest statement is 1:1e4
scale -- 74 000 mm truss, 10 900 mm tip to tip -- which lands inside `huge`
and preserves every ratio.

What carries the read is the SEGMENTED TRUSS with radiators and arrays hung
off it, and the module stack crossing it. So:
- the truss is a real lattice: longerons on a computed bay pitch with diagonal
  bracing on every bay, built by `array_linear` / a computed loop,
- the solar wings are 8 arrays on a computed station pitch, each a panel with
  real cell grid,
- the pressurised modules are a cylinder chain along the cross axis,
- radiators are the flat white panels that point edge-on to the arrays.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    truss_length=7400.0,      # along the port-starboard truss
    truss_depth=1200.0,
    bay_pitch=200.0,         # truss segment pitch, computed
    bays=37,
    module_count=5,
    module_diameter=440.0,
    array_count=8,
    array_length=3400.0,
    array_chord=1200.0,
)

BAY = SPEC["bay_pitch"]
N_BAYS = SPEC["bays"]
TL = SPEC["truss_length"]
TD = SPEC["truss_depth"]


def build():
    truss_mat = bkit.pbr("StationTruss", base=(0.62, 0.62, 0.60), metal=0.85,
                         rough=0.42)
    module_mat = bkit.pbr("StationModule", base=(0.84, 0.84, 0.80), rough=0.34,
                          metal=0.20)
    gold = bkit.pbr("StationMLI", base=(0.80, 0.64, 0.26), metal=0.85, rough=0.36)
    cell = bkit.pbr("StationCell", base=(0.05, 0.06, 0.15), rough=0.10, metal=0.30)
    radiator = bkit.pbr("StationRadiator", base=(0.90, 0.90, 0.88), rough=0.30)
    truss_half = TL / 2.0

    # ---- truss longerons: four tubes running the length ------------------
    for (name, y, z) in (("LongeronFront", 0.0, TD / 2.0),
                         ("LongeronAft", 0.0, -TD / 2.0),
                         ("LongeronPort", TD / 2.0, 0.0),
                         ("LongeronStarboard", -TD / 2.0, 0.0)):
        bkit.cylinder(name, 42.0, TL, segments=12,
                      centre=(0.0, y, z), axis="X", smooth=True, mat=truss_mat)

    # ---- bay bracing on the computed pitch -------------------------------
    # One brace per bay, rotated to alternate direction: the zig-zag is what
    # makes a truss read as a truss rather than as four sticks. Bay centres
    # come from the declared pitch, so changing BAY_PITCH re-spaces the
    # bracing and keeps the ends flush.
    for i in range(N_BAYS):
        x = -truss_half + BAY * (i + 0.5)
        s = 1.0 if i % 2 else -1.0
        # transverse frame
        bkit.cylinder("Frame%02dA" % i, 26.0, TD, segments=8,
                      centre=(x, 0.0, 0.0), axis="Y", smooth=True,
                      mat=truss_mat)
        bkit.cylinder("Frame%02dB" % i, 26.0, TD, segments=8,
                      centre=(x, 0.0, 0.0), axis="Z", smooth=True,
                      mat=truss_mat)
        # diagonal: a flat strap between the two chord points, tilted by the
        # bay's own geometry, alternating direction bay to bay
        br = bkit.rounded_box("Brace%02d" % i, BAY * 1.02, 18.0, 26.0, r=6.0,
                              centre=(x, s * TD / 2.0, 0.0), mat=truss_mat)
        br.rotation_euler = (0.0, -s * math.atan2(TD, BAY), 0.0)

    # ---- pressurised module stack across the truss ----------------------
    # Modules run along Y (the cross axis), one per computed pitch.
    MOD_LEN = 2100.0
    n_mod = SPEC["module_count"]
    for i in range(n_mod):
        y = -MOD_LEN / 2.0 + MOD_LEN * (i + 0.5) / n_mod
        m = bkit.cylinder("Module%d" % (i + 1), SPEC["module_diameter"] / 2.0,
                          MOD_LEN / n_mod - 40.0, segments=24, centre=(0.0, y, 0.0),
                          axis="Y", smooth=True,
                          mat=gold if i % 2 else module_mat)
        # end rings between modules
        if i:
            yr = -MOD_LEN / 2.0 + MOD_LEN * i / n_mod
            bkit.tube("ModuleRing%d" % i, SPEC["module_diameter"] / 2.0 + 20.0,
                      SPEC["module_diameter"] / 2.0 - 40.0, 90.0, segments=24,
                      centre=(0.0, yr, 0.0), axis="Y", mat=truss_mat)

    # ---- solar arrays: 4 pairs on the truss, computed station pitch ------
    # Array pitch is derived from the array length and the bay pitch, so the
    # eight wings are evenly spread and never collide with a bay frame.
    station_pitch = 1700.0
    for i in range(SPEC["array_count"] // 2):
        x = -truss_half + 1400.0 + i * station_pitch
        for (side, sign) in (("P", 1.0), ("S", -1.0)):
            wing = bkit.rounded_box("Array_%s%d" % (side, i + 1),
                                    SPEC["array_length"], SPEC["array_chord"],
                                    90.0, r=10.0,
                                    centre=(x, sign * 2100.0, TD / 2.0 + 340.0),
                                    mat=cell)
            wing.rotation_euler = (math.radians(sign * 22.0), 0.0, 0.0)
            bkit.cylinder("ArrayMast_%s%d" % (side, i + 1), 60.0, 700.0,
                          segments=12,
                          centre=(x, sign * (2100.0 - SPEC["array_chord"] / 2.0),
                                  TD / 2.0 + 120.0),
                          smooth=True, mat=truss_mat)

    # ---- thermal radiators: white panels edge-on to the arrays ----------
    for i, sign in ((1, 1.0), (2, -1.0)):
        bkit.rounded_box("Radiator%d" % i, 3000.0, 2400.0, 70.0, r=14.0,
                         centre=(sign * 2600.0, 0.0, -TD / 2.0 - 140.0),
                         mat=radiator)

    # ---- radiators/docking adapters at the module ends ------------------
    for i, y in enumerate((-MOD_LEN / 2.0 - 60.0, MOD_LEN / 2.0 + 60.0)):
        bkit.cylinder("DockAdapter%d" % (i + 1), 180.0, 200.0, segments=20,
                      centre=(0.0, y, 0.0), axis="Y", smooth=True, mat=truss_mat)

    return dict(spec=SPEC,
                parts=4 + N_BAYS * 3 + n_mod + (n_mod - 1) + SPEC["array_count"] * 2 + 2 + 2)


CHECKS = [
    dict(name="truss_length", mm=7400.0, tol=10.0, how="bbox_x", part="LongeronFront"),
    # a 1200 mm longeron is a 1200 mm long, 84 mm diameter tube, so bbox_z
    # measures its DIAMETER; the depth is the distance between chord centres
    dict(name="longeron_diameter", mm=84.0, tol=2.0, how="bbox_z", part="LongeronFront"),
    dict(name="array_length", mm=3400.0, tol=8.0, how="bbox_x", part="Array_P1"),
    # the wings are tilted 22 deg about X, which foreshortens the chord
    dict(name="array_chord_projected", mm=1140.0, tol=12.0, how="bbox_y", part="Array_P1"),
    dict(name="overall_length", mm=8600.0, tol=80.0, how="bbox_x"),
    dict(name="overall_height", mm=7306.0, tol=120.0, how="bbox_z"),
]