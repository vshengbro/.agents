"""
washbasin -- pedestal basin: a vitreous china bowl with a real 14 mm wall and
an overhanging rim, carried on a turned pedestal column.

The 560 x 440 plan at an 850 mm rim is what separates a basin from a bowl, but
the thing that makes it a PEDESTAL basin is the overhang: the bowl's underside
stops at 620 mm and the column continues to the floor. Running the bowl's
outer wall all the way down to z = 0 -- which is the obvious way to build it --
produces a smooth flare with no waist, and the whole thing renders as a waste
bin.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=560.0,
    depth=440.0,
    height=850.0,          # floor to rim
    rim_width=120.0,       # rim slab, as a fraction of the depth
    wall=14.0,             # vitreous china
    bowl_depth=155.0,
    bowl_underside=620.0,  # the bowl stops here; the column carries on down
    pedestal_base_width=250.0,
    pedestal_base_depth=230.0,
    pedestal_waist_width=185.0,
    pedestal_top_width=240.0,
    waste_diameter=40.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
WALL = SPEC["wall"]
RIM = SPEC["rim_width"]
BOWL_Z = H - RIM
BOWL_FLOOR = BOWL_Z - SPEC["bowl_depth"]


def _ring(sx, sy, r, z):
    """One rounded-rect loft section.

    `rounded_rect_section` silently self-intersects when r > min(sx,sy)/2, and
    a loft built from such a ring survives until the first boolean, which then
    returns an EMPTY mesh with no error. Clamp.
    """
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=8)]


def build():
    china = bkit.preset("ceramic")

    # ---- bowl: underside at 620, up the outside, over the rim, back down --
    # cap_start closes the underside (hidden against the column) and cap_end
    # closes the bowl floor, so the 14 mm wall is real geometry all the way.
    bowl = bkit.loft("BasinBowl", [
        _ring(W - 90.0, D - 90.0, 70.0, SPEC["bowl_underside"]),
        _ring(W - 40.0, D - 40.0, 120.0, SPEC["bowl_underside"] + 80.0),
        _ring(W, D, 150.0, BOWL_Z),                 # outer wall at the rim
        _ring(W, D, 150.0, H),                      # rim top, outer
        _ring(W - RIM * 0.5, D - RIM, 120.0, H),    # across the rim
        _ring(W - RIM * 0.5 - WALL, D - RIM - WALL, 110.0, BOWL_Z - 4.0),
        _ring(W - 190.0, D - 190.0, 130.0, BOWL_FLOOR + 40.0),
        _ring(W - 280.0, D - 280.0, 100.0, BOWL_FLOOR),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=china)
    bkit.recalc(bowl)

    # ---- pedestal: a turned column with a waist, up into the bowl --------
    ped = bkit.loft("Pedestal", [
        _ring(SPEC["pedestal_base_width"], SPEC["pedestal_base_depth"],
              55.0, 0.0),
        _ring(SPEC["pedestal_base_width"] - 24.0,
              SPEC["pedestal_base_depth"] - 24.0, 50.0, 110.0),
        _ring(SPEC["pedestal_waist_width"], SPEC["pedestal_base_depth"] - 44.0,
              46.0, 330.0),
        _ring(SPEC["pedestal_waist_width"] + 6.0,
              SPEC["pedestal_base_depth"] - 30.0, 50.0, 470.0),
        _ring(SPEC["pedestal_top_width"], SPEC["pedestal_base_depth"] + 20.0,
              60.0, SPEC["bowl_underside"] + 70.0),
    ], closed_loop=True, cap_start=True, cap_end=True, mat=china)
    bkit.recalc(ped)

    # ---- waste: a real hole through the bowl floor ------------------------
    bkit.bore(bowl, SPEC["waste_diameter"] / 2.0, depth=140.0,
              centre=(0.0, 0.0, BOWL_FLOOR), axis="Z", host_segments=96)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="width", mm=560.0, tol=0.5, how="bbox_x", part="BasinBowl"),
    dict(name="depth", mm=440.0, tol=0.5, how="bbox_y", part="BasinBowl"),
    # "how high is the rim above the floor" is a COORDINATE, not a size: the
    # bowl is only 230 mm deep, so bbox_z on it reports the bowl, not the rim.
    dict(name="rim_height", mm=850.0, tol=0.5, how="top_z", part="BasinBowl"),
    # The waist is a local width 330 mm up the column; no bounding box can
    # express it, and bbox_x of the pedestal is the 250 mm BASE. Claim the base.
    dict(name="pedestal_base_width", mm=250.0, tol=0.5, how="bbox_x",
         part="Pedestal"),
    dict(name="overall_height", mm=850.0, tol=0.5, how="bbox_z"),
]
