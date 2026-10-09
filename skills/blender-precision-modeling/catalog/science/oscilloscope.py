"""
oscilloscope -- 400 x 210 x 172 mm 4-channel bench scope: moulded chassis on
four feet, a genuinely recessed 230 x 120 mm CRT with an 18-division graticule,
an eight-key soft keypad, a six-knob control block, four BNC inputs and a top
extraction grille.

The display is a real recess, not a decal. `_recess` sinks a rounded-box cutter
4 mm into the front face while leaving it standing 2 mm proud, so the cutter
genuinely crosses the surface instead of meeting it: a cutter that ends exactly
flush touches the host along a rectangle, and that contact line becomes a
non-manifold edge. This is the trap that bites hardest on instrument fronts.

Every repeated feature is computed from a real pitch -- 10 vertical and 8
horizontal graticule divisions from `lay_out`, 8 soft keys and 6 knobs from
`grid_positions`, 32 grille holes from `perforated_panel` -- because the count
is what makes it read as an instrument rather than as a box.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    chassis_width=400.0,
    chassis_depth=210.0,
    chassis_height=172.0,
    screen_width=230.0,
    screen_height=120.0,
    graticule_divisions=18,
    soft_keys=8,
    knobs=6,
    bnc_inputs=4,
    grille_holes=32,
)

CW, CD, CH = SPEC["chassis_width"], SPEC["chassis_depth"], SPEC["chassis_height"]
FOOT_H = 14.0
BODY_Z = FOOT_H + CH / 2.0
FRONT = -CD / 2.0                    # -105, the front face


def _recess(name, host, sx, sz, cx, cz, mat, depth=4.0, proud=2.0, margin=2.0):
    """Sink a pocket into the front face and set the panel 0.5 mm inside it."""
    bkit.boolean(host, bkit.rounded_box(
        "_pocket", sx + 2 * margin, proud + depth, sz + 2 * margin,
        r=2.0, segments=2,
        centre=(cx, FRONT + (depth - proud) / 2.0, cz)), "DIFFERENCE")
    return bkit.rounded_box(name, sx, 2.0, sz, r=1.5, segments=2,
                            centre=(cx, FRONT + 1.5, cz), mat=mat)


def build():
    shell = bkit.pbr("ScopeShell", base=(0.80, 0.80, 0.79), rough=0.34)
    dark = bkit.pbr("ScopeDark", base=(0.065, 0.065, 0.070), rough=0.42)
    knob_mat = bkit.pbr("ScopeKnob", base=(0.14, 0.14, 0.15), rough=0.46)
    nickel = bkit.preset("brushed_metal")
    screen = bkit.pbr("ScopeScreen", base=(0.04, 0.07, 0.06), rough=0.10,
                      emission=(0.20, 0.52, 0.34), emission_strength=0.85)
    trace = bkit.pbr("ScopeTrace", base=(0.30, 0.90, 0.45),
                     emission=(0.35, 0.95, 0.50), emission_strength=1.6)

    # ---- chassis and feet -------------------------------------------------
    bkit.rounded_box("ScopeChassis", CW, CD, CH, r=10.0, segments=3,
                     centre=(0.0, 0.0, BODY_Z), mat=shell)
    feet = [bkit.cylinder("_foot", 12.0, 16.0, segments=20,
                          centre=(fx, fy, 8.0), mat=dark)
            for (fx, fy) in bkit.grid_positions(2, 2, CW - 80.0, CD - 70.0)]
    bkit.join(feet, name="ScopeFeet")

    # ---- recessed CRT and its 18-division graticule ------------------------
    sx, sz, szc = SPEC["screen_width"], SPEC["screen_height"], 112.0
    _recess("ScopeScreen", bpy.data.objects["ScopeChassis"], sx, sz, -56.0,
            szc, screen)

    grat = []
    for i, (gx, gw) in enumerate(bkit.lay_out([0.6] * 10, gap=22.4)):
        grat.append(bkit.box("_v%d" % i, gw, 0.6, sz, mat=trace,
                             centre=(-56.0 + gx, FRONT + 1.15, szc)))
    for i, (gz, gh) in enumerate(bkit.lay_out([0.6] * 8, gap=15.4)):
        grat.append(bkit.box("_h%d" % i, sx, 0.6, gh, mat=trace,
                             centre=(-56.0, FRONT + 1.15, szc + gz)))
    bkit.join(grat, name="ScopeGraticule")

    # ---- eight soft keys from one grid ------------------------------------
    keys = []
    for i, (kx, kz) in enumerate(bkit.grid_positions(4, 2, 48.0, 20.0)):
        keys.append(bkit.rounded_box(
            "_key%d" % i, 38.0, 7.0, 14.0, r=2.5, segments=2, mat=knob_mat,
            centre=(-56.0 + kx, FRONT + 2.5, 38.0 + kz)))
    bkit.join(keys, name="ScopeSoftKeys")

    # ---- six knobs with a pointer mark, on one computed grid --------------
    knobs = []
    for i, (kx, kz) in enumerate(bkit.grid_positions(3, 2, 34.0, 36.0)):
        knobs.append(bkit.cylinder("_knob%d" % i, 13.0, 14.0, segments=32,
                                   axis="Y", mat=knob_mat,
                                   centre=(kx, FRONT + 6.0, 92.0 + kz)))
        knobs.append(bkit.box("_mark%d" % i, 1.4, 2.0, 10.0, mat=shell,
                              centre=(kx, FRONT - 1.0, 92.0 + kz + 8.0)))
    bkit.join(knobs, name="ScopeKnobs")

    # ---- four BNC inputs on one computed pitch ----------------------------
    bnc = []
    for i, (bx, bw) in enumerate(bkit.lay_out([20.0] * SPEC["bnc_inputs"],
                                               gap=26.0)):
        bnc.append(bkit.cylinder("_bnc%d" % i, 10.0, 9.0, segments=28,
                                 axis="Y", mat=nickel,
                                 centre=(110.0 + bx, FRONT + 3.5, 32.0)))
        bnc.append(bkit.cylinder("_bncp%d" % i, 4.0, 12.0, segments=20,
                                 axis="Y", mat=dark,
                                 centre=(110.0 + bx, FRONT + 3.0, 32.0)))
    bkit.join(bnc, name="ScopeBncInputs")

    # ---- top extraction grille, 8 x 4 holes at 20 mm pitch ---------------
    bkit.perforated_panel("ScopeGrille", 8, 4, 20.0, 20.0, 7.0, 170.0, 90.0,
                          4.0, mat=dark)
    bkit.move(bpy.data.objects["ScopeGrille"], 110.0, 0.0, BODY_Z + CH / 2.0)

    # ---- carry handle: an arch over the chassis --------------------------
    bkit.arc_torus("CarryHandle", 92.0, 7.0, 18.0, 162.0, plane="XZ",
                   centre=(0.0, 0.0, BODY_Z + CH / 2.0), seg_major=40,
                   mat=dark, caps=True)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="chassis_width", mm=400.0, tol=0.8, how="bbox_x",
         part="ScopeChassis"),
    dict(name="chassis_depth", mm=210.0, tol=0.8, how="bbox_y",
         part="ScopeChassis"),
    dict(name="chassis_height", mm=172.0, tol=0.8, how="bbox_z",
         part="ScopeChassis"),
    dict(name="screen_width", mm=230.0, tol=0.8, how="bbox_x",
         part="ScopeScreen"),
    # Six knobs joined into one bank: `diameter` = max(bbox_x, bbox_y) would read
    # the 94 mm BANK WIDTH, so the check names the bank instead.
    dict(name="knob_bank_width", mm=94.0, tol=0.8, how="bbox_x",
         part="ScopeKnobs"),
]