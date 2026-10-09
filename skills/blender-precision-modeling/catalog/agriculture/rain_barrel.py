"""
rain_barrel -- a 900 mm water butt: corrugated barrel, lid, tap, inlet.

A water butt is a fat cylinder, and the three things that stop it reading as a
plain drum are the corrugation hoops, the tap and the overflow. The hoops are
the same trick as the silo's and are best done IN THE LATHE PROFILE, so the
corrugation is part of one closed solid.

    barrel     580 mm dia, 900 tall, 8 rolled hoops at 100 mm pitch
    wall       8 mm, so it is a real closed shell, not a solid cylinder
    lid        a hinged flat lid overhanging the barrel by 15 mm
    tap        a 1/2" brass tap with a lever handle, 220 mm above the ground
    inlet      a screen over the top, and an overflow at the top rim

The tap is at 220 mm because that is a real tap height on a water butt -- low
enough to put a watering can under it, which is the whole purpose of the object.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    barrel_dia=580.0,
    barrel_height=900.0,
    wall=8.0,
    hoops=8,
    hoop_depth=18.0,
    lid_thickness=20.0,
    tap_height=220.0,
    tap_bore=16.0,
    inlet_screen_dia=220.0,
    overflow_dia=40.0,
)

D = SPEC["barrel_dia"]
RB = D / 2.0
H = SPEC["barrel_height"]
WALL = SPEC["wall"]
NH = SPEC["hoops"]
HD = SPEC["hoop_depth"]

# ---- the closed lathe profile: outer skin, hoops, inner wall, closed loop ----
# The profile is walked UP the outside, across the lid seat, back DOWN the inside
# and then to the start, which makes the swept surface a closed tube.
PROF = []
n_hoop_steps = NH * 2
for i in range(n_hoop_steps + 1):
    z = H * i / float(n_hoop_steps)
    r = RB + (HD if i % 2 == 0 else 0.0)
    PROF.append((r, z))
PROF.append((RB - WALL, H))
for i in range(n_hoop_steps, -1, -1):
    z = H * i / float(n_hoop_steps)
    PROF.append((RB - WALL, z))
PROF.append(PROF[0])

CHECKS = [
    dict(name="barrel_dia", mm=616.0, tol=4.0, how="diameter", part="ButtBarrel"),
    dict(name="barrel_height", mm=900.0, tol=4.0, how="bbox_z", part="ButtBarrel"),
    dict(name="lid_dia", mm=610.0, tol=4.0, how="diameter", part="ButtLid"),
    dict(name="tap_height", mm=200.0, tol=4.0, how="bottom_z", part="ButtTap"),
    dict(name="tap_spout_dia", mm=40.0, tol=2.0, how="bbox_z", part="ButtTap"),
    dict(name="overall_height", mm=960.0, tol=4.0, how="bbox_z", part=None),
]


def build():
    plastic = bkit.pbr("ButtPlastic", base=(0.24, 0.34, 0.28), rough=0.46)
    lid_mat = bkit.pbr("ButtLid", base=(0.20, 0.30, 0.24), rough=0.40)
    brass = bkit.preset("brass") if False else bkit.preset("gold")

    barrel = bkit.lathe("ButtBarrel", PROF, segments=48, centre=(0.0, 0.0, 0.0),
                        mat=plastic, cap_ends=False)
    bkit.recalc(barrel)
    bkit.weld(barrel)

    # ---- the hinged lid, overhanging the barrel ---------------------
    bkit.cylinder("ButtLid", RB + 15.0, SPEC["lid_thickness"], segments=48,
                  centre=(0.0, 0.0, H + SPEC["lid_thickness"] / 2.0),
                  mat=lid_mat)
    bkit.cylinder("ButtLidKnob", 26.0, 40.0, segments=16,
                  centre=(0.0, 0.0, H + SPEC["lid_thickness"] + 20.0),
                  mat=lid_mat)

    # ---- the inlet screen over the top ------------------------------
    bkit.tube("ButtInletScreen", SPEC["inlet_screen_dia"] / 2.0,
              SPEC["inlet_screen_dia"] / 2.0 - 6.0, 40.0, segments=24,
              axis="Z", centre=(0.0, 0.0, H + 20.0), mat=bkit.preset("dark_metal"))

    # ---- the overflow at the top rim --------------------------------
    bkit.tube("ButtOverflow", SPEC["overflow_dia"] / 2.0,
              SPEC["overflow_dia"] / 2.0 - 3.0, 90.0, segments=16, axis="Z",
              centre=(RB - 10.0, 0.0, H - 45.0), mat=plastic)

    # ---- the tap: a real bored spout, 220 mm above the floor --------
    # The spout points OUT and is bored through, so it reads as a tap and not a
    # peg. `bore` picks its own cutter segment count -- a cutter sharing the
    # host's count puts coincident facets on both surfaces.
    spout = bkit.cylinder("ButtTap", 20.0, 120.0, segments=24, axis="X",
                          centre=(RB + 40.0, 0.0, SPEC["tap_height"]), mat=brass)
    bkit.bore(spout, SPEC["tap_bore"] / 2.0, 200.0,
              centre=(RB + 40.0, 0.0, SPEC["tap_height"]), axis="X",
              host_segments=64)
    # the elbow down to the barrel wall, and the lever handle on top
    bkit.cylinder("ButtTapElbow", 20.0, 60.0, segments=24, axis="Z",
                  centre=(RB + 40.0, 0.0, SPEC["tap_height"] + 20.0), mat=brass)
    bkit.rounded_box("ButtTapHandle", 16.0, 90.0, 12.0, r=5.0, segments=1,
                     centre=(RB + 40.0, 0.0, SPEC["tap_height"] + 56.0),
                     mat=brass)

    return dict(spec=SPEC, parts=6, hoops=NH)