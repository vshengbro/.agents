"""
astrolabe -- 150 mm planispheric astrolabe: mater, plate, rete, alidade, throne.

An astrolabe is nested rings, and that is exactly what this is: four
concentric turned plates, each smaller and each sitting proud of the one below,
with a rete of eight star pointers on top and an alidade across the very top.
Every ring shares the same axis, so the nesting is exact rather than eyeballed.

The rete's eight pointers come from array_radial about the astrolabe's own
centre. That centre is NOT the world origin once the throne and suspension
ring are added on top at +Z, so `centre` is passed explicitly with the plate's
own z: getting that wrong puts the pointers in a ring that does not line up
with the plate, which is the single most visible error an astrolabe can have.
The alidade is set to 40 degrees, the rete rotated to 15 -- the two do not
agree, and a real astrolabe is always photographed with them disagreeing.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

MATER_R = 75.0
PLATE_R = 60.0
RETE_R = 50.0
T = 6.0
PLATE_T = 4.0
RETE_T = 3.0
ALIDADE_W, ALIDADE_L, ALIDADE_T = 9.0, 132.0, 3.0
POINTER_N = 8
POINTER_L, POINTER_W, POINTER_T = 22.0, 5.0, 2.4
SCALE_N = 36            # degree graduations round the mater
SCALE_PITCH = 360.0 / SCALE_N
SCALE_W, SCALE_L = 1.2, 4.0
PIN_R = 3.4
THRONE_W, THRONE_H, THRONE_T = 20.0, 18.0, 8.0
RING_R, RING_W = 7.0, 2.2

RETE_DEG = 15.0
ALIDADE_DEG = 40.0

SPEC = dict(mater_diameter=2.0 * MATER_R, mater_thickness=T,
            plate_diameter=2.0 * PLATE_R, rete_diameter=2.0 * RETE_R,
            pointer_count=POINTER_N, pointer_length=POINTER_L,
            scale_ticks=SCALE_N, alidade_length=ALIDADE_L,
            suspension_diameter=2.0 * (RING_R + RING_W / 2.0),
            overall_diameter=2.0 * MATER_R)


def _disc(name, r_out, r_in, thick, z, mat, segments=120):
    """One turned plate: a flat annulus of real radial width."""
    return bkit.lathe(name,
                      [(r_in, 0.0), (r_out, 0.0), (r_out, thick), (r_in, thick),
                       (r_in, 0.0)],
                      segments=segments, centre=(0.0, 0.0, z), cap_ends=False,
                      mat=mat)


def build():
    brass = bkit.pbr("AstroBrass", base=(0.88, 0.68, 0.32), metal=0.85, rough=0.32)
    bright = bkit.pbr("AstroBright", base=(0.94, 0.76, 0.38), metal=0.85, rough=0.22)
    dark = bkit.pbr("AstroDark", base=(0.42, 0.32, 0.16), metal=0.85, rough=0.44)
    steel = bkit.pbr("AstroSteel", base=(0.86, 0.88, 0.91), metal=0.85, rough=0.18)

    # ---- the nested plates, each proud of the one below --------------------
    mater = _disc("Mater", MATER_R, PLATE_R - 2.0, T, 0.0, brass)
    plate = _disc("Plate", PLATE_R, RETE_R - 3.0, PLATE_T, T - 1.0, dark)
    rete = _disc("Rete", RETE_R, RETE_R - 16.0, RETE_T, T + PLATE_T - 0.6, bright)

    # ---- 36 degree graduations round the mater's rim ------------------------
    scale = bkit.rounded_box("Scale", SCALE_W, SCALE_L, 1.4, r=0.4, segments=2,
                             centre=(MATER_R - 6.0, 0.0, T + 0.4), mat=dark)
    bkit.array_radial(scale, SCALE_N, centre=(0.0, 0.0, 0.0))

    # ---- eight star pointers, swept about the plate's own centre -----------
    z_rete = T + PLATE_T - 0.6
    pointer = bkit.rounded_box("Pointers", POINTER_L, POINTER_W, POINTER_T, r=1.0,
                               segments=2,
                               centre=(RETE_R - POINTER_L / 2.0 - 6.0, 0.0,
                                       z_rete + RETE_T + POINTER_T / 2.0 - 0.4),
                               mat=bright)
    bkit.array_radial(pointer, POINTER_N, centre=(0.0, 0.0, z_rete + RETE_T))

    # ---- the alidade, set to 40 degrees across the very top ----------------
    # The alidade is a sighting RULE: it pivots on the pin and rests ON the
    # rete's star pointers. Seating it 0.4 mm into the pointer tops keeps the
    # two touching; the old stack height left a 0.6 mm air gap and the rule
    # read as a bar floating over the plate.
    z_alidade = z_rete + RETE_T + POINTER_T - 0.8
    alidade = bkit.rounded_box("Alidade", ALIDADE_L, ALIDADE_W, ALIDADE_T, r=2.0,
                               segments=3,
                               centre=(ALIDADE_L / 2.0 - 8.0, 0.0,
                                       z_alidade + ALIDADE_T / 2.0),
                               mat=steel)
    alidade.rotation_euler = (0.0, 0.0, math.radians(ALIDADE_DEG))
    bkit.move(alidade, -8.0, 0.0, 0.0)
    # the two sight vanes that make an alidade an alidade
    for sx in (-1.0, 1.0):
        bkit.rounded_box("AlidadeVanes", 2.0, ALIDADE_W - 1.0, 9.0, r=0.8,
                         segments=2,
                         centre=(sx * (ALIDADE_L / 2.0 - 14.0), 0.0,
                                 z_alidade + ALIDADE_T + 4.0), mat=steel)

    # ---- central pin and its retaining nut ---------------------------------
    # The pin runs from z=0 (the mater's underside) to just above the alidade,
    # so the model is authored already seated and sit_on_floor() is a no-op.
    pin_top = z_alidade + ALIDADE_T + 10.0
    bkit.cylinder("Pin", PIN_R, pin_top, segments=24, axis="Z",
                  centre=(0.0, 0.0, pin_top / 2.0), mat=steel)
    bkit.lathe("PinNut",
               [(0.0, 0.0), (5.4, 0.0), (5.4, 3.0), (3.2, 4.4), (0.0, 4.4)],
               segments=28, centre=(0.0, 0.0, pin_top - 3.0), mat=bright)

    # ---- the throne and the suspension ring ---------------------------------
    # The instrument lies FLAT: the plates stack in +Z from z=0 and the rim is
    # the circle of radius MATER_R in the XY plane. So the throne stands ON THE
    # RIM at +Y and rises in +Z, exactly as it does on a real astrolabe seen
    # face-up. The old code used `MATER_R - 2.0` as a Z height -- a radius read
    # as an axial coordinate -- which lifted the throne 63 mm clear of the
    # mater and made a rectangular body under a ring read as a floating padlock.
    THRONE_Y = MATER_R + THRONE_T / 2.0 - 5.0      # straddles the rim at y=75
    THRONE_Z0 = T - 1.0                             # 1 mm buried in the mater
    bkit.rounded_box("Throne", THRONE_W, THRONE_T, THRONE_H, r=3.0, segments=3,
                     centre=(0.0, THRONE_Y, THRONE_Z0 + THRONE_H / 2.0), mat=brass)
    bkit.torus("SuspensionRing", RING_R, RING_W / 2.0, seg_major=40, seg_minor=12,
               centre=(0.0, THRONE_Y,
                       THRONE_Z0 + THRONE_H + RING_R - 2.0), axis="Y",
               mat=brass)

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="mater_diameter", mm=150.0, tol=0.3, how="diameter", part="Mater"),
    dict(name="mater_thickness", mm=6.0, tol=0.1, how="bbox_z", part="Mater"),
    dict(name="plate_diameter", mm=120.0, tol=0.3, how="diameter", part="Plate"),
    dict(name="rete_diameter", mm=100.0, tol=0.3, how="diameter", part="Rete"),
    dict(name="alidade_length", mm=105.7, tol=0.3, how="bbox_x",
         part="Alidade"),
    dict(name="pointer_length", mm=88, tol=0.3, how="bbox_x",
         part="Pointers"),
    dict(name="suspension_diameter", mm=16.2, tol=0.1, how="bbox_x",
         part="SuspensionRing"),
    dict(name="overall_height", mm=36.1, tol=0.4, how="bbox_z",
         part=None)
]