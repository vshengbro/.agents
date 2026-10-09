"""
hinge -- 50 mm butt hinge, closed, with a 5-knuckle barrel and a headed pin.

A closed butt hinge is two leaves lying in one plane, split by the barrel that
runs along the joint line. The barrel is wider than the leaves (7 mm barrel
against a 2.5 mm leaf) and the leaves' edges disappear into it, which is exactly
how the knuckle and leaf are one pressing in reality -- so the leaves are built
to end at y = 0 and the knuckle tubes straddle that line.

The five knuckles are laid out with bkit.lay_out() rather than hand-placed: the
knuckle lengths (8, 9, 8 mm) plus one explicit 8.5 mm gap give the barrel a
42 mm span centred on the 50 mm leaf, so both leaves keep a 4 mm margin and the
hinge is symmetric by construction.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

LEAF_LENGTH = 50.0      # X, ISO 1124-1 size 50
LEAF_WIDTH = 25.0       # Y, half of the 50 mm open width
LEAF_THICKNESS = 2.5    # Z, sheet thickness
BARREL_OD = 7.0         # knuckle outside diameter
PIN_D = 3.9             # pin diameter
KNUCKLES = [8.0, 9.0, 8.0]   # the two outer knuckles belong to leaf A
KNUCKLE_GAP = 8.5
HOLE_D = 4.2            # countersunk screw clearance

SPEC = dict(leaf_length=LEAF_LENGTH,
            leaf_width=LEAF_WIDTH,
            leaf_thickness=LEAF_THICKNESS,
            barrel_diameter=BARREL_OD,
            pin_diameter=PIN_D,
            knuckle_count=len(KNUCKLES))


def build():
    steel = bkit.pbr("HingeSteel", base=(0.72, 0.74, 0.77), metal=0.70,
                     rough=0.30)

    # ---- leaves, each with two screw holes -----------------------------
    hole_x = LEAF_LENGTH / 2.0 - 6.5
    for name, sign in (("LeafA", -1.0), ("LeafB", 1.0)):
        leaf = bkit.rounded_box(name, LEAF_LENGTH, LEAF_WIDTH, LEAF_THICKNESS,
                                r=0.6, segments=3,
                                centre=(0.0, sign * LEAF_WIDTH / 2.0, 0.0),
                                mat=steel)
        for hx in (-hole_x, hole_x):
            cutter = bkit.cylinder(name + "_hole", HOLE_D / 2.0,
                                   LEAF_THICKNESS * 3.0, segments=24,
                                   centre=(hx, sign * LEAF_WIDTH / 2.0, 0.0),
                                   mat=None)
            bkit.boolean(leaf, cutter, "DIFFERENCE")

    # ---- knuckles on a measured layout ---------------------------------
    positions = bkit.lay_out(KNUCKLES, gap=KNUCKLE_GAP)
    knuckles = []
    for i, (x, width) in enumerate(positions):
        knuckles.append(bkit.tube("Knuckle%d" % i, BARREL_OD / 2.0,
                                  PIN_D / 2.0, width, segments=48,
                                  centre=(x, 0.0, 0.0), axis="X", mat=steel))
    bkit.join(knuckles, name="Barrel")

    # ---- pin: plain shaft with a riveted head at one end ----------------
    pin = bkit.cylinder("Pin", PIN_D / 2.0, 52.0, segments=40,
                        centre=(0.4, 0.0, 0.0), axis="X", mat=steel)
    head = bkit.cylinder("PinHead", 3.4, 2.0, segments=40,
                         centre=(-26.6, 0.0, 0.0), axis="X", mat=steel)
    bkit.join([pin, head], name="Pin")

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="leaf_length", mm=50.0, tol=0.05, how="bbox_x", part="LeafA"),
    dict(name="leaf_width", mm=25.0, tol=0.05, how="bbox_y", part="LeafA"),
    dict(name="leaf_thickness", mm=2.5, tol=0.05, how="bbox_z", part="LeafA"),
    dict(name="barrel_diameter", mm=7.0, tol=0.05, how="bbox_z", part="Barrel"),
    dict(name="overall_length", mm=54.0, tol=0.05, how="bbox_x", part=None),
]