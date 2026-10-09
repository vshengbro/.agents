"""
archery_bow -- a 68-inch English longbow, 1720 mm, 68 lb draw.

A longbow is a LAMINATED STACK, and the lamination is the object: five layers
of yew/horn/bamboo, each a loft along the bow's curve, with the belly and back
curving in OPPOSITE directions. Recurve is the other half of it -- the limbs
bend back toward the archer at the tips, which is why the limb is lofted from a
curved spine rather than being a straight box.

The string is the third part and the reason it reads as a bow: it runs tip to
tip in a straight line while the limbs curve away from it, and it hangs at the
brace height of 180 mm, not at the tips.

Real English longbow: 1720 mm overall, 68 lb @ 28", 45 mm limb width at the
fading nock, 32 mm belly-to-back, 12 mm brace height at 180 mm.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _ritual as R_

SPEC = dict(
    length=1720.0,
    riser_height=240.0,
    limb_length=740.0,
    limb_width_root=46.0,
    limb_width_tip=14.0,
    limb_depth=32.0,
    belly_limb_sag=170.0,
    back_limb_sag=60.0,
    string_dia=3.0,
    brace_height=180.0,
    laminations=5,
)

HALF = SPEC["length"] / 2.0

CHECKS = [
    dict(name="overall_length", mm=1720.0, tol=6.0, how="bbox_x",
         part="BowLimbs"),
    dict(name="riser_height", mm=240.0, tol=5.0, how="bbox_z",
         part="BowRiser"),
    dict(name="limb_width_root", mm=46.0, tol=4.0, how="bbox_z",
         part="BowLimbs"),
    dict(name="string_dia", mm=3.0, tol=0.8, how="bbox_y", part="BowString"),
    dict(name="brace_height", mm=-178.5, tol=8.0, how="y_max",
         part="BowString"),
    dict(name="tip_reach", mm=860.0, tol=6.0, how="x_max", part="BowLimbs"),
    dict(name="riser_on_floor", mm=0.0, tol=3.0, how="z_min", part="BowRiser"),
]


def _tri(ring):
    """`rounded_rect_section` returns a 2D ring; a loft section needs 3D."""
    return [(a, b, 0.0) for (a, b) in ring]


def build():
    yew = R_.cedar("BowYew", base=(0.52, 0.34, 0.16), rough=0.56)
    horn = R_.cedar("BowHorn", base=(0.14, 0.11, 0.10), rough=0.40)
    bamboo = R_.cedar("BowBamboo", base=(0.68, 0.52, 0.26), rough=0.50)
    string = bkit.pbr("BowString", base=(0.86, 0.84, 0.74), rough=0.70)
    brass = R_.gild("BowBrass")

    # ---- the riser: the carved middle, a loft of rounded sections ----
    secs = []
    for (z, sx, sy, r) in ((0.0, 44.0, 70.0, 12.0),
                           (60.0, 48.0, 86.0, 14.0),
                           (120.0, 46.0, 74.0, 13.0),
                           (180.0, 42.0, 60.0, 12.0),
                           (240.0, 36.0, 48.0, 10.0)):
        ring = bkit.rounded_rect_section(sx, sy, r, per_corner=4,
                                         centre=(0.0, 0.0))
        secs.append([(x, y, z) for (x, y) in ring])
    riser = bkit.loft("BowRiser", secs, mat=yew)
    bkit.recalc(riser)
    bkit.shade_smooth(riser, 38.0)
    bkit.uv_sphere("BowArrowRest", 17.0, segments=20, rings=12,
                   centre=(30.0, -34.0, 130.0), mat=horn)

    # ---- the limb: ONE closed loft, both halves, laminations by face ---
    # belly and back are the SAME section now: one watertight solid whose
    # faces are coloured in bands.  Mirroring a half, or joining five
    # laminations that tile the section exactly, leaves coincident
    # internal faces -- the join reports a near-zero NEGATIVE volume and
    # the part never passes `health()`.
    mats = (horn, bamboo, yew, bamboo, horn)
    sec = []
    for s in (1, -1):
        for i in range(25):
            t = i / 24.0
            x = s * HALF * t
            # the limb curves toward the string, and the depth and the
            # face width both taper to the fading nock
            d = SPEC["limb_depth"] * (1.0 - 0.80 * t)
            w = (SPEC["limb_width_root"] +
                 (SPEC["limb_width_tip"] - SPEC["limb_width_root"]) * t)
            yc = -SPEC["belly_limb_sag"] * (t ** 2.0)
            ring = bkit.rounded_rect_section(d, w, min(d, w) * 0.28,
                                             per_corner=3)
            sec.append([(x, yc + dy, SPEC["riser_height"] * 0.62 + dz)
                        for (dy, dz) in ring])
    limb = bkit.loft("BowLimbs", sec, mat=yew)
    bkit.recalc(limb)
    bkit.shade_smooth(limb, 38.0)
    # the laminations are face bands along the limb's depth
    lo = SPEC["belly_limb_sag"]
    for j in range(1, len(mats)):
        cut = -lo * 0.5 + 2.0 * lo * 0.5 * j / float(len(mats))
        bkit.assign_faces_by(limb, mats[j],
                             lambda c, n, cut=cut: c.y / bkit.MM < cut)

    # ---- the string: tip to tip, at the brace height ----------------
    tip = SPEC["limb_length"]
    bkit.cylinder("BowString", SPEC["string_dia"] / 2.0, 2.0 * HALF,
                  segments=12, axis="X", centre=(0.0, -SPEC["brace_height"],
                                                 SPEC["riser_height"] * 0.62),
                  mat=string)
    for s in (1, -1):
        bkit.cylinder("BowNock%d" % (0 if s < 0 else 1), 9.0, 30.0,
                      segments=14, axis="X",
                      centre=(s * (HALF - 14.0), 0.0,
                              SPEC["riser_height"] * 0.62), mat=brass)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 5,
                note="One watertight limb loft with the lamination bands as "
                     "face materials, not five stacked solids.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
