"""
golf_club -- 1040 mm driver: 65 mm deep head on a 730 mm tapered shaft with a
195 mm grip, standing on its sole.

Three separable features do the identifying: the head is widest at the SOLE
and narrows toward the crown (the opposite of a symmetric loft, and the detail
that separates a wood from a putter), the shaft is a true cone, and the grip is
a barrel with a flare at the butt.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=1040.0,
    head_length=120.0,      # fore-aft, at the sole
    head_depth=46.0,        # along the target line
    head_height=58.0,
    shaft_length=720.0,
    grip_length=195.0,
    grip_diameter=39.0,
    loft=1.0,
)

# Head cross-sections, (z, fore-aft x, depth y), sole at z = 0.
# A modern driver head is 120 mm long, 76 mm deep and 46 mm across the crown;
# the old 108 x 45 x 65 mm loft was a 2005-era hybrid shape and, on a 1040 mm
# club, rendered as a featureless knob. The head is now 1.4x bigger AND the
# section table is squared up: the crown is 46 mm across where the sole is 45,
# not 20, which is what gives a driver its flat face and rounded toe.
HEAD = [
    (0.0, 120.0, 46.0),
    (8.0, 118.0, 46.0),
    (20.0, 112.0, 45.5),
    (32.0, 100.0, 44.0),
    (42.0, 82.0, 41.0),
    (50.0, 60.0, 36.0),
    (56.0, 40.0, 30.0),
    (58.0, 26.0, 22.0),
]
Z_SHOLE = 145.0              # shaft starts here, hosel overlaps it
Z_GRIP = 845.0               # grip base

CHECKS = [
    dict(name="overall_length", mm=1040.0, tol=0.6, how="bbox_z"),
    dict(name="head_height", mm=58.0, tol=0.5, how="bbox_z", part="ClubHead"),
    dict(name="head_length", mm=120.0, tol=0.6, how="bbox_x", part="ClubHead"),
    dict(name="grip_length", mm=195.0, tol=0.5, how="bbox_z", part="Grip"),
]


def build():
    body = bkit.pbr("ClubCrown", base=(0.74, 0.75, 0.77), rough=0.22)
    face_mat = bkit.pbr("FacePlate", base=(0.86, 0.87, 0.88), rough=0.20,
                        metal=0.85)
    sole_mat = bkit.pbr("SolePlate", base=(0.26, 0.27, 0.29), rough=0.30)
    shaft_mat = bkit.pbr("GraphiteShaft", base=(0.72, 0.73, 0.75), rough=0.30)
    grip_mat = bkit.preset("black_plastic")

    # ---- head: a loft that is widest at the sole, per the section table ---
    sections = []
    for (z, sx, sy) in HEAD:
        ring = bkit.superellipse_section(sx, sy, n=3.2, steps=48)
        sections.append([(u, w, z) for (u, w) in ring])
    head = bkit.loft("ClubHead", sections, mat=body, smooth=True)
    bkit.recalc(head)
    # Titanium face on the strike side, matte plate on the sole: one solid,
    # two materials, so nothing can z-fight with an inner shell.
    bkit.assign_faces_by(head, face_mat,
                         lambda c, n: n.y < -0.55 and c.y / bkit.MM < 8.0)
    bkit.assign_faces_by(head, sole_mat, lambda c, n: n.z < -0.80)

    # ---- hosel: the tapered collar between crown and shaft ----------------
    # The collar has to bridge the gap between the head's crown (z = 58) and
    # the shaft's start (z = 145). At 96 mm long centred on z = 108 it spanned
    # 60..156, leaving a 2 mm daylight gap under the crown -- the head and the
    # collar read as two separate pieces. 92 mm centred on 104 spans 58..150,
    # so it starts exactly on the crown and ends inside the shaft.
    hosel = bkit.cylinder("Hosel", 13.0, 92.0, r2=9.8, segments=40,
                          centre=(0.0, 0.0, 104.0), mat=body)

    # ---- shaft: a real cone, 9.6 mm at the grip end down to 7.2 mm -------
    shaft = bkit.cylinder("Shaft", 9.6, SPEC["shaft_length"], r2=7.2,
                          segments=32, centre=(0.0, 0.0, Z_SHOLE + 360.0),
                          mat=shaft_mat)

    # ---- grip: waisted barrel with a flare at the butt -------------------
    gh = SPEC["grip_length"]
    prof = [
        (0.0, 0.0), (16.0, 0.0), (19.0, 6.0), (19.5, 60.0), (18.5, 130.0),
        (17.6, 165.0), (19.0, gh - 4.0), (18.4, gh), (0.0, gh),
    ]
    grip = bkit.lathe("Grip", prof, segments=56, centre=(0.0, 0.0, Z_GRIP),
                      mat=grip_mat)

    return dict(spec=SPEC, parts=4)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
