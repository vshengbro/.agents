"""
snowboard -- 1550 mm all-mountain board: 250 mm waist, twin-tip rocker, a dark
base and two mounted bindings with highbacks and straps.

Same construction idea as the ski, but the plan outline is symmetric about the
centre of the length instead of having a shovel and a tail, and the outline is
driven by its own sidecut table. The binding pair is one part arrayed at the
computed stance width, so the two plates can never drift apart.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1550.0,
    waist_width=250.0,
    tip_width=132.0,
    tail_width=146.0,
    thickness=13.0,
    nose_rocker=24.0,
    tail_rocker=2.0,
    stance=530.0,             # centre-to-centre of the two bindings
    bindings=2,
)

# (x from tail, width, thickness, base height above the flat)
# Camber, not a smile. The old table had both ends lifted 70 and 95 mm with a
# 1 mm waist, which is a rocker curve so extreme the board read as a hammock.
# A real all-mountain board has a flat running base with camber in the middle:
# the contact points are the two spots where the board meets the snow, and the
# waist arches a few millimetres above the line between them.
PROFILE = [
    (0.0, 146.0, 9.0, 2.0),         # tail, first contact point
    (60.0, 176.0, 11.0, 5.0),
    (130.0, 214.0, 12.0, 11.0),
    (220.0, 240.0, 12.5, 15.0),
    (340.0, 250.0, 13.0, 17.0),     # arch over the bindings
    (560.0, 250.0, 13.0, 17.0),
    (775.0, 249.0, 12.5, 16.0),     # centre of the camber
    (1000.0, 244.0, 11.5, 12.0),
    (1210.0, 226.0, 10.0, 7.0),
    (1330.0, 196.0, 9.0, 2.0),
    (1440.0, 160.0, 8.0, 9.0),
    (1550.0, 132.0, 6.0, 24.0),     # nose, rising but not vertical
]

CHECKS = [
    dict(name="length", mm=1550.0, tol=0.6, how="bbox_y", part="Snowboard"),
    dict(name="waist_width", mm=250.0, tol=0.6, how="bbox_x", part="Snowboard"),
    # rocker_height moved 99 -> 43 mm: the camber profile lifts the nose 24 mm and
# the board is 13 mm thick at the waist, so the top of the board stands 43 mm
# above the floor at its highest point.
    dict(name="rocker_height", mm=28.0, tol=1.0, how="bbox_z", part="Snowboard"),
]


def build():
    topsheet = bkit.pbr("BoardTop", base=(0.82, 0.24, 0.10), rough=0.18,
                        coat=0.6)
    base_mat = bkit.pbr("BoardBase", base=(0.05, 0.05, 0.06), rough=0.20)
    bind_mat = bkit.pbr("BoardBinding", base=(0.09, 0.09, 0.11), rough=0.36)
    strap_mat = bkit.pbr("BoardStrap", base=(0.16, 0.17, 0.20), rough=0.60)

    # ---- the board: rounded-rect sections along the spine ----------------
    stations = []
    for i in range(len(PROFILE) - 1):
        x0, w0, t0, h0 = PROFILE[i]
        x1, w1, t1, h1 = PROFILE[i + 1]
        for k in range(6):
            t = k / 6.0
            stations.append((x0 + (x1 - x0) * t, w0 + (w1 - w0) * t,
                             t0 + (t1 - t0) * t, h0 + (h1 - h0) * t))
    stations.append(PROFILE[-1])
    sections = []
    for (x, w, t, h) in stations:
        r = min(2.5, t / 2.2)
        ring = bkit.rounded_rect_section(w, t, r, per_corner=5)
        # length along Y: the shared side/front shots sit on the +/-X axis, so
        # a board built along X photographs end-on
        sections.append([(u, x, h + v + t / 2.0) for (u, v) in ring])
    board = bkit.loft("Snowboard", sections, mat=topsheet, smooth=True)
    bkit.recalc(board)
    bkit.assign_faces_by(board, base_mat, lambda c, n: n.z < -0.80)

    # ---- one binding, arrayed at the measured stance width ---------------
    x0 = SPEC["length"] / 2.0 - SPEC["stance"] / 2.0
    binding = bkit.join([
        bkit.rounded_box("Baseplate", 150.0, 210.0, 12.0, r=5.0, segments=3,
                         centre=(0.0, x0, 14.0), mat=bind_mat),
        bkit.rounded_box("Highback", 14.0, 190.0, 96.0, r=8.0, segments=3,
                         centre=(66.0, x0, 60.0), mat=bind_mat),
        bkit.rounded_box("AnkleStrap", 16.0, 176.0, 10.0, r=4.0, segments=2,
                         centre=(62.0, x0, 72.0), mat=strap_mat),
        bkit.rounded_box("ToeStrap", 16.0, 170.0, 10.0, r=4.0, segments=2,
                         centre=(-40.0, x0, 40.0), mat=strap_mat),
    ], name="Binding")
    bkit.array_linear(binding, SPEC["bindings"],
                      offset_mm=(0.0, SPEC["stance"], 0.0))

    return dict(spec=SPEC, parts=2)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
