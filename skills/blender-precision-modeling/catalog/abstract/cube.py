"""
cube -- a 60 mm machined aluminium reference cube.

The primitive is `box`; the modelled object is the *chamfered* block a real
milling operation leaves behind. A raw `box` render reads as a modelling
placeholder, while a 2 mm broken edge catches the key light on all twelve
edges and reads instantly as a manufactured solid.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    edge=60.0,            # nominal cube edge, as milled
    chamfer=2.0,          # edge break on all twelve edges
    face_flatness=0.02,   # how flat the six milled faces are meant to be
)

CHECKS = [
    dict(name="edge_x", mm=60.0, tol=0.15, how="bbox_x", part="Cube"),
    dict(name="edge_y", mm=60.0, tol=0.15, how="bbox_y", part="Cube"),
    dict(name="edge_z", mm=60.0, tol=0.15, how="bbox_z", part="Cube"),
]


def build():
    mat = bkit.pbr("CubeAlu", base=(0.74, 0.75, 0.77), metal=0.25, rough=0.30)

    edge = SPEC["edge"]
    cube = bkit.box("Cube", edge, edge, edge, centre=(0, 0, edge / 2.0), mat=mat)

    # ANGLE-limited bevel: only the 90 deg cube edges break, the flat faces stay
    # planar. A chamfer never shrinks the bounding box, so the 60 mm CHECKS
    # above stay true after the modifier is baked in.
    bkit.bevel(cube, width_mm=SPEC["chamfer"], segments=3, angle_deg=30)
    # Auto-smooth at 30 deg keeps the chamfer facets smooth with each other
    # while every face/chamfer transition stays a crisp highlight line.
    bkit.shade_smooth(cube, 30)

    return dict(spec=SPEC, parts=1)