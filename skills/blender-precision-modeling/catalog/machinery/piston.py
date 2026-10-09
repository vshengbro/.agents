"""
piston -- 82 mm forged piston: crown, three ring lands, hollow skirt, pin bosses.

The ring lands are the detail that makes a piston read as a piston, so they are
cut into the revolved profile itself (three grooves at a real 6 mm ring pitch)
rather than modelled as separate rings -- a separate ring object inside the
groove z-fights and doubles the non-manifold count. The underside is a real
hollow: the profile returns up the inner skirt wall to an internal roof, which
is what the wrist-pin boss is then attached to.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    outside_diameter=82.0,
    total_height=62.0,
    crown_height=4.0,
    ring_groove_count=3,
    ring_groove_pitch=6.0,
    ring_groove_depth=2.4,
    ring_land_width=3.0,
    skirt_wall=5.0,
    internal_roof_height=18.0,
    pin_boss_diameter=26.0,
    pin_bore_diameter=22.0,
    pin_height=30.0,
    compression_height=52.0,
)


def build():
    r_out = SPEC["outside_diameter"] / 2.0
    r_in = r_out - SPEC["skirt_wall"]
    h = SPEC["total_height"]
    d = SPEC["ring_groove_depth"]

    alloy = bkit.pbr("anodised", base=(0.52, 0.53, 0.55), metal=0.45, rough=0.40)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    # ---- revolved piston section ---------------------------------------
    prof = [(0.0, 0.0), (r_out - 2.0, 0.0), (r_out, 2.0), (r_out, SPEC["crown_height"])]
    z0 = 6.0
    for i in range(SPEC["ring_groove_count"]):
        prof += [(r_out, z0),
                 (r_out - d, z0 + 1.2),
                 (r_out - d, z0 + 1.2 + 1.8),
                 (r_out, z0 + SPEC["ring_groove_pitch"])]
        z0 += SPEC["ring_groove_pitch"]
    prof += [(r_out, h), (r_in, h), (r_in, SPEC["internal_roof_height"]),
             (0.0, SPEC["internal_roof_height"])]

    # Author crown-up. The profile above is written with the crown at z=0 and
    # the skirt at z=h, which reads correctly but means sit_on_floor() stands
    # the piston on its crown with the hollow skirt facing the camera. Mirroring
    # the section puts the crown at the top and the open skirt on the floor,
    # which is how a piston stands on a bench. recalc() below fixes the winding
    # that the mirror reverses.
    prof = [(r, h - z) for (r, z) in prof]

    piston = bkit.lathe("Piston", prof, segments=128, mat=alloy)
    bkit.recalc(piston)

    # ---- wrist-pin boss + bore -----------------------------------------
    # The boss must reach 2 mm INTO the skirt wall. Ending it exactly at the
    # wall (76 -> 36 = the wall's inner radius) makes its end cap tangent to
    # that wall, and the boolean answers the tangency with 3 non-manifold edges.
    # ---- pin boss + bore, mirrored with the section --------------------
    z_pin = h - SPEC["pin_height"]
    boss = bkit.cylinder("PinBoss", SPEC["pin_boss_diameter"] / 2.0, 76.0,
                         segments=64, axis="Y", centre=(0.0, 0.0, z_pin),
                         mat=alloy)
    bkit.boolean(piston, boss, "UNION")
    bore = bkit.cylinder("PinBore", SPEC["pin_bore_diameter"] / 2.0, 78.0,
                         segments=64, axis="Y", centre=(0.0, 0.0, z_pin))
    bkit.boolean(piston, bore, "DIFFERENCE")
    bkit.recalc(piston)

    # ---- pin boss bosses on the skirt, outside the bore ----------------
    bkit.assign_faces_by(piston, dark, lambda c, n: c.y > 30.0)
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="outside_diameter", mm=82.0, tol=0.4, how="diameter", part="Piston"),
    dict(name="total_height", mm=62.0, tol=0.4, how="bbox_z", part="Piston"),
    dict(name="overall_diameter_y", mm=82.0, tol=0.4, how="bbox_y", part="Piston"),
]
