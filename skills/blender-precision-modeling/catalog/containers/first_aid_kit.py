"""
first_aid_kit -- a moulded plastic aid case: a rounded shell, a lid with a
lip, two latches and a cross on the front face.

The cross is the only thing that makes this object identifiable, so it is
modelled as real geometry (two crossing bars) rather than a material trick:
a painted cross on a rounded corner disappears at any angle but head-on.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=250.0,              # along X
    depth=180.0,              # along Y
    height=90.0,              # closed case, base to lid top (cross excluded)
    base_height=62.0,         # the shell below the lid parting line
    lid_height=28.0,
    wall=3.0,
    corner_radius=14.0,
    cross_arm=40.0,
    cross_thickness=17.0,
)

W = SPEC["width"]
D = SPEC["depth"]
BH = SPEC["base_height"]
LH = SPEC["lid_height"]
H = SPEC["height"]


def build():
    shell = bkit.pbr("AidCaseShell", base=(0.90, 0.90, 0.88), rough=0.36)
    shell_lid = bkit.pbr("AidCaseLid", base=(0.82, 0.83, 0.81), rough=0.40)
    latch = bkit.preset("black_plastic")
    red = bkit.pbr("AidCrossRed", base=(0.72, 0.06, 0.05), rough=0.34)

    # ---- shell --------------------------------------------------------------
    body = bkit.rounded_box("AidCaseBase", W, D, BH,
                            r=SPEC["corner_radius"], segments=5,
                            centre=(0.0, 0.0, BH / 2.0), mat=shell)

    # ---- lid, seated on the shell with a visible parting line --------------
    lid = bkit.rounded_box("AidCaseLid", W + 2.0, D + 2.0, LH,
                           r=SPEC["corner_radius"], segments=5,
                           centre=(0.0, 0.0, BH + LH / 2.0 - 1.5),
                           mat=shell_lid)

    # A recessed skirt just under the parting line reads as the real moulding
    # step and stops the two boxes looking like one solid lump.
    skirt = bkit.rounded_box("AidCaseSkirt", W - 10.0, D - 10.0, 5.0,
                             r=9.0, segments=3,
                             centre=(0.0, 0.0, BH - 1.0), mat=latch)

    # ---- two latches on the front, placed by symmetry ----------------------
    # lay_out() returns (x_centre, width) pairs -- iterating it bare hands the
    # tuple straight to rounded_box as a centre and the build dies on `tuple - float`.
    for i, (x, _w) in enumerate(bkit.lay_out([26.0, 26.0], gap=90.0)):
        bkit.rounded_box("AidCaseLatch%d" % (i + 1), 26.0, 8.0, 20.0,
                         r=3.0, segments=3,
                         centre=(x, -D / 2.0 - 1.0, BH + 2.0), mat=latch)

    # ---- the cross, two crossing bars on the lid top ------------------------
    # A 28 mm cross on a 250 mm case disappears at every angle but dead-on. A
    # real aid-case cross is 70-90 mm, and the bars stand proud enough to cast
    # their own shadow edge rather than reading as a printed mark.
    a = SPEC["cross_arm"]
    t = SPEC["cross_thickness"]
    bar_x = bkit.rounded_box("AidCrossArmX", a * 1.9, t, 3.0, r=1.0,
                             segments=2, centre=(0.0, 0.0, H + 1.2), mat=red)
    bar_y = bkit.rounded_box("AidCrossArmY", t, a * 1.9, 3.0, r=1.0,
                             segments=2, centre=(0.0, 0.0, H + 1.2), mat=red)

    # ---- moulded recess on the lid, so the top is not a flat slab ----------
    bkit.assign_faces_by(
        lid, shell_lid,
        lambda c, n: c.z / bkit.MM > BH + LH - 2.0 and abs(c.x / bkit.MM) > W / 4.0,
    )

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="width", mm=250.0, tol=0.5, how="bbox_x", part="AidCaseBase"),
    dict(name="depth", mm=180.0, tol=0.5, how="bbox_y", part="AidCaseBase"),
    dict(name="overall_height", mm=92.7, tol=0.3, how="bbox_z"),
]
