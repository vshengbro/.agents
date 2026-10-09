"""
vacuum_cleaner -- 500 x 300 x 1050 mm upright vacuum cleaner: a moulded floor
head on two wheels, a lathed dust cup with a hinged lid, a metal wand, a wide
handle yoke, and a ribbed hose stub behind the head.

The upright silhouette -- low head, tall column, loop handle -- is the whole
identity; the parts have to stack in that order.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    head_width=500.0,
    head_depth=300.0,
    head_height=200.0,
    overall_height=1050.0,
    corner_radius=30.0,
    wheel_diameter=90.0,
    cup_diameter=200.0,
    cup_height=300.0,
    wand_diameter=52.0,
    handle_reach=110.0,
    handle_tube=15.0,
    yoke_width=260.0,
)

HW = SPEC["head_width"]
HD = SPEC["head_depth"]
HH = SPEC["head_height"]
OH = SPEC["overall_height"]
WR = SPEC["wheel_diameter"] / 2.0
CR = SPEC["cup_diameter"] / 2.0
CH = SPEC["cup_height"]
WAND_R = SPEC["wand_diameter"] / 2.0
CUP_Z = HH - 10.0
# The yoke height is derived, not chosen: the crown of a reach+tube arc centred
# here lands exactly on overall_height.
YOKE_Z = OH - SPEC["handle_reach"] - SPEC["handle_tube"]
WAND_BOT = CUP_Z + CH - 10.0
WAND_TOP = YOKE_Z - 12.0


def build():
    shell = bkit.pbr("VacuumShell", base=(0.34, 0.36, 0.42), metal=0.0, rough=0.30,
                     coat=0.25)
    dark = bkit.preset("black_plastic")
    rubber = bkit.preset("rubber")
    # The cup was 0.72 base with coat 0.4 and no transmission, so it rendered as
    # an opaque pale cylinder indistinguishable from the shell. A real cyclonic
    # dust bin is clear plastic you can see the dirt through: partial
    # transmission plus a little self-emission makes it read as a transparent
    # canister against the dark studio instead of another grey cylinder.
    clear = bkit.pbr("VacuumCup", base=(0.86, 0.90, 0.94), rough=0.10,
                     transmission=0.55, ior=1.46, coat=0.5,
                     emission=(0.70, 0.76, 0.82), emission_strength=0.25)
    steel = bkit.preset("brushed_metal")

    # ---- floor head -------------------------------------------------------
    bkit.rounded_box("VacuumHead", HW, HD, HH, r=SPEC["corner_radius"],
                     segments=6, centre=(0.0, 0.0, HH / 2.0), mat=shell)
    # The sole plate is where the floor clearance is made; without it the head
    # reads as a block floating above the studio floor.
    bkit.rounded_box("SolePlate", HW - 26.0, HD - 30.0, 14.0, r=8.0, segments=3,
                     centre=(0.0, 0.0, 7.0), mat=dark)

    # The wheels were at x = +-216, i.e. INSIDE a 500 mm wide head whose own half
    # width is 250, and at z = 45 inside a head that stands 200 mm tall on the
    # floor. Both wheels were completely swallowed by the shell, so the machine
    # read as a box on a stick. They now stand proud of each side at the rear
    # corner, where the wheel face is actually visible.
    for ix, sx in ((0, -1.0), (1, 1.0)):
        bkit.cylinder("Wheel%d" % ix, WR, 34.0, segments=48, axis="X",
                      centre=(sx * (HW / 2.0 + 9.0), HD / 2.0 - 40.0, WR),
                      mat=rubber)
        # a hub cap, so the wheel reads as a wheel and not a black stub
        bkit.cylinder("WheelHub%d" % ix, WR * 0.42, 6.0, segments=24, axis="X",
                      centre=(sx * (HW / 2.0 + 28.0), HD / 2.0 - 40.0, WR),
                      mat=steel)

    # ---- dust cup ---------------------------------------------------------
    bkit.lathe("DustCup",
               [(0.0, 0.0), (CR - 12.0, 0.0), (CR, 12.0), (CR, CH - 20.0),
                (CR - 8.0, CH), (CR - 14.0, CH), (CR - 16.0, CH - 22.0),
                (CR - 6.0, 14.0), (0.0, 10.0)],
               segments=96, centre=(0.0, 0.0, CUP_Z), mat=clear)
    bkit.lathe("CupLid",
               [(0.0, 0.0), (CR - 6.0, 0.0), (CR + 2.0, 4.0), (CR + 2.0, 16.0),
                (CR - 10.0, 24.0), (40.0, 28.0), (0.0, 29.0)],
               segments=96, centre=(0.0, 0.0, CUP_Z + CH - 8.0), mat=shell)
    bkit.cylinder("ReleaseButton", 22.0, 18.0, segments=32,
                  centre=(0.0, -(CR + 8.0), CUP_Z + CH - 4.0), mat=dark)

    # ---- wand and handle yoke ---------------------------------------------
    bkit.cylinder("Wand", WAND_R, WAND_TOP - WAND_BOT, segments=48,
                  centre=(0.0, 0.0, (WAND_BOT + WAND_TOP) / 2.0), mat=steel)
    bkit.rounded_box("HandleYoke", 62.0, SPEC["yoke_width"], 46.0, r=14.0,
                     segments=4, centre=(0.0, 0.0, YOKE_Z), mat=shell)
    # A 0..180 deg arc is a yoke, not an arch: its two tips land at the same
    # height on opposite sides and disappear into the yoke block.
    bkit.arc_torus("HandleLoop", SPEC["handle_reach"], SPEC["handle_tube"],
                   0.0, 180.0, centre=(0.0, 0.0, YOKE_Z), plane="YZ",
                   seg_major=56, mat=dark, caps=True)

    # ---- ribbed hose stub behind the head ---------------------------------
    bkit.cylinder("HoseStub", 34.0, 130.0, segments=32, axis="Y",
                  centre=(0.0, HD / 2.0 + 30.0, 96.0), mat=dark)
    for i in range(5):
        bkit.tube("HoseRib%d" % i, 40.0, 30.0, 10.0, segments=32, axis="Y",
                  centre=(0.0, HD / 2.0 + 4.0 + i * 24.0, 96.0), mat=dark)

    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="head_width", mm=500.0, tol=0.5, how="bbox_x", part="VacuumHead"),
    dict(name="head_depth", mm=300.0, tol=0.5, how="bbox_y", part="VacuumHead"),
    dict(name="head_height", mm=200.0, tol=0.5, how="bbox_z", part="VacuumHead"),
    dict(name="overall_height", mm=1050.0, tol=0.8, how="bbox_z"),
    # overall_width moved 500 -> 552 mm: the wheels now stand 9 mm proud of each
    # side plus their own 34 mm width, so the machine's widest dimension is the
    # track over the shell, not the shell itself.
    dict(name="overall_width", mm=562.0, tol=1.0, how="bbox_x"),
    dict(name="wheel_diameter", mm=90.0, tol=0.4, how="diameter", part="Wheel0"),
]