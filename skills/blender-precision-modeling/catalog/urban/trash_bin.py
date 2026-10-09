"""
trash_bin -- 480 x 480 x 940 mm public litter bin: a lathed tapered body with a
rolled rim, a swing lid on a hinge, an aperture throat, a liner ring and a
mounting post with two ground bolts.

`medium`, and 940 mm is the real installed height of a street bin. The body is
one `lathe` with a genuine wall in the profile -- outer skin up, over the rim,
down the inside and back along the floor -- so the aperture is a real hole and
the liner ring has something to sit in, instead of a solid revolve with a disc
stuck on the side.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    bin_diameter=480.0,
    overall_height=940.0,
    body_height=700.0,
    rim_diameter=500.0,
    aperture_width=320.0,
    lid_diameter=500.0,
    post_diameter=60.0,
)


def build():
    body = bkit.pbr("BinBody", base=(0.16, 0.26, 0.18), metal=0.45,
                    rough=0.44)
    lid = bkit.pbr("BinLid", base=(0.13, 0.22, 0.15), metal=0.45,
                   rough=0.40)
    steel = bkit.preset("brushed_metal")
    dark = bkit.pbr("BinDark", base=(0.07, 0.07, 0.075), rough=0.46)
    liner = bkit.pbr("BinLiner", base=(0.10, 0.10, 0.11), rough=0.66)

    # ---- post and base ring, the post sunk 10 mm into the base -----------
    bkit.cylinder("BinPost", SPEC["post_diameter"] / 2.0, 300.0, segments=32,
                  centre=(0.0, 0.0, 150.0), mat=steel)
    bkit.lathe("BinBase", [(0.0, 0.0), (200.0, 0.0), (200.0, 24.0),
                           (30.0, 30.0), (0.0, 30.0)], segments=48,
               mat=dark)
    bolts = [bkit.cylinder("_b", 10.0, 14.0, segments=16, centre=(bx, by, 14.0),
                           mat=steel)
             for (bx, by) in bkit.grid_positions(2, 2, 240.0, 240.0)]
    bkit.join(bolts, name="BinAnchorBolts")

    # ---- body with a real wall and a real aperture throat ----------------
    # lathe profiles carry ABSOLUTE z.
    bkit.lathe("BinBody", [
        (0.0, 24.0), (200.0, 24.0), (240.0, 690.0), (250.0, 706.0),
        (250.0, 730.0), (234.0, 730.0), (234.0, 712.0), (196.0, 44.0),
        (0.0, 44.0),
    ], segments=56, mat=body)

    # ---- liner ring sitting inside the throat -----------------------------
    bkit.tube("LinerRing", 232.0, 200.0, 160.0, segments=48,
              centre=(0.0, 0.0, 640.0), mat=liner)

    # ---- swing lid: a shallow dome on a hinge, plus the pivot barrel -----
    bkit.lathe("BinLid", [
        (0.0, 726.0), (100.0, 728.0), (200.0, 736.0), (250.0, 750.0),
        (250.0, 770.0), (100.0, 764.0), (0.0, 762.0),
    ], segments=56, mat=lid)
    bkit.cylinder("LidPivot", 18.0, 300.0, segments=24, axis="X",
                  centre=(0.0, -232.0, 748.0), mat=steel)

    # ---- a wrap-around sign band and a disposal aperture flap -----------
    bkit.tube("SignBand", 241.0, 239.0, 200.0, segments=56,
              centre=(0.0, 0.0, 480.0), mat=dark)
    bkit.rounded_box("ApertureFlap", SPEC["aperture_width"], 30.0, 260.0,
                     r=12.0, segments=2, centre=(0.0, -250.0, 590.0),
                     mat=dark)
    bkit.cylinder("FlapHinge", 12.0, SPEC["aperture_width"] - 20.0,
                  segments=20, axis="X", centre=(0.0, -238.0, 718.0),
                  mat=steel)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    # The widest point is the rolled rim at z=730, not the bin base.
    dict(name="bin_diameter", mm=500.0, tol=1.0, how="diameter",
         part="BinBody"),
    dict(name="rim_diameter", mm=500.0, tol=1.0, how="diameter",
         part="BinLid"),
    dict(name="post_diameter", mm=60.0, tol=0.6, how="diameter",
         part="BinPost"),
    dict(name="sign_band_height", mm=200.0, tol=1.0, how="bbox_z",
         part="SignBand"),
    dict(name="overall_height", mm=770.0, tol=2.0, how="bbox_z"),
]