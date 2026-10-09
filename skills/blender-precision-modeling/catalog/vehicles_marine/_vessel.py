"""
Shared hull construction for the vehicles_marine domain.

Every boat in this catalog is the same four decisions:

  1. a HULL lofted along X over U-shaped cross-sections -- a boat's section is
     not a superellipse. A superellipse closes to a point at the sheer, so the
     widest point is amidships at mid-depth: that is a car body, not a boat.
     `section()` here runs from the deck edge DOWN the topsides, round a
     bilge of finite width, across a flat bottom and up the far side, then
     closes across the deck. `k` (bottom ratio) is what separates a flat-bottom
     workboat from a round-bilge canoe.
  2. a sheer line -- the deck edge rises toward the bow, so z1 is a per-station
     value, not a constant.
  3. SUPERSTRUCTURE riding on the deck: a deckhouse, a wheelhouse with a window
     band, a funnel, a mast. All boxes or lofts, all sunk 2 mm into the deck so
     nothing is exactly tangent to it.
  4. one part built at the origin, frozen, then repeated -- oars, propeller
     blades, frames, rails.

Units are millimetres everywhere, exactly as in bkit.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bkit
import bpy

# Points per side of one hull section. Ring size is 2*STEPS + TOP, constant for
# every station so the loft can bridge them.
STEPS = 20
TOP = 3


# --------------------------------------------------------------------------
# transforms
# --------------------------------------------------------------------------

def freeze(ob):
    """Bake location/rotation/scale into the mesh data and reset the origin.

    `bkit.duplicate()` SETS location. A part that still carries a location
    (cylinder/lathe/tube go through `place()`) therefore lands at
    `mesh_coords + offset`, which is the offset twice. Freeze first, always.
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


# --------------------------------------------------------------------------
# hull
# --------------------------------------------------------------------------

def _half(t, hw, hb):
    """Half width of one side at normalised depth t: 0 = sheer, 1 = keel.

    The topsides run nearly VERTICAL down to t=tb and then turn hard into the
    bilge. That matters for more than looks: a topside that narrows as it
    drops has an outward normal that points upward, so any predicate of the
    form "faces pointing up inside the boat get the interior material" also
    paints the flanks and the boat comes out two-tone the wrong way round.
    """
    tb = 0.70                      # where the topsides turn into the bilge
    if t < tb:
        u = t / tb
        return hw + (hb - hw) * (u ** 2.6)
    u = (t - tb) / (1.0 - tb)
    return hb * (1.0 - u ** 0.62)


def section(x, hw, z0, z1, k=0.55):
    """One closed hull ring at station `x`, in millimetres.

    hw  half beam at the sheer, z0 keel (or bottom) height, z1 sheer (deck
    edge) height, k  bottom half-beam as a fraction of hw. k=0.95 is a barge,
    k=0.30 a round-bilge tender.
    """
    hb = hw * k
    d = z1 - z0
    pts = []
    for i in range(STEPS + 1):                       # starboard, sheer -> keel
        t = i / float(STEPS)
        pts.append((x, _half(t, hw, hb), z1 - d * t))
    for i in range(STEPS - 1, -1, -1):               # port, keel -> sheer
        t = i / float(STEPS)
        pts.append((x, -_half(t, hw, hb), z1 - d * t))
    for j in range(1, TOP):                          # close across the deck
        pts.append((x, -hw + 2.0 * hw * j / TOP, z1))
    return pts


def hull(name, stations, mat=None, smooth=38.0, k=0.55):
    """Loft `(x, half_beam, z_keel, z_sheer, [k])` stations into one hull.

    A single loft along X is what gives a boat its profile -- sheer rise, bow
    entry, transom -- which is the thing the side render is judged on. Splitting
    "hull" and "topsides" into two lofts makes the join line show in every
    three-quarter view.
    """
    secs = []
    for s in stations:
        x, hw, z0, z1 = s[0], s[1], s[2], s[3]
        kk = s[4] if len(s) > 4 else k
        secs.append(section(x, hw, z0, z1, kk))
    ob = bkit.loft(name, secs, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, smooth)
    return ob


