"""
crate -- a slatted wooden crate: four corner posts, three horizontal boards per
face, and a plank floor.

Every repeated board comes from `lay_out()` with its real width and one gap, as
hard rule 4 requires. Hand-placed constants on four faces put two boards on the
same coordinate, and the result looks like a crate missing half its slats.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=400.0,             # along X
    width=300.0,              # along Y
    height=260.0,
    board=14.0,               # slat thickness
    post=26.0,                # corner post section
    slat_gap=22.0,            # air between slats
    slat_inset=6.0,           # slats sit inside the post faces
)

L = SPEC["length"]
W = SPEC["width"]
H = SPEC["height"]
B = SPEC["board"]
P = SPEC["post"]
GAP = SPEC["slat_gap"]
INSET = SPEC["slat_inset"]

# Materials belong inside build(): run_model.py calls bkit.reset() after import,
# and reset() is a factory-settings read that deletes anything made before it.


def build():
    wood = bkit.preset("wood")
    wood_dark = bkit.pbr("CrateWoodDark", base=(0.26, 0.145, 0.065), rough=0.56)

    # ---- floor planks, laid out across the width ---------------------------
    # Two planks per row computed from their own width plus a gap, so the floor
    # always fills the footprint exactly whatever the crate size becomes.
    rows = []
    n_planks = 2
    plank_w = (W - P * 2 - GAP * (n_planks - 1)) / n_planks
    for i, (cy, _w) in enumerate(bkit.lay_out([plank_w] * n_planks, gap=GAP)):
        rows.append(bkit.rounded_box(
            "CrateFloor%d" % (i + 1), L - P * 2, plank_w, B, r=2.0,
            segments=2, centre=(0.0, cy, B / 2.0), mat=wood))

    # ---- four corner posts --------------------------------------------------
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        bkit.rounded_box("CratePost%d" % (i + 1), P, P, H, r=2.5, segments=2,
                         centre=(sx * (L / 2.0 - P / 2.0),
                                 sy * (W / 2.0 - P / 2.0), H / 2.0),
                         mat=wood_dark)

    # ---- three horizontal slats per face, heights computed once ------------
    # Same vertical rhythm on all four faces, so the crate reads as one object.
    usable = H - B - 8.0
    slat_h = (usable - GAP * 2) / 3.0
    z_top = H - 6.0
    heights = [z_top - slat_h / 2.0 - i * (slat_h + GAP) for i in range(3)]
    for zi, cz in enumerate(heights):
        # long faces, front and back
        for yi, sy in enumerate((-1.0, 1.0)):
            bkit.rounded_box(
                "CrateSlatL%d%s" % (zi, "AB"[yi]),
                L - P * 2 + INSET, B, slat_h, r=2.0, segments=2,
                centre=(0.0, sy * (W / 2.0 - B / 2.0), cz), mat=wood)
        # short faces, left and right
        for xi, sx in enumerate((-1.0, 1.0)):
            bkit.rounded_box(
                "CrateSlatS%d%s" % (zi, "AB"[xi]),
                B, W - P * 2 + INSET - 2 * B, slat_h, r=2.0, segments=2,
                centre=(sx * (L / 2.0 - B / 2.0), 0.0, cz), mat=wood)

    # ---- a top rail pair, nailed on -----------------------------------------
    for i, (cx, _w) in enumerate(bkit.lay_out([P, P], gap=(W - P * 2 - 40.0))):
        bkit.rounded_box("CrateTopRail%d" % (i + 1), L - P * 2 + INSET, P, B,
                         r=2.0, segments=2,
                         centre=(0.0, cx, H - B / 2.0), mat=wood_dark)

    return dict(spec=SPEC, parts=20)


CHECKS = [
    dict(name="length", mm=400.0, tol=0.5, how="bbox_x"),
    dict(name="width", mm=300.0, tol=0.5, how="bbox_y"),
    dict(name="height", mm=260.0, tol=0.5, how="bbox_z"),
]
