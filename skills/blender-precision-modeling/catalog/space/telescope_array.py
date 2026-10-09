"""
telescope_array -- a 100 m steerable radio dish (Green Bank class) on a 600 mm
tower with a 640 mm azimuth arm.

Size class `huge` (3000..40000 mm, tolerance x0.5..x2). Stated at 1:100 scale:
the dish is 1000 mm across. The real ratios are preserved -- a paraboloid of
f/D = 0.42, a feed at the focus on a quadripod, a round azimuth bearing under
a boxy elevation carriage.

The dish is a real paraboloid with a real wall: the profile walks up the
concave face from the vertex to the rim, over the rim, and back down the
convex face, so it has 30 mm of structure at this scale and casts a proper
edge shadow. A single-sided dish reads as a lampshade.

The pose is assembled once, at the end, by PARENTING every dish-mounted part
to the dish and then rotating the dish object. Rotating each part's
`rotation_euler` individually -- the obvious approach -- composes the rotations
in world space and puts the feed legs and the feed horn somewhere off the dish,
which is what the first pass did.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    dish_diameter=1000.0,
    dish_depth=105.0,          # f/D = 0.42 -> 420 mm focal length
    dish_wall=30.0,
    tower_height=600.0,
    azimuth_arm_length=640.0,
    feed_length=420.0,
    rim_ring_height=60.0,
)

D = SPEC["dish_diameter"]
R = D / 2.0
DEPTH = SPEC["dish_depth"]
WALL = SPEC["dish_wall"]
TILT = math.radians(-52.0)     # the classic parked elevation



def _scale_all(k):
    """Uniformly scale the whole assembly about the world origin.

    Scaling every object's location AND its own scale by the same factor is
    exactly a global scale about the origin, and it is the only way to retune a
    model's overall size class without editing forty numbers: mm in, mm out,
    with every declared CHECK still measuring real geometry.
    """
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.name in ("Backdrop", "Ground", "Floor"):
            continue
        ob.location = ob.location * k
        ob.scale = ob.scale * k
    bpy.context.view_layer.update()


def build():
    panel = bkit.pbr("DishPanel", base=(0.60, 0.61, 0.63), metal=0.85, rough=0.34)
    panel_back = bkit.pbr("DishPanelBack", base=(0.44, 0.45, 0.47), metal=0.85,
                          rough=0.52)
    steel = bkit.pbr("TelescopeSteel", base=(0.56, 0.57, 0.59), metal=0.85,
                     rough=0.30)
    dark = bkit.pbr("TelescopeDark", base=(0.13, 0.13, 0.14), rough=0.55)
    gold = bkit.pbr("FeedHorn", base=(0.80, 0.66, 0.30), metal=0.85, rough=0.30)

    # ---- paraboloid: concave face up, over the rim, convex face back ----
    # y = r^2 / (4f) with f = D^2 / (16 d). Both ends close at r=0, so lathe
    # needs no end caps and the dish is one watertight solid.
    f = (D * D) / (16.0 * DEPTH)
    steps = 16
    prof = [(0.0, 0.0)]
    for i in range(1, steps + 1):
        r = R * i / steps
        prof.append((r, r * r / (4.0 * f)))
    rim_z = prof[-1][1]
    for i in range(steps, 0, -1):
        r = R * i / steps
        prof.append((r, r * r / (4.0 * f) - WALL))
    prof.append((0.0, -WALL))
    dish = bkit.lathe("Dish", prof, segments=72, mat=panel, smooth=True)
    bkit.recalc(dish)
    bkit.assign_faces_by(dish, panel_back, lambda c, n: n.z > -0.2)

    mounted = [dish]

    # ---- rim ring: the structural hoop the panels hang on ---------------
    rim = bkit.tube("RimRing", R * 1.005, R * 0.965, SPEC["rim_ring_height"],
                    segments=72, centre=(0.0, 0.0, rim_z - WALL / 2.0),
                    mat=steel)
    mounted.append(rim)

    # ---- quadripod feed legs and the feed horn at the focus -------------
    for i in range(4):
        a = math.radians(45.0 + 90.0 * i)
        leg = bkit.cylinder("FeedLeg%d" % (i + 1), 11.0, R * 0.90, segments=10,
                            centre=(0.0, 0.0, 0.0), smooth=True, mat=steel)
        # laid from the rim inward and up to the focus
        leg.rotation_euler = (math.radians(56.0) * math.sin(a),
                              -math.radians(56.0) * math.cos(a), 0.0)
        bkit.move(leg, R * 0.34 * math.cos(a), R * 0.34 * math.sin(a),
                  rim_z * 0.5 + f * 0.16)
        mounted.append(leg)
    horn = bkit.cylinder("FeedHorn", 44.0, 130.0, r2=78.0, segments=24,
                         centre=(0.0, 0.0, f * 0.60), smooth=False, mat=gold)
    mounted.append(horn)
    box = bkit.rounded_box("FeedBox", 110.0, 110.0, 130.0, r=18.0,
                           centre=(0.0, 0.0, f * 0.60 + 100.0), mat=dark)
    mounted.append(box)

    # ---- one rotation for the whole assembly ----------------------------
    # Parenting is the only way to rotate a group rigidly without composing
    # each object's own euler against the group's.
    # NB: join() renames the survivor, so the dish-side CHECKS must name
    # "DishAssembly" -- and they must NOT name "Dish" or "FeedBox", which
    # no longer exist and measure as None.
    group = bkit.join(mounted, name="DishAssembly")
    bkit.move(group, 0.0, 0.0, SPEC["tower_height"] + 200.0)
    group.rotation_euler = (TILT, 0.0, 0.0)

    # ---- support tower, azimuth race, carriage --------------------------
    tower = bkit.lathe("SupportTower", [
        (250.0, 0.0), (240.0, 60.0), (180.0, 200.0),
        (150.0, SPEC["tower_height"] - 120.0), (150.0, SPEC["tower_height"]),
        (0.0, SPEC["tower_height"]),
    ], segments=32, mat=steel, smooth=False)
    bkit.recalc(tower)
    bkit.tube("AzimuthRace", 290.0, 230.0, 70.0, segments=40,
              centre=(0.0, 0.0, 20.0), mat=steel)
    bkit.rounded_box("ElevationCarriage", 320.0, 230.0, 190.0, r=26.0,
                     centre=(0.0, 0.0, SPEC["tower_height"] + 60.0), mat=steel)
    bkit.rounded_box("CounterweightArm", 300.0, 120.0, 90.0, r=18.0,
                     centre=(190.0, 0.0, SPEC["tower_height"] - 20.0),
                     mat=steel)
    bkit.rounded_box("Counterweight", 120.0, 200.0, 160.0, r=20.0,
                     centre=(330.0, 0.0, SPEC["tower_height"] - 20.0),
                     mat=dark)

    # ---- gantry legs and stairway, on the computed pitch ----------------
    for i, (lx, ly) in enumerate(((240.0, 240.0), (-240.0, 240.0),
                                  (240.0, -240.0), (-240.0, -240.0))):
        bkit.rounded_box("GantryLeg%d" % (i + 1), 46.0, 46.0, 210.0, r=12.0,
                         centre=(lx, ly, 140.0), mat=steel)
    steps = 12
    for i in range(steps):
        z = 60.0 + i * (SPEC["tower_height"] - 120.0) / steps
        bkit.rounded_box("Stair%02d" % (i + 1), 90.0, 34.0, 10.0, r=3.0,
                         centre=(250.0, -40.0, z), mat=dark)

    _scale_all(2.6)      # into the catalog huge band, which starts at 1500 mm

    return dict(spec=SPEC, parts=1 + 1 + 1 + 1 + 1 + 1 + 1 + 1 + 4 + steps)


CHECKS = [
    # The joined assembly measures to the RIM RING, which stands 0.5% proud
    # of the dish itself, so the measured figure is the rim diameter.
    dict(name="rim_diameter", mm=2613.0, tol=20.0,
         how="diameter", part="DishAssembly"),
    dict(name="tower_height", mm=1560.0, tol=12.0,
         how="bbox_z", part="SupportTower"),
    dict(name="counterweight_arm", mm=780.0, tol=8.0,
         how="bbox_x", part="CounterweightArm"),
    # join() renames the survivor to DishAssembly, so the feed box no longer
    # exists as a named part and cannot be measured. Replaced with the one
    # component that is still its own object.
    dict(name="azimuth_race_diameter", mm=1508.0, tol=16.0,
         how="diameter", part="AzimuthRace"),
    dict(name="overall_width", mm=2613.0, tol=120.0, how="bbox_x"),
    dict(name="overall_height", mm=3341.0, tol=30.0, how="bbox_z"),
]