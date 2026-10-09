"""
hard_drive -- 3.5" 7200 rpm drive, 147 x 101.6 x 26.1 mm.

A 3.5" drive is the rare consumer object whose case is not a rounded box: the
top cover is a stamped steel shell over a drawn lip, and the lip is a
separate, slightly smaller solid that overlaps the base casting. That overlap
is what makes the cover seam visible instead of a single welded block.

The two repeated features are both arrayed cutters feeding one boolean each --
nine flank vent slots and 22 SATA contacts -- because 31 separate booleans is
31 chances for the EXACT solver to meet a coincident face.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=147.0,
    width=101.6,
    height=26.1,
    cover_thickness=1.4,
    pins=22,
)

L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]
COVER = SPEC["cover_thickness"]


def build():
    cast = bkit.pbr("HddBase", base=(0.38, 0.39, 0.41), metal=0.85, rough=0.42)
    steel = bkit.preset("brushed_metal")
    label = bkit.pbr("HddLabel", base=(0.82, 0.81, 0.76), rough=0.55)
    dark = bkit.pbr("HddDark", base=(0.12, 0.12, 0.14), rough=0.48)
    gold = bkit.preset("gold")

    # ---- base casting, 24.5 mm of the 26.1 mm total ----------------------
    bkit.rounded_box("HddBase", L, W, 24.5, r=2.5, segments=3,
                     centre=(0, 0, 12.25), mat=cast)

    # ---- drawn lip + stamped cover, both overlapping the casting ---------
    lip = bkit.rounded_box("HddLip", L - 1.2, W - 1.2, 8.0, r=2.0,
                           segments=3, centre=(0, 0, 21.0), mat=cast)
    cover = bkit.rounded_box("HddCover", L, W, COVER, r=2.5, segments=3,
                             centre=(0, 0, 25.4), mat=steel)

    # ---- label bay pressed into the cover, label floating 0.1 mm up ------
    # The cutter is 3 mm tall but the cover is only 1.4: a 5 mm cutter would
    # take the cover off entirely in that footprint and leave a window you can
    # see the dark interior through, instead of a recess. 25.15 puts the floor
    # at 25.65, so 0.95 mm of cover survives under the label.
    bay = bkit.rounded_box("_bay", 104.0, 62.0, 3.0, r=2.0, segments=3,
                           centre=(6.0, 0.0, 25.15))
    bkit.boolean(cover, bay, "DIFFERENCE")
    bkit.rounded_box("HddLabel", 100.0, 58.0, 0.4, r=1.2, segments=2,
                     centre=(6.0, 0.0, 25.9), mat=label)

    # ---- nine flank vent slots through the lip, one arrayed cutter ------
    slot = bkit.rounded_box("_slot", 2.6, 30.0, 5.0, r=1.0, segments=2,
                            centre=(-40.0, W / 2.0 - 0.4, 19.0), mat=dark)
    bkit.array_linear(slot, count=9, offset_mm=(7.0, 0, 0))
    bkit.boolean(lip, slot, "DIFFERENCE")

    # ---- SATA header block standing proud of the +X end -----------------
    bkit.rounded_box("HddConnector", 22.0, 14.0, 8.0, r=0.8, segments=2,
                     centre=(L / 2.0 - 6.0, 34.0, 8.0), mat=dark)
    rows = []
    for i, y in enumerate((30.0, 38.0)):
        pin = bkit.box("_pin%d" % i, 0.8, 1.2, 0.8,
                       centre=(L / 2.0 - 6.0, y, 12.4), mat=gold)
        bkit.array_linear(pin, count=SPEC["pins"] // 2, offset_mm=(1.0, 0, 0))
        rows.append(pin)
    bkit.join(rows, name="HddPins")

    # ---- six cover screws on a computed 2 x 3 grid -----------------------
    screws = []
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=3,
                                                   pitch_x=124.0, pitch_y=42.0)):
        screws.append(bkit.cylinder("_s%d" % i, 3.0, 1.2, segments=20,
                                    centre=(x, y, 26.0), mat=steel))
    bkit.join(screws, name="HddScrews")

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="length", mm=147.0, tol=0.6, how="bbox_x", part="HddBase"),
    dict(name="width", mm=101.6, tol=0.6, how="bbox_y", part="HddBase"),
    dict(name="height", mm=26.1, tol=0.6, how="bbox_z"),
]
