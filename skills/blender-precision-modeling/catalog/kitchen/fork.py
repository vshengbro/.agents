"""fork -- 195 mm table fork: shaped handle, narrow neck, four tapered tines.

Same edge-on presentation as the knife, for the same reason: the silhouette a
fork is recognised by is its side profile. The tine centres come from
`lay_out()` with an explicit gap rather than four hand-typed numbers, because
the spacing is what makes the head read as a fork instead of a comb.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    fork_length=195.0,      # butt of the handle to the tine tips
    head_width=24.0,        # across the four tines
    tine_length=37.0,
    tine_thickness=1.8,
    handle_width=12.0,      # height of the handle at its widest point
    handle_thickness=5.5,
)

TINE_W = 4.5
TINE_GAP = 2.0

# handle: up the top edge from the butt to the neck, back along the bottom
HANDLE = [
    (13.0, 0.0),
    (14.0, 8.0),
    (13.2, 34.0),
    (11.6, 64.0),
    (8.6, 96.0),
    (6.2, 122.0),
    (2.0, 122.0),
    (2.6, 96.0),
    (4.4, 64.0),
    (5.6, 34.0),
    (5.4, 8.0),
    (5.0, 0.0),
]

# head: widens from the neck into the shoulder the tines spring from
HEAD = [
    (6.2, 112.0),
    (8.5, 134.0),
    (12.5, 152.0),
    (12.5, 162.0),
    (3.0, 162.0),
    (3.0, 152.0),
    (2.4, 134.0),
    (2.0, 112.0),
]


def _profile(name, shape, thickness, mat):
    ob = bkit.extrude_profile(name, [(-z, y) for (z, y) in shape],
                              thickness, centre=(0.0, 0.0, 0.0),
                              axis="X", mat=mat)
    # extrude_profile does not orient the winding, and the sign of the signed
    # volume follows the polygon's winding. One recalc settles it either way.
    return bkit.recalc(ob)


def build():
    # A mirror metal reflects this dark studio and renders black. Dropping the
    # metallic fraction to 0.65 keeps a diffuse component for the key light to
    # land on, which is what makes cutlery read as steel instead of a silhouette.
    steel = bkit.pbr("CutlerySteel", base=(0.82, 0.83, 0.85), metal=0.65,
                     rough=0.22)

    handle = _profile("ForkHandle", HANDLE, SPEC["handle_thickness"], steel)
    head = _profile("ForkHead", HEAD, 3.0, steel)

    # ---- tines: one loft each, tapering and lifting slightly to the tip ----
    stations = [(155.0, 4.5, 2.4, 7.5),      # y, width, thickness, centre z
                (175.0, 4.3, 2.0, 7.7),
                (188.0, 3.9, 1.8, 7.9),
                (195.0, 3.2, 1.5, 8.1)]
    tines = []
    for i, (xc, w) in enumerate(bkit.lay_out([TINE_W] * 4, gap=TINE_GAP)):
        sections = []
        for (y, tw, tt, zc) in stations:
            ring = bkit.rounded_rect_section(tw, tt, 0.5, per_corner=3)
            sections.append([(px + xc, y, pz + zc) for (px, pz) in ring])
        tines.append(bkit.loft("Tine%d" % (i + 1), sections, closed_loop=True,
                               cap_start=True, cap_end=True, mat=steel))
    tine_obj = bkit.recalc(bkit.join(tines, name="ForkTines"))

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="fork_length", mm=195.0, tol=0.3, how="bbox_y"),
    dict(name="head_width", mm=24.0, tol=0.3, how="bbox_x", part="ForkTines"),
    dict(name="handle_width", mm=12.0, tol=0.3, how="bbox_z", part="ForkHandle"),
]
