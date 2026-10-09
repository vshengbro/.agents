"""
wheelbarrow_buckets -- a 10 litre grain bucket: 270 mm across, 225 mm tall.

A bucket is a lathe with a REAL WALL, not a solid cone with a second object
inside it: the profile runs up the outside, over the rim and back down the
inside to the floor, and both ends of that closed profile touch the axis so
`lathe` welds them into poles. One closed profile is one closed solid, so
there is nothing to z-fight.

The bail handle is TWO rods and a grip rather than an arc, because an arc long
enough to clear a 270 mm rim is taller than the bucket and would put the whole
object in the wrong size class.

Real 10 L grain bucket: 270 mm top diameter, 200 mm base, 225 mm tall, 3 mm
wall, 34 mm bail grip.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit
import bpy

SPEC = dict(
    top_diameter=270.0,
    base_diameter=204.0,
    height=225.0,
    wall=3.0,
    handle_span=265.6,
    handle_rise=60.0,
    grip_dia=22.0,
    grip_length=90.0,
    spout_reach=152.0,
)

RT = SPEC["top_diameter"] / 2.0
RB = SPEC["base_diameter"] / 2.0 - 4.0     # the moulded base ring adds 4 mm
H = SPEC["height"]
T = SPEC["wall"]

CHECKS = [
    dict(name="top_diameter", mm=270.0, tol=2.0, how="bbox_y",
         part="BucketBody"),
    dict(name="base_diameter", mm=204.0, tol=2.0, how="bbox_x",
         part="BucketBase"),
    dict(name="height", mm=225.0, tol=2.0, how="bbox_z", part="BucketBody"),
    dict(name="rim_outer_dia", mm=278.0, tol=2.0, how="bbox_x",
         part="BucketRim"),
    dict(name="handle_span", mm=265.6, tol=3.0, how="bbox_max",
         part="BucketBail"),
    dict(name="handle_rise", mm=60.0, tol=4.0, how="bbox_z",
         part="BucketBail"),
    dict(name="grip_length", mm=90.0, tol=2.0, how="bbox_y",
         part="BucketGrip"),
    dict(name="bucket_on_floor", mm=0.0, tol=2.0, how="z_min",
         part="BucketBody"),
]


def build():
    pp = bkit.pbr("BucketPoly", base=(0.72, 0.32, 0.05), rough=0.42)
    steel = bkit.preset("brushed_metal")

    # ---- the body: outside up, over the rim, back down the inside ------
    prof = [(0.0, 0.0), (RB, 0.0), (RT, H), (RT - T, H),
            (RB - T, T), (0.0, T)]
    bkit.lathe("BucketBody", prof, segments=56, mat=pp)

    # a rolled rim, as its own ring so the wall thickness is measurable
    bkit.tube("BucketRim", RT + 4.0, RT - T - 2.0, 14.0, segments=56,
              centre=(0.0, 0.0, H - 5.0), mat=pp)

    # a moulded base ring: what the bucket actually stands on
    bkit.lathe("BucketBase",
               [(0.0, 0.0), (RB + 4.0, 0.0), (RB + 4.0, 12.0),
                (RB - T, 14.0), (0.0, 14.0)], segments=56, mat=pp)

    # ---- the pouring spout, a pinched lip on one side -----------------
    bkit.extrude_profile("BucketSpout",
                         [(-40.0, 0.0), (40.0, 0.0), (24.0, 110.0),
                          (-24.0, 110.0)], 80.0,
                         centre=(112.0, 0.0, H - 30.0), axis="Z", mat=pp)

    # ---- the bail: two rods, two lugs, one grip -----------------------
    for s in (1, -1):
        bkit.cylinder("BucketLug%d" % (0 if s < 0 else 1), 11.0, 22.0,
                      segments=16, axis="X",
                      centre=(s * (RT - 4.0), 0.0, H - 22.0), mat=pp)
    from mathutils import Vector                                  # noqa: E402
    for s in (1, -1):
        p0 = Vector((s * (RT - 4.0), 0.0, H - 22.0))
        p1 = Vector((0.0, 0.0, H + 28.0))
        d = p1 - p0
        rod = bkit.cylinder("BucketBail", 5.0, d.length, segments=12,
                            mat=steel)
        rod.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        rod.location = bkit.v(*(0.5 * (p0 + p1)))
    bkit.join([o for o in bpy.data.objects
               if o.name.startswith("BucketBail")], name="BucketBail")
    bkit.cylinder("BucketGrip", 11.0, 90.0, segments=16, axis="Y",
                  centre=(0.0, 0.0, H + 28.0), mat=steel)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=8)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
