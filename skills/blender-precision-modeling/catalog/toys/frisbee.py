"""
frisbee -- a 135 mm flying disc with a real lip and a dished flight plate.

A frisbee is a solid of revolution with a NON-CIRCULAR cross-section: the
flight plate domes up in the middle, the rim is a thickened lip that rolls
under, and the underside is a shallow bowl. Writing that as one lathed profile
walked from the top centre out over the plate, round the lip, and back in
along the underside is what makes it fly-shaped; a flat disc reads as a plate.

The profile is ordered so that a trace of it never doubles back on itself in
(radius, z). A profile that goes back outward after coming inward crosses
itself, and the lathe then produces a self-intersecting solid with NEGATIVE
VOLUME -- a disc that passes a non-manifold check and renders inside out.

The moulded rim ring and the printed hub are second MATERIALS on the one
solid, selected by radius. A separate ring object would z-fight with both
faces and double the non-manifold count.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    disc_diameter=135.0,
    disc_height=30.0,        # rim lip above the table
    plate_height=4.5,        # the domed flight plate at the centre
    rim_start=54.0,          # radius where the plate starts to roll over
    rim_lip_height=7.0,
    hub_diameter=40.0,
    rim_ring_width=7.0,
)

D = SPEC["disc_diameter"]
R = D / 2.0
H = SPEC["disc_height"]
PLATE = SPEC["plate_height"]
RS = SPEC["rim_start"]
LIPH = SPEC["rim_lip_height"]
HUB = SPEC["hub_diameter"] / 2.0
RING = SPEC["rim_ring_width"] / 2.0


def build():
    red = bkit.preset("red_paint")
    white = bkit.preset("white_plastic")
    blue = bkit.preset("blue_paint")

    # ---- one lathe, walked from the top centre out over the domed plate to
    # the rim, down the rim's outer face, and back in along the concave
    # underside.
    #
    # The two rules that keep this profile simple: radius increases
    # monotonically along the top and decreases monotonically along the
    # bottom, AND every underside point sits clearly BELOW the top surface at
    # the same radius. Break the second rule near the rim and the profile
    # crosses itself there -- the lathe then builds a self-intersecting solid
    # with NEGATIVE VOLUME, which passes a non-manifold check and renders
    # inside out.
    prof = [
        (0.0, 25.5),                 # domed flight plate, highest at the centre
        (30.0, 26.5),
        (54.0, 28.0),
        (66.0, 29.5),
        (R, 30.0),                   # top of the rim
        (R, 26.0),                   # the rim's outer face, 4 mm of lip
        (54.0, 22.0),                # concave underside, coming back in
        (30.0, 12.0),
        (12.0, 5.0),
        (0.0, 0.0),                  # underside centre, on the table
    ]
    disc = bkit.lathe("Frisbee", prof, segments=72, mat=red)
    bkit.recalc(disc)
    bkit.shade_smooth(disc, 34)

    # ---- moulded rim ring and a printed hub: disjoint radius bands, so no
    # face is claimed twice and the order they are applied in does not matter
    bkit.assign_faces_by(
        disc, white,
        lambda c, n: R - 4.0 - RING < ((c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM)
        <= R - 4.0 + RING)
    # The hub band has to be at least as wide as the radius of the first
    # profile ring, or it selects no face at all: the lathe's topmost band
    # runs from the pole out to r=30, and its face CENTRES sit at r=15, so a
    # 14 mm threshold paints nothing and the disc comes out all red.
    bkit.assign_faces_by(
        disc, blue,
        lambda c, n: (c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM <= HUB)

    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="disc_diameter", mm=135.0, tol=0.6, how="diameter", part="Frisbee"),
    dict(name="disc_height", mm=30.0, tol=0.8, how="bbox_z", part="Frisbee"),
    dict(name="disc_depth", mm=135.0, tol=0.6, how="bbox_y", part="Frisbee"),
]
