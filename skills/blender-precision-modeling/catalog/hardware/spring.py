"""
spring -- helical compression spring, 30 mm OD, 2.5 mm wire, 95 mm long.

Real wire springs have three numbers that fix the whole layout: outside
diameter, wire diameter and pitch (wire dia x 8 is the usual rule for a
working compression spring). Those give D/d = 12 and a pitch of 7.5 mm against
a 2.5 mm wire, so the coils never touch -- the gaps are what make it read as a
spring instead of a smooth tube.

bkit has no helix recipe, and arc_torus cannot be bent into one (it sweeps a
plane, so extra turns would retrace the same circle and self-overlap). The coil
is therefore built as a loft: a circle of wire cross-section swept along a
computed helical path, with the cross-section frame carried on a radial basis
vector so the wire stays square to the wire centreline all the way round.
"""
import math
import os
import sys

from mathutils import Vector

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

OUTSIDE_D = 30.0        # D, coil outside diameter
WIRE_D = 2.5            # d, wire diameter
TURNS = 12              # total coils
COIL_LEN = 90.0         # length occupied by the coiled section
LEAD_IN = 2.5           # plain ground lead at each end

SPEC = dict(outside_diameter=OUTSIDE_D,
            wire_diameter=WIRE_D,
            coils=TURNS,
            coil_length=COIL_LEN,
            lead_in=LEAD_IN,
            free_length=COIL_LEN + 2.0 * LEAD_IN)


def coil_sections(coil_len, radius, wire_r, turns, per_turn=24, wire_seg=16,
                  lead_in=LEAD_IN, lead_seg=3):
    """Circular cross-sections along lead-in + helix + lead-in, in mm.

    e1 is the radial basis vector, which is exactly perpendicular to the helix
    tangent, so the wire cross-section never twists around its own axis.
    """
    sections = []
    half = coil_len / 2.0

    def ring(centre, tangent, radial):
        e1 = Vector(radial).normalized()
        e2 = Vector(tangent).cross(e1).normalized()
        pts = []
        for i in range(wire_seg):
            a = 2.0 * math.pi * i / wire_seg
            p = Vector(centre) + e1 * (wire_r * math.cos(a)) \
                + e2 * (wire_r * math.sin(a))
            pts.append((p.x, p.y, p.z))
        return pts

    # straight, ground lead-in at -X (tangent exactly +X, so the end ring is
    # square to the axis and the bbox length is the true free length)
    for i in range(lead_seg):
        t = i / float(lead_seg)
        x = -half - lead_in * (1.0 - t)
        sections.append(ring((x, radius, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))

    steps = turns * per_turn
    dtheta = 2.0 * math.pi * turns
    for i in range(steps + 1):
        s = i / float(steps)
        theta = dtheta * s
        centre = (-half + coil_len * s, radius * math.cos(theta),
                  radius * math.sin(theta))
        tangent = (coil_len, -radius * math.sin(theta) * dtheta,
                   radius * math.cos(theta) * dtheta)
        sections.append(ring(centre, tangent, (0.0, math.cos(theta),
                                               math.sin(theta))))

    for i in range(1, lead_seg + 1):
        t = i / float(lead_seg)
        x = half + lead_in * t
        sections.append(ring((x, radius, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    return sections


def build():
    steel = bkit.pbr("SpringSteel", base=(0.58, 0.60, 0.63), metal=0.74,
                     rough=0.27)

    sections = coil_sections(COIL_LEN, (OUTSIDE_D - WIRE_D) / 2.0,
                             WIRE_D / 2.0, TURNS)
    coil = bkit.loft("CoilSpring", sections, closed_loop=True,
                     cap_start=True, cap_end=True, mat=steel, smooth=True)
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="free_length", mm=95.0, tol=0.10, how="bbox_x", part="CoilSpring"),
    dict(name="outside_diameter", mm=30.0, tol=0.10, how="bbox_y", part="CoilSpring"),
    dict(name="outside_diameter_z", mm=30.0, tol=0.10, how="bbox_z", part="CoilSpring"),
]