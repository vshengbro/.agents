"""
circuit_board -- 150 x 100 x 1.6 mm microcontroller board, populated.

A bare PCB is a green rectangle; what makes this read as a board is the
population and the counts. A 2 x 10 pin header at the real 2.54 mm pitch, six
SMD passives on a `grid_positions` lattice, three electrolytic cans, two
bga-ish ICs with pin rows on an `array_linear`, and four mounting holes
drilled with `bkit.bore` so the cutters never share a segment count with the
board they pass through.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=150.0,
    width=100.0,
    board_thickness=1.6,
    header_pins=20,
    pin_pitch=2.54,
    smd_parts=24,
    capacitors=3,
)

L, W, T = SPEC["length"], SPEC["width"], SPEC["board_thickness"]
PITCH = SPEC["pin_pitch"]


def build():
    pcb_mat = bkit.pbr("BoardSoldermask", base=(0.07, 0.24, 0.15), rough=0.48)
    chip = bkit.pbr("BoardChip", base=(0.11, 0.11, 0.13), rough=0.42)
    gold = bkit.preset("gold")
    silver = bkit.preset("brushed_metal")
    can = bkit.pbr("BoardCap", base=(0.20, 0.26, 0.42), rough=0.34)
    smd = bkit.pbr("BoardSmd", base=(0.55, 0.52, 0.44), rough=0.42)
    plastic = bkit.pbr("BoardPlastic", base=(0.10, 0.10, 0.12), rough=0.40)

    board = bkit.rounded_box("BoardPcb", L, W, T, r=1.5, segments=2,
                             centre=(0, 0, T / 2.0), mat=pcb_mat)

    # ---- four mounting holes, drilled off the real corner pattern --------
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=L - 12.0,
                                                   pitch_y=W - 12.0)):
        bkit.bore(board, radius=3.2, depth=6.0, centre=(x, y, T / 2.0),
                  host_segments=32)

    # ---- the main controller, sunk 0.1 mm into the solder mask ----------
    bkit.rounded_box("BoardMcu", 32.0, 32.0, 3.2, r=1.0, segments=2,
                     centre=(-28.0, 4.0, 2.4), mat=chip)
    mcu_pins = []
    # z = 1.85 puts the 0.5 mm pins proud of the 1.6 mm board surface and
    # flush with the package edge; dropped to the board mid-plane they vanish
    # inside the solder mask, which is where a first pass put them.
    for i, y in enumerate((-13.0, 21.0)):
        pin = bkit.box("_mp%d" % i, 32.0, 1.4, 0.5,
                       centre=(-28.0, y, 1.85), mat=silver)
        bkit.array_linear(pin, count=8, offset_mm=(4.0, 0, 0))
        mcu_pins.append(pin)
    bkit.join(mcu_pins, name="BoardMcuPins")

    # ---- two support ICs --------------------------------------------------
    bkit.rounded_box("BoardFlash", 15.0, 13.0, 1.8, r=0.6, segments=2,
                     centre=(18.0, 28.0, 1.6), mat=chip)
    bkit.rounded_box("BoardRegulator", 9.0, 7.0, 1.6, r=0.5, segments=2,
                     centre=(18.0, 8.0, 1.5), mat=chip)

    # ---- 2 x 10 pin header on the real 2.54 mm pitch ---------------------
    shroud = bkit.rounded_box("BoardHeader", 10 * PITCH + 1.2, 2 * PITCH + 1.2,
                              8.5, r=0.6, segments=2, centre=(52.0, 30.0, 4.4),
                              mat=plastic)
    pins = []
    for r, y in enumerate((30.0 - PITCH / 2.0, 30.0 + PITCH / 2.0)):
        pin = bkit.box("_h%d" % r, 0.64, 0.64, 9.5,
                       centre=(52.0 - (10 - 1) * PITCH / 2.0, y, 4.7),
                       mat=gold)
        bkit.array_linear(pin, count=10, offset_mm=(PITCH, 0, 0))
        pins.append(pin)
    bkit.join(pins, name="BoardHeaderPins")

    # ---- three electrolytic cans -----------------------------------------
    cans = []
    for i, (x, y) in enumerate(bkit.grid_positions(cols=3, rows=1,
                                                   pitch_x=14.0, pitch_y=0.0)):
        cans.append(bkit.cylinder("_c%d" % i, 5.0, 11.0, segments=32,
                                  centre=(x + 18.0, -26.0, 5.5), mat=can))
    bkit.join(cans, name="BoardCapacitors")

    # ---- 24 SMD passives on a computed lattice ----------------------------
    parts = []
    for i, (x, y) in enumerate(bkit.grid_positions(
            cols=SPEC["smd_parts"] // 4, rows=4, pitch_x=3.2, pitch_y=2.4)):
        parts.append(bkit.box("_s%d" % i, 1.6, 0.8, 0.4,
                              centre=(-58.0 + x, -14.0 + y, 1.6), mat=smd))
    bkit.join(parts, name="BoardSmdParts")

    # ---- USB-C receptacle standing proud of the -X edge ------------------
    bkit.rounded_box("BoardUsb", 13.0, 17.0, 11.0, r=1.0, segments=3,
                     centre=(-L / 2.0 + 5.0, -34.0, 5.5), mat=silver)
    bkit.rounded_box("BoardBarrel", 12.0, 12.0, 9.0, r=1.0, segments=2,
                     centre=(L / 2.0 - 7.0, -34.0, 4.5), mat=plastic)
    bkit.rounded_box("BoardCrystal", 4.8, 3.2, 1.6, r=0.8, segments=3,
                     centre=(18.0, -8.0, 1.5), mat=silver)

    return dict(spec=SPEC, parts=13)


CHECKS = [
    dict(name="length", mm=150.0, tol=0.5, how="bbox_x", part="BoardPcb"),
    dict(name="width", mm=100.0, tol=0.5, how="bbox_y", part="BoardPcb"),
    dict(name="board_thickness", mm=1.6, tol=0.4, how="bbox_z",
         part="BoardPcb"),
]
