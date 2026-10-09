"""
anchor -- 290 mm stockless fisherman's anchor, 280 x 200 x 165 mm.

A Hall anchor is five parts and the geometry of two of them does all the work:
a shank straight down the centre, and a pair of ARCS that sweep up and out of
the crown to the fluke tips -- the fluke angle is what stops the anchor
tripping under load, and an arc is the only honest way to draw it. Each fluke
is an extruded curved plate. Two traps this file exists to record: the fluke
outline must be wound COUNTER-CLOCKWISE (up the trailing edge, back down the
leading one) or `extrude_profile` returns a solid with inward normals, and the
second fluke is a `duplicate` of the first, never a mirror -- the outline is
already symmetric about Y, so a mirror lands the copy exactly on the original
and quadruples every face.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vessel as V

SPEC = dict(
    head_top_z=273.0,
    shank_length=190.0,
    arm_reach=76.0,
    fluke_span=96.0,
    crown_width=176.0,
    stock_width=200.0,
    head_ring_diameter=66.0,
)

CHECKS = [
    dict(name="head_top_z", mm=273.0, tol=8.0, how="top_z",
         part="AnchorRing"),
    dict(name="shank_length", mm=190.0, tol=3.0, how="bbox_z",
         part="AnchorShank"),
    dict(name="crown_width", mm=176.0, tol=3.0, how="bbox_y",
         part="AnchorCrown"),
    dict(name="fluke_span", mm=96.0, tol=4.0, how="bbox_x",
         part="AnchorFluke0"),
    dict(name="stock_width", mm=200.0, tol=3.0, how="bbox_y",
         part="AnchorStock"),
    dict(name="head_ring", mm=66.0, tol=3.0, how="diameter",
         part="AnchorRing"),
]

Y_FLUKE = 36.0            # half the distance between the two flukes


def _edge(t):
    """One point of the fluke spine: forward and up, chord growing to the tip."""
    x = -20.0 + 96.0 * t
    z = 44.0 + 40.0 * (t ** 1.7)
    c = 100.0 * (0.30 + 0.70 * math.sin(math.pi * min(1.0, t * 1.12 + 0.05)))
    return x, z, c


def fluke_profile():
    """The digging blade, wound counter-clockwise so the extrusion is solid.

    Runs forward along the LOWER edge and back along the upper one. The 13 mm
    extrusion is real thickness: an `extrude_profile` cut, not two boxes
    pretending to be a blade.
    """
    n = 12
    pts = []
    for i in range(n + 1):
        x, z, c = _edge(i / float(n))
        pts.append((x, z - c * 0.5))
    for i in range(n, -1, -1):
        x, z, c = _edge(i / float(n))
        pts.append((x, z + c * 0.5))
    return pts


def build():
    steel = bkit.pbr("AnchorSteel", base=(0.34, 0.35, 0.37), metal=0.80,
                     rough=0.44)
    rust = bkit.pbr("AnchorRust", base=(0.33, 0.21, 0.13), metal=0.55,
                    rough=0.62)

    bkit.cylinder("AnchorShank", 11.0, 190.0, r2=9.0, segments=24, axis="Z",
                  centre=(0.0, 0.0, 125.0), mat=steel)
    bkit.torus("AnchorRing", 22.0, 11.0, seg_major=40, seg_minor=14,
               centre=(0.0, 0.0, 240.0), axis="Y", mat=steel)
    bkit.lathe("AnchorHead", [(0.0, 208.0), (15.0, 208.0), (17.0, 232.0),
                              (0.0, 232.0)], segments=24, mat=steel)

    bkit.rounded_box("AnchorCrown", 46.0, 176.0, 30.0, r=12.0, segments=2,
                     centre=(0.0, 0.0, 15.0), mat=steel)
    bkit.lathe("AnchorStockBoss", [(0.0, 26.0), (20.0, 26.0), (20.0, 60.0),
                                   (0.0, 60.0)], segments=24, mat=steel)
    bkit.cylinder("AnchorStock", 12.0, 200.0, segments=20, axis="Y",
                  centre=(0.0, 0.0, 46.0), mat=steel)

    # one digging arm per side: a true arc, root buried in the crown, tip
    # inside the fluke. No mirror -- a second arc per side would double the
    # part count and read as an anchor with four flukes.
    for i, s in enumerate((1, -1)):
        bkit.arc_torus("AnchorArm%d" % i, 68.0, 9.0, 5.0, 55.0,
                       centre=(0.0, s * Y_FLUKE, 26.0), plane="XZ",
                       seg_major=20, seg_minor=14, mat=steel, caps=True)

    # one fluke, frozen, then repeated on the other side
    f = bkit.extrude_profile("AnchorFluke0", fluke_profile(), 13.0, axis="Y",
                             mat=rust)
    V.freeze(f)
    f.location = (0.0, 0.0, 0.0)
    bkit.duplicate(f, "AnchorFluke1", offset_mm=(0.0, -2.0 * Y_FLUKE, 0.0))
    bkit.move(f, 0.0, Y_FLUKE, 0.0)

    return dict(spec=SPEC, parts=9)
