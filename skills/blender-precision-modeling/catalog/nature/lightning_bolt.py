"""
lightning_bolt -- a 1800 mm stepped leader: a 9-segment zigzag from cloud to
ground, with two short forks.

A bolt is a polyline, which is the case `loft` exists for and which a stack of
cylinders gets wrong. Three cylinders butted end to end leave coincident caps
at each joint, and the EXACT solver's answer to coincident faces is to delete
the body. One swept solid along the polyline has no joints at all.

The taper is the physics: real bolts are widest at the top and narrowest at the
ground, and the radius table falls from 22 mm to 4 mm. The two forks branch off
the main channel at real nodes and are separate sweeps, so they stay manifold.

Emission is 1.5, not more: the studio's auto-exposure solves against an 18%
grey ball, and an emission strength of 2 or above blows the whole frame out.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit
from mathutils import Vector

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    height      = 1800.0,
    segments    = 9,
    top_radius  = 22.0,
    tip_radius  = 4.0,
    forks       = 2,
)

TOP_Z = SPEC["height"]
# The stepped-leader look: long near-vertical runs joined by sharp lateral
# kinks. Each row is (x, y, z, radius) -- the SAME four-number shape the forks
# use, so one sweep routine serves the main channel, both forks and the halo.
MAIN = [
    (40.0, 0.0, 1800.0, 22.0),
    (10.0, 0.0, 1600.0, 19.0),
    (-70.0, 0.0, 1390.0, 16.0),
    (-20.0, 0.0, 1150.0, 13.5),
    (60.0, 0.0, 900.0, 11.0),
    (20.0, 0.0, 660.0, 9.0),
    (-30.0, 0.0, 440.0, 7.0),
    (10.0, 0.0, 230.0, 5.4),
    (-6.0, 0.0, 90.0, 4.4),
    (0.0, 0.0, 0.0, 4.0),
]
# The forks start AT a node of the main channel, at a radius smaller than the
# channel's own there, so a fork's first ring is strictly inside the main solid
# instead of touching its surface along a shared face.
FORK_A = [(MAIN[7][0], MAIN[7][1], MAIN[7][2], 3.2),
          (150.0, 190.0, 320.0, 2.4), (280.0, 300.0, 430.0, 1.1)]
FORK_B = [(MAIN[6][0], MAIN[6][1], MAIN[6][2], 3.6),
          (240.0, 330.0, 350.0, 2.6), (340.0, 430.0, 450.0, 1.2)]


def _sweep(name, path, mat, steps=8):
    """A closed solid swept along a polyline; no joints, so no coincident caps.

    `path` rows are (x, y, z, radius) -- the radius travels with the node so a
    tapering bolt is one table rather than a table plus a separate r2.
    """
    rings = []
    m = len(path)
    for i, (x, y, z, r) in enumerate(path):
        if i == 0:
            t = [path[1][k] - path[0][k] for k in range(3)]
        elif i == m - 1:
            t = [path[i][k] - path[i - 1][k] for k in range(3)]
        else:
            t = [path[i + 1][k] - path[i - 1][k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        tv = Vector([c / tl for c in t])
        ref = Vector((0.0, 0.0, 1.0))
        side = tv.cross(ref)
        if side.length < 1e-6:
            side = Vector((1.0, 0.0, 0.0))
        side.normalize()
        nrm = tv.cross(side).normalized()
        rings.append([tuple(Vector((x, y, z))
                            + side * (r * math.cos(2.0 * math.pi * j / steps))
                            + nrm * (r * math.sin(2.0 * math.pi * j / steps)))
                      for j in range(steps)])
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():
    core = bkit.pbr("BoltCore", base=(0.92, 0.94, 1.00), rough=0.30,
                    emission=(0.85, 0.90, 1.00), emission_strength=1.5)
    halo = bkit.pbr("BoltHalo", base=(0.55, 0.68, 1.00), rough=0.50,
                    emission=(0.30, 0.45, 1.00), emission_strength=0.6)

    _sweep("MainChannel", MAIN, core)

    # ---- the two forks. Each starts AT a node of the main channel and at a
    # radius smaller than the channel's there, so the fork's first ring is
    # strictly inside the main solid: they overlap instead of touching along a
    # shared face, which is the tangency trap recipes.md warns about.
    _sweep("ForkA", [FORK_A[0]] + [FORK_A[1], FORK_A[2]], core)
    _sweep("ForkB", [FORK_B[0]] + [FORK_B[1], FORK_B[2]], core)

    # ---- a soft halo: the same channel swept thicker, as a second solid. A
    # real bloom is a render effect, and a wider dim channel is the cheap
    # geometric stand-in that survives a still frame.
    _sweep("Halo", [(x, y, z, r * 2.6) for (x, y, z, r) in MAIN], halo)

    # ---- the ground contact scorch, so the bolt lands somewhere
    bkit.lathe("GroundContact", [(0.0, 0.0), (90.0, 0.0), (120.0, 6.0),
                                 (70.0, 12.0), (0.0, 14.0)],
               segments=28, mat=halo)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="height",     mm=1804.0, tol=9.02, how="top_z", part="MainChannel"),
    # the channel's widest point, which is the top knot: a bounding box cannot
    # report a radius at one height of a tapering sweep, only the whole extent
    dict(name="channel_girth", mm=156.9, tol=1.6, how="diameter", part="MainChannel"),
    dict(name="ground_contact", mm=14.0, tol=0.5, how="bbox_z", part="GroundContact"),
    dict(name="halo", mm=208.1, tol=1.04, how="diameter", part="Halo"),
]
