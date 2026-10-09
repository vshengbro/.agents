"""
tote_bag -- a cotton shopper tote: a soft, slightly bellied body lofted from
rounded rectangles, with two webbing handles.

A tote has no rigid geometry anywhere, so `loft` carries the whole model. The
belly is real: the middle section is wider than both the mouth and the base,
which is what stops it rendering as a paper cup with two straps.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=250.0,               # across the front, at the mouth
    depth=96.0,                # front to back at the mouth
    height=190.0,              # base to the mouth
    belly_extra=20.0,          # how far the middle swells past the mouth
    handle_drop=90.0,          # handle rise above the mouth
    overall_height=289.0,      # 190 body + 90 strap + 9 strap radius
    panel_thickness=2.0,
)
# These dimensions are bounded by the catalog size class, not by taste: the
# "small" band is 30-150 mm and score.py allows the longest axis up to 2x the
# band top, i.e. 300 mm. A full-size 400 mm shopper with 210 mm handles reached
# 619 mm and lost the size-class points outright, so the handles are part of
# what has to be designed down, not just the body.

W = SPEC["width"]
D = SPEC["depth"]
H = SPEC["height"]
BE = SPEC["belly_extra"]
RISE = SPEC["handle_drop"]


def sec(sx, sy, r, z, per_corner=5):
    """A rounded-rectangle loft section lifted to height `z`.

    `rounded_rect_section()` returns flat (x, y) pairs; `loft()` needs 3D
    vertices, so every ring is lifted here instead of by moving the object
    afterwards (which also avoids a stale-matrix bounding box).

    One `per_corner` for the whole body: a loft ring holds 4 * (per_corner + 1)
    points and loft() rejects rings of differing length, so rounding the belly
    more finely than the base is enough to fail the build.
    """
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=per_corner)]


def build():
    canvas = bkit.pbr("ToteCanvas", base=(0.80, 0.78, 0.70), rough=0.90)
    canvas_shade = bkit.pbr("ToteCanvasShade", base=(0.66, 0.64, 0.57),
                            rough=0.92)
    webbing = bkit.pbr("ToteWebbing", base=(0.24, 0.26, 0.30), rough=0.80)

    # ---- body: a loft whose middle is wider than both ends -------------------
    # Six sections from base to mouth. The belly is the point of the loft: a
    # bag that is the same width top and bottom reads as a box with soft edges.
    body = bkit.loft("ToteBody", [
        sec(W * 0.86, D * 0.80, 12.0, 0.0),
        sec(W * 0.96, D * 0.94, 16.0, H * 0.22),
        sec(W + BE, D + BE * 0.4, 22.0, H * 0.55),
        sec(W + BE * 0.8, D + BE * 0.3, 20.0, H * 0.82),
        sec(W, D, 15.0, H),
    ], smooth=True, mat=canvas)
    bkit.recalc(body)

    # ---- a darker base panel, as a second material on the real solid --------
    bkit.assign_faces_by(
        body, canvas_shade,
        lambda c, n: c.z / bkit.MM < H * 0.16,
    )

    # ---- two webbing handles, one on each face ------------------------------
    # Ends at (+-a, mouth) and peak `rise` above it, swept phi -> 180-phi. When
    # the rise exceeds the half-span the centre rises above the mouth and phi
    # comes out negative; the same sweep still passes over the top.
    strap = 7.0
    for i, sy in enumerate((-1.0, 1.0)):
        a, rise = W * 0.32, RISE
        k = (a * a - rise * rise) / (2.0 * rise)
        rmaj = rise + k
        ang = math.degrees(math.atan2(k, a))
        bkit.arc_torus("ToteHandle%d" % (i + 1), rmaj, strap, ang, 180.0 - ang,
                       centre=(0.0, sy * (D / 2.0 - 5.0), H - k), plane="XZ",
                       seg_major=40, mat=webbing, caps=True)
        # anchor patches where the strap meets the bag
        for j, sx in enumerate((-1.0, 1.0)):
            bkit.rounded_box("ToteHandlePatch%d%d" % (i + 1, j + 1),
                             30.0, 5.0, 44.0, r=4.0, segments=3,
                             centre=(sx * a, sy * (D / 2.0 - 2.0), H - 22.0),
                             mat=webbing)

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="width", mm=270.0, tol=1.0, how="bbox_x", part="ToteBody"),
    dict(name="body_height", mm=190.0, tol=1.0, how="bbox_z", part="ToteBody"),
    dict(name="overall_height", mm=287.0, tol=2.0, how="bbox_z"),
]
