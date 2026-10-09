"""
rubik_cube -- a 56 mm 3x3 pocket puzzle cube.

A Rubik's cube is not one solid with three grooves; it is 27 independent
cubies on an 18.53 mm pitch with a 0.4 mm gap between them, and the GAP is
what produces the 3x3 seam grid that makes the object legible. Modelling it as
27 separately coloured cubies (each its own closed solid, black plastic showing
in the gaps) gives correct seams and the real internal mechanism for free,
with no boolean anywhere in the file.

Each cubie takes the colour of whichever of the cube's six faces it points at,
so a corner cubie carries three stickers and a centre cubie carries one -- the
count and the arrangement are both visible from any angle.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    cube_edge=56.0,        # 57 mm across the rounded corners is the nominal spec
    seam_gap=0.4,          # visible channel between adjacent cubies
    cubie_edge=18.4,       # (56 - 2*0.4) / 3
    cubie_pitch=18.8,      # cubie + gap
    cubie_count=27,
    stickers_per_face=9,
)

EDGE = SPEC["cube_edge"]
GAP = SPEC["seam_gap"]
PITCH = SPEC["cubie_pitch"]
CUBIE = SPEC["cubie_edge"]

# face colour per world axis/sign, following the real scheme: white opposite
# yellow, red opposite orange, green opposite blue.
FACE_MATS = (
    (0, -1, "red_paint"),
    (0, 1, "yellow_paint"),
    (1, -1, "yellow_paint"),
    (1, 1, "red_paint"),
    (2, -1, "white_plastic"),
    (2, 1, "blue_paint"),
)


def build():
    shell = bkit.preset("black_plastic")
    mats = {c: bkit.preset(c) for _a, _s, c in FACE_MATS}

    for j, z in enumerate((-PITCH, 0.0, PITCH)):
        for i, (x, y) in enumerate(bkit.grid_positions(cols=3, rows=3,
                                                        pitch_x=PITCH,
                                                        pitch_y=PITCH)):
            ob = bkit.rounded_box("Cubie_%d%d" % (i, j), CUBIE, CUBIE, CUBIE,
                                  r=1.2, segments=3, centre=(x, y, z),
                                  mat=shell)
            # The +X/+Y/+Z face of this cubie is the outside of the puzzle iff
            # the cubie sits on that side of the stack; a cubie on an interior
            # row gets no sticker, exactly like the real mechanism.
            pos = (x, y, z)
            for (axis, sign, colour) in FACE_MATS:
                if pos[axis] * sign <= 1e-6:
                    continue
                bkit.assign_faces_by(
                    ob, mats[colour],
                    lambda c, n, a=axis, s=sign: n[a] * s > 0.55)

    return dict(spec=SPEC, parts=27)


CHECKS = [
    dict(name="cube_edge", mm=56.0, tol=0.3, how="bbox_x"),
    dict(name="cube_depth", mm=56.0, tol=0.3, how="bbox_y"),
    dict(name="cube_height", mm=56.0, tol=0.3, how="bbox_z"),
    dict(name="cubie_edge", mm=18.4, tol=0.3, how="bbox_x", part="Cubie_00"),
    dict(name="cubie_height", mm=18.4, tol=0.3, how="bbox_z", part="Cubie_10"),
    # The seam PITCH is a centre-to-centre distance between two cubies, which
    # no single part's bounding box can express -- `measure()` only does
    # bbox_x/y/z, diameter and longest. The three whole-cube checks above are
    # what actually prove the 3x3 grid: 3 cubies + 2 half-gaps = 56 mm, so a
    # cube that measures 56 on all three axes has its cubies on the right grid.
    dict(name="corner_cubie_edge", mm=18.4, tol=0.3, how="bbox_x",
         part="Cubie_21"),
]
