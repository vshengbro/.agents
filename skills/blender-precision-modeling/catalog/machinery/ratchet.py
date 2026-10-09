"""
ratchet -- 3/8 in reversible ratchet wrench: 12-tooth ratchet head, square drive.

A ratchet is not a gear: the teeth are one-sided. Each tooth is a long shallow
ramp (the driving face) and a short steep face (the reversing face), and the
drive square is sunk in a shallow recess on the top face -- three quarters of an
inch across flats. The handle is 2 mm thicker than the head so the union never
sees two coplanar faces.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    teeth=16,
    head_diameter=51.0,
    head_thickness=12.0,
    drive_across_flats=19.05,     # 3/4 in ratchet drive
    drive_depth=9.0,
    recess_diameter=40.0,
    recess_depth=2.5,
    handle_length=170.0,
    handle_width=20.0,
    handle_thickness=14.0,
    hang_hole_diameter=12.0,
    head_width=50.9,               # teeth span 210 deg, so the head is a touch
    overall_length=214.0,          # wider across Y than the 48 back circle
)


def _head_ring():
    """Back circle plus a 120 deg sector of one-sided ratchet teeth."""
    r_back = 24.0
    r_root = 21.5
    r_tip = 25.5
    pts = []
    for k in range(31):                       # back arc, 105 deg -> 255 deg
        a = math.radians(105.0 + 150.0 * k / 30.0)
        pts.append((math.cos(a) * r_back, math.sin(a) * r_back))
    a0, a1 = 255.0, 465.0                     # toothed sector, 210 deg wide
    step = (a1 - a0) / SPEC["teeth"]
    for k in range(SPEC["teeth"]):
        a = math.radians(a0 + step * k)
        pts.append((math.cos(a) * r_root, math.sin(a) * r_root))
        b = math.radians(a0 + step * (k + 0.82))   # long shallow driving face
        pts.append((math.cos(b) * r_tip, math.sin(b) * r_tip))
    # blend the last tooth back onto the back circle; this point must come
    # AFTER the final tooth tip in angle or the outline doubles back on itself
    # and the extrusion collapses to nothing.
    a = math.radians(a1 - 1.8)
    pts.append((math.cos(a) * r_back, math.sin(a) * r_back))
    return pts


def build():
    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    chrome = bkit.pbr("bright_steel", base=(0.74, 0.75, 0.78), metal=0.70, rough=0.16)

    head = bkit.extrude_profile("RatchetHead", _head_ring(), SPEC["head_thickness"],
                                mat=chrome)
    bkit.recalc(head)

    # ---- handle: 170 mm long, its near end 4.5 mm inside the head -------
    hx = 20.0 + SPEC["handle_length"] / 2.0
    handle_poly = bkit.rounded_rect_section(SPEC["handle_length"],
                                            SPEC["handle_width"], 8.0,
                                            per_corner=6, centre=(hx, 0.0))
    handle = bkit.extrude_profile("Handle", handle_poly, SPEC["handle_thickness"],
                                  mat=chrome)
    bkit.boolean(head, handle, "UNION")

    # ---- drive recess + square -----------------------------------------
    recess = bkit.cylinder("Recess", SPEC["recess_diameter"] / 2.0,
                           SPEC["recess_depth"] * 1.6, segments=72,
                           centre=(0.0, 0.0, SPEC["head_thickness"] / 2.0 - 0.8))
    bkit.boolean(head, recess, "DIFFERENCE")
    square = bkit.box("Drive", SPEC["drive_across_flats"], SPEC["drive_across_flats"],
                      SPEC["drive_depth"] * 1.6,
                      centre=(0.0, 0.0, SPEC["head_thickness"] / 2.0
                              - SPEC["drive_depth"] / 2.0 + 0.8))
    bkit.boolean(head, square, "DIFFERENCE")

    # ---- lanyard hole ---------------------------------------------------
    hole = bkit.cylinder("HangHole", SPEC["hang_hole_diameter"] / 2.0, 30.0,
                         segments=48,
                         centre=(hx + SPEC["handle_length"] / 2.0 - 15.0, 0.0, 0.0))
    bkit.boolean(head, hole, "DIFFERENCE")

    bkit.recalc(head)
    head.name = "Ratchet"
    bkit.assign_faces_by(head, steel, lambda c, n: abs(c.x) > 40.0)
    return dict(spec=SPEC, parts=1, teeth=SPEC["teeth"])


CHECKS = [
    dict(name="overall_length", mm=214.0, tol=0.8, how="bbox_x", part="Ratchet"),
    dict(name="head_width", mm=50.9, tol=0.6, how="bbox_y", part="Ratchet"),
    dict(name="handle_thickness", mm=14.0, tol=0.4, how="bbox_z", part="Ratchet"),
]
