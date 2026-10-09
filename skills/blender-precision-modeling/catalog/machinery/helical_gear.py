"""
helical_gear -- single-start helical gear, 20 deg helix angle, bored and hubbed.

The teeth are not a spur profile that has been sheared: every cross-section of
the blank is rotated by an amount proportional to its distance along the face,
so the flanks are genuinely helical. Twist over the face width follows
    dtheta = w * tan(beta) / r_pitch
which is the one equation that separates a helical gear from a straight-toothed
disc. Lead chamfers are built in as a taper of the last sections.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    teeth=26,
    module_mm=3.0,
    helix_angle_deg=20.0,
    pitch_diameter=78.0,        # m * z
    outside_diameter=84.0,      # m * (z + 2)
    root_diameter=70.5,         # m * (z - 2.5)
    face_width=26.0,
    twist_degrees=13.9,         # across the face at the pitch circle
    bore_diameter=18.0,
    hub_diameter=44.0,
    hub_length=6.0,
    total_height=32.0,
)

FLANK_STEPS = 5
SECTIONS = 12                   # sections along the face; more = smoother helix


def _tooth_ring(r_out, r_root, z, twist, teeth, lead=0.0):
    """One cross-section of the blank: a full toothed ring at height z, rotated
    by `twist` radians. `lead` pulls the tip back for a chamfer at the ends."""
    step = 2.0 * math.pi / teeth
    half_root = step * 0.19
    half_tip = step * 0.115
    pts = []
    for t in range(teeth):
        a = t * step
        for k in range(FLANK_STEPS + 1):          # rising flank, root -> tip
            f = k / float(FLANK_STEPS)
            ang = a - half_root + (half_root - half_tip) * f + twist
            r = r_root + (r_out - lead - r_root) * f
            pts.append((math.cos(ang) * r, math.sin(ang) * r, z))
        ang = a + half_tip + twist                 # tip land
        pts.append((math.cos(ang) * (r_out - lead),
                    math.sin(ang) * (r_out - lead), z))
        for k in range(FLANK_STEPS - 1, -1, -1):   # falling flank (no dup tip)
            f = k / float(FLANK_STEPS)
            ang = a + half_root - (half_root - half_tip) * f + twist
            r = r_root + (r_out - lead - r_root) * f
            pts.append((math.cos(ang) * r, math.sin(ang) * r, z))
    return pts


def build():
    z = SPEC["teeth"]
    m = SPEC["module_mm"]
    r_out = SPEC["outside_diameter"] / 2.0
    r_root = SPEC["root_diameter"] / 2.0
    r_pitch = SPEC["pitch_diameter"] / 2.0
    w = SPEC["face_width"]
    r_bore = SPEC["bore_diameter"] / 2.0
    hub_l = SPEC["hub_length"]

    # MATERIAL NOTE (this pattern is used across the machinery domain).
    # bkit's metal presets are metal=1.0. A pure metal has NO diffuse term, and
    # this skill's studio is a dark box with a dark world, so a model built
    # from preset("brushed_metal")/preset("steel") renders near-black: only the
    # small bright highlights survive. Defining the metal with bkit.pbr at
    # metal=0.55 keeps the specular reading of machined steel and gives the
    # body a diffuse tone the key light can actually illuminate.
    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    # total twist of the tooth helix across the face
    twist = w * math.tan(math.radians(SPEC["helix_angle_deg"])) / r_pitch

    sections = []
    for s in range(SECTIONS + 1):
        t = s / float(SECTIONS)
        z_h = -w / 2.0 + w * t
        # 1.2 mm lead chamfer, tapering the last 1.5 mm of the face at both ends
        lead = 1.2 * max(0.0, 1.0 - t / 0.06) + 1.2 * max(0.0, 1.0 - (1.0 - t) / 0.06)
        sections.append(_tooth_ring(r_out, r_root, z_h, twist * t, z, lead))

    gear = bkit.loft("HelicalGear", sections, closed_loop=True,
                     cap_start=True, cap_end=True, mat=steel)
    bkit.recalc(gear)
    bkit.weld(gear)

    # web relief: the rim is left full width, the web is thinned both sides
    relief = bkit.cylinder("Relief", r_root - 3.0, w * 0.55, segments=96)
    bkit.boolean(gear, relief, "DIFFERENCE")

    # hub boss on the back face: 6 mm proud, but reaching 10 mm INTO the blank
    # so the union never sees two faces meeting on the back plane
    hub = bkit.cylinder("Hub", SPEC["hub_diameter"] / 2.0, hub_l + 10.0,
                        segments=96,
                        centre=(0, 0, -w / 2.0 + 10.0 - (hub_l + 10.0) / 2.0),
                        mat=steel)
    bkit.boolean(gear, hub, "UNION")

    bore = bkit.cylinder("Bore", r_bore, w * 4, segments=96)
    bkit.boolean(gear, bore, "DIFFERENCE")

    # keyway across the bore and hub
    key = bkit.box("Keyway", 5.0, 3.0, w * 4, centre=(r_bore - 1.0, 0, 0))
    bkit.boolean(gear, key, "DIFFERENCE")

    bkit.recalc(gear)
    bkit.assign_faces_by(gear, dark, lambda c, n: c.z < -w / 2.0 - 0.5)
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="outside_diameter", mm=84.0, tol=0.5, how="diameter", part="HelicalGear"),
    dict(name="total_height", mm=32.0, tol=0.5, how="bbox_z", part="HelicalGear"),
    dict(name="outside_diameter_y", mm=84.0, tol=0.5, how="bbox_y", part="HelicalGear"),
]
