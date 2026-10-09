"""
solar_panel -- 1956 x 1058 mm monocrystalline PV module, 72 cells (12 x 6).

The cell count has to be right, and it is derived rather than typed:
bkit.grid_positions is called with the real 12 x 6 layout, the module is built
from the returned coordinates, and build() asserts len(cells) == 72 so a change
to the layout that breaks the count fails the build instead of shipping.

The 72 cells are ONE object. Not 72 rounded boxes (72 bevel modifiers, 72
objects, 72 chances for a coincident face) and not a loft of cell rings --
`loft` bridges CONSECUTIVE sections, so a section list holding 72 cell outlines
would weld each cell to its neighbour into one caterpillar. One cell plus two
array_linear modifiers gives 72 closed shells in a single part in one bake.

Layout is the real construction: 156 mm wafers on a 159 mm pitch (3 mm gap)
inside a 32 mm aluminium frame with the frame lip overlapping the outer cells,
as it does on a real 72-cell module.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    module_length=1956.0,    # standard 72-cell module
    module_width=1058.0,
    frame_height=32.0,
    frame_width=32.0,
    cell_columns=12,
    cell_rows=6,
    cell_size=156.0,         # standard mono wafer
    cell_pitch=159.0,        # 156 mm cell + 3 mm gap
    cell_thickness=3.2,
    cell_count=72,           # 12 * 6 -- asserted against grid_positions
)

FRAME_H = SPEC["frame_height"]
CELL_T = SPEC["cell_thickness"]


def build():
    frame_mat = bkit.preset("anodized")
    backsheet = bkit.preset("white_plastic")
    silicon = bkit.pbr("SolarCell", base=(0.045, 0.055, 0.115), metal=0.30,
                       rough=0.16, coat=0.65)

    L = SPEC["module_length"]
    W = SPEC["module_width"]
    cs = SPEC["cell_size"]
    pitch = SPEC["cell_pitch"]
    cols, rows = SPEC["cell_columns"], SPEC["cell_rows"]

    # ---- the computed grid: one call defines layout AND count -----------
    cells = bkit.grid_positions(cols=cols, rows=rows, pitch_x=pitch, pitch_y=pitch)
    if len(cells) != SPEC["cell_count"]:
        raise ValueError("cell grid is %d cells, SPEC declares %d"
                         % (len(cells), SPEC["cell_count"]))

    # ---- frame: four rails, so the aperture is genuinely open -----------
    inner_l = L - 2 * SPEC["frame_width"]
    inner_w = W - 2 * SPEC["frame_width"]
    fw = SPEC["frame_width"]
    rails = [
        bkit.rounded_box("_railN", L, fw, FRAME_H, r=3.0, segments=3,
                         centre=(0.0, W / 2.0 - fw / 2.0, FRAME_H / 2.0), mat=frame_mat),
        bkit.rounded_box("_railS", L, fw, FRAME_H, r=3.0, segments=3,
                         centre=(0.0, -W / 2.0 + fw / 2.0, FRAME_H / 2.0), mat=frame_mat),
        bkit.rounded_box("_railW", fw, inner_w, FRAME_H, r=3.0, segments=3,
                         centre=(-L / 2.0 + fw / 2.0, 0.0, FRAME_H / 2.0), mat=frame_mat),
        bkit.rounded_box("_railE", fw, inner_w, FRAME_H, r=3.0, segments=3,
                         centre=(L / 2.0 - fw / 2.0, 0.0, FRAME_H / 2.0), mat=frame_mat),
    ]
    frame_ob = bkit.join(rails, name="PanelFrame")

    # ---- backsheet the cells are laminated onto ------------------------
    sheet = bkit.rounded_box("PanelBacksheet", inner_l, inner_w, 6.0, r=1.5,
                             segments=3, centre=(0.0, 0.0, 3.0), mat=backsheet)

    # ---- 72 cells in ONE part: one cell + two arrays --------------------
    # grid_positions is row-major with a pitch of `pitch`, so a single cell
    # placed on cells[0] reproduces the whole grid exactly.
    cells_ob = bkit.rounded_box("PanelCells", cs, cs, CELL_T, r=4.0, segments=2,
                                centre=(cells[0][0], cells[0][1], 6.0 + CELL_T / 2.0),
                                mat=silicon)
    bkit.array_linear(cells_ob, cols, (pitch, 0.0, 0.0))
    bkit.array_linear(cells_ob, rows, (0.0, pitch, 0.0))
    bkit.recalc(cells_ob)

    # ---- junction box on the back --------------------------------------
    jbox = bkit.rounded_box("PanelJunctionBox", 130.0, 90.0, 26.0, r=6.0,
                            segments=3, centre=(0.0, 0.0, -13.0), mat=backsheet)

    return dict(spec=SPEC, parts=5, cell_count=len(cells),
                cell_grid="%dx%d" % (cols, rows))


CHECKS = [
    dict(name="module_length", mm=1956.0, tol=0.6, how="bbox_x", part="PanelFrame"),
    dict(name="module_width", mm=1058.0, tol=0.6, how="bbox_y", part="PanelFrame"),
    dict(name="frame_height", mm=32.0, tol=0.4, how="bbox_z", part="PanelFrame"),
    dict(name="cell_block_length", mm=1905.0, tol=0.6, how="bbox_x", part="PanelCells"),
    dict(name="cell_block_width", mm=951.0, tol=0.6, how="bbox_y", part="PanelCells"),
]