"""
wind_turbine -- small horizontal-axis turbine: 2.4 m tapered mast, nacelle on a
horizontal axis, and three lofted blades swept by bkit.array_radial.

Two things this has to get right, and both were wrong in the first attempt:

1. `array_radial` sweeps about the WORLD Z axis, so a blade built straight onto
   the rotor produces a horizontal disc -- a ceiling fan. The blades are built
   in the world XY plane about the origin, swept there, and only THEN swung 90
   degrees about X and lifted to hub height. Rotating after the sweep (and
   translating after the rotation) keeps the rotor plane vertical about a
   horizontal axis.

2. The swept object must have an identity transform. `bkit.lathe` routes through
   `place()`, which sets obj.location, and Blender's array object offset is
   `empty.matrix_world.inverted() @ obj.matrix_world` -- so a part carrying a
   location gets a pure-translation offset and the three copies march off in a
   straight line. `loft` writes coordinates straight into the vertices and
   never touches obj.location, which is exactly why the blade is a loft.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    mast_height=2400.0,
    mast_base_diameter=160.0,
    mast_top_diameter=110.0,
    base_diameter=300.0,
    nacelle_length=700.0,     # along the rotor axis
    nacelle_width=260.0,
    nacelle_height=260.0,
    blade_count=3,
    blade_root_chord=300.0,
    blade_tip_chord=80.0,
    blade_length=1300.0,      # hub face to tip
    rotor_diameter=3200.0,   # 2 x (hub_face + blade_length)
    hub_diameter=124.0,
    # swept envelope of the 3-blade rotor. NOT 2 x tip radius: the blades are
    # twisted, so the chord of the root section rotates into X and the tip
    # section into Z as the array orbits them.
    rotor_tip_span=2811.8,
    blade_reach=2435.1,
    overall_height=4225.0,
)

HUB_Z = SPEC["mast_height"] + 170.0
HUB_FACE = 300.0              # blade root starts here along +X
ROTOR = SPEC["blade_length"]


def _foil(chord, thick, twist_deg, n=24):
    """Closed aerofoil ring as (y, z): chord along +Y, thickness along +Z.

    Returned in 2D because the caller places each ring at its own radius.
    """
    t = math.radians(twist_deg)
    ct, st = math.cos(t), math.sin(t)
    pts = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        c = chord / 2.0 * math.cos(a)
        th = thick / 2.0 * math.sin(a)
        pts.append((c * ct - th * st, c * st + th * ct))
    return pts


def build():
    steel = bkit.preset("anodized")
    white = bkit.preset("white_plastic")
    glass = bkit.pbr("SpinnerGlass", base=(0.85, 0.88, 0.92), rough=0.10)

    mast_h = SPEC["mast_height"]

    # ---- base plate + tapered mast --------------------------------------
    base = bkit.lathe("TurbineBase", [
        (0.0, 0.0),
        (150.0, 0.0),
        (150.0, 22.0),
        (110.0, 32.0),
        (95.0, 32.0),
        (95.0, 24.0),
        (0.0, 24.0),
    ], segments=72, mat=white)

    mast = bkit.lathe("TurbineMast", [
        (0.0, 0.0),             # socketed down into the base plate
        (95.0, 0.0),
        (SPEC["mast_base_diameter"] / 2.0 - 8.0, 88.0),
        (SPEC["mast_top_diameter"] / 2.0, mast_h),
        (0.0, mast_h),
    ], segments=64, mat=steel)

    # ---- nacelle: long axis along Y, which is the rotor axis ------------
    nacelle = bkit.rounded_box("TurbineNacelle", SPEC["nacelle_width"],
                               SPEC["nacelle_length"], SPEC["nacelle_height"],
                               r=70.0, segments=6,
                               centre=(0.0, 0.0, HUB_Z), mat=white)

    # ---- spinner hub on the nose, standing along -Y ---------------------
    hub = bkit.cylinder("TurbineHub", 62.0, 200.0, r2=20.0, segments=64,
                        axis="Y", centre=(0.0, -280.0, HUB_Z), mat=glass)

    # ---- three blades: lofted, swept, then stood upright ----------------
    stations = [
        (0.00, 1.00, 1.00, 18.0),
        (0.22, 0.84, 0.70, 12.0),
        (0.46, 0.66, 0.46, 7.0),
        (0.70, 0.48, 0.28, 4.0),
        (0.88, 0.35, 0.18, 2.0),
        (1.00, 0.27, 0.13, 0.5),
    ]
    secs = []
    for (f, cf, tf, tw) in stations:
        radius = HUB_FACE + ROTOR * f
        secs.append([(radius, py, pz)
                     for (py, pz) in _foil(SPEC["blade_root_chord"] * cf,
                                           48.0 * tf, tw)])
    blade = bkit.loft("TurbineBlades", secs, closed_loop=True,
                      cap_start=True, cap_end=True, mat=white)
    bkit.recalc(blade)
    bkit.array_radial(blade, SPEC["blade_count"])   # true orbit: location == 0

    # stand the rotor up about X and only then lift it to hub height, so the
    # rotation happens about the hub centre rather than the world origin
    blade.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(blade, 0.0, 0.0, HUB_Z)

    return dict(spec=SPEC, parts=5, blades=SPEC["blade_count"])


CHECKS = [
    dict(name="mast_height", mm=2400.0, tol=1.0, how="bbox_z", part="TurbineMast"),
    dict(name="nacelle_length", mm=700.0, tol=0.6, how="bbox_y", part="TurbineNacelle"),
    dict(name="nacelle_width", mm=260.0, tol=0.6, how="bbox_x", part="TurbineNacelle"),
    dict(name="hub_diameter", mm=124.0, tol=0.4, how="bbox_x", part="TurbineHub"),
    dict(name="base_diameter", mm=300.0, tol=0.6, how="diameter", part="TurbineBase"),
    dict(name="rotor_tip_span", mm=2811.8, tol=1.0, how="bbox_z", part="TurbineBlades"),
    dict(name="blade_reach", mm=2435.1, tol=1.0, how="bbox_x", part="TurbineBlades"),
]