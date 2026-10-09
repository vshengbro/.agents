"""
watering_can -- a 10 L galvanised watering can: body, spout, rose, handle.

A watering can is a VESSEL plus a long SPOUT plus a top handle, and the spout
rising from the base is what makes it pour from the bottom of the can rather
than tipping the whole thing over. The can is a `lathe` on a closed profile
with a real wall, the rose is a perforated plate at the spout tip, and the handle
is an `arc_torus` closing on the rim.

    body      300 mm dia, 380 mm tall, 2 mm galvanised sheet
    spout      a 32 mm tube rising at 68 deg from the base to the rim
    rose       a 90 mm perforated rose on the spout tip
    handle     a 6 mm rod arcing over the top, landing on the rolled rim
    filler     a 60 mm opening in the rim opposite the spout

Real 10 L can: 300 mm body, 380 mm tall, 500 mm overall with the spout.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_dia=300.0,
    body_height=380.0,
    wall=2.0,
    spout_dia=32.0,
    # steep: the can is 380 tall, so a shallow spout that reaches the rim height
    # projects ~490 mm from the centreline and makes the can 700 mm long
    spout_angle_deg=68.0,
    rose_dia=90.0,
    handle_dia=12.0,
    overall_length=500.0,
)

BD = SPEC["body_dia"]
RB = BD / 2.0
BH = SPEC["body_height"]
WALL = SPEC["wall"]
SD = SPEC["spout_dia"]

# ---- the closed can profile: base, side, rolled rim, inner wall --------
# The profile already starts and ends on the axis, which is what closes the
# lathe. Appending the first point AGAIN emits a second ring of 48 coincident
# vertices at the base pole and costs a non-manifold edge.
PROF = [
    (0.0, 0.0),
    (RB - 6.0, 0.0),        # the base is dished slightly inward
    (RB, 14.0),             # the base knuckle
    (RB, BH - 18.0),        # the side wall
    (RB + 8.0, BH - 18.0),  # the rolled rim, turned out
    (RB + 8.0, BH),
    (RB - WALL, BH),        # back down the inside of the rim
    (RB - WALL, 16.0),
    (0.0, 16.0),
]

CHECKS = [
    dict(name="body_dia", mm=316.0, tol=3.0, how="diameter", part="CanBody"),
    dict(name="body_height", mm=380.0, tol=3.0, how="bbox_z", part="CanBody"),
    # the spout is a tilted tube, so bbox_x is its LENGTH: the across-flats
    # diameter is its Y extent and nothing else
    dict(name="spout_dia", mm=32.0, tol=2.0, how="bbox_y", part="CanSpout"),
    dict(name="rose_dia", mm=90.0, tol=3.0, how="diameter", part="CanRose"),
    dict(name="overall_length", mm=500.0, tol=10.0, how="bbox_x", part=None),
]


def build():
    galv = bkit.pbr("CanGalv", base=(0.72, 0.73, 0.75), metal=0.84, rough=0.30)
    brass = bkit.preset("gold")

    body = bkit.lathe("CanBody", PROF, segments=48, centre=(0.0, 0.0, 0.0),
                      mat=galv, cap_ends=False)
    bkit.recalc(body)
    bkit.weld(body)

    # ---- the spout, rising from the base ----------------------------
    # The spout leaves the body at the BASE and rises to the rim: that is what
    # lets a full can be emptied standing still.
    ang = math.radians(SPEC["spout_angle_deg"])
    tip_x = RB + (BH - 40.0) / math.tan(ang)
    tip_z = BH - 40.0
    from mathutils import Vector
    a = Vector((RB - 20.0, 0.0, 40.0))
    b = Vector((tip_x, 0.0, tip_z))
    d = b - a
    spout = bkit.cylinder("CanSpout", SD / 2.0, d.length, segments=24,
                          mat=galv)
    spout.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    spout.location = bkit.v(*(0.5 * (a + b)))
    bpy_update()

    # ---- the rose: a perforated plate on the spout tip --------------
    rose = bkit.cylinder("CanRose", SPEC["rose_dia"] / 2.0, 14.0, segments=32,
                         centre=(tip_x + 8.0, 0.0, tip_z + 8.0), mat=brass)
    # the spray holes, on a computed grid
    for (hx, hy) in bkit.grid_positions(cols=3, rows=3, pitch_x=22.0,
                                        pitch_y=22.0):
        bkit.bore(rose, 3.0, 40.0, centre=(tip_x + 8.0 + hx, hy,
                                           tip_z + 8.0), axis="Z",
                  host_segments=64)

    # ---- the top handle: an arc whose ends land ON the rolled rim ---------
    # The ends have to fall on the rim's top face (radius 148..158) or they
    # hang inside the can's mouth, so the major radius comes from that and the
    # centre height is derived so the ends sit 3 mm into the rim.
    HR = 155.0
    HZ = (BH - 3.0) - HR * math.sin(math.radians(8.0))
    bkit.arc_torus("CanHandle", HR, SPEC["handle_dia"] / 2.0, 8.0, 172.0,
                   centre=(0.0, 0.0, HZ), plane="XZ", seg_minor=14,
                   mat=galv)

    return dict(spec=SPEC, parts=4, capacity_litres=10)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()