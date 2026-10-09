"""
wallet -- 110 x 92 x 16 mm bifold wallet, 3 card slots, saddle-stitched edge.

A bifold is a folded shell, so the fold is the feature that has to be modelled
rather than painted: the body carries three card slots cut into its top edge
from a measured pitch, and the spine down one long side is a separate piece of
the same leather that stands slightly proud. The two are separate solids that
overlap by 2 mm -- a single object with a cove cut into it would be watertight
but would not show a spine.

Slots are cut with plain cylinders/boxes rather than bkit.bore() because the
host is a box, not a revolved surface: bore()'s +7 segment trick exists to
avoid coincident facets on a coaxial host, and there is no coaxial host here.
Positions come from bkit.lay_out() so the three slots cannot collide.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

W, D, H = 110.0, 92.0, 16.0        # width (X), depth (Y), thickness (Z)
CORNER_R = 7.0
SLOT_N = 3
SLOT_PITCH = 26.0
SLOT_W = 20.0
SLOT_D = 3.4                        # how deep each slot is cut
SPINE_W = 11.0
STITCH_PITCH = 5.0

SPEC = dict(width=W, depth=D, thickness=H,
            corner_radius=CORNER_R,
            slot_count=SLOT_N,
            slot_pitch=SLOT_PITCH,
            slot_depth=SLOT_D,
            spine_width=SPINE_W)


def build():
    leather = bkit.pbr("WalletLeather", base=(0.19, 0.11, 0.07), metal=0.0, rough=0.55)
    lining = bkit.pbr("WalletLining", base=(0.11, 0.07, 0.05), metal=0.0, rough=0.70)
    thread = bkit.pbr("WalletThread", base=(0.72, 0.58, 0.30), metal=0.0, rough=0.65)

    # ---- body ---------------------------------------------------------------
    body = bkit.rounded_box("Body", W, D, H, r=CORNER_R, segments=5,
                            centre=(0.0, 0.0, H / 2.0), mat=leather)

    # ---- three card slots in the top edge, on a measured pitch -------------
    # lay_out centres the run on the wallet's own centre line.
    for (x, w) in bkit.lay_out([SLOT_W] * SLOT_N, gap=SLOT_PITCH - SLOT_W):
        cutter = bkit.rounded_box("_slot", w, D - 2.0 * CORNER_R, 2.0 * SLOT_D,
                                  r=1.2, segments=2,
                                  centre=(x, 0.0, H))
        bkit.boolean(body, cutter, "DIFFERENCE")

    # ---- spine: the folded edge, standing 2 mm proud of the body -----------
    spine = bkit.rounded_box("Spine", SPINE_W, D, H + 2.4, r=3.0, segments=4,
                             centre=(-W / 2.0 + SPINE_W / 2.0 - 1.0, 0.0,
                                     (H + 2.4) / 2.0 - 1.2),
                             mat=lining)

    # ---- saddle stitching: a run of stitches along the front edge ----------
    # The count comes from the usable edge length divided by the pitch, and the
    # run is centred on that edge, so the first stitch lands at
    # -(n-1)*pitch/2 and the last at +(n-1)*pitch/2.
    n_stitch = int((D - 2.0 * CORNER_R) / STITCH_PITCH)
    y0 = -(n_stitch - 1) * STITCH_PITCH / 2.0
    stitch = bkit.rounded_box("Stitch", 1.0, 2.6, 0.8, r=0.35, segments=2,
                              centre=(W / 2.0 - 2.6, y0, H - 0.3), mat=thread)
    bkit.array_linear(stitch, n_stitch, (0.0, STITCH_PITCH, 0.0), world=True)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="width", mm=110.0, tol=0.1, how="bbox_x", part="Body"),
    dict(name="depth", mm=92.0, tol=0.1, how="bbox_y", part="Body"),
    dict(name="thickness", mm=16.0, tol=0.1, how="bbox_z", part="Body"),
    dict(name="spine_height", mm=18.4, tol=0.1, how="bbox_z", part="Spine"),
    dict(name="stitch_run", mm=72.6, tol=0.2, how="bbox_y", part="Stitch")
]