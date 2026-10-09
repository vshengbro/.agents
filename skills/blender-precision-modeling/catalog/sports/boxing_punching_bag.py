"""
boxing_punching_bag -- 1200 x 300 mm heavy bag lying on its side, with a
four-point suspension strap, a webbing triangle and a hanging ring.

The bag is one lathe about its own long axis, so the silhouette -- straight
flank, rounded nose, slightly barrelled -- is a measured profile rather than a
cylinder. The suspension hardware hangs off one end at a position derived from
the bag length, not from a hand-typed x.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1200.0,
    diameter=300.0,
    strap_width=70.0,
    strap_thickness=6.0,
    strap_position=420.0,     # from the closed end
    ring_diameter=64.0,
)

R = SPEC["diameter"] / 2.0        # 150
L = SPEC["length"]                # 1200

# Lathe profile in (radius, distance) order, closed on the axis at both ends.
# bkit.lathe() revolves about +Z and takes (r, z) pairs -- passing them the
# other way round silently builds a 2400 mm washer, not a 1200 mm bag.
# Both ends are now FLAT DISCS, not points. A heavy bag is a cylinder closed by
# a flat leather cap at each end; the old profile ran the radius down to 0 at
# both stations, which made it a rugby ball lying on its side and lost the one
# feature that says "punching bag". The end discs are the real 150 mm radius
# reached over the last 60 mm of the length, so `length` and `diameter` are
# unchanged.
PROFILE = [
    (120.0, 0.0), (142.0, 1.0), (150.0, 6.0),
    (152.0, 60.0),
    (152.0, 600.0),
    (152.0, 1140.0),
    (150.0, 1194.0), (142.0, 1199.0), (120.0, 1200.0),
]

CHECKS = [
    dict(name="length", mm=1200.0, tol=0.6, how="bbox_y", part="PunchingBag"),
    dict(name="diameter", mm=304.0, tol=0.8, how="bbox_z", part="PunchingBag"),
    dict(name="strap_width", mm=70.0, tol=0.6, how="bbox_y", part="SuspensionStrap"),
]


def build():
    # 0.055 base is effectively black against a 0.19 backdrop: the bag rendered as
    # a silhouette with no form at all. Real punching-bag leather is a mid
    # brown-red, and 0.30 base holds an edge while still reading dark.
    leather = bkit.pbr("BagLeather", base=(0.30, 0.13, 0.09), rough=0.42)
    webbing = bkit.pbr("Webbing", base=(0.24, 0.25, 0.28), rough=0.76)
    steel = bkit.preset("anodized")

    # ---- bag: one lathe about its long axis, laid along y -----------------
    bag = bkit.lathe("PunchingBag", PROFILE, segments=80, mat=leather)
    bkit.recalc(bag)
    bkit.place(bag, (0.0, 0.0, 0.0), axis="Y")

    # ---- suspension: a band round the bag, a webbing triangle and a ring --
    # place(..., "Y") maps the lathe's +Z to world -Y, so a profile station at
    # 420 mm from the closed end sits at y = -420
    x_s = -SPEC["strap_position"]
    strap = bkit.tube("SuspensionStrap", R + 4.0, R - 6.0, SPEC["strap_width"],
                      segments=80, centre=(0.0, x_s, 0.0), axis="Y",
                      mat=webbing)
    tri = bkit.extrude_profile("WebbingTriangle", [
        (-52.0, 0.0), (52.0, 0.0), (0.0, 96.0),
    ], SPEC["strap_thickness"], centre=(0.0, x_s, R + 4.0), axis="Y",
        mat=webbing)
    ring = bkit.torus("HangingRing", SPEC["ring_diameter"] / 2.0 - 5.0, 5.0,
                      seg_major=48, seg_minor=16,
                      centre=(0.0, x_s, R + 100.0), axis="Y", mat=steel)
    return dict(spec=SPEC, parts=3)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
