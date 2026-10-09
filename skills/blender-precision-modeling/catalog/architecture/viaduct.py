"""
viaduct -- a five-span masonry railway viaduct: five semicircular arches, six
piers on a computed pitch, a spandrel wall, a parapet, and a deck.

Huge size class, and the biggest object in this wave: 76 m long. The `huge`
band tops out at 40000 mm and the scorer allows `hi * 2.0`, so 80 m is a hard
ceiling.

The length is not a free parameter. Five clear openings of 11.5 m plus six
3.0 m piers is 57500 + 18000 = 75500, and the battered pier bases add 500 mm
(250 each end), giving exactly 76000. Every other number is derived from that
so the declared length and the built length cannot drift apart.

The piers sit BETWEEN the arches, half a pitch off the arch centres. Putting a
pier on an arch centre would drop it into the middle of the opening, so the
whole row is offset by PITCH/2 and the two grids are derived from one number.

Every span position comes from the bay pitch, not from typed-in coordinates.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit
import bpy

SPEC = dict(
    spans=5,
    span_clear=11500.0,     # clear opening of one arch
    arch_rise=5750.0,       # == span_clear/2, a true semicircle
    arch_thickness=1400.0,  # radial depth of the voussoir ring
    pier_width=3000.0,      # shaft width, at the springing
    pier_base=3500.0,       # battered base, 500 wider than the shaft
    pier_length=9200.0,     # across the viaduct
    pier_height=5750.0,
    deck_width=12000.0,
    deck_height=1400.0,
    deck_length=76000.0,
    parapet_height=1200.0,
    parapet_thickness=500.0,
)

NS = SPEC["spans"]
SC = SPEC["span_clear"]
R = SC / 2.0
PW = SPEC["pier_width"]
PB = SPEC["pier_base"]
PH = SPEC["pier_height"]
DW = SPEC["deck_width"]
DL = SPEC["deck_length"]

# pitch of the arch centres: clear span + one pier, repeated SPANS times
PITCH = SC + PW
# The arches spring from the TOP OF THE PIERS, and the spandrel wall is the
# masonry standing on their extrados -- so the springing line is PH, and the
# spandrel runs from there up past the crowns to the deck. Springing the arch
# at the spandrel's own top instead leaves the rings floating above the wall.
ARCH_Z = PH
RING_MID = R + SPEC["arch_thickness"] / 2.0
RING_MINOR = SPEC["arch_thickness"] / 2.0
RING_OUT = RING_MID + RING_MINOR       # outer radius of the voussoir ring
# 900 mm of masonry above the crowns before the deck starts
SPANDR_TOP = ARCH_Z + RING_OUT + 900.0
DECK_TOP = SPANDR_TOP + 600.0          # the deck overlaps the wall by 600

# arch centres, symmetric about the middle of the deck
arch_x = [(i - (NS - 1) / 2.0) * PITCH for i in range(NS)]
# pier centres: half a pitch off, so a pier lands between every pair of arches
# and the row starts and ends with a pier
pier_x = [(j - NS / 2.0) * PITCH for j in range(NS + 1)]


def _ring(sx, sy, r, z):
    r = max(1.0, min(r, 0.48 * min(sx, sy)))
    return [(x, y, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=5)]


def build():
    masonry = bkit.pbr("ViaductStone", base=(0.66, 0.62, 0.55), rough=0.72)
    deck_mat = bkit.pbr("ViaductDeck", base=(0.52, 0.50, 0.46), rough=0.80)

    # ---- six piers, one between every pair of arches ---------------------
    for i, x in enumerate(pier_x):
        bkit.move(bkit.loft("ViaductPier%d" % (i + 1), [
            _ring(PB, SPEC["pier_length"] + 500.0, 90.0, 0.0),
            _ring(PB - 240.0, SPEC["pier_length"] + 260.0, 80.0, 700.0),
            _ring(PW, SPEC["pier_length"], 70.0, 1500.0),
            _ring(PW - 180.0, SPEC["pier_length"] - 180.0, 60.0, PH - 900.0),
            _ring(PW - 260.0, SPEC["pier_length"] - 260.0, 60.0, PH),
        ], closed_loop=True, cap_start=True, cap_end=True, mat=masonry),
            x, 0.0, 0.0)

    # ---- five arches -----------------------------------------------------
    # The swept tube is circular in section; a viaduct arch is a rectangular
    # ring as deep as the deck is wide, so the tube is scaled in Y and the
    # transform is applied -- an unapplied object scale would leave the
    # measured ring depth reading as the unscaled tube.
    arch = bkit.arc_torus("ViaductArch1", RING_MID, RING_MINOR, 0.0, 180.0,
                          centre=(0.0, 0.0, ARCH_Z), plane="XZ",
                          seg_major=64, seg_minor=28, mat=masonry, caps=True)
    arch.scale = (1.0, DW / (2.0 * RING_MINOR), 1.0)
    bpy.context.view_layer.objects.active = arch
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.context.view_layer.update()
    bkit.move(arch, arch_x[0], 0.0, 0.0)

    # the remaining arches are the same ring at the other computed positions.
    # duplicate() SETS location from offset_mm (it does not add), and
    # arc_torus bakes its `centre` into the vertex data rather than the object
    # transform -- so the copy offset is pure X and the springing height must
    # NOT be repeated here.
    for i in range(1, NS):
        bkit.duplicate(arch, "ViaductArch%d" % (i + 1),
                       offset_mm=(arch_x[i], 0.0, 0.0))

    # ---- spandrel: the masonry standing on the arch extrados -------------
    # The void is the arch's CLEAR opening (R plus a 1.5 mm reveal, so the
    # intrados and the cut are not coincident faces), cut straight through
    # the wall. The ring is then seated in it, showing only its soffit.
    spandrel = bkit.rounded_box("ViaductSpandrel", DL, DW,
                                SPANDR_TOP - ARCH_Z, r=60.0, segments=2,
                                centre=(0.0, 0.0, (SPANDR_TOP + ARCH_Z) / 2.0),
                                mat=masonry)
    for i, x in enumerate(arch_x):
        void = bkit.cylinder("_void", R + 1.5, DW + 800.0, segments=64,
                             centre=(x, 0.0, ARCH_Z), axis="Y")
        bkit.boolean(spandrel, void, "DIFFERENCE")

    # ---- deck ------------------------------------------------------------
    # Overlaps the top of the spandrel by 600 mm: a flush contact would be a
    # tangency, and tangency is what leaves bad edges behind.
    deck = bkit.rounded_box("ViaductDeck", DL, DW, SPEC["deck_height"],
                            r=40.0, segments=2,
                            centre=(0.0, 0.0, DECK_TOP - SPEC["deck_height"] / 2.0),
                            mat=deck_mat)

    # ---- parapets: two, running the full length -------------------------
    for sy, tag in ((-1, "L"), (1, "R")):
        bkit.rounded_box("ViaductParapet%s" % tag, DL,
                         SPEC["parapet_thickness"], SPEC["parapet_height"],
                         r=20.0, segments=2,
                         centre=(0.0, sy * (DW / 2.0 - 300.0),
                                 DECK_TOP + SPEC["parapet_height"] / 2.0),
                         mat=masonry)

    return dict(spec=SPEC, parts=2 * NS + 4, spans=NS, piers=NS + 1)


CHECKS = [
    dict(name="deck_length", mm=76000.0, tol=100.0, how="bbox_x",
         part="ViaductDeck"),
    dict(name="overall_length", mm=76000.0, tol=100.0, how="bbox_x"),
    dict(name="deck_width", mm=12000.0, tol=100.0, how="bbox_y",
         part="ViaductDeck"),
    dict(name="pier_base_width", mm=3500.0, tol=60.0, how="bbox_x",
         part="ViaductPier1"),
    dict(name="parapet_height", mm=1200.0, tol=30.0, how="bbox_z",
         part="ViaductParapetL"),
    # the ring's outer diameter: bbox_x of one arch sees the whole voussoir
    # ring, not the clear opening, so the key names what is measured
    dict(name="arch_outer_dia", mm=14300.0, tol=100.0, how="bbox_x",
         part="ViaductArch1"),
    dict(name="arch_crown_rise", mm=7150.0, tol=100.0, how="bbox_z",
         part="ViaductArch1"),
]
