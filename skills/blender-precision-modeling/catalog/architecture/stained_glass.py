"""
stained_glass -- a tall stained-glass panel: a leaded lattice in a real
frame, with coloured glass lights in each cell.

Large size class (600..3000 mm): 1.85 m tall. The read is the LEAD -- the
came network -- so the lattice is real extruded geometry in front of coloured
panes, not a texture. Panel positions come from `grid_positions`, so no two
lights can land on the same coordinate.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=1100.0,
    height=1850.0,
    frame_width=70.0,
    frame_depth=45.0,
    lead_width=22.0,
    lead_depth=26.0,
    columns=4,
    rows=7,
    glass_depth=8.0,
)

W = SPEC["width"]
H = SPEC["height"]
FW = SPEC["frame_width"]
LW = SPEC["lead_width"]
NC = SPEC["columns"]
NR = SPEC["rows"]

IN_W = W - 2.0 * FW
IN_H = H - 2.0 * FW


def build():
    lead = bkit.preset("dark_metal")
    glass_mats = [
        bkit.pbr("GlassRuby", base=(0.62, 0.10, 0.12), rough=0.10,
                 transmission=0.55),
        bkit.pbr("GlassCobalt", base=(0.10, 0.22, 0.58), rough=0.10,
                 transmission=0.55),
        bkit.pbr("GlassAmber", base=(0.78, 0.52, 0.10), rough=0.10,
                 transmission=0.55),
        bkit.pbr("GlassEmerald", base=(0.10, 0.44, 0.28), rough=0.10,
                 transmission=0.55),
    ]

    # ---- frame: four members, mitred by overlapping half-lengths --------
    for sx, tag in ((-1, "L"), (1, "R")):
        bkit.rounded_box("FrameStile%s" % tag, FW, SPEC["frame_depth"], H,
                         r=6.0, segments=2,
                         centre=(sx * (W / 2.0 - FW / 2.0), 0.0, H / 2.0),
                         mat=lead)
    for sz, tag in ((1, "T"), (-1, "B")):
        bkit.rounded_box("FrameRail%s" % tag, W - 2.0 * FW,
                         SPEC["frame_depth"], FW, r=6.0, segments=2,
                         centre=(0.0, 0.0,
                                 H / 2.0 + sz * (H / 2.0 - FW / 2.0)), mat=lead)

    # ---- coloured glass lights, one per cell ---------------------------
    pitch_x = IN_W / NC
    pitch_y = IN_H / NR
    # Deterministic colour choice: a 4-colour cycle down each column, so the
    # panel reads as a repeating pattern rather than noise.
    for (x, y) in bkit.grid_positions(NC, NR, pitch_x, pitch_y):
        c = int(round((x / pitch_x + (NC - 1) / 2.0))) % len(glass_mats)
        c = (c + int(round((y / pitch_y + (NR - 1) / 2.0)))) % len(glass_mats)
        bkit.rounded_box("Light_%d" % c, pitch_x - LW, SPEC["glass_depth"],
                         pitch_y - LW, r=3.0, segments=1,
                         centre=(x, SPEC["frame_depth"] / 2.0 - 10.0,
                                 H / 2.0 + y),
                         mat=glass_mats[c])

    # ---- lead cames: the vertical and horizontal lattice ---------------
    # One vertical run and one horizontal run, both swept, so the grid is 2
    # + NC + NR members rather than NC*NR boxes.
    for i in range(NC + 1):
        x = -IN_W / 2.0 + i * pitch_x
        bkit.rounded_box("CameV%d" % i, LW, SPEC["lead_depth"], IN_H, r=4.0,
                         segments=1, centre=(x, SPEC["frame_depth"] / 2.0
                                             - 2.0, H / 2.0), mat=lead)
    for j in range(NR + 1):
        z = -IN_H / 2.0 + j * pitch_y
        bkit.rounded_box("CameH%d" % j, IN_W, SPEC["lead_depth"], LW, r=4.0,
                         segments=1, centre=(0.0, SPEC["frame_depth"] / 2.0
                                            - 2.0, H / 2.0 + z), mat=lead)

    return dict(spec=SPEC, parts=4 + NC * NR + NC + 1 + NR + 1,
                lights=NC * NR)


CHECKS = [
    dict(name="width", mm=1100.0, tol=3.0, how="bbox_x"),
    dict(name="panel_height", mm=1850.0, tol=4.0, how="bbox_z",
         part="FrameStileL"),
    dict(name="frame_depth", mm=45.0, tol=2.0, how="bbox_y", part="FrameStileL"),
    dict(name="frame_width", mm=70.0, tol=2.0, how="bbox_x", part="FrameStileL"),
    dict(name="overall_height", mm=1850.0, tol=4.0, how="bbox_z"),
]
