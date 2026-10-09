"""
subway_train -- two-car metro unit, 35,400 mm of car plus couplers.

A metro car is a tube: near-constant section from end to end, a smooth roof,
and a raked driving cab only at the OUTER ends. The two cars are ONE body
object duplicated and shifted -- `duplicate()` SETS location, so the copy lands
at the shift exactly, and the face materials come with the copied mesh, so the
second car's glazing and gangway bellows are already correct.

The gangway gap is 200 mm between the inner ends, with a bellows bridging it,
which is what stops two identical tubes reading as one long tube.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bpy
import bkit
import _rail as R

SPEC = dict(
    unit_length=35620.0,
    car_length=17600.0,
    car_width=2900.0,
    car_body_bottom_z=900.0,
    roof_crown_z=3700.0,
    bogie_centre_offset=5900.0,
    bogie_wheelbase=2200.0,
    wheel_diameter=840.0,
    gangway_gap=200.0,
    seats_per_car=180,
    gauge=1435.0,
)

CHECKS = [
    dict(name="car_length", mm=17600.0, tol=4.0, how="bbox_x",
         part="SubwayCarA"),
    dict(name="car_width", mm=2900.0, tol=4.0, how="bbox_y",
         part="SubwayCarA"),
    dict(name="roof_crown_z", mm=3700.0, tol=4.0, how="top_z",
         part="SubwayCarA"),
    dict(name="car_bottom_z", mm=900.0, tol=4.0, how="bottom_z",
         part="SubwayCarA"),
    dict(name="unit_over_buffers", mm=8910.0, tol=4.0, how="x_max",
         part="SubwayBuffersF"),
    dict(name="wheel_flange_diameter", mm=896.0, tol=3.0, how="bbox_z",
         part="SubwayEastAxles"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min",
         part="SubwayEastAxles"),
]

CAR_L = 17600.0
HW = 1450.0
BODY_Z0 = 900.0
CROWN_Z = 3700.0
WHEEL_D = 840.0
BOGIE_X = 5900.0
BOGIE_WB = 2200.0
GAP = 200.0


def build():
    livery = bkit.pbr("SubwayLivery", base=(0.62, 0.63, 0.64), rough=0.32)
    stripe = bkit.pbr("SubwayStripe", base=(0.06, 0.28, 0.44), rough=0.34)
    glass = bkit.pbr("SubwayGlass", base=(0.09, 0.13, 0.17), rough=0.05,
                     transmission=0.65)
    frame_m = bkit.preset("dark_metal")
    steel = bkit.preset("brushed_metal")

    # A car built about its own centre: the driving end at +X is raked, the
    # inner end at -X is flat and carries the gangway.
    stations = [
        (-CAR_L / 2.0, 1330.0, BODY_Z0, 3000.0, 2720.0),
        (-CAR_L / 2.0 + 700.0, HW, BODY_Z0, 3420.0, 3180.0),
        (-CAR_L / 2.0 + 1700.0, HW, BODY_Z0, CROWN_Z, 3320.0),
        (CAR_L / 2.0 - 1700.0, HW, BODY_Z0, CROWN_Z, 3320.0),
        (CAR_L / 2.0 - 700.0, HW, BODY_Z0, 3420.0, 3180.0),
        (CAR_L / 2.0, 1180.0, BODY_Z0, 2400.0, 2200.0),
    ]
    car_a = R.body("SubwayCarA", stations, mat=livery, smooth=42.0)
    R.window_band(car_a, 1500.0, 2700.0, glass, max_nz=0.70)
    R.window_band(car_a, 1150.0, 1480.0, stripe, max_nz=0.70)
    R.window_band(car_a, 3450.0, 3900.0, stripe, max_nz=0.92)

    car_b = bkit.duplicate(car_a, "SubwayCarB")
    bkit.move(car_b, -(CAR_L + GAP), 0.0, 0.0)

    # --- gangway bellows between the two cars ------------------------------
    bellows = bkit.rounded_box("SubwayGangway", GAP + 260.0, 2200.0, 2400.0,
                               r=90.0, segments=3, centre=(0.0, 0.0, 2350.0),
                               mat=bkit.preset("rubber"))

    # --- doors and car underframes -----------------------------------------
    trim = []
    for i, x in enumerate(R.evenly(3, 11000.0)):
        for s, tag in ((1.0, "L"), (-1.0, "R")):
            trim.append(bkit.rounded_box("SubwayDoor%s%d" % (tag, i), 1300.0,
                                         70.0, 2000.0, r=45.0, segments=2,
                                         centre=(x, s * (HW - 18.0), 2000.0),
                                         mat=stripe))
    tr_ob = bkit.join(trim, "SubwayDoors")
    bkit.recalc(tr_ob)

    covers = []
    for cx, tags in ((0.0, (("F", 1.0), ("R", -1.0))),
                     (-(CAR_L + GAP), (("BF", -1.0), ("BR", 1.0)))):
        for tag, s in tags:
            for bs, btag in ((1.0, "F"), (-1.0, "R")):
                covers.append(bkit.rounded_box("SubwayBogieCover%s%s" % (tag,
                                                                         btag),
                                               4200.0, 2.0 * (HW - 70.0),
                                               780.0, r=80.0, segments=3,
                                               centre=(cx + s * BOGIE_X, 0.0,
                                                       900.0), mat=stripe))
    cv_ob = bkit.join(covers, "SubwayBogieCovers")
    bkit.recalc(cv_ob)

    R.underframe("SubwayFrameA", CAR_L - 500.0, half_w=HW - 20.0, z_bot=800.0,
                 depth=220.0, mat=frame_m)
    frame_b = bkit.duplicate(bpy.data.objects["SubwayFrameA"], "SubwayFrameB")
    bkit.move(frame_b, -(CAR_L + GAP), 0.0, 0.0)

    R.running_gear("SubwayEast", WHEEL_D, BOGIE_X, BOGIE_WB,
                   mat_frame=frame_m)
    R.running_gear("SubwayWest", WHEEL_D, BOGIE_X, BOGIE_WB,
                   mat_frame=frame_m)
    R.shift([bpy.data.objects["SubwayWestAxles"]], -(CAR_L + GAP), 0.0, 0.0)
    for tag in ("BogieF", "BogieR", "BrakeCylF", "BrakeCylR"):
        ob = bpy.data.objects.get("SubwayWest" + tag)
        if ob:
            bkit.move(ob, -(CAR_L + GAP), 0.0, 0.0)

    # --- end equipment, placed RELATIVE TO EACH CAR'S OWN CENTRE ----------
    # Car A is built about the origin and car B is the same body shifted by
    # -(CAR_L + GAP), so anything that hangs off a car's end has to be placed
    # from that car's centre. Using one global `CAR_X` for both leaves the far
    # car's buffers, headlights and steps floating in empty space.
    for cx, ends in ((0.0, (("F", 1.0), ("R", -1.0))),
                     (-(CAR_L + GAP), (("BF", -1.0), ("BR", 1.0)))):
        for tag, s in ends:
            R.buffers("SubwayBuffers" + tag,
                      cx + s * (CAR_L / 2.0 + 110.0), z=1065.0, pitch=1750.0,
                      mat_body=frame_m, mat_head=steel)
            for i, y in enumerate((-950.0, 950.0)):
                bkit.rounded_box("SubwayHeadlight%s%d" % (tag, i), 150.0,
                                 280.0, 260.0, r=70.0, segments=3,
                                 centre=(cx + s * (CAR_L / 2.0 - 60.0), y,
                                         2700.0), mat=steel)
            for sy, ytag in ((1.0, "L"), (-1.0, "R")):
                R.steps("SubwayStep%s%s" % (tag, ytag),
                        cx + s * (CAR_L / 2.0 - 900.0), sy * 1430.0, 480.0,
                        BODY_Z0 - 40.0, steel, width=440.0, n=3)
    bkit.rounded_box("SubwayCoupler", 620.0, 340.0, 300.0, r=60.0, segments=2,
                     centre=(-GAP / 2.0, 0.0, R.above_rail(1065.0)),
                     mat=frame_m)

    return dict(spec=SPEC, parts=14)