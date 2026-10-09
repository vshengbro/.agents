"""
shopping_bag -- a flat-bottomed paper shopping bag with folded-in side
gussets and two rope handles.

The gusset is the whole point of the silhouette, and a rounded rectangle
cannot express it: the section is a ten-point ring whose side panels pinch
inward to a crease at mid-depth. Every loft section uses the same ten points,
because `loft` requires equal-length rings.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=260.0,              # across the front panel
    depth=110.0,              # front panel to back panel, flat
    height=230.0,             # base to the mouth
    gusset_fold=22.0,         # how far the side crease pulls inward
    handle_rise=58.0,         # rope handle rise above the mouth
    overall_height=293.0,
    board=0.4,                # paper thickness, read as a sealed edge
)

W = SPEC["width"]
D = SPEC["depth"]
H = SPEC["height"]
FOLD = SPEC["gusset_fold"]
RISE = SPEC["handle_rise"]


def bag_section(w, d, fold):
    """One closed ten-point bag ring: front panel, folded side, back panel.

    The side panels fold *inward*, so the crease sits at x = w/2 - fold while
    the panel corners stay at x = w/2. Ten points, always, so any two sections
    can be lofted together.
    """
    hw, hd = w / 2.0, d / 2.0
    return [
        (-hw, -hd), (hw, -hd),                 # front panel
        (hw, -hd * 0.42), (hw - fold, 0.0), (hw, hd * 0.42),   # right gusset
        (hw, hd), (-hw, hd),                   # back panel
        (-hw, hd * 0.42), (-hw + fold, 0.0), (-hw, -hd * 0.42),  # left gusset
    ]


def build():
    paper = bkit.pbr("ShoppingPaper", base=(0.78, 0.62, 0.42), rough=0.80)
    paper_inner = bkit.pbr("ShoppingPaperInner", base=(0.64, 0.50, 0.33),
                           rough=0.86)
    rope = bkit.pbr("ShoppingRope", base=(0.84, 0.78, 0.62), rough=0.86)
    print_mat = bkit.pbr("ShoppingPrint", base=(0.14, 0.30, 0.22), rough=0.70)

    # ---- bag: lofted from a narrow base to the full mouth -------------------
    body = bkit.loft("ShoppingBagBody", [
        _lift(bag_section(W * 0.80, D * 0.74, FOLD * 0.7), 0.0),
        _lift(bag_section(W * 0.80, D * 0.74, FOLD * 0.7), H * 0.02),
        _lift(bag_section(W * 0.90, D * 0.88, FOLD * 0.9), H * 0.45),
        _lift(bag_section(W, D, FOLD), H),
    ], mat=paper)
    bkit.recalc(body)

    # ---- the inside of the bag, as a second material on the same solid ------
    bkit.assign_faces_by(
        body, paper_inner,
        lambda c, n: c.z / bkit.MM < H * 0.30,
    )

    # ---- printed panel, so the front is not one flat tone -------------------
    bkit.assign_faces_by(
        body, print_mat,
        lambda c, n: H * 0.42 < c.z / bkit.MM < H * 0.74
        and c.y / bkit.MM < -D * 0.40,
    )

    # ---- two rope handles ---------------------------------------------------
    # The arc's ENDS sit at (+-a, mouth) and its PEAK is `rise` above the
    # mouth: k = (a^2 - rise^2) / (2 * rise), sweeping phi -> 180-phi.
    a, rise = W * 0.28, RISE
    k = (a * a - rise * rise) / (2.0 * rise)
    rmaj = rise + k
    ang = math.degrees(math.atan2(k, a))
    for i, sy in enumerate((-1.0, 1.0)):
        bkit.arc_torus("ShoppingHandle%d" % (i + 1), rmaj, 5.0,
                       ang, 180.0 - ang,
                       centre=(0.0, sy * (D / 2.0 - 4.0), H - k), plane="XZ",
                       seg_major=36, mat=rope, caps=True)

    return dict(spec=SPEC, parts=3)


def _lift(section, z):
    """Return a bag ring raised to height `z` (sections are authored flat)."""
    return [(x, y, z) for (x, y) in section]


CHECKS = [
    dict(name="width", mm=260.0, tol=1.0, how="bbox_x", part="ShoppingBagBody"),
    dict(name="body_height", mm=230.0, tol=1.0, how="bbox_z",
         part="ShoppingBagBody"),
    dict(name="overall_height", mm=293.0, tol=1.0, how="bbox_z"),
]
