"""
pipe -- a 300 mm length of DN50 steel tube: a real hollow annulus, a raised
weld seam from the mill, and end reinforcement rings.

Medium size class (150..600 mm) and the only plumbing item that is pure
geometry -- no curves, no controls. Getting it right is all about the annulus:
`bkit.tube` builds it directly, and a closed-profile `lathe` is the trap here
(64 non-manifold edges, one per segment, because lathe caps both ends of a
profile that returns to its own first point).

Every part is a `tube`, then `recalc`. An earlier version chamfered the bore
with two lathed cones whose profiles ran in -Z; those came back with negative
signed volume and are gone rather than fudged.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=300.0,
    outer_diameter=60.3,     # DN50 steel tube
    inner_diameter=53.1,
    wall=3.6,
    weld_band_width=18.0,
    weld_band_height=2.4,
    end_ring_width=14.0,
    end_ring_height=3.0,
)

L = SPEC["length"]
RO = SPEC["outer_diameter"] / 2.0
RI = SPEC["inner_diameter"] / 2.0


def build():
    steel = bkit.preset("brushed_metal")
    weld_mat = bkit.pbr("PipeWeld", base=(0.56, 0.57, 0.59), metal=0.85,
                        rough=0.46)

    # ---- the tube: an annulus lying along X -------------------------------
    pipe = bkit.tube("Pipe", RO, RI, L, segments=96, centre=(0.0, 0.0, 0.0),
                     axis="X", mat=steel)
    bkit.move(pipe, 0.0, 0.0, RO)
    bkit.recalc(pipe)

    # ---- weld seam: the raised longitudinal joint the mill leaves --------
    band = bkit.tube("PipeWeldBand", RO + SPEC["weld_band_height"], RO - 0.5,
                     SPEC["weld_band_width"], segments=96,
                     centre=(0.0, 0.0, 0.0), axis="X", mat=weld_mat)
    bkit.move(band, 0.0, 0.0, RO)
    bkit.recalc(band)

    # ---- end reinforcement rings, one per end ---------------------------
    for sx, tag in ((-1, "A"), (1, "B")):
        ring = bkit.tube("PipeEndRing%s" % tag,
                         RO + SPEC["end_ring_height"], RO - 0.5,
                         SPEC["end_ring_width"], segments=96,
                         centre=(sx * (L / 2.0 - SPEC["end_ring_width"] / 2.0),
                                 0.0, 0.0), axis="X", mat=weld_mat)
        bkit.move(ring, 0.0, 0.0, RO)
        bkit.recalc(ring)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    # The tube lies along X, so its length is bbox_x and its diameter is
    # bbox_y. There is deliberately NO check on the bore: a bounding box
    # cannot see a hole, so `inner_diameter` would be scored against the
    # OUTER diameter and always fail. The bore is proved by the mesh instead.
    dict(name="length", mm=300.0, tol=0.5, how="bbox_x", part="Pipe"),
    dict(name="outer_diameter", mm=60.3, tol=0.3, how="bbox_y", part="Pipe"),
    dict(name="band_width", mm=18.0, tol=0.4, how="bbox_x", part="PipeWeldBand"),
    dict(name="band_height", mm=65.1, tol=0.4, how="bbox_y", part="PipeWeldBand"),
    dict(name="overall_length", mm=300.0, tol=0.6, how="bbox_x"),
]
