"""
bidet -- floor-standing bidet: a fold-back loft bowl with a real 14 mm wall, a
rear deck, and a real tap hole.

A bidet is a toilet bowl's sibling with no cistern: 560 x 380 x 400, a rim at
400 mm, and two tap holes in the rear deck. The shape that distinguishes it from
a toilet is the continuous curve from the foot to the rim -- a bidet has no
pedestal waist, it swells.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=560.0,
    width=380.0,
    height=400.0,          # floor to rim
    rim_width=50.0,
    wall=14.0,
    bowl_depth=150.0,
    foot_width=280.0,
    foot_length=440.0,
    tap_holes=2,
    tap_hole_diameter=34.0,
    tap_hole_spacing=100.0,
    waste_diameter=40.0,
)

L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]
WALL = SPEC["wall"]
RIM = SPEC["rim_width"]


def _ring(sx, sy, r, z, cy=0.0):
    """One rounded-rect loft section.

    `rounded_rect_section` self-intersects when r > min(sx,sy)/2, and a loft
    built from such a ring survives until the first boolean, which then returns
    an EMPTY mesh with no error. Clamp.
    """
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y + cy, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=8)]


def build():
    china = bkit.preset("ceramic")

    fw, fl = SPEC["foot_width"], SPEC["foot_length"]
    bowl_z = H - RIM

    # ---- bowl: a continuous swell from foot to rim, wall real ------------
    # Convention: sx is the X extent (the 560 mm LENGTH) and sy the Y extent
    # (the 380 mm WIDTH). Passing them the other way round produces a bowl
    # that measures 380 along X -- the classic silent swap, because every
    # section is still a valid closed ring and the mesh is still watertight.
    bowl = bkit.loft("BidetBowl", [
        _ring(fl, fw, 80.0, 0.0),                             # 440 x 280 foot
        _ring(fl + 40.0, fw + 30.0, 100.0, 70.0),
        _ring(L - 60.0, W - 40.0, 120.0, 220.0),
        _ring(L - 20.0, W - 10.0, 130.0, bowl_z - 30.0),
        _ring(L, W, 135.0, bowl_z),                           # outer rim, under
        _ring(L, W, 135.0, H),                                # rim top, outer
        _ring(L - RIM * 0.6, W - RIM, 110.0, H),              # across the rim
        _ring(L - RIM * 0.6 - WALL, W - RIM - WALL, 105.0, bowl_z - 4.0),
        _ring(L - 210.0, W - 170.0, 110.0, 170.0),            # inner wall down
        _ring(L - 300.0, W - 240.0, 90.0, H - SPEC["bowl_depth"]),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=china)
    bkit.recalc(bowl)

    # ---- waste ------------------------------------------------------------
    bkit.bore(bowl, SPEC["waste_diameter"] / 2.0, depth=110.0,
              centre=(0.0, 0.0, H - SPEC["bowl_depth"]), axis="Z",
              host_segments=96)

    # ---- two tap holes in the rear deck, laid out by arithmetic -----------
    # Positions come from the stated spacing, mirrored about the bowl axis, so
    # the two cutters can never land on the same coordinate -- two bores that
    # coincide defeat the EXACT solver and delete the body.
    pitch = SPEC["tap_hole_spacing"]
    for i, sy in enumerate((-1, 1)):
        bkit.bore(bowl, SPEC["tap_hole_diameter"] / 2.0, depth=130.0,
                  centre=(L / 2.0 - 62.0, sy * pitch / 2.0, H), axis="Z",
                  host_segments=96)

    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="length", mm=560.0, tol=0.5, how="bbox_x", part="BidetBowl"),
    dict(name="width", mm=380.0, tol=0.5, how="bbox_y", part="BidetBowl"),
    dict(name="rim_height", mm=400.0, tol=0.5, how="bbox_z", part="BidetBowl"),
    dict(name="overall_height", mm=400.0, tol=0.5, how="bbox_z"),
]
