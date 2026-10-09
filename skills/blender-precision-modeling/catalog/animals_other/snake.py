"""snake -- a 900 mm corn snake coiled on the substrate: a long tapering body
that follows a real spiral of loops, with a distinct head and a visible scale
pattern.

The coil is the model. A snake authored as a straight taper reads as a rope; a
snake reads as a snake when the body follows overlapping loops whose radius
grows along the body. So the path is generated from a real Archimedean-ish
spiral in plan with a per-node taper, and the head sits on the end of it.

Construction: one swept body from a generated path, a swept head with a real
snout, and the dorsal blotches as a second material on the one body solid so
there is no z-fighting. Nothing is booleaned.

Orientation: the coil lies in the X-Y plane, head raised at the -Y end, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    body_length=900.0,
    body_diameter=22.0,
    coil_diameter=316.0,
    coil_turns=2.25,
    head_length=48.0,
)

TURNS = 2.25
R0 = 66.0               # radius of the first (innermost) loop
DR = 92.0               # radius added per turn
STEPS = 120
BODY_R = 13.0            # maximum half-diameter, at mid-body
Z0 = 13.0                # the body rests on the substrate


def coil_path():
    """The body's centreline: a growing spiral in the X-Y plane.

    Generated from the real turn count and the real radius growth, so the coil
    is a curve rather than a stack of hand-placed rings. The body ends at the
    OUTER loop, where the head sits.
    """
    pts = []
    total = TURNS * 2.0 * math.pi
    for i in range(STEPS + 1):
        t = i / float(STEPS)
        a = total * t
        r = R0 + DR * t
        pts.append((r * math.cos(a), -r * math.sin(a), Z0))
    return pts


def taper(t):
    """Half-diameter along the body: thin tail, thickest at 40%, thin neck."""
    if t < 0.40:
        return BODY_R * (0.34 + 0.66 * (t / 0.40))
    if t < 0.86:
        return BODY_R * (1.0 - 0.30 * ((t - 0.40) / 0.46))
    return BODY_R * (0.70 - 0.30 * ((t - 0.86) / 0.14))


def build():
    scale = bkit.pbr("SnakeScale", base=(0.62, 0.28, 0.14), rough=0.60,
                     coat=0.15)
    blotch = bkit.pbr("SnakeBlotch", base=(0.32, 0.12, 0.07), rough=0.58)
    belly = bkit.pbr("SnakeBelly", base=(0.82, 0.72, 0.56), rough=0.64)
    eye = bkit.pbr("SnakeEye", base=(0.03, 0.02, 0.02), rough=0.08)
    tongue = bkit.pbr("SnakeTongue", base=(0.62, 0.10, 0.12), rough=0.40)

    path = coil_path()
    rad = [(taper(i / float(STEPS)), taper(i / float(STEPS)) * 0.86)
           for i in range(len(path))]
    body = F.tube("Body", path, rad, scale, n=2.2, steps=20)

    # the pale underside: a second material on the ONE body solid. A second
    # shell shaped like the belly would z-fight with the real surface.
    bkit.assign_faces_by(body, belly,
                         lambda c, n: c.z / bkit.MM < 9.0)
    # the dorsal blotches: a computed checker of patches over the coil. Pitches
    # come from the patch counts, so no two patches share a station.
    pitch_a, pitch_t = math.radians(16.0), 0.055
    for i in range(46):
        t = 0.06 + i * pitch_t
        if t > 0.94:
            break
        a = TURNS * 2.0 * math.pi * t
        r = R0 + DR * t
        for da in (-pitch_a / 2.0, pitch_a / 2.0):
            px = (r + 2.0) * math.cos(a + da)
            py = -(r + 2.0) * math.sin(a + da)
            bkit.uv_sphere("Blotch%d_%d" % (i, int(da > 0)), taper(t) * 0.75,
                           segments=12, rings=6,
                           centre=(px, py, Z0 + taper(t) * 0.45), mat=blotch)

    # ---- head: the neck end of the coil, raised and flattened
    end = path[-1]
    dx, dy = path[-1][0] - path[-2][0], path[-1][1] - path[-2][1]
    dl = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dl, dy / dl
    head_path = [(end[0], end[1], Z0),
                 (end[0] + ux * 14.0, end[1] + uy * 14.0, Z0 + 4.0),
                 (end[0] + ux * 30.0, end[1] + uy * 30.0, Z0 + 6.0),
                 (end[0] + ux * 44.0, end[1] + uy * 44.0, Z0 + 5.0)]
    F.tube("Head", head_path,
           [(11.0, 8.0), (13.0, 10.0), (12.0, 8.5), (7.5, 5.5)],
           scale, n=2.6, steps=20)
    for side, s in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 3.4, segments=16, rings=8,
                       centre=(head_path[2][0] - uy * s * 9.0,
                               head_path[2][1] + ux * s * 9.0,
                               Z0 + 9.0), mat=eye)
    F.cone_between("Tongue",
                   (head_path[3][0], head_path[3][1], Z0 + 4.0),
                   (head_path[3][0] + ux * 22.0, head_path[3][1] + uy * 22.0,
                    Z0 + 2.0),
                   2.0, 0.7, seg=8, mat=tongue)

    # ---- tail tip: the coil's other end, tapering to a point on the substrate
    F.cone_between("TailTip", path[0],
                   (path[0][0] - (path[1][0] - path[0][0]) * 1.6,
                    path[0][1] - (path[1][1] - path[0][1]) * 1.6, Z0 * 0.5),
                   taper(0.0) * 1.05, 0.6, seg=12, mat=scale)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=96)


CHECKS = [
    dict(name="body_diameter", mm=22.0, tol=2.0, how="bbox_z", part="Body"),
    dict(name="coil_diameter", mm=316.0, tol=25.0, how="bbox_x"),
    dict(name="head_length", mm=48.0, tol=6.0, how="longest", part="Head"),
    dict(name="stand_height", mm=27.0, tol=4.0, how="bbox_z"),
]