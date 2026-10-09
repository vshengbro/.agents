"""
heat_gun -- 2000 W heat gun, 230 mm barrel and 200 mm to the top of the shell.

A heat gun is a barrel, a hot-air nozzle and a handle hung under the rear third
of the barrel. The number that fixes it is the nozzle: 68 mm across the tip and
a 58 mm bore, stepped down from an 88 mm barrel. The barrel's own axis sits at
z = 156 and the grip rakes forward off vertical, which is what makes the
silhouette a heat gun rather than a hair dryer. The heel under the grip is the
floor datum -- its underside is z = 0 by construction, so `sit_on_floor()` is a
no-op and every `top_z` below is the number that was authored.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    barrel_length=230.0,
    barrel_diameter=88.0,
    nozzle_diameter=68.0,
    nozzle_bore=58.0,
    handle_height=200.0,
    grip_height=129.0,      # bbox_z of the grip: the rake adds to the 122 span
    cord_diameter=12.0,
    axis_z=156.0,
)

CHECKS = [
    dict(name="barrel_length", mm=230.0, tol=1.0, how="bbox_x",
         part="HeatBarrel"),
    dict(name="barrel_diameter", mm=88.0, tol=1.0, how="bbox_y",
         part="HeatBarrel"),
    dict(name="nozzle_diameter", mm=68.0, tol=0.8, how="bbox_y",
         part="HeatNozzle"),
    dict(name="handle_height", mm=200.0, tol=1.5, how="top_z",
         part="HeatBarrel"),
    # The grip is raked forward, so its axis-ALIGNED extent is larger than the
    # 122 mm foot-to-barrel span -- which is the number _tool.grip() warns a
    # bbox_z check has to expect.
    dict(name="grip_height", mm=129.0, tol=2.0, how="bbox_z",
         part="HeatGrip"),
    dict(name="cord_diameter", mm=12.0, tol=0.8, how="bbox_y",
         part="HeatCord"),
]

AZ = SPEC["axis_z"]
GZ0 = 34.0                  # grip foot: the heel below it is the floor datum


def build():
    yellow = bkit.preset("yellow_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    cast = bkit.pbr("HeatCast", base=(0.42, 0.43, 0.45), metal=0.70,
                    rough=0.52)
    grip_mat = bkit.pbr("HeatGripRubber", base=(0.07, 0.07, 0.08),
                        rough=0.62)

    # ---- barrel + nozzle: one axis, three diameters ------------------------
    barrel = bkit.lathe("HeatBarrel",
                        [(0.0, 0.0), (44.0, 0.0), (44.0, 186.0),
                         (38.0, 206.0), (38.0, 230.0), (0.0, 230.0)],
                        segments=40, centre=(0, 0, 0), mat=yellow)
    bkit.place(barrel, (-115.0, 0.0, AZ), "X")

    nozzle = bkit.lathe("HeatNozzle",
                        [(29.0, 0.0), (34.0, 0.0), (34.0, 12.0),
                         (30.0, 34.0), (30.0, 58.0), (29.0, 58.0),
                         (29.0, 0.0)],
                        segments=40, cap_ends=False, mat=cast)
    bkit.place(nozzle, (115.0, 0.0, AZ), "X")
    bkit.bore(nozzle, SPEC["nozzle_bore"] / 2.0, 70.0,
              centre=(146.0, 0.0, AZ), axis="X", host_segments=40)

    # ---- handle: raked forward off vertical, heel on the floor -------------
    T.grip("HeatGrip", (-28.0, 0.0, AZ), (-10.0, 0.0, GZ0),
           62.0, 50.0, 56.0, 46.0, mat=grip_mat)
    T.trigger("HeatSwitch", (-6.0, 0.0, AZ), (2.0, 0.0, AZ - 22.0),
              26.0, 14.0, mat=dark)
    # the heel is the floor datum: its underside is z = 0 by construction
    T.shell("HeatHeel", 74.0, 56.0, 34.0, centre=(-10.0, 0.0, 17.0),
            r=8.0, mat=yellow)

    # ---- intake vents + rear grille ---------------------------------------
    T.vent_panel("HeatVent", 5, 2, 13.0, 15.0, 3.4, 60.0, 28.0, 5.0,
                 centre=(-100.0, 0.0, AZ), axis="X", mat=dark)
    T.vent_panel("HeatGrille", 5, 3, 14.0, 14.0, 4.6,
                          70.0, 42.0, 5.0,
                          centre=(-118.0, 0.0, AZ), axis="X", mat=dark)

    # ---- cord --------------------------------------------------------------
    T.coiled_cord("HeatCord", (-170.0, 0.0, 74.0), 26.0,
                  SPEC["cord_diameter"] / 2.0, 20.0, 340.0)
    T.rod("HeatCordTail", (-150.0, 22.0, 48.0), (-118.0, -8.0, 22.0), 6.0)

    return dict(spec=SPEC, parts=10)