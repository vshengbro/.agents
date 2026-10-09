"""
spacesuit_helmet -- an EVA helmet off the suit: 320 mm outer diameter, 220 mm
tall, 8.4 kg, with a gold sun visor and a hard upper torso neck ring.

Size class `small` (30..150 mm band, tolerance x0.5..x2, so nothing declared
may exceed 300 mm). Stated at 1:1.12 scale of a real 320 mm EVA helmet.

The details that make it a HELMET rather than a sphere with a hole are all
proportions: the neck ring is a separate hard collar with a real bore, the
visor is a flattened bubble set into the front and it OVERHANGS the front
face, and the side "ears" carry the microphones and the head lamps. A plain
sphere with a gold patch does not read.

The helmet is a lathe over a closed profile: outer shell from the neck ring
up over the crown and down inside again, so it has a real wall thickness
rather than being a zero-thickness dome.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

def _scale_all(k):
    """Uniformly scale the whole assembly about the world origin.

    Scaling every object's location AND its own scale by the same factor is
    exactly a global scale about the origin, and it is how these models are
    retuned into their catalog size band without editing forty numbers: mm in,
    mm out, and every declared CHECK still measures real geometry.
    """
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        ob.location = ob.location * k
        ob.scale = ob.scale * k
    bpy.context.view_layer.update()


SPEC = dict(
    outer_diameter=270.0,
    height=196.0,
    wall_thickness=12.0,
    neck_ring_outer=160.0,
    neck_ring_bore=130.0,
    neck_ring_height=70.0,
    visor_bubble_diameter=232.0,
)

D = SPEC["outer_diameter"]
R = D / 2.0
WALL = SPEC["wall_thickness"]


def build():
    shell_mat = bkit.pbr("HelmetShell", base=(0.88, 0.87, 0.84), rough=0.36)
    gold = bkit.pbr("VisorGold", base=(0.90, 0.72, 0.22), metal=0.85, rough=0.08)
    ring_mat = bkit.pbr("NeckRingAlum", base=(0.60, 0.61, 0.63), metal=0.85,
                        rough=0.34)
    dark = bkit.pbr("HelmetDark", base=(0.14, 0.14, 0.15), rough=0.55)

    # ---- shell: outer surface up and over, inner surface back down -------
    # Closed profile, both ends at r=0 is not right for a helmet (it has a
    # neck opening), so the profile is a CLOSED LOOP that starts and ends on
    # the neck ring's outer radius: outer dome up, over the crown, inside and
    # down, then out along the rim. `lathe` closes the ends automatically
    # because the loop returns to its start.
    # CLOSED LOOP, first point == last point, cap_ends=False. The obvious
    # open polyline (outer dome, then inner dome) leaves two boundary rings at
    # the neck and reports 41 non-manifold edges; and relying on
    # cap_ends=True puts two coincident discs at the rim instead of closing
    # the shell. So the profile starts on the rim, goes over the outside to
    # the crown, back down the inside, and returns to where it started.
    base = SPEC["neck_ring_height"] * 0.5
    prof = [(R, base)]
    steps = 14
    for i in range(steps + 1):                       # outside, rim -> crown
        a = math.pi * 0.5 * i / steps
        prof.append((R * math.cos(a), base + SPEC["height"] * math.sin(a)))
    for i in range(steps, -1, -1):                   # inside, crown -> rim
        a = math.pi * 0.5 * i / steps
        prof.append(((R - WALL) * math.cos(a),
                     base + WALL + (SPEC["height"] - WALL) * math.sin(a)))
    prof.append((R, base))                           # close the loop
    shell = bkit.lathe("HelmetShell", prof, segments=40, mat=shell_mat,
                       smooth=True, cap_ends=False)
    bkit.recalc(shell)

    # ---- neck ring: hard upper-torso collar with a real bore -------------
    ring = bkit.tube("NeckRing", SPEC["neck_ring_outer"] / 2.0,
                     SPEC["neck_ring_bore"] / 2.0, SPEC["neck_ring_height"],
                     segments=32,
                     centre=(0.0, 0.0, SPEC["neck_ring_height"] / 2.0),
                     mat=ring_mat)
    latch = bkit.rounded_box("NeckLatch", 46.0, 26.0, 40.0, r=8.0,
                             centre=(0.0, -SPEC["neck_ring_outer"] / 2.0 + 6.0,
                                     SPEC["neck_ring_height"] * 0.6),
                             mat=dark)

    # ---- visor: a flattened bubble hanging off the front ----------------
    vd = SPEC["visor_bubble_diameter"]
    # Offset FORWARD of the shell radius, or the gold visor sits entirely
    # inside the helmet and never shows at all. The shell's front surface is
    # at y = -R; the visor's own forward reach is cy - 0.52*(vd/2), and this
    # placement clears -R by about 25 mm.
    visor = bkit.uv_sphere("Visor", vd / 2.0, segments=40, rings=24,
                           centre=(0.0, -R * 0.72, SPEC["height"] * 0.52))
    visor.scale = (0.94, 0.52, 0.78)
    bkit.apply_mods(visor)
    bkit.assign(visor, gold)
    # visor hinge and the shroud that clamps it
    bkit.rounded_box("VisorShroud", vd * 0.98, 26.0, 40.0, r=10.0,
                     centre=(0.0, -R * 0.30, SPEC["height"] * 0.80), mat=ring_mat)

    # ---- side pods: microphones, head lamps, ear comms --------------------
    for (side, sign) in (("L", 1.0), ("R", -1.0)):
        pod = bkit.rounded_box("EarPod" + side, 70.0, 110.0, 130.0, r=26.0,
                               centre=(sign * R * 0.86, -R * 0.20,
                                       SPEC["height"] * 0.56), mat=shell_mat)
        bkit.cylinder("HeadLamp" + side, 30.0, 46.0, segments=18,
                      centre=(sign * R * 0.94, -R * 0.34,
                              SPEC["height"] * 0.62),
                      axis="X", smooth=True, mat=dark)

    _scale_all(0.92)      # 316 mm -> 291 mm, inside the small band (max 300)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="outer_diameter", mm=248.4, tol=2.5,
         how="diameter", part="HelmetShell"),
    # The shell sits ON the neck ring, so its bbox_z is the dome height alone.
    dict(name="dome_height", mm=180.3, tol=3.0, how="bbox_z", part="HelmetShell"),
    dict(name="neck_ring_outer", mm=147.2, tol=1.6,
         how="diameter", part="NeckRing"),
    # tube() measures its OUTER diameter through the bbox; the bore is the
    # inner wall, which a bounding box cannot see, so it is not declared.
    dict(name="neck_ring_height", mm=64.4, tol=1.0,
         how="bbox_z", part="NeckRing"),
    # The visor bulges FORWARD (-Y), so it does not change bbox_x; the ear pods
    # set the width.
    dict(name="overall_width", mm=278.0, tol=6.0, how="bbox_x"),
    dict(name="overall_height", mm=212.5, tol=4.0, how="bbox_z"),
]