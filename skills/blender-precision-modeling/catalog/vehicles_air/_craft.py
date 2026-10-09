"""
Shared construction for the vehicles_air domain.

An aircraft is three things and every model in this catalog is a different
answer to how they meet:

  1. a FUSELAGE -- a loft of superellipse sections along X. `body()` here
     takes `(x, half_width, bottom_z, top_z, n)` stations, which is the same
     section generator the road and marine domains use, with n high (6-9) for
     a tube-like fuselage and low (2.5-3.5) for a lifting body.
  2. a WING -- a loft of airfoil SECTIONS stacked across the span. `wing()`
     builds a tapered, swept, dihedral wing from root and tip sections. Wings
     are where the span is declared, so this is the part the CHECKS point at.
  3. hard points -- engine nacelles, pylons, fin, tailplane, undercarriage.

Units are millimetres everywhere, exactly as in bkit.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bkit
import bpy

MM = bkit.MM


# --------------------------------------------------------------------------
# transforms
# --------------------------------------------------------------------------

def freeze(ob):
    """Bake location/rotation/scale into the mesh and reset the origin.

    `bkit.duplicate()` SETS location, so a part that still carries one lands at
    mesh + offset -- the offset twice. Freeze before repeating anything.
    """
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.select_set(False)
    return ob


def strut(name, p0, p1, r, mat=None, seg=16, r2=None):
    """A round tube between two arbitrary points, in millimetres."""
    import mathutils
    a = mathutils.Vector((p0[0], p0[1], p0[2]))
    b = mathutils.Vector((p1[0], p1[1], p1[2]))
    d = b - a
    ob = bkit.cylinder(name, r, d.length, segments=seg, mat=mat, r2=r2)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (a + b)))
    return ob


def mirror_y(obj, name=None):
    """Mirror across the Y=0 centreline, keeping it as ONE object."""
    freeze(obj)
    bkit.mirror(obj, "Y")
    if name:
        obj.name = name
    return obj


def place_in_mesh(ob, dx=0.0, dy=0.0, dz=0.0):
    """Bake a millimetre offset into the MESH, leaving `ob.location` at zero.

    `bkit.array_radial` orbits LOCAL coordinates -- the array modifier applies
    the object offset to the prototype's mesh and the object's `location` is
    added once, afterwards. A prototype whose radius lives in `obj.location`,
    which is what `cylinder`, `lathe` and `place()` produce, therefore collapses
    the ring into one spoke plus a stack of copies. `rounded_box` and `box` bake
    `centre` into the mesh and can be positioned directly; everything else is
    shifted in the mesh first.
    """
    delta = bkit.v(dx, dy, dz)
    for v in ob.data.vertices:
        v.co = v.co + delta
    ob.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    return ob


# --------------------------------------------------------------------------
# fuselage
# --------------------------------------------------------------------------

def body(name, stations, mat=None, steps=56, smooth=38.0):
    """Loft `(x, half_width, z_bottom, z_top, n)` stations into a fuselage.

    A single loft along X is what gives an aircraft its profile -- nose taper,
    constant-section cabin, tail cone upsweep -- and a high n keeps the barrel
    round instead of egg-shaped.
    """
    secs = []
    for (x, hw, z0, z1, n) in stations:
        ring = bkit.superellipse_section(z1 - z0, 2.0 * hw, n=n, steps=steps,
                                         centre=(0.5 * (z1 + z0), 0.0))
        secs.append([(x, y, z) for (z, y) in ring])
    ob = bkit.loft(name, secs, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, smooth)
    return ob


def glass_band(ob, x_lo, x_hi, z_lo, z_hi, mat, max_nz=0.75):
    """Paint the near-vertical faces of a fuselage in a box as cockpit glass.

    World coordinates arrive in METRES, so the comparison is back in mm.
    """
    def pred(c, n):
        x = c.x / MM
        z = c.z / MM
        return x_lo <= x <= x_hi and z_lo <= z <= z_hi and abs(n.z) <= max_nz
    return bkit.assign_faces_by(ob, mat, pred)


# --------------------------------------------------------------------------
# wing
# --------------------------------------------------------------------------

def foil(chord, thick, camber=0.02, n=18):
    """One airfoil-ish section outline in (x, z), counter-clockwise.

    A symmetric foil with a little camber -- enough to read as an aerofoil in
    silhouette without needing a real NACA table.
    """
    up, lo = [], []
    for i in range(n + 1):
        t = i / float(n)
        half = 0.5 * thick * (1.0 - 2.4 * t + 1.55 * t * t
                              - 0.42 * t * t * t)
        x = chord * t
        up.append((x, camber * chord * math.sin(math.pi * t) + max(half, 0.0)))
        lo.append((x, camber * chord * math.sin(math.pi * t) - max(half, 0.0)))
    return up + lo[::-1]


def wing(name, root, tip, mat, z_centre=0.0, steps=20, smooth=30.0,
         dihedral=0.06):
    """One wing panel, from a root section to a tip section, along +Y.

    `root` and `tip` are `(x_le, chord, thickness, y)` -- the leading-edge
    station, chord, thickness ratio and spanwise station of each end. Sweep
    comes out of the x difference, dihedral out of the `dihedral` slope
    (0.06 = 6 per cent, which is airliner; a glider wants 0.025). The panel is
    built and frozen at the origin so the caller can mirror it.
    """
    (rx, rc, rt, ry) = root
    (tx, tc, tt, ty) = tip
    zt = z_centre + (ty - ry) * dihedral
    secs = []
    for i in range(steps + 1):
        t = i / float(steps)
        x = rx + (tx - rx) * t
        c = rc + (tc - rc) * t
        th = (rt + (tt - rt) * t) * c
        y = ry + (ty - ry) * t
        zz = z_centre + (zt - z_centre) * t
        secs.append([(x + px, y, zz + pz)
                     for (px, pz) in foil(c, th)])
    ob = bkit.loft(name, secs, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, smooth)
    return ob


def full_wing(name, root, tip, mat, z_centre=0.0, steps=20, dihedral=0.06):
    """A whole wing: one panel, mirrored in Y, as a single object.

    Built at the origin and frozen, so the object origin is the wing root on
    the centreline -- which is what `bkit.move()` and `duplicate()` expect.
    """
    w = wing(name, root, tip, mat, z_centre=z_centre, steps=steps,
             dihedral=dihedral)
    freeze(w)
    bkit.mirror(w, "Y")
    w.location = (0.0, 0.0, 0.0)
    return w


def nacelle(name, x, z, length, diameter, mat, axis="X", taper=0.88,
            segments=40, inlet=1.0):
    """An engine nacelle or a fuselage-side pod, axis along X.

    `inlet` scales the front lip radius, so a turbofan nacelle can have a
    bigger lip than its fan case and still be one closed solid.
    """
    r = diameter / 2.0
    prof = [(0.0, -length / 2.0),
            (r * inlet, -length / 2.0 + length * 0.10),
            (r, -length / 2.0 + length * 0.26),
            (r * taper, length / 2.0 - length * 0.18),
            (r * taper * 0.82, length / 2.0),
            (0.0, length / 2.0)]
    ob = bkit.lathe(name, prof, segments=segments, mat=mat, cap_ends=True)
    bkit.place(ob, (x, 0.0, z), axis)
    return ob


def tailplane(name, x, z, span_half, root_chord, tip_chord, thickness,
              mat, sweep=0.35, dihedral=0.0, steps=12):
    """A horizontal stabiliser, both halves, built at the origin and frozen."""
    w = wing(name, (x, root_chord, thickness, 0.0),
             (x - span_half * sweep, tip_chord, thickness * 0.8,
              span_half), mat, z_centre=0.0, steps=steps)
    freeze(w)
    bkit.mirror(w, "Y")
    w.location = (0.0, 0.0, 0.0)
    bkit.move(w, 0.0, 0.0, z)
    return w


def fin(name, height, root_chord, tip_chord, thickness, mat, sweep=0.42,
        steps=12, z0=0.0, roll=0.0):
    """A vertical fin: an airfoil lofted up the Z axis, with a swept leading edge.

    Built as a wing panel and then stood on end, because an airfoil lying on
    its side is the same geometry as one standing up.
    """
    w = wing(name, (0.0, root_chord, thickness, 0.0),
             (-height * sweep, tip_chord, thickness * 0.8, height), mat,
             steps=steps, smooth=30.0)
    # the panel was built lying in the XZ plane at y=0..height: rotate it so
    # the span runs up Z and the chord stays along X
    w.rotation_euler = (0.0, 0.0, 0.0)
    for v in w.data.vertices:
        x, y, z = v.co
        v.co = (x, -z, y)
    bkit.recalc(w)
    bkit.shade_smooth(w, 30.0)
    bkit.move(w, 0.0, 0.0, z0)
    return w


def blade(name, span, chord, thick, mat, twist=0.0, n=10):
    """One propeller blade: a tapered, twisted aerofoil standing on the Z axis.

    Built at the origin so `array_radial()` sweeps it about Z into a rotor.
    """
    secs = []
    for i in range(n + 1):
        t = i / float(n)
        r = 0.10 * span + t * 0.90 * span
        c = chord * (0.62 + 0.38 * (1.0 - t) ** 0.8)
        th = thick * (0.9 - 0.5 * t)
        a = math.radians(twist * t)
        ring = []
        for (px, pz) in foil(c, th):
            ring.append((r, px * math.cos(a) - pz * math.sin(a),
                         px * math.sin(a) + pz * math.cos(a)))
        secs.append(ring)
    ob = bkit.loft(name, secs, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, 30.0)
    return ob


def rotor(name, diameter, blades, hub_dia, mat, chord=None, thick=None,
          twist=28.0):
    """A rotor: hub plus `blades` copies of one aerofoil, axis along Z."""
    span = diameter / 2.0 - hub_dia / 2.0
    c = chord if chord is not None else diameter * 0.20
    t = thick if thick is not None else diameter * 0.022
    b = blade(name + "_Blade", span, c, t, mat, twist=twist)
    b.location = bkit.v(0.0, 0.0, hub_dia / 2.0)
    bkit.array_radial(b, blades, axis="Z")
    hub = bkit.lathe(name + "_Hub",
                     [(0.0, -hub_dia * 0.9), (hub_dia / 2.0, -hub_dia * 0.9),
                      (hub_dia / 2.0, hub_dia * 0.5), (0.0, hub_dia * 0.5)],
                     segments=32, mat=mat)
    freeze(hub)
    ob = bkit.join([b, hub], name)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def nacelle_pair(name, x, z, half_span, diameter, length, mat, pylon=None,
                 pylon_mat=None, inlet=1.0):
    """Two nacelles on pylons, mirrored in Y, as two named objects."""
    out = []
    for i, s in enumerate((1, -1)):
        n = bkit.lathe("%s%d" % (name, i),
                       [(0.0, -length / 2.0),
                        (diameter / 2.0 * inlet, -length / 2.0 + length * 0.10),
                        (diameter / 2.0, -length / 2.0 + length * 0.26),
                        (diameter / 2.0 * 0.88, length / 2.0 - length * 0.18),
                        (diameter / 2.0 * 0.72, length / 2.0),
                        (0.0, length / 2.0)], segments=40, mat=mat)
        bkit.place(n, (x, s * half_span, z), "X")
        out.append(n)
        if pylon:
            b = bkit.rounded_box("%sPylon%d" % (name, i), pylon[0], pylon[1],
                                 pylon[2], r=pylon[0] * 0.3, segments=2,
                                 centre=(x + pylon[0] * 0.25,
                                         s * half_span, z + diameter * 0.5
                                         + pylon[2] / 2.0),
                                 mat=pylon_mat or mat)
            out.append(b)
    return out


def cockpit_glass(ob, x_lo, x_hi, z_lo, z_hi, mat, max_nz=0.8):
    return glass_band(ob, x_lo, x_hi, z_lo, z_hi, mat, max_nz=max_nz)