def hull_open(name, stations, wall=8.0, mat=None, mat_in=None, k=0.55):
    """A hull with the cockpit cut out of it -- canoes, kayaks, skiffs.

    A closed loft ring always carries a lid, so an open boat is a solid hull
    minus a cavity. The cavity is lofted from the SAME stations inset by
    `wall`, with its sheer lifted well above the deck so the top opens, and
    every inset is clamped so the inner surface never reaches the outer one.
    That 1 mm+ clearance is what keeps the EXACT solver from answering a
    near-tangent cut with bad edges.

    Faces left inside the boat are painted `mat_in`, which is what makes the
    cockpit read as an opening from the top view instead of a dark stripe.
    """
    secs = []
    for s in stations:
        x, hw, z0, z1 = s[0], s[1], s[2], s[3]
        kk = s[4] if len(s) > 4 else k
        secs.append(section(x, hw, z0, z1, kk))
    ob = bkit.loft(name, secs, mat=mat)
    bkit.recalc(ob)

    inner = []
    for s in stations:
        x, hw, z0, z1 = s[0], s[1], s[2], s[3]
        kk = s[4] if len(s) > 4 else k
        ihw = max(hw - wall, 1.5)
        iz0 = z0 + wall
        inner.append(section(x, ihw * 0.92, iz0, z1 + 80.0,
                             max(0.12, min(kk, kk - 0.30))))
    cut = bkit.loft(name + "_cavity", inner)
    bkit.recalc(cut)
    bkit.boolean(ob, cut, "DIFFERENCE")
    bkit.recalc(ob)
    if mat_in is not None:
        sheer = max(s[3] for s in stations)
        bkit.assign_faces_by(ob, mat_in,
                             lambda c, n: (c.z / bkit.MM < sheer - wall * 0.5
                                           and n.z > 0.55))
    bkit.shade_smooth(ob, 38.0)
    return ob


def deckhouse(name, x0, x1, hw, z0, z1, mat, r=None, mat_glass=None,
              glass_z=None, steps=48, n=4.0, glass_half=None):
    """A lofted deckhouse / wheelhouse block that sits on the deck.

    `n` above 6 is a genuinely boxy superstructure; 3.5 gives a rounded,
    smaller-vessel house. Glass, when asked for, is assigned to the faces whose
    centres sit in the window band and whose normal is not vertical.
    """
    stations = []
    for (x, w, kk) in ((x0 + 40.0, hw * 0.80, 0.55),
                       (x0 + 260.0, hw * 0.97, 0.9),
                       (x1 - 260.0, hw * 0.97, 0.9),
                       (x1 - 40.0, hw * 0.80, 0.55)):
        if x1 - x0 < 700.0:
            break
        stations.append((x, w, z0 - 40.0, z1, n))
    if len(stations) < 4:
        stations = [(x0, hw * 0.92, z0 - 40.0, z1, n),
                    (x1, hw * 0.92, z0 - 40.0, z1, n)]
    rings = []
    for (x, w, z0, z1, n) in stations:
        r = bkit.superellipse_section(z1 - (z0 - 40.0), 2.0 * w, n=n,
                                     steps=steps,
                                     centre=(0.5 * (z1 + z0) - 20.0, 0.0))
        rings.append([(x, p[1], p[0]) for p in r])
    ob = bkit.loft(name, rings, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, 30.0)
    if mat_glass is not None:
        lo, hi = glass_z or (z0 + (z1 - z0) * 0.55, z0 + (z1 - z0) * 0.86)
        window_band(ob, lo, hi, mat_glass, x_lo=x0, x_hi=x1)
    return ob


def window_band(ob, z_lo, z_hi, mat, max_nz=0.8, x_lo=None, x_hi=None,
                y_half=None):
    """Paint the near-vertical faces in a z band as glass.

    `assign_faces_by` hands the predicate a world-space centre in METRES, so
    the comparison is back in millimetres here.
    """
    def pred(c, n):
        z = c.z / bkit.MM
        x = c.x / bkit.MM
        y = c.y / bkit.MM
        if not (z_lo <= z <= z_hi) or abs(n.z) > max_nz:
            return False
        if x_lo is not None and x < x_lo:
            return False
        if x_hi is not None and x > x_hi:
            return False
        if y_half is not None and abs(y) < y_half:
            return False
        return True
    return bkit.assign_faces_by(ob, mat, pred)


def funnel(name, x, y, z0, h, r0, r1=None, mat=None, seg=28, lean=0.0):
    """A funnel: a slightly tapered cylinder, optionally raked aft."""
    ob = bkit.cylinder(name, r0, h, r2=r1 if r1 is not None else r0 * 0.88,
                       segments=seg, centre=(x, y, z0 + h / 2.0), mat=mat)
    if lean:
        ob.rotation_euler = (0.0, math.radians(lean), 0.0)
        bkit.move(ob, 0.0, 0.0, -h * 0.5)
        bkit.move(ob, 0.0, 0.0, h * 0.5)
    return ob


