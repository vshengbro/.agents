"""
Shared rolling-stock construction for the vehicles_rail domain.

Every vehicle in this domain is the same five decisions:

  1. THE FLOOR DATUM IS THE RAIL HEAD, and a wheel's tread rests EXACTLY on it.
     Every wheelset is therefore placed at z = dia/2, which makes
     `sit_on_floor()` a no-op -- and makes every `top_z` CHECKS entry read
     straight off the model instead of shifted by however much the seat moved
     the whole assembly. Authoring a wheel 50 mm proud of the rails is what
     drags the entire vehicle up with it.
  2. GEOMETRY IS COMPUTED, NEVER HAND-PLACED. Axle x positions come from
     `axles()` off a bogie wheelbase; sleeper rows come from
     `array_linear(..., world=True)`; buffer pairs come from a buffer-centre
     pitch. A three-wheel-per-side vehicle reads as broken instantly, and a
     hand-placed fourth wheel is how that happens.
  3. BODIES ARE LOFTED over `car_ring`, not raw boxes: vertical flanks with a
     separately-controlled roof arc, and stations along X, so the nose rake and
     the roof line live in the side silhouette where they are judged.
  4. THE UNDERFRAME IS THE DETAIL. Solebars, headstocks, buffers, steps, battery
     boxes and air reservoirs are what separate a railway wagon from a
     container sitting on four circles.
  5. SYMMETRY IS A MODIFIER, not a second hand-placed copy. `mirror_y()`
     freezes first, because a Mirror modifier works through the object's LOCAL
     origin and an un-frozen primitive mirrors through its own centre.

Units are millimetres everywhere, exactly as in bkit.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit
import bpy

# Standard gauge: inner face of one rail head to inner face of the other.
GAUGE = 1435.0
# (1435 + 70) / 2 -- the centreline of each rail head.
RAIL_Y = 752.5
# Railway wheels are narrower than road wheels and have the same centre offset.
WHEEL_Y = 752.5
TREAD = 135.0
# How far the flange stands proud of the tread.
FLANGE = 28.0
# z of the RAIL HEAD plane when the flange tips rest on z=0. A real wheel's
# lowest point is its flange, not its tread, so if the tread were authored on
# z=0 the whole vehicle would hang 28 mm high and `sit_on_floor()` would drag
# every single part down by 28 mm. Quoting every height against the railhead --
# buffers at 1065 mm, floors at 1100 mm -- and adding this on the way in keeps
# both the datum and the quoted numbers honest.
RAILHEAD = FLANGE


def wheel_r(dia, flange=FLANGE):
    """Axle height above z=0: the radius to the flange tip, not the tread."""
    return dia / 2.0 + flange


def above_rail(h):
    """Convert a height quoted above the railhead into a build-frame z."""
    return h + RAILHEAD


# --------------------------------------------------------------------------
# transforms
# --------------------------------------------------------------------------

def freeze(ob):
    """Bake location/rotation/scale into the mesh data and reset the origin.

    `bkit.duplicate()` SETS location, and the Mirror modifier works through the
    local origin, so anything that will be repeated or mirrored must be frozen.
    """
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    ob.select_set(False)
    return ob


def shift(objs, dx=0.0, dy=0.0, dz=0.0):
    """Move a list of objects by millimetres (never by raw `.location`)."""
    out = []
    for o in objs:
        if o is None:
            continue
        bkit.move(o, dx, dy, dz)
        out.append(o)
    return out


def strut(name, p0, p1, r, mat=None, seg=16, r2=None):
    """A round tube between two arbitrary points, in millimetres."""
    import mathutils
    a = mathutils.Vector(p0)
    b = mathutils.Vector(p1)
    d = b - a
    ob = bkit.cylinder(name, r, d.length, segments=seg, mat=mat, r2=r2)
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    ob.location = bkit.v(*(0.5 * (a + b)))
    # matrix_world is CACHED. Without this, a strut that happens to be the last
    # thing built in build() still reads its pre-move transform, so bbox()
    # reports it centred on the world origin -- and `sit_on_floor()` then seats
    # the whole assembly off a phantom that is not there.
    bpy.context.view_layer.update()
    return ob


def mirror_y(obj, name=None):
    """Mirror across the Y=0 centreline, keeping it as ONE object."""
    freeze(obj)
    bkit.mirror(obj, "Y")
    if name:
        obj.name = name
    return obj


# --------------------------------------------------------------------------
# wheels and running gear
# --------------------------------------------------------------------------

def _one_wheel(tag, y_centre, dia, tread, flange, seg, rim_mat, steel_mat):
    """One flanged railway wheel: rim, web, hub and bearing boss.

    The flange is on the INBOARD face and is what actually keeps the wheel on
    the rail; it is 28 mm proud of the tread, so in the side view the wheel
    shows a flat tread circle and in the three-quarter it shows the lip.

    `lathe()` revolves (radius, z) about Z and `place(..., "Y")` then maps
    local +z to world -y, so a profile written in world y has to be NEGATED on
    the way in. Without that, both wheels of a wheelset land on the same side
    of the centreline and the whole thing is quietly one-sided.
    """
    rt = dia / 2.0
    rf = rt + flange
    rw = rt - 70.0                       # rim bore / web outer radius
    hw = tread / 2.0
    # `sg` points from the wheel towards the vehicle centreline. The section is
    # written once with the flange on the +y side and mirrored for the other
    # wheel by flipping every y offset -- two hand-written mirror-image
    # profiles is how one wheel silently ends up on the wrong side.
    sg = 1.0 if y_centre < 0.0 else -1.0
    y_in = y_centre + sg * hw
    y_out = y_centre - sg * hw

    prof_world = [
        (rw, y_out + sg * 14.0),        # outboard end of the inner bore
        (rf, y_out + sg * 26.0),        # flange root
        (rf, y_in - sg * 26.0),         # flange tip band
        (rt, y_in - sg * 4.0),          # taper back down to the tread
        (rt, y_in + sg * 8.0),          # THE TREAD
        (rt - 6.0, y_out),              # outboard chamfer
        (rw, y_in - sg * 18.0),         # inner bore
        (rw, y_out + sg * 14.0),        # close on the first point
    ]
    prof = [(r, -y) for (r, y) in prof_world]
    rim = bkit.lathe("Wheel%s_Rim" % tag, prof, segments=seg, cap_ends=False,
                     mat=rim_mat)
    bkit.place(rim, (0.0, 0.0, 0.0), "Y")
    web = bkit.cylinder("Wheel%s_Web" % tag, rw + 20.0, 55.0, segments=seg,
                        axis="Y", centre=(0.0, y_centre, 0.0), mat=steel_mat)
    hub = bkit.cylinder("Wheel%s_Hub" % tag, 95.0, 190.0, segments=24,
                        axis="Y", centre=(0.0, y_centre - 15.0, 0.0),
                        mat=steel_mat)
    boss = bkit.cylinder("Wheel%s_Boss" % tag, 50.0, 60.0, segments=20,
                         axis="Y", centre=(0.0, y_centre + 75.0, 0.0),
                         mat=steel_mat)
    ob = bkit.join([rim, web, hub, boss], "Wheel%s" % tag)
    bkit.recalc(ob)
    return ob


def wheelset(name, dia=920.0, tread=TREAD, flange=FLANGE, seg=48,
             wheel_y=WHEEL_Y, mat_rim=None, mat_steel=None):
    """One axle with a flanged wheel each side, built and frozen at the origin.

    The tread plane sits `flange` mm above z=0, so placing the axle at
    `wheel_r(dia)` puts the FLANGE TIPS -- the vehicle's true lowest points --
    exactly on the floor datum. `wheel_y` is the wheel centre offset, so
    standard gauge is the default and a mine car is the same call at 300 mm.
    """
    rim_mat = mat_rim or bkit.preset("steel")
    steel_mat = mat_steel or bkit.preset("dark_metal")
    left = _one_wheel("L", -wheel_y, dia, tread, flange, seg, rim_mat, steel_mat)
    right = _one_wheel("R", wheel_y, dia, tread, flange, seg, rim_mat, steel_mat)
    axle = bkit.cylinder(name + "_Axle", min(78.0, dia * 0.19),
                         2.0 * (wheel_y + tread / 2.0 + 200.0),
                         segments=24, axis="Y", centre=(0.0, 0.0, 0.0),
                         mat=steel_mat)
    ob = bkit.join([left, right, axle], name)
    bkit.recalc(ob)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def axles(name, ws, xs, r):
    """Repeat one wheelset at an ARBITRARY list of axle positions.

    The list must not be assumed evenly spaced: four axles on two two-axle
    bogies have a 2,000 mm pitch inside each bogie and a 5,000 mm gap between
    them, so `array_linear` off `xs[1] - xs[0]` puts the inner axle half a
    bogie out of place. `duplicate()` SETS location, which for a frozen wheelset
    whose mesh is centred on the origin is exactly the absolute offset wanted,
    so every axle is placed from its own x.

    `r` is the axle height (`wheel_r(dia)`), so the flange tips land on z=0 and
    `sit_on_floor()` is a no-op.
    """
    xs = sorted(xs)
    ws.name = "%s_A1" % name
    bkit.move(ws, xs[0], 0.0, r)
    objs = [ws]
    for i, x in enumerate(xs[1:], start=2):
        objs.append(bkit.duplicate(ws, "%s_A%d" % (name, i),
                                   offset_mm=(x, 0.0, r)))
    ob = bkit.join(objs, name)
    bkit.recalc(ob)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def bogie(name, wheelbase, dia, mat_frame, mat_steel=None, frame_z=40.0,
          wheel_y=WHEEL_Y, tread=TREAD):
    """A two-axle bogie: side frames, axleboxes and a bolster, built at x=0.

    Returned at the ORIGIN with its axle axes at x = +/- wheelbase/2 and the
    axle centres at z = 0, so `bogie()` plus `axles()` plus one `shift()` puts a
    complete four-wheel bogie anywhere without a hand-placed coordinate.
    """
    steel = mat_steel or bkit.preset("dark_metal")
    hz = wheel_y + tread / 2.0 + 90.0      # side-frame plane, clear of the tyre
    parts = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        parts.append(bkit.rounded_box("Bogie%s_Frame" % tag,
                                      wheelbase + 900.0, 160.0, 300.0,
                                      r=60.0, segments=3,
                                      centre=(0.0, s * hz, frame_z),
                                      mat=mat_frame))
        for xs, atag in ((-wheelbase / 2.0, "F"), (wheelbase / 2.0, "R")):
            parts.append(bkit.rounded_box("Bogie%s_Axlebox%s" % (tag, atag),
                                          300.0, 200.0, 260.0, r=35.0,
                                          segments=2,
                                          centre=(xs, s * (hz - 80.0), 0.0),
                                          mat=steel))
    parts.append(bkit.rounded_box("BogieBolster", 460.0, 2.0 * hz, 210.0,
                                  r=50.0, segments=3,
                                  centre=(0.0, 0.0, frame_z + 240.0),
                                  mat=mat_frame))
    parts.append(bkit.cylinder("BogiePivot", 240.0, 180.0, segments=28,
                               axis="Z", centre=(0.0, 0.0, frame_z + 420.0),
                               mat=steel))
    ob = bkit.join(parts, name)
    bkit.recalc(ob)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def brake_cylinder(name, x, y, z, mat, r=180.0, length=700.0):
    """A bogie-mounted brake cylinder -- small, and it says 'railway'."""
    return bkit.cylinder(name, r, length, segments=24, axis="X",
                         centre=(x, y, z), mat=mat)


# --------------------------------------------------------------------------
# bodies
# --------------------------------------------------------------------------

def raked_panel(name, sx, sy, sz, angle_deg, axis="X", centre=(0, 0, 0),
                r=12.0, mat=None):
    """A panel tilted about X or Y -- hopper slopes, raked legs, boom struts.

    `rounded_box()` bakes its centre into the mesh and leaves the object at
    the origin, so setting `rotation_euler` pivots it about its OWN centre and
    `move()` then carries it to the right place. Rotate a primitive that is
    still sitting at `place()`'s location and it pivots about the world origin
    instead, which throws the panel off the vehicle entirely.
    """
    ob = bkit.rounded_box(name, sx, sy, sz, r=r, segments=2, mat=mat)
    ob.rotation_euler = (math.radians(angle_deg) if axis == "X" else 0.0,
                         math.radians(angle_deg) if axis == "Y" else 0.0,
                         0.0)
    bpy.context.view_layer.update()
    bkit.move(ob, *centre)
    return ob


def running_gear(name, dia, bogie_x, bogie_wb, mat_frame=None, mat_steel=None,
                 brake=True, frame_z_off=40.0, wheel_y=WHEEL_Y, flange=FLANGE):
    """Wheelsets, bogie frames and brake cylinders for a railway vehicle.

    `bogie_x` is ONE bogie centre (four axles) or a LIST of them (a diesel
    locomotive on three two-axle bogies, a tram on three four-axle bogies).
    Wheel count and bogie centres are the whole read of a rail vehicle: a
    three-wheel-per-side arrangement or loose axles with no bogie frame reads
    as broken instantly, and both are what you get from hand-placing wheels.

    Returns the joined axle object, which is the part that carries the flange
    datum check.
    """
    steel = mat_steel or bkit.preset("dark_metal")
    frame_m = mat_frame or bkit.preset("dark_metal")
    centres = [bogie_x] if not isinstance(bogie_x, (list, tuple)) \
        else list(bogie_x)
    r = wheel_r(dia, flange)
    axle_x = sorted([s * bx + w * bogie_wb / 2.0
                     for bx in centres for s in (-1.0, 1.0)
                     for w in (-1.0, 1.0)])
    ax = axles("%sAxles" % name,
               wheelset("%sWheel" % name, dia=dia, seg=48, wheel_y=wheel_y,
                        flange=flange, mat_steel=steel),
               axle_x, r)
    for i, bx in enumerate(centres):
        tag_i = "" if len(centres) == 1 else str(i)
        for s, tag in ((1.0, "F"), (-1.0, "R")):
            ob = bogie("%sBogie%s%s" % (name, tag_i, tag), bogie_wb, dia,
                       frame_m, steel, frame_z=r + frame_z_off,
                       wheel_y=wheel_y)
            bkit.move(ob, s * bx, 0.0, r)
            if brake:
                brake_cylinder("%sBrakeCyl%s%s" % (name, tag_i, tag), s * bx,
                               0.0, r + 470.0, steel, r=170.0, length=620.0)
    return ax


def car_ring(x, hw, z0, z1, shoulder=None, n_side=4, n_roof=10):
    """One closed body cross-section at station `x`.

    Flat floor, vertical flanks, then a circular roof arc from `shoulder` to
    `z1`. A coach is NOT a superellipse: the flank has to be dead vertical so
    the window band lands on flat glass, and the roof radius is chosen
    independently of the body height. The vertex count is
    `2*n_side + n_roof + 2` for every station, which is what lets `loft()`
    bridge them.
    """
    sh = shoulder if shoulder is not None else z1 - (z1 - z0) * 0.24
    sh = max(sh, z0 + 40.0)
    rise = max(z1 - sh, 1.0)
    pts = []
    for i in range(n_side + 1):                       # starboard, floor -> shoulder
        t = i / float(n_side)
        pts.append((x, hw, z0 + (sh - z0) * t))
    for i in range(1, n_roof):                        # roof, over the top
        a = math.pi * i / n_roof
        pts.append((x, hw * math.cos(a), sh + rise * math.sin(a)))
    for i in range(n_side, -1, -1):                   # port, shoulder -> floor
        t = i / float(n_side)
        pts.append((x, -hw, z0 + (sh - z0) * t))
    pts.append((x, 0.0, z0))                          # close across the floor
    return pts


def body(name, stations, mat=None, smooth=40.0):
    """Loft `(x, hw, z0, z1, [shoulder])` stations into one closed body."""
    secs = []
    for s in stations:
        sh = s[4] if len(s) > 4 else None
        secs.append(car_ring(s[0], s[1], s[2], s[3], shoulder=sh))
    ob = bkit.loft(name, secs, mat=mat)
    bkit.recalc(ob)
    bkit.shade_smooth(ob, smooth)
    return ob


def window_band(ob, z_lo, z_hi, mat, max_nz=0.72, x_lo=None, x_hi=None,
                y_half=None):
    """Paint the near-vertical faces of a body as glass.

    `assign_faces_by` hands the predicate a world-space centre in METRES, so
    the comparisons here are back in millimetres.
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


