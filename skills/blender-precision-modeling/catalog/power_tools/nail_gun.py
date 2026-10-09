"""
nail_gun -- pneumatic framing nailer, 356 mm long, 300 mm to the top of the
magazine.

A nail gun is three masses in a line: the driver cylinder up top, a long
straight magazine raked down at 12 degrees, and the nose/contact tip at the
front end. The number that fixes it is the magazine -- 340 mm of it -- because
that is what makes a nail gun a nail gun and not a rivet gun.

The magazine's lower lip is z = 0, so the tool rests on the magazine the way a
framing nailer does on a joist.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _tool as T

SPEC = dict(
    driver_length=210.0,
    driver_diameter=64.0,
    magazine_length=340.0,
    magazine_span=336.3,
    magazine_width=44.0,
    magazine_rake_deg=12.0,
    nose_length=52.0,
    overall_height=276.0,
    grip_span=132.0,
)

CHECKS = [
    dict(name="driver_length", mm=210.0, tol=1.0, how="bbox_x",
         part="NailDriver"),
    dict(name="driver_diameter", mm=64.0, tol=0.8, how="bbox_y",
         part="NailDriver"),
    dict(name="magazine_span", mm=336.3, tol=1.0, how="bbox_x",
         part="NailMagazine"),
    dict(name="magazine_width", mm=44.0, tol=0.8, how="bbox_y",
         part="NailMagazine"),
    dict(name="nose_length", mm=52.0, tol=0.8, how="bbox_x", part="NailNose"),
    dict(name="grip_height", mm=143.0, tol=2.0, how="bbox_z",
         part="NailGrip"),
    dict(name="overall_height", mm=276.0, tol=2.0, how="top_z", part=None),
]


def build():
    orange = bkit.preset("yellow_paint")
    dark = bkit.preset("black_plastic")
    steel = bkit.preset("steel")
    grip_mat = bkit.pbr("NailGripRubber", base=(0.07, 0.07, 0.08),
                        rough=0.62)
    cast = bkit.pbr("NailCast", base=(0.46, 0.47, 0.49), metal=0.80,
                    rough=0.46)

    # ---- driver: a horizontal cylinder with a cast head -------------------
    driver = bkit.lathe("NailDriver",
                        [(0.0, 0.0), (32.0, 0.0), (32.0, 190.0),
                         (26.0, 210.0), (0.0, 210.0)],
                        segments=36, centre=(0, 0, 0), mat=orange)
    bkit.place(driver, (-210.0, 0.0, 244.0), "X")
    T.shell("NailHead", 66.0, 76.0, 80.0, centre=(24.0, 0.0, 234.0),
            r=16.0, mat=cast)
    T.vent_panel("NailVent", 5, 2, 14.0, 16.0, 4.0, 66.0, 30.0, 5.0,
                 centre=(-150.0, 0.0, 244.0), axis="X", mat=dark)

    # ---- grip + trigger ----------------------------------------------------
    T.grip("NailGrip", (-92.0, 0.0, 230.0), (-122.0, 0.0, 98.0),
           56.0, 52.0, 52.0, 46.0, mat=grip_mat, bow=6.0)
    T.trigger("NailTrigger", (-70.0, 0.0, 226.0), (-76.0, 0.0, 204.0),
              28.0, 14.0, mat=dark)

    # ---- nose: the contact trip and the driver guide ----------------------
    T.shell("NailNose", SPEC["nose_length"], 46.0, 132.0,
            centre=(46.0, 0.0, 176.0), r=8.0, mat=cast)
    T.strut("NailTrip", (46.0, 0.0, 112.0), (66.0, 0.0, 96.0),
            34.0, 12.0, mat=steel)
    T.rod("NailNoseSpring", (58.0, 0.0, 128.0), (58.0, 0.0, 240.0), 7.0,
          mat=steel)

    # ---- magazine: a raked channel whose rail underside is z = 0 ----------
    # The 12 degree rake means the magazine's projected span (336.3 mm) is
    # shorter than its own length (340 mm); both numbers are declared and the
    # check measures the projection, because that is what a bounding box sees.
    mag = bkit.rounded_box("NailMagazine", SPEC["magazine_length"],
                           SPEC["magazine_width"], 26.0, r=4.0, segments=2,
                           centre=(0.0, 0.0, 0.0), mat=steel)
    mag.rotation_euler = (0.0, math.radians(SPEC["magazine_rake_deg"]), 0.0)
    mag.location = bkit.v(-90.0, 0.0, 86.0)
    import bpy
    bpy.context.view_layer.update()
    rail = bkit.rounded_box("NailMagRail", SPEC["magazine_length"] - 40.0,
                            20.0, 16.0, r=3.0, segments=2,
                            centre=(0.0, 0.0, 0.0), mat=cast)
    rail.rotation_euler = (0.0, math.radians(SPEC["magazine_rake_deg"]), 0.0)
    rail.location = bkit.v(-110.0, 0.0, 39.0)
    bpy.context.view_layer.update()
    T.rod("NailFollower", (-238.0, 0.0, 72.0), (-246.0, 0.0, 110.0), 15.0,
          mat=dark)

    # ---- air inlet + hose -------------------------------------------------
    bkit.cylinder("NailAirFitting", 15.0, 40.0, segments=20,
                  centre=(-250.0, 0.0, 244.0), axis="X", mat=steel)
    T.coiled_cord("NailHose", (-300.0, 0.0, 168.0), 40.0, 8.0, 20.0, 340.0,
                  mat=dark)

    return dict(spec=SPEC, parts=12)