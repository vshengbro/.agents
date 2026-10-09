"""
frozen_ice_cube -- a single ice cube from a domestic freezer tray: 24 mm
edge, 13.8 g.

Size class `small` (30..150 mm band; the band is a category, not a ruling).

Two details make ice read as ice rather than as glass or frosted acrylic: the
edges are ROUNDED OFF by the tray's meniscus and the freeze line, and the body
is cloudy rather than clear -- commercial ice is full of trapped air and the
opaque centre is what a viewer recognises. So: `rounded_box` with a generous
corner radius, a cloudy high-scatter body, and a slightly clearer melt film
on the faces via `assign_faces_by` rather than a second shell.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    edge=24.0,
    corner_radius=3.2,     # tray meniscus plus the freeze line
    cloudy_centre=True,
    mass_g=13.8,
)

E = SPEC["edge"]
R = SPEC["corner_radius"]


def build():
    ice = bkit.pbr("IceCloudy", base=(0.80, 0.87, 0.92), rough=0.26,
                   transmission=0.52, ior=1.31)
    ice_clear = bkit.pbr("IceClearFace", base=(0.86, 0.92, 0.96), rough=0.07,
                         transmission=0.80, ior=1.31)
    frost = bkit.pbr("IceFrost", base=(0.88, 0.93, 0.97), rough=0.62,
                     transmission=0.20, ior=1.31)

    # ---- the cube ---------------------------------------------------------
    # rounded_box, not box: a sharp-edged cube renders as a glass block, and
    # a tray cube's arrises are always softened by the mould it froze in.
    cube = bkit.rounded_box("IceCube", E, E, E, r=R, segments=5,
                            centre=(0.0, 0.0, E / 2.0), mat=ice)

    # Clearer melt film on the flat faces, cloudy core: face selection on one
    # solid. A second inner shell would z-fight with the outer wall and double
    # the non-manifold count.
    bkit.assign_faces_by(cube, ice_clear,
                         lambda c, n: abs(n.z) > 0.80 or abs(n.x) > 0.80)

    # ---- frost bloom on the upper half ------------------------------------
    # Grows downward from the top face, so the gradient is a z test rather
    # than a random scatter: frost forms where the vapour touches coldest.
    bkit.assign_faces_by(cube, frost,
                         lambda c, n: c.z / bkit.MM > E * 0.62 and n.z > -0.2)

    # ---- two cubes from the tray, so the ice reads as ice ----------------
    # A single isolated cube looks like a calibration weight; the second,
    # half-melted piece is what makes it read as something from a glass.
    second = bkit.rounded_box("IceCubeMelted", E * 0.86, E * 0.9, E * 0.62,
                              r=R * 1.5, segments=5,
                              centre=(E * 0.86, -E * 0.22, E * 0.31), mat=ice)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="edge_x", mm=24.0, tol=0.3, how="bbox_x", part="IceCube"),
    dict(name="edge_y", mm=24.0, tol=0.3, how="bbox_y", part="IceCube"),
    dict(name="edge_z", mm=24.0, tol=0.3, how="bbox_z", part="IceCube"),
    dict(name="overall_width", mm=44.0, tol=1.5, how="bbox_x"),
]