# --------------------------------------------------------------------------
# underframe
# --------------------------------------------------------------------------

def solebar(name, length, y, z, h=300.0, t=60.0, mat=None, r=12.0):
    """One longitudinal solebar / angle-iron edge member."""
    return bkit.rounded_box(name, length, t, h, r=r, segments=2,
                            centre=(0.0, y, z), mat=mat)


def buffers(name, x_face, z=1065.0, pitch=1750.0, mat_body=None, mat_head=None):
    """Two sprung buffers and a coupling hook, facing outward from `x_face`.

    Real: 450 mm heads, 1750 mm between buffer centres, 1065 mm above the
    railhead. `z` is quoted ABOVE RAIL so the caller cannot forget the flange
    offset, and `x_face` is the plane the buffer faces lie in -- so a vehicle's
    declared length is honest about its buffers rather than about its solebars.

    The assembly is BUILT facing outward, not merely moved to the face. It used
    to be authored once at negative X and then translated, and a translation
    cannot mirror: every rear-ended vehicle got a buffer set pointing back along
    its own body instead of out of its rear. The tell was exact -- all four rail
    vehicles measured 440 mm of end asymmetry, 440 being the pad depth, which a
    vehicle whose two ends come from the same call cannot have.

    So the direction is a build parameter. Every part here is centred on its own
    axis, so negating each X centre mirrors the assembly exactly, with no mirror
    modifier and no normal flip to get wrong.
    """
    body_m = mat_body or bkit.preset("dark_metal")
    head_m = mat_head or bkit.preset("steel")
    z = above_rail(z)
    d = 1.0 if x_face >= 0.0 else -1.0
    parts = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        y = s * pitch / 2.0
        parts.append(bkit.rounded_box(name + "_Pad" + tag, 240.0, 340.0, 330.0,
                                      r=30.0, segments=2,
                                      centre=(d * -320.0, y, z), mat=body_m))
        parts.append(bkit.cylinder(name + "_Shank" + tag, 90.0, 280.0,
                                   segments=20, axis="X",
                                   centre=(d * -170.0, y, z), mat=head_m))
        parts.append(bkit.cylinder(name + "_Head" + tag, 225.0, 110.0,
                                   segments=32, axis="X",
                                   centre=(d * -55.0, y, z), mat=head_m))
    parts.append(bkit.rounded_box(name + "_Hook", 320.0, 190.0, 270.0, r=45.0,
                                  segments=2, centre=(d * -160.0, 0.0, z),
                                  mat=body_m))
    ob = bkit.join(parts, name)
    bkit.recalc(ob)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    bkit.move(ob, x_face, 0.0, 0.0)
    return ob


