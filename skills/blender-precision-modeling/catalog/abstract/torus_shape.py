"""
torus_shape -- a copper ring, 108 mm outside diameter, 28 mm section.

The catalog's only pure torus: `bmesh.ops.create_torus` does not exist in the
4.x namespace, so `bkit.torus` builds the two parametric loops explicitly.
That matters here because a naive torus silently leaves a seam that reads as a
bright hairline crack straight around the ring in the hero shot.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    outer_diameter=108.0,  # major + minor, the number a caliper gives
    minor_diameter=28.0,   # section diameter
    major_radius=40.0,
    minor_radius=14.0,
)

CHECKS = [
    dict(name="outer_diameter", mm=108.0, tol=0.1, how="diameter", part="Torus"),
    dict(name="section_diameter", mm=28.0, tol=0.1, how="bbox_z", part="Torus"),
]


def build():
    ring = bkit.torus("Torus", SPEC["major_radius"], SPEC["minor_radius"],
                      seg_major=192, seg_minor=48,
                      mat=bkit.pbr("TorusCopper", base=(0.90, 0.50, 0.32),
                                   metal=0.30, rough=0.26))
    # Both loops close on themselves (i -> i+1 mod n), so the ring is one closed
    # manifold shell with no boundary: recalc() inside torus() has already
    # oriented it outward, which is what keeps calc_volume() positive.
    bkit.recalc(ring)

    return dict(spec=SPEC, parts=1)