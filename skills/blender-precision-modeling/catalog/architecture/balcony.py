"""
balcony -- a cantilevered stone balcony: a slab on two corbels, a moulded
balustrade with turned balusters on a computed pitch, and two newel piers.

Large size class (600..3000 mm): 3.6 m wide, 1.1 m deep, 1.05 m to the hand
rail. The balustrade is the read, and its spacing is the contract: balusters
at a computed pitch between the two newels, so the run always ends flush.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=3600.0,
    depth=1100.0,
    slab_thickness=220.0,
    corbel_height=520.0,
    balustrade_height=1050.0,
    rail_width=180.0,
    rail_thickness=90.0,
    baluster_pitch=200.0,
    baluster_width=70.0,
    newel_width=260.0,
    newel_height=1150.0,
)

W = SPEC["width"]
D = SPEC["depth"]
ST = SPEC["slab_thickness"]
CH = SPEC["corbel_height"]
BH = SPEC["balustrade_height"]
NW = SPEC["newel_width"]

Z_SLAB = CH                 # underside of the slab
Z_DECK = Z_SLAB + ST        # walking surface


def build():
    stone = bkit.pbr("BalconyStone", base=(0.76, 0.73, 0.67), rough=0.68)
    stone_dk = bkit.pbr("BalconyStoneDark", base=(0.66, 0.63, 0.58), rough=0.72)
    rail_mat = bkit.pbr("BalconyRail", base=(0.72, 0.69, 0.63), rough=0.62)

    # ---- corbels: two brackets under the slab --------------------------
    # They are what makes the balcony CANTILEVER rather than post-supported,
    # so they get their own taper and sit inside the slab's footprint.
    for sx, tag in ((-1, "L"), (1, "R")):
        bkit.loft("BalconyCorbel%s" % tag, [
            _ring(300.0, D - 120.0, 40.0, 0.0),
            _ring(420.0, D - 60.0, 50.0, CH * 0.45),
            _ring(560.0, D, 60.0, CH),
        ], closed_loop=True, cap_start=True, cap_end=True, mat=stone_dk)
        bkit.move(_last("BalconyCorbel%s" % tag),
                  sx * (W / 2.0 - 420.0), 0.0, 0.0)

    # ---- the slab -------------------------------------------------------
    slab = bkit.rounded_box("BalconySlab", W, D, ST, r=22.0, segments=2,
                            centre=(0.0, 0.0, Z_SLAB + ST / 2.0), mat=stone)

    # ---- balustrade: newels, turned balusters, top and bottom rails -----
    # Baluster count from the clear width between the newels, so the first
    # and last baluster both land a half-pitch in from the newel face.
    clear = W - 2.0 * NW
    nb = max(2, int(round(clear / SPEC["baluster_pitch"])))
    pitch = clear / (nb + 1)
    for sx, tag in ((-1, "L"), (1, "R")):
        bkit.rounded_box("BalconyNewel%s" % tag, NW, NW, SPEC["newel_height"],
                         r=20.0, segments=3,
                         centre=(sx * (W / 2.0 - NW / 2.0), 0.0,
                                 Z_DECK + SPEC["newel_height"] / 2.0),
                         mat=stone)

    by = -D / 2.0 + 140.0
    bal = bkit.lathe("BalconyBalusters", [
        (0.0, 0.0), (SPEC["baluster_width"] / 2.0 + 8.0, 0.0),
        (SPEC["baluster_width"] / 2.0 + 8.0, 120.0),
        (SPEC["baluster_width"] / 2.0 - 6.0, 200.0),   # waist
        (SPEC["baluster_width"] / 2.0 - 10.0, BH * 0.5),
        (SPEC["baluster_width"] / 2.0 + 6.0, BH - 200.0),
        (SPEC["baluster_width"] / 2.0 + 10.0, BH - 120.0),
        (0.0, BH),
    ], segments=24, mat=rail_mat)
    bkit.array_linear(bal, nb, (pitch, 0.0, 0.0), apply=False)
    bkit.move(bal, -clear / 2.0 + pitch, 0.0, 0.0)
    bkit.move(bal, 0.0, by, Z_DECK)
    bpy_update()

    # ---- top rail and bottom rail --------------------------------------
    top = bkit.rounded_box("BalconyTopRail", W, SPEC["rail_thickness"],
                           SPEC["rail_width"], r=18.0, segments=2,
                           centre=(0.0, by, Z_DECK + BH + SPEC["rail_width"] / 2.0),
                           mat=rail_mat)
    bot = bkit.rounded_box("BalconyBottomRail", W - 2.0 * NW,
                           SPEC["rail_thickness"] * 0.85, 90.0, r=14.0,
                           segments=2,
                           centre=(0.0, by, Z_DECK + 140.0), mat=rail_mat)

    return dict(spec=SPEC, parts=2 + 1 + 2 + 1 + 2, balusters=nb)


def _ring(sx, sy, r, z):
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=5)]


def _last(name):
    import bpy
    return bpy.data.objects[name]


def bpy_update():
    import bpy
    bpy.context.view_layer.update()


CHECKS = [
    dict(name="width", mm=3600.0, tol=10.0, how="bbox_x", part="BalconySlab"),
    dict(name="depth", mm=1100.0, tol=6.0, how="bbox_y", part="BalconySlab"),
    dict(name="slab_thickness", mm=220.0, tol=4.0, how="bbox_z",
         part="BalconySlab"),
    dict(name="newel_height", mm=1150.0, tol=6.0, how="bbox_z",
         part="BalconyNewelL"),
    dict(name="overall_height", mm=1970.0, tol=12.0, how="bbox_z"),
]
