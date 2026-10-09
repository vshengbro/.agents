"""
Shared construction for the power_tools domain.

A power tool is the hand-tool language with more torque, so every model here is
the same five things in a different order:

  1. a SHELL -- a rounded plastic housing, never a box (`rounded_box`),
  2. a METAL HEAD -- the gearbox/cast-aluminium end that carries the tool,
  3. a CORD or a BATTERY -- the power source, and it is the thing that sets
     the tool's silhouette against a bare tool head,
  4. VENTS -- a real perforated panel, computed with `perforated_panel`,
  5. a GRIP and a TRIGGER -- generated with `grip()`, a loft, so the handle
     can be raked without hand-authoring rings.

The helper functions here exist so all 14 items agree on those five, and so a
dimension is measured on the part that owns it.

Units are millimetres everywhere, exactly as in bkit.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bkit
import bpy
from mathutils import Vector


# --------------------------------------------------------------------------
# transforms
# --------------------------------------------------------------------------

def freeze(ob):
    """Bake location/rotation/scale into the mesh; `duplicate()` SETS location."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.select_set(False)
    return ob


def aim(ob, p0, p1):
    """Point the object's local +Z from p0 to p1 (mm) and move it to p0."""
    d = Vector(p1) - Vector(p0)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*p0)
    bpy.context.view_layer.update()
    return ob


# --------------------------------------------------------------------------
# shells and members
# --------------------------------------------------------------------------

def shell(name, sx, sy, sz, centre=(0, 0, 0), r=None, mat=None, segments=3):
    """A moulded housing: rounded box with the radius derived from its size.

    `r` defaults to a fifth of the smallest axis, which is roughly what a
    injection-moulded tool housing looks like -- the edge break is visible but
    the panel is still flat.
    """
    r = r if r is not None else max(1.5, min(sx, sy, sz) * 0.20)
    return bkit.rounded_box(name, sx, sy, sz, r=r, segments=segments,
                            centre=centre, mat=mat)


def strut(name, p0, p1, w, h, mat=None, r=1.5, segments=2):
    """A rectangular member (a D-handle crosspiece, a fence, a base rail)."""
    d = Vector(p1) - Vector(p0)
    ob = bkit.rounded_box(name, w, h, d.length, r=r, segments=segments,
                          mat=mat or bkit.preset("dark_metal"))
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (Vector(p0) + Vector(p1))))
    bpy.context.view_layer.update()
    return ob


def rod(name, p0, p1, r, mat=None, seg=20, r2=None):
    """A round tube between two points (mm)."""
    d = Vector(p1) - Vector(p0)
    ob = bkit.cylinder(name, r, d.length, segments=seg,
                       mat=mat or bkit.preset("brushed_metal"), r2=r2)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (Vector(p0) + Vector(p1))))
    bpy.context.view_layer.update()
    return ob


# --------------------------------------------------------------------------
# the raked grip
# --------------------------------------------------------------------------

def grip(name, p0, p1, w0, d0, w1, d1, mat=None, bow=0.0, r0=None, r1=None):
    """A handle lofted between two points, tapering along its length.

    `bow` pushes the middle of the handle off the straight line -- that offset
    is what stops a handle reading as a stick. Note that it also inflates the
    handle's bounding box by up to `bow`, so a CHECKS entry that measures a grip
    by `bbox_z` wants the number the bow actually produces, not the p0-p1 span.
    """
    d = Vector(p1) - Vector(p0)
    L = d.length
    n = 6
    rings = []
    for i in range(n + 1):
        t = i / float(n)
        w = w0 + (w1 - w0) * t
        dp = d0 + (d1 - d0) * t
        rr = (r0 if r0 is not None else min(w, dp) * 0.42)
        off = bow * math.sin(math.pi * t)
        ring = bkit.rounded_rect_section(w, dp, min(rr, min(w, dp) * 0.49),
                                         per_corner=4)
        rings.append([(x, y, L * t) for (x, y) in ring])
    ob = bkit.loft(name, rings, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, 34.0)
    aim(ob, p0, p1)
    return ob


def trigger(name, p0, p1, w, h, mat=None):
    """The finger paddle under a handle."""
    return strut(name, p0, p1, w, h, mat=mat, r=2.0)


# --------------------------------------------------------------------------
# vents, packs, cables
# --------------------------------------------------------------------------

def vent_panel(name, cols, rows, pitch_x, pitch_y, hole_r, sx, sy, thick,
               centre=(0, 0, 0), axis="Z", mat=None):
    """A real perforated grille, positioned on a named face."""
    ob = bkit.perforated_panel(name, cols, rows, pitch_x, pitch_y, hole_r,
                               sx, sy, thick, mat=mat or bkit.preset("black_plastic"))
    bkit.place(ob, centre, axis)
    return ob


def battery(name, sx, sy, sz, centre=(0, 0, 0), mat=None, rail_mat=None,
            terminal_mat=None, terminals=True):
    """A slide-on battery pack: case, slide rail, and two contact blocks."""
    mat = mat or bkit.preset("black_plastic")
    rail_mat = rail_mat or bkit.preset("dark_metal")
    terminal_mat = terminal_mat or bkit.preset("copper")
    case = shell(name, sx, sy, sz, centre=centre, r=4.0, mat=mat)
    top = centre[2] + sz / 2.0
    bkit.rounded_box(name + "_Rail", sx * 0.62, sy * 0.94, sz * 0.10, r=2.0,
                     segments=2, centre=(centre[0], centre[1], top - sz * 0.02),
                     mat=rail_mat)
    if terminals:
        for i, dx in enumerate((-sx * 0.14, sx * 0.14)):
            bkit.rounded_box("%s_Terminal%d" % (name, i), sx * 0.10,
                             sy * 0.30, sz * 0.06, r=1.5, segments=2,
                             centre=(centre[0] + dx, centre[1],
                                     top + sz * 0.045), mat=terminal_mat)
    return case


