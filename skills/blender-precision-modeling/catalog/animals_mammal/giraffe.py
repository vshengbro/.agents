"""
giraffe -- a 2700 mm-shoulder adult giraffe

The neck is the model: it is a near-vertical sweep whose radii taper hard from the massive base to the narrow poll, and it is what takes the overall height to more than twice the withers. Ossicones are two short capped spikes on the crown.

Construction: one torso loft, four leg sweeps whose soles sit exactly on z=0,
and separate watertight solids for neck, head, ears and tail. Nothing is booleaned:
overlapping closed solids stay manifold solids, which is why `health()` reports
zero non-manifold edges on an eighteen-part assembly.

Orientation: the nose points at -Y, world X is lateral, Z is up. The catalog's
fixed shot list puts the camera on +X for the SIDE view and on -Y for the FRONT
view, so a quadruped has to be built along Y for side.png to show a silhouette
instead of a face. All four soles rest on z=0.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real-world anatomy, millimetres ---------------------------------------
SPEC = dict(
    withers                  = 2700.0,
    body_length              = 1500.0,
    body_width               = 700.0,
    chest_depth              = 980.1,
    neck_length              = 2080.8,
    head_length              = 357.3,
    head_width               = 236.0,
    head_top_height          = 4230.0,
    shoulder_joint_height    = 1701.0,
    stance_front_track       = 532.0,
    stance_hind_track        = 546.0,
    tail_length              = 1085.3,
    overall_length           = 2124.4,
    overall_height           = 4436.0,
)

# --- construction tables, millimetres ---------------------------------------
TORSO = [
            (750, 231, 784.1, 2443.5),
            (510, 322, 950.7, 2619),
            (75, 350, 980.1, 2673),
            (-330, 339.5, 980.1, 2700),
            (-540, 308, 921.3, 2659.5),
            (-705, 245, 725.3, 2511),
            (-750, 175, 529.3, 2335.5),
    ]
FRONT_PATH = [(450, 266, 1704.5), (444, 266, 1080), (448, 266, 540), (454, 266, 243), (503.5, 266, 40), (591.5, 266, 40)]
FRONT_RAD = [(78, 82), (54.3, 59), (30.7, 28.3), (32.5, 28.3), (67, 40), (58.3, 35.2)]
HIND_PATH = [(-450, 273, 1704.5), (-410, 273, 1053), (-440, 273, 540), (-418, 273, 243), (-368.5, 273, 40), (-280.5, 273, 40)]
HIND_RAD = [(78, 82), (54.3, 59), (30.7, 28.3), (32.5, 28.3), (67, 40), (58.3, 35.2)]
EAR_PATH = [(790.6, 88, 4113.3), (813.3, 104.5, 4200.2), (831.9, 118.1, 4254.3)]
EAR_RAD = [(16.1, 41.8), (14, 44), (4.9, 13.2)]
OSSICONES = [(879.4, 64, 4222), (889.4, 76, 4342), (893.4, 82, 4412)]


def _sweep(name, path, rad, mat, n=2.4, steps=32):
    """Sweep a superellipse ring along a polyline.

    The animal's long axis is Y -- its nose points at -Y, which is what the
    fixed shot list means by a front view -- so every path here runs in the Y-Z
    plane and world X is the lateral axis. The ring's in-plane axis is the
    tangent crossed with X, which keeps each ring perpendicular to its own
    segment so a bend never twists the profile. Rings are bridged by `loft()`
    and capped, so every part is a closed solid on its own.

    `rad` is one (lateral_half_width, in_plane_half_height) per path node.
    """
    rings = []
    m = len(path)
    for i, p in enumerate(path):
        if i == m - 1:
            t = [p[k] - path[i - 1][k] for k in range(3)]
        else:
            t = [path[i + 1][k] - p[k] for k in range(3)]
        tl = math.sqrt(sum(c * c for c in t)) or 1.0
        ty, tz = t[1] / tl, t[2] / tl
        ul = math.hypot(ty, tz)
        if ul < 1e-9:
            uy, uz = 1.0, 0.0
        else:
            uy, uz = tz / ul, -ty / ul
        w, h = rad[i]
        ring = []
        for j in range(steps):
            a = 2.0 * math.pi * j / steps
            ca, sa = math.cos(a), math.sin(a)
            cx = math.copysign(abs(ca) ** (2.0 / n), ca)
            cy = math.copysign(abs(sa) ** (2.0 / n), sa)
            ring.append((p[0] + w * cy, p[1] + uy * h * cx,
                         p[2] + uz * h * cx))
        rings.append(ring)
    ob = bkit.loft(name, rings, mat=mat, smooth=True)
    bkit.recalc(ob)
    return ob


def build():

    coat = bkit.pbr("GiraffeCoat", base=(0.860, 0.700, 0.380), rough=0.70)
    pale = bkit.pbr("GiraffePale", base=(0.900, 0.860, 0.740), rough=0.74)
    dark = bkit.pbr("GiraffeDark", base=(0.240, 0.180, 0.120), rough=0.34)

    # ---- torso: seven superellipse sections, +X is the chest, -X the
    # rump. Every row is (x, half_width, depth, top_z) in millimetres, so
    # body width and chest depth are properties of the table, not a
    # claim made afterwards.
    sections = []
    for (y, hw, depth, ztop) in TORSO:
        ring = bkit.superellipse_section(2.0 * hw, depth, n=2.8, steps=40)
        sections.append([(u, y, ztop - depth / 2.0 + v) for (u, v) in ring])
    torso = bkit.loft("Torso", sections, mat=coat)
    bkit.recalc(torso)
    bkit.shade_smooth(torso, 50.0)

    # pale underside: a second material on the one solid. A second
    # shell shaped like the belly would z-fight with the real wall.
    bkit.assign_faces_by(torso, pale,
                      lambda c, n: c.z / bkit.MM < 1796.6)

    # spots: selected faces of the one torso solid take the darker coat.
    bkit.assign_faces_by(torso, dark,
                      lambda c, n: (math.sin(c.x / bkit.MM * 0.0671)
                                * math.sin(c.y / bkit.MM * 0.0524
                                          + 0.55 * c.z / bkit.MM)
                                > 0.22))

    # ---- front legs: plumb under the shoulder, the elbow only just forward of the vertical. The last two nodes share a z, which makes
    # their rings horizontal and the sole a flat strip resting on z=0,
    # so all four feet meet the floor at the same height.
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("LegFront%s" % side,
               [(sy * y, -x, z) for (x, y, z) in FRONT_PATH],
               FRONT_RAD, coat, n=2.2, steps=28)

    # ---- hind legs: stifle forward and hock back, so the leg reads as a zigzag rather than a post. The last two nodes share a z, which makes
    # their rings horizontal and the sole a flat strip resting on z=0,
    # so all four feet meet the floor at the same height.
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("LegHind%s" % side,
               [(sy * y, -x, z) for (x, y, z) in HIND_PATH],
               HIND_RAD, coat, n=2.2, steps=28)

    # ---- neck: five swept nodes from inside the chest to the poll, so the
    # two solids overlap instead of meeting on a shared face
    _sweep("Neck", [(0, -570, 2052), (0, -683.1, 2666), (0, -788.3, 3281.3), (0, -865.5, 3774.7), (0, -915, 4104)],
           [(250, 260), (217.5, 227.3), (174.2, 183.5), (134.5, 143.1), (108, 116)], coat, n=2.4, steps=32)

    # ---- head: skull to muzzle in one loft. The muzzle taper is the main
    # species cue, so the head gets five nodes rather than two.
    _sweep("Head", [(0, -809.4, 4104), (0, -899.4, 4124), (0, -1039.4, 4144), (0, -1139.4, 4144)],
           [(118, 126), (113.3, 121), (66, 96), (62, 84)], coat, n=2.4, steps=32)

    # ---- nose pad
    bkit.uv_sphere("Nose", 60.0, segments=24, rings=12,
                  centre=(0.0, -1155.4, 4136.0), mat=dark)

    # ---- ears: flattened swept plates splayed outward off the skull
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ear%s" % side,
               [(sy * y, -x, z) for (x, y, z) in EAR_PATH],
               EAR_RAD, coat, n=2.0, steps=24)

    # ---- tail
    _sweep("Tail", [(0, 750, 2430), (0, 855, 1998), (0, 900, 1350)],
           [(20, 20), (14, 14), (9, 9)], coat, n=2.4, steps=24)

    # ---- ossicones: two short capped spikes on the crown
    for side, sy in (("L", 1.0), ("R", -1.0)):
        _sweep("Ossicone%s" % side,
               [(sy * y, -x, z) for (x, y, z) in OSSICONES],
               [(22.0, 22.0), (16.0, 16.0), (24.0, 24.0)], dark, n=2.0, steps=16)

    # ---- every part above is its own closed solid: nothing was
    # booleaned, so the assembly stays manifold part by part.
    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=13)


# How each SPEC dimension is measured. The harness measures the real geometry,
# so these are claims the model has to earn.
CHECKS = [
    dict(name="body_length", mm=1500, tol=0.5, how="bbox_y", part="Torso"),
    dict(name="body_width", mm=700, tol=0.5, how="bbox_x", part="Torso"),
    dict(name="chest_depth", mm=1040.6, tol=0.5, how="bbox_z", part="Torso"),
    dict(name="head_length", mm=357.3, tol=0.5, how="bbox_y", part="Head"),
    dict(name="head_width", mm=236, tol=0.5, how="bbox_x", part="Head"),
    dict(name="tail_length", mm=1085.3, tol=0.8, how="longest", part="Tail"),
    dict(name="overall_length", mm=2124.4, tol=1.2, how="bbox_y"),
]