def steps(name, x, y, z0, z1, mat, width=420.0, n=3, r=18.0):
    """A rung step hanging off a solebar: two stiles and `n` treads.

    The tread pitch is computed from the two stiles' own height, so the ladder
    can be re-used at any hanging height without editing a constant.
    """
    h = z1 - z0
    parts = []
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        parts.append(bkit.rounded_box("%s_Stile%s" % (name, tag), 60.0, 60.0, h,
                                      r=20.0, segments=2,
                                      centre=(x + s * (width / 2.0 - 30.0), y,
                                              z0 + h / 2.0), mat=mat))
    tread = 70.0
    gap = (h - tread) / float(n + 1)
    for (zc, _w) in bkit.lay_out([tread] * n, gap=gap, centre=False):
        parts.append(bkit.rounded_box("%s_Tread%d" % (name, int(zc)), 90.0,
                                      width, tread, r=r, segments=2,
                                      centre=(x, y, z0 + zc + tread / 2.0),
                                      mat=mat))
    ob = bkit.join(parts, name)
    bkit.recalc(ob)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def underframe(name, length, half_w=1450.0, z_bot=950.0, depth=300.0,
               mat=None, headstock_t=90.0):
    """A railway underframe: two solebars, a headstock at each end, a deck.

    This is the piece that makes a body read as rolling stock. The deck sits
    ON TOP of the solebars (1 mm overlap, never flush) and the headstocks close
    the frame at the buffer ends.
    """
    zc = z_bot + depth / 2.0
    deck = bkit.rounded_box(name + "_Deck", length - 2.0 * headstock_t,
                            2.0 * half_w, 40.0, r=8.0, segments=2,
                            centre=(0.0, 0.0, z_bot + depth - 20.0), mat=mat)
    parts = [deck]
    for s, tag in ((1.0, "L"), (-1.0, "R")):
        parts.append(solebar("%s_Solebar%s" % (name, tag), length,
                             s * (half_w - 30.0), zc, h=depth, t=60.0, mat=mat))
    for s, tag in ((1.0, "F"), (-1.0, "R")):
        parts.append(bkit.rounded_box("%s_Headstock%s" % (name, tag),
                                      headstock_t, 2.0 * half_w, depth, r=14.0,
                                      segments=2,
                                      centre=(s * (length / 2.0 - headstock_t / 2.0),
                                              0.0, zc), mat=mat))
    ob = bkit.join(parts, name)
    bkit.recalc(ob)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