def coiled_cord(name, centre, r_major, r_minor, a0, a1, plane="XZ", mat=None,
                seg_minor=10):
    """A slack mains cord coiled on itself -- a partial torus, watertight."""
    return bkit.arc_torus(name, r_major, r_minor, a0, a1, centre=centre,
                          plane=plane, seg_minor=seg_minor,
                          mat=mat or bkit.preset("rubber"))


def cord_run(name, pts, r, mat=None, seg=14):
    """A cord as a chain of straight rods joined by small spheres."""
    mat = mat or bkit.preset("rubber")
    out = []
    for i in range(len(pts) - 1):
        out.append(rod("%s_Seg%d" % (name, i), pts[i], pts[i + 1], r, mat,
                       seg=seg))
    for i in range(1, len(pts) - 1):
        out.append(bkit.uv_sphere("%s_Knee%d" % (name, i), r, segments=16,
                                  rings=10, centre=pts[i], mat=mat))
    return out


# --------------------------------------------------------------------------
# discs and cutters
# --------------------------------------------------------------------------

def saw_blade(name, diameter, thickness, bore_r, teeth=24, mat=None):
    """A toothed circular blade: a `gear` ring is the honest way to get teeth.

    `gear()` puts the TIP circle at `(teeth/2 + 1) * module`, so the module is
    `diameter / (teeth + 2)` -- declaring `diameter / teeth` gives a blade whose
    measured tip circle overshoots the number in the SPEC by exactly one module.
    """
    module = diameter / float(teeth + 2)
    return bkit.gear(name, teeth, module, thickness, bore_r,
                    mat=mat or bkit.preset("steel"))


def shroud(name, r_in, r_out, width, a0_deg, a1_deg, centre=(0, 0, 0),
           axis="Y", mat=None, seg=32):
    """A sheet-metal guard: an annular arc extruded across its width.

    A lathe cannot make a half-cowl -- it always revolves the full 360 deg -- so
    the arc is a 2D outline and `extrude_profile` gives it real thickness and a
    real width. `axis` is the direction the width runs.
    """
    n = seg
    poly = []
    for i in range(n + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
        poly.append((math.cos(a) * r_out, math.sin(a) * r_out))
    for i in range(n, -1, -1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
        poly.append((math.cos(a) * r_in, math.sin(a) * r_in))
    ob = bkit.extrude_profile(name, poly, width, mat=mat)
    if axis == "Y":
        ob.rotation_euler = (math.pi / 2.0, 0.0, 0.0)     # width -> Y
    elif axis == "X":
        ob.rotation_euler = (0.0, math.pi / 2.0, 0.0)     # width -> X
    elif axis == "Z":
        ob.rotation_euler = (0.0, 0.0, 0.0)
    ob.location = bkit.v(*centre)
    bpy.context.view_layer.update()
    return ob


def disc_cutter(name, diameter, thickness, rim_r, bore_r, seg=48, mat=None):
    """A plain cutting/abrasive disc with a depressed centre and a real bore."""
    rt = diameter / 2.0
    prof = [(bore_r, -thickness / 2.0),
            (rim_r, -thickness / 2.0),
            (rim_r, thickness / 2.0),
            (bore_r, thickness / 2.0)]
    body = bkit.lathe(name, prof, segments=seg, cap_ends=True, mat=mat,
                      smooth=False)
    centre_bolt = bkit.cylinder(name + "_Boss", rim_r, thickness * 0.7,
                                segments=bore_segments(seg), mat=mat,
                                smooth=False)
    bkit.boolean(body, centre_bolt, "UNION")
    bkit.recalc(body)
    return body


def guard_ring(name, r_in, r_out, height, arc_deg=200.0, seg_major=None,
               mat=None):
    """A partial-shroud guard: an arc_torus that reads as a sheet-metal cowl."""
    a0 = 90.0 - arc_deg / 2.0
    return bkit.arc_torus(name, (r_in + r_out) / 2.0, (r_out - r_in) / 2.0,
                          a0, a0 + arc_deg, seg_major=seg_major or 40,
                          plane="XZ", caps=True, mat=mat)


def knob(name, r, h, centre, mat=None, grip_flutes=8):
    """A fluted adjustment knob: a knurled disc on a short stem."""
    mat = mat or bkit.preset("black_plastic")
    body = bkit.cylinder(name, r, h, segments=grip_flutes * 4, centre=centre,
                         mat=mat, smooth=False)
    return body


def screw(name, p, r, length, mat=None, axis="Z"):
    """A pan-head screw standing proud of a face at p."""
    return bkit.cylinder(name, r, length, segments=12,
                         centre=(p[0], p[1], p[2] + length / 2.0), axis=axis,
                         mat=mat or bkit.preset("dark_metal"), smooth=False)


def label_plate(name, sx, sy, thick, centre, mat=None):
    """A spec plate on a tool flank."""
    return bkit.rounded_box(name, sx, thick, sy, r=1.0, segments=1,
                            centre=centre,
                            mat=mat or bkit.preset("anodized"))