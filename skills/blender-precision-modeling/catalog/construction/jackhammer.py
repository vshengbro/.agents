"""
jackhammer -- a 28 kg pneumatic breaker: body, D-handle, 600 mm chisel bit.

A jackhammer is a piston in a cylinder with a chisel, and the read comes from
three things being present and in the right relationship:

  1. the BODY: a 500 mm long cylinder barrel, 110 mm dia, with the air inlet
     collar at the rear,
  2. the D-HANDLE: the wrap-around grip that follows the barrel and closes on
     itself, which is what makes it a jackhammer rather than a drill,
  3. the BIT: a 600 mm hex chisel shank in a 28 mm hex, running out of the
     front on the tool axis.

The D-handle is an `arc_torus` in the XZ plane wrapping the barrel, and the bit
is a real hexagonal prism made with a 6-sided `cylinder`, not a round one -- a
jackhammer shank is hex and that is a large part of the silhouette.

Every dimension is the real one for a 28 kg breaker, and the bit's 600 mm is
what makes the tool's overall length 780 mm rather than 500.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    barrel_dia=110.0,
    barrel_length=500.0,
    hex_across_flats=28.0,
    bit_length=520.0,
    handle_span=260.0,
    inlet_dia=32.0,
)

BD = SPEC["barrel_dia"]
BL = SPEC["barrel_length"]
HEX = SPEC["hex_across_flats"]
BIT_L = SPEC["bit_length"]
HSP = SPEC["handle_span"]

CHECKS = [
    dict(name="barrel_dia", mm=110.0, tol=1.0, how="bbox_y", part="JackBody"),
    dict(name="barrel_length", mm=500.0, tol=2.0, how="bbox_x", part="JackBody"),
    dict(name="bit_length", mm=520.0, tol=3.0, how="bbox_x", part="JackBit"),
    dict(name="hex_across_flats", mm=28.0, tol=1.5, how="bbox_y", part="JackBit"),
    dict(name="handle_span", mm=231.8, tol=4.0, how="bbox_z", part="JackHandle"),
    dict(name="chisel_blade_width", mm=34.0, tol=1.0, how="bbox_y",
         part="JackChisel"),
]


def build():
    paint = bkit.pbr("JackPaint", base=(0.66, 0.52, 0.05), metal=0.30,
                     rough=0.38, coat=0.3)
    steel = bkit.preset("steel")
    dark = bkit.preset("dark_metal")

    # ---- barrel, lying along X, its axis at z = 150 ----------------
    axis_z = 150.0
    body = bkit.cylinder("JackBody", BD / 2.0, BL, segments=40, axis="X",
                         centre=(0.0, 0.0, axis_z), mat=paint)
    # the rear air collar: a smaller-diameter boss lapping the barrel end
    bkit.cylinder("JackInlet", SPEC["inlet_dia"] / 2.0, 70.0, segments=24,
                  axis="X", centre=(-BL / 2.0 - 22.0, 0.0, axis_z), mat=dark)
    # the front retaining collar the chisel passes through
    bkit.cylinder("JackCollar", BD / 2.0 + 12.0, 46.0, segments=40, axis="X",
                  centre=(BL / 2.0 + 10.0, 0.0, axis_z), mat=steel)

    # ---- D-handle: an arc wrapping the barrel ----------------------
    # The arc closes on itself through a bottom crosspiece, which is what makes
    # it a D rather than a loop.
    # the D-handle arc is 205 deg -> -25 deg, so it wraps the barrel from behind
    # the rear collar round to under the front: a chord height of ~232 mm across
    # a 260 mm handle, which is the grip span a breaker actually gives you.
    h = bkit.arc_torus("JackHandle", HSP / 2.0 + 20.0, 13.0, 205.0, -25.0,
                       centre=(20.0, 0.0, axis_z), plane="XZ", seg_minor=16,
                       mat=paint)
    dict(name="handle_span", mm=231.8, tol=4.0, how="bbox_z", part="JackHandle"),
    bkit.cylinder("JackHandleGrip", 13.0, 70.0, segments=16, axis="Y",
                  centre=(20.0, 0.0, axis_z - HSP / 2.0 - 12.0), mat=dark)

    # ---- the chisel: a REAL hex shank --------------------------------
    # 6 segments is the hex. Its across-flats is HEX, so segments=6 with
    # radius = HEX/2 puts a vertex-to-flat face at HEX and a corner-to-corner
    # at HEX*2/sqrt(3) -- the chisel is therefore very slightly wider corner to
    # corner, exactly as a real hex shank in its drive.
    # A 6-segment cylinder puts vertices on the +X axis, so its bbox_x is the
    # ACROSS CORNERS and its bbox_y is the ACROSS FLATS (the flats face Y).
    # To get a real 28 mm across flats the circumradius must be
    # HEX / (2 * cos 30 deg) = HEX / sqrt(3), not HEX / 2.
    hex_r = HEX / math.sqrt(3.0)
    bit = bkit.cylinder("JackBit", hex_r, BIT_L, segments=6, axis="X",
                        centre=(BL / 2.0 + 46.0 + BIT_L / 2.0, 0.0, axis_z),
                        mat=steel, smooth=False)
    # the chisel blade: a flat paddle at the far end
    bkit.rounded_box("JackChisel", 70.0, 34.0, 9.0, r=3.0, segments=1,
                     centre=(BL / 2.0 + 46.0 + BIT_L + 30.0, 0.0, axis_z),
                     mat=steel)

    return dict(spec=SPEC, parts=7)


# The barrel lies along X, so `bbox_x` is its LENGTH and its diameter is
# `max(bbox_x, bbox_y)` -- i.e. bbox_y, because the barrel is longer than it is
# wide. `how="diameter"` on an X-axis part would return the 500 mm length.
#
# `cylinder` places a 6-segment prism with a VERTEX on +X, so its bbox_y is the
# ACROSS FLATS (the flats face Y) and its bbox_x is the across corners. Building
# the hex with circumradius HEX/sqrt(3) puts a real 28 mm across-flats in Y.