"""
binoculars -- 152 x 136 mm 10x42 roof binocular: two barrels on a centre bridge,
72 mm objective bells with recessed glass, a side focus wheel, a dioptre ring
and two soft eyecups.

Both barrels are `lathe` solids offset in X rather than mirrored copies: the
right-hand stack is built from the same helper as the left, so the two sides
cannot drift apart by a millimetre the way a hand-placed duplicate would.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    overall_height=152.0,
    overall_width=136.0,
    barrel_diameter=38.0,
    objective_bell_diameter=72.0,
    objective_glass_diameter=60.0,
    eyecup_diameter=42.0,
)

BARREL_X = 32.0          # half the interpupillary distance
BELL_R = SPEC["objective_bell_diameter"] / 2.0


def _barrel(side, black, glass):
    """One complete optical barrel. `side` is -1 (left) or +1 (right)."""
    sx = side * BARREL_X
    tag = "L" if side < 0 else "R"
    parts = []
    # NOTE: lathe profiles carry ABSOLUTE z; only x/y are passed as `centre`.
    # bkit.lathe does not normalise about its origin the way cylinder/tube do,
    # so an absolute profile PLUS a z centre measures double height.
    parts.append(bkit.lathe(
        "Barrel" + tag,
        [(0.0, 8.0), (19.0, 8.0), (19.0, 130.0), (0.0, 130.0)],
        segments=56, centre=(sx, 0.0, 0.0), mat=black))
    # Objective bell is a genuine tube -- 30 mm bore, so the glass inside it
    # is visible instead of buried in a solid revolve.
    parts.append(bkit.tube(
        "ObjectiveBell" + tag, BELL_R, 30.0, 22.0, segments=56,
        centre=(sx, 0.0, 141.0), mat=black))
    parts.append(bkit.lathe(
        "ObjectiveGlass" + tag,
        [(0.0, 143.0), (30.0, 143.0), (30.0, 148.0), (0.0, 148.0)],
        segments=56, centre=(sx, 0.0, 0.0), mat=glass))
    parts.append(bkit.lathe(
        "Eyecup" + tag,
        [(0.0, 0.0), (21.0, 0.0), (21.0, 9.0), (17.0, 12.0), (17.0, 17.0),
         (0.0, 17.0)], segments=56, centre=(sx, 0.0, 0.0),
        mat=bkit.pbr("BinoCup", base=(0.075, 0.075, 0.080), rough=0.80)))
    parts.append(bkit.tube(
        "DioptreRing" + tag, 21.0, 17.5, 13.0, segments=56,
        centre=(sx, 0.0, 26.0), mat=black))
    return parts


def build():
    black = bkit.pbr("BinoBlack", base=(0.060, 0.060, 0.065), rough=0.36)
    glass = bkit.pbr("BinoGlass", base=(0.17, 0.28, 0.42), metal=0.35,
                     rough=0.04)
    body = bkit.pbr("BinoBody", base=(0.14, 0.145, 0.155), rough=0.44)

    left = _barrel(-1, black, glass)
    right = _barrel(1, black, glass)

    # ---- centre bridge: overlaps each barrel by 9 mm, never flush ---------
    bkit.rounded_box("BinocularBridge", 44.0, 40.0, 74.0, r=10.0, segments=4,
                     centre=(0.0, 0.0, 100.0), mat=body)

    # ---- side focus wheel, 18 knurl ribs. Assembled at the ORIGIN with its
    # axis on Y, then moved -- array_radial orbits the world origin, so a wheel
    # built in place would throw its ribs around the middle of the binoculars.
    wheel = bkit.cylinder("_wheel", 13.0, 14.0, segments=40, axis="Y", mat=black)
    # No rotation on the rib: with the wheel already on Y, a box at +Z is
    # already oriented radially, so the 18-way sweep about Y lands a clean ring.
    # Rotating the rib before the sweep would also stale matrix_world, which is
    # what array_radial reads for its pivot.
    tooth = bkit.box("_tooth", 2.2, 12.0, 1.6, centre=(0.0, 0.0, 13.6),
                     mat=black)
    bkit.array_radial(tooth, count=18, axis="Y")
    bkit.move(bkit.join([wheel, tooth], name="FocusWheel"), 0.0, 24.0, 100.0)

    # ---- hinge barrel joining the two halves at the top -----------------
    bkit.cylinder("HingePin", 7.0, 56.0, segments=24,
                  centre=(0.0, 0.0, 136.0), axis="X", mat=black)

    # ---- neck-strap lugs -------------------------------------------------
    for side in (-1.0, 1.0):
        bkit.torus("StrapLug" + ("L" if side < 0 else "R"), 6.0, 1.8,
                   seg_major=28, seg_minor=10, axis="X",
                   centre=(side * 23.0, 0.0, 128.0), mat=black)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=len(left) + len(right) + 5)


CHECKS = [
    dict(name="overall_height", mm=152.0, tol=0.6, how="bbox_z"),
    dict(name="overall_width", mm=136.0, tol=0.6, how="bbox_x"),
    dict(name="objective_bell_diameter", mm=72.0, tol=0.5, how="diameter",
         part="ObjectiveBellL"),
    dict(name="barrel_diameter", mm=38.0, tol=0.5, how="diameter",
         part="BarrelL"),
    dict(name="eyecup_diameter", mm=42.0, tol=0.5, how="diameter",
         part="EyecupL"),
]