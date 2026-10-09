"""
stone_arch_bridge -- a single-span masonry arch bridge: a 9 m semicircular
arch, two abutments, spandrel walls, a roadway deck, and parapets with
piercings.

Huge size class, 24 m long. One arch, so this is the clearest test of the arch
family: the arch ring is a swept `arc_torus` scaled flat, the void through the
spandrel is a real boolean, and the parapet openings are placed on a computed
pitch.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    span=9000.0,            # clear opening
    rise=4500.0,
    arch_thickness=1200.0,
    deck_width=6800.0,
    deck_height=900.0,
    abutment_width=2600.0,
    overall_length=24000.0,
    parapet_height=1100.0,
    parapet_thickness=420.0,
    piercings=7,            # openings in each parapet, computed pitch
    piercing_width=900.0,
    spandrel_height=5200.0,
)

SC = SPEC["span"]
R = SC / 2.0
DW = SPEC["deck_width"]
DH = SPEC["deck_height"]
AW = SPEC["abutment_width"]
OL = SPEC["overall_length"]
SPH = SPEC["spandrel_height"]

ARCH_Z = SPH


def _ring(sx, sy, r, z):
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=5)]


def build():
    masonry = bkit.pbr("BridgeStone", base=(0.63, 0.59, 0.52), rough=0.74)
    road = bkit.pbr("BridgeRoad", base=(0.34, 0.33, 0.31), rough=0.88)

    # ---- abutments: the mass the arch springs from -----------------------
    for sx, tag in ((-1, "L"), (1, "R")):
        bkit.loft("BridgeAbutment%s" % tag, [
            _ring(AW + 700.0, DW + 900.0, 90.0, 0.0),
            _ring(AW + 400.0, DW + 600.0, 80.0, 800.0),
            _ring(AW + 200.0, DW + 400.0, 70.0, 1800.0),
            _ring(AW, DW + 300.0, 70.0, SPH + DH),
        ], closed_loop=True, cap_start=True, cap_end=True, mat=masonry)
        ob = _last("BridgeAbutment%s" % tag)
        bkit.move(ob, sx * (R + AW / 2.0), 0.0, 0.0)

    # ---- the arch ring: swept, then scaled flat --------------------------
    ring_mid = R + SPEC["arch_thickness"] / 2.0
    arch = bkit.arc_torus("BridgeArch", ring_mid, SPEC["arch_thickness"] / 2.0,
                          0.0, 180.0, centre=(0.0, 0.0, ARCH_Z), plane="XZ",
                          seg_major=64, seg_minor=26, mat=masonry, caps=True)
    arch.scale = (1.0, DW / SPEC["arch_thickness"], 1.0)
    import bpy
    bpy.context.view_layer.update()

    # ---- spandrel walls either side of the roadway, arch void cut -------
    for sy, tag in ((-1, "L"), (1, "R")):
        w = bkit.rounded_box("BridgeSpandrel%s" % tag, OL, (DW - 1800.0) / 2.0,
                             SPH + DH, r=50.0, segments=2,
                             centre=(0.0, sy * ((DW + 1800.0) / 4.0 + 200.0),
                                     (SPH + DH) / 2.0), mat=masonry)
        void = bkit.cylinder("_void", R + 30.0, DW * 2.0, segments=64,
                             centre=(0.0, 0.0, ARCH_Z - 150.0), axis="Y")
        bkit.boolean(w, void, "DIFFERENCE")

    # ---- roadway deck ----------------------------------------------------
    deck = bkit.rounded_box("BridgeDeck", OL, DW, DH, r=30.0, segments=2,
                            centre=(0.0, 0.0, SPH + DH / 2.0 + 200.0),
                            mat=road)

    # ---- parapets with real piercings, on a computed pitch --------------
    npier = SPEC["piercings"]
    pw = SPEC["piercing_width"]
    # pitch that fits piercings AND the solid piers between them inside the
    # deck length, so neither run out of deck
    pitch = (OL - 1200.0) / npier
    assert pitch > pw + 500.0, "piercings too wide for their pitch"
    for sy, tag in ((-1, "L"), (1, "R")):
        par = bkit.rounded_box("BridgeParapet%s" % tag, OL,
                               SPEC["parapet_thickness"],
                               SPEC["parapet_height"], r=16.0, segments=2,
                               centre=(0.0, sy * (DW / 2.0 - 260.0),
                                       SPH + DH + 200.0
                                       + SPEC["parapet_height"] / 2.0),
                               mat=masonry)
        for i in range(npier):
            x = -(OL - 1200.0) / 2.0 + pitch * (i + 0.5)
            cut = bkit.rounded_box("_piercing", pw, SPEC["parapet_thickness"] + 600.0,
                                   SPEC["parapet_height"] * 0.66, r=8.0,
                                   segments=1, centre=(x, 0.0, 0.0))
            bkit.move(cut, 0.0,
                      sy * (DW / 2.0 - 260.0),
                      SPH + DH + 200.0 + SPEC["parapet_height"] * 0.17)
            bkit.boolean(par, cut, "DIFFERENCE")

    return dict(spec=SPEC, parts=2 + 1 + 2 + 1 + 2,
                piercings=npier * 2)


def _last(name):
    import bpy
    return bpy.data.objects[name]


CHECKS = [
    dict(name="overall_length", mm=24000.0, tol=120.0, how="bbox_x"),
    dict(name="deck_width", mm=6800.0, tol=60.0, how="bbox_y", part="BridgeDeck"),
    dict(name="arch_depth", mm=6800.0, tol=60.0, how="bbox_y", part="BridgeArch"),
    dict(name="parapet_height", mm=1100.0, tol=30.0, how="bbox_z",
         part="BridgeParapetL"),
    # the abutment batters: its base is 700 wider than the shaft it springs
    # from, so the part's own width is the footing, not abutment_width
    dict(name="abutment_base_width", mm=3300.0, tol=60.0, how="bbox_x",
         part="BridgeAbutmentL"),
]
