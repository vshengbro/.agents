"""
grandfather_clock -- 2000 x 460 x 300 mm longcase clock with pendulum and weights.

A longcase clock is a plinth, a trunk and a hood, and the two things that make
it a longcase clock rather than a wall clock are the visible pendulum and the
pair of weights -- so both are modelled, hanging on real rods inside the
trunk's glazed door, and both are what a viewer checks first.

The dial is a real dial: a chapter ring, twelve markers swept about the dial's
own centre, and two hands set to 10:09 the way every clock catalogue is
photographed. The pendulum hangs from the hood's underside and its bob swings
clear of the weights, so the three moving masses are at three different depths
in Y and read as three separate objects.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

W, D, H = 460.0, 300.0, 2000.0
PLINTH_H = 220.0
TRUNK_W, TRUNK_D, TRUNK_H = 400.0, 250.0, 1180.0
HOOD_H = 600.0
DIAL_R = 128.0
DIAL_Y = -D / 2.0 - 6.0        # the dial stands PROUD of the hood's front face
DIAL_Z = H - HOOD_H / 2.0
MARK_N = 12
HAND_L = 96.0
ROD_R = 4.0
PEND_R = 6.0
PEND_L = 620.0
BOB_R = 72.0
BOB_T = 14.0
WEIGHT_R = 26.0
WEIGHT_H = 150.0
WEIGHT_DROP = 520.0
FINIAL_H = 70.0

HOUR, MINUTE = 10, 9
MIN_ANG = 90.0 - MINUTE * 6.0
HOUR_ANG = 90.0 - (HOUR % 12) * 30.0 - MINUTE * 0.5

SPEC = dict(width=W, depth=D, height=H, plinth_height=PLINTH_H,
            trunk_height=TRUNK_H, hood_height=HOOD_H,
            dial_diameter=2.0 * DIAL_R, marker_count=MARK_N,
            pendulum_length=PEND_L, bob_diameter=2.0 * BOB_R,
            weight_diameter=2.0 * WEIGHT_R, weight_drop=WEIGHT_DROP)


def build():
    mahogany = bkit.pbr("ClockMahogany", base=(0.24, 0.10, 0.055), metal=0.0,
                        rough=0.38, coat=0.4)
    gold = bkit.pbr("ClockGold", base=(0.95, 0.76, 0.32), metal=0.85, rough=0.20)
    enamel = bkit.pbr("ClockEnamel", base=(0.93, 0.91, 0.85), metal=0.0, rough=0.20,
                      coat=0.6)
    steel = bkit.pbr("ClockSteel", base=(0.82, 0.84, 0.87), metal=0.85, rough=0.18)
    brass = bkit.pbr("ClockBrass", base=(0.90, 0.70, 0.32), metal=0.85, rough=0.26)
    glass = bkit.pbr("ClockGlass", base=(0.86, 0.90, 0.94), metal=0.0, rough=0.05,
                     transmission=0.5, ior=1.5)

    # ---- the case: plinth, trunk, hood --------------------------------------
    plinth = bkit.rounded_box("Plinth", W, D, PLINTH_H, r=6.0, segments=3,
                              centre=(0.0, 0.0, PLINTH_H / 2.0), mat=mahogany)
    trunk = bkit.rounded_box("Trunk", TRUNK_W, TRUNK_D, TRUNK_H, r=5.0, segments=3,
                             centre=(0.0, 0.0, PLINTH_H + TRUNK_H / 2.0),
                             mat=mahogany)
    hood = bkit.rounded_box("Hood", W, D, HOOD_H, r=8.0, segments=3,
                            centre=(0.0, 0.0, H - HOOD_H / 2.0), mat=mahogany)
    # swan-neck pediment: two arcs meeting at the centre finial
    pediment = []
    for sx in (-1.0, 1.0):
        pediment.append(bkit.arc_torus(
            "Pediment", 150.0, 22.0, 0.0, 74.0, plane="XZ", seg_major=40,
            seg_minor=14, centre=(sx * 80.0, 0.0, H - 40.0), mat=mahogany,
            caps=True))
    bkit.join(pediment, name="Pediment")
    finial = bkit.lathe(
        "Finial",
        [(0.0, 0.0), (16.0, 4.0), (20.0, 18.0), (12.0, 34.0), (16.0, 46.0),
         (6.0, 58.0), (0.0, FINIAL_H)],
        segments=40, centre=(0.0, 0.0, H - 30.0), mat=gold)

    # ---- the dial -------------------------------------------------------------
    dial = bkit.lathe(
        "Dial",
        [(0.0, -6.0), (DIAL_R, -6.0), (DIAL_R, 6.0), (DIAL_R - 14.0, 9.0),
         (0.0, 9.0)],
        segments=80, mat=enamel)
    dial.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(dial, 0.0, DIAL_Y, DIAL_Z)
    chapter = bkit.torus("ChapterRing", DIAL_R - 20.0, 5.0, seg_major=80,
                         seg_minor=12, centre=(0.0, DIAL_Y - 6.0, DIAL_Z),
                         axis="Y", mat=gold)
    # twelve markers swept about the dial's own centre
    mark = bkit.rounded_box("Markers", 9.0, 4.0, 34.0, r=2.0, segments=2,
                            centre=(0.0, DIAL_Y - 11.0, DIAL_Z + DIAL_R - 32.0),
                            mat=gold)
    bkit.array_radial(mark, MARK_N, axis="Y", centre=(0.0, DIAL_Y, DIAL_Z))

    hour = bkit.rounded_box("HourHand", 64.0, 4.0, 11.0, r=3.0, segments=2,
                            centre=(32.0, 0.0, 0.0), mat=steel)
    hour.rotation_euler = (0.0, 0.0, math.radians(HOUR_ANG))
    bkit.move(hour, 0.0, DIAL_Y - 14.0, DIAL_Z)
    minute = bkit.rounded_box("MinuteHand", HAND_L, 3.2, 8.0, r=2.4, segments=2,
                              centre=(HAND_L / 2.0, 0.0, 0.0), mat=steel)
    minute.rotation_euler = (0.0, 0.0, math.radians(MIN_ANG))
    bkit.move(minute, 0.0, DIAL_Y - 17.0, DIAL_Z)
    cap = bkit.cylinder("HandCap", 10.0, 8.0, segments=24,
                        centre=(0.0, DIAL_Y - 20.0, DIAL_Z), axis="Y", mat=gold)

    # ---- pendulum ---------------------------------------------------------------
    pend_top = H - HOOD_H + 30.0
    pend_z = pend_top - PEND_L / 2.0
    rod = bkit.cylinder("PendulumRod", ROD_R, PEND_L, segments=16,
                        centre=(0.0, 0.0, pend_z), mat=steel)
    bob = bkit.lathe(
        "PendulumBob",
        [(0.0, -BOB_T / 2.0), (BOB_R, -BOB_T / 2.0), (BOB_R, BOB_T / 2.0),
         (0.0, BOB_T / 2.0)],
        segments=64, mat=brass)
    bob.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(bob, 0.0, -20.0, pend_top - PEND_L + BOB_R * 0.5)

    # ---- two weights, at two depths, clear of the pendulum ----------------------
    weights, wrods = [], []
    for (sx, wy) in ((-1.0, 30.0), (1.0, 30.0)):
        wrods.append(bkit.cylinder("WeightRods", 2.6, WEIGHT_DROP + WEIGHT_H,
                                   segments=12,
                                   centre=(sx * 108.0, wy,
                                           H - HOOD_H - (WEIGHT_DROP + WEIGHT_H) / 2.0),
                                   mat=steel))
        weights.append(bkit.lathe(
            "Weights",
            [(0.0, 0.0), (WEIGHT_R - 4.0, 0.0), (WEIGHT_R, 4.0),
             (WEIGHT_R, WEIGHT_H - 4.0), (WEIGHT_R - 4.0, WEIGHT_H), (0.0, WEIGHT_H)],
            segments=40,
            centre=(sx * 108.0, wy, H - HOOD_H - WEIGHT_DROP - WEIGHT_H),
            mat=brass))
    bkit.join(wrods, name="WeightRods")
    bkit.join(weights, name="Weights")

    # ---- glazed trunk door ------------------------------------------------------
    # The trunk is a SOLID box by default, so a pendulum and two weights built
    # inside it are invisible in every render: a transmissive glass panel in
    # front of a dark interior renders near-black in this studio. So the trunk
    # gets a real aperture cut clean through it, the pendulum and weights hang
    # in the opening, and a separate back panel closes the case.
    aperture = bkit.rounded_box("_aperture", TRUNK_W - 70.0, 4.0 * TRUNK_D,
                                TRUNK_H - 150.0, r=4.0, segments=2,
                                centre=(0.0, 0.0, PLINTH_H + TRUNK_H / 2.0))
    bkit.boolean(trunk, aperture, "DIFFERENCE")
    back = bkit.rounded_box("TrunkBack", TRUNK_W - 60.0, 10.0, TRUNK_H - 140.0,
                            r=3.0, segments=2,
                            centre=(0.0, TRUNK_D / 2.0 - 10.0,
                                    PLINTH_H + TRUNK_H / 2.0), mat=mahogany)
    surround = bkit.rounded_box("DoorSurround", TRUNK_W - 40.0, 12.0,
                                TRUNK_H - 120.0, r=4.0, segments=2,
                                centre=(0.0, -TRUNK_D / 2.0 + 4.0,
                                        PLINTH_H + TRUNK_H / 2.0), mat=mahogany)
    bkit.boolean(surround, bkit.rounded_box("_win", TRUNK_W - 70.0, 30.0,
                                            TRUNK_H - 150.0, r=4.0, segments=2,
                                            centre=(0.0, -TRUNK_D / 2.0 + 4.0,
                                                    PLINTH_H + TRUNK_H / 2.0)),
                 "DIFFERENCE")
    surround.name = "DoorSurround"

    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="width", mm=460.0, tol=0.4, how="bbox_x", part="Plinth"),
    dict(name="depth", mm=300.0, tol=0.4, how="bbox_y", part="Plinth"),
    dict(name="plinth_height", mm=220.0, tol=0.3, how="bbox_z", part="Plinth"),
    dict(name="trunk_height", mm=1180.0, tol=0.4, how="bbox_z", part="Trunk"),
    dict(name="hood_height", mm=600.0, tol=0.3, how="bbox_z", part="Hood"),
    dict(name="dial_diameter", mm=256.0, tol=0.4, how="diameter", part="Dial"),
    dict(name="pendulum_length", mm=620.0, tol=0.3, how="bbox_z", part="PendulumRod"),
    dict(name="bob_diameter", mm=144.0, tol=0.3, how="diameter", part="PendulumBob"),
    dict(name="weight_height", mm=150.0, tol=0.3, how="bbox_z", part="Weights")
]