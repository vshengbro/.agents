"""
obsidian_shard -- a conchoidal fracture fragment of volcanic glass.

Real object: a 26 mm shard from an obsidian flow, near-black with a
greasy vitreous lustre and conchoidal ripple marks. Two things sell it: the
fracture surfaces are curved (conchoidal) rather than flat, and the edges are
feathered thin, not cut.

Modelled as a `loft` through four elliptical rings of decreasing size, tilted
and slightly rotated against each other -- that gives curved, non-parallel
fracture faces for free, where six flat facets would read as a rock. The
lump of parent glass it broke from is a separate overlapping shell.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=26.0,
    width=17.0,
    thickness=6.5,       # feathered edge, as a fracture leaves it
    parent_block=34.0,
)

L = SPEC["length"]
W = SPEC["width"]
T = SPEC["thickness"]


def build():
    glass = bkit.pbr("Obsidian", base=(0.030, 0.030, 0.036), rough=0.055,
                     ior=1.49, coat=0.6)
    conchoidal = bkit.pbr("ObsidianConchoidal", base=(0.055, 0.052, 0.060),
                          rough=0.10, ior=1.49, coat=0.35)

    # ---- the shard: four curved rings, each tilted a little differently ---
    # Ring offsets are cumulative, so each band is a distinct conchoidal
    # surface and no two adjacent faces are parallel.
    rings = [
        (W * 0.86, T * 0.30, 0.0, 0.0, 0.0),
        (W, T, -1.4, 0.9, 8.0),
        (W * 0.72, T * 0.74, -3.6, 2.6, 22.0),
        (W * 0.30, T * 0.34, -6.2, 5.0, 41.0),
    ]
    # z runs 0..L over the rings: dividing by len(rings) instead of
    # len(rings)-1 stops the last ring short of the declared length and
    # measures 19.5 mm on a 26 mm shard.
    secs = []
    for i, (sx, sy, cx, cy, rz) in enumerate(rings):
        ring = bkit.superellipse_section(sx, sy, n=2.3, steps=32)
        a = math.radians(rz)
        secs.append([(cx + x * math.cos(a) - y * math.sin(a),
                      cy + x * math.sin(a) + y * math.cos(a),
                      L * i / float(len(rings) - 1)) for (x, y) in ring])
    shard = bkit.loft("ObsidianShard", secs, mat=glass, smooth=True)
    bkit.recalc(shard)

    # Ripple marks on the big fracture face: three thin curved ridges whose
    # long axis follows the conchoidal sweep, not straight lines across it.
    for i in range(3):
        arc = bkit.arc_torus("Ripple%d" % (i + 1), 26.0 - 2.0 * i, 0.55,
                             34.0, 96.0, centre=(-4.0 + 2.4 * i, 0.0,
                             5.0 + 4.4 * i), plane="XZ", seg_major=26,
                             seg_minor=8, mat=conchoidal, caps=True)

    # ---- parent block the shard broke from --------------------------------
    # Overlapping shells, not a boolean: the two surfaces are close to
    # parallel over a wide area and the EXACT solver has nothing to gain.
    parent = bkit.extrude_profile(
        "ParentBlock",
        [(SPEC["parent_block"] / 2.0 * math.cos(math.radians(60 * i)) +
          (2.0 if i % 2 else -2.0),
          SPEC["parent_block"] / 2.4 * math.sin(math.radians(60 * i)))
         for i in range(6)],
        9.0, centre=(-19.0, 6.0, 4.5), mat=glass)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="shard_length", mm=26.0, tol=0.5, how="bbox_z", part="ObsidianShard"),
    dict(name="shard_width", mm=17.0, tol=0.6, how="diameter", part="ObsidianShard"),
    dict(name="overall_width", mm=52.0, tol=2.0, how="bbox_x"),
    dict(name="overall_height", mm=9.0, tol=1.0, how="bbox_z", part="ParentBlock"),
]