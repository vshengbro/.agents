"""
hammer -- 16 oz claw hammer, 280 mm overall.

One handle lofted from oval sections (a lathe would make it round; a hammer
handle is flattened across the grip) plus a forged steel head. The claw is TWO
separate prongs separated in Y, which is how a real one is made -- a single
concave outline only reads as a solid paddle from the front.

Orientation: handle down at z=0, head across the top. sit_on_floor then rests
the model on the hammer butt, which is stable and shows the full length.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

HANDLE_TOP = 262.0          # where the handle enters the head
HEAD_Z = 258.0              # head centre height
HEAD_THICK = 26.0           # head thickness across the strike face

SPEC = dict(
    overall_length=280.0,
    handle_length=HANDLE_TOP,
    handle_grip_width=33.0,
    head_length=70.0,       # poll to face
    head_height=44.0,
    head_width=HEAD_THICK,
)


def _z(pts, dz=HEAD_Z):
    """Lift a head-outline point list (x, z-offset) into world Z."""
    return [(x, z + dz) for (x, z) in pts]


def build():
    wood = bkit.preset("wood")
    steel = bkit.pbr("HammerSteel", base=(0.64, 0.66, 0.70), metal=0.30,
                     rough=0.32)

    # ---- handle: oval sections, waisted at the grip, flaring into the eye ---
    grip = ((0.0, 30.0), (14.0, 26.0), (60.0, 24.0), (140.0, 25.5),
            (215.0, 28.0), (250.0, 31.0), (HANDLE_TOP, 33.0))
    sections = [[(x, y, z) for (x, y) in
                 bkit.superellipse_section(sx, sx * 0.72, n=2.6, steps=48)]
                for (z, sx) in grip]
    handle = bkit.loft("HammerHandle", sections, mat=wood)
    bkit.recalc(handle)

    # ---- head: forged block from the poll out to the striking face ---------
    head_poly = _z([(60, 14), (48, 18), (14, 22), (-4, 18), (-10, 15),
                    (-10, -16), (-4, -18), (14, -22), (48, -17), (60, -13)])
    head = bkit.extrude_profile("HammerHead", head_poly, HEAD_THICK,
                                axis="Y", mat=steel)
    bkit.recalc(head)
    bkit.bevel(head, width_mm=1.4, segments=2, angle_deg=35)

    # ---- claw: two curved prongs with a real slot between them -------------
    prong_poly = _z([(-6, 15), (-28, 13), (-48, 8), (-60, 1), (-63, -3),
                     (-50, -5), (-32, -10), (-14, -14), (-6, -16)])
    prongs = []
    for i, y in enumerate((-6.5, 6.5)):
        p = bkit.extrude_profile("HammerClawProng%d" % (i + 1), prong_poly,
                                 5.0, centre=(0, y, 0), axis="Y", mat=steel)
        bkit.recalc(p)
        bkit.bevel(p, width_mm=0.7, segments=2, angle_deg=35)
        prongs.append(p)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="head_length", mm=70.0, tol=0.5, how="bbox_x", part="HammerHead"),
    dict(name="head_height", mm=44.0, tol=0.5, how="bbox_z", part="HammerHead"),
    dict(name="handle_length", mm=262.0, tol=1.0, how="bbox_z",
         part="HammerHandle"),
    dict(name="overall_length", mm=280.0, tol=1.5, how="bbox_z"),
]