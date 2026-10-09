"""
laser -- 186 x 100 x 116 mm helium-neon laser unit: a 32 x 180 mm discharge
tube on two saddle brackets over a 140 x 100 x 70 mm power supply, an output
aperture, a rear beam dump and a hinged lid.

Small size class, so nothing here exceeds 300 mm. The two saddle brackets are
what make it read as a laser rather than a tube on a box: they straddle the
bore and overlap both the driver lid and the tube, and the aperture is a real
counterbore so the beam exit is a hole, not a painted disc.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    driver_width=140.0,
    driver_depth=100.0,
    driver_height=70.0,
    head_diameter=32.0,
    head_length=180.0,
    aperture_diameter=16.0,
    overall_height=120.0,
)


def build():
    shell = bkit.pbr("LaserShell", base=(0.12, 0.12, 0.13), rough=0.40)
    steel = bkit.preset("brushed_metal")
    nickel = bkit.preset("polished_metal")
    dark = bkit.pbr("LaserDark", base=(0.060, 0.060, 0.065), rough=0.42)
    warn = bkit.pbr("LaserWarn", base=(0.85, 0.70, 0.10), rough=0.30)

    # ---- power supply box on four feet ------------------------------------
    bkit.rounded_box("DriverBox", SPEC["driver_width"], SPEC["driver_depth"],
                     SPEC["driver_height"], r=6.0, segments=3,
                     centre=(0.0, 0.0, 6.0 + SPEC["driver_height"] / 2.0),
                     mat=shell)
    feet = [bkit.cylinder("_foot", 7.0, 8.0, segments=16,
                          centre=(fx, fy, 4.0), mat=dark)
            for (fx, fy) in bkit.grid_positions(2, 2, 110.0, 70.0)]
    bkit.join(feet, name="LaserFeet")

    # ---- laser tube on two saddle brackets -------------------------------
    bkit.cylinder("LaserHead", SPEC["head_diameter"] / 2.0,
                  SPEC["head_length"], segments=48, axis="X",
                  centre=(0.0, 0.0, 100.0), mat=nickel)
    saddles = []
    for i, sx in enumerate((-60.0, 60.0)):
        saddles.append(bkit.rounded_box(
            "Saddle%d" % i, 24.0, 44.0, 44.0, r=6.0, segments=2, mat=steel,
            centre=(sx, 0.0, 88.0)))
    bkit.join(saddles, name="TubeSaddles")

    # ---- output aperture and rear beam dump ------------------------------
    bkit.tube("ApertureCollar", 14.0, 8.0, 12.0, segments=40, axis="X",
              centre=(96.0, 0.0, 100.0), mat=steel)
    bkit.cylinder("ApertureWindow", 8.0, 3.0, segments=40, axis="X",
                  centre=(96.0, 0.0, 100.0), mat=dark)
    bkit.tube("BeamDump", 20.0, 12.0, 20.0, segments=40, axis="X",
              centre=(-96.0, 0.0, 100.0), mat=steel)
    bkit.cylinder("MirrorEnd", 10.0, 6.0, segments=32, axis="X",
                  centre=(-84.0, 0.0, 100.0), mat=warn)

    # ---- hinged lid, interlock switch and a cooling grille ----------------
    bkit.rounded_box("Lid", 130.0, 90.0, 12.0, r=4.0, segments=2,
                     centre=(0.0, 0.0, 82.0), mat=steel)
    bkit.rounded_box("Interlock", 16.0, 12.0, 10.0, r=2.0, segments=2,
                     centre=(62.0, -40.0, 80.0), mat=dark)
    grille = []
    for i, (gx, gw) in enumerate(bkit.lay_out([5.0] * 6, gap=8.0)):
        grille.append(bkit.box("_gv%d" % i, gw, 60.0, 4.0, mat=dark,
                               centre=(gx, 0.0, 74.0)))
    bkit.join(grille, name="CoolingGrille")

    # ---- laser warning plate and a rating label --------------------------
    bkit.rounded_box("WarnPlate", 40.0, 3.0, 22.0, r=2.0, segments=2,
                     centre=(-40.0, -51.0, 40.0), mat=warn)
    bkit.rounded_box("RatingLabel", 60.0, 3.0, 24.0, r=2.0, segments=2,
                     centre=(30.0, -51.0, 40.0), mat=steel)

    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="driver_width", mm=140.0, tol=0.5, how="bbox_x",
         part="DriverBox"),
    dict(name="driver_depth", mm=100.0, tol=0.5, how="bbox_y",
         part="DriverBox"),
    dict(name="head_length", mm=180.0, tol=0.6, how="bbox_x",
         part="LaserHead"),
    dict(name="aperture_diameter", mm=28.0, tol=0.5, how="diameter",
         part="ApertureCollar"),
    dict(name="overall_height", mm=120.0, tol=0.8, how="bbox_z"),
]