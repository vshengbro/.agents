"""
scarecrow -- a 2.2 m field scarecrow on a cross frame, with a sack head.

A scarecrow is FIVE THINGS in silhouette: a vertical post, a crossbar, a
cross-hatched second brace, a head and a hat. The post and the crossbar are one
X-frame because that is what stops it turning in the wind, and the straw arms
are bundles of tubes whose free ends fan out -- a straw bundle is several tubes,
not one cone, and that is the whole difference between a scarecrow and a
scarecrow-shaped object.

The head is a loft of superellipse sections with n about 2.6, so it is a sack
and not a ball, and the hat brim is a separate lathed disc.

Real field scarecrow: 2200 mm to the top of the hat, 1400 mm crossbar,
750 mm head, 350 mm hat brim.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _agri as A

SPEC = dict(
    total_height=2200.0,
    crossbar_span=1400.0,
    crossbar_height=1620.0,
    head_dia=300.0,
    head_height=340.0,
    hat_brim_dia=350.0,
    arm_bundle=70.0,
    straw_tubes=7,
)

CROSS_Z = SPEC["crossbar_height"]

CHECKS = [
    dict(name="post_dia", mm=90.0, tol=2.0, how="bbox_x", part="ScarecrowPost"),
    dict(name="crossbar_span", mm=1400.0, tol=6.0, how="bbox_x",
         part="ScarecrowCrossbar"),
    dict(name="crossbar_top", mm=1650.0, tol=4.0, how="top_z",
         part="ScarecrowCrossbar"),
    dict(name="head_max_dia", mm=315.0, tol=6.0, how="bbox_y",
         part="ScarecrowHead"),
    dict(name="head_height", mm=340.0, tol=8.0, how="bbox_z",
         part="ScarecrowHead"),
    dict(name="hat_brim_dia", mm=350.0, tol=6.0, how="bbox_y",
         part="ScarecrowHatBrim"),
    dict(name="total_height", mm=2200.0, tol=8.0, how="top_z",
         part="ScarecrowHatCrown"),
    dict(name="post_on_floor", mm=0.0, tol=2.0, how="z_min",
         part="ScarecrowPost"),
]


def build():
    timber = bkit.pbr("ScareTimber", base=(0.48, 0.36, 0.22), rough=0.76)
    sack = bkit.pbr("ScareSack", base=(0.68, 0.60, 0.42), rough=0.88)
    shirt = bkit.pbr("ScareShirt", base=(0.34, 0.20, 0.14), rough=0.84)
    straw = bkit.pbr("ScareStraw", base=(0.76, 0.66, 0.30), rough=0.80)
    felt = bkit.pbr("ScareFelt", base=(0.30, 0.32, 0.18), rough=0.74)
    soil = bkit.preset("soil")

    # ---- the X frame: a post and a leaning brace, crossed --------------
    bkit.cylinder("ScarecrowPost", 45.0, 1780.0, segments=20,
                  centre=(0.0, 0.0, 890.0), mat=timber)
    # the leaning brace is TUBE BETWEEN two points: a `cylinder` with a
    # centre stays vertical, dips 70 mm below the floor and lifts the whole
    # scarecrow 70 mm when `sit_on_floor()` seats it.
    A.tube_between("ScarecrowBrace", (330.0, 0.0, 120.0), (95.0, 0.0, 1500.0),
                   32.0, mat=timber)
    bkit.rounded_box("ScarecrowCrossbar", 1400.0, 60.0, 60.0, r=14.0,
                     segments=2, centre=(0.0, 0.0, CROSS_Z), mat=timber)
    # lashings where the bar meets the post: three turns of rope each
    for i, x in enumerate((-140.0, 140.0)):
        bkit.tube("ScarecrowLashing%d" % i, 60.0, 50.0, 70.0, segments=24,
                  axis="X", centre=(x, 0.0, CROSS_Z), mat=straw)

    # ---- the shirt body, lofted so it hangs ---------------------------
    secs = []
    for (z, sx, sy, n) in ((1500.0, 420.0, 240.0, 3.4),
                           (1350.0, 460.0, 260.0, 3.2),
                           (900.0, 520.0, 280.0, 3.0),
                           (520.0, 600.0, 300.0, 2.8),
                           (330.0, 640.0, 310.0, 2.6)):
        ring = bkit.superellipse_section(sx, sy, n=n, steps=40)
        secs.append([(x, y, z) for (x, y) in ring])
    body = bkit.loft("ScarecrowShirt", secs, mat=shirt)
    bkit.recalc(body)
    bkit.shade_smooth(body, 40.0)

    # ---- the straw arms: seven tubes each, fanned at the ends ---------
    for s in (1, -1):
        for i in range(SPEC["straw_tubes"]):
            dy = (i - (SPEC["straw_tubes"] - 1) / 2.0) * 26.0
            A.tube_between("ScarecrowArm%d_%d" % (0 if s < 0 else 1, i),
                           (s * 90.0, dy, CROSS_Z + 6.0),
                           (s * 690.0, dy * 1.9, CROSS_Z - 90.0 - 10.0 * i),
                           13.0, mat=straw)

    # ---- the sack head: n = 2.6 makes a sack, not a ball -------------
    # `loft()` has no `centre`, so the head's station z values are absolute:
    # the neck starts at z=1780, just inside the shirt.
    hs = []
    for (dz, sx, sy, n) in ((0.0, 300.0, 290.0, 2.6),
                            (90.0, 330.0, 315.0, 2.7),
                            (250.0, 300.0, 290.0, 2.8),
                            (340.0, 200.0, 195.0, 2.8)):
        ring = bkit.superellipse_section(sx, sy, n=n, steps=40)
        hs.append([(x, y, 1780.0 + dz) for (x, y) in ring])
    head = bkit.loft("ScarecrowHead", hs, mat=sack)
    bkit.recalc(head)
    bkit.shade_smooth(head, 40.0)

    # ---- the hat: crown, brim, and a neck band ------------------------
    bkit.lathe("ScarecrowHatBrim",
               [(0.0, 0.0), (175.0, 0.0), (175.0, 9.0), (150.0, 15.0),
                (0.0, 15.0)], segments=40, centre=(0.0, 0.0, 2118.0),
               mat=felt)
    bkit.lathe("ScarecrowHatCrown",
               [(0.0, 0.0), (118.0, 0.0), (112.0, 40.0), (95.0, 76.0),
                (60.0, 88.0), (0.0, 88.0)], segments=40,
               centre=(0.0, 0.0, 2112.0), mat=felt)
    bkit.tube("ScarecrowHatBand", 120.0, 112.0, 26.0, segments=36,
              centre=(0.0, 0.0, 2130.0), mat=shirt)

    # ---- the cross brace behind, and the soil at the foot -------------
    A.bar_between("ScarecrowBackBrace", (-40.0, 120.0, 1200.0),
                  (40.0, 120.0, 200.0), 50.0, 50.0, mat=timber, r=6.0)
    A.make_ground("Ground", 1500.0, 1200.0, 26.0, mat=soil)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 1 + 1 + 2 + 1 + 14 + 2 + 3 + 1,
                note="Straw arms are bundles of seven tubes each, fanning at "
                     "the ends; a single cone reads as a bottle, not straw.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
