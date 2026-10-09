"""
envelope -- C5 / DL envelope, 220 x 110 mm.

Flat lying on the table, which is the orientation that reads: a rounded body
with a real flap folded across the top face and a visible seam. The flap is a
separate solid with real thickness -- a zero-thickness sheet here is exactly
the failure the domain rules forbid, and a bevelled body plus a second bevelled
flap gives two readable edges instead of one ghost edge.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=220.0,
    height=110.0,
    body_thickness=4.0,
    flap_thickness=0.9,
)

W = SPEC["width"]
H = SPEC["height"]


def build():
    # Bright manila: the 0.19 backdrop swallows anything darker, and a dark
    # envelope renders as a silhouette with no readable flap.
    paper = bkit.pbr("EnvelopePaper", base=(0.88, 0.83, 0.70), rough=0.70)
    flap_mat = bkit.pbr("EnvelopeFlap", base=(0.84, 0.79, 0.66), rough=0.72)

    body = bkit.rounded_box("EnvelopeBody", W, H, SPEC["body_thickness"],
                            r=2.0, segments=3,
                            centre=(0, 0, SPEC["body_thickness"] / 2.0),
                            mat=paper)

    # Flap: a triangular tab folded from the back edge, lying on the top face.
    flap_poly = [
        (-W / 2.0 + 3.0, H / 2.0 - 2.0),
        (W / 2.0 - 3.0, H / 2.0 - 2.0),
        (W / 2.0 - 3.0, -H / 2.0 + 6.0),
        (-W / 2.0 + 3.0, -H / 2.0 + 6.0),
    ]
    # Taper the front edge so it reads as a triangular flap, not a second sheet.
    flap_poly = [
        (-W / 2.0 + 4.0, H / 2.0 - 3.0),
        (W / 2.0 - 4.0, H / 2.0 - 3.0),
        (W * 0.12, -H / 2.0 + 10.0),
        (-W * 0.12, -H / 2.0 + 10.0),
    ]
    flap = bkit.extrude_profile("EnvelopeFlap", flap_poly,
                                SPEC["flap_thickness"],
                                centre=(0, 0, SPEC["body_thickness"]
                                        + SPEC["flap_thickness"] / 2.0),
                                mat=flap_mat)
    bkit.recalc(flap)
    bkit.bevel(flap, width_mm=0.25, segments=1, angle_deg=30)

    # Address window: a real recess CUT into the face with a thin pane in it.
    # A box merely laid on the surface reads as a floating shadow; a cut
    # recess gives it an edge that catches the key light.
    well = bkit.rounded_box("win_cut", 54.0, 32.0, 2.4, r=1.0,
                            centre=(-46.0, -20.0,
                                    SPEC["body_thickness"] + 0.2), mat=None)
    bkit.boolean(body, well, "DIFFERENCE")
    window = bkit.rounded_box("EnvelopeWindow", 51.0, 29.0, 0.8, r=0.6,
                              centre=(-46.0, -20.0,
                                      SPEC["body_thickness"] - 0.5),
                              mat=bkit.pbr("EnvelopeWindowPane",
                                           base=(0.93, 0.92, 0.88),
                                           rough=0.18, transmission=0.6,
                                           ior=1.45))
    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="width", mm=220.0, tol=0.6, how="bbox_x", part="EnvelopeBody"),
    dict(name="height", mm=110.0, tol=0.6, how="bbox_y", part="EnvelopeBody"),
    dict(name="flap_thickness", mm=0.9, tol=0.35, how="bbox_z",
         part="EnvelopeFlap"),
]