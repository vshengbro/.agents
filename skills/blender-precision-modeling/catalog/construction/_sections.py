"""
Shared structural helpers for the construction domain.

Three decisions live here so all 18 items agree on them:

  1. SECTION OUTLINES. An I-beam, a channel and a hollow section are the same
     thing: a closed 2D outline extruded along one axis. Getting the web and
     flange proportions right is the whole read, so the outlines are computed
     from the real dimensions (depth, width, web, flange) rather than typed in
     as a list of points.
  2. MEMBERS BETWEEN POINTS. Joists, rafters, scaffold braces and stair
     stringers are all "a rectangular bar from A to B". bkit's primitives are
     axis-aligned, so every one of them needs the same rotation glue.
  3. UNITS. Millimetres, like every other model script.

Authored profile coordinates are (x = depth direction, y = width direction) and
the polygons are wound counter-clockwise, so `extrude_profile(..., axis="X")`
puts the section's depth along Z and its width along Y.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit
import bpy
from mathutils import Vector


# --------------------------------------------------------------------------
# section outlines
# --------------------------------------------------------------------------

def i_section(depth, width, web, flange, fillet=0.0):
    """Universal-beam / I-section outline, counter-clockwise.

    (depth, width) are the overall section; `web` and `flange` are the plate
    thicknesses. An optional root fillet rounds the four web-to-flange corners
    with a few points each -- it is the difference between a section that reads
    as rolled steel and one that reads as three rectangles glued together.
    """
    hx, hy, hw = depth / 2.0, width / 2.0, web / 2.0
    if fillet > 0.0:
        f = min(fillet, 0.45 * min(web, flange),
                0.45 * (depth / 2.0 - flange))
        # Chamfered web roots: two points per corner instead of a sharp step,
        # which is what makes the outline read as rolled steel rather than as
        # three rectangles glued together. `hy` bounds the width and `hx` the
        # depth -- mixing the two is what silently skews the flange width.
        return [
            (-hx, -hy), (hx, -hy), (hx, -hy + flange),
            (hw + f, -hy + flange), (hw, -hy + flange + f),
            (hw, hy - flange - f), (hw + f, hy - flange),
            (hx, hy - flange), (hx, hy), (-hx, hy),
            (-hx, hy - flange), (-hw - f, hy - flange),
            (-hw, hy - flange - f), (-hw, -hy + flange + f),
            (-hw - f, -hy + flange), (-hx, -hy + flange),
        ]
    return [
        (-hx, -hy), (hx, -hy), (hx, -hy + flange), (hw, -hy + flange),
        (hw, hy - flange), (hx, hy - flange), (hx, hy), (-hx, hy),
        (-hx, hy - flange), (-hw, hy - flange), (-hw, -hy + flange),
        (-hx, -hy + flange),
    ]


def channel_section(depth, width, web, flange):
    """Parallel-flange channel (PFC) outline, web on the -y side.

    Every y bound comes from `hy` (the flange WIDTH half) and every x bound from
    `hx` (the DEPTH half). Deriving a y coordinate from `hx` is the one mistake
    that makes a channel measure 127 mm wide instead of 75 mm and still look
    plausible in a render.
    """
    hx, hy, hw = depth / 2.0, width / 2.0, web / 2.0
    return [
        (-hx, -hy), (hx, -hy), (hx, -hy + flange), (-hw, -hy + flange),
        (-hw, hy - flange), (hx, hy - flange), (hx, hy), (-hx, hy),
    ]


def angle_section(leg_a, leg_b, thick):
    """Equal-leg or unequal-leg L-angle, outline counter-clockwise."""
    a, b, t = leg_a / 2.0, leg_b / 2.0, thick
    return [
        (-a, -b), (a, -b), (a, -b + t), (-a + t, -b + t),
        (-a + t, b), (-a, b),
    ]


def rhs_section(depth, width, thick):
    """Rectangular hollow section outline (outer ring minus inner ring is not
    expressible as one polygon, so this is the solid block; the hollow is made
    with a bore when the model actually needs one)."""
    hx, hy = depth / 2.0, width / 2.0
    return [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]


def tube_between(name, p0, p1, r, mat=None, seg=16, r2=None):
    """A round tube from point p0 to point p1 (mm), in any direction."""
    a, b = Vector(p0), Vector(p1)
    d = b - a
    ob = bkit.cylinder(name, r, d.length, segments=seg, mat=mat, r2=r2)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (a + b)))
    bpy.context.view_layer.update()
    return ob


def bar_between(name, p0, p1, w, h, mat=None, r=1.5, segments=2):
    """A rectangular member from p0 to p1, `w` across and `h` deep.

    `rounded_box` bakes its centre into the mesh data and leaves the object at
    the origin, so rotating the object and then setting `location` to the member
    midpoint is correct -- the rotation happens about the member's own centre.
    """
    a, b = Vector(p0), Vector(p1)
    d = b - a
    ob = bkit.rounded_box(name, w, h, d.length, r=r, segments=segments,
                          mat=mat)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (a + b)))
    bpy.context.view_layer.update()
    return ob


def plate_line(name, p0, p1, width, thick, mat=None, r=1.5):
    """A flat plate lying in the XY plane from p0 to p1 -- a gusset, a stiffener
    or a base plate seen edge-on."""
    a, b = Vector(p0), Vector(p1)
    d = b - a
    ob = bkit.rounded_box(name, d.length, width, thick, r=r, segments=2, mat=mat)
    ob.rotation_euler = (0.0, 0.0, math.atan2(d.y, d.x))
    ob.location = bkit.v((a.x + b.x) / 2.0, (a.y + b.y) / 2.0,
                         (a.z + b.z) / 2.0)
    bpy.context.view_layer.update()
    return ob


def refresh():
    """matrix_world is cached: call this after any raw transform change."""
    bpy.context.view_layer.update()


STRUCT_NOTE = ("Section outlines are generated from (depth, width, web, "
               "flange), never typed as point lists, so a declared section "
               "dimension and the extruded outline cannot disagree.")