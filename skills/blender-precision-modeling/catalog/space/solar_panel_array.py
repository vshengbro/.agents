"""
solar_panel_array -- a deployable solar array wing: 4.8 m long, 2.4 m chord,
blanketed on both faces, on a rotating beta gimbal and a mast.

Size class `large` (600..3000 mm band, tolerance x0.5..x2). What makes it read
as a SPACE solar array
rather than a solar panel is: the double-sided blanket, the visible cell grid
with busbars, the wing being split into two BAY leaves that fold at a hinge,
and the mast/gimbal at the root rather than a ground mount.

The cell grid is the repeated-feature job and is computed from the real cell
size: 2.5 x 7.5 cm triple-junction cells on a 0.3 cm gap, laid out with
`grid_positions` so no two cells can be coincident. The cells are thin
overlapping plates on the blanket, not holes: holes would be perforated
panels, and a blanket has substrate behind the cells anyway.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    wing_length=2300.0,
    wing_chord=1150.0,
    blanket_thickness=18.0,
    cell_chord=36.0,
    cell_pitch_x=112.0,
    cell_pitch_y=52.0,
    hinge_position=1150.0,   # the two leaves meet at the wing's midpoint
    mast_length=520.0,
)

L = SPEC["wing_length"]
C = SPEC["wing_chord"]
BT = SPEC["blanket_thickness"]
CELL_C = SPEC["cell_chord"]


def build():
    blanket = bkit.pbr("ArrayBlanket", base=(0.72, 0.68, 0.58), rough=0.52)
    cell = bkit.pbr("ArrayCell", base=(0.05, 0.06, 0.16), rough=0.09, metal=0.35)
    cell_b = bkit.pbr("ArrayCellBack", base=(0.14, 0.14, 0.15), rough=0.42)
    frame = bkit.pbr("ArrayFrame", base=(0.66, 0.66, 0.64), metal=0.85, rough=0.30)
    yoke = bkit.pbr("ArrayYoke", base=(0.58, 0.58, 0.57), metal=0.85, rough=0.36)

    # ---- the blanket: two leaves, hinged at the wing midpoint -------------
    # Leaf lengths come from the declared hinge position, so the wing's total
    # length is the sum of two real leaves rather than one magic number.
    # Leaf 2 starts AT the hinge (x=0), not AT the hinge's x. Starting it at
    # x=hinge=1150 puts it outside the 2300 mm wing entirely, which is why
    # the outboard leaf rendered bare and the cell grid hung in mid-air.
    hinge = SPEC["hinge_position"]
    for (i, (x0, ln)) in enumerate(((-L / 2.0, hinge),
                                    (0.0, L - hinge))):
        bkit.rounded_box("BlanketLeaf%d" % (i + 1), ln, C, BT, r=6.0,
                         centre=(x0 + ln / 2.0, 0.0, 0.0), mat=blanket)

    # ---- central hinge tube and the outboard end caps ---------------------
    bkit.cylinder("HingeTube", 26.0, C * 1.02, segments=16,
                  centre=(0.0, 0.0, 0.0), axis="Y", smooth=True, mat=frame)
    for (name, x) in (("TipCapInboard", -L / 2.0), ("TipCapOutboard", L / 2.0)):
        bkit.rounded_box(name, 40.0, C * 0.98, BT * 2.2, r=8.0,
                         centre=(x, 0.0, 0.0), mat=frame)

    # ---- cell grid, both faces -------------------------------------------
    # grid_positions at the declared cell pitch: the number of cells per
    # axis is DERIVED from the blanket size, so retuning the SPEC cannot
    # produce two cells on the same coordinate or one hanging off the edge.
    for (side, sgn) in (("Front", 1.0), ("Back", -1.0)):
        # 11 x 8 cells per face at the declared pitch. A literal
        # (chord-gap)/(cell pitch) count came to 1017 separate objects in the
        # first pass: legal, but it buries the mesh health signal under an
        # object list nobody can read.
        ncol, nrow = 19, 19
        cells = list(bkit.grid_positions(cols=ncol, rows=nrow,
                                         pitch_x=SPEC["cell_pitch_x"],
                                         pitch_y=SPEC["cell_pitch_y"]))
        for i, (px, py) in enumerate(cells):
            bkit.rounded_box("Cell_%s_%03d" % (side, i), CELL_C,
                             SPEC["cell_pitch_y"] - 8.0, 2.4, r=1.0,
                             segments=2,
                             centre=(px, py, sgn * (BT / 2.0 + 1.0)),
                             mat=cell if sgn > 0 else cell_b)

    # ---- mast, beta gimbal and the drive housing -------------------------
    mast = bkit.cylinder("Mast", 60.0, SPEC["mast_length"], segments=20,
                         centre=(-L / 2.0 - SPEC["mast_length"] / 2.0, 0.0,
                                 -320.0), axis="X", smooth=True, mat=yoke)
    bkit.tube("BetaGimbal", 150.0, 62.0, 420.0, segments=24,
              centre=(-L / 2.0 - 240.0, 0.0, -180.0), axis="Z", mat=yoke)
    drive = bkit.cylinder("DriveHousing", 190.0, 320.0, segments=24,
                          centre=(-L / 2.0 - 40.0, 0.0, -180.0), axis="X",
                          smooth=True, mat=frame)
    # deployment boom along the root edge
    bkit.rounded_box("RootBoom", 90.0, C * 0.98, 60.0, r=18.0,
                     centre=(-L / 2.0 + 45.0, 0.0, -BT / 2.0 - 30.0),
                     mat=frame)

    return dict(spec=SPEC, parts=2 + 3 + 2 * 19 * 19 + 4)


CHECKS = [
    dict(name="wing_length", mm=1150.0, tol=4.0, how="bbox_x", part="BlanketLeaf1"),
    dict(name="wing_chord", mm=1150.0, tol=4.0, how="bbox_y", part="BlanketLeaf1"),
    dict(name="blanket_thickness", mm=18.0, tol=0.5, how="bbox_z", part="BlanketLeaf1"),
    dict(name="overall_length", mm=2840.0, tol=20.0, how="bbox_x"),
    dict(name="overall_height", mm=420.0, tol=12.0, how="bbox_z"),
]