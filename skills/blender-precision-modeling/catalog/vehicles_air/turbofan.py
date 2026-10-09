"""
turbofan -- a high-bypass turbofan: 2800 mm fan, 5300 mm long, on its pylon.

A turbofan is read in three bands: the FAN at the front, the CORE in the
middle, and the EXHAUST at the back, and the fan is the only part with a count
in it -- twenty-two wide-chord blades on a spinner, arrayed about the engine's
own longitudinal X axis.

Two things about the axis are worth stating, because both cost a rebuild:

  * `lathe` revolves about Z. An engine lying along X is a lathe that is then
    `place(..., "X")`d -- passing the axis to `lathe(centre=...)` instead
    leaves the engine standing on end and every axial check measures the
    wrong axis.
  * An open cowl profile leaves the surface open at both ends and the part
    reports 112 non-manifold edges. The nacelle here is a CLOSED profile
    that runs out along the outside and back along the duct, so the lathe
    makes a tube and the mesh is watertight.

The pylon is what puts the engine on the floor: its root box bottom is at z=0
and the engine axis is 1260 mm above that, so nothing hangs below the floor.

Real modern high-bypass turbofan: 2800 mm fan diameter, 22 fan blades,
5300 mm nacelle, 3100 mm fan case, 1200 mm pylon root.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import bpy
import _craft as C

SPEC = dict(
    nacelle_length=5300.0,
    fan_dia=2800.0,
    fan_blades=22,
    spinner_dia=700.0,
    fan_case_dia=3100.0,
    booster_dia=1500.0,
    exhaust_dia=1500.0,
    pylon_chord=3200.0,
    axis_height=1860.0,
)

FR = SPEC["fan_dia"] / 2.0
L = SPEC["nacelle_length"]
X0 = -L / 2.0
X1 = L / 2.0                    # the profile x values are ABSOLUTE, so the
ZC = SPEC["axis_height"]        # aft end is X1, never L -- writing L puts the
                                # tail 2650 mm past the nose and every axial
                                # check measures 7950 mm

CHECKS = [
    dict(name="nacelle_length", mm=5300.0, tol=12.0, how="bbox_x",
         part="FanNacelle"),
    dict(name="fan_disc_span", mm=2773.5, tol=8.0, how="bbox_y",
         part="FanBlades"),
    dict(name="fan_case_dia", mm=3100.0, tol=20.0, how="bbox_y",
         part="FanNacelle"),
    dict(name="spinner_dia", mm=700.0, tol=5.0, how="bbox_y",
         part="FanSpinner"),
    dict(name="booster_dia", mm=1500.0, tol=15.0, how="bbox_y",
         part="FanBooster"),
    dict(name="exhaust_dia", mm=1500.0, tol=15.0, how="bbox_y",
         part="FanExhaust"),
    dict(name="pylon_chord", mm=3200.0, tol=8.0, how="bbox_x",
         part="FanPylon"),
    dict(name="root_on_floor", mm=0.0, tol=6.0, how="z_min",
         part="FanPylonRoot"),
]


def _axial(name, profile, mat, segments=48):
    """A lathe whose axis is X: revolved about Z, then laid down.

    The profile is (radius, x) in millimetres; passing it to `lathe` as
    (radius, z) and then placing it on the X axis is the only way to get a
    body of revolution lying along the engine.
    """
    ob = bkit.lathe(name, profile, segments=segments, mat=mat,
                    cap_ends=True)
    bkit.place(ob, (0.0, 0.0, ZC), "X")
    return ob


def build():
    cowl = bkit.pbr("FanCowl", base=(0.88, 0.88, 0.86), rough=0.22, coat=0.5)
    lip = bkit.pbr("FanLipMetal", base=(0.76, 0.77, 0.79), metal=0.85,
                   rough=0.16)
    blade = bkit.pbr("FanBlade", base=(0.70, 0.71, 0.73), metal=0.85,
                     rough=0.22)
    hot = bkit.pbr("FanHot", base=(0.44, 0.40, 0.36), metal=0.85, rough=0.44)
    pylon_mat = bkit.pbr("FanPylonMat", base=(0.80, 0.80, 0.78), rough=0.30)

    # ---- the nacelle cowl: a CLOSED profile, so it is a solid of
    #      revolution with a duct rather than an open shell -------------
    out_r = [(FR * 1.11, X0), (FR * 1.10, X0 + 220.0),
             (FR * 1.02, X0 + 620.0), (FR * 1.00, X0 + 1200.0),
             (FR * 1.03, L * 0.28), (FR * 0.98, L * 0.42),
             (FR * 0.86, L * 0.47), (FR * 0.84, L * 0.495),
             (FR * 0.78, X1)]
    cowl_prof = [(0.0, out_r[0][1])] + out_r + \
        [(FR * 0.70, X1), (FR * 0.78, X1 * 0.97), (FR * 0.82, X1 * 0.86),
         (FR * 0.90, X1 * 0.52), (FR * 0.90, X0 + 1200.0),
         (FR * 0.92, X0 + 620.0), (FR * 1.02, X0 + 120.0),
         (FR * 1.05, X0), (0.0, X0)]
    _axial("FanNacelle", cowl_prof, cowl, segments=56)

    # ---- the polished inlet lip, rolled back over the front -----------
    _axial("FanInlet",
           [(FR * 1.11, X0 - 40.0), (FR * 1.05, X0 - 40.0),
            (FR * 0.98, X0 + 60.0), (FR * 0.90, X0 + 300.0),
            (FR * 1.02, X0 + 300.0), (FR * 1.11, X0 + 120.0)], lip,
           segments=56)

    # ---- the fan: spinner plus twenty-two wide-chord blades ----------
    _axial("FanSpinner",
           [(0.0, X0 + 60.0), (160.0, X0 + 120.0), (260.0, X0 + 320.0),
            (330.0, X0 + 600.0), (350.0, X0 + 900.0), (320.0, X0 + 1050.0),
            (0.0, X0 + 1050.0)], lip, segments=40)
    blade_h = FR - 360.0
    fb = bkit.rounded_box("FanBlades", 180.0, 42.0, blade_h, r=14.0,
                          segments=2,
                          centre=(X0 + 700.0, 0.0,
                                  ZC + 360.0 + blade_h / 2.0),
                          mat=blade)
    bpy.context.view_layer.update()
    bkit.array_radial(fb, SPEC["fan_blades"], axis="X", centre=(0.0, 0.0, ZC))

    # ---- the booster, the core and the exhaust plug -------------------
    _axial("FanBooster",
           [(0.0, X0 + 1050.0), (750.0, X0 + 1050.0), (750.0, X0 + 1500.0),
            (0.0, X0 + 1500.0)], hot, segments=40)
    _axial("FanCore",
           [(0.0, X0 + 1500.0), (760.0, X0 + 2400.0), (820.0, X0 + 3200.0),
            (820.0, X1 * 0.86), (0.0, X1 * 0.86)], hot, segments=40)
    _axial("FanExhaust",
           [(0.0, X1 * 0.80), (700.0, X1 * 0.84), (750.0, X1 * 0.88),
            (640.0, X1 * 0.96), (420.0, X1), (0.0, X1)], hot, segments=40)

    # ---- the pylon, which is what puts the engine on the floor -------
    bkit.rounded_box("FanPylon", SPEC["pylon_chord"], 420.0, 1200.0,
                     r=100.0, segments=3, centre=(-200.0, 0.0, 600.0),
                     mat=pylon_mat)
    bkit.rounded_box("FanPylonRoot", 900.0, 700.0, 600.0, r=80.0,
                     segments=3, centre=(-200.0, 0.0, 300.0), mat=pylon_mat)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=7,
                note="22 fan blades arrayed about the engine's X axis with "
                     "the orbit radius baked into the mesh.")


def bpy_update():
    import bpy
    bpy.context.view_layer.update()
