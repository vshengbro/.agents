"""
Shared vehicle construction helpers for the vehicles_road domain.

Every vehicle in this domain is the same four decisions:

  1. a body shell lofted along X over superellipse cross-sections,
  2. wheel arches cut as Y-axis pockets (not through-tunnels),
  3. ONE wheel built at the origin and repeated at the corners,
  4. every dimension taken from a real vehicle, not invented.

This module holds those decisions so all 18 items share them. It is prefixed
with `_` so blrun.py's directory scan skips it (`not f.startswith("_")`).

Units are millimetres everywhere, exactly as in bkit.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit
import bpy


# --------------------------------------------------------------------------
# transforms
# --------------------------------------------------------------------------

def freeze(ob):
    """Bake location/rotation/scale into the mesh data.

    `bkit.duplicate()` re-locates the copy absolutely, which is only correct if
    the source object's transform is identity -- otherwise the copy inherits the
    source's rotation *and* gets a fresh location, and the wheel ends up rotated.
    Every wheel part here is laid on its Y axis with `place(..., "Y")`, so the
    joined wheel MUST be frozen before it is repeated.
    """
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.select_set(False)
    return ob


# --------------------------------------------------------------------------
# body shells
# --------------------------------------------------------------------------

def ring(x, hw, z0, z1, n=3.6, steps=64):
    """One car cross-section at station `x`, returned as a 3D ring.

    The ring is a superellipse in the YZ plane: `hw` is the half width, z0/z1
    the section's vertical extent (sill line to roof line) and `n` the exponent.
    n ~ 2.6 is a soft nose, n ~ 3.6 a car flank, n ~ 4.4 a squarer box body.
    """
    h = z1 - z0
    c = 0.5 * (z0 + z1)
    r2 = bkit.superellipse_section(h, 2.0 * hw, n=n, steps=steps, centre=(c, 0.0))
    return [(x, y, z) for (z, y) in r2]


def shell(name, stations, mat=None, steps=64, smooth_angle=34.0, loft_kw=None):
    """Loft a list of `(x, hw, z0, z1, n)` stations into one closed body.

    A single loft along X is what gives a car its SIDE SILHOUETTE -- nose slope,
    bonnet, screen rake, roof, tailgate -- which is the thing renders are judged
    on. Splitting "lower body" and "greenhouse" into two lofts makes the
    shoulder fight the roof and the join line shows in every three-quarter view.
    """
    secs = [ring(s[0], s[1], s[2], s[3], n=s[4], steps=steps) for s in stations]
    ob = bkit.loft(name, secs, mat=mat, **(loft_kw or {}))
    bkit.recalc(ob)
    bkit.shade_smooth(ob, smooth_angle)
    return ob


def arch_cut(body, x, y_in, y_out, z, r, seg=56, both=True):
    """Cut a wheel-arch pocket into a body shell.

    The cutter is a Y-axis cylinder that reaches from outside the flank
    (`y_out`) into the cabin (`y_in`) but stops there, so the well has an inner
    fender wall. Running it all the way through the far flank would leave a
    see-through tunnel, which reads as a modelling error from every low angle.

    Overlap rule: `y_out` must be at least 20 mm proud of the body half width and
    `y_in` must be at least 10 mm inside it, or the two surfaces touch along an
    edge instead of crossing and the EXACT solver answers with bad edges.
    """
    cut = bkit.cylinder("_arch", r, (y_out - y_in), segments=seg,
                        centre=(x, 0.5 * (y_in + y_out), z), axis="Y")
    bkit.boolean(body, cut, "DIFFERENCE")
    if both:
        cut = bkit.cylinder("_arch", r, (y_out - y_in), segments=seg,
                            centre=(x, -0.5 * (y_in + y_out), z), axis="Y")
        bkit.boolean(body, cut, "DIFFERENCE")
    return body


def glass_band(ob, z_lo, z_hi, mat, max_nz=0.72, x_lo=None, x_hi=None):
    """Paint the greenhouse faces of a body shell as glass.

    A face qualifies when its centre sits inside the belt-to-headroom band and
    its normal is not close to vertical -- that keeps the roof and the bonnet
    body-coloured while the screens and side glass go dark. `x_lo`/`x_hi`
    restrict the band along the length, which is what a van or a bus needs: its
    glazed area stops at the bulkhead and the body sides stay panel.

    `assign_faces_by` hands the predicate a world-space centre in METRES, so the
    comparison is back in millimetres here.
    """
    def pred(c, n):
        z = c.z / bkit.MM
        x = c.x / bkit.MM
        if not (z_lo <= z <= z_hi) or abs(n.z) > max_nz:
            return False
        if x_lo is not None and x < x_lo:
            return False
        if x_hi is not None and x > x_hi:
            return False
        return True
    return bkit.assign_faces_by(ob, mat, pred)


# --------------------------------------------------------------------------
# wheels
# --------------------------------------------------------------------------

def wheel(name, tyre_dia, tyre_w, rim_dia, spokes=5, seg=48, dish=True,
          mat_tyre=None, mat_rim=None):
    """One road wheel, axis along +Y, built at the origin and frozen.

    Tyre is a revolved closed cross-section (a real toroidal carcass with
    shouldered shoulders, not a plain cylinder). Rim is a barrel plus a face:
    a dished disc for solid wheels, or a hub plus radial spokes for ones where
    you can see through the wheel. Parts interpenetrate by >=1 mm by design;
    each is independently watertight, so no boolean is needed anywhere.
    """
    rt = tyre_dia / 2.0
    ri = rim_dia / 2.0
    hw = tyre_w / 2.0
    sh = tyre_w * 0.30
    rubber = mat_tyre or bkit.preset("rubber")
    steel = mat_rim or bkit.preset("brushed_metal")

    prof = [(ri, -hw), (rt - sh * 0.85, -hw), (rt, -hw + sh),
            (rt, hw - sh), (rt - sh * 0.85, hw), (ri, hw), (ri, -hw)]
    tyre = bkit.lathe(name + "_Tyre", prof, segments=seg, cap_ends=False,
                      mat=rubber)
    bkit.place(tyre, (0.0, 0.0, 0.0), "Y")

    barrel = bkit.tube(name + "_Barrel", ri + 1.0, ri - 18.0, tyre_w * 0.86,
                       segments=seg, axis="Y", mat=steel)

    if spokes:
        r_a = ri * 0.30 - 8.0
        r_b = ri - 13.0
        sp = bkit.rounded_box(name + "_Spoke", r_b - r_a, ri * 0.26, tyre_w * 0.22,
                              r=2.5, segments=2,
                              centre=((r_a + r_b) / 2.0, 0.0, 0.0), mat=steel)
        bkit.array_radial(sp, spokes, axis="Y")
        parts = [barrel, sp]
    else:
        prof2 = [(0.0, -hw * 0.28), (ri - 20.0, -hw * 0.28),
                 (ri - 1.0, -hw * 0.62), (ri - 1.0, hw * 0.62),
                 (ri - 20.0, hw * 0.28), (0.0, hw * 0.28)]
        parts = [barrel, bkit.lathe(name + "_Face", prof2, segments=seg,
                                    cap_ends=False, mat=steel)]

    hub = bkit.cylinder(name + "_Hub", ri * 0.32, tyre_w * 0.52, segments=32,
                        axis="Y", mat=steel)
    cap = bkit.cylinder(name + "_Cap", ri * 0.13, tyre_w * 0.66, segments=24,
                        axis="Y", mat=bkit.preset("polished_metal"))
    parts += [hub, cap]

    rim = bkit.join(parts, name + "_Rim")
    freeze(rim)
    rim.location = (0.0, 0.0, 0.0)
    w = bkit.join([tyre, rim], name)
    freeze(w)
    w.location = (0.0, 0.0, 0.0)
    return w


def place_wheels(w, positions, prefix="Wheel", names=None):
    """Repeat one wheel at every `(x, y, z)` corner; z is the wheel radius.

    The last element of each position is the radius, so a wheel can never be
    authored at the wrong height: `z = tyre_dia/2` puts its tread exactly on
    z=0, which is what `sit_on_floor()` expects to be a no-op. `names` lets a
    vehicle with different front and rear wheels name all four without Blender
    silently suffixing a collision into `Wheel0.001`.
    """
    nm = list(names or ["%s%d" % (prefix, i) for i in range(len(positions))])
    w.name = nm[0]
    for name, (x, y, z) in zip(nm[1:], positions[1:]):
        bkit.duplicate(w, name, offset_mm=(x, y, z))
    bkit.move(w, *positions[0])
    return nm


def corners(wb, track, r, axles=None):
    """Four wheel positions for a car: +/-wb/2 along X, +/-track/2 along Y."""
    xf, xr = (axles or (-wb / 2.0, wb / 2.0))
    return [(xf, -track / 2.0, r), (xf, track / 2.0, r),
            (xr, -track / 2.0, r), (xr, track / 2.0, r)]


def strut(name, p0, p1, r, mat=None, seg=16, r2=None):
    """A round tube between two arbitrary points, in millimetres.

    bkit's primitives are axis-aligned, which is fine for a boxy vehicle and
    useless for a bicycle frame, a forklift mast or a wheelbarrow handle. This
    is the one piece of geometry glue every open-frame item needs.
    """
    import mathutils
    a = mathutils.Vector((p0[0], p0[1], p0[2]))
    b = mathutils.Vector((p1[0], p1[1], p1[2]))
    d = b - a
    ob = bkit.cylinder(name, r, d.length, segments=seg, mat=mat, r2=r2)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (a + b)))
    return ob


def spoked_wheel(name, tyre_dia, tyre_w, rim_dia, spokes=24, hub_dia=90.0,
                 seg=48, mat_tyre=None, mat_rim=None):
    """A thin spoked wheel -- bicycles, motorcycles, anything without a tyre wall.

    Real cross-laced spokes are what make a bicycle wheel read as a bicycle
    wheel, and unlike a car rim they are the only thing between the hub and the
    tyre, so the wheel is mostly hole. Build one, freeze it, repeat it.
    """
    rt = tyre_dia / 2.0
    ri = rim_dia / 2.0
    hw = tyre_w / 2.0
    sh = tyre_w * 0.30
    rubber = mat_tyre or bkit.preset("rubber")
    steel = mat_rim or bkit.pbr("SpokeSteel", base=(0.70, 0.71, 0.73),
                                metal=0.80, rough=0.30)

    prof = [(ri - 12.0, -hw), (rt - sh * 0.8, -hw), (rt, -hw + sh),
            (rt, hw - sh), (rt - sh * 0.8, hw), (ri - 12.0, hw),
            (ri - 12.0, -hw)]
    tyre = bkit.lathe(name + "_Tyre", prof, segments=seg, cap_ends=False,
                      mat=rubber)
    bkit.place(tyre, (0.0, 0.0, 0.0), "Y")

    rim = bkit.tube(name + "_Rim", ri, ri - 24.0, tyre_w * 0.86, segments=seg,
                    axis="Y", mat=steel)
    hub = bkit.cylinder(name + "_Hub", hub_dia / 2.0, tyre_w * 1.25, segments=24,
                        axis="Y", mat=steel)
    r_a = hub_dia / 2.0 - 4.0
    ln = (ri - 20.0) - r_a
    sp = bkit.rounded_box(name + "_Spoke", ln, tyre_w * 0.16, max(2.2, hw * 0.10),
                          r=1.0, segments=1,
                          centre=(r_a + ln / 2.0, 0.0, 0.0), mat=steel)
    bkit.array_radial(sp, spokes, axis="Y")

    w = bkit.join([tyre, rim, hub, sp], name)
    freeze(w)
    w.location = (0.0, 0.0, 0.0)
    return w


def mirror_y(obj, name=None):
    """Mirror a part across the Y=0 centreline and keep it as ONE object.

    `bkit.duplicate()` writes an ABSOLUTE location and `bkit.move()` is relative,
    so duplicating with an offset and then moving again silently doubles the
    offset. The Mirror modifier is the right tool for a symmetric vehicle: it
    cannot drift, it halves the part count, and it guarantees both sides agree.

    freeze() FIRST is not optional. Blender's Mirror modifier reflects through
    the object's LOCAL origin plane, not the world one. `rounded_box` bakes its
    centre into the mesh and leaves the object at the origin, so it mirrors
    correctly by accident -- but `cylinder`/`tube`/`lathe` go through
    `place()`, which puts the centre in `obj.location`. Mirroring one of those
    un-frozen reflects it through its own centre, producing a copy that lands
    exactly on top of the original: every edge ends up with four faces and
    `bkit.health()` reports non-manifold edges.
    """
    freeze(obj)
    bkit.mirror(obj, "Y")
    if name:
        obj.name = name
    return obj


def box_lamp(name, sx, sy, sz, centre, mat, r=6.0):
    """A rounded lamp lens -- the small parts that make a car read as a car."""
    return bkit.rounded_box(name, sx, sy, sz, r=r, segments=3,
                            centre=centre, mat=mat)