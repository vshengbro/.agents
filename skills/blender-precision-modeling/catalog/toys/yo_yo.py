"""
yo_yo -- a 56 mm wooden yo-yo with a real rim groove, axle bore and wound string.

The silhouette of a yo-yo is two discs and a GROOVE: without the V channel cut
into the rim the object reads as a wheel or a pulley, not a toy. So the body is
one lathe whose profile walks out along the left flange, up over the rim,
through the groove, and back -- which gives the channel a real depth and a
real string seat in a single watertight solid. Two discs with a gap between
them would leave the string floating in mid-air.

Construction notes:
  * The lathe profile is authored from axis to axis, so the end caps close it.
    A lathe CANNOT produce a through-hole (a profile that never touches the
    axis is an annulus, and capping it plugs the hole), so the axle bore is a
    real `bore()` afterwards, with a cutter that crosses both end faces. It
    is deliberately NOT the same segment count as the lathe: a coaxial cutter
    sharing the host's facets is what leaves the EXACT solver non-manifold
    edges.
  * The painted centre band is a second material on the one solid, selected by
    radius. A separate ring object would z-fight with the flange faces.
  * The string is one swept tube along a helix, not a chain of overlapping
    rings, so it is a single watertight solid.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    body_diameter=28.0,     # a small 28 mm pocket yo-yo
    body_width=13.0,
    groove_opening=7.5,
    groove_depth=3.6,
    bore_diameter=3.0,      # axle bearing, through the whole body
    string_diameter=1.2,
    string_turns=2.0,
)

R = SPEC["body_diameter"] / 2.0
W = SPEC["body_width"] / 2.0
GW = SPEC["groove_opening"] / 2.0
GD = SPEC["groove_depth"]
BR = SPEC["bore_diameter"] / 2.0
SR = SPEC["string_diameter"] / 2.0
FT = 1.6                   # flange thickness at the rim
GR_IN = R - FT             # radius at the groove shoulders
GR_BOT = GR_IN - GD        # radius at the bottom of the groove

AXIS_Z = R                 # the body lies on its rim, so the axis is at z = R


def _tube_along(name, path, radius, mat, seg=12, closed_caps=True):
    """Sweep a circular section of `radius` along a polyline (mm).

    Frames are parallel-transported rather than rebuilt from a global
    up-vector: a rebuilt frame flips wherever the path runs vertical, which
    twists a round section into a visible spiral of quads.
    """
    n = len(path)
    tans = []
    for i in range(n):
        if i == 0:
            t = [path[1][k] - path[0][k] for k in range(3)]
        elif i == n - 1:
            t = [path[-1][k] - path[-2][k] for k in range(3)]
        else:
            t = [path[i + 1][k] - path[i - 1][k] for k in range(3)]
        L = math.sqrt(sum(c * c for c in t)) or 1.0
        tans.append([c / L for c in t])

    # seed a normal perpendicular to the first tangent
    ref = [0.0, 0.0, 1.0]
    if abs(tans[0][2]) > 0.9:
        ref = [1.0, 0.0, 0.0]
    u = [tans[0][1] * ref[2] - tans[0][2] * ref[1],
         tans[0][2] * ref[0] - tans[0][0] * ref[2],
         tans[0][0] * ref[1] - tans[0][1] * ref[0]]
    L = math.sqrt(sum(c * c for c in u)) or 1.0
    u = [c / L for c in u]

    sections = []
    for i in range(n):
        if i > 0:
            # parallel transport: project the previous normal onto the new
            # plane perpendicular to the tangent
            d = sum(u[k] * tans[i][k] for k in range(3))
            u = [u[k] - d * tans[i][k] for k in range(3)]
            L = math.sqrt(sum(c * c for c in u)) or 1.0
            u = [c / L for c in u]
        v = [tans[i][1] * u[2] - tans[i][2] * u[1],
             tans[i][2] * u[0] - tans[i][0] * u[2],
             tans[i][0] * u[1] - tans[i][1] * u[0]]
        p = path[i]
        ring = []
        for j in range(seg):
            a = 2.0 * math.pi * j / seg
            ca, sa = math.cos(a), math.sin(a)
            ring.append(tuple(p[k] + radius * (u[k] * ca + v[k] * sa)
                              for k in range(3)))
        sections.append(ring)
    ob = bkit.loft(name, sections, mat=mat, smooth=True)
    bkit.recalc(ob)
    if closed_caps:
        bkit.weld(ob)
    return ob


def build():
    wood = bkit.pbr("YoYoWood", base=(0.58, 0.36, 0.16), rough=0.34, coat=0.35)
    red = bkit.preset("red_paint")
    cream = bkit.pbr("YoYoString", base=(0.85, 0.82, 0.72), rough=0.72)

    # ---- body: one lathe profile that IS the yo-yo cross-section.
    # Axis to axis, so the two end caps close the solid.
    prof = [
        (0.0, -W),
        (R * 0.80, -W),
        (R, -W + 1.0),            # filleted flange edge
        (R, -GW - 0.6),
        (GR_IN, -GW),              # groove shoulder
        (GR_BOT, -GW * 0.45),
        (GR_BOT, 0.0),             # bottom of the groove
        (GR_BOT, GW * 0.45),
        (GR_IN, GW),
        (R, GW + 0.6),
        (R, W - 1.0),
        (R * 0.80, W),
        (0.0, W),
    ]
    body = bkit.lathe("YoYoBody", prof, segments=72, mat=wood)
    # Real through-bore for the axle. The cutter spans W*1.4 either side, so
    # it crosses both end faces instead of ending flush with them.
    bkit.bore(body, BR, W * 2.8, centre=(0.0, 0.0, 0.0), axis="Z",
              host_segments=72)
    bkit.recalc(body)
    bkit.shade_smooth(body, 32)

    # ---- painted centre band: a second material on the one solid
    bkit.assign_faces_by(
        body, red,
        lambda c, n: (c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM < R * 0.52)

    # ---- lay the body on its rim: the lathe axis Z becomes world Y, so the
    # groove faces up and the camera looks straight into the string channel.
    body.rotation_euler = (1.5707963, 0.0, 0.0)
    bkit.move(body, 0.0, 0.0, AXIS_Z)
    bpy.context.view_layer.update()

    # ---- axle: a real pin through the bearing, in polished metal
    axle = bkit.cylinder("YoYoAxle", BR * 0.62, W * 2.2, segments=24,
                         centre=(0.0, 0.0, AXIS_Z), axis="Y",
                         mat=bkit.preset("brushed_metal"))
    del axle

    # ---- string: two turns lying in the rim groove, then the free end
    # rising out of the top of it. The body is already lying on its side with
    # its axis along Y, so the groove is a channel running along Y with its
    # floor a radius GR_BOT from that axis: the helix therefore advances in Y
    # and circles in X/Z.
    path = []
    turns = SPEC["string_turns"]
    steps = 72
    y0, y1 = -GW * 0.85, GW * 0.85
    for i in range(steps + 1):
        t = i / steps
        a = t * turns * 2.0 * math.pi
        rr = GR_BOT + SR + 0.7 - t * 0.4      # each turn sits a hair lower
        path.append((rr * math.cos(a), y0 + (y1 - y0) * t,
                     AXIS_Z + rr * math.sin(a)))
    # free end: leaves the top of the channel and rises clear of the body.
    # Kept short deliberately: a full-length trailing string would triple the
    # bounding box and push the model out of its own size class.
    a_top = math.pi / 2.0
    r0 = GR_BOT + SR + 0.3
    for i in range(1, 21):
        t = i / 20.0
        path.append((r0 * math.cos(a_top) * (1.0 - 0.55 * t),
                     y1 + t * 1.6,
                     AXIS_Z + r0 * math.sin(a_top) + t * 9.0))
    cord = _tube_along("YoYoString", path, SR, cream, seg=10)
    bkit.shade_smooth(cord, 60)

    return dict(spec=SPEC, parts=3)


# How each dimension is measured. The harness measures the geometry; the model
# only declares which part owns the dimension and how to read it off.
CHECKS = [
    dict(name="body_diameter", mm=28.0, tol=0.4, how="diameter", part="YoYoBody"),
    dict(name="body_width", mm=13.0, tol=0.4, how="bbox_y", part="YoYoBody"),
    dict(name="body_height", mm=28.0, tol=0.4, how="bbox_z", part="YoYoBody"),
    dict(name="axle_length", mm=14.3, tol=0.6, how="bbox_y", part="YoYoAxle"),
]
