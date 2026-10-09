"""
film_reel -- 248 x 62 mm 35 mm cine spool: two flange plates, a 100 mm hub
bore and a wound film pack.

The spool is ONE `lathe`, not five stacked primitives. A single profile that
runs axis -> out along the bottom flange -> in to the hub -> up the bore ->
out along the top flange -> back to axis revolves into a frame with real
thickness everywhere and no coincident faces between separate discs -- which
is why a reel built from stacked cylinders needs two booleans before it will
report watertight, and this one needs none.

The film pack deliberately overlaps each flange by 0.5 mm (z 2.5..59.5 against
flange faces at 3 and 59). A flush pack touches the flange along a whole disc,
which is one of the three tangency traps and produces non-manifold edges.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    flange_diameter=248.0,
    overall_height=62.0,
    flange_thickness=3.0,
    hub_diameter=100.0,
    film_pack_diameter=228.0,
    spindle_diameter=28.0,
)

R = SPEC["flange_diameter"] / 2.0      # 124
H = SPEC["overall_height"]             # 62
HUB = SPEC["hub_diameter"] / 2.0       # 50
FT = SPEC["flange_thickness"]          # 3


def build():
    film = bkit.pbr("ReelFilm", base=(0.16, 0.14, 0.12), rough=0.42)
    plastic = bkit.pbr("ReelPlastic", base=(0.30, 0.31, 0.33), rough=0.34)
    hub_mat = bkit.pbr("ReelHub", base=(0.55, 0.55, 0.56), rough=0.30)

    # ---- the spool frame: one revolve, real thickness throughout --------
    bkit.lathe("ReelFrame", [
        (0.0, 0.0), (R, 0.0), (R, FT), (HUB, FT),
        (HUB, H - FT), (R, H - FT), (R, H), (0.0, H),
    ], segments=96, centre=(0.0, 0.0, 0.0), mat=plastic)

    # ---- wound film, overlapping both flanges by 0.5 mm ------------------
    bkit.lathe("FilmPack", [(0.0, 2.5), (114.0, 2.5), (114.0, 59.5),
                            (0.0, 59.5)], segments=96,
               centre=(0.0, 0.0, 31.0), mat=film)

    # ---- three-piece spool hub, through the 100 mm bore ------------------
    bkit.cylinder("Spindle", 14.0, 66.0, segments=32, centre=(0.0, 0.0, 31.0),
                  mat=hub_mat)
    for zc, zt in ((1.5, 3.0), (59.0, 3.0)):
        bkit.tube("SpindleCollar%.0f" % (zc * 10.0), 26.0, 14.0, zt,
                  segments=32, centre=(0.0, 0.0, zc), mat=hub_mat)

    # ---- the 3-slot cut pattern: three radial webs on the bottom flange ---
    #     Each is a rib standing on the flange, swept by array_radial about Z,
    #     so the three slots are computed rather than hand-placed.
    rib = bkit.box("_rib", 62.0, 5.0, 4.0, centre=(74.0, 0.0, 5.0),
                   mat=plastic)
    bkit.array_radial(rib, count=3, axis="Z")

    # ---- index label on the top flange ----------------------------------
    bkit.tube("ReelLabel", 52.0, 44.0, 1.2, segments=64,
              centre=(0.0, 0.0, 62.0), mat=film)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="flange_diameter", mm=248.0, tol=0.6, how="diameter",
         part="ReelFrame"),
    dict(name="overall_height", mm=62.0, tol=0.6, how="bbox_z",
         part="ReelFrame"),
    dict(name="film_pack_diameter", mm=228.0, tol=0.6, how="diameter",
         part="FilmPack"),
    dict(name="spindle_diameter", mm=28.0, tol=0.4, how="diameter",
         part="Spindle"),
]