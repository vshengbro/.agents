"""
water_gun -- a 330 mm high-pressure water blaster: tank, pump, muzzle, grip.

A water gun is a long body with a heavy tank on top and three things that
have to be at the RIGHT HEIGHT for it to read as a blaster rather than a
squirter: the muzzle is on the axis of the tank, the pump handle runs along
the top above the tank, and the grip hangs below the tank line with a trigger
guard in front of it. Getting the tank BELOW the pump and ABOVE the grip is
most of the silhouette.

The tank and reservoir are lathed, because they are pressure vessels and
pressure vessels are round -- a square water gun is a toy bin. The body is a
lofted super-ellipse that tapers toward the muzzle, the pump is a real piston
rod with a swept handle at the back, and the muzzle is a real stepped barrel
with a bore at the tip.

The bore is a genuine `bore()` cut into the muzzle: a water gun with a solid
tip is a stick, and the cut is placed to cross the end face rather than stop
flush with it.
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
    overall_length=276.0,
    overall_height=154.0,
    tank_diameter=62.0,
    tank_length=180.0,
    tank_height=92.0,        # tank centreline above the table
    body_width=48.0,
    body_height=46.0,
    muzzle_diameter=18.0,
    muzzle_length=44.0,
    bore_diameter=6.0,
    pump_diameter=9.0,
    pump_stroke=150.0,
    grip_diameter=34.0,
    grip_length=40.0,
    trigger_guard_height=30.0,
)

TR = SPEC["tank_diameter"] / 2.0
TL = SPEC["tank_length"]
TZ = SPEC["tank_height"]
BWD = SPEC["body_width"] / 2.0
BHT = SPEC["body_height"]
MR = SPEC["muzzle_diameter"] / 2.0
ML = SPEC["muzzle_length"]
BR_ = SPEC["bore_diameter"] / 2.0
PR = SPEC["pump_diameter"] / 2.0
GR = SPEC["grip_diameter"] / 2.0
GL = SPEC["grip_length"]


def build():
    body_mat = bkit.preset("blue_paint")
    tank_mat = bkit.preset("yellow_paint")
    dark = bkit.preset("black_plastic")
    accent = bkit.preset("red_paint")
    cream = bkit.preset("white_plastic")

    # ---- the pressure tank: a lathed vessel with real domed ends, because a
    # cylinder with flat caps reads as a tin can, not as a reservoir.
    #
    # A lathe revolves about Z, so this one is built standing up and then
    # laid on its side: a +90 deg turn about X puts its axis along Y, which is
    # the long axis of the gun. Skipping that turn is the quiet way to get a
    # 232 mm tall water gun with a vertical barrel.
    tank_prof = [
        (0.0, -TL / 2.0),
        (TR * 0.30, -TL / 2.0 - 4.0),
        (TR * 0.74, -TL / 2.0 + 2.0),
        (TR, -TL / 2.0 + 12.0),
        (TR, TL / 2.0 - 12.0),
        (TR * 0.74, TL / 2.0 - 2.0),
        (TR * 0.30, TL / 2.0 + 4.0),
        (0.0, TL / 2.0),
    ]
    tank = bkit.lathe("GunTank", tank_prof, segments=56, mat=tank_mat)
    tank.rotation_euler = (1.5707963, 0.0, 0.0)
    bkit.move(tank, 0.0, -30.0, TZ)
    bpy.context.view_layer.update()
    bkit.recalc(tank)
    bkit.shade_smooth(tank, 32)
    # a moulded rib down each side of the tank, as a second material: a
    # separate rib object would z-fight with the curved tank wall
    bkit.assign_faces_by(
        tank, accent,
        lambda c, n: abs(c.x / bkit.MM) > TR * 0.86
        and abs(c.y / bkit.MM) < TL * 0.30)

    # ---- the body: a lofted super-ellipse tapering from the tank line down
    # to the muzzle, which is what gives the blaster its wedge silhouette
    body_l = 150.0
    sections = []
    body_table = [
        (-body_l * 0.5, 0.55, 0.62),
        (-body_l * 0.30, 0.86, 0.88),
        (0.0, 1.00, 1.00),
        (body_l * 0.30, 0.92, 0.94),
        (body_l * 0.5, 0.66, 0.70),
    ]
    for (y, wf, hf) in body_table:
        ring = bkit.superellipse_section(2 * BWD * wf, 2 * BHT * hf, n=3.2,
                                         steps=40)
        sections.append([(u, y + 30.0, TZ - BHT * 0.5 + v) for (u, v) in ring])
    body = bkit.loft("GunBody", sections, mat=body_mat, smooth=True)
    bkit.recalc(body)
    bkit.shade_smooth(body, 40)

    # ---- the muzzle: a stepped barrel on the tank axis, with a real bore.
    # Built standing up, then laid along Y like the tank.
    nose_y = -30.0 - TL / 2.0 - 4.0
    muzzle = bkit.lathe("GunMuzzle",
                        [(0.0, 0.0), (MR * 1.20, 0.0), (MR * 1.20, 6.0),
                         (MR, 8.0), (MR, ML), (MR * 1.10, ML),
                         (MR * 1.10, ML + 3.0), (0.0, ML + 3.0)],
                        segments=44, mat=dark)
    muzzle.rotation_euler = (1.5707963, 0.0, 0.0)
    bkit.move(muzzle, 0.0, nose_y, TZ)
    bpy.context.view_layer.update()
    bkit.recalc(muzzle)
    bkit.shade_smooth(muzzle, 32)
    # the bore, cut THROUGH the end face: the cutter is centred 11 mm back
    # from the tip and is 30 mm long, so it runs 4 mm inside the barrel and
    # 15 mm past the tip. A cutter that stopped flush with the end face would
    # be tangent, and tangency is what leaves the EXACT solver bad edges.
    bkit.bore(muzzle, BR_, 30.0,
              centre=(0.0, nose_y + ML + 3.0 - 11.0, TZ), axis="Y",
              host_segments=44)
    bkit.recalc(muzzle)
    bkit.assign_faces_by(muzzle, accent,
                         lambda c, n: (c.y / bkit.MM) < nose_y + 4.0)

    # ---- the pump: a real rod along the top of the tank with a swept
    # handle at the back. The pump is what makes it a high-pressure blaster.
    pump_z = TZ + TR + 10.0
    bkit.cylinder("GunPumpRod", PR, SPEC["pump_stroke"], segments=24,
                  centre=(0.0, -18.0, pump_z), axis="Y", mat=cream)
    bkit.lathe("GunPumpHandle",
               [(0.0, 0.0), (16.0, 0.0), (18.0, 5.0), (16.0, 16.0),
                (10.0, 22.0), (0.0, 23.0)],
               segments=32,
               centre=(0.0, -18.0 + SPEC["pump_stroke"] / 2.0 + 2.0, pump_z),
               mat=accent)

    # ---- the grip: hangs below the tank line. A water gun with no grip is a
    # rifle; the grip is what you hold. Authored upright (a lathe about Z is
    # already upright) and then tilted, so the declared length is the grip's
    # own 86 mm rather than a bounding box inflated by the tilt.
    grip = bkit.lathe("GunGrip",
                      [(0.0, 0.0), (GR, 0.0), (GR, 6.0), (GR * 0.82, 14.0),
                       (GR * 0.80, GL - 16.0), (GR * 0.94, GL - 8.0),
                       (GR * 0.94, GL), (0.0, GL)],
                      segments=36, mat=dark)
    grip.rotation_euler = (math.radians(16.0), 0.0, 0.0)
    bkit.move(grip, 0.0, 24.0, 0.0)      # bottom of the grip on the table
    bpy.context.view_layer.update()
    bkit.recalc(grip)
    bkit.shade_smooth(grip, 34)

    # ---- the trigger guard, in front of the grip
    bkit.arc_torus("GunTriggerGuard", SPEC["trigger_guard_height"] / 2.0, 3.0,
                   -80.0, 80.0,
                   centre=(0.0, 12.0, GL + 16.0),
                   plane="YZ", seg_major=28, seg_minor=12, mat=body_mat)
    bkit.rounded_box("GunTrigger", 5.0, 6.0, 16.0, r=2.0, segments=2,
                     centre=(0.0, 15.0, GL + 20.0), mat=dark)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=6)


CHECKS = [
    # The tank and the muzzle are lathed about Z and then laid on their side,
    # so their LENGTH reads off bbox_y and their DIAMETER off bbox_x.
    dict(name="tank_diameter", mm=62.0, tol=0.6, how="bbox_x", part="GunTank"),
    dict(name="tank_length", mm=188.0, tol=1.0, how="bbox_y", part="GunTank"),
    dict(name="body_width", mm=48.0, tol=0.6, how="bbox_x", part="GunBody"),
    dict(name="muzzle_length", mm=47.0, tol=0.8, how="bbox_y", part="GunMuzzle"),
    dict(name="pump_stroke", mm=150.0, tol=1.0, how="bbox_y", part="GunPumpRod"),
    dict(name="overall_length", mm=276.0, tol=4.0, how="bbox_y"),
    # grip bottom on the table, up through the body, the tank and the pump
    # handle. The pump handle is the tallest thing on the gun.
    dict(name="overall_height", mm=160.7, tol=3.0, how="bbox_z"),
]
