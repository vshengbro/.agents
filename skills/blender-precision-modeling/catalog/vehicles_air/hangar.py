"""
hangar -- a 45 x 30 m barrel-vault aircraft hangar with a 40 m clear door.

A hangar is a SHELL, and the shell is a profile swept along the building's
length -- which is exactly a two-section loft of a closed ring, the same trick
the glasshouse uses. The ring is a barrel vault: vertical side walls to the
eave, then a segmental arch over the top. The door opening is a second ring
lofted through the front wall, and the ribs are the repeated feature, spaced on
a computed 5 m pitch from the building width.

The door is modelled as a set of horizontal tracks and a partially rolled-up
sectional door, because a hangar with a closed door is a wall with a roof.

Real maintenance hangar: 45000 x 30000 x 16000 mm, 40000 x 12000 mm door,
5.0 m rib pitch, 500 mm purlin depth.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy

SPEC = dict(
    length=45000.0,
    width=30000.0,
    eave_height=11000.0,
    ridge_height=16000.0,
    ridge_height_outer=16400.0,
    door_width=40000.0,
    door_height=12000.0,
    rib_pitch=5000.0,
    ribs=9,
    wall_thickness=400.0,
)

W = SPEC["width"]
L = SPEC["length"]
EAVE = SPEC["eave_height"]
T = SPEC["wall_thickness"]
HW = W / 2.0
# segmental arch: a 15000 mm half-span rising 5000 mm is a 27500 mm radius
ARCH_R = (HW * HW + (SPEC["ridge_height"] - EAVE) ** 2) / \
    (2.0 * (SPEC["ridge_height"] - EAVE))
ZC = SPEC["ridge_height"] - ARCH_R

A_EAVE = math.degrees(math.asin((EAVE - ZC) / ARCH_R))

CHECKS = [
    dict(name="length", mm=45000.0, tol=20.0, how="bbox_x",
         part="HangarShell"),
    dict(name="shell_width", mm=30800.0, tol=20.0, how="bbox_y",
         part="HangarShell"),
    dict(name="eave_height", mm=11000.0, tol=20.0, how="z_max",
         part="HangarSideWall0"),
    dict(name="ridge_height", mm=16400.0, tol=30.0, how="top_z",
         part="HangarShell"),
    dict(name="door_clear_width", mm=41400.0, tol=30.0, how="bbox_y",
         part="HangarDoorHead"),
    dict(name="door_head_top", mm=12800.0, tol=20.0, how="top_z",
         part="HangarDoorHead"),
    dict(name="rib1_x", mm=-16730.0, tol=8.0, how="x_min",
         part="HangarRib1"),
    dict(name="hangar_on_floor", mm=0.0, tol=20.0, how="z_min",
         part="HangarShell"),
]


def _shell_ring(x, t=T):
    """Closed ring: down the inside of the left wall, over the arch, down the
    right, and back along the outside.  Two of these lofted make a watertight
    shell with real wall thickness."""
    inner = [(-HW, 0.0), (-HW, EAVE)]
    a0 = math.degrees(math.asin((EAVE - ZC) / ARCH_R))
    for i in range(29):
        a = math.radians(a0 + (180.0 - 2.0 * a0) * i / 28.0)
        inner.append((ARCH_R * math.cos(a), ZC + ARCH_R * math.sin(a)))
    inner += [(HW, EAVE), (HW, 0.0)]
    outer = [(HW + t, 0.0), (HW + t, EAVE)]
    for i in range(29):
        a = math.radians(a0 + (180.0 - 2.0 * a0) * (28 - i) / 28.0)
        outer.append(((ARCH_R + t) * math.cos(a),
                      ZC + (ARCH_R + t) * math.sin(a)))
    outer += [(-HW - t, EAVE), (-HW - t, 0.0)]
    return [(x, y, z) for (y, z) in inner + outer]


def build():
    steel = bkit.pbr("HangarSteel", base=(0.68, 0.70, 0.72), metal=0.85,
                     rough=0.38)
    roof_mat = bkit.pbr("HangarRoof", base=(0.76, 0.77, 0.78), metal=0.85,
                        rough=0.34)
    door_mat = bkit.pbr("HangarDoor", base=(0.30, 0.34, 0.40), metal=0.85,
                        rough=0.40)
    apron = bkit.pbr("HangarApron", base=(0.30, 0.30, 0.31), rough=0.90)

    # ---- the shell: two rings, one loft, real 400 mm wall ------------
    ring = _shell_ring(0.0)
    shell = bkit.loft("HangarShell",
                      [list(ring), [(x + L, y, z) for (x, y, z) in ring]],
                      mat=roof_mat)
    bkit.recalc(shell)

    # ---- nine ribs on the computed pitch -----------------------------
    pitch = SPEC["rib_pitch"]
    for i in range(SPEC["ribs"]):
        x = -L / 2.0 + 900.0 + i * pitch
        # the rib follows the arch only BETWEEN the eaves: a full 180 deg
        # arc sweeps down to the arch centre, which for a 30 m span sits
        # 9000 mm BELOW the floor, and `sit_on_floor` then lifts the whole
        # hangar 9000 mm and every absolute height check with it.
        bkit.arc_torus("HangarRib%d" % i, ARCH_R - 260.0, 130.0,
                       A_EAVE, 180.0 - A_EAVE,
                       centre=(x, 0.0, ZC), plane="YZ", seg_minor=10,
                       mat=steel)
        for s in (1, -1):
            bkit.rounded_box("HangarRibPost%d%s" % (i, "R" if s > 0 else "L"),
                             260.0, 260.0, EAVE, r=20.0, segments=2,
                             centre=(x, s * (HW - 260.0), EAVE / 2.0),
                             mat=steel)

    # ---- the side walls and the eave gutters -------------------------
    for s in (1, -1):
        bkit.rounded_box("HangarSideWall%d" % (0 if s < 0 else 1),
                         L, T, EAVE, r=20.0, segments=2,
                         centre=(0.0, s * (HW + T / 2.0), EAVE / 2.0),
                         mat=steel)
        bkit.rounded_box("HangarGutter%d" % (0 if s < 0 else 1),
                         L, 500.0, 400.0, r=40.0, segments=3,
                         centre=(0.0, s * (HW + 250.0), EAVE), mat=steel)

    # ---- the door: jambs, head, tracks and a rolled-up leaf ---------
    dx = L / 2.0
    dw = SPEC["door_width"] / 2.0
    dh = SPEC["door_height"]
    for s in (1, -1):
        bkit.rounded_box("HangarDoorJamb%d" % (0 if s < 0 else 1),
                         700.0, 700.0, dh + 800.0, r=40.0, segments=3,
                         centre=(dx, s * (dw + 350.0), (dh + 800.0) / 2.0),
                         mat=steel)
        bkit.rounded_box("HangarDoorTrack%d" % (0 if s < 0 else 1),
                         600.0, 500.0, dh - 1200.0, r=20.0, segments=2,
                         centre=(dx - 200.0, s * (dw - 250.0),
                                 (dh - 1200.0) / 2.0), mat=door_mat)
    bkit.rounded_box("HangarDoorHead", 800.0, SPEC["door_width"] + 1400.0,
                     800.0, r=40.0, segments=3,
                     centre=(dx, 0.0, dh + 400.0), mat=steel)

    # the leaf, rolled up under the head in visible sections
    n_sec = 7
    ys = [p[0] for p in bkit.lay_out([6000.0] * n_sec, gap=40.0)]
    for i, y in enumerate(ys):
        bkit.rounded_box("HangarDoorLeaf%d" % i, 300.0, 5960.0, 1100.0,
                         r=30.0, segments=3,
                         centre=(dx - 260.0, y, dh - 700.0), mat=door_mat)

    # ---- the apron the aircraft parks on -----------------------------
    # named "Ground" so both `scene_bbox()` and `sit_on_floor()` skip it: an
    # apron built with its centre below z=0 would otherwise be the lowest
    # point in the scene and would lift the whole hangar 240 mm.
    bkit.rounded_box("Ground", 26000.0, W + 4000.0, 240.0, r=30.0,
                     segments=2, centre=(L / 2.0 + 11000.0, 0.0, -120.0),
                     mat=apron)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + SPEC["ribs"] * 3 + 4 + n_sec + 1,
                note="The shell is a two-ring loft: inside wall, arch, "
                     "outside wall, so the wall has real thickness.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
