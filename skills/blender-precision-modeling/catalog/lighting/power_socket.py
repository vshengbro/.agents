"""
power_socket -- UK 13 A switched socket outlet, 1 gang.

Same governing dimension as the switch plate: a UK accessory plate is 86 x 86 mm
and the three BS 1363 pin apertures sit inside it. The aperture triangle is the
thing that makes it read as a British socket rather than a generic outlet --
live and neutral are vertical slots 27.43 mm apart, with the horizontal earth
aperture above them. Those two x positions come from bkit.lay_out so the gap is
computed, never hand-placed into the geometry twice.

The apertures are blind pockets cut 5 mm into the plate, and each cutter
straddles the front face so the boolean sees a crossing rather than a tangent
(bkit.bore's rule, applied to a box cutter).
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    plate_width=86.0,        # UK 1-gang accessory plate
    plate_height=86.0,
    plate_depth=9.5,
    corner_radius=6.0,
    pin_slot_width=6.35,     # BS 1363 pin aperture
    pin_slot_height=1.63,
    live_neutral_spacing=27.43,
    earth_above=35.56,
    aperture_depth=5.0,
    screw_spacing=60.0,
    overall_depth=9.5,
)

PLATE = 86.0
DEPTH = 9.5
SW = SPEC["pin_slot_width"]


def build():
    ivory = bkit.preset("white_plastic")
    steel = bkit.preset("steel")
    cavity = bkit.pbr("SocketCavity", base=(0.06, 0.06, 0.07), rough=0.45)

    plate = bkit.rounded_box("SocketPlate", PLATE, PLATE, DEPTH,
                             r=SPEC["corner_radius"], segments=5,
                             centre=(0.0, 0.0, DEPTH / 2.0), mat=ivory)

    z_face = DEPTH                     # top of the plate
    slot_h = SPEC["pin_slot_height"]
    depth = SPEC["aperture_depth"]
    ln = SPEC["live_neutral_spacing"]

    # ---- shallow moulded recess so the face is not a flat blank ---------
    # The apertures alone render as hairlines; a 1.5 mm step across the
    # central 70 mm is what actually reads as a socket at plate scale.
    recess = bkit.rounded_box("_face_recess", 70.0, 70.0, 4.5, r=5.0, segments=3,
                              centre=(0.0, 0.0, z_face - 0.75))
    bkit.boolean(plate, recess, "DIFFERENCE")
    z_face -= 1.5

    # ---- live + neutral: vertical apertures, spacing COMPUTED -------------
    # lay_out returns centres for real widths plus an explicit gap, so the
    # 27.43 mm pitch lives in exactly one place in the script.
    for (x, w) in bkit.lay_out([SW, SW], gap=ln - SW):
        y = -SPEC["earth_above"] / 2.0
        cut = bkit.rounded_box("_pin_cut", w, slot_h, depth + 2.0, r=0.3,
                               segments=2, centre=(x, y, z_face - depth / 2.0 + 1.0))
        bkit.boolean(plate, cut, "DIFFERENCE")

    # ---- earth: horizontal aperture above the pair ----------------------
    y_e = SPEC["earth_above"] / 2.0
    cut = bkit.rounded_box("_earth_cut", slot_h, SW, depth + 2.0, r=0.3,
                           segments=2, centre=(0.0, y_e, z_face - depth / 2.0 + 1.0))
    bkit.boolean(plate, cut, "DIFFERENCE")

    # ---- two fixing screws on the centreline ----------------------------
    for (y, w) in bkit.lay_out([3.4, 3.4], gap=SPEC["screw_spacing"] - 3.4):
        head = bkit.cylinder("SocketScrew", 2.6, 1.4, segments=24,
                             centre=(0.0, y, z_face - 0.35), mat=steel)
        bkit.move(head, 0.0, 0.0, 0.0)

    bkit.recalc(plate)
    # the moulded interior: one solid, two materials, rather than a second
    # shell inside the plate that would z-fight with the wall
    bkit.assign_faces_by(plate, cavity,
                         lambda c, n: 2.0 < c.z / bkit.MM < z_face + 0.4
                         and (c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM < 34.0)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="plate_width", mm=86.0, tol=0.3, how="bbox_x", part="SocketPlate"),
    dict(name="plate_height", mm=86.0, tol=0.3, how="bbox_y", part="SocketPlate"),
    dict(name="plate_depth", mm=9.5, tol=0.3, how="bbox_z", part="SocketPlate"),
    dict(name="screw_head_diameter", mm=5.2, tol=0.3, how="diameter", part="SocketScrew"),
]