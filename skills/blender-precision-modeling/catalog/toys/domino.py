"""
domino -- a 50 x 25 x 8.5 mm double-six domino tile with real pips.

The count is the model. A blank cream slab is a domino-shaped eraser; a tile
with a score line down the middle and 6 pips on one half and 4 on the other
is a domino. Both halves are drilled with the standard 1..6 arrangements, and
the pips are recessed 0.8 mm into the face rather than printed on it, so they
catch a shadow instead of reading as flat dots.

The one thing this model gets right by construction: every cutter is positioned
so that it STARTS OUTSIDE the tile and ends PD below the surface. A cutter
whose top face stops exactly at the scored face cuts an internal void that
never breaks the skin -- the mesh still reports watertight and the render
still shows a blank slab.

The tile is stood on its long edge with the scored face turned toward +X, so
the pips face the hero and three-quarter cameras instead of the floor.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    tile_length=50.0,      # a standard double-six tile
    tile_width=25.0,
    tile_thickness=8.5,
    corner_radius=1.6,
    pip_radius=1.5,
    pip_depth=0.8,
    pip_spacing=6.0,       # centre-to-centre inside one half
    pips_left=6,
    pips_right=4,
    pip_count=10,
    divider_width=0.9,
    divider_depth=0.5,
)

LX = SPEC["tile_length"]
LY = SPEC["tile_width"]
LT = SPEC["tile_thickness"]
TOP = LT                      # scored face, in the flat authoring frame
PR = SPEC["pip_radius"]
PD = SPEC["pip_depth"]
PS = SPEC["pip_spacing"]
CUT = 5.0                    # cutter length; only PD of it is inside the tile

# (u, v) offsets for 1..6 pips on one half, in units of pip_spacing.
PIP_GRID = {
    1: [(0, 0)],
    2: [(-1, -1), (1, 1)],
    3: [(-1, -1), (0, 0), (1, 1)],
    4: [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)],
    6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)],
}

# The tile is authored flat on the floor with the scored face up, so the pip
# grid is laid out in real face coordinates. Half centres are +-LX/4.
HALF_CENTRE = LX / 4.0


def _pips(count, cx):
    """Face-plane pip centres on the scored face for one half of the tile."""
    return [(cx + u * PS, v * PS) for (u, v) in PIP_GRID[count]]


def _pip_pred(pips):
    reach2 = (PR * 2.1) ** 2

    def pred(centre, normal):
        p = (centre.x / bkit.MM, centre.y / bkit.MM, centre.z / bkit.MM)
        if p[2] > TOP - 0.25:
            return False                     # the untouched outer face
        for (x, y) in pips:
            if (p[0] - x) ** 2 + (p[1] - y) ** 2 <= reach2:
                return True
        return False
    return pred


def build():
    ivory = bkit.pbr("DominoIvory", base=(0.91, 0.88, 0.80), rough=0.20, coat=0.35)
    ink = bkit.pbr("DominoInk", base=(0.10, 0.09, 0.10), rough=0.28)
    line = bkit.pbr("DominoScore", base=(0.42, 0.09, 0.08), rough=0.30)

    tile = bkit.rounded_box("Domino", LX, LY, LT, r=SPEC["corner_radius"],
                            segments=5, centre=(0.0, 0.0, LT / 2.0), mat=ivory)

    # ---- pips. The cutter spans [TOP-PD, TOP-PD+CUT], so it crosses the
    # scored face by CUT-PD = 4.2 mm and cuts a real 0.8 mm dimple.
    left = _pips(SPEC["pips_left"], -HALF_CENTRE)
    right = _pips(SPEC["pips_right"], HALF_CENTRE)
    for (x, y) in left + right:
        bkit.bore(tile, PR, CUT, centre=(x, y, TOP - PD + CUT / 2.0),
                  axis="Z", host_segments=32)

    # ---- the score line: a shallow channel down the middle of the tile. It
    # is 0.9 mm wide and 0.5 mm deep and it crosses the surface, so the two
    # halves read as two halves.
    bkit.boolean(tile,
                 bkit.box("_score", SPEC["divider_width"], LY - 5.0, CUT,
                          centre=(0.0, 0.0, TOP - SPEC["divider_depth"]
                                  + CUT / 2.0), mat=None),
                 "DIFFERENCE")
    bkit.recalc(tile)

    bkit.assign_faces_by(tile, ink, _pip_pred(left + right))
    # the score groove gets its own colour: a real tile has the divider
    # painted, and colour is what makes the two halves read as two halves.
    bkit.assign_faces_by(
        tile, line,
        lambda c, n: abs(c.x / bkit.MM) < 1.3 and c.z / bkit.MM < TOP - 0.15)

    # ---- stand the tile on its long edge, scored face toward +X. A +90 deg
    # turn about Y maps the authored +Z face to +X, which is where the hero
    # (az -35) and three-quarter (az +40) cameras both live.
    tile.rotation_euler = (0.0, 1.5707963, 0.0)
    bpy.context.view_layer.update()

    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="tile_length", mm=50.0, tol=0.3, how="bbox_z", part="Domino"),
    dict(name="tile_width", mm=25.0, tol=0.3, how="bbox_y", part="Domino"),
    dict(name="tile_thickness", mm=8.5, tol=0.3, how="bbox_x", part="Domino"),
]
