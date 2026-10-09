"""
watering_pivot -- an elevated single-pivot sprinkler head on a tripod, 1.2 m.

A pivot sprinkler is a HEAD on a riser: a tripod mast, the rotating nozzle
carriage, and four spray booms arrayed RADIALLY about the riser axis. The array
hub is not at the world origin by accident -- the riser stands at the origin, so
`centre` is passed explicitly anyway, because the next model that puts the unit
on a concrete pad will need it.

The booms carry two nozzles each, spaced along the boom rather than repeated by
eye, and the whole thing stands on three splayed feet so it reads as a field
unit rather than a lamp post.

Real market-garden pivot sprinkler: 1200 mm to the top of the head, 1000 mm boom
span, 100 mm riser, four booms at 90 deg.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _agri as A

SPEC = dict(
    head_height=1200.0,
    boom_span=1000.0,
    boom_tip_radius=500.0,
    riser_dia=100.0,
    riser_height=880.0,
    booms=4,
    boom_length=436.0,
    foot_radius=330.0,
    foot_pad=150.0,
    nozzles_per_boom=2,
    nozzle_pitch=240.0,
)

TOP = SPEC["head_height"]
BOOM_L = SPEC["boom_length"]
HEAD_C = (0.0, 0.0, 1150.0)      # the hub the booms orbit about

CHECKS = [
    dict(name="head_height", mm=1200.0, tol=6.0, how="top_z", part="PivotHead"),
    dict(name="boom_span", mm=1000.0, tol=8.0, how="bbox_y", part="PivotBooms"),
    dict(name="boom_tip_radius", mm=500.0, tol=8.0, how="x_max",
         part="PivotBooms"),
    dict(name="riser_dia", mm=100.0, tol=2.0, how="bbox_x", part="PivotRiser"),
    dict(name="foot_pad", mm=150.0, tol=2.0, how="bbox_x", part="PivotFoot0"),
    dict(name="foot_on_floor", mm=0.0, tol=2.0, how="z_min", part="PivotFoot0"),
]


def build():
    galv = bkit.preset("brushed_metal")
    dark = bkit.preset("dark_metal")
    brass = bkit.pbr("PivotBrass", base=(0.80, 0.64, 0.30), metal=0.85,
                     rough=0.26)

    # ---- the tripod: three legs from a ring of feet to the mast ---------
    # the legs start at z=14, not z=0: a cylinder laid on a slant dips r*sin
    # below its endpoint, and an 8 mm dip lifts the whole model 8 mm when
    # `sit_on_floor` seats it, which then breaks every absolute z check.
    foot_r = SPEC["foot_radius"]
    for i in range(3):
        a = math.radians(90.0 + 120.0 * i)
        fx, fy = foot_r * math.cos(a), foot_r * math.sin(a)
        A.tube_between("PivotLeg%d" % i, (fx, fy, 14.0),
                       (0.0, 0.0, 840.0), 22.0, mat=galv)
        bkit.rounded_box("PivotFoot%d" % i, SPEC["foot_pad"], SPEC["foot_pad"],
                         40.0, r=10.0, segments=2, centre=(fx, fy, 20.0),
                         mat=dark)

    # ---- the riser and the rotating head -------------------------------
    bkit.cylinder("PivotRiser", 50.0, SPEC["riser_height"], segments=24,
                  centre=(0.0, 0.0, SPEC["riser_height"] / 2.0), mat=galv)
    bkit.tube("PivotRiserCollar", 62.0, 50.0, 90.0, segments=24,
              centre=(0.0, 0.0, 700.0), mat=dark)
    bkit.lathe("PivotHead",
               [(0.0, 0.0), (86.0, 0.0), (86.0, 30.0), (64.0, 42.0),
                (64.0, 50.0), (0.0, 50.0)],
               segments=28, centre=HEAD_C, mat=dark)

    # ---- four spray booms, arrayed about the HEAD, not the origin ------
    # the orbit radius lives in the MESH: `array_radial` works on local
    # coordinates, so a boom positioned by `obj.location` sweeps no ring.
    boom = bkit.rounded_box("PivotBooms", BOOM_L, 26.0, 26.0, r=10.0,
                            segments=2,
                            centre=(64.0 + BOOM_L / 2.0, 0.0, HEAD_C[2]),
                            mat=galv)
    bpy.context.view_layer.update()
    bkit.array_radial(boom, SPEC["booms"], axis="Z", centre=HEAD_C)

    # ---- two nozzles per boom, on the boom's own pitch -----------------
    nozzle = bkit.lathe("PivotNozzles",
                        [(0.0, 0.0), (17.0, 0.0), (17.0, 26.0), (9.0, 40.0),
                         (0.0, 40.0)], segments=16, mat=brass)
    A.place_in_mesh(nozzle, 197.0, 0.0, HEAD_C[2] - 40.0)
    bpy.context.view_layer.update()
    bkit.array_radial(nozzle, SPEC["booms"], axis="Z", centre=HEAD_C)
    nozzle2 = bkit.lathe("PivotNozzles2",
                         [(0.0, 0.0), (17.0, 0.0), (17.0, 26.0), (9.0, 40.0),
                          (0.0, 40.0)], segments=16, mat=brass)
    A.place_in_mesh(nozzle2, -69.0, 0.0, HEAD_C[2] - 40.0)
    bpy.context.view_layer.update()
    bkit.array_radial(nozzle2, SPEC["booms"], axis="Z", centre=HEAD_C)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6 + 2 + 1 + 2,
                note="Booms and nozzles are arrayed about the HEAD centre "
                     "and carry their orbit radius in the mesh.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
