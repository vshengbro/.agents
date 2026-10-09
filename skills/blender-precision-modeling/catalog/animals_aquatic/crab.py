"""crab -- a 140 mm shore crab: broad flattened carapace, eight walking legs,
and two claws held in front.

Eight legs is the count that fails. One leg is authored on +X and swept with
`array_radial(count=8, centre=BODY_CENTRE)` about the carapace's own centre at
(0, 0, 26) -- six legs is the classic miss, and without the explicit `centre`
the copies orbit the WORLD origin instead of the carapace, which throws every
leg outside the animal's own footprint.

Construction: a lathed carapace squashed into a flattened dome, an eye-stalk
pair, one leg arrayed eight times, and two mirrored claw arms whose chelae are
real two-part solids (a fixed finger and a moving finger) rather than blocks.
Nothing is booleaned; every part is a closed solid.

Orientation: the crab faces -Y, world X lateral, Z up, so side.png shows the
stance. Real width across the legs is about 140 mm.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    carapace_length=95.0,
    carapace_width=88.0,
    carapace_height=19.0,
    leg_count=8,
    leg_span=149.0,
    claw_length=22.0,
)

CENTRE = (0.0, 0.0, 26.0)        # the hub every walking leg orbits
# one walking leg, authored on +X: out, up, then down to a point
LEG = [
    (34.0, 4.0, 26.0),
    (50.0, 12.0, 24.0),
    (62.0, 22.0, 16.0),
    (68.0, 30.0, 4.0),
    (70.0, 34.0, 0.5),
]
LEG_RAD = [(7.0, 7.0), (6.0, 6.0), (5.0, 5.0), (3.5, 4.0), (1.6, 1.6)]
# the claw arm: out from the front of the carapace
CLAWARM = [
    (0.0, -40.0, 26.0),
    (16.0, -58.0, 24.0),
    (26.0, -74.0, 20.0),
    (30.0, -86.0, 16.0),
]
CLAWARM_RAD = [(9.0, 9.0), (8.0, 8.0), (7.0, 7.0), (7.5, 7.5)]


def build():
    shell = bkit.pbr("CrabShell", base=(0.48, 0.16, 0.10), rough=0.44,
                     coat=0.2)
    under = bkit.pbr("CrabUnderside", base=(0.72, 0.44, 0.32), rough=0.50)
    legm = bkit.pbr("CrabLeg", base=(0.42, 0.14, 0.09), rough=0.46)
    clawm = bkit.pbr("CrabClaw", base=(0.55, 0.20, 0.12), rough=0.40,
                     coat=0.25)
    eye = bkit.pbr("CrabEye", base=(0.02, 0.02, 0.025), rough=0.08)

    # ---- carapace: a lathed dome, then squashed to a crab's flat shield by
    # scaling the mesh in Z. The scale is baked into the vertices, not left on
    # the object, so the world-space mirror stays exact.
    shell_ob = bkit.lathe(
        "Carapace",
        [(0.0, 0.0), (30.0, 2.0), (42.0, 9.0), (44.0, 20.0), (34.0, 28.0),
         (0.0, 30.0)],
        segments=48, centre=(0.0, 6.0, 8.0), mat=shell)
    me = shell_ob.data
    for v in me.vertices:
        v.co.y = v.co.y * 1.08          # a shade longer than wide
        # mesh vertices are METRES even though every number in this script is
        # millimetres: squashing about z=8 mm with a bare `8.0` here lands the
        # carapace at 3 metres and the scene bounding box with it
        v.co.z = bkit.u(8.0) + (v.co.z - bkit.u(8.0)) * 0.62
    shell_ob.data.update()

    bkit.assign_faces_by(shell_ob, under,
                         lambda c, n: c.z / bkit.MM < 14.0)

    # ---- eye stalks: the crab's eyes sit on short raised stalks
    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.cylinder("EyeStalk%s" % side, 3.2, 10.0, segments=14,
                      centre=(sx * 12.0, -26.0, 38.0), mat=under)
        bkit.uv_sphere("Eye%s" % side, 4.6, segments=16, rings=8,
                       centre=(sx * 12.0, -27.0, 44.0), mat=eye)

    # ---- eight walking legs, one authored and swept about the carapace
    leg = F.tube("Leg0", LEG, LEG_RAD, legm, n=2.2, steps=14)
    bkit.array_radial(leg, SPEC["leg_count"], centre=CENTRE)

    # ---- two claw arms, each with a real two-part chela
    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.tube("ClawArm%s" % side,
               [(sx * p[0], p[1], p[2]) for p in CLAWARM],
               CLAWARM_RAD, legm, n=2.2, steps=14)
        palm = bkit.uv_sphere("Palm%s" % side, 11.0, segments=24, rings=12,
                              centre=(sx * 32.0, -88.0, 15.0), mat=clawm)
        bkit.move(palm, sx * 4.0, -4.0, 0.0)
        F.tube("Finger%s" % side,
               [(sx * 34.0, -94.0, 15.0), (sx * 38.0, -106.0, 12.0),
                (sx * 40.0, -116.0, 10.0)],
               [(5.0, 4.0), (3.5, 3.0), (1.4, 1.4)], clawm, n=2.4, steps=10)
        F.tube("Thumb%s" % side,
               [(sx * 30.0, -95.0, 17.0), (sx * 30.0, -105.0, 16.0),
                (sx * 29.0, -112.0, 14.0)],
               [(4.0, 3.5), (3.0, 2.6), (1.2, 1.2)], clawm, n=2.4, steps=10)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=20)


CHECKS = [
    dict(name="carapace_length", mm=95.0, tol=4.0, how="bbox_y",
         part="Carapace"),
    dict(name="carapace_width", mm=88.0, tol=4.0, how="bbox_x",
         part="Carapace"),
    dict(name="carapace_height", mm=19.0, tol=3.0, how="bbox_z",
         part="Carapace"),
    dict(name="leg_span", mm=149.0, tol=6.0, how="bbox_x"),
    dict(name="claw_length", mm=22.0, tol=3.0, how="bbox_y", part="PalmL"),
]