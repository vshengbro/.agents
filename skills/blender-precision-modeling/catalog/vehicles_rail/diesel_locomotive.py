"""
diesel_locomotive -- Co-Co diesel-electric locomotive, 20,800 mm frame,
10,400 mm each side of centre, six axles on three two-axle bogies.

Three bogies is the Co-Co arrangement and it is what separates a diesel
locomotive from a shunter: bogie centres at -7,000, 0 and +7,000 with a
2,500 mm wheelbase give axle centres at -8,250 / -5,750 / -1,250 / +1,250 /
+5,750 / +8,250. Six wheels per side, never three -- a locomotive on three
wheels a side reads as broken the instant it is rendered.

The body is three lofts (cab, long hood, short hood) rather than one, because
a locomotive roof line STEPS: full height over the cab, lower over the long
hood, lower still over the short hood. Forcing that into one loft would need a
section count that changes along the length, which `loft()` cannot bridge.

1050 mm wheels put the axle centres at 553, so the flange tips -- the real
lowest points -- sit exactly on z=0 and `sit_on_floor()` is a no-op.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _rail as R

SPEC = dict(
    frame_length=20800.0,
    length_over_buffers=21020.0,
    body_width=2900.0,
    cab_roof_z=3900.0,
    hood_roof_z=3500.0,
    short_hood_z=3200.0,
    bogie_centres=(-7000.0, 0.0, 7000.0),
    bogie_wheelbase=2500.0,
    wheel_diameter=1050.0,
    axle_count=6,
    power_kw=2270.0,
    gauge=1435.0,
)

CHECKS = [
    dict(name="frame_length", mm=20800.0, tol=4.0, how="bbox_x",
         part="DieselFrame"),
    dict(name="over_buffers", mm=10510.0, tol=4.0, how="x_max",
         part="DieselBuffersF"),
    dict(name="cab_roof_z", mm=3900.0, tol=4.0, how="top_z", part="DieselCab"),
    dict(name="hood_roof_z", mm=3500.0, tol=4.0, how="top_z",
         part="DieselLongHood"),
    dict(name="body_width", mm=2900.0, tol=4.0, how="bbox_y", part="DieselCab"),
    dict(name="wheel_flange_diameter", mm=1106.0, tol=3.0, how="bbox_z",
         part="DieselAxles"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min",
         part="DieselAxles"),
    # 2 x 8,250 outer axle centres + 2 x 553 flange radius.
    dict(name="axle_row_span", mm=17606.0, tol=4.0, how="bbox_x",
         part="DieselAxles"),
]

FRAME_L = 20800.0
HW = 1450.0
FLOOR_Z = 1250.0
WHEEL_D = 1050.0
BOGIE_X = [-7000.0, 0.0, 7000.0]
BOGIE_WB = 2500.0


def build():
    livery = bkit.pbr("DieselLivery", base=(0.13, 0.34, 0.46), rough=0.30)
    dark = bkit.pbr("DieselDark", base=(0.09, 0.10, 0.12), rough=0.46)
    roof_m = bkit.pbr("DieselRoof", base=(0.34, 0.35, 0.37), rough=0.72)
    glass = bkit.pbr("DieselGlass", base=(0.09, 0.13, 0.17), rough=0.06,
                     transmission=0.55)
    steel = bkit.preset("dark_metal")
    frame_m = bkit.preset("dark_metal")

    R.underframe("DieselFrame", FRAME_L, half_w=HW, z_bot=950.0, depth=300.0,
                 mat=frame_m)

    cab = R.body("DieselCab", [
        (-FRAME_L / 2.0, 1360.0, FLOOR_Z, 3560.0, 3260.0),
        (-FRAME_L / 2.0 + 520.0, HW, FLOOR_Z, 3900.0, 3560.0),
        (-6400.0, HW, FLOOR_Z, 3900.0, 3560.0),
        (-6250.0, 1430.0, FLOOR_Z, 3620.0, 3300.0),
    ], mat=livery, smooth=42.0)
    R.window_band(cab, 2350.0, 3350.0, glass, max_nz=0.70)

    hood = R.body("DieselLongHood", [
        (-6250.0, 1430.0, FLOOR_Z, 3500.0, 3260.0),
        (-5600.0, HW, FLOOR_Z, 3500.0, 3260.0),
        (6800.0, HW, FLOOR_Z, 3500.0, 3260.0),
        (7000.0, 1400.0, FLOOR_Z, 3200.0, 2980.0),
    ], mat=livery, smooth=42.0)
    R.window_band(hood, 3560.0, 4000.0, roof_m, max_nz=0.90)

    nose = R.body("DieselShortHood", [
        (7000.0, 1400.0, FLOOR_Z, 3200.0, 2980.0),
        (10150.0, 1380.0, FLOOR_Z, 3150.0, 2930.0),
        (FRAME_L / 2.0, 1290.0, FLOOR_Z, 2950.0, 2760.0),
    ], mat=livery, smooth=42.0)
    R.window_band(nose, 3200.0, 3600.0, roof_m, max_nz=0.90)

    # --- radiator grilles down the long hood flank -------------------------
    grilles = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        for i, (x, w) in enumerate(bkit.lay_out([900.0, 2600.0, 900.0],
                                                gap=700.0)):
            grilles.append(bkit.rounded_box("DieselGrille%s%d" % (tag, i), w,
                                            70.0, 1350.0, r=30.0, segments=2,
                                            centre=(x, s * (HW - 15.0), 2400.0),
                                            mat=dark))
    g_ob = bkit.join(grilles, "DieselGrilles")
    bkit.recalc(g_ob)

    # --- roof detail: exhaust, radiator fans, horn -------------------------
    bkit.cylinder("DieselExhaust", 260.0, 420.0, segments=28, axis="Z",
                  centre=(2900.0, 0.0, 3620.0), mat=dark)
    fans = []
    for i, x in enumerate(R.evenly(3, 6000.0)):
        fans.append(bkit.cylinder("DieselRoofFan%d" % i, 620.0, 120.0,
                                  segments=32, axis="Z",
                                  centre=(x, 0.0, 3560.0), mat=dark))
    f_ob = bkit.join(fans, "DieselRoofFans")
    bkit.recalc(f_ob)
    bkit.rounded_box("DieselHorn", 380.0, 260.0, 300.0, r=90.0, segments=3,
                     centre=(-5900.0, 700.0, 3700.0), mat=steel)

    # --- handrails along the running plate --------------------------------
    rails = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        rails.append(R.strut("DieselWalkRail" + tag,
                             (-5900.0, s * (HW + 60.0), 1950.0),
                             (6600.0, s * (HW + 60.0), 1950.0), 32.0, steel,
                             seg=10))
        for i, x in enumerate(R.evenly(7, 12000.0)):
            rails.append(R.strut("DieselWalkStanchion%s%d" % (tag, i),
                                 (x, s * (HW + 60.0), 1300.0),
                                 (x, s * (HW + 60.0), 1950.0), 26.0, steel,
                                 seg=8))
    r_ob = bkit.join(rails, "DieselHandrails")
    bkit.recalc(r_ob)

    # --- fuel tanks in the frame, steps, lamps, buffers --------------------
    tanks = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        tanks.append(bkit.rounded_box("DieselFuelTank" + tag, 2400.0, 900.0,
                                      620.0, r=70.0, segments=3,
                                      centre=(s * 2975.0, s * 900.0, 620.0),
                                      mat=dark))
    t_ob = bkit.join(tanks, "DieselFuelTanks")
    bkit.recalc(t_ob)
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        for sy, ytag in ((1.0, "L"), (-1.0, "R")):
            R.steps("DieselStep%s%s" % (tag, ytag), s * 9600.0, sy * 1450.0,
                    480.0, FLOOR_Z - 60.0, steel, width=460.0, n=3)
        for i, y in enumerate((-1050.0, 1050.0)):
            bkit.rounded_box("DieselHeadlight%s%d" % (tag, i), 160.0, 320.0,
                             300.0, r=70.0, segments=3,
                             centre=(s * (FRAME_L / 2.0 - 300.0), y, 2900.0),
                             mat=steel)
        R.buffers("DieselBuffers" + tag, s * (FRAME_L / 2.0 + 110.0),
                  z=1065.0, pitch=1750.0, mat_body=frame_m, mat_head=steel)

    R.running_gear("Diesel", WHEEL_D, BOGIE_X, BOGIE_WB, mat_frame=frame_m)

    return dict(spec=SPEC, parts=17)