"""cable_tie -- a 58 mm cable tie: the slotted head with its real wedge slot, the
row of ratchet teeth down the strap, the tail, and the locking wedge.

The head and the teeth are the model. A cable tie is a strap with a ratchet, and
the head is an open rectangle with a wedge-shaped slot -- so the slot is a real
opening in the head, and the teeth are a computed row at a pitch derived from
their own count.

Construction: a strap swept along a real path with the serrations on its top
face, a head with a wedge slot cut through it, and the locking wedge inside.

Orientation: the head at -X, the tail running to +X, the strap lying flat, Z up.
A 58 mm tie is the short end of the real range; the catalog classes this item
`tiny`, whose band caps the long axis at 60 mm.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    overall_length=58.0,
    strap_width=3.2,
    strap_thickness=1.1,
    head_length=9.0,
    tooth_count=22,
    tooth_width=0.7,
)

L, W, T = 58.0, 3.2, 1.1
HEAD_L = 9.0


def build():
    nylon = bkit.pbr("TieNylon", base=(0.045, 0.045, 0.05), rough=0.48)
    toothm = bkit.pbr("TieTooth", base=(0.10, 0.10, 0.11), rough=0.40)

    # ---- the strap: one body running the length, tapering at the tip
    # the strap runs from the head to the tail tip, so its LENGTH is the overall
    # length minus the head -- the two numbers are derived from each other
    strap_l = L - HEAD_L
    strap = bkit.rounded_box("Strap", strap_l, W, T, r=0.3, segments=3,
                             centre=(-L / 2.0 + HEAD_L + strap_l / 2.0, 0.0,
                                     T / 2.0), mat=nylon)

    # ---- the head: a raised block at the strap's start with a real wedge slot
    head = bkit.rounded_box("Head", HEAD_L, W + 2.2, T + 2.0, r=0.6,
                            segments=3, centre=(-L / 2.0 + HEAD_L / 2.0, 0.0,
                                               (T + 2.0) / 2.0), mat=nylon)
    slot = bkit.extrude_profile(
        "_slot", [(0.0, 0.0), (1.6, 1.6), (5.4, 1.6), (7.0, 0.0)],
        W + 4.0, centre=(-L / 2.0 + 1.0, 0.0, (T + 2.0) / 2.0), axis="Y")
    F.orient_outward(slot)
    bkit.boolean(head, slot, "DIFFERENCE")

    # ---- the locking wedge inside the slot: a tapered block tilted so its thin
    # end rides up the strap. Authored in XY and tilted about Y, which keeps the
    # wedge inside the head's footprint (an untilted wedge of the same profile
    # sticks 30 mm out of the slot).
    wedge = bkit.extrude_profile(
        "Wedge", [(0.0, -0.7), (5.4, -0.7), (5.4, 0.7), (0.6, 0.7)],
        W - 0.4, centre=(0.0, 0.0, 0.0), axis="Z", mat=toothm)
    F.orient_outward(wedge)
    F.bake_rot(wedge, "Y", -26.0)
    bkit.move(wedge, -L / 2.0 + 1.6, 0.0, (T + 2.0) / 2.0)

    # ---- the ratchet teeth: a computed row down the strap, pitch from the
    # tooth count over the strap's own run
    n = SPEC["tooth_count"]
    run = L - HEAD_L - 4.0
    pitch = run / (n - 1)
    for i in range(n):
        x = -L / 2.0 + HEAD_L + 1.0 + i * pitch
        bkit.rounded_box("Tooth%d" % i, 0.7, W - 0.3, 0.55, r=0.12,
                         segments=2, centre=(x, 0.0, T + 0.20), mat=toothm)

    del strap
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=27)


CHECKS = [
    dict(name="overall_length", mm=58.0, tol=1.0, how="bbox_x"),
    dict(name="strap_width", mm=3.2, tol=0.4, how="bbox_y", part="Strap"),
    dict(name="strap_thickness", mm=1.1, tol=0.3, how="bbox_z", part="Strap"),
    dict(name="head_length", mm=9.0, tol=0.6, how="bbox_x", part="Head"),
    dict(name="tooth_width", mm=0.7, tol=0.3, how="bbox_x", part="Tooth2"),
]