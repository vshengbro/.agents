"""
extension_lead -- 4-way extension lead: socket block, coiled flex and a plug.

The recognisable thing about an extension lead is the COIL. A straight 2 m cable
laid out flat is a rope; a lead photographed as it is sold has the flex wound
into a flat spiral with the plug tucked against it. So the flex here is a real
torus of one and a half turns, and the block and plug are placed relative to
the coil's real radius rather than at invented coordinates.

The four outlet recesses are cut with positions from bkit.lay_out, so the
outlets are evenly spaced by construction -- hand-placing four identical
recesses is how you end up with two that overlap and destroy the boolean.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    block_length=196.0,
    block_width=58.0,
    block_height=34.0,
    outlet_count=4,
    outlet_width=40.0,
    outlet_depth=30.0,
    outlet_recess=2.5,
    cable_diameter=7.0,
    coil_turns=1.5,
    coil_radius=82.0,
    plug_length=44.0,
    plug_width=30.0,
    plug_height=26.0,
    pin_diameter=4.8,
)


def build():
    white = bkit.preset("white_plastic")
    rubber = bkit.preset("rubber")
    brass = bkit.preset("brushed_metal")
    cavity = bkit.pbr("OutletCavity", base=(0.05, 0.05, 0.06), rough=0.5)

    bw = SPEC["block_width"]
    bh = SPEC["block_height"]
    bl = SPEC["block_length"]
    ow = SPEC["outlet_width"]
    od = SPEC["outlet_depth"]

    # ---- socket block ----------------------------------------------------
    block = bkit.rounded_box("LeadBlock", bl, bw, bh, r=5.0, segments=4,
                             centre=(0.0, 0.0, bh / 2.0), mat=white)

    # ---- four outlet recesses, positions COMPUTED ------------------------
    z_face = bh
    for (x, w) in bkit.lay_out([ow] * SPEC["outlet_count"], gap=8.0):
        cut = bkit.rounded_box("_outlet_cut", w, od,
                               SPEC["outlet_recess"] + 2.0, r=3.0, segments=3,
                               centre=(x, 0.0, z_face - SPEC["outlet_recess"] / 2.0 + 1.0))
        bkit.boolean(block, cut, "DIFFERENCE")

    # a switch and an indicator, one at each end of the top face
    sw = bkit.rounded_box("LeadSwitch", 16.0, 20.0, 3.0, r=1.2, segments=3,
                          centre=(bl / 2.0 - 16.0, 0.0, z_face + 0.6), mat=rubber)
    bkit.move(sw, 0.0, 0.0, 0.0)
    pilot = bkit.cylinder("LeadPilot", 3.0, 2.2, segments=20,
                          centre=(-bl / 2.0 + 14.0, 0.0, z_face + 0.5), mat=rubber)

    # ---- coiled flex: 1.5 turns of real cable ---------------------------
    cd = SPEC["cable_diameter"]
    coil = bkit.arc_torus("LeadCable", SPEC["coil_radius"], cd / 2.0,
                          0.0, 360.0 * SPEC["coil_turns"],
                          centre=(0.0, 0.0, cd / 2.0), plane="XY",
                          seg_major=120, mat=rubber, caps=True)

    # ---- plug, lying just outside the coil ------------------------------
    pr = SPEC["coil_radius"]
    px, py = pr * math.cos(math.radians(205.0)), pr * math.sin(math.radians(205.0))
    plug = bkit.rounded_box("LeadPlug", SPEC["plug_length"],
                            SPEC["plug_width"], SPEC["plug_height"],
                            r=5.0, segments=4,
                            centre=(px + 16.0, py - 14.0, SPEC["plug_height"] / 2.0),
                            mat=rubber)

    pins = []
    for (dx, dy) in bkit.grid_positions(cols=2, rows=2, pitch_x=14.0, pitch_y=13.0):
        p = bkit.cylinder("_pin", SPEC["pin_diameter"] / 2.0, 17.0, segments=16,
                          centre=(px + 30.0 + dx, py - 14.0 + dy,
                                  SPEC["plug_height"] / 2.0), mat=brass)
        bkit.move(p, 0.0, 0.0, 0.0)
        pins.append(p)
    bkit.join(pins, name="LeadPlugPins")

    bkit.recalc(block)
    # Only the moulded recess interior goes dark. The bound must EXCLUDE the
    # top face itself: that face's centre sits at exactly z_face and within
    # the outlet footprint, so an upper bound of z_face - eps is what stops
    # the whole top of the block being painted black.
    bkit.assign_faces_by(block, cavity,
                         lambda c, n: z_face - SPEC["outlet_recess"] - 0.8
                         < c.z / bkit.MM < z_face - 0.4
                         and abs(c.x) / bkit.MM < bl / 2.0 - 6.0
                         and abs(c.y) / bkit.MM < od / 2.0 + 1.0)

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="block_length", mm=196.0, tol=0.4, how="bbox_x", part="LeadBlock"),
    dict(name="block_width", mm=58.0, tol=0.4, how="bbox_y", part="LeadBlock"),
    dict(name="block_height", mm=34.0, tol=0.4, how="bbox_z", part="LeadBlock"),
    dict(name="cable_diameter", mm=7.0, tol=0.4, how="bbox_z", part="LeadCable"),
    dict(name="plug_width", mm=30.0, tol=0.4, how="bbox_y", part="LeadPlug"),
]