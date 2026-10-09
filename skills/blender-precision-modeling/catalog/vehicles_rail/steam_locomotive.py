"""
steam_locomotive -- 4-6-4 tender locomotive, 20,640 mm over buffers.

A steam locomotive is a REVIVAL about one axis. The boiler, the smokebox and
the chimney are a single cylinder on the centreline; everything else -- the
running plate, the splashers, the cylinders, the cab -- hangs off it. Getting
the boiler axis at 2,850 mm is the whole job: it clears the 1,806 mm crown of
the 1,750 mm driving wheels by 44 mm, and any lower and the wheels cut into the
firebox.

Wheel count is what makes it read, and here it is a 4-6-4: a four-wheel LEADING
truck at +3,600/+5,000, three coupled driving axles at -2,000 / 0 / +2,000,
and a four-wheel TRAILING truck at -4,900/-3,600 -- ten wheels on the engine,
four more on the tender. Two wheels a side would be a trolley.

1750 mm drivers give an axle height of 903, and those flange tips are the
model's floor datum: everything else -- buffers at 1,065 mm over the railhead,
the running plate at 2,350 -- is quoted from there.
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
    length_over_buffers=20640.0,
    boiler_diameter=2000.0,
    boiler_length=6600.0,
    chimney_top_z=4650.0,
    cab_roof_z=4300.0,
    running_plate_z=2350.0,
    driving_wheel_diameter=1750.0,
    driving_axles=(-2000.0, 0.0, 2000.0),
    truck_wheel_diameter=900.0,
    leading_truck=3600.0,
    trailing_truck=-4900.0,
    tender_wheel_diameter=1000.0,
    gauge=1435.0,
)

CHECKS = [
    dict(name="over_buffers", mm=6000.0, tol=4.0, how="x_max",
         part="LocoBuffersF"),
    dict(name="tender_over_buffers", mm=-14640.0, tol=4.0, how="x_min",
         part="LocoBuffersR"),
    dict(name="boiler_diameter", mm=2040.0, tol=4.0, how="bbox_y",
         part="LocoSmokebox"),
    dict(name="boiler_length", mm=6600.0, tol=4.0, how="bbox_x",
         part="LocoBoiler"),
    dict(name="chimney_top_z", mm=4650.0, tol=4.0, how="top_z",
         part="LocoChimney"),
    dict(name="cab_roof_z", mm=4300.0, tol=4.0, how="top_z", part="LocoCabRoof"),
    dict(name="running_plate_z", mm=2350.0, tol=4.0, how="top_z",
         part="LocoPlate"),
    dict(name="driving_flange_diameter", mm=1806.0, tol=3.0, how="bbox_z",
         part="LocoDrivingAxles"),
    dict(name="flange_on_datum", mm=0.0, tol=0.6, how="z_min",
         part="LocoDrivingAxles"),
    dict(name="tender_flange_diameter", mm=1056.0, tol=3.0, how="bbox_z",
         part="TenderAxles"),
]

BOILER_R = 1000.0
BOILER_Z = 2850.0
SMOKE_R = 1020.0
PLATE_Z = 2350.0
LOCO_FACE = 6000.0
LOCO_TAIL = -5700.0
DRIVE_D = 1750.0
DRIVE_X = [-2000.0, 0.0, 2000.0]
TRUCK_D = 900.0
TRUCK_X = [3600.0, 5000.0, -4900.0, -3600.0]
TENDER_FACE = -14200.0
TENDER_NOSE = -6300.0
TENDER_D = 1000.0


def build():
    black = bkit.pbr("LocoBlack", base=(0.045, 0.045, 0.048), rough=0.40)
    red = bkit.pbr("LocoLiningRed", base=(0.42, 0.08, 0.06), rough=0.30)
    steel = bkit.preset("dark_metal")
    brass = bkit.preset("brushed_metal")
    glass = bkit.pbr("LocoCabGlass", base=(0.12, 0.16, 0.19), rough=0.07,
                     transmission=0.5)

    # --- boiler, smokebox, chimney -----------------------------------------
    boiler = bkit.cylinder("LocoBoiler", BOILER_R, 6600.0, segments=72,
                           axis="X", centre=(900.0, 0.0, BOILER_Z), mat=black)
    bkit.recalc(boiler)
    for x, nm in ((-2400.0, "LocoBoilerFront"), (4200.0, "LocoBoilerBand")):
        bkit.tube(nm, BOILER_R + 26.0, BOILER_R - 6.0, 90.0, segments=72,
                  axis="X", centre=(x, 0.0, BOILER_Z), mat=brass)
    smoke = bkit.cylinder("LocoSmokebox", SMOKE_R, 1800.0, segments=72,
                          axis="X", centre=(5100.0, 0.0, BOILER_Z), mat=black)
    bkit.recalc(smoke)
    bkit.cylinder("LocoSmokeDoor", 560.0, 90.0, segments=40, axis="X",
                  centre=(6040.0, 0.0, BOILER_Z), mat=brass)
    bkit.cylinder("LocoChimney", 430.0, 1080.0, segments=36, axis="Z",
                  centre=(4900.0, 0.0, 4110.0), mat=black)
    bkit.cylinder("LocoChimneyCap", 520.0, 130.0, segments=36, axis="Z",
                  centre=(4900.0, 0.0, 4585.0), mat=black)

    domes = []
    for x, r, nm in ((2400.0, 480.0, "LocoSteamDome"),
                     (3350.0, 400.0, "LocoSandDome")):
        domes.append(bkit.uv_sphere(nm, r, segments=32, rings=16,
                                    centre=(x, 0.0, BOILER_Z + BOILER_R * 0.55),
                                    mat=brass))
    d_ob = bkit.join(domes, "LocoDomes")
    bkit.recalc(d_ob)

    # --- running plate, splashers, cylinders -------------------------------
    plate = bkit.rounded_box("LocoPlate", 11500.0, 3000.0, 70.0, r=20.0,
                             segments=2, centre=(150.0, 0.0, PLATE_Z - 35.0),
                             mat=steel)
    splash = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        for x in DRIVE_X:
            splash.append(bkit.rounded_box("LocoSplasher%s%d" % (tag, 0), 2100.0,
                                           60.0, 700.0, r=300.0, segments=4,
                                           centre=(x, s * 1240.0, PLATE_Z + 330.0),
                                           mat=black))
    sp_ob = bkit.join(splash, "LocoSplashers")
    bkit.recalc(sp_ob)
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        bkit.cylinder("LocoCylinder" + tag, 430.0, 1500.0, segments=32, axis="X",
                      centre=(4750.0, s * 1120.0, PLATE_Z - 250.0), mat=black)

    # --- cab ----------------------------------------------------------------
    cab = R.body("LocoCab", [
        (-5700.0, 1420.0, 1250.0, 3900.0, 3600.0),
        (-5300.0, 1500.0, 1250.0, 4180.0, 3900.0),
        (-2600.0, 1500.0, 1250.0, 4180.0, 3900.0),
        (-2300.0, 1440.0, 1250.0, 3900.0, 3600.0),
    ], mat=red, smooth=40.0)
    R.window_band(cab, 2900.0, 3700.0, glass, max_nz=0.70)
    roof = bkit.rounded_box("LocoCabRoof", 3300.0, 3160.0, 240.0, r=180.0,
                            segments=4, centre=(-4000.0, 0.0, 4180.0), mat=black)

    # --- running gear: two trucks and three coupled axles ------------------
    r_drive = R.wheel_r(DRIVE_D)
    R.axles("LocoDrivingAxles",
            R.wheelset("LocoDrivingWheel", dia=DRIVE_D, tread=150.0, seg=48,
                       mat_rim=steel, mat_steel=steel),
            DRIVE_X, r_drive)
    r_truck = R.wheel_r(TRUCK_D)
    R.axles("LocoTruckAxles",
            R.wheelset("LocoTruckWheel", dia=TRUCK_D, tread=135.0, seg=48,
                       mat_steel=steel),
            TRUCK_X, r_truck)
    for i, bx in enumerate((3600.0, -4900.0)):
        bk = R.bogie("LocoTruck%d" % i, 1400.0, TRUCK_D, steel, steel,
                     frame_z=r_truck + 40.0)
        bkit.move(bk, bx, 0.0, r_truck)
    for i, x in enumerate(DRIVE_X):
        bkit.cylinder("LocoCrankPin%d" % i, 150.0, 420.0, segments=24,
                      axis="Y", centre=(x, 1030.0, r_drive + 320.0), mat=steel)
        R.strut("LocoCouplingRod%d" % i, (x - 2000.0, 1030.0, r_drive + 320.0),
                (x + 2000.0, 1030.0, r_drive + 320.0), 70.0, steel, seg=12)

    R.buffers("LocoBuffersF", LOCO_FACE, z=1065.0, pitch=1750.0,
              mat_body=black, mat_head=steel)

    # --- tender --------------------------------------------------------------
    frame = bkit.rounded_box("TenderFrame", 7900.0, 2900.0, 300.0, r=30.0,
                             segments=2,
                             centre=((TENDER_FACE + TENDER_NOSE) / 2.0, 0.0,
                                     1100.0), mat=black)
    tender = R.body("TenderBody", [
        (TENDER_FACE + 120.0, 1380.0, 1250.0, 3100.0, 2900.0),
        (TENDER_FACE + 620.0, 1450.0, 1250.0, 3300.0, 3080.0),
        (TENDER_NOSE - 620.0, 1450.0, 1250.0, 3300.0, 3080.0),
        (TENDER_NOSE - 120.0, 1380.0, 1250.0, 3100.0, 2900.0),
    ], mat=black, smooth=40.0)
    coal = bkit.rounded_box("TenderCoal", 4200.0, 2500.0, 500.0, r=200.0,
                            segments=3, centre=((TENDER_FACE + TENDER_NOSE) / 2.0
                                                - 900.0, 0.0, 3250.0),
                            mat=bkit.preset("black_plastic"))
    R.axles("TenderAxles",
            R.wheelset("TenderWheel", dia=TENDER_D, tread=140.0, seg=48,
                       mat_steel=steel),
            [-12700.0, -8600.0], R.wheel_r(TENDER_D))
    R.buffers("LocoBuffersR", TENDER_FACE, z=1065.0, pitch=1750.0,
              mat_body=black, mat_head=steel)
    bkit.rounded_box("LocoCoupling", 700.0, 320.0, 280.0, r=60.0, segments=2,
                     centre=(-6000.0, 0.0, R.above_rail(1065.0)),
                     mat=steel)
    bkit.rounded_box("LocoTenderBeam", 1600.0, 2700.0, 260.0, r=40.0,
                     segments=2, centre=(-6050.0, 0.0, 1100.0), mat=steel)

    return dict(spec=SPEC, parts=24)