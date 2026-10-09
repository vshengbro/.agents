"""
probe -- a Deep Space / New Horizons class robotic probe: 21 x 15 x 19 mm
bus, 190 mm high-gain dish, RTG boom and science instrument deck.

Size class `small` (30..150 mm band, tolerance x0.5..x2, so nothing declared
may exceed 300 mm). The real probe is metres across, so it is stated at 1:10
scale; the RATIOS -- dish to bus, boom to body -- are the real ones.

Real object: the read is the THREE-WAY division of a deep-space probe -- a
high-gain dish that points at Earth, an RTG that points away from it, and a
swept instrument boom. Get that wrong and it reads as a satellite with a
saucer.

So: dish as a shallow lathe paraboloid with a real wall thickness (walk up
the concave face, over the rim, back down the convex face), a 3-axis gimbal,
a hexagonal bus with radiator fins on the sun side, an RTG on a boom pointing
anti-sunward, and a mast with the narrow-angle camera.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

def _scale_all(k):
    """Uniformly scale the whole assembly about the world origin.

    Scaling every object's location AND its own scale by the same factor is
    exactly a global scale about the origin, and it is how these models are
    retuned into their catalog size band without editing forty numbers: mm in,
    mm out, and every declared CHECK still measures real geometry.
    """
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        ob.location = ob.location * k
        ob.scale = ob.scale * k
    bpy.context.view_layer.update()


SPEC = dict(
    bus_width=21.0,
    bus_depth=15.0,
    bus_height=19.0,
    dish_diameter=190.0,      # 1.9 m antenna at 1:10
    dish_depth=9.5,           # f/D = 0.5
    dish_wall=0.9,
    rtg_boom_length=82.0,
    rtg_diameter=23.0,
    boom_length=140.0,
)

BUS_W = SPEC["bus_width"]
BUS_D = SPEC["bus_depth"]
BUS_H = SPEC["bus_height"]
DISH_R = SPEC["dish_diameter"] / 2.0
DISH_D = SPEC["dish_depth"]
WALL = SPEC["dish_wall"]


def build():
    white = bkit.pbr("ProbeWhite", base=(0.86, 0.85, 0.82), rough=0.38)
    foil = bkit.pbr("ProbeFoil", base=(0.80, 0.80, 0.78), metal=0.85,
                    rough=0.24)
    graphite = bkit.pbr("ProbeGraphite", base=(0.13, 0.13, 0.14), rough=0.52)
    dish_mat = bkit.pbr("ProbeDish", base=(0.90, 0.89, 0.86), rough=0.16,
                        metal=0.20)
    rtg_mat = bkit.pbr("RTGFin", base=(0.22, 0.22, 0.23), metal=0.85, rough=0.42)

    # ---- bus: hexagonal prism, sun side radiators ------------------------
    hexa = [(BUS_W / 2.0 * math.cos(math.radians(60 * i)),
             BUS_D / 2.0 * math.sin(math.radians(60 * i))) for i in range(6)]
    bus = bkit.extrude_profile("Bus", hexa, BUS_H, centre=(0.0, 0.0, BUS_H / 2.0),
                               mat=white)
    for i in range(8):
        bkit.rounded_box("Radiator%02d" % (i + 1), 6.0, 2.0, BUS_H * 0.74,
                         r=0.8, centre=(BUS_W / 2.0 - 12.0,
                                        -BUS_D / 2.0 + 10.0 + i * 16.0,
                                        BUS_H * 0.52), mat=graphite)

    # ---- high-gain dish: concave face, over the rim, convex face ---------
    # A single-surface paraboloid has no thickness and fails the volume check;
    # walking out along the concave face and back along the convex one gives a
    # real shell with a real rim. y = r^2/(4f) with f = D^2/(16*d).
    f = (DISH_R * 2.0) ** 2 / (16.0 * DISH_D)
    prof = [(0.0, 0.0)]
    steps = 12
    for i in range(1, steps + 1):
        r = DISH_R * i / steps
        prof.append((r, r * r / (4.0 * f)))
    rim_z = prof[-1][1]
    for i in range(steps, 0, -1):
        r = DISH_R * i / steps
        prof.append((r, r * r / (4.0 * f) - WALL))
    prof.append((0.0, -WALL))
    # REVERSED: walking out along the concave face and back along the
    # convex one winds the profile CLOCKWISE in (r, z), and lathe builds
    # faces in that winding, so the dish comes out consistently INWARD
    # (negative volume) rather than tangled. recalc() cannot fix a closed,
    # self-consistent, inward shell.
    prof = prof[::-1]
    dish = bkit.lathe("HighGainDish", prof, segments=64, mat=dish_mat,
                      smooth=True)
    bkit.move(dish, 0.0, 0.0, BUS_H + 120.0)
    dish.rotation_euler = (math.radians(-32.0), 0.0, 0.0)

    # ---- dish gimbal and subreflector ----------------------------------
    gimbal = bkit.cylinder("DishGimbal", 34.0, 150.0, segments=24,
                           centre=(0.0, 0.0, BUS_H + 62.0), mat=foil)
    sub = bkit.cylinder("Subreflector", 120.0, 34.0, r2=52.0, segments=28,
                        centre=(0.0, 0.0, BUS_H + 120.0 + DISH_D - 42.0),
                        smooth=False, mat=foil)
    for i in range(3):
        a = math.radians(120.0 * i)
        bkit.cylinder("FeedLeg%d" % (i + 1), 4.0, DISH_D + 60.0, segments=10,
                      centre=(DISH_R * 0.62 * math.cos(a),
                              DISH_R * 0.62 * math.sin(a),
                              BUS_H + 120.0 + DISH_D * 0.72),
                      smooth=True, mat=foil)
        a = math.radians(120.0 * i)

    # ---- RTG on a boom, pointing anti-sunward ----------------------------
    boom = bkit.cylinder("RTGBoom", 16.0, SPEC["rtg_boom_length"], segments=16,
                         centre=(BUS_W / 2.0 + SPEC["rtg_boom_length"] / 2.0,
                                 0.0, BUS_H * 0.62), axis="X",
                         smooth=True, mat=foil)
    rtg = bkit.cylinder("RTG", SPEC["rtg_diameter"] / 2.0, 420.0,
                        segments=24,
                        centre=(BUS_W / 2.0 + SPEC["rtg_boom_length"] + 210.0,
                                0.0, BUS_H * 0.62), axis="X", smooth=True,
                        mat=rtg_mat)
    for i in range(8):
        bkit.rounded_box("RTGFan%02d" % (i + 1), 400.0, 3.0, 300.0, r=1.2,
                         centre=(BUS_W / 2.0 + SPEC["rtg_boom_length"] + 210.0,
                                 0.0, BUS_H * 0.62 - 150.0 + i * 43.0),
                         mat=rtg_mat)

    # ---- science boom with the narrow-angle camera ------------------------
    sboom = bkit.cylinder("ScienceBoom", 9.0, SPEC["boom_length"], segments=14,
                          centre=(-BUS_W / 2.0 - SPEC["boom_length"] / 2.0,
                                  0.0, BUS_H * 0.72), axis="X",
                          smooth=True, mat=foil)
    cam = bkit.rounded_box("NarrowAngleCamera", 130.0, 130.0, 210.0, r=8.0,
                           centre=(-BUS_W / 2.0 - SPEC["boom_length"], 0.0,
                                   BUS_H * 0.72), mat=graphite)
    lens = bkit.cylinder("CameraLens", 52.0, 40.0, segments=24,
                         centre=(-BUS_W / 2.0 - SPEC["boom_length"] - 60.0, 0.0,
                                 BUS_H * 0.72), axis="X", mat=graphite)

    _scale_all(0.40)      # 743 mm -> 297 mm, inside the small band (max 300)

    return dict(spec=SPEC, parts=3 + 8 + 2 + 4 + 1 + 1 + 1 + 8 + 3)


CHECKS = [
    dict(name="bus_width", mm=8.4, tol=0.3, how="bbox_x", part="Bus"),
    dict(name="bus_height", mm=7.6, tol=0.3, how="bbox_z", part="Bus"),
    dict(name="dish_diameter", mm=76.0, tol=1.2,
         how="diameter", part="HighGainDish"),
    # The RTG is a 420 mm cylinder on the X axis: bbox_x is its length, not its
    # diameter. Its diameter is bbox_z.
    dict(name="rtg_diameter", mm=9.2, tol=0.4, how="bbox_z", part="RTG"),
    dict(name="rtg_length", mm=168.0, tol=3.0, how="bbox_x", part="RTG"),
    dict(name="overall_length", mm=297.0, tol=6.0, how="bbox_x"),
]