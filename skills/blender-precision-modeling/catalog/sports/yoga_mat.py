"""
yoga_mat -- 1830 x 610 mm mat rolled into a 158 mm radius tube, with the free
end unrolled onto the floor and two carry straps.

A rolled mat shown as a bare tube is a paper-towel roll, so two things sell it:
the loose end, lofted with a rising curl because a mat that has been unrolled
never lies flat, and the straps. The roll itself is bkit.tube() rather than a
lathe, because a real wall thickness needs an annulus at both ends rather than
a disc.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1830.0,
    rolled_diameter=610.0,
    mat_thickness=5.0,
    radial_layers=32.0,
    unrolled_length=400.0,
    unrolled_width=590.0,
)

RO = SPEC["rolled_diameter"] / 2.0      # 305
RI = RO - SPEC["radial_layers"]         # 273, ~16 layers of 5 mm foam
UW = SPEC["unrolled_width"]
UL = SPEC["unrolled_length"]

# (distance along the unrolled tail, height, width scale)
# The tail now starts UNDER the roll -- x starts at RO - mat_thickness - 1, so
# the first section is buried in the roll's outer wall and the sheet unrolls
# out of it. It used to start at RO - 4 mm, which is still outside the roll's
# 273 mm bore and left a visible gap between the roll and the loose flap. The
# height column starts at the roll's own tangent height rather than on the
# floor, so the sheet peels off the tube instead of lying beside it.
TAIL = [
    (0.0, 14.0, 1.0),
    (90.0, 8.0, 1.0),
    (190.0, 2.0, 1.0),
    (300.0, 0.0, 1.0),
    (UL, 22.0, 0.9),        # the tip curls back up off the floor
]

CHECKS = [
    dict(name="roll_diameter", mm=610.0, tol=0.6, how="diameter",
         part="MatRoll"),
    dict(name="roll_length", mm=1830.0, tol=0.6, how="bbox_z", part="MatRoll"),
    dict(name="unrolled_width", mm=590.0, tol=0.6, how="bbox_y", part="MatTail"),
]


def build():
    foam = bkit.pbr("MatFoam", base=(0.10, 0.30, 0.40), rough=0.72)
    edge = bkit.pbr("MatEdge", base=(0.06, 0.20, 0.28), rough=0.78)
    strap_mat = bkit.pbr("MatStrap", base=(0.05, 0.05, 0.06), rough=0.68)

    # ---- the roll: a real tube, 610 across and 32 mm of radial wall ------
    roll = bkit.tube("MatRoll", RO, RI, SPEC["length"], segments=80,
                     centre=(0.0, 0.0, SPEC["length"] / 2.0), mat=foam)
    # the inside of the roll is the cut edge of the foam, a shade darker
    bkit.assign_faces_by(roll, edge,
                         lambda c, n: c.x * n.x + c.y * n.y < 0.0)

    # ---- the unrolled end, lying on the floor and curling at the tip -----
    sections = []
    stations = []
    for i in range(len(TAIL) - 1):
        d0, h0, s0 = TAIL[i]
        d1, h1, s1 = TAIL[i + 1]
        for k in range(8):
            t = k / 8.0
            stations.append((d0 + (d1 - d0) * t, h0 + (h1 - h0) * t,
                             s0 + (s1 - s0) * t))
    stations.append(TAIL[-1])
    # x_start is inside the roll's outer wall (RO - thickness - 1), so the
    # first section is buried in the roll and the sheet visibly unrolls out of
    # it rather than starting beside it.
    x_start = RO - SPEC["mat_thickness"] - 1.0
    for (d, h, s) in stations:
        w = UW * s
        t = SPEC["mat_thickness"]
        ring = bkit.rounded_rect_section(w, t, t / 2.2, per_corner=3)
        sections.append([(x_start + d, u, h + t / 2.0 + v) for (u, v) in ring])
    tail = bkit.loft("MatTail", sections, mat=foam, smooth=True)
    bkit.recalc(tail)
    bkit.assign_faces_by(tail, edge, lambda c, n: n.z < -0.5)

    # ---- one carry strap, low on the roll --------------------------------
    # Two full-width black bands around the tube read as segmentation rings --
    # the roll looked like a stack of discs rather than one sheet of foam. A
    # single strap placed low, at the same radius as the roll so it hugs it,
    # carries the mat and stops the roll reading as segmented.
    strap = bkit.tube("MatStrap", RO + 3.0, RO - 1.0, 34.0, segments=80,
                      centre=(0.0, 0.0, 300.0), mat=strap_mat)
    buckle = bkit.rounded_box("MatStrapBuckle", 26.0, 18.0, 9.0, r=2.0,
                              segments=2,
                              centre=(RO + 2.0, 0.0, 300.0), mat=strap_mat)
    return dict(spec=SPEC, parts=4)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
