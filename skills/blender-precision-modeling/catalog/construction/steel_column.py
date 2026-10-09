"""
steel_column -- a 6 m square hollow section column, SHS 300 x 300 x 12,
with a welded base plate and cap plate.

The column itself is a hollow section, so the real geometry is two rings, not
one outline: `extrude_profile` gives the outer 300 x 300 block and a `bore`
removes the 276 x 276 void. The bore is coaxial with the section and is taken
with `bkit.bore`, which picks its own segment count, because a cutter sharing
the host's segment count puts coincident facets on both surfaces and the EXACT
solver answers that with non-manifold edges.

The plates are what tell you it is a COLUMN and not a length of tube: a 20 mm
base plate lapping the tube 10 mm so the weld has something to attach to, four
holding-down bolt holes bored through it, and a 16 mm cap plate on top.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _sections as S

SPEC = dict(
    length=6000.0,
    section=300.0,          # outside of the SHS
    wall=12.0,              # real wall thickness
    base_plate=420.0,
    base_thickness=20.0,
    cap_thickness=16.0,
    tube_length=5984.0,     # L - base_thickness - cap_thickness + 2 x 10 lap
    bolt_holes=4,
    bolt_pitch=340.0,
    bolt_dia=24.0,
)

L = SPEC["length"]
SEC = SPEC["section"]
WALL = SPEC["wall"]

BASE = SPEC["base_plate"]
BT = SPEC["base_thickness"]
CT = SPEC["cap_thickness"]

# the tube laps 10 mm into the base plate and the cap plate, so neither plate
# face is exactly tangent to the tube wall
TUBE_BOTTOM = BT - 10.0
TUBE_TOP = L - CT + 10.0

CHECKS = [
    dict(name="tube_length", mm=5984.0, tol=3.0, how="bbox_z", part="SteelColumn"),
    dict(name="section_width", mm=300.0, tol=0.6, how="bbox_x", part="SteelColumn"),
    dict(name="section_depth", mm=300.0, tol=0.6, how="bbox_y", part="SteelColumn"),
    dict(name="base_plate_width", mm=420.0, tol=1.0, how="bbox_x",
         part="SteelColumnBase"),
    dict(name="cap_plate_width", mm=420.0, tol=1.0, how="bbox_x",
         part="SteelColumnCap"),
    dict(name="overall_length", mm=6000.0, tol=6.0, how="bbox_z", part=None),
]


def build():
    paint = bkit.pbr("ColumnPaint", base=(0.36, 0.38, 0.40), metal=0.55,
                     rough=0.44)
    plate = bkit.preset("dark_metal")

    # ---- base plate, bored for the holding-down bolts ------------------
    base = bkit.box("SteelColumnBase", BASE, BASE, BT,
                    centre=(0.0, 0.0, BT / 2.0), mat=plate)
    bp = SPEC["bolt_pitch"]
    bd = SPEC["bolt_dia"]
    # bolt holes through the base plate: computed on the computed pitch, so the
    # count and the spacing can never disagree with each other
    for (x, y) in bkit.grid_positions(cols=2, rows=2, pitch_x=bp, pitch_y=bp):
        bkit.bore(base, bd / 2.0, BT * 3.0, centre=(x, y, BT / 2.0),
                  axis="Z", host_segments=64)

    # ---- the tube itself, hollowed ------------------------------------
    tube_h = TUBE_TOP - TUBE_BOTTOM
    tube = bkit.extrude_profile("SteelColumn", S.rhs_section(SEC, SEC, WALL),
                                tube_h,
                                centre=(0.0, 0.0, TUBE_BOTTOM + tube_h / 2.0),
                                axis="Z", mat=paint)
    inner = SEC - 2.0 * WALL
    bkit.bore(tube, inner / 2.0, tube_h + 4.0,
              centre=(0.0, 0.0, TUBE_BOTTOM + tube_h / 2.0), axis="Z",
              host_segments=64)

    # ---- cap plate ----------------------------------------------------
    bkit.box("SteelColumnCap", BASE, BASE, CT,
             centre=(0.0, 0.0, L - CT / 2.0), mat=plate)

    # ---- four stiffener ribs down the corners: what a real column has ---
    rib = 60.0
    off = SEC / 2.0 - WALL / 2.0
    for i, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        bkit.box("SteelColumnRib%d" % i, rib, rib, L - BT - CT - 20.0,
                 centre=(sx * (off + rib / 2.0 - 6.0),
                         sy * (off + rib / 2.0 - 6.0),
                         (TUBE_BOTTOM + TUBE_TOP) / 2.0), mat=paint)

    return dict(spec=SPEC, parts=3 + 4)