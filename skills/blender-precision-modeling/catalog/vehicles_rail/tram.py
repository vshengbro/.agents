"""
tram -- 33 m three-section low-floor tram with a raised diamond pantograph.

Two things separate a tram from a coach on the same bogies. It is LOW FLOOR:
the skirt comes down to 350 mm above rail and the only step up is at the
doors, where a 230 mm solebar would put the floor half a metre higher. And it
takes its power from overhead wire, so the roof carries a pantograph -- a
diamond pantograph is four struts meeting at a knee plus a contact shoe, and
that silhouette is the single most recognisable tram cue there is.

Three four-wheel bogies at -12,000 / 0 / +12,000, so eight wheels a side.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    length_over_buffers=33220.0,
    body_length=32000.0,
    body_width=2500.0,
    skirt_above_rail=350.0,
    floor_above_rail=350.0,
    roof_crown_z=3260.0,
    bogie_centres=(-12000.0, 0.0, 12000.0),
    bogie_wheelbase=1800.0,
    wheel_diameter=650.0,
    pantograph_top_z=4345.0,
    gauge=1435.0,
)

CHECKS = [
    dict(name="body_length", mm=32000.0, tol=4.0, how="bbox_x",
         part="TramBody"),
    dict(name="body_width", mm=2500.0, tol=4.0, how="bbox_y", part="TramBody"),
    dict(name="roof_crown_z", mm=3260.0, tol=4.0, how="top_z", part="TramBody"),
    dict(name="skirt_bottom_z", mm=378.0, tol=4.0, how="bottom_z",
         part="TramBody"),
    dict(name="pantograph_top_z", mm=4345.0, tol=5.0, how="top_z",
         part="TramPantograph"),
    dict(name="wheel_flange_diameter", mm=706.0, tol=3.0, how="bbox_z",
         part="TramAxles"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min",
         part="TramAxles"),
]

BODY_L = 32000.0
HW = 1250.0
SKIRT_Z = R.above_rail(350.0)          # 378
CROWN_Z = 3260.0
WHEEL_D = 650.0
BOGIE_X = [-12000.0, 0.0, 12000.0]
BOGIE_WB = 1800.0


def build():
    livery = bkit.pbr("TramLivery", base=(0.62, 0.14, 0.12), rough=0.28)
    skirt_m = bkit.pbr("TramSkirt", base=(0.16, 0.17, 0.20), rough=0.48)
    glass = bkit.pbr("TramGlass", base=(0.10, 0.14, 0.18), rough=0.05,
                     transmission=0.65)
    frame_m = bkit.preset("dark_metal")
    steel = bkit.preset("brushed_metal")

    body = R.body("TramBody", [
        (-BODY_L / 2.0, 1010.0, SKIRT_Z, 2800.0, 2500.0),
        (-BODY_L / 2.0 + 800.0, HW, SKIRT_Z, 3120.0, 2880.0),
        (-BODY_L / 2.0 + 2200.0, HW, SKIRT_Z, CROWN_Z, 2980.0),
        (BODY_L / 2.0 - 2200.0, HW, SKIRT_Z, CROWN_Z, 2980.0),
        (BODY_L / 2.0 - 800.0, HW, SKIRT_Z, 3120.0, 2880.0),
        (BODY_L / 2.0, 1010.0, SKIRT_Z, 2800.0, 2500.0),
    ], mat=livery, smooth=42.0)
    R.window_band(body, 1300.0, 2500.0, glass, max_nz=0.70)

    # --- door leaves, in body colour, between the window bays --------------
    doors = []
    for i, x in enumerate(R.evenly(8, 24000.0)):
        for s, tag in ((1.0, "L"), (-1.0, "R")):
            doors.append(bkit.rounded_box("TramDoor%s%d" % (tag, i), 1400.0,
                                          60.0, 1900.0, r=40.0, segments=2,
                                          centre=(x, s * (HW - 12.0), 1650.0),
                                          mat=skirt_m))
    d_ob = bkit.join(doors, "TramDoors")
    bkit.recalc(d_ob)

    # --- low skirt down to 350 mm above rail, and bogie fairings -----------
    skirt = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        skirt.append(bkit.rounded_box("TramSkirt" + tag, BODY_L - 4000.0, 60.0,
                                      560.0, r=20.0, segments=2,
                                      centre=(0.0, s * (HW - 8.0), 660.0),
                                      mat=skirt_m))
    for i, bx in enumerate(BOGIE_X):
        for s, tag in ((1.0, "L"), (-1.0, "R")):
            skirt.append(bkit.rounded_box("TramBogieFairing%d%s" % (i, tag),
                                          3600.0, 70.0, 420.0, r=30.0,
                                          segments=2,
                                          centre=(s * bx, s * (HW - 4.0),
                                                  540.0), mat=skirt_m))
    sk_ob = bkit.join(skirt, "TramSkirts")
    bkit.recalc(sk_ob)

    R.underframe("TramFrame", BODY_L - 1000.0, half_w=HW - 30.0, z_bot=380.0,
                 depth=200.0, mat=frame_m)
    R.running_gear("Tram", WHEEL_D, BOGIE_X, BOGIE_WB, mat_frame=frame_m)

    # --- diamond pantograph on the roof ------------------------------------
    px = 8000.0
    knee_z = 3760.0
    head_z = 4300.0
    panto = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        panto.append(R.strut("TramPantoBase" + tag,
                             (px, s * 900.0, CROWN_Z - 100.0),
                             (px, s * 150.0, knee_z), 80.0, steel, seg=14))
        panto.append(R.strut("TramPantoUpper" + tag,
                             (px, s * 150.0, knee_z),
                             (px, s * 520.0, head_z), 62.0, steel, seg=14))
    panto.append(bkit.rounded_box("TramPantoShoe", 2400.0, 210.0, 90.0,
                                  r=30.0, segments=2,
                                  centre=(px, 0.0, head_z), mat=steel))
    panto.append(bkit.rounded_box("TramPantoBase", 900.0, 2000.0, 140.0,
                                  r=50.0, segments=2,
                                  centre=(px, 0.0, CROWN_Z - 60.0),
                                  mat=steel))
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        panto.append(R.strut("TramPantoHorn" + tag,
                             (px, s * 520.0, head_z),
                             (px, s * 1150.0, head_z - 190.0), 52.0, steel,
                             seg=10))
    pa_ob = bkit.join(panto, "TramPantograph")
    bkit.recalc(pa_ob)

    # --- destination blind, steps, buffers ---------------------------------
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        bkit.rounded_box("TramBlind" + tag, 120.0, 1500.0, 260.0, r=40.0,
                         segments=3,
                         centre=(s * (BODY_L / 2.0 - 60.0), 0.0, 2900.0),
                         mat=bkit.pbr("TramBlindFace", base=(0.04, 0.04, 0.05),
                                      rough=0.3,
                                      emission=(1.0, 0.72, 0.15),
                                      emission_strength=1.4))
        R.buffers("TramBuffers" + tag, s * (BODY_L / 2.0 + 110.0), z=1065.0,
                  pitch=1750.0, mat_body=frame_m, mat_head=steel)
        for sy, ytag in ((1.0, "L"), (-1.0, "R")):
            R.steps("TramStep%s%s" % (tag, ytag), s * 15200.0, sy * 1200.0,
                    200.0, SKIRT_Z + 40.0, steel, width=420.0, n=2)

    return dict(spec=SPEC, parts=12)