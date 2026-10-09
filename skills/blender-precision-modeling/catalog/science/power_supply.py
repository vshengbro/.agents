"""
power_supply -- 230 x 260 x 118 mm laboratory bench DC supply: chassis on four
feet, two recessed 96 x 38 mm displays (voltage and current), six control
knobs, four banana output terminals, a top ventilation grille and a carry
handle.

Twin readouts are what distinguishes a lab supply from a generic instrument
box, so both displays are real recesses cut into the front panel. The four
terminals sit on a computed 14 mm gap from `lay_out` and the knobs on a
`grid_positions` block, because a terminal bank with hand-spaced posts is the
classic way to produce coincident boolean faces.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    chassis_width=230.0,
    chassis_depth=260.0,
    chassis_height=118.0,
    display_width=96.0,
    display_height=38.0,
    displays=2,
    knobs=6,
    terminals=4,
    grille_holes=21,
)

CW, CD, CH = SPEC["chassis_width"], SPEC["chassis_depth"], SPEC["chassis_height"]
BODY_Z = 6.0 + CH / 2.0
FRONT = -CD / 2.0                    # -130


def _recess(name, host, sx, sz, cx, cz, mat, depth=4.0, proud=2.0, margin=2.0):
    bkit.boolean(host, bkit.rounded_box(
        "_pocket", sx + 2 * margin, proud + depth, sz + 2 * margin,
        r=2.0, segments=2,
        centre=(cx, FRONT + (depth - proud) / 2.0, cz)), "DIFFERENCE")
    return bkit.rounded_box(name, sx, 2.0, sz, r=1.5, segments=2,
                            centre=(cx, FRONT + 1.5, cz), mat=mat)


def build():
    shell = bkit.pbr("PsuShell", base=(0.80, 0.80, 0.79), rough=0.34)
    dark = bkit.pbr("PsuDark", base=(0.065, 0.065, 0.070), rough=0.42)
    knob_mat = bkit.pbr("PsuKnob", base=(0.14, 0.14, 0.15), rough=0.46)
    red = bkit.preset("red_paint")
    black = bkit.preset("black_plastic")
    screen = bkit.pbr("PsuScreen", base=(0.05, 0.08, 0.07), rough=0.10,
                      emission=(0.86, 0.36, 0.18), emission_strength=1.2)

    # ---- chassis and feet -------------------------------------------------
    bkit.rounded_box("PsuChassis", CW, CD, CH, r=8.0, segments=3,
                     centre=(0.0, 0.0, BODY_Z), mat=shell)
    feet = [bkit.cylinder("_foot", 10.0, 8.0, segments=20,
                          centre=(fx, fy, 4.0), mat=dark)
            for (fx, fy) in bkit.grid_positions(2, 2, CW - 50.0, CD - 60.0)]
    bkit.join(feet, name="PsuFeet")

    # ---- two recessed readouts -------------------------------------------
    for tag, sx_off in (("L", -52.0), ("R", 52.0)):
        _recess("PsuDisplay" + tag, bpy.data.objects["PsuChassis"],
                SPEC["display_width"], SPEC["display_height"], sx_off, 90.0,
                screen)

    # ---- six knobs on one grid, each with a pointer ----------------------
    knobs = []
    for i, (kx, kz) in enumerate(bkit.grid_positions(3, 2, 38.0, 34.0)):
        knobs.append(bkit.cylinder("_k%d" % i, 16.0, 16.0, segments=40,
                                   axis="Y", mat=knob_mat,
                                   centre=(kx, FRONT + 7.0, 44.0 + kz)))
        knobs.append(bkit.box("_m%d" % i, 2.0, 3.0, 12.0, mat=shell,
                              centre=(kx, FRONT - 1.5, 44.0 + kz + 10.0)))
    bkit.join(knobs, name="PsuKnobs")

    # ---- four banana terminals, two red and two black on a computed pitch -
    posts = []
    for i, (tx, tw) in enumerate(bkit.lay_out([26.0] * SPEC["terminals"],
                                               gap=14.0)):
        mat = red if i < 2 else black
        posts.append(bkit.cylinder("_post%d" % i, 7.0, 14.0, segments=24,
                                   axis="Y", mat=mat,
                                   centre=(tx, FRONT + 6.0, 18.0)))
        posts.append(bkit.cylinder("_sleeve%d" % i, 10.0, 4.0, segments=24,
                                   axis="Y", mat=dark,
                                   centre=(tx, FRONT + 1.0, 18.0)))
    bkit.join(posts, name="PsuTerminals")

    # ---- top ventilation grille, 7 x 3 holes ------------------------------
    bkit.perforated_panel("PsuGrille", 7, 3, 16.0, 16.0, 5.5, 120.0, 48.0,
                          4.0, mat=dark)
    bkit.move(bpy.data.objects["PsuGrille"], 0.0, 70.0, BODY_Z + CH / 2.0)

    # ---- carry handle over the chassis ------------------------------------
    bkit.arc_torus("PsuHandle", 62.0, 6.0, 20.0, 160.0, plane="XZ",
                   centre=(0.0, 0.0, BODY_Z + CH / 2.0), seg_major=32,
                   mat=dark, caps=True)

    # ---- rear mains inlet and an earth stud -------------------------------
    bkit.rounded_box("MainsInlet", 34.0, 6.0, 26.0, r=2.0, segments=2,
                     centre=(-70.0, CD / 2.0 - 1.0, 46.0), mat=dark)
    bkit.cylinder("EarthStud", 6.0, 8.0, segments=20, axis="Y", mat=knob_mat,
                  centre=(70.0, CD / 2.0 + 1.0, 46.0))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="chassis_width", mm=230.0, tol=0.6, how="bbox_x",
         part="PsuChassis"),
    dict(name="chassis_depth", mm=260.0, tol=0.6, how="bbox_y",
         part="PsuChassis"),
    dict(name="chassis_height", mm=118.0, tol=0.6, how="bbox_z",
         part="PsuChassis"),
    dict(name="display_width", mm=96.0, tol=0.6, how="bbox_x",
         part="PsuDisplayL"),
    # Six knobs joined into one bank: `diameter` = max(bbox_x, bbox_y) would read
    # the 108 mm BANK WIDTH, so the check names the bank instead.
    dict(name="knob_bank_width", mm=108.0, tol=0.8, how="bbox_x",
         part="PsuKnobs"),
]