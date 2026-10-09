"""
railcar -- single-unit diesel railcar (DMU), 23,000 mm over buffers.

A railcar is a coach that happens to have its engines in it, and the two
things that say so are the RAISED BODY and the BOGIES. 230 mm above rail at
the solebar, a body that runs the full 23 m between two two-axle bogies at
+/-8,000, and a raked cab end at each extremity.

The ends are STATIONS on one loft, not a separate nose object: the body runs
-11,300 -> +11,300 with the first and last station narrowed and dropped, so
the cab rake lives in the side silhouette where the eye reads it.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    length_over_buffers=23020.0,
    body_length=22600.0,
    body_width=2900.0,
    solebar_above_rail=230.0,
    roof_crown_z=3800.0,
    bogie_centres=(-8000.0, 8000.0),
    bogie_wheelbase=2400.0,
    wheel_diameter=850.0,
    seats=140,
    gauge=1435.0,
)

CHECKS = [
    dict(name="body_length", mm=22600.0, tol=4.0, how="bbox_x",
         part="RailcarBody"),
    dict(name="body_width", mm=2900.0, tol=4.0, how="bbox_y",
         part="RailcarBody"),
    dict(name="roof_crown_z", mm=3800.0, tol=4.0, how="top_z",
         part="RailcarBody"),
    dict(name="cab_floor_z", mm=1050.0, tol=4.0, how="bottom_z",
         part="RailcarBody"),
    dict(name="over_buffers", mm=11410.0, tol=4.0, how="x_max",
         part="RailcarBuffersF"),
    dict(name="wheel_flange_diameter", mm=906.0, tol=3.0, how="bbox_z",
         part="RailcarAxles"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min",
         part="RailcarAxles"),
]

BODY_L = 22600.0
HW = 1450.0
FLOOR_Z = 1050.0
CROWN_Z = 3800.0
WHEEL_D = 850.0
BOGIE_X = [-8000.0, 8000.0]
BOGIE_WB = 2400.0


def build():
    livery = bkit.pbr("RailcarLivery", base=(0.55, 0.56, 0.58), rough=0.30)
    cant = bkit.pbr("RailcarCantRail", base=(0.09, 0.11, 0.15), rough=0.46)
    glass = bkit.pbr("RailcarGlass", base=(0.09, 0.13, 0.17), rough=0.06,
                     transmission=0.55)
    frame_m = bkit.preset("dark_metal")
    steel = bkit.preset("brushed_metal")

    body = R.body("RailcarBody", [
        (-BODY_L / 2.0, 1250.0, FLOOR_Z, 3120.0, 2800.0),
        (-BODY_L / 2.0 + 900.0, HW, FLOOR_Z, 3700.0, 3440.0),
        (-BODY_L / 2.0 + 1900.0, HW, FLOOR_Z, CROWN_Z, 3480.0),
        (BODY_L / 2.0 - 1900.0, HW, FLOOR_Z, CROWN_Z, 3480.0),
        (BODY_L / 2.0 - 900.0, HW, FLOOR_Z, 3700.0, 3440.0),
        (BODY_L / 2.0, 1250.0, FLOOR_Z, 3120.0, 2800.0),
    ], mat=livery, smooth=42.0)
    R.window_band(body, 1500.0, 2750.0, glass, max_nz=0.70)
    R.window_band(body, 1180.0, 1480.0, cant, max_nz=0.70)

    # --- doors, skirt, bogie covers ----------------------------------------
    trim = []
    for i, x in enumerate(R.evenly(4, 15000.0)):
        for s, tag in ((1.0, "L"), (-1.0, "R")):
            trim.append(bkit.rounded_box("RailcarDoor%s%d" % (tag, i), 1300.0,
                                         70.0, 2100.0, r=40.0, segments=2,
                                         centre=(x, s * (HW - 18.0), 2150.0),
                                         mat=cant))
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        trim.append(bkit.rounded_box("RailcarSkirt" + tag, BODY_L - 3000.0,
                                     60.0, 420.0, r=20.0, segments=2,
                                     centre=(0.0, s * (HW - 10.0), 900.0),
                                     mat=cant))
    tr_ob = bkit.join(trim, "RailcarTrim")
    bkit.recalc(tr_ob)

    covers = []
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        for i, bx in enumerate(BOGIE_X):
            covers.append(bkit.rounded_box("RailcarBogieCover%d%s" % (i, tag),
                                           4400.0, 2.0 * (HW - 60.0), 900.0,
                                           r=90.0, segments=3,
                                           centre=(s * bx, 0.0, 1000.0),
                                           mat=cant))
    cv_ob = bkit.join(covers, "RailcarBogieCovers")
    bkit.recalc(cv_ob)

    R.underframe("RailcarFrame", BODY_L - 600.0, half_w=HW - 20.0,
                 z_bot=880.0, depth=280.0, mat=frame_m)
    R.running_gear("Railcar", WHEEL_D, BOGIE_X, BOGIE_WB, mat_frame=frame_m)

    # --- roof pod, steps, headlights, buffers ------------------------------
    bkit.rounded_box("RailcarRoofPod", 3600.0, 1900.0, 420.0, r=160.0,
                     segments=3, centre=(0.0, 0.0, CROWN_Z + 180.0),
                     mat=frame_m)
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        R.buffers("RailcarBuffers" + tag, s * (BODY_L / 2.0 + 110.0),
                  z=1065.0, pitch=1750.0, mat_body=frame_m, mat_head=steel)
        for sy, ytag in ((1.0, "L"), (-1.0, "R")):
            R.steps("RailcarStep%s%s" % (tag, ytag), s * 10400.0,
                    sy * 1440.0, 560.0, FLOOR_Z - 60.0, steel, width=440.0,
                    n=3)
            bkit.rounded_box("RailcarHeadlight%s%s" % (tag, ytag), 160.0,
                             300.0, 280.0, r=70.0, segments=3,
                             centre=(s * (BODY_L / 2.0 - 150.0),
                                     sy * 900.0, 2700.0), mat=steel)

    return dict(spec=SPEC, parts=12)