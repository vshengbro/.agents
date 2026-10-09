"""
carton -- 1 litre gable-top milk carton: a rectangular body, a gable (roof)
panel with a ridge, and a screw spout cap on the slope.

A gable top is the one packaging shape that is genuinely *lofted*: the body is
a rounded rectangle and the top narrows along a ridge. Both halves are solid
revolutions of rectangular sections, so the model stays watertight without a
single boolean.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=70.0,               # gable carton body, across the front
    depth=70.0,               # through the gable, front to back
    body_height=195.0,        # base to the shoulder
    gable_height=40.0,        # shoulder to the ridge
    overall_height=235.0,       # gable apex; the ridge is capped flush with it
    spout_diameter=24.0,
    spout_height=9.0,
    volume_l=1.0,
)

W = SPEC["width"]
D = SPEC["depth"]
BH = SPEC["body_height"]
GH = SPEC["gable_height"]
H = SPEC["overall_height"]


def sec(sx, sy, r, z, per_corner=4):
    """A rounded-rectangle loft section lifted to height `z`.

    `rounded_rect_section()` returns flat (x, y) pairs, but `loft()` builds its
    mesh with `v(p)` on every vertex -- and v() unpacks exactly three numbers.
    Handing it 2D points fails with "expected 3, got 2", so every section is
    lifted to 3D here rather than by mutating the object afterwards.

    `per_corner` is fixed at 4 for the whole gable: the point count is
    4 * (per_corner + 1), and loft() rejects rings of differing length, so a
    single tighter corner on one section is enough to fail the build.
    """
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=per_corner)]


def build():
    carton = bkit.pbr("CartonBoard", base=(0.93, 0.94, 0.95), rough=0.42)
    carton_shade = bkit.pbr("CartonBoardShade", base=(0.80, 0.83, 0.86),
                            rough=0.46)
    blue = bkit.pbr("CartonBlue", base=(0.06, 0.26, 0.62), rough=0.38)
    cap = bkit.preset("white_plastic")

    # ---- body: rectangular section, very slightly tapered in at the top -----
    # The sections already carry their own absolute z (0 .. BH), so the loft
    # needs no extra lift -- adding one here would stand the carton on stilts.
    body = bkit.loft("CartonBody", [
        sec(W, D, 4.0, 0.0),
        sec(W, D, 4.0, BH * 0.55),
        sec(W, D, 4.0, BH - 6.0),
        sec(W, D - 3.0, 4.0, BH),
    ], mat=carton)
    bkit.recalc(body)

    # ---- gable: the same section narrowed to a ridge over the last 40 mm ----
    gable = bkit.loft("CartonGable", [
        sec(W, D - 3.0, 4.0, BH),
        sec(W, 12.0, 5.0, BH + GH * 0.72),
        sec(W, 5.0, 2.0, BH + GH),
    ], mat=carton)
    bkit.recalc(gable)

    # ---- the crimped ridge seal along the top -------------------------------
    # Seated on the gable apex by BODY + GABLE, never by overall_height: tying
    # the ridge to the declared overall height means editing the number moves
    # the geometry, and the two then disagree by construction.
    ridge = bkit.rounded_box("CartonRidge", W + 2.0, 7.0, 5.0, r=1.6,
                             segments=3, centre=(0.0, 0.0, BH + GH - 2.5),
                             mat=carton_shade)

    # ---- screw spout cap on the front slope ---------------------------------
    spout = bkit.lathe("CartonSpout", [
        (0.0, 0.0), (10.0, 0.0), (10.0, 2.0), (12.0, 3.0),
        (12.0, SPEC["spout_height"]), (0.0, SPEC["spout_height"]),
    ], segments=48, centre=(0.0, -D / 2.0 + 16.0, BH + 4.0), mat=cap)

    # ---- printed panel, as a second material on the real body ---------------
    bkit.assign_faces_by(
        body, blue,
        lambda c, n: 40.0 < c.z / bkit.MM < BH - 22.0
        and abs(c.y / bkit.MM) > (D / 2.0 - 1.5),
    )
    bkit.assign_faces_by(
        gable, carton_shade,
        lambda c, n: c.z / bkit.MM < BH + GH * 0.45,
    )

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="width", mm=70.0, tol=0.5, how="bbox_x", part="CartonBody"),
    dict(name="body_height", mm=195.0, tol=0.5, how="bbox_z", part="CartonBody"),
    dict(name="overall_height", mm=235.0, tol=0.3, how="bbox_z"),
]
