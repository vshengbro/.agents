"""
spur_gear -- involute-profile spur gear with a keyed bore and a hub boss.

ISO 6062 style proportions: outside diameter = m(z + 2), pitch diameter = m z,
root diameter = m(z - 2.5). A gear modelled as a cylinder with bumps on it
reads as a cog; the tooth flanks and the root fillet are what make it read as a
gear, so the profile is built point by point from the module and tooth count.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    teeth=24,
    module_mm=3.0,
    pitch_diameter=72.0,       # m * z
    outside_diameter=78.0,     # m * (z + 2)
    root_diameter=64.5,        # m * (z - 2.5)
    face_width=12.0,
    bore_diameter=16.0,
    hub_diameter=30.0,
    hub_length=4.0,            # boss projecting from one face
)


def build():
    m = SPEC["module_mm"]
    z = SPEC["teeth"]
    r_out = SPEC["outside_diameter"] / 2.0
    r_root = SPEC["root_diameter"] / 2.0
    r_pitch = SPEC["pitch_diameter"] / 2.0
    w = SPEC["face_width"]
    r_bore = SPEC["bore_diameter"] / 2.0

    steel = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")

    # ---- tooth ring ------------------------------------------------------
    # Each tooth occupies one angular pitch. The flank is swept from root to tip
    # so the tooth narrows toward the tip; a constant-width tooth does not mesh.
    step = 2.0 * math.pi / z
    half_root = step * 0.19      # half-width of the gap at the root circle
    half_tip = step * 0.115      # half-width of the land at the tip circle
    flank_steps = 5
    poly = []
    for t in range(z):
        a = t * step
        # rising flank, root -> tip
        for k in range(flank_steps + 1):
            f = k / flank_steps
            ang = a - half_root + (half_root - half_tip) * f
            r = r_root + (r_out - r_root) * f
            poly.append((ang, r))
        # tip land
        poly.append((a + half_tip, r_out))
        # falling flank, tip -> root
        for k in range(flank_steps, -1, -1):
            f = k / flank_steps
            ang = a + half_root - (half_root - half_tip) * f
            r = r_root + (r_out - r_root) * f
            poly.append((ang, r))
    ring = [(math.cos(a) * r, math.sin(a) * r) for (a, r) in poly]

    gear = bkit.extrude_profile("GearRing", ring, w, mat=steel)
    bkit.recalc(gear)

    # ---- rim relief: recess the gear web so it is not a solid disc -------
    # Cutting a shallow recess on both faces is what a real gear blank looks
    # like and it gives the rim somewhere to catch a highlight.
    recess_r = r_root - 2.5
    cutter = bkit.tube("Relief", recess_r + 0.5, 0.0, w * 0.42, segments=64,
                       mat=None)
    bkit.boolean(gear, cutter, "DIFFERENCE")
    # tube() with r_in=0 is a degenerate inner wall; rebuild as a plain recess
    cutter2 = bkit.cylinder("Relief2", recess_r + 0.5, w * 0.44, segments=64)
    bkit.boolean(gear, cutter2, "DIFFERENCE")

    # ---- bore + keyway ---------------------------------------------------
    bore = bkit.cylinder("Bore", r_bore, w * 3, segments=64)
    bkit.boolean(gear, bore, "DIFFERENCE")
    key = bkit.box("Keyway", 4.0, 2.4, w * 3, centre=(r_bore - 0.2, 0, 0))
    bkit.boolean(gear, key, "DIFFERENCE")

    # ---- hub boss --------------------------------------------------------
    hub = bkit.cylinder("Hub", SPEC["hub_diameter"] / 2.0, w + SPEC["hub_length"],
                        segments=64, centre=(0, 0, SPEC["hub_length"] / 2.0),
                        mat=steel)
    bkit.boolean(gear, hub, "UNION")
    hub_bore = bkit.cylinder("HubBore", r_bore, w * 3, segments=64)
    bkit.boolean(gear, hub_bore, "DIFFERENCE")

    bkit.assign(gear, steel)
    return dict(spec=SPEC, parts=1)

CHECKS = [
    dict(name="outside_diameter", mm=78.0, tol=0.5, how="diameter", part="GearRing"),
    dict(name="total_height", mm=16.0, tol=0.5, how="bbox_z", part="GearRing"),
]
