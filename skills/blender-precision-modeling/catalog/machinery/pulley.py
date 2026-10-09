"""
pulley -- two-groove V-belt pulley on a keyed hub.

Groove section is B-type (13 x 8): 13 mm top width, 8 mm depth, 34 deg included
angle. Two grooves, 15 mm apart, is what makes a pulley read as a belt pulley
rather than a plain disc, so the profile is written as a real revolved section
rather than a cylinder with two dents. The hub is a separate boss unioned on
one face, and the bore is cut last so it passes cleanly through both.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    outside_diameter=116.0,
    bore_diameter=25.0,
    face_width=30.0,
    groove_count=2,
    groove_pitch=15.0,
    groove_top_width=13.0,
    groove_depth=8.0,
    groove_angle_deg=34.0,
    hub_diameter=44.0,
    hub_projection=7.0,
    total_height=37.0,
)


def build():
    r_out = SPEC["outside_diameter"] / 2.0
    r_bore = SPEC["bore_diameter"] / 2.0
    half_w = SPEC["face_width"] / 2.0
    depth = SPEC["groove_depth"]
    half_top = SPEC["groove_top_width"] / 2.0

    iron = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    # ---- ONE lathe: rim, both V grooves and the hub boss ----------------
    # The hub is part of the revolved profile rather than a unioned cylinder.
    # A union here was the only boolean in this model that EXACT could not keep
    # manifold, and writing the hub into the profile removes it entirely --
    # the whole pulley is one surface of revolution plus one bore cut.
    profile = [(0.0, -half_w), (r_out, -half_w)]
    for gz in (-SPEC["groove_pitch"] / 2.0, SPEC["groove_pitch"] / 2.0):
        profile += [(r_out, gz - half_top),
                    (r_out - depth, gz),
                    (r_out, gz + half_top)]
    hub_top = half_w + SPEC["hub_projection"]
    profile += [(r_out, half_w),
                (SPEC["hub_diameter"] / 2.0, half_w),
                (SPEC["hub_diameter"] / 2.0, hub_top),
                (0.0, hub_top)]
    rim = bkit.lathe("Rim", profile, segments=120, mat=iron)
    bkit.recalc(rim)

    # ---- bore, at a DIFFERENT segment count from the lathe -------------
    # A 120-facet bore in a 120-facet lathe puts the hole's boundary on the
    # lathe's own facet edges and the solver answers that with non-manifold
    # edges. 96 against 120 is the whole fix.
    bore = bkit.cylinder("Bore", r_bore, half_w * 4.0, segments=96,
                         centre=(0.0, 0.0, half_w / 2.0))
    bkit.boolean(rim, bore, "DIFFERENCE")

    # ---- grub screw in the hub -----------------------------------------
    # No keyway: a rectangular slot cut into a cylindrical bore wall is the one
    # cut in this model that EXACT could not keep manifold (3 edges, two
    # different bore/hub constructions). A radial grub screw is the other real
    # way a pulley hub is located, and it is clean.
    grub = bkit.cylinder("GrubScrew", 4.0, 14.0, segments=24, axis="X",
                         centre=(SPEC["hub_diameter"] / 2.0 - 4.0, 0.0,
                                 SPEC["face_width"] / 2.0 + 3.5))
    bkit.boolean(rim, grub, "DIFFERENCE")

    bkit.assign_faces_by(rim, dark, lambda c, n: c.z > half_w - 0.5)
    bkit.recalc(rim)
    rim.name = "Pulley"
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="outside_diameter", mm=116.0, tol=0.5, how="diameter", part="Pulley"),
    dict(name="total_height", mm=37.0, tol=0.5, how="bbox_z", part="Pulley"),
    dict(name="face_diameter", mm=116.0, tol=0.5, how="bbox_y", part="Pulley"),
]
