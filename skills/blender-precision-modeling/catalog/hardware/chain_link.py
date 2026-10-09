"""
chain_link -- single welded chain link, 46 x 23 mm, 5 mm wire.

Chain wire is drawn, not forged, so a link is a stadium: two straight sides and
two semicircular ends of equal radius, with the wire thickness adding to the
overall size on both axes. Modelling that path (rather than a torus, which is
always an O-link) is what makes the part read as chain.

bkit has no closed-sweep-along-a-path recipe, so the wire is lofted: a circle of
wire cross-section swept along the computed stadium path, with the ring's first
and last section coincident so the loft closes, then welded at the seam. The
cross-section frame uses the in-plane normal to the path and the vertical, which
are both exactly perpendicular to a planar path -- no twist, no zero-area faces.

Wire diameter is checkable here because the link lies flat: its height *is* the
wire diameter, which no other part in this catalog can claim.
"""
import math
import os
import sys

from mathutils import Vector

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

WIRE_D = 5.0
OUTER_L = 46.0          # overall length
OUTER_W = 23.0          # overall width

ARC_R = (OUTER_W - WIRE_D) / 2.0            # 9.0 centreline end radius
STRAIGHT = OUTER_L - WIRE_D - 2.0 * ARC_R   # 23.0 centreline straight length

SPEC = dict(outer_length=OUTER_L,
            outer_width=OUTER_W,
            wire_diameter=WIRE_D,
            end_radius=ARC_R)


def stadium_path(step=0.9):
    """Centreline of the link, walked by arc length in mm, as (x, y, tangent)."""
    pts = []
    quarter = math.pi * ARC_R / 2.0
    straight_half = STRAIGHT / 2.0
    legs = [
        # (centre_x, from_angle, to_angle) -- right end, top, left end, bottom
        (straight_half, -math.pi / 2, math.pi / 2),
        (-straight_half, math.pi / 2, 3 * math.pi / 2),
    ]
    for cx, a0, a1 in legs:
        # an EVEN step count, so the sample at t = 0.5 lands exactly on the arc
        # apex. With an odd count the apex is straddled by two samples and the
        # overall length comes up ~0.13 mm short of the real one.
        n = 2 * max(1, int(round(quarter / step / 2.0)))
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            x, y = cx + ARC_R * math.cos(a), ARC_R * math.sin(a)
            tx, ty = -math.sin(a), math.cos(a)
            pts.append((x, y, tx, ty))
        # straight run leaving this end, along the tangent (which already
        # points the way travel continues)
        sx, sy, tx, ty = pts[-1]
        n2 = max(2, int(STRAIGHT / step))
        for i in range(1, n2 + 1):
            f = i / float(n2)
            pts.append((sx + tx * STRAIGHT * f, sy + ty * STRAIGHT * f, tx, ty))
    # The duplicated closing point is KEPT: loft() has to bridge the last ring
    # back onto the first for the wire loop to close. weld() then merges the two
    # coincident rings into one seam.
    return pts


def build():
    galv = bkit.pbr("GalvanisedWire", base=(0.72, 0.74, 0.77), metal=0.72,
                    rough=0.34)

    sections = []
    wire_seg = 16
    for (x, y, tx, ty) in stadium_path():
        e1 = Vector((ty, -tx, 0.0))          # in-plane normal to the path
        e2 = Vector((0.0, 0.0, 1.0))         # the link lies flat
        centre = Vector((x, y, 0.0))
        ring = []
        for i in range(wire_seg):
            a = 2.0 * math.pi * i / wire_seg
            p = centre + e1 * (WIRE_D / 2.0 * math.cos(a)) \
                + e2 * (WIRE_D / 2.0 * math.sin(a))
            ring.append((p.x, p.y, p.z))
        sections.append(ring)

    link = bkit.loft("ChainLink", sections, closed_loop=True, cap_start=False,
                     cap_end=False, mat=galv, smooth=True)
    bkit.weld(link)
    bkit.recalc(link)
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="outer_length", mm=46.0, tol=0.05, how="bbox_x", part="ChainLink"),
    dict(name="outer_width", mm=23.0, tol=0.05, how="bbox_y", part="ChainLink"),
    dict(name="wire_diameter", mm=5.0, tol=0.05, how="bbox_z", part="ChainLink"),
]