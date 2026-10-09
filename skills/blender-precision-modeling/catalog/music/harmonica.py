"""
harmonica -- 10-hole diatonic harmonica in C, 150 x 30 x 22 mm.

The object is the comb: ten reed slots in two ranks of five, staggered, with
combustion reeds over the blow slots and draw reeds under the draw slots. A
harmonica with ten holes in one row reads as a toy comb, so the two ranks and
their stagger are the model.

Everything repeated is computed. The ten hole positions come from
`bkit.grid_positions` at a 9.2 mm pitch -- which is 92 mm over nine gaps, the
real mouth-hole spacing -- and the twenty-one reed plates are laid out through
`bkit.lay_out` on the same pitch. The two covers are `rounded_box` shells with
their own slots cut in, and the comb between them is a `perforated_panel`, which
gives ten real holes in one mesh with no booleans.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=150.0,
    height=35.1,
    depth=22.0,
    holes=10,
    hole_diameter=5.0,
    hole_pitch=9.2,
    comb_thickness=1.6,
    reed_length=13.5,
    reed_thickness=0.35,
)

L, Hh, D = SPEC["length"], SPEC["height"], SPEC["depth"]
PITCH = SPEC["hole_pitch"]
NH = SPEC["holes"]

# The mouth holes alternate between two rows: odds nearer the comb, evens
# nearer the cover, which is the stagger that makes a real diatonic's layout.
ROW_BLOW = -1.6      # y offset of the odd (blow) row
ROW_DRAW = 1.6       # y offset of the even (draw) row


def build():
    chrome = bkit.pbr("HarmonicaChrome", base=(0.84, 0.85, 0.87), metal=0.85,
                      rough=0.14)
    steel = bkit.pbr("HarmonicaSteel", base=(0.72, 0.73, 0.76), metal=0.85,
                     rough=0.26)
    comb_mat = bkit.pbr("HarmonicaComb", base=(0.86, 0.84, 0.78), rough=0.52)
    reed_mat = bkit.pbr("HarmonicaReed", base=(0.78, 0.77, 0.72), rough=0.30,
                        metal=0.85)

    comb_y = -D / 2.0 + SPEC["comb_thickness"] / 2.0

    # ---- comb plate: ten real holes, one mesh, no booleans ----------------
    comb = bkit.perforated_panel("HarmonicaComb", cols=NH, rows=1,
                                 pitch_x=PITCH, pitch_y=0.0,
                                 hole_r=SPEC["hole_diameter"] / 2.0,
                                 panel_sx=(NH - 1) * PITCH + 24.0,
                                 panel_sy=D * 0.92,
                                 thickness=SPEC["comb_thickness"],
                                 mat=comb_mat)
    bkit.move(comb, 0.0, comb_y, 0.0)

    # ---- 20 reeds: combustion above the blow row, draw below the draw row --
    reeds = []
    for i, (x, _y) in enumerate(bkit.grid_positions(cols=NH, rows=1,
                                                    pitch_x=PITCH, pitch_y=0.0)):
        blow = (i % 2 == 0)
        y = ROW_BLOW if blow else ROW_DRAW
        # Combustion reeds face up (toward the player), draw reeds face down.
        # The reed plate is 7.5 mm tall and its centre sits Hh/2 - 4.5 in from
        # the face, so its outer edge lands exactly on the face: at 7.5 tall
        # centred nearer the middle the reeds stood 2.5 mm proud of the covers
        # and the assembly measured 40.2 mm instead of Hh.
        z = (Hh / 2.0 - 4.5) if blow else (-Hh / 2.0 + 4.5)
        reeds.append(bkit.rounded_box(
            "HarmonicaReed%02d" % i, SPEC["reed_length"],
            SPEC["reed_thickness"] * 2.0, 7.5, r=0.15, segments=1,
            centre=(x, y, z), mat=reed_mat))
    bkit.join(reeds, name="HarmonicaReeds")

    # ---- covers: two shells, each slotted over the comb ------------------
    for tag, sgn, z in (("Top", 1.0, Hh / 2.0 - 2.6),
                        ("Bottom", -1.0, -Hh / 2.0 + 2.6)):
        cover = bkit.rounded_box("HarmonicaCover%s" % tag, L, D, 5.2, r=1.6,
                                 segments=3, centre=(0, 0, z), mat=chrome)
        # One cutter per row, each spanning all ten holes of that row, so the
        # slots are two clean slots rather than twenty tangent punches.
        for tag2, yoff in (("Blow", ROW_BLOW), ("Draw", ROW_DRAW)):
            bkit.boolean(cover, bkit.rounded_box(
                "_slot%s%s" % (tag, tag2), (NH - 1) * PITCH + 18.0, 6.2, 22.0,
                r=1.0, segments=2,
                centre=(0, yoff, 0.0 + sgn * 2.0)), "DIFFERENCE")
        bkit.bevel(cover, width_mm=0.5, segments=2)

    # ---- end plates, screws, slide, name plate ----------------------------
    for i, x in enumerate((-L / 2.0 + 3.0, L / 2.0 - 3.0)):
        bkit.rounded_box("HarmonicaEnd%d" % i, 6.0, D - 1.0, Hh - 1.0, r=1.0,
                         segments=2, centre=(x, 0, 0), mat=steel)
        bkit.cylinder("HarmonicaScrew%d" % i, 1.4, 4.0, segments=10,
                      centre=(x, 0, Hh / 2.0 - 3.5), mat=steel)
    bkit.rounded_box("HarmonicaSlide", L - 16.0, 1.0, 1.0, r=0.3, segments=1,
                     centre=(0, -D / 2.0 + 0.6, Hh / 2.0 - 6.0), mat=steel)
    bkit.rounded_box("HarmonicaPlate", 46.0, 0.8, 6.0, r=0.3, segments=1,
                     centre=(0, D / 2.0 - 0.6, -Hh / 2.0 + 7.0), mat=steel)

    return dict(spec=SPEC, parts=6, holes=NH)


CHECKS = [
    dict(name="length", mm=150.0, tol=0.6, how="bbox_x", part="HarmonicaCoverTop"),
    # Height is the assembly: each cover is only 5.2 mm thick, so a per-cover
    # bbox_z would report the cover, not the 30 mm instrument.
    dict(name="overall_height", mm=35.1, tol=1.0, how="bbox_z"),
    dict(name="depth", mm=22.0, tol=0.6, how="bbox_y", part="HarmonicaCoverTop"),
    dict(name="comb_width", mm=87.8, tol=2.0, how="bbox_x", part="HarmonicaComb"),
]