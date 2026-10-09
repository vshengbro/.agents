"""
passenger_carriage -- 26 m bogie passenger coach, 25,800 mm body on two
four-wheel bogies.

A coach is a LONG FLANK with a shallow roof arch and a continuous window
band, so the body is a single loft over `car_ring` rather than a stack of
boxes: the flank has to be dead vertical so the glass lands on flat body side,
and the roof rise is set independently of the body height. Splitting "body"
and "roof" into two lofts makes the shoulder fight and the join line shows in
every three-quarter view.

Bogies at +/-9,000 with a 2,500 mm wheelbase is what stops it reading as a bus
on four circles -- and the bogie covers, roof vents, drop lights, steps and
tail lamps are what stop it reading as a plain box.

The window band is a `assign_faces_by` predicate on face centre and normal:
faces in the 2,050..3,350 band whose normal is not vertical become glass,
which keeps the roof and the cant rails body-coloured.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    length_over_buffers=26020.0,
    body_length=25800.0,
    body_width=2960.0,
    floor_z=1150.0,
    roof_crown_z=4400.0,
    window_band_z=(2050.0, 3350.0),
    bogie_centre_distance=18000.0,
    bogie_wheelbase=2500.0,
    wheel_diameter=920.0,
    seats=72,
    gauge=1435.0,
)

CHECKS = [
    dict(name="body_length", mm=25800.0, tol=4.0, how="bbox_x",
         part="CoachBody"),
    dict(name="body_width", mm=2960.0, tol=4.0, how="bbox_y", part="CoachBody"),
    dict(name="roof_crown_z", mm=4400.0, tol=4.0, how="top_z",
         part="CoachBody"),
    dict(name="floor_z", mm=1150.0, tol=4.0, how="bottom_z", part="CoachBody"),
    dict(name="over_buffers", mm=13010.0, tol=4.0, how="x_max",
         part="CoachBuffersF"),
    dict(name="wheel_flange_diameter", mm=976.0, tol=3.0, how="bbox_z",
         part="CoachAxles"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min",
         part="CoachAxles"),
    dict(name="bogie_frame_length", mm=3400.0, tol=3.0, how="bbox_x",
         part="CoachBogieF"),
]

BODY_L = 25800.0
HW = 1480.0
FLOOR_Z = 1150.0
CROWN_Z = 4400.0
SHOULDER_Z = 4050.0
FRAME_Z0 = 980.0
WHEEL_D = 920.0
BOGIE_X = 9000.0
BOGIE_WB = 2500.0


def build():
    livery = bkit.pbr("CoachMaroon", base=(0.34, 0.10, 0.09), rough=0.28)
    cant = bkit.pbr("CoachCantRail", base=(0.10, 0.12, 0.16), rough=0.45)
    roof_m = bkit.pbr("CoachRoofGrey", base=(0.40, 0.41, 0.43), rough=0.70)
    glass = bkit.pbr("CoachGlass", base=(0.10, 0.14, 0.18), rough=0.06,
                     transmission=0.55)
    frame_m = bkit.preset("dark_metal")
    steel = bkit.preset("brushed_metal")

    # --- body: one loft over rounded-corner stations -----------------------
    stations = [
        (-BODY_L / 2.0, HW - 110.0, FLOOR_Z, 3900.0, 3560.0),
        (-BODY_L / 2.0 + 420.0, HW - 20.0, FLOOR_Z, 4300.0, 3990.0),
        (-BODY_L / 2.0 + 1400.0, HW, FLOOR_Z, CROWN_Z, SHOULDER_Z),
        (BODY_L / 2.0 - 1400.0, HW, FLOOR_Z, CROWN_Z, SHOULDER_Z),
        (BODY_L / 2.0 - 420.0, HW - 20.0, FLOOR_Z, 4300.0, 3990.0),
        (BODY_L / 2.0, HW - 110.0, FLOOR_Z, 3900.0, 3560.0),
    ]
    body = R.body("CoachBody", stations, mat=livery, smooth=42.0)
    R.window_band(body, 2050.0, 3350.0, glass, max_nz=0.70)
    # cant rail: the dark band under the windows, and the roof above the
    # shoulder -- two separate bands off the same predicate shape.
    R.window_band(body, 1750.0, 2040.0, cant, max_nz=0.70)
    R.window_band(body, 4100.0, 4600.0, roof_m, max_nz=0.90)

    # --- doors, in the gaps between the window bays ------------------------
    doors = []
    for i, x in enumerate(R.evenly(8, 20600.0)):
        for s, tag in ((1.0, "L"), (-1.0, "R")):
            doors.append(bkit.rounded_box("CoachDoor%s%d" % (tag, i), 1200.0,
                                          70.0, 2100.0, r=45.0, segments=2,
                                          centre=(x, s * (HW - 18.0), 2200.0),
                                          mat=cant))
    door_ob = bkit.join(doors, "CoachDoors")
    bkit.recalc(door_ob)

    # --- underframe, bogie covers, running gear ----------------------------
    R.underframe("CoachFrame", BODY_L - 400.0, half_w=HW - 20.0,
                 z_bot=FRAME_Z0, depth=280.0, mat=frame_m)
    covers = []
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        covers.append(bkit.rounded_box("CoachBogieCover" + tag, 4600.0,
                                       2.0 * (HW - 60.0), 900.0, r=90.0,
                                       segments=3,
                                       centre=(s * BOGIE_X, 0.0, 1050.0),
                                       mat=cant))
    cv_ob = bkit.join(covers, "CoachBogieCovers")
    bkit.recalc(cv_ob)
    R.running_gear("Coach", WHEEL_D, BOGIE_X, BOGIE_WB, mat_frame=frame_m)

    # --- roof vents, steps, tail lamps, buffers ----------------------------
    vents = []
    for i, x in enumerate(R.evenly(5, 18000.0)):
        vents.append(bkit.rounded_box("CoachRoofVent%d" % i, 420.0, 420.0,
                                      180.0, r=70.0, segments=3,
                                      centre=(x, 0.0, CROWN_Z + 40.0),
                                      mat=roof_m))
    v_ob = bkit.join(vents, "CoachRoofVents")
    bkit.recalc(v_ob)

    for s, tag in ((1.0, "F"), (-1.0, "R")):
        R.buffers("CoachBuffers" + tag, s * (BODY_L / 2.0 + 110.0),
                  z=1065.0, pitch=1750.0, mat_body=frame_m, mat_head=steel)
        for sy, ytag in ((1.0, "L"), (-1.0, "R")):
            R.steps("CoachStep%s%s" % (tag, ytag), s * 11800.0, sy * 1450.0,
                    620.0, FLOOR_Z - 60.0, steel, width=460.0, n=3)
        for i, y in enumerate((-1150.0, 1150.0)):
            bkit.rounded_box("CoachTailLamp%s%d" % (tag, i), 140.0, 240.0,
                             300.0, r=50.0, segments=3,
                             centre=(s * (BODY_L / 2.0 - 240.0), y, 3350.0),
                             mat=bkit.preset("red_paint"))

    return dict(spec=SPEC, parts=14)