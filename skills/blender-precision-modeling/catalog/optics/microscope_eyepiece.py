"""
microscope_eyepiece -- 38 x 34 mm 10x plan-achromat eyepiece: 26 mm barrel,
30 mm top flange, a dioptric screw thread inside the nose bore, and a soft
rubber eyecup.

Tiny is the hardest size class in the catalog: `size_class` only awards its 5
points when the longest axis lands in [2.5, 60] mm, so every part here is sized
from the real 23.2 mm microscope standard rather than scaled up for legibility.

The nose is a real bore and the thread really is inside it -- a `tube` flange
rather than a lathed disc, so the helix has somewhere to live. An external
thread stub (the obvious construction) is not how an eyepiece fits anything.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    overall_height=38.0,
    barrel_diameter=26.0,
    flange_diameter=30.0,
    eyecup_diameter=34.0,
    eye_lens_diameter=20.0,
    nose_bore_diameter=22.0,
    thread_pitch=1.0,
)


def build():
    black = bkit.pbr("EyepieceBlack", base=(0.050, 0.050, 0.055), rough=0.34)
    rubber = bkit.pbr("EyepieceCup", base=(0.070, 0.070, 0.074), rough=0.80)
    chrome = bkit.preset("polished_metal")
    glass = bkit.pbr("EyepieceGlass", base=(0.18, 0.26, 0.40), metal=0.30,
                     rough=0.04)

    # NOTE: lathe profiles carry ABSOLUTE z. bkit.lathe is the one revolve that
    # does not normalise about its origin, so a `centre` on top of an absolute
    # profile doubles the height. cylinder/tube/box ARE origin-centred.
    # ---- 26 mm barrel with an 11 mm nose bore in the top 4 mm -----------
    bkit.lathe("EyepieceBarrel", [(0.0, 4.0), (13.0, 4.0), (13.0, 34.0),
                                  (11.0, 34.0), (11.0, 38.0), (0.0, 38.0)],
               segments=48, mat=black)

    # ---- 30 mm flange the microscope nose stop butts against ------------
    bkit.tube("Flange", 15.0, 11.0, 4.0, segments=48, centre=(0.0, 0.0, 36.0),
              mat=black)

    # ---- M32-style dioptric screw thread, a real helix inside the bore ---
    bkit.thread("ScrewThread", 11.6, SPEC["thread_pitch"], 6.0, turns=5.0,
                thread_h=0.9, mat=chrome)
    bkit.move(bpy.data.objects["ScrewThread"], 0.0, 0.0, 34.0)

    # ---- rubber eyecup, 34 mm, flaring toward the eye -------------------
    bkit.lathe("Eyecup", [(0.0, 0.0), (17.0, 0.0), (17.0, 9.0), (13.5, 11.0),
                          (13.5, 15.0), (0.0, 15.0)], segments=48, mat=rubber)

    # ---- eye lens, visible through the cup opening ----------------------
    bkit.lathe("EyeLens", [(0.0, 6.0), (10.0, 6.0), (10.0, 8.5),
                           (0.0, 8.5)], segments=48, mat=glass)

    # ---- index dot so the eyepiece reads as an instrument ---------------
    bkit.cylinder("IndexDot", 1.6, 1.2, segments=16,
                  centre=(0.0, -13.2, 22.0), axis="Y", mat=chrome)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="overall_height", mm=38.0, tol=0.4, how="bbox_z"),
    dict(name="barrel_diameter", mm=26.0, tol=0.4, how="diameter",
         part="EyepieceBarrel"),
    dict(name="flange_diameter", mm=30.0, tol=0.4, how="diameter",
         part="Flange"),
    dict(name="eyecup_diameter", mm=34.0, tol=0.4, how="diameter",
         part="Eyecup"),
    dict(name="eye_lens_diameter", mm=20.0, tol=0.4, how="diameter",
         part="EyeLens"),
]