"""
capacitor -- 10.6 x 10.6 x 40 mm radial electrolytic capacitor: PVC sleeved
can, rubber base seal, crimp bead, scored top vent and two axial lead wires.

`tiny` class, so the whole assembly must fit inside [2.5, 60] mm on its
longest axis -- which is why the leads are 16 mm rather than the 25 mm a real
105 C part has. The polarity stripe is a `tube` standing 0.3 mm proud of the
can: flush, it would touch the can along a full cylinder and read as nothing
at all.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    can_diameter=10.0,
    can_height=26.0,
    overall_height=40.0,
    lead_diameter=0.9,
    lead_length=16.0,
    lead_spacing=5.0,
)

R = SPEC["can_diameter"] / 2.0
LEAD_R = SPEC["lead_diameter"] / 2.0
STRIPE = 0.3                        # polarity stripe proud of the sleeve


def build():
    sleeve = bkit.pbr("CapSleeve", base=(0.09, 0.11, 0.32), rough=0.42)
    black = bkit.preset("black_plastic")
    stripe_mat = bkit.pbr("CapStripe", base=(0.85, 0.86, 0.88), rough=0.38)
    tin = bkit.preset("brushed_metal")
    rubber = bkit.preset("rubber")

    # ---- two axial lead wires --------------------------------------------
    for side, mx in ((-1.0, tin), (1.0, black)):
        bkit.cylinder("Lead%d" % int(side), LEAD_R, SPEC["lead_length"],
                      segments=16,
                      centre=(side * SPEC["lead_spacing"] / 2.0, 0.0, 8.0),
                      mat=mx)

    # ---- rubber base seal, overlapping the can by 2 mm -------------------
    bkit.lathe("CapBase", [(0.0, 12.0), (R, 12.0), (R, 16.0), (0.0, 16.0)],
               segments=40, mat=rubber)

    # ---- the can. lathe profiles carry ABSOLUTE z. -----------------------
    bkit.lathe("CapCan", [(0.0, 14.0), (R, 14.0), (R, 40.0), (0.0, 40.0)],
               segments=40, mat=sleeve)

    # ---- polarity stripe standing 0.3 mm proud of the sleeve -------------
    bkit.tube("PolarityStripe", R + STRIPE, R - 0.2, 22.0, segments=40,
              centre=(0.0, 0.0, 27.0), mat=stripe_mat)

    # ---- crimp bead round the top and the scored X vent ------------------
    bkit.torus("CrimpBead", 4.8, 0.7, seg_major=40, seg_minor=10,
               centre=(0.0, 0.0, 39.0), mat=stripe_mat)
    vent = [bkit.box("_vx", 6.0, 1.0, 0.8, centre=(0.0, 0.0, 40.0),
                     mat=black),
            bkit.box("_vy", 1.0, 6.0, 0.8, centre=(0.0, 0.0, 40.0),
                     mat=black)]
    bkit.join(vent, name="TopVent")

    # ---- printed value legend on the sleeve ------------------------------
    bkit.rounded_box("CapLegend", 4.0, 0.6, 14.0, r=0.2, segments=2,
                     centre=(0.0, -R - 0.3, 28.0), mat=stripe_mat)

    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="can_diameter", mm=10.0, tol=0.4, how="diameter",
         part="CapCan"),
    dict(name="can_height", mm=26.0, tol=0.4, how="bbox_z", part="CapCan"),
    dict(name="base_diameter", mm=10.0, tol=0.4, how="diameter",
         part="CapBase"),
    dict(name="lead_length", mm=16.0, tol=0.3, how="bbox_z", part="Lead-1"),
    dict(name="overall_height", mm=40.4, tol=0.5, how="bbox_z"),
]