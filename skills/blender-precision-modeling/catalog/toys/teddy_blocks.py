"""
teddy_blocks -- four 24 mm wooden alphabet blocks in a real 2x2 stack.

A set of building blocks reads by three things: the SIZE (a 24 mm wooden
alphabet block, not a 60 mm foam brick), the COUNT, and the letters. The
letters are the hard part and they are built as real geometry -- seven
segments' worth of small boxes per block -- rather than as texture, because a
block with a texture and no letter reads as a blank cube in a render.

The blocks are laid out with `grid_positions` and stacked with a real 0.6 mm
reveal between courses, so the stack has visible joints instead of merging
into one solid lump. Every block is a separate closed solid, which is why a
twelve-part assembly is still watertight.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    block_size=24.0,        # a standard wooden alphabet block
    corner_radius=2.2,
    reveal=0.6,             # the visible joint between two courses
    block_count=4,
    course_count=2,
    letter_stroke=2.4,
    stack_height=48.6,      # 2 courses of 24 plus one reveal
    stack_width=48.0,
)

B = SPEC["block_size"]
R = SPEC["corner_radius"]
G = SPEC["reveal"]
LS = SPEC["letter_stroke"]      # stroke width
LT = SPEC["letter_stroke"] * 0.55   # stroke relief off the face

# Each letter is a list of (x, y, w, h) strokes in a -1..1 face frame:
# x/y are centres, w/h are full sizes. Drawn as one horizontal bar of the
# block, and repeated on the +X face so the hero and side views both show one.
LETTERS = {
    "A": [(-0.45, -0.35, 0.30, 0.75), (0.45, -0.35, 0.30, 0.75),
          (0.0, 0.05, 0.30, 0.75), (0.0, 0.45, 0.70, 0.26)],
    "B": [(-0.42, 0.0, 0.30, 1.0), (0.15, 0.28, 0.62, 0.34),
          (0.15, -0.28, 0.62, 0.34)],
    "C": [(0.0, 0.42, 0.9, 0.30), (-0.30, 0.0, 0.30, 0.9),
          (0.0, -0.42, 0.9, 0.30)],
    "D": [(-0.40, 0.0, 0.30, 1.0), (0.18, 0.30, 0.55, 0.34),
          (0.18, -0.30, 0.55, 0.34)],
}

# the four blocks: (letter, colour, x, y, course)
BLOCKS = (
    ("A", "red_paint", -1, -1, 0),
    ("B", "blue_paint", 1, -1, 0),
    ("C", "yellow_paint", 1, 1, 0),
    ("D", "red_paint", -1, 1, 1),
)


def _letter(name, letter, x, y, z, face, ink):
    """Raised letter strokes on one face of a block, as one joined solid."""
    strokes = []
    for (sx, sy, sw, sh) in LETTERS[letter]:
        # face frame -> world
        if face == "Z":
            c = (x + sx * B * 0.34, y + sy * B * 0.34,
                 z + B / 2.0 + LT / 2.0)
            dim = (sw * B * 0.34, sh * B * 0.34, LT)
        else:                                   # "X"
            c = (x + B / 2.0 + LT / 2.0, y + sx * B * 0.34,
                 z + sy * B * 0.34)
            dim = (LT, sw * B * 0.34, sh * B * 0.34)
        strokes.append(bkit.box("_st", dim[0], dim[1], dim[2],
                                centre=c, mat=ink))
    return bkit.join(strokes, name)


def build():
    mats = {c: bkit.preset(c) for c in
            ("red_paint", "blue_paint", "yellow_paint", "white_plastic")}
    ink = bkit.pbr("BlockInk", base=(0.06, 0.06, 0.07), rough=0.35)

    for (letter, colour, gx, gy, course) in BLOCKS:
        x = gx * (B / 2.0 + G / 2.0)
        y = gy * (B / 2.0 + G / 2.0)
        z = B / 2.0 + course * (B + G)
        blk = bkit.rounded_box("Block_%s" % letter, B, B, B, r=R,
                               segments=4, centre=(x, y, z),
                               mat=mats[colour])
        bkit.shade_smooth(blk, 34)
        # a letter on the top face and one on the +X face, so the hero shot
        # and the side shot each show a character
        _letter("Letter_%s_Top" % letter, letter, x, y, z, "Z", ink)
        _letter("Letter_%s_Side" % letter, letter, x, y, z, "X", ink)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2 * len(BLOCKS))


CHECKS = [
    dict(name="block_size", mm=24.0, tol=0.3, how="bbox_x", part="Block_A"),
    dict(name="block_height", mm=24.0, tol=0.3, how="bbox_z", part="Block_A"),
    # the two courses are 24 + 24 with a 0.6 reveal between them, and the
    # raised letters stand LT proud of the top and the +X faces
    dict(name="stack_width", mm=49.9, tol=0.4, how="bbox_x"),
    dict(name="stack_depth", mm=48.6, tol=0.4, how="bbox_y"),
    dict(name="stack_height", mm=49.9, tol=0.4, how="bbox_z"),
]
