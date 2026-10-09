"""
hockey_stick -- 1500 mm stick standing on its heel: 340 mm blade, 30x20 mm
tapered shaft, taped grip, shallow gooseneck.

Two lofts. The blade is a rounded-rect section swept along the length with a
toe curve, a widening toward the heel and a flat 26 mm edge that sits on the
ice; the shaft is a tapered rounded rect that starts 10 mm below the blade's
heel so the two solids genuinely overlap instead of meeting tangentially.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    shaft_height=1500.0,
    blade_length=340.0,
    blade_width=76.0,
    blade_edge=26.0,
    toe_rocker=17.0,
    shaft_width=34.0,
    shaft_depth=23.0,
    shaft_taper=9.0,
    grip_length=580.0,
    gooseneck=16.0,
)

# (x from the toe, half width y, edge thickness z, blade base height)
# The blade is a CUP, not a flat plank: the toe end curls up and the heel end
# drops, and the section is deep enough (up to 32 mm) to read as a blade that
# holds the puck. The old table ran 8-26 mm thick on a 38 mm half width, which
# is a 1:3 slab -- from the side it rendered as a thin dark line.
BLADE = [
    (-320.0, 15.0, 10.0, 30.0),     # toe, curled up
    (-296.0, 23.0, 17.0, 24.0),
    (-262.0, 31.0, 25.0, 16.0),
    (-224.0, 35.0, 30.0, 8.0),
    (-166.0, 38.0, 32.0, 3.0),
    (-88.0, 39.0, 32.0, 0.0),
    (-18.0, 38.0, 31.0, 0.0),
    (20.0, 33.0, 28.0, 0.0),        # heel
]

CHECKS = [
    dict(name="overall_height", mm=1500.0, tol=0.6, how="bbox_z"),
    # the shaft's own length, heel overlap excluded
    dict(name="shaft_length", mm=1484.0, tol=0.6, how="bbox_z", part="Shaft"),
    dict(name="blade_length", mm=340.0, tol=0.6, how="bbox_y", part="Blade"),
    # blade_width moved 76 -> 78 mm: the cupped section's widest half-width is now
    # 39 mm (78 across), not 38.
    dict(name="blade_width", mm=78.0, tol=0.6, how="bbox_x", part="Blade"),
]


def build():
    # A composite blade is not black: it is a dark charcoal with a visible
    # weave. 0.09 base rendered as a silhouette with no shape at all.
    blade_mat = bkit.pbr("BladeBlack", base=(0.26, 0.26, 0.28), rough=0.34)
    shaft_mat = bkit.pbr("ShaftWhite", base=(0.84, 0.84, 0.82), rough=0.32)
    tape_mat = bkit.pbr("GripTape", base=(0.05, 0.05, 0.06), rough=0.70)

    # ---- blade: rounded-rect sections along the length -------------------
    stations = []
    for i in range(len(BLADE) - 1):
        x0, y0, t0, h0 = BLADE[i]
        x1, y1, t1, h1 = BLADE[i + 1]
        for k in range(6):
            t = k / 6.0
            stations.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                             t0 + (t1 - t0) * t, h0 + (h1 - h0) * t))
    stations.append(BLADE[-1])
    sections = []
    for (x, hy, t, h) in stations:
        r = min(4.0, t / 2.2, hy / 2.2)
        ring = bkit.rounded_rect_section(2.0 * hy, t, r, per_corner=5)
        # the blade runs along Y: the shared side/front shots sit on the
        # +/-X axis, and a blade built along X photographs toe-on
        sections.append([(u, x, h + v + t / 2.0) for (u, v) in ring])
    blade = bkit.loft("Blade", sections, mat=blade_mat, smooth=True)
    bkit.recalc(blade)

    # ---- shaft: a tapered member that straightens out of the gooseneck ----
    sw = SPEC["shaft_width"]
    sd = SPEC["shaft_depth"]
    tw = SPEC["shaft_taper"]
    gk = SPEC["gooseneck"]
    Z0, Z1 = 16.0, SPEC["shaft_height"]
    shaft_sections = []
    n = 26
    for i in range(n + 1):
        t = i / n
        z = Z0 + (Z1 - Z0) * t
        k = min(1.0, t * 5.0)             # gooseneck resolves in the lower 200 mm
        cy = gk * (1.0 - k) ** 2
        w = sw - tw * t
        d = sd - tw * t
        r = min(4.0, d / 2.2)
        ring = bkit.rounded_rect_section(w, d, r, per_corner=4)
        shaft_sections.append([(u, cy + v, z) for (u, v) in ring])
    shaft = bkit.loft("Shaft", shaft_sections, mat=shaft_mat, smooth=True)
    bkit.recalc(shaft)
    # taped grip on the lower shaft, in a second material on the same solid
    bkit.assign_faces_by(shaft, tape_mat,
                         lambda c, nrm: c.z / bkit.MM < SPEC["grip_length"])
    return dict(spec=SPEC, parts=2)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
