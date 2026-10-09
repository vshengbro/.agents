"""
jack_in_box -- a 130 mm jack-in-the-box with the lid open and the jack out.

A jack-in-the-box is a box, a hinged lid, and a figure on a spring, and the
read depends on all three being in the right RELATIONSHIP: the lid has to be
thrown back, not resting on the rim, and the jack has to be emerging from
inside the box rather than standing beside it.

The box is a rounded box with a real hollow interior -- the cavity is a
second solid subtracted by boolean, cut THROUGH the top so it genuinely opens
rather than sitting 1 mm below the rim, which is the tangency failure that
leaves non-manifold edges. The lid is a rounded box rotated about its own
hinge edge, and the jack is a lathed body with a spherical head, a cone hat
and a ruff collar, so it reads as a clown at a glance.

The crank on the side is the detail that says "this is a mechanism": a real
shaft, a real crank arm and a real handle knob.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
from mathutils import Matrix, Vector
import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    box_width=130.0,
    box_depth=130.0,
    box_height=118.0,
    wall=6.0,
    lid_width=136.0,
    lid_height=20.0,
    lid_open_angle=112.0,    # degrees the lid is thrown back
    jack_height=96.0,        # how far the figure stands proud of the rim
    head_diameter=34.0,
    hat_diameter=38.0,
    hat_height=30.0,
    crank_length=22.0,
    shaft_diameter=7.0,
)

BW = SPEC["box_width"]
BD = SPEC["box_depth"]
BH = SPEC["box_height"]
WALL = SPEC["wall"]
LW = SPEC["lid_width"]
LH = SPEC["lid_height"]
ANG = SPEC["lid_open_angle"]
JH = SPEC["jack_height"]
HD = SPEC["head_diameter"] / 2.0
HATD = SPEC["hat_diameter"] / 2.0
HATH = SPEC["hat_height"]
CL = SPEC["crank_length"]
SHAFT_R = SPEC["shaft_diameter"] / 2.0


def build():
    red = bkit.preset("red_paint")
    yellow = bkit.preset("yellow_paint")
    cream = bkit.preset("white_plastic")
    blue = bkit.preset("blue_paint")
    skin = bkit.pbr("JackSkin", base=(0.90, 0.74, 0.62), rough=0.44, coat=0.3)
    wood = bkit.pbr("JackWood", base=(0.60, 0.36, 0.17), rough=0.40)

    # ---- the box, with a real hollow interior
    box = bkit.rounded_box("JackBox", BW, BD, BH, r=3.0, segments=4,
                           centre=(0.0, 0.0, BH / 2.0), mat=red)
    # The cavity cutter is deliberately TALLER than the box and starts well
    # below the rim, so it crosses the top face instead of ending flush with
    # it: a cutter whose top stops exactly at the surface is tangent, and
    # tangency is what leaves the EXACT solver a handful of bad edges.
    cav = bkit.rounded_box("JackCavity", BW - 2 * WALL, BD - 2 * WALL,
                           BH, r=2.0, segments=3,
                           centre=(0.0, 0.0, BH - WALL
                                   + (BH - WALL) / 2.0), mat=None)
    bkit.boolean(box, cav, "DIFFERENCE")
    bkit.recalc(box)
    bkit.shade_smooth(box, 34)
    # painted stars: a second material on the box, not decal objects
    # painted spots: a bounded disc on each visible side, not the whole wall.
    # A predicate that selects "the front face" paints the entire face and the
    # box comes out two-tone, which reads as packaging, not as a toy.
    bkit.assign_faces_by(
        box, yellow,
        lambda c, n: (c.y / bkit.MM) < -BD / 2.0 + WALL + 0.6
        and (c.x / bkit.MM) ** 2 + (c.z / bkit.MM - BH * 0.55) ** 2
        < (BW * 0.26) ** 2)

    # ---- the lid, thrown back on its hinge at the rear top edge.
    #
    # The lid is authored lying flat, centred on the origin, and then ROTATED
    # about its own hinge line and moved so that line lands on the box's rear
    # top edge. Rotating about the world origin instead would swing the lid
    # through the floor: the hinge is 65 mm behind the lid's own centre, so a
    # rotation about (0,0,0) drops the far edge below z=0 and the model is
    # then seated on its lid corner.
    a = math.radians(ANG)
    lid = bkit.rounded_box("JackLid", LW, LW, LH, r=3.0, segments=4,
                           centre=(0.0, 0.0, LH / 2.0), mat=blue)
    hinge = Vector(bkit.v(0.0, BD / 2.0, BH))
    # the lid's centre relative to the hinge: back by half the box, up by half
    # the lid thickness
    off = Vector(bkit.v(0.0, -BD / 2.0 - LW / 2.0, LH / 2.0))
    rot = Matrix.Rotation(a, 3, "X")
    lid.rotation_euler = (a, 0.0, 0.0)
    lid.location = hinge + rot @ off
    bpy.context.view_layer.update()

    # ---- the jack. A lathed body rising out of the box, a ball head, a ruff
    # and a cone hat: four cues that together read as a clown.
    #
    # jack_base_z is set so the FIGURE clears the rim by most of its height.
    # Starting it low inside the box is the quiet way to model a jack-in-the-
    # box that is still a closed box with a hat poking out of the lid.
    jack_base_z = BH * 0.72
    body = bkit.lathe("JackBody",
                      [(0.0, 0.0), (16.0, 0.0), (16.0, 4.0), (11.0, 6.0),
                       (9.0, 14.0), (10.0, 22.0), (12.0, 26.0), (9.0, 30.0),
                       (0.0, 31.0)],
                      segments=40, centre=(0.0, 0.0, jack_base_z), mat=blue)
    bkit.recalc(body)
    bkit.shade_smooth(body, 34)
    # the ruff: the wide collar that says clown
    bkit.lathe("JackRuff",
               [(9.0, 0.0), (24.0, 3.0), (25.0, 6.0), (20.0, 8.0), (9.0, 9.0)],
               segments=40, centre=(0.0, 0.0, jack_base_z + 28.0), mat=cream)
    head_z = jack_base_z + 30.0 + HD * 0.9
    bkit.uv_sphere("JackHead", HD, segments=40, rings=22,
                   centre=(0.0, 0.0, head_z), mat=skin)
    # the nose, because a clown without a nose is a doll
    bkit.uv_sphere("JackNose", 6.0, segments=24, rings=14,
                   centre=(0.0, -HD * 0.86, head_z + HD * 0.05), mat=red)
    bkit.lathe("JackHat",
               [(0.0, 0.0), (HATD, 0.0), (HATD, 2.5), (HATD * 0.34, 4.0),
                (HATD * 0.20, HATH * 0.6), (HATD * 0.13, HATH), (0.0, HATH)],
               segments=40, centre=(0.0, 0.0, head_z + HD * 0.62), mat=red)
    bkit.uv_sphere("JackPom", 7.0, segments=20, rings=12,
                   centre=(0.0, 0.0, head_z + HD * 0.62 + HATH), mat=yellow)
    # arms: two stubby sleeves out to the sides, breaking the box's symmetry
    for side, sx in (("L", 1.0), ("R", -1.0)):
        arm = bkit.cylinder("JackArm%s" % side, 6.0, 26.0, segments=20,
                            centre=(sx * 22.0, 0.0, jack_base_z + 24.0),
                            axis="X", mat=blue)
        arm.rotation_euler = (0.0, math.radians(-24.0 * sx), 0.0)
        bpy.context.view_layer.update()
        bkit.shade_smooth(arm, 40)
        bkit.uv_sphere("JackHand%s" % side, 6.4, segments=20, rings=12,
                       centre=(sx * 35.0, 0.0, jack_base_z + 29.0), mat=skin)

    # ---- the crank on the left wall: shaft, arm and knob. This is the
    # detail that says "mechanism" rather than "painted box".
    crank_z = BH * 0.50
    bkit.cylinder("CrankShaft", SHAFT_R, 18.0, segments=20,
                  centre=(-BW / 2.0 - 6.0, 0.0, crank_z), axis="X",
                  mat=bkit.preset("brushed_metal"))
    bkit.rounded_box("CrankArm", 5.0, 6.0, CL, r=2.0, segments=2,
                     centre=(-BW / 2.0 - 14.0, 0.0, crank_z + CL / 2.0),
                     mat=bkit.preset("brushed_metal"))
    bkit.cylinder("CrankKnob", 7.0, 12.0, segments=24,
                  centre=(-BW / 2.0 - 14.0, 0.0, crank_z + CL), mat=wood)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 1 + 1 + 1 + 1 + 1 + 1 + 4 + 3)


CHECKS = [
    dict(name="box_width", mm=130.0, tol=0.6, how="bbox_x", part="JackBox"),
    dict(name="box_height", mm=118.0, tol=0.6, how="bbox_z", part="JackBox"),
    dict(name="head_diameter", mm=34.0, tol=0.5, how="diameter", part="JackHead"),
    dict(name="hat_diameter", mm=38.0, tol=0.6, how="diameter", part="JackHat"),
    dict(name="crank_length", mm=22.0, tol=0.8, how="bbox_z", part="CrankArm"),
    # the assembly is box + the lid thrown back on its hinge + the jack
    # standing proud of the rim. The lid at 112 degrees is the tallest thing.
    dict(name="overall_height", mm=256.5, tol=4.0, how="bbox_z"),
    dict(name="overall_width", mm=154.0, tol=3.0, how="bbox_x"),
]
