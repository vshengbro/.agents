"""
wood_screw -- #8 x 40 mm slotted pan-head wood screw.

Wood screws are coarse: a #8 has a 4.2 mm major diameter on a 3.2 mm lead
pitch, which is why its thread reads as deep stacked flutes rather than the
fine helical ridge of a machine screw. The point is a 40 degree tapered cone
(2.5 diameters long, the usual wood-screw practice) and the head is slotted,
not Phillips, because a single flat-bottomed slot is the profile a render can
actually show as depth.

The head and the shank are separate watertight solids rather than one joined
mesh, so each CHECKS entry can be measured against the part that owns the
dimension instead of against a bounding box that also contains the other part.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

MAJOR_D = 4.2            # #8 major diameter
ROOT_R = 1.55            # thread root radius
CREST_R = MAJOR_D / 2.0
PITCH = 3.2              # coarse lead
LENGTH = 40.0            # under the head
THREAD_START = 8.0       # smooth shank above the point
HEAD_DIA = 8.0           # pan head
HEAD_HEIGHT = 2.6        # above the shank top
SLOT_WIDTH = 1.1
SLOT_DEPTH = 0.7

SPEC = dict(major_diameter=MAJOR_D,
            lead_pitch=PITCH,
            length=LENGTH,
            head_diameter=HEAD_DIA,
            head_height=HEAD_HEIGHT,
            slot_width=SLOT_WIDTH)


def build():
    # zinc-plated steel: see socket_screw.py for why metal < 1.0 in this studio
    steel = bkit.pbr("ScrewZinc", base=(0.76, 0.78, 0.80), metal=0.70, rough=0.30)

    # ---- shank: tapered point, smooth length, coarse sawtooth thread -----
    prof = [(0.0, 0.0)]
    for i in range(1, 9):                       # 40 deg tapered point
        t = i / 8.0
        prof.append((ROOT_R * t * t, THREAD_START * t))
    prof.append((ROOT_R, THREAD_START))
    z = THREAD_START
    while z < LENGTH - 0.6 * PITCH:
        prof += [(CREST_R, z + 0.05 * PITCH),
                 (CREST_R, z + 0.45 * PITCH),
                 (ROOT_R, z + 0.55 * PITCH),
                 (ROOT_R, z + 0.95 * PITCH)]
        z += PITCH
    prof += [(CREST_R, LENGTH), (0.0, LENGTH)]

    shank = bkit.lathe("ScrewShank", prof, segments=64, mat=steel)

    # ---- pan head, domed, with a slot milled across it ------------------
    head = bkit.lathe("ScrewHead",
                      [(0.0, LENGTH), (CREST_R, LENGTH),
                       (CREST_R, LENGTH + 0.4), (HEAD_DIA / 2.0 - 0.4,
                                                  LENGTH + 1.7),
                       (HEAD_DIA / 2.0, LENGTH + 2.2),
                       (HEAD_DIA / 2.0, LENGTH + 2.4),
                       (2.4, LENGTH + HEAD_HEIGHT),
                       (0.0, LENGTH + HEAD_HEIGHT)],
                      segments=64, mat=steel)
    slot = bkit.box("SlotCutter", 6.6, SLOT_WIDTH, 1.6,
                    centre=(0, 0, LENGTH + HEAD_HEIGHT + 0.1))
    bkit.boolean(head, slot, "DIFFERENCE")

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="head_diameter", mm=8.0, tol=0.05, how="bbox_x", part="ScrewHead"),
    dict(name="major_diameter", mm=4.2, tol=0.05, how="bbox_x", part="ScrewShank"),
    dict(name="shank_length", mm=40.0, tol=0.10, how="bbox_z", part="ScrewShank"),
    dict(name="overall_length", mm=42.6, tol=0.20, how="bbox_z", part=None),
]