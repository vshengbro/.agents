"""
Shared helpers for the agriculture domain.

Machinery in this domain has three repeated problems, and this module holds the
answers so all 18 items agree on them:

  1. GROUNDED WHEELS. A farm machine is judged on its wheels: the right count,
     the right diameter, and every tread exactly on z=0. One wheel is built at
     the origin and repeated, and the radius is the last element of each
     position tuple so a wheel can never be authored at the wrong height.
  2. FARM TRACKS. Every implement wider than its tractor runs on a common
     `make_ground` plane, so a plough and a seed drill are both standing on
     something and neither floats.
  3. DISC ARRAYS. Disc harrows and seed drills are gangs of discs, and the only
     correct way to place a gang is from the axle centre the discs orbit --
     never from the world origin.

Units are millimetres everywhere, exactly as in bkit.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit
import bpy


def place_in_mesh(ob, dx=0.0, dy=0.0, dz=0.0):
    """Bake a millimetre offset into the MESH, leaving `ob.location` at zero.

    `bkit.array_radial` orbits LOCAL coordinates: the array modifier applies the
    object offset to the prototype's own mesh, and the object's `location` is
    added once, afterwards. So a prototype that carries its orbit radius in
    `obj.location` -- which is exactly what `cylinder`, `lathe` and `place()`
    produce, because they set `location = centre` and leave the mesh at the
    origin -- collapses the ring into a single spoke plus a stack of rotated
    copies on top of it. Verified: a 380 mm boom placed at `location` and
    arrayed 4x about (0,0,1150) measures x[64,444] y[-190,190] instead of the
    correct x[-444,444] y[-444,444].

    Only primitives that bake `centre` into the mesh (`rounded_box`, `box`) can
    be positioned before an array; everything else is shifted in the mesh.
    """
    delta = bkit.v(dx, dy, dz)
    for v in ob.data.vertices:
        v.co = v.co + delta
    ob.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    return ob


# --------------------------------------------------------------------------
# wheels
# --------------------------------------------------------------------------

def freeze(ob):
    """Bake location/rotation/scale into the mesh.

    `bkit.duplicate()` sets an ABSOLUTE location and copies the source's
    rotation, so a wheel assembled from `place(..., "Y")` parts must be frozen
    before it is repeated or every copy arrives still rotated about its own
    centre. (This is the same helper `vehicles_road/_vehicles.py` uses.)
    """
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.select_set(False)
    return ob


def ground_wheel(name, dia, width, rim_dia=None, seg=40, dish=True,
                 mat_tyre=None, mat_rim=None):
    """One tractor wheel, axis along +Y, built and frozen at the origin.

    The tyre is a revolved carcass with shouldered sides rather than a plain
    cylinder: a farm tyre's shoulder is most of its silhouette. R1 = tread
    radius, and the tread band is the full width, which is what puts the tread
    exactly on z=0 when the wheel is placed at z = dia/2.
    """
    rt = dia / 2.0
    ri = (rim_dia or dia * 0.52) / 2.0
    hw = width / 2.0
    sh = width * 0.30
    rubber = mat_tyre or bkit.preset("rubber")
    steel = mat_rim or bkit.preset("dark_metal")

    prof = [(ri, -hw), (rt - sh * 0.85, -hw), (rt, -hw + sh),
            (rt, hw - sh), (rt - sh * 0.85, hw), (ri, hw), (ri, -hw)]
    tyre = bkit.lathe(name + "_Tyre", prof, segments=seg, cap_ends=False,
                      mat=rubber)
    tyre.rotation_euler = (math.pi / 2.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    parts = [tyre]
    parts.append(bkit.tube(name + "_Rim", ri + 1.0, ri - 22.0, width * 0.84,
                           segments=seg, axis="Y", mat=steel))
    if dish:
        parts.append(bkit.lathe(name + "_Disc",
                               [(0.0, -hw * 0.30), (ri - 22.0, -hw * 0.30),
                                (ri - 2.0, -hw * 0.62), (ri - 2.0, hw * 0.62),
                                (ri - 22.0, hw * 0.30), (0.0, hw * 0.30)],
                               segments=seg, cap_ends=False, mat=steel))
    parts.append(bkit.cylinder(name + "_Hub", ri * 0.34, width * 0.9,
                               segments=24, axis="Y", mat=steel))
    ob = bkit.join(parts, name)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def place_wheels(w, positions, names=None):
    """Repeat one wheel at every (x, y, z) corner; z IS the wheel radius.

    Because z is supplied as the radius rather than a hand-typed height, the
    treads land on z=0 by construction and `sit_on_floor()` becomes a no-op --
    which is what the render's ground contact depends on.
    """
    nm = list(names or ["Wheel%d" % i for i in range(len(positions))])
    w.name = nm[0]
    for name, (x, y, z) in zip(nm[1:], positions[1:]):
        bkit.duplicate(w, name, offset_mm=(x, y, z))
    bkit.move(w, *positions[0])
    return nm


def track_positions(wheelbase, track, radius, axles=None):
    """Four wheel positions: +/- wheelbase/2 along X, +/- track/2 along Y."""
    xf, xr = axles or (-wheelbase / 2.0, wheelbase / 2.0)
    return [(xf, -track / 2.0, radius), (xf, track / 2.0, radius),
            (xr, -track / 2.0, radius), (xr, track / 2.0, radius)]


# --------------------------------------------------------------------------
# ground and context
# --------------------------------------------------------------------------

def make_ground(name, sx, sy, height=40.0, mat=None):
    """A soil pad under the implement.

    Machinery reads as floating without it, and it gives `sit_on_floor` a
    sensible lowest point. Kept as its own named object so it can be excluded
    from a dimension check by pointing `part` at the implement instead.
    """
    return bkit.box(name, sx, sy, height,
                    centre=(0.0, 0.0, -height / 2.0),
                    mat=mat or bkit.preset("soil"))


# --------------------------------------------------------------------------
# disc gangs
# --------------------------------------------------------------------------

def disc(name, dia, thickness, dish_depth, seg=32, mat=None):
    """One concave plough disc, axis along +X, standing in the YZ plane.

    The CONCAVITY is what makes a disc look like a plough disc and not a washer:
    the face is dished `dish_depth`, so the rim is a knife edge and the centre is
    set back. The disc is a closed lathe about Z, then rolled 90 deg about Y so
    its axis lies along X -- a roll about Z would leave the disc lying FLAT,
    which is a disc on a table rather than a disc on a gang.
    """
    rt = dia / 2.0
    hd = dish_depth
    prof = [(0.0, -hd), (rt * 0.55, -hd * 0.62), (rt, 0.0),
            (rt, thickness), (rt * 0.55, thickness + hd * 0.62),
            (0.0, thickness + hd)]
    ob = bkit.lathe(name, prof, segments=seg, cap_ends=False,
                    mat=mat or bkit.preset("brushed_metal"))
    ob.rotation_euler = (0.0, math.pi / 2.0, 0.0)
    bpy.context.view_layer.update()
    return ob


def gang(name, discs, dia, thickness, dish_depth, positions_x, positions_y,
         z, tilt_deg=0.0, axis="X", mat=None):
    """A row of concave discs on one axle, on a computed spacing.

    A gang is a STRAIGHT ROW along its own axle, so the spacing is linear and
    comes from `grid_positions`. It is not a radial array: `array_radial` about
    the axle would wrap the discs into a circle standing in the plane
    perpendicular to the axle, which is a windmill, not a harrow.
    """
    out = []
    for i, (px, py) in enumerate(positions_x if positions_y is None
                                  else zip(positions_x, positions_y)):
        d = disc("%s%d" % (name, i), dia, thickness, dish_depth, mat=mat)
        # Tilt the disc off vertical so it cuts AND rolls. The tilt has to be
        # ADDED to the 90 deg roll about the SAME axis: a separate Z rotation
        # spins the disc sideways within the horizontal plane, which leans the
        # gang over instead of raking the discs back.
        d.rotation_euler = (0.0, math.pi / 2.0 + math.radians(tilt_deg), 0.0)
        bpy.context.view_layer.update()
        bkit.move(d, px, py, z)
        out.append(d)
    return out


# --------------------------------------------------------------------------
# frames
# --------------------------------------------------------------------------

def bar_between(name, p0, p1, w, h, mat=None, r=2.0, segments=2):
    """A rectangular member from p0 to p1 (mm), in any direction.

    `rounded_box` bakes its centre into the mesh and leaves the object at the
    origin, so rotating the object and then setting its location to the member
    midpoint is correct -- the rotation happens about the member's own centre.
    """
    from mathutils import Vector
    a, b = Vector(p0), Vector(p1)
    d = b - a
    ob = bkit.rounded_box(name, w, h, d.length, r=r, segments=segments,
                          mat=mat)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (a + b)))
    bpy.context.view_layer.update()
    return ob


def tube_between(name, p0, p1, r, mat=None, seg=16, r2=None):
    """A round tube from p0 to p1 (mm), in any direction."""
    from mathutils import Vector
    a, b = Vector(p0), Vector(p1)
    d = b - a
    ob = bkit.cylinder(name, r, d.length, segments=seg, mat=mat, r2=r2)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (a + b)))
    bpy.context.view_layer.update()
    return ob


def mirror_y(obj, name=None):
    """Mirror a part across Y=0 and keep it as ONE object.

    `freeze()` FIRST is not optional: Blender's Mirror modifier reflects
    through the object's LOCAL origin plane, and `cylinder`/`lathe` leave their
    centre in `obj.location`. Mirroring one of those unfrozen reflects it
    through its own centre and lands the copy exactly on the original.
    """
    freeze(obj)
    bkit.mirror(obj, "Y")
    if name:
        obj.name = name
    return obj


AGRI_NOTE = (
    "One wheel is built at the origin and repeated, with the wheel RADIUS as "
    "the z of every position, so treads land on z=0 by construction. Disc gangs "
    "are arrayed about their own axle centre, never the world origin.")