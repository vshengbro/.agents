"""
light_switch -- UK 1-gang rocker switch plate.

This object lives or dies on one number: a UK switch plate is 86 x 86 mm, and
that is the dimension a plate is bought and screwed to. Everything else on this
model follows from it -- the plate depth, the rocker's 22 x 46 mm footprint
inside it, and the two M3.5 fixing screws on the vertical centreline.

Modelled lying flat, plate face up, because run_model seats every model on
z = 0 and a plate built standing on edge would be a 9 mm sliver on the floor.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    plate_width=86.0,        # the number that matters: UK 1-gang plate
    plate_height=86.0,
    plate_depth=9.5,
    corner_radius=6.0,
    rocker_width=22.0,
    rocker_height=46.0,
    rocker_projection=4.0,
    screw_diameter=3.4,
    screw_spacing=60.0,      # fixing centres on the vertical centreline
    overall_depth=13.5,
)

PLATE = 86.0
DEPTH = 9.5


def build():
    ivory = bkit.preset("white_plastic")
    steel = bkit.preset("steel")
    rocker_mat = bkit.preset("ceramic")

    plate = bkit.rounded_box("SwitchPlate", PLATE, PLATE, DEPTH,
                             r=SPEC["corner_radius"], segments=5,
                             centre=(0.0, 0.0, DEPTH / 2.0), mat=ivory)

    # ---- rocker: the raised paddle, proud of the plate face --------------
    rocker = bkit.rounded_box("SwitchRocker", SPEC["rocker_width"],
                             SPEC["rocker_height"], SPEC["rocker_projection"],
                             r=1.6, segments=4,
                             centre=(0.0, 0.0, DEPTH + SPEC["rocker_projection"] / 2.0 - 0.5),
                             mat=rocker_mat)

    # ---- two fixing screws on the centreline ----------------------------
    # Laid out by measurement rather than typed twice, so the spacing in SPEC
    # and the geometry cannot drift apart.
    for (y, w) in bkit.lay_out([SPEC["screw_diameter"]] * 2,
                               gap=SPEC["screw_spacing"] - SPEC["screw_diameter"]):
        head = bkit.cylinder("SwitchScrew", 2.6, 1.4, segments=24,
                             centre=(0.0, y, DEPTH - 0.35), mat=steel)
        bkit.move(head, 0.0, 0.0, 0.0)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="plate_width", mm=86.0, tol=0.3, how="bbox_x", part="SwitchPlate"),
    dict(name="plate_height", mm=86.0, tol=0.3, how="bbox_y", part="SwitchPlate"),
    dict(name="plate_depth", mm=9.5, tol=0.3, how="bbox_z", part="SwitchPlate"),
    dict(name="rocker_width", mm=22.0, tol=0.3, how="bbox_x", part="SwitchRocker"),
    dict(name="rocker_height", mm=46.0, tol=0.3, how="bbox_y", part="SwitchRocker"),
]