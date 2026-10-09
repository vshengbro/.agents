"""
climbing_hold -- 90 x 72 mm incut jug: a scooped face, a rounded back, a lip
along the bottom edge, and a counterbored fixing hole.

A climbing hold is defined by its IN CUT: the bottom edge has to overhang the
face so a finger can catch behind it. The face is therefore not a flat cap but
a dish (the first section is smaller than the second), and the lip is a real
swept ridge rather than a painted line. The fixing hole is cut with
bkit.bore(), whose segment count differs from the host's on purpose.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=90.0,
    height=72.0,
    depth=56.0,
    face_scoop=28.0,
    lip_radius=9.0,
    fixing_hole=10.0,
    fixing_depth=14.0,
)

# (y from the face plane, width, height, superellipse exponent)
BODY = [
    (0.0, 62.0, 44.0, 2.6),        # the dish, sunk into the face
    (6.0, 90.0, 72.0, 3.0),        # the widest point, the lip line
    (20.0, 88.0, 68.0, 3.0),
    (34.0, 74.0, 56.0, 2.8),
    (46.0, 52.0, 40.0, 2.6),
    (56.0, 30.0, 24.0, 2.4),       # rounded back
]

CHECKS = [
    dict(name="width", mm=90.0, tol=0.5, how="bbox_x", part="HoldBody"),
    dict(name="height", mm=72.0, tol=0.5, how="bbox_z", part="HoldBody"),
    dict(name="depth", mm=56.0, tol=0.6, how="bbox_y", part="HoldBody"),
]


def build():
    resin = bkit.pbr("HoldResin", base=(0.72, 0.30, 0.09), rough=0.52)
    # the lip is the same resin, a shade lighter: a contrasting colour makes
    # it read as a separate part glued to the hold
    lip_mat = bkit.pbr("HoldLip", base=(0.80, 0.40, 0.16), rough=0.48)

    # ---- body: a dished face lofted back to a rounded tail ---------------
    # the 6-row table is interpolated to 4x the stations, because
    # shade_smooth averages normals and a coarse loft terraces visibly
    table = []
    for i in range(len(BODY) - 1):
        y0, x0, z0, n0 = BODY[i]
        y1, x1, z1, n1 = BODY[i + 1]
        for k in range(17):
            t = k / 17.0
            # smoothstep between rows: a linear blend leaves a slope break at
            # every row, and shade_smooth draws each break as a visible band.
            # 5 stations per row was still coarse enough that the six rows
            # showed as terracing across the face; 17 makes each row's blend
            # smooth enough that the contour reads as moulded, not stepped.
            ts = t * t * (3.0 - 2.0 * t)
            table.append((y0 + (y1 - y0) * t, x0 + (x1 - x0) * ts,
                          z0 + (z1 - z0) * ts, n0 + (n1 - n0) * ts))
    table.append(BODY[-1])
    sections = []
    for (y, sx, sz, n) in table:
        ring = bkit.superellipse_section(sx, sz, n=n, steps=48)
        sections.append([(u, y, v + sz / 2.0) for (u, v) in ring])
    body = bkit.loft("HoldBody", sections, mat=resin, smooth=True)
    bkit.recalc(body)

    # ---- the incut lip: a real ridge along the bottom of the face --------
    # centred on the face plane, so the front half of the tube stands 9 mm
    # proud of the dish and the back half is buried in the body
    lip = bkit.arc_torus("HoldLip", 31.0, SPEC["lip_radius"], 204.0, 336.0,
                         centre=(0.0, 0.0, 31.0), plane="XZ", seg_major=48,
                         seg_minor=22, mat=lip_mat)

    # ---- counterbored fixing hole in the back -----------------------------
    bkit.bore(body, radius=SPEC["fixing_hole"] / 2.0, depth=40.0,
              centre=(0.0, 40.0, 24.0), axis="Y", host_segments=80)
    bkit.recalc(body)

    return dict(spec=SPEC, parts=2)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
