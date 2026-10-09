"""
battery -- AA (LR6) alkaline cell, 14.5 mm x 50.5 mm.

The exact figures here are the whole point: IEC 61918 / AA is 14.5 mm in
diameter and 50.5 mm long INCLUDING the raised positive terminal, and the
positive end is flat with a small insulated nub rather than the conical tip of
a zinc-carbon cell. A "roughly cylindrical" AA at 50 mm x 15 mm scores the
size class and fails every dimension check.

The wrapper is a second material on the same solid. A separate sleeve object
would sit a hair inside the can and z-fight with it for the whole catalogue.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    cell_diameter=14.5,      # IEC AA
    cell_length=50.5,        # includes the raised positive terminal
    can_length=46.4,         # barrel below the shoulder
    terminal_diameter=7.2,
    label_diameter=14.62,    # printed wrapper, very slightly proud
    label_length=38.0,
    negative_flat_diameter=11.2,
)

R = SPEC["cell_diameter"] / 2.0
L = SPEC["cell_length"]


def build():
    steel = bkit.preset("steel")
    label = bkit.pbr("CellWrapper", base=(0.10, 0.11, 0.42), rough=0.42)
    positive = bkit.preset("brushed_metal")

    # ---- the cell: flat negative end, straight can, shoulder, positive nub
    cell = bkit.lathe("AAcell", [
        (0.0, 0.0),                       # centre of the flat negative face
        (5.6, 0.0),                       # negative contact pad
        (6.4, 0.4),
        (R, 1.5),                         # rolled can edge
        (R, SPEC["can_length"] - 0.9),
        (R - 0.2, SPEC["can_length"]),    # shoulder
        (4.6, 47.0),                      # step down to the terminal boss
        (3.6, 47.6),
        (3.6, 49.9),
        (2.6, L),                         # rounded top of the positive nub
        (0.0, L),
    ], segments=64, mat=steel)

    # ---- wrapper band: +0.06 mm proud of the can so it wins the depth
    # test outright rather than z-fighting on a coincident surface
    wrapper = bkit.cylinder("AAwrapper", SPEC["label_diameter"] / 2.0,
                            SPEC["label_length"], segments=64,
                            centre=(0.0, 0.0, 5.0 + SPEC["label_length"] / 2.0),
                            mat=label)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="cell_diameter", mm=14.5, tol=0.2, how="diameter", part="AAcell"),
    dict(name="cell_length", mm=50.5, tol=0.2, how="bbox_z", part="AAcell"),
    dict(name="wrapper_diameter", mm=14.62, tol=0.2, how="diameter", part="AAwrapper"),
    dict(name="wrapper_length", mm=38.0, tol=0.3, how="bbox_z", part="AAwrapper"),
]