def blade(name, span, chord, thick, mat, seg=10, twist_deg=0.0):
    """One propeller / impeller blade: a tapered aerofoil on an X-axis shaft.

    The profile is written in (chord, radius) and extruded along X, because
    `extrude_profile(..., axis="X")` maps profile-x -> world -Z (tangential),
    profile-y -> world +Y (radial) and the extrusion -> world X (axial). Get
    that mapping wrong and the blade comes out as a slab with no chord at all.

    Built at the origin, so `array_radial(..., axis="X")` sweeps it round a
    fore-and-aft shaft.
    """
    pts = []
    for i in range(seg + 1):                       # leading edge, root -> tip
        t = i / float(seg)
        r = 0.12 * span + t * 0.88 * span
        c = chord * (0.62 + 0.38 * (1.0 - t) ** 0.8)
        pts.append((c * 0.5, r))
    for i in range(seg, -1, -1):                   # trailing edge, tip -> root
        t = i / float(seg)
        r = 0.12 * span + t * 0.88 * span
        c = chord * (0.62 + 0.38 * (1.0 - t) ** 0.8)
        pts.append((-c * 0.5, r))
    ob = bkit.extrude_profile(name, pts, thick, axis="X", mat=mat)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def propeller(name, dia, blades, hub_dia, mat, hub_mat=None, chord=None,
              thick=None, pitch=0.42):
    """A screw propeller on an X axis, centred on the origin.

    Dia is the swept diameter, so a `diameter` check on this part reads the
    propeller size directly. The blade therefore runs from the hub's own radius
    out to the FULL dia/2 tip circle -- measuring the span as `dia/2 - hub_r`
    put the tips at dia/2 - hub_r, so the swept circle came out one hub short
    (242 mm on a declared 360 mm screw).
    """
    hub_r = hub_dia / 2.0
    # blade() sweeps r from 0.12*span to span, so span is the tip radius. Add
    # the hub radius on so the root starts at the hub face and the tip lands
    # exactly on the dia/2 circle.
    span = dia / 2.0
    c = chord if chord is not None else dia * pitch
    t = thick if thick is not None else dia * 0.035
    b = blade(name + "_Blade", span, c, t, mat)
    bkit.array_radial(b, blades, axis="X")
    hub = bkit.lathe(name + "_Hub",
                     [(0.0, -hub_dia * 0.55), (hub_r, -hub_dia * 0.55),
                      (hub_r, hub_dia * 0.55), (0.0, hub_dia * 0.55)],
                     segments=32, cap_ends=True,
                     mat=hub_mat or bkit.preset("brushed_metal"))
    bkit.place(hub, (0.0, 0.0, 0.0), "X")
    freeze(hub)
    ob = bkit.join([b, hub], name)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def foil(name, span, root_chord, tip_chord, thick, mat, x=0.0):
    """A symmetric foil section extruded along Z -- a keel, rudder or skeg.

    Returns the object at the origin, frozen, so the caller can place it with
    `move()` or repeat it.
    """
    pts = []
    n = 14
    for i in range(n + 1):
        t = i / float(n)
        c = root_chord + (tip_chord - root_chord) * t
        pts.append((c * 0.5 * (0.30 + 0.70 * math.sin(math.pi * min(1.0, t * 1.2 + 0.05))),
                    t * span))
    for i in range(n, -1, -1):
        t = i / float(n)
        c = root_chord + (tip_chord - root_chord) * t
        pts.append((c * 0.5 * (0.30 + 0.70 * math.sin(math.pi * min(1.0, t * 1.2 + 0.05)))
                    * -1.0, t * span))
    ob = bkit.extrude_profile(name, pts, thick, axis="Y", mat=mat)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def rail_bulwark(name, stations, mat, h=180.0, t=40.0, tag="P"):
    """A stanchion-and-rail guard rail along a deck edge."""
    parts = []
    prof = [(x, 0.0) for (x, _y) in stations]
    for i, (x, y) in enumerate(stations):
        parts.append(bkit.cylinder("%sStanchion%02d" % (name, i), t / 2.0, h,
                                   segments=10, centre=(x, y, h / 2.0), mat=mat))
    for i in range(len(stations) - 1):
        a, b = stations[i], stations[i + 1]
        parts.append(strut("%sRail%02d" % (name, i), (a[0], a[1], h - 20.0),
                           (b[0], b[1], h - 20.0), t * 0.35, mat, 8))
    ob = bkit.join(parts, name)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob
