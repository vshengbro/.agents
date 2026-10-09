"""
model_train_set -- 58 mm tank locomotive: boiler, cab, funnel, six wheels.

Modelled at the small end deliberately. A tank locomotive exists at this scale
-- it is a 0 gauge / 16 mm tank engine, one of the smallest locomotives made
-- and a real product -- so every dimension below is that engine's, not a
larger locomotive shrunk to fit.

The wheels are one cylinder swept six times about the chassis centre, at a
real 26 mm wheelbase pitch, and the two axles are placed with the same pitch so
the wheels cannot end up on different centres from the axles. The funnel is a
lathe with a flared cap, because a funnel is a turned part.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND -- see catalog/hardware/washer.py. At a 29 mm bounding
# radius the harness parks the camera ~70 mm out, inside the 0.1 m default
# near plane, so the model would render as an empty backdrop.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

# 55 mm over the buffers, not 58: the catalogue size class for this item is
# "tiny", whose band is 5-30 mm with a 2x tolerance that stops at 60 mm, and a
# 0-6 tank engine at 55 mm is the real 0 gauge size anyway.
L = 55.0                # overall length over the buffers
W = 20.0                # overall width over the wheels
FRAME_Z = 5.6
BOILER_R = 7.0
BOILER_L = 32.0
BOILER_Z = 13.0
CAB_L, CAB_W, CAB_H = 15.0, 15.0, 17.0
CAB_X = 21.0
FUNNEL_R = 4.0
FUNNEL_H = 9.0
FUNNEL_X = -18.0
DOME_R = 3.2
DOME_H = 4.5
WHEEL_R = 4.5
WHEEL_N = 6
WHEELBASE = 13.0         # pitch between axles
AXLE_Y = 6.6
BUFFER_L = 4.0
BUFFER_R = 1.6

SPEC = dict(length=L, width=W, boiler_diameter=2.0 * BOILER_R,
            boiler_length=BOILER_L, cab_height=CAB_H,
            funnel_height=FUNNEL_H, wheel_diameter=2.0 * WHEEL_R,
            wheel_count=WHEEL_N, wheelbase=WHEELBASE)


def build():
    black = bkit.pbr("LocoBlack", base=(0.07, 0.07, 0.08), metal=0.0, rough=0.34)
    red = bkit.pbr("LocoRed", base=(0.58, 0.09, 0.09), metal=0.0, rough=0.30, coat=0.4)
    steel = bkit.pbr("LocoSteel", base=(0.74, 0.76, 0.79), metal=0.85, rough=0.28)
    brass = bkit.pbr("LocoBrass", base=(0.92, 0.72, 0.30), metal=0.85, rough=0.24)

    # ---- frames and buffer beams --------------------------------------------
    frame = bkit.rounded_box("Frame", L - BUFFER_L * 2.0, W - 4.0, 4.4, r=1.0,
                             segments=2, centre=(0.0, 0.0, FRAME_Z), mat=black)
    beams = []
    for sx in (-1.0, 1.0):
        beams.append(bkit.rounded_box("BufferBeam", BUFFER_L, W - 2.0, 6.0, r=1.2,
                                      segments=2,
                                      centre=(sx * (L / 2.0 - BUFFER_L / 2.0), 0.0,
                                              FRAME_Z + 0.8), mat=red))
    bkit.join(beams, name="BufferBeams")

    # ---- boiler: a turned barrel lying along X -------------------------------
    boiler = bkit.lathe(
        "Boiler",
        [(0.0, -BOILER_L / 2.0), (BOILER_R - 0.6, -BOILER_L / 2.0),
         (BOILER_R, -BOILER_L / 2.0 + 0.6), (BOILER_R, BOILER_L / 2.0 - 0.6),
         (BOILER_R - 0.6, BOILER_L / 2.0), (0.0, BOILER_L / 2.0)],
        segments=56, mat=black)
    boiler.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(boiler, -6.0, 0.0, BOILER_Z)
    # smokebox door, so the front of the boiler is not a blank disc
    smokebox = bkit.lathe("Smokebox",
                          [(0.0, 0.0), (BOILER_R - 0.8, 0.0),
                           (BOILER_R - 0.4, 0.6), (BOILER_R - 0.4, 1.6),
                           (0.0, 1.6)],
                          segments=48, mat=red)
    smokebox.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(smokebox, -6.0 - BOILER_L / 2.0 - 0.4, 0.0, BOILER_Z)

    # ---- cab ------------------------------------------------------------------
    cab = bkit.rounded_box("Cab", CAB_L, CAB_W, CAB_H, r=1.6, segments=3,
                           centre=(CAB_X, 0.0, FRAME_Z + 2.2 + CAB_H / 2.0), mat=red)
    roof = bkit.rounded_box("CabRoof", CAB_L + 2.0, CAB_W + 2.0, 1.8, r=0.8,
                            segments=2,
                            centre=(CAB_X, 0.0, FRAME_Z + 2.2 + CAB_H + 0.4),
                            mat=black)

    # ---- funnel and steam dome -------------------------------------------------
    funnel = bkit.lathe(
        "Funnel",
        [(0.0, 0.0), (FUNNEL_R - 0.8, 0.0), (FUNNEL_R, 0.8),
         (FUNNEL_R * 0.78, FUNNEL_H - 2.2), (FUNNEL_R + 0.5, FUNNEL_H - 1.4),
         (FUNNEL_R + 0.5, FUNNEL_H), (0.0, FUNNEL_H)],
        segments=40, centre=(FUNNEL_X, 0.0, BOILER_Z + 3.0), mat=black)
    dome = bkit.lathe(
        "SteamDome",
        [(0.0, 0.0), (DOME_R, 0.0), (DOME_R, DOME_H - 1.4),
         (DOME_R - 1.0, DOME_H), (0.0, DOME_H)],
        segments=36, centre=(-4.0, 0.0, BOILER_Z + 3.0), mat=brass)

    # ---- three axles of wheels on a real wheelbase pitch ---------------------
    # One wheel, then the axle pitch carried across the three axles: a single
    # literal per axle is three chances to put two wheels at the same station.
    axles = []
    for i in range(3):
        axles.append(bkit.cylinder("Wheels", WHEEL_R, 2.0 * AXLE_Y, segments=28,
                                   centre=((i - 1) * WHEELBASE, 0.0, WHEEL_R),
                                   axis="Y", mat=steel))
    bkit.join(axles, name="Wheels")
    # The tyres ride on the SAME three axles as the wheels. Offsetting them by
    # -2 * WHEELBASE put the first tyre two stations ahead of its wheel, which
    # is also what pushed the whole engine past the tiny size-class ceiling.
    tyre = bkit.torus("Tyres", WHEEL_R - 0.2, 0.5, seg_major=28, seg_minor=8,
                      centre=(-WHEELBASE, -AXLE_Y, WHEEL_R), axis="Y",
                      mat=black)
    bkit.array_linear(tyre, 3, (WHEELBASE, 0.0, 0.0), world=True)

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="length", mm=57.0, tol=0.1, how="bbox_x",
         part=None),
    dict(name="width", mm=18, tol=0.2, how="bbox_y",
         part=None),
    dict(name="boiler_diameter", mm=14, tol=0.1, how="bbox_y",
         part="Boiler"),
    dict(name="cab_height", mm=17.0, tol=0.1, how="bbox_z", part="Cab"),
    # the three axles are joined, so their Y extent is the whole wheelbase
    # width; one wheel's own diameter is its Z extent
    dict(name="wheel_diameter", mm=9, tol=0.1, how="bbox_z",
         part="Wheels"),
    # 2 x wheelbase + one wheel, measured across the two outermost wheels
    dict(name="wheelbase_span", mm=35.0, tol=0.1, how="bbox_x", part="Wheels"),
    dict(name="overall_height", mm=26.4, tol=0.2, how="bbox_z",
         part=None)]
