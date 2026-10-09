"""
chainsaw -- 16 inch petrol chainsaw: 450 mm guide bar, 616 mm overall.

Two things decide whether a chainsaw reads. The BAR: 450 mm between the tip and
the sprocket nose, tapering from 32 mm at the root to 8 mm at the tip, with a
real chain loop running round it -- two straight runs and two arcs, not a
cylinder. And the ENGINE: a fan cover over the sprocket and a wrap handle over
the top, so the silhouette has a mass at the front and a handle loop at the
back.

The bar's underside is z = 0 -- a chainsaw always rests on its guide bar and
the chain wrapped round it, so that is the floor datum here.
"""
import math
import os
import sys

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    bar_length=449.0,
    bar_width=32.0,
    bar_thickness=8.0,
    chain_diameter=10.0,
    sprocket_cover_diameter=124.0,
    engine_length=240.0,
    overall_length=747.0,
    top_z=294.0,
)

CHECKS = [
    dict(name="bar_length", mm=449.0, tol=2.0, how="bbox_x", part="SawBar"),
    dict(name="bar_width", mm=32.0, tol=1.0, how="bbox_z", part="SawBar"),
    dict(name="bar_thickness", mm=8.0, tol=0.5, how="bbox_y", part="SawBar"),
    dict(name="chain_diameter", mm=10.0, tol=0.6, how="bbox_y",
         part="SawChainTop"),
    dict(name="sprocket_cover_diameter", mm=124.0, tol=1.0, how="diameter",
         part="SawSprocketCover"),
    dict(name="engine_length", mm=240.0, tol=1.5, how="bbox_x",
         part="SawEngine"),
    dict(name="overall_length", mm=747.0, tol=4.0, how="longest", part=None),
    dict(name="top_z", mm=294.0, tol=3.0, how="top_z", part=None),
]

BAR_X0, BAR_X1 = -40.0, 410.0        # bar root / nose-tip stations
BAR_H0, BAR_H1 = 16.0, 13.0          # half height at the root and at the nose


def bar_profile():
    """The guide bar outline: tapering flanks and a semicircular nose."""
    poly = []
    nose_c, nose_r = 396.0, BAR_H1
    steps = 24
    for i in range(steps + 1):                       # nose, top -> bottom
        a = math.pi / 2.0 - math.pi * i / steps
        poly.append((nose_c + math.cos(a) * nose_r,
                     math.sin(a) * nose_r))
    for i in range(13):                               # bottom flank
        t = i / 12.0
        poly.append((396.0 - (396.0 - BAR_X0) * t,
                     -BAR_H1 + (BAR_H1 - BAR_H0) * t))
    for i in range(13):                               # top flank
        t = 1.0 - i / 12.0
        poly.append((396.0 - (396.0 - BAR_X0) * t,
                     BAR_H0 - (BAR_H0 - BAR_H1) * t))
    return poly


def build():
    orange = bkit.preset("red_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    cast = bkit.pbr("SawCast", base=(0.38, 0.39, 0.41), metal=0.75,
                    rough=0.48)
    grip_mat = bkit.pbr("SawGripRubber", base=(0.07, 0.07, 0.08),
                        rough=0.62)

    # ---- guide bar --------------------------------------------------------
    bar = bkit.extrude_profile("SawBar", bar_profile(), SPEC["bar_thickness"],
                               mat=cast)
    bar.rotation_euler = (math.pi / 2.0, 0.0, 0.0)
    bar.location = bkit.v(0.0, 0.0, BAR_H0)
    bpy.context.view_layer.update()
    bkit.recalc(bar)          # extrude_profile does not recalc, and the
                              # outline is wound anticlockwise in outline space

    # ---- chain: two straight runs and two arcs around the bar ------------
    for i, z in enumerate((BAR_H0 + 4.0, -(BAR_H0 + 4.0))):
        T.rod("SawChain%s" % ("Top" if z > 0 else "Bottom"),
              (30.0, 0.0, z), (396.0, 0.0, z * BAR_H1 / BAR_H0),
              SPEC["chain_diameter"] / 2.0, mat=steel)
    bkit.arc_torus("SawChainNose", 17.0, 5.0, -88.0, 88.0,
                   centre=(396.0, 0.0, 0.0), plane="XZ", seg_major=28,
                   mat=steel)
    bkit.arc_torus("SawChainTail", 34.0, 5.0, 92.0, 268.0,
                   centre=(4.0, 0.0, 0.0), plane="XZ", seg_major=28,
                   mat=steel)

    # ---- sprocket cover + clutch drum -------------------------------------
    cover = bkit.lathe("SawSprocketCover",
                       [(0.0, 0.0), (62.0, 0.0), (62.0, 56.0),
                        (54.0, 62.0), (0.0, 62.0)],
                       segments=40, centre=(0, 0, 0), mat=orange)
    bkit.place(cover, (-92.0, 0.0, 0.0), "X")
    T.knob("SawClutch", 40.0, 24.0, (30.0, 78.0, 90.0), mat=dark)

    # ---- engine + rear handle --------------------------------------------
    T.shell("SawEngine", SPEC["engine_length"], 116.0, 132.0,
            centre=(-150.0, 0.0, 96.0), r=22.0, mat=orange)
    T.vent_panel("SawVent", 4, 2, 16.0, 18.0, 5.0, 60.0, 32.0, 5.0,
                 centre=(-268.0, 0.0, 96.0), axis="X", mat=dark)
    bkit.arc_torus("SawRearHandle", 54.0, 13.0, 40.0, 320.0,
                   centre=(-262.0, 0.0, 148.0), plane="XZ", seg_major=30,
                   mat=grip_mat)
    T.strut("SawRearPost", (-262.0, 0.0, 196.0), (-262.0, 0.0, 232.0),
            26.0, 30.0, mat=grip_mat)

    # ---- wrap handle over the top ----------------------------------------
    for i, s in enumerate((1, -1)):
        T.rod("SawWrapPost%d" % i, (-150.0, s * 40.0, 160.0),
              (-60.0, s * 78.0, 220.0), 12.0, mat=grip_mat)
    T.rod("SawWrapBar", (-60.0, -78.0, 220.0), (-60.0, 78.0, 220.0), 12.0,
          mat=grip_mat)
    T.strut("SawThrottle", (-150.0, 0.0, 168.0), (-104.0, 0.0, 196.0),
            22.0, 16.0, mat=dark)

    # ---- oil + fuel caps --------------------------------------------------
    T.knob("SawOilCap", 34.0, 26.0, (-210.0, 30.0, 168.0), mat=dark)
    T.knob("SawFuelCap", 38.0, 30.0, (-210.0, -30.0, 170.0), mat=cast)

    return dict(spec=SPEC, parts=15)