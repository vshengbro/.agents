"""
surfboard -- 1830 x 508 mm shortboard: a squash tail, a real rocker curve, a
tucked rail, and three fins.

The brief for a board is "not a flat slab", and the answer is the station
table: the height column is nose rocker plus tail rocker, and it is the ONLY
thing separating a surfboard from a plank. The width column is the plan
outline, the thickness column is the foil. The fins are swept sections rather
than flat plates, and the whole thing reads as a board from the side view.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1830.0,
    width=508.0,
    thickness=57.0,
    nose_rocker=138.0,
    tail_rocker=62.0,
    fins=3,
    fin_height=92.0,
)

# (x from tail, half width, thickness, base height above the flat)
# The tail is a proper round pin, not a flat squash: the width runs back down
# and the thickness goes to a point at the very tail, so the plan outline closes
# and the side view shows a curl instead of a cut-off end. The last third of the
# nose is pulled in tighter and lifted harder, which is what makes a shortboard
# read as a shortboard rather than a plank with a bent end.
PROFILE = [
    (0.0, 96.0, 6.0, 34.0),         # round pin: narrow, thin, lifted
    (34.0, 176.0, 17.0, 26.0),
    (80.0, 224.0, 27.0, 14.0),
    (160.0, 246.0, 36.0, 5.0),
    (300.0, 254.0, 46.0, 1.0),
    (520.0, 254.0, 53.0, 0.0),       # wide point / thickest
    (760.0, 250.0, 55.0, 0.0),
    (1000.0, 238.0, 52.0, 3.0),
    (1230.0, 214.0, 43.0, 12.0),
    (1420.0, 176.0, 32.0, 30.0),
    (1580.0, 130.0, 22.0, 56.0),
    (1700.0, 82.0, 14.0, 88.0),
    (1780.0, 42.0, 8.0, 120.0),
    (1830.0, 12.0, 5.0, 138.0),      # nose, fully up
]

CHECKS = [
    dict(name="length", mm=1830.0, tol=0.6, how="bbox_y", part="Surfboard"),
    dict(name="width", mm=508.0, tol=0.6, how="bbox_x", part="Surfboard"),
    dict(name="rocker_height", mm=143.0, tol=0.8, how="bbox_z", part="Surfboard"),
]


def _bar(name, p0, p1, w, t, mat=None):
    """A straight fin blade: rounded-rect section swept from p0 to p1.

    d x (0,1,0) lies in the board's XZ plane, so w is the chord and t the
    foil thickness.
    """
    d = [p1[i] - p0[i] for i in range(3)]
    ln = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 1.0
    d = [c / ln for c in d]
    ex = [d[2], 0.0, -d[0]]                       # in-plane, perpendicular to d
    el = math.sqrt(ex[0] ** 2 + ex[2] ** 2) or 1.0
    ex = [ex[0] / el, 0.0, ex[2] / el]
    ey = [d[1] * ex[2] - d[2] * ex[1],
          d[2] * ex[0] - d[0] * ex[2],
          d[0] * ex[1] - d[1] * ex[0]]            # = d x ex
    ring = bkit.rounded_rect_section(w, t, min(2.0, t / 2.2), per_corner=4)
    s0 = [(p0[0] + ex[0] * u + ey[0] * v, p0[1] + ex[1] * u + ey[1] * v,
           p0[2] + ex[2] * u + ey[2] * v) for (u, v) in ring]
    s1 = [(p1[0] + ex[0] * u + ey[0] * v, p1[1] + ex[1] * u + ey[1] * v,
           p1[2] + ex[2] * u + ey[2] * v) for (u, v) in ring]
    ob = bkit.loft(name, [s0, s1], mat=mat)
    bkit.recalc(ob)
    return ob


def build():
    deck = bkit.pbr("SurfDeck", base=(0.88, 0.90, 0.91), rough=0.14, coat=0.8)
    rail = bkit.pbr("SurfRail", base=(0.10, 0.42, 0.66), rough=0.16, coat=0.7)
    glass = bkit.pbr("BottomGlass", base=(0.05, 0.05, 0.06), rough=0.10,
                     coat=0.9)
    fin_mat = bkit.pbr("FinGlass", base=(0.16, 0.20, 0.26), rough=0.14,
                       coat=0.8)

    # ---- the board: rounded-rect sections along the rocker spine ----------
    stations = []
    for i in range(len(PROFILE) - 1):
        x0, y0, t0, h0 = PROFILE[i]
        x1, y1, t1, h1 = PROFILE[i + 1]
        for k in range(6):
            t = k / 6.0
            stations.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                             t0 + (t1 - t0) * t, h0 + (h1 - h0) * t))
    stations.append(PROFILE[-1])
    sections = []
    for (x, hy, t, h) in stations:
        r = min(6.0, t / 2.4, hy / 2.4)
        ring = bkit.rounded_rect_section(2.0 * hy, t, r, per_corner=6)
        # length along Y: the shared side/front shots sit on the +/-X axis, and
        # a board built along X photographs nose-on
        sections.append([(u, x, h + v + t / 2.0) for (u, v) in ring])
    board = bkit.loft("Surfboard", sections, mat=deck, smooth=True)
    bkit.recalc(board)
    bkit.assign_faces_by(board, glass, lambda c, n: n.z < -0.80)
    bkit.assign_faces_by(board, rail, lambda c, n: n.x < -0.93)

    # ---- three fins: a centre thruster and a pair, laid out from the tail --
    # every fin root is sunk INTO the foil, not sat on it: the board's base
    # line at x = 120 is z = 20, at x = 330 it is z = 3.
    fh = SPEC["fin_height"]
    fins = [
        _bar("FinCentre", (0.0, 120.0, 34.0), (0.0, 86.0, 34.0 - fh),
             112.0, 6.0, fin_mat),
        _bar("FinLeft", (122.0, 330.0, 22.0), (152.0, 300.0, 22.0 - 0.62 * fh),
             104.0, 5.5, fin_mat),
        _bar("FinRight", (-122.0, 330.0, 22.0), (-152.0, 300.0, 22.0 - 0.62 * fh),
             104.0, 5.5, fin_mat),
    ]
    fin = bkit.join(fins, name="Fins")
    return dict(spec=SPEC, parts=2)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
