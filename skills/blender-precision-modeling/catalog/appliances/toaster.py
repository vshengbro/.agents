"""
toaster -- two-slice domestic toaster: pressed-steel shell with rounded vertical
corners, twin bread slots, a carriage lever on the right cheek, a browning dial
on the left, a crumb tray at the back and four rubber feet.

260 x 150 x 180 mm is the real envelope of every mainstream two-slot toaster, so
every number below is a millimetre measurement of one of those.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_width=260.0,        # X, across the long face
    body_depth=150.0,        # Y, front to back
    body_height=174.0,       # shell only; feet add the rest
    overall_height=180.0,    # feet on the floor to the top of the shell
    overall_width=280.0,     # dial face to the tip of the carriage lever
    corner_radius=20.0,      # the pressed-steel corner that says "appliance"
    foot_height=6.0,
    slot_length=140.0,
    slot_width=13.0,
    slot_pitch=52.0,
    slot_depth=35.0,
    lever_protrusion=10.0,
    dial_diameter=26.0,
)

W = SPEC["body_width"]
D = SPEC["body_depth"]
H = SPEC["body_height"]
FOOT = SPEC["foot_height"]
R = SPEC["corner_radius"]
SL = SPEC["slot_length"]
SW = SPEC["slot_width"]
SP = SPEC["slot_pitch"]
TOP = FOOT + H                       # 180 mm, top of the shell


def build():
    # Appliance silver, not chrome: a near-mirror finish has no diffuse term and
    # this studio is dark, so the shell renders as a black blob.
    steel = bkit.pbr("ToasterSteel", base=(0.86, 0.87, 0.88),
                     metal=0.45, rough=0.30)
    chrome = bkit.preset("polished_metal")
    dark = bkit.preset("black_plastic")

    # ---- shell ------------------------------------------------------------
    # A hard box reads as a crate; the 20 mm corner radius is the whole
    # difference between "pressed steel appliance" and "cardboard".
    body = bkit.rounded_box("ToasterBody", W, D, H, r=R, segments=6,
                            centre=(0.0, 0.0, FOOT + H / 2.0), mat=steel)

    # ---- twin bread slots -------------------------------------------------
    # Positions come from the real slot width plus the real gap between slots,
    # never from two hand-typed constants that could land on top of each other.
    slot_y = [x for (x, _w) in bkit.lay_out([SW, SW], gap=SP - SW)]
    cut_h = SPEC["slot_depth"] + 11.0            # over-travel below the crown
    cut_z = TOP - SPEC["slot_depth"] + cut_h / 2.0
    for y in slot_y:
        cut = bkit.rounded_box("_slot_cut", SL, SW, cut_h, r=5.0, segments=3,
                               centre=(0.0, y, cut_z))
        bkit.boolean(body, cut, "DIFFERENCE")
        bkit.recalc(body)
        bkit.health(body)

    # ---- feet -------------------------------------------------------------
    # Real toaster feet are pressed pads at the four corners, well inside the
    # filleted base so nothing is left hanging over a rounded corner.
    for ix, sx in ((0, -1.0), (1, 1.0)):
        for iy, sy in ((0, -1.0), (1, 1.0)):
            bkit.cylinder("Foot_%d%d" % (ix, iy), 10.0, FOOT, segments=32,
                          centre=(sx * 100.0, sy * 50.0, FOOT / 2.0),
                          mat=bkit.preset("rubber"))

    # ---- carriage lever and its guide rib ---------------------------------
    bkit.rounded_box("ToasterLever", 18.0, 34.0, 12.0, r=4.0, segments=3,
                     centre=(W / 2.0 + 1.0, -34.0, FOOT + 100.0), mat=chrome)
    bkit.rounded_box("CarriageGuide", 8.0, 26.0, 96.0, r=3.0, segments=2,
                     centre=(W / 2.0 + 2.0, 34.0, FOOT + 66.0), mat=dark)

    # ---- browning dial ----------------------------------------------------
    bkit.cylinder("BrowningDial", SPEC["dial_diameter"] / 2.0, 12.0, segments=48,
                  axis="X", centre=(-(W / 2.0) - 3.0, -30.0, FOOT + 90.0),
                  mat=dark)
    bkit.rounded_box("DialPointer", 5.0, 3.5, 9.0, r=1.2, segments=2,
                     centre=(-(W / 2.0) - 7.5, -30.0, FOOT + 98.0), mat=chrome)

    # ---- crumb tray: a shallow pressed pan at the back ---------------------
    bkit.rounded_box("CrumbTray", 230.0, 12.0, 42.0, r=4.0, segments=3,
                     centre=(0.0, D / 2.0 + 1.0, FOOT + 24.0),
                     mat=bkit.preset("brushed_metal"))

    # ---- chrome trim band across the front skirt -------------------------
    # A toaster front is never a bare slab; the band gives the eye a datum and
    # stops the shell reading as an untextured box.
    bkit.rounded_box("FrontBand", 244.0, 10.0, 26.0, r=4.0, segments=3,
                     centre=(0.0, -(D / 2.0) - 1.0, FOOT + 22.0), mat=chrome)

    # ---- cooling louvres on the left cheek --------------------------------
    # Real louvres are repeated, so they are laid out from one pitch: the bars
    # are a single mesh of disjoint closed solids, which stays watertight.
    vent = bkit.rounded_box("SideVent", 5.0, 84.0, 6.0, r=1.5, segments=2,
                            centre=(-(W / 2.0) + 0.5, 8.0, FOOT + 114.0), mat=dark)
    bkit.array_linear(vent, 4, (0.0, 0.0, 9.0))

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="body_width", mm=260.0, tol=0.4, how="bbox_x", part="ToasterBody"),
    dict(name="body_depth", mm=150.0, tol=0.4, how="bbox_y", part="ToasterBody"),
    dict(name="body_height", mm=174.0, tol=0.4, how="bbox_z", part="ToasterBody"),
    dict(name="overall_height", mm=180.0, tol=0.4, how="bbox_z"),
    dict(name="overall_width", mm=280.0, tol=0.6, how="bbox_x"),
    dict(name="dial_diameter", mm=26.0, tol=0.4, how="diameter", part="BrowningDial"),
]