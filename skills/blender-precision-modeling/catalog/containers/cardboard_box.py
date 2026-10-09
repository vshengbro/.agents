"""
cardboard_box -- a closed RSC shipping carton: a rounded-corner body, four
closed top flaps with a centre seam, and a packing-tape strip over the seam.

Boxes are where `rounded_box` earns its keep. A plain `box` reads as a grey
CAD block; a 3 mm fillet plus four separately named flaps reads as corrugated
board. Every flap is computed from the body footprint and the flap thickness
rather than hand-placed, so the seam always lands exactly on the centreline.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=400.0,             # external, along X
    width=300.0,              # external, along Y
    height=250.0,             # external, base to the top of the closed flaps
    board=4.0,                # single-wall corrugated thickness
    corner_radius=6.0,
    flap_gap=2.0,             # centre seam between the two top flaps
)

L = SPEC["length"]
W = SPEC["width"]
H = SPEC["height"]
T = SPEC["board"]
GAP = SPEC["flap_gap"]


def build():
    board = bkit.pbr("CorrugatedBoard", base=(0.62, 0.44, 0.24), rough=0.82)
    board_in = bkit.pbr("CorrugatedInner", base=(0.52, 0.36, 0.19), rough=0.88)
    tape = bkit.pbr("PackingTape", base=(0.78, 0.68, 0.50), rough=0.28,
                    coat=0.3)
    print_mat = bkit.pbr("BoxPrint", base=(0.18, 0.20, 0.24), rough=0.55)

    # ---- body: closed tub ---------------------------------------------------
    # A closed carton hides its interior entirely, so the tub is a solid
    # rounded box and the cavity is simply not modelled. Only the flap seam
    # needs to read, and that is geometry on top.
    body = bkit.rounded_box("CartonBody", L, W, H - T,
                            r=SPEC["corner_radius"], segments=4,
                            centre=(0.0, 0.0, (H - T) / 2.0), mat=board)

    # ---- four top flaps, closed over the mouth ------------------------------
    # The long flaps fold from the two L-long faces and meet on the centreline.
    # The short flaps come from the two W-long faces and sit UNDER them, running
    # along Y -- giving them an L-sized extent put them 66 mm outside the box.
    flap_l = (L - 12.0) / 2.0 - GAP / 2.0
    flap_long_a = bkit.rounded_box(
        "CartonFlapLongA", L - 12.0, flap_l, T, r=3.0, segments=2,
        centre=(0.0, -(flap_l / 2.0 + GAP / 2.0), H - T / 2.0), mat=board)
    flap_long_b = bkit.rounded_box(
        "CartonFlapLongB", L - 12.0, flap_l, T, r=3.0, segments=2,
        centre=(0.0, (flap_l / 2.0 + GAP / 2.0), H - T / 2.0), mat=board)
    short_w = 96.0
    for i, sx in enumerate((-1.0, 1.0)):
        bkit.rounded_box(
            "CartonFlapShort%d" % (i + 1), short_w, W - 14.0, T, r=2.5,
            segments=2,
            centre=(sx * (L / 2.0 - 6.0 - short_w / 2.0), 0.0, H - T * 1.5),
            mat=board_in)

    # ---- tape over the seam -------------------------------------------------
    tape_strip = bkit.rounded_box(
        "CartonTape", L - 10.0, 52.0, 0.6, r=0.25, segments=2,
        centre=(0.0, 0.0, H + 0.3), mat=tape)

    # ---- a printed shipping mark on one side so it is not one flat tone -----
    bkit.assign_faces_by(
        body, print_mat,
        lambda c, n: c.z / bkit.MM < (H - T) * 0.55
        and abs(c.y / bkit.MM) > (W / 2.0 - 1.0),
    )

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="length", mm=400.0, tol=0.5, how="bbox_x", part="CartonBody"),
    dict(name="width", mm=300.0, tol=0.5, how="bbox_y", part="CartonBody"),
    dict(name="overall_height", mm=250.6, tol=0.2, how="bbox_z"),
]
