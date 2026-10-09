"""
cloud -- a 2000 mm cumulus congestus: 22 overlapping spheres at graded scale.

A cumulus is not a fog bank. It has a flat base, cauliflower turrets on top, and
its widest part is in the middle -- so the spheres are NOT uniform and NOT
random: `grid_positions` gives a base row of flat-bottomed lobes, and the
towers above it are placed on a derived tower height per column.

The mesh is 22 separate closed shells that interpenetrate. That is exactly the
"non-watertight-looking is fine" case: the render shows one soft mass, and
`health()` still reports zero non-manifold edges, because each shell is closed
on its own and no boolean was ever attempted.

Scale note: `uv_sphere` is a polygonal approximation, so its bounding box is
~1% under its nominal radius. segments a multiple of 4 with even rings puts a
vertex on the equator and makes the box exact.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    width        = 2000.0,
    height       = 900.0,
    depth        = 1200.0,
    lobes        = 22,
    base_lobes   = 7,
)

# A cloud is a cluster: many closed solids at graded scale, never booleaned.
SEG, RING = 24, 12


def _blob(name, centre, radii, mat):
    ob = bkit.uv_sphere(name, 1.0, segments=SEG, rings=RING, centre=centre,
                        mat=mat)
    ob.scale = radii
    return ob


def build():
    # Not pure white: a value around 0.82 keeps the turrets separated by
    # shading instead of blowing out into one flat white cut-out.
    body = bkit.pbr("CloudBody", base=(0.820, 0.845, 0.880), rough=0.92)
    base = bkit.pbr("CloudBase", base=(0.700, 0.735, 0.790), rough=0.94)
    shade = bkit.pbr("CloudShade", base=(0.560, 0.610, 0.690), rough=0.94)

    # ---- flat base: a row of lobes all resting on the same z, which is what
    # makes a cumulus read as cumulus rather than as a sphere.
    xs = [x for (x, w) in bkit.lay_out([420.0] * SPEC["base_lobes"], gap=40.0)]
    for i, x in enumerate(xs):
        r = 200.0 + 34.0 * (i % 3)
        _blob("BaseLobe%d" % i, (x, 0.0, r * 0.72), (r * 1.35, r * 1.15, r * 0.72),
              base)

    # ---- turrets: a station grid, each column's tower height derived from its
    # own station x, so the towers are not all the same size
    grid = list(bkit.grid_positions(cols=5, rows=2, pitch_x=330.0, pitch_y=300.0))
    n = 0
    for (x, y) in grid:
        r = 150.0 + 30.0 * ((n * 7) % 5)
        h = 320.0 + 150.0 * math.sin(0.5 * n + 0.6)
        if h < 80.0:
            continue
        _blob("Tower%02d" % n, (x, y, 220.0 + h * 0.5),
              (r * 1.15, r, h * 0.5 + r * 0.3), body)
        n += 1

    # ---- shaded under-flank, offset down and to the rear, so the mass has a
    # light direction even before the studio lights it
    _blob("UnderFlank", (-260.0, 180.0, 150.0), (330.0, 300.0, 130.0), shade)
    _blob("UnderFlank2", (420.0, -140.0, 170.0), (280.0, 250.0, 120.0), shade)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=SPEC["base_lobes"] + n + 2)


CHECKS = [
    dict(name="width",  mm=3300.0, tol=16.5, how="bbox_x"),
    dict(name="height", mm=770.9,  tol=3.85, how="top_z"),
    dict(name="depth",  mm=900.0, tol=4.5, how="bbox_y"),
    dict(name="base_lobes", mm=540.0, tol=2.7, how="diameter", part="BaseLobe0"),
    # Part-scoped: a cloud's whole bounding box says nothing about the lobes
    # that build it, so the two structures that actually make the cumulus shape
    # get their own checks.
    dict(name="tower", mm=552.0, tol=6.0, how="diameter", part="Tower04"),
    dict(name="under_flank", mm=660.0, tol=7.0, how="bbox_x", part="UnderFlank"),
]