def battery_box(name, x, y, z, mat, sx=1200.0, sy=520.0, sz=520.0):
    """An underframe equipment case."""
    return bkit.rounded_box(name, sx, sy, sz, r=40.0, segments=2,
                            centre=(x, y, z), mat=mat)


def air_reservoir(name, x, y, z, mat, r=230.0, length=1200.0):
    """A brake air reservoir under a wagon."""
    return bkit.cylinder(name, r, length, segments=28, axis="X",
                         centre=(x, y, z), mat=mat)


def handrail(name, p0, p1, mat, r=26.0):
    """A grab rail / handrail between two points."""
    return strut(name, p0, p1, r, mat, seg=12)


def spoked_ring(name, radius, spoke_n, axis="Z", rim_r=None, hub_r=None,
                spoke_w=50.0, spoke_t=50.0, mat=None, seg=32):
    """A spoked ring -- handbrake wheel, valve wheel, gear rim -- built at the
    ORIGIN and then moved by the caller.

    The spokes are OFFSET from the hub and swept with the hub at the origin,
    which is the only place `array_radial` needs no `centre` argument. Arraying
    a member that is already sitting at its final position and then handing
    `centre=` is how a five-spoke brake wheel becomes a 19 m starburst; and a
    spoke centred ON the origin arrayed five times is a star, not a wheel.
    """
    rim_r = rim_r if rim_r is not None else max(14.0, 0.10 * radius)
    hub_r = hub_r if hub_r is not None else max(30.0, 0.24 * radius)
    ring = bkit.torus(name + "_Rim", radius, rim_r, seg_major=seg,
                      seg_minor=max(8, seg // 3), centre=(0.0, 0.0, 0.0),
                      axis=axis, mat=mat)
    lo, hi = hub_r * 0.45, radius - rim_r * 0.45
    sp = bkit.rounded_box(name + "_Spoke", hi - lo, spoke_w, spoke_t,
                          r=min(spoke_w, spoke_t) * 0.3, segments=2,
                          centre=(0.5 * (lo + hi), 0.0, 0.0), mat=mat)
    bkit.array_radial(sp, spoke_n, axis=axis)
    hub = bkit.cylinder(name + "_Hub", hub_r, spoke_w * 1.6, segments=20,
                        axis=axis, centre=(0.0, 0.0, 0.0), mat=mat)
    ob = bkit.join([ring, sp, hub], name)
    bkit.recalc(ob)
    freeze(ob)
    ob.location = (0.0, 0.0, 0.0)
    return ob


# --------------------------------------------------------------------------
# permanent way
# --------------------------------------------------------------------------

def rail_profile(h=172.0, head_w=70.0, foot_w=150.0, web_w=16.0):
    """A flat-bottom rail cross-section, as `(y, z)` with the foot on z=0.

    60E1 proportions: 172 mm tall, 150 mm foot, 70 mm head. A rectangle would
    read as a bar of steel; the head/foot/web silhouette is what says 'rail'.
    """
    hh = h * 0.58
    fw = foot_w / 2.0
    hw = head_w / 2.0
    ww = web_w / 2.0
    return [
        (-fw, 0.0), (fw, 0.0), (fw, 13.0), (ww, 33.0), (ww, h - hh - 14.0),
        (hw, h - hh), (hw, h - 7.0), (hw - 8.0, h), (-hw + 8.0, h),
        (-hw, h - 7.0), (-hw, h - hh), (-ww, h - hh - 14.0), (-ww, 33.0),
        (-fw, 13.0),
    ]


def rail(name, length, centre_x=0.0, y=0.0, z0=0.0, h=172.0, mat=None):
    """One flat-bottom rail of `length` along X, foot resting on z=z0.

    `extrude_profile(..., axis="X")` maps profile-x -> world -Z and profile-y ->
    world +Y, so the section is fed in NEGATED to get the rail the right way
    up. Getting that mapping wrong silently produces a rail lying on its side.
    """
    prof = [(-z, yy) for (yy, z) in rail_profile(h=h)]
    ob = bkit.extrude_profile(name, prof, length, centre=(centre_x, y, z0),
                              axis="X", mat=mat)
    bkit.recalc(ob)
    return ob


def sleeper_row(name, count, pitch, length, sx=250.0, sz=200.0,
                x0=None, z0=0.0, mat=None, r=18.0):
    """A row of sleepers, tread down, arrayed in WORLD space.

    `world=True` is mandatory here: without it the Array modifier steps in the
    sleeper's own local frame, which for a member that has been rotated or
    mirrored walks the row somewhere else entirely. `z0` buries the row in the
    ballast, which is where concrete sleepers actually sit.
    """
    s = bkit.rounded_box(name, sx, length, sz, r=r, segments=2,
                         centre=(0.0, 0.0, sz / 2.0), mat=mat)
    if count > 1:
        bkit.array_linear(s, count, (pitch, 0.0, 0.0), world=True)
    if x0 is None:
        x0 = -(count - 1) * pitch / 2.0
    bkit.move(s, x0, 0.0, z0)
    s.name = name
    return s


def evenly(count, span, centre=True, start=0.0):
    """`count` positions spread first-to-last across `span` mm.

    The anti-hand-placing rule for a row of identical MEMBERS (stakes,
    stanchions, roof ribs) where `lay_out()` -- which spaces by widths plus one
    gap -- would force the row to be sized from its contents.

    `centre=True` (the default) puts the MIDDLE of the row at `start`;
    `centre=False` puts the FIRST position at `start`. Reading `start` as the
    first position while `centre` is on silently shifts the whole row by half
    its span -- which is how a tram's eight door leaves end up 24 m behind the
    tram, floating in mid-air.
    """
    if count < 2:
        return [start + (span / 2.0 if centre else 0.0)]
    step = span / float(count - 1)
    x0 = start + (-span / 2.0 if centre else 0.0)
    return [x0 + i * step for i in range(count)]


def ballast(name, length, top_w=3600.0, base_w=5200.0, height=250.0,
            mat=None):
    """A trapezoidal ballast prism: the only thing holding the track down."""
    # profile-x -> world -Z and profile-y -> world +Y, so the section is fed
    # in as (-z, y): x=0 at the ballast toe, x=-height at the shoulder.
    poly = [(0.0, -base_w / 2.0), (0.0, base_w / 2.0),
            (-height, top_w / 2.0), (-height, -top_w / 2.0)]
    ob = bkit.extrude_profile(name, poly, length, centre=(0.0, 0.0, 0.0),
                              axis="X", mat=mat)
    bkit.recalc(ob)
    return ob