"""
bus_shelter -- 4200 x 1700 x 2390 mm kerbside bus shelter: concrete plinth,
four 120 mm square posts, a cantilever roof, glazed back and side walls, two
front panels either side of a 1000 mm boarding gap, a three-slat bench and an
illuminated advertising panel.

Street furniture in the large class, so the repeated elements are structural:
the front glazing is two panels either side of a computed gap, the mullions
come from `grid_positions`, and the bench slats from one `array_linear`. The
plinth overlaps the posts by 0 mm on purpose -- posts start at the plinth top
exactly, and each glass panel overlaps its frame by more than 1 mm so no two
surfaces touch along an edge.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    plinth_width=4100.0,
    plinth_depth=1600.0,
    roof_length=4200.0,
    roof_depth=1700.0,
    post_width=120.0,
    posts=4,
    boarding_gap=1000.0,
    bench_length=3000.0,
    bench_slats=3,
    overall_height=2390.0,
)

PX, PY = 1900.0, 680.0            # post grid
GLAZE_B = 150.0                    # glazing sill height
GLAZE_T = 2050.0                   # glazing head height


def build():
    frame = bkit.pbr("ShelterFrame", base=(0.34, 0.36, 0.38), metal=0.85,
                     rough=0.40)
    roof = bkit.pbr("ShelterRoofMat", base=(0.62, 0.63, 0.64), metal=0.85,
                    rough=0.34)
    glass = bkit.preset("glass")
    concrete = bkit.pbr("ShelterConcrete", base=(0.58, 0.57, 0.55),
                        rough=0.72)
    timber = bkit.pbr("ShelterTimber", base=(0.30, 0.17, 0.08), rough=0.52)
    lit = bkit.pbr("ShelterAdPanel", base=(0.85, 0.87, 0.90), rough=0.16,
                   emission=(0.90, 0.93, 1.0), emission_strength=2.4)

    # ---- plinth and four posts -------------------------------------------
    bkit.rounded_box("ShelterPlinth", SPEC["plinth_width"],
                     SPEC["plinth_depth"], 100.0, r=10.0, segments=2,
                     centre=(0.0, 0.0, 50.0), mat=concrete)
    posts = []
    for i, (px, py) in enumerate(bkit.grid_positions(2, 2, 2 * PX, 2 * PY)):
        tag = "%d%d" % (1 if px > 0 else 0, 1 if py > 0 else 0)
        posts.append(bkit.rounded_box("Post%s" % tag, SPEC["post_width"],
                                      SPEC["post_width"], 2160.0, r=10.0,
                                      segments=2, mat=frame,
                                      centre=(px, py, 1180.0)))
    bkit.join(posts, name="ShelterPosts")

    # ---- roof, overhanging the posts on every side ----------------------
    bkit.rounded_box("ShelterRoof", SPEC["roof_length"], SPEC["roof_depth"],
                     140.0, r=30.0, segments=3, centre=(0.0, 0.0, 2320.0),
                     mat=roof)
    bkit.rounded_box("RoofFascia", SPEC["roof_length"] - 60.0,
                     SPEC["roof_depth"] - 60.0, 30.0, r=14.0, segments=2,
                     centre=(0.0, 0.0, 2238.0), mat=frame)

    # ---- glazed walls: back, two sides, two front panels ------------------
    gh = GLAZE_T - GLAZE_B
    bkit.rounded_box("GlazingBack", 3760.0, 20.0, gh, r=4.0, segments=2,
                     centre=(0.0, PY - 10.0, (GLAZE_B + GLAZE_T) / 2.0),
                     mat=glass)
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        bkit.rounded_box("GlazingSide" + tag, 20.0, 1300.0, gh, r=4.0,
                         segments=2, mat=glass,
                         centre=(side * (PX - 10.0), 0.0,
                                 (GLAZE_B + GLAZE_T) / 2.0))
    # Two front panels either side of a computed boarding gap.
    span = 2 * PX - SPEC["post_width"]
    panel_w = (span - SPEC["boarding_gap"]) / 2.0
    for side, tag in ((-1.0, "L"), (1.0, "R")):
        bkit.rounded_box("GlazingFront" + tag, panel_w, 20.0, gh, r=4.0,
                         segments=2, mat=glass,
                         centre=(side * (SPEC["boarding_gap"] / 2.0 + panel_w
                                         / 2.0), -(PY - 10.0),
                                 (GLAZE_B + GLAZE_T) / 2.0))

    # ---- mullions: one every 600 mm along the back glazing ---------------
    mull = []
    for i, mx in enumerate(bkit.lay_out([50.0] * 6, gap=550.0)):
        mull.append(bkit.box("_m%d" % i, mx[1], 40.0, gh + 20.0, mat=frame,
                             centre=(mx[0], PY - 10.0,
                                     (GLAZE_B + GLAZE_T) / 2.0)))
    bkit.join(mull, name="BackMullions")

    # ---- three-slat bench on two cast supports ---------------------------
    slat = bkit.rounded_box("_bs", SPEC["bench_length"], 100.0, 40.0,
                            r=8.0, segments=2, centre=(0.0, -80.0, 440.0),
                            mat=timber)
    bkit.array_linear(slat, count=SPEC["bench_slats"],
                      offset_mm=(0.0, 110.0, 0.0))
    slat.name = "ShelterSeatSlats"
    for side in (-1.0, 1.0):
        bkit.rounded_box("BenchLeg%.0f" % side, 70.0, 340.0, 420.0, r=12.0,
                         segments=3, mat=frame,
                         centre=(side * 1100.0, 40.0, 230.0))

    # ---- illuminated advertising panel on the back wall ------------------
    bkit.rounded_box("AdPanel", 1200.0, 90.0, 1700.0, r=10.0, segments=2,
                     centre=(-1100.0, PY - 90.0, 1150.0), mat=lit)
    bkit.rounded_box("AdFrame", 1240.0, 60.0, 1740.0, r=10.0, segments=2,
                     centre=(-1100.0, PY - 40.0, 1150.0), mat=frame)

    # ---- a litter bin and a timetable case --------------------------------
    bkit.lathe("ShelterBin", [(0.0, 100.0), (160.0, 100.0), (170.0, 700.0),
                              (185.0, 720.0), (185.0, 760.0), (150.0, 760.0),
                              (150.0, 720.0), (0.0, 700.0)], segments=40,
               mat=frame)
    bkit.rounded_box("Timetable", 420.0, 60.0, 700.0, r=8.0, segments=2,
                     centre=(1400.0, PY - 60.0, 1150.0), mat=lit)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=15)


CHECKS = [
    dict(name="roof_length", mm=4200.0, tol=1.0, how="bbox_x",
         part="ShelterRoof"),
    dict(name="roof_depth", mm=1700.0, tol=1.0, how="bbox_y",
         part="ShelterRoof"),
    dict(name="overall_height", mm=2390.0, tol=2.0, how="bbox_z"),
    dict(name="bench_length", mm=3000.0, tol=1.0, how="bbox_x",
         part="ShelterSeatSlats"),
    dict(name="plinth_width", mm=4100.0, tol=1.0, how="bbox_x",
         part="ShelterPlinth"),
]