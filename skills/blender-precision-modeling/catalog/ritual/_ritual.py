"""
Shared construction for the ritual domain.

Ritual objects are CARVED and TURNED forms, which in bkit means four recipes
carry almost every model here:

  1. `lathe` -- the turned profile.  Every bowl, censer, vase, finial and
     bead in this domain is a revolved closed profile, and the wall thickness
     is in the profile rather than faked with a second object.
  2. `extrude_profile` -- the carved plaque.  A mask, a moai's brow, a door
     panel and a scroll end are all 2D outlines given depth.
  3. `array_linear` / `array_radial` -- the ORNAMENT.  A totem pole is a stack
     of repeated carved motifs, a sunburst is a radial array, a feather crown
     is a fan.  None of these are hand-placed.
  4. `perforated_panel` -- the pierced pattern of a censer lid or a mask's
     cheek panels.

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


def place_in_mesh(ob, dx=0.0, dy=0.0, dz=0.0):
    """Bake a millimetre offset into the MESH, leaving `ob.location` at zero.

    `bkit.array_radial` orbits LOCAL coordinates -- the array modifier applies
    the object offset to the prototype's mesh, and the object's `location` is
    added once, afterwards. A prototype whose radius lives in `obj.location`
    (what `cylinder`, `lathe` and `place()` produce) therefore collapses the
    ring into one spoke plus a stack of copies. Only primitives that bake
    `centre` into the mesh (`rounded_box`, `box`) can be positioned first.
    """
    delta = bkit.v(dx, dy, dz)
    for v in ob.data.vertices:
        v.co = v.co + delta
    ob.location = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    return ob


# --------------------------------------------------------------------------
# wood
# --------------------------------------------------------------------------

def cedar(name="RitualCedar", base=(0.42, 0.24, 0.12), rough=0.52):
    return bkit.pbr(name, base=base, rough=rough)


def basalt(name="RitualBasalt", base=(0.13, 0.13, 0.14)):
    return bkit.pbr(name, base=base, rough=0.78)


def patina(name="RitualPatina", base=(0.30, 0.36, 0.30), rough=0.45):
    return bkit.pbr(name, base=base, rough=rough, metal=0.35)


def gild(name="RitualGold", base=(0.92, 0.74, 0.32)):
    return bkit.pbr(name, base=base, rough=0.26, metal=0.85)


def lacquer(name="RitualLacquer", base=(0.28, 0.05, 0.05), rough=0.16):
    return bkit.pbr(name, base=base, rough=rough, coat=0.6)


# --------------------------------------------------------------------------
# turned forms
# --------------------------------------------------------------------------

def bowl(name, r_out, r_in, height, foot_h=14.0, foot_r=None, segments=64,
         mat=None):
    """A turned bowl with a REAL wall: outer up, over the rim, and back down
    the inside to the floor of the bowl.  One closed profile means one closed
    solid, so there is no second inner shell to z-fight with the wall."""
    fr = foot_r if foot_r is not None else r_out * 0.42
    prof = [(0.0, 0.0), (fr * 0.9, 0.0), (fr, foot_h),
            (r_out * 0.86, foot_h + height * 0.10),
            (r_out, foot_h + height * 0.72), (r_out, foot_h + height),
            (r_in, foot_h + height), (r_in, foot_h + height * 0.34),
            (r_in * 0.42, foot_h + height * 0.20), (0.0, foot_h + height * 0.20)]
    ob = bkit.lathe(name, prof, segments=segments, cap_ends=True,
                    mat=mat or patina())
    bkit.recalc(ob)
    return ob


def turned_leg(name, height, r_max, foot_r, waist_r, segments=32, mat=None):
    """A turned leg: foot, waist, knee, capital.  The whole profile in one
    revolution, which is what makes turned wood read as turned."""
    h = height
    prof = [(0.0, 0.0), (foot_r, 0.0), (foot_r, h * 0.06),
            (r_max * 0.92, h * 0.16), (waist_r, h * 0.42),
            (r_max * 0.80, h * 0.70), (r_max, h * 0.88),
            (r_max, h), (0.0, h)]
    ob = bkit.lathe(name, prof, segments=segments, mat=mat or cedar())
    bkit.recalc(ob)
    return ob


def finial(name, height, r, segments=32, mat=None):
    """A turned finial knob -- the top of a lid, a fence post, a finial."""
    h = height
    prof = [(0.0, 0.0), (r, 0.0), (r, h * 0.10), (r * 0.62, h * 0.22),
            (r * 0.86, h * 0.40), (r * 0.70, h * 0.58),
            (r * 0.40, h * 0.76), (r * 0.22, h * 0.90), (0.0, h)]
    ob = bkit.lathe(name, prof, segments=segments, mat=mat or gild())
    bkit.recalc(ob)
    return ob


def dome(name, r, height, thickness, segments=48, mat=None):
    """A hollow dome lid: over the outside, then back down the inside.

    The profile is a CLOSED LOOP that never reaches the axis.  Taking the outer
    surface to r = 0 and starting the inner surface at r = 0 puts an AXIAL
    SEGMENT between them, and a lathe turns an axial segment into a ring of
    zero-width quads -- exactly one non-manifold edge, every time.  The crown
    keeps a flat `thickness`-thick bridge instead.
    """
    t = thickness
    rc = r * 0.26
    outer = [(r - t, 0.0), (r, t * 0.7), (r * 0.94, t + height * 0.18),
             (r * 0.78, t + height * 0.48), (r * 0.52, t + height * 0.80),
             (rc, t + height)]
    crown = [(rc * 0.82, t + height), (rc * 0.82, height)]
    inner = [(r * 0.44, height * 0.78), (r * 0.70, height * 0.46),
             (r * 0.86, t + height * 0.16), (r - t, t * 0.7)]
    prof = outer + crown + inner + [outer[0]]
    ob = bkit.lathe(name, prof, segments=segments, cap_ends=False, mat=mat)
    bkit.recalc(ob)
    return ob


def pierce(shell, cols, rows, radius, pitch_a, pitch_z, z0, hole_r,
           host_segments):
    """Drill a real hole grid through a cylindrical shell.

    One `bore()` per hole, with the cutter's segment count taken from
    `bore_segments()` so no facet lands on a facet.  The angular pitch is a
    real arc length at the given radius, so the holes do not bunch at the
    equator.
    """
    n = 0
    for i in range(cols):
        a = 2.0 * math.pi * i / cols
        cx, cy = radius * math.cos(a), radius * math.sin(a)
        for j in range(rows):
            z = z0 + pitch_z * j
            cut = bkit.cylinder("_pierce", hole_r, radius * 4.0,
                                segments=bore_segments(host_segments),
                                centre=(cx, cy, z))
            bkit.boolean(shell, cut, "DIFFERENCE")
            n += 1
    bkit.recalc(shell)
    return n


def bore_segments(host_segments):
    return bkit.bore_segments(host_segments)


# --------------------------------------------------------------------------
# ornament
# --------------------------------------------------------------------------

def ray_crown(name, r, count, h, w, mat=None, taper=0.55, axis="Z",
              centre=None, upright=True):
    """A crown/halo of rays, arrayed radially about `centre`.

    `upright` stands the rays on end first: a ray extruded in XY lies flat, and
    a radial array of flat rays is a starfish, not a crown.  Rotating the
    prototype about X BEFORE `array_radial` puts every copy's long axis vertical
    while the orbit itself stays horizontal.
    """
    blade = bkit.extrude_profile(name,
                                 [(-w / 2.0, 0.0), (w / 2.0, 0.0),
                                  (w * taper / 2.0, h), (-w * taper / 2.0, h)],
                                 max(2.0, w * 0.35), mat=mat or gild())
    if upright and axis == "Z":
        blade.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = blade
    blade.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    blade.select_set(False)
    blade.location = bkit.v(r, 0.0, 0.0)
    bpy.context.view_layer.update()
    bkit.array_radial(blade, count, axis=axis, centre=centre or (0.0, 0.0, 0.0))
    return blade


def stack_motifs(name, count, pitch, proto, first_z=0.0, axis="Z"):
    """Repeat one carved motif up a pole.

    The spacing is the PITCH, so a motif can never land on top of its
    neighbour; `array_linear(..., world=True)` steps in millimetres rather
    than in the proto's own local space.
    """
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = proto
    proto.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    proto.select_set(False)
    off = [0.0, 0.0, pitch]
    if axis == "X":
        off = [pitch, 0.0, 0.0]
    proto.location = bkit.v(*([0.0, 0.0, first_z] if axis == "Z"
                              else [first_z, 0.0, 0.0]))
    bpy.context.view_layer.update()
    bkit.array_linear(proto, count, off, world=True)
    return proto


def pierced_band(name, cols, rows, pitch, hole_r, band_r, band_h, thickness,
                 mat=None, segments=16):
    """A pierced collar around a vessel: the hole pattern wrapped onto a
    cylinder, as one mesh, with no boolean to go wrong."""
    ob = bkit.perforated_panel(name, cols, rows, pitch, pitch, hole_r,
                               band_r * math.pi / max(cols, 1) * 1.02,
                               band_h, thickness,
                               mat=mat or gild())
    # roll the flat panel round the vessel axis and stand it up
    ob.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bpy.context.view_layer.update()
    return ob


def plinth(name, sx, sy, sz, mat=None, r=8.0):
    return bkit.rounded_box(name, sx, sy, sz, r=r, segments=2,
                            centre=(0.0, 0.0, sz / 2.0), mat=mat or basalt())


# --------------------------------------------------------------------------
# organic stone
# --------------------------------------------------------------------------

def boulder(name, stations, segments=40, mat=None, smooth=32.0):
    """A rock from `(z, half_x, half_y, n, dx, dy)` stations lofted up.

    A garden rock is the one object in this domain with no rotational symmetry,
    so it is a loft of jittered superellipse sections rather than a lathe: the
    offset columns are what stop it reading as a bean.
    """
    secs = []
    for (z, hx, hy, n, dx, dy) in stations:
        ring = bkit.superellipse_section(2.0 * hx, 2.0 * hy, n=n, steps=segments,
                                         centre=(dx, dy))
        secs.append([(x, y, z) for (x, y) in ring])
    ob = bkit.loft(name, secs, mat=mat or basalt())
    bkit.recalc(ob)
    bkit.shade_smooth(ob, smooth)
    return ob


# --------------------------------------------------------------------------
# small parts
# --------------------------------------------------------------------------

def bead(name, r, centre, mat=None, segments=20, rings=12):
    return bkit.uv_sphere(name, r, segments=segments, rings=rings,
                          centre=centre, mat=mat or cedar())


def bar(name, p0, p1, w, h, mat=None, r=2.0, segments=2):
    d = Vector(p1) - Vector(p0)
    ob = bkit.rounded_box(name, w, h, d.length, r=r, segments=segments,
                          mat=mat or cedar())
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (Vector(p0) + Vector(p1))))
    bpy.context.view_layer.update()
    return ob


def rope(name, p0, p1, r, mat=None, seg=12):
    """A cord between two points (mm)."""
    d = Vector(p1) - Vector(p0)
    ob = bkit.cylinder(name, r, d.length, segments=seg,
                       mat=mat or bkit.preset("fabric"))
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (Vector(p0) + Vector(p1))))
    bpy.context.view_layer.update()
    return ob