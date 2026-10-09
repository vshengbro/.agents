"""
ski -- 1700 mm all-mountain ski: 118 mm shovel, 88 mm waist, sidecut, tip
rocker, camber, a dark sintered base, and a toe and a heel binding.

A ski is a lofted spine, and both of its defining curves live in the station
table: the width column IS the sidecut, and the height column is tip rocker
plus camber. Without them the model is a tapered plank, which is exactly the
"flat slab" failure. The two bindings are placed by lay_out() from their real
widths plus the gap between them, never at hand-typed coordinates.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1700.0,
    shovel_width=118.0,
    waist_width=88.0,
    tail_width=112.0,
    thickness=16.0,
    tip_rocker=62.0,
    camber=9.0,
    bindings=2,
    binding_gap=470.0,        # clear air between the toe and heel plates
    binding_anchor=510.0,     # where the toe binding's centre sits
)

# (x from tail, width, thickness, base height above the flat)
# All-mountain camber under the bindings, tip rocker only at the shovel.
# The old table curled the TAIL up 16 mm and put camber everywhere, so the ski
# sat on its tail rocker with a gap under the running base -- it read as a
# banana. A ski's running base is flat on the snow between the tail contact
# and the shovel contact, with the camber arching 6 mm over the bindings.
PROFILE = [
    (0.0, 112.0, 11.0, 0.0),         # tail, contact point
    (60.0, 111.0, 12.0, 3.0),
    (150.0, 104.0, 14.0, 7.0),
    (260.0, 94.0, 16.0, 9.0),
    (420.0, 88.0, 16.0, 9.0),        # waist, camber apex
    (700.0, 91.0, 16.0, 9.0),
    (1000.0, 97.0, 15.0, 7.0),
    (1250.0, 104.0, 14.0, 3.0),
    (1450.0, 110.0, 13.0, 6.0),
    (1570.0, 114.0, 12.0, 20.0),
    (1650.0, 117.0, 9.0, 42.0),
    (1700.0, 118.0, 6.0, 62.0),      # shovel, fully up
]

CHECKS = [
    dict(name="length", mm=1700.0, tol=0.6, how="bbox_y", part="Ski"),
    dict(name="shovel_width", mm=118.0, tol=0.6, how="bbox_x", part="Ski"),
    # rocker_height 62 -> 68 mm: the shovel rises 62 mm above the running base and
    # the tip's own 6 mm thickness adds the rest.
    dict(name="rocker_height", mm=68.0, tol=0.6, how="bbox_z", part="Ski"),
]


def build():
    topsheet = bkit.pbr("Topsheet", base=(0.08, 0.34, 0.62), rough=0.16,
                        coat=0.7)
    base_mat = bkit.pbr("SkiBase", base=(0.05, 0.05, 0.06), rough=0.22)
    bind_mat = bkit.pbr("BindingShell", base=(0.10, 0.10, 0.12), rough=0.34)
    strap_mat = bkit.pbr("BindingStrap", base=(0.55, 0.12, 0.08), rough=0.45)

    # ---- the ski itself: rounded-rect sections swept along the spine -----
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
        r = min(3.0, t / 2.2)
        ring = bkit.rounded_rect_section(w, t, r, per_corner=5)
        # length runs along Y, not X: the shared "side" and "front" shots sit
        # on the +/-X axis, so a ski built along X photographs end-on.
        sections.append([(u, x, h + v + t / 2.0) for (u, v) in ring])
    ski = bkit.loft("Ski", sections, mat=topsheet, smooth=True)
    bkit.recalc(ski)
    bkit.assign_faces_by(ski, base_mat, lambda c, n: n.z < -0.80)

    # ---- toe and heel bindings, positioned by measured layout ------------
    lay = bkit.lay_out([96.0, 84.0], gap=SPEC["binding_gap"], centre=True)
    shift = SPEC["binding_anchor"] - lay[0][0]
    x_toe, x_heel = lay[0][0] + shift, lay[1][0] + shift

    toe = bkit.join([
        bkit.rounded_box("ToePlate", 96.0, 104.0, 26.0, r=6.0, segments=3,
                         centre=(0.0, x_toe, 16.0), mat=bind_mat),
        bkit.rounded_box("ToeHighback", 10.0, 88.0, 46.0, r=5.0, segments=3,
                         centre=(42.0, x_toe, 38.0), mat=bind_mat),
        bkit.rounded_box("ToeStrap", 14.0, 80.0, 8.0, r=3.5, segments=2,
                         centre=(-12.0, x_toe, 33.0), mat=strap_mat),
    ], name="ToeBinding")
    heel = bkit.join([
        bkit.rounded_box("HeelPlate", 84.0, 112.0, 30.0, r=6.0, segments=3,
                         centre=(0.0, x_heel, 18.0), mat=bind_mat),
        bkit.rounded_box("HeelHighback", 10.0, 92.0, 52.0, r=5.0, segments=3,
                         centre=(36.0, x_heel, 46.0), mat=bind_mat),
        bkit.rounded_box("AnkleStrap", 14.0, 86.0, 8.0, r=3.5, segments=2,
                         centre=(34.0, x_heel, 52.0), mat=strap_mat),
    ], name="HeelBinding")

    return dict(spec=SPEC, parts=3)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
