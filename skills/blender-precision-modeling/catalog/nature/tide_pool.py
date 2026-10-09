"""
tide_pool -- a 520 mm rock pool at low tide: a dished rock shelf, a raised rim of
18 boulders on a computed ring, and 3 mm of water inside.

The rim is the model. A tide pool is a bowl whose wall is made of discrete
boulders, so the wall is a radial array of 18 rocks about the pool centre at
(0, 0, 26) -- the water's surface height, NOT the world origin, because the
rocks stand in the water and the array has to orbit the pool, not the world.
Sweep about (0, 0, 0) and half the rocks land outside the shelf.

The water is a shallow closed solid of revolution sitting in the dish, not a
flat disc: a zero-thickness plane disappears edge-on in the side view and has
no volume for the transmissive material to shade.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    pool_diameter  = 520.0,
    water_depth    = 3.0,
    rim_rocks      = 18,
    shelf_diameter = 740.0,
)

R_POOL = SPEC["pool_diameter"] / 2.0
WATER_Z = 26.0


def build():
    rock = bkit.pbr("PoolRock", base=(0.400, 0.380, 0.350), rough=0.86)
    rock_l = bkit.pbr("PoolRockLight", base=(0.540, 0.515, 0.470), rough=0.88)
    rock_w = bkit.pbr("PoolRockWet", base=(0.230, 0.230, 0.215), rough=0.48)
    sand = bkit.pbr("PoolSand", base=(0.700, 0.630, 0.480), rough=0.92)
    water = bkit.pbr("PoolWater", base=(0.140, 0.360, 0.380), rough=0.06,
                     transmission=0.72, ior=1.333)
    weed = bkit.pbr("PoolWeed", base=(0.110, 0.260, 0.120), rough=0.70)
    anemone = bkit.pbr("Anemone", base=(0.700, 0.330, 0.380), rough=0.44,
                       coat=0.25)

    # ---- the rock shelf: a dished solid with a raised lip, one lathe
    bkit.lathe("Shelf", [(0.0, 0.0), (300.0, 0.0), (330.0, 10.0), (300.0, 20.0),
                         (250.0, 22.0), (120.0, 20.0), (0.0, 19.0)],
               segments=56, mat=rock)
    bkit.lathe("ShelfLip", [(230.0, 18.0), (330.0, 14.0), (370.0, 40.0),
                            (330.0, 52.0), (250.0, 30.0)],
               segments=56, mat=rock_l)

    # ---- the sand floor of the pool
    bkit.lathe("Sand", [(0.0, 20.0), (110.0, 20.5), (200.0, 22.0),
                        (250.0, 24.0)],
               segments=48, mat=sand)

    # ---- the water: a shallow closed solid, so it has real volume to shade
    bkit.lathe("Water", [(0.0, 21.0), (150.0, 21.5), (250.0, 24.0),
                         (252.0, WATER_Z), (0.0, WATER_Z)],
               segments=56, mat=water)

    # ---- the rim of 18 boulders, swept about the POOL centre at the water
    # surface height. This is the one `centre` in the file that is not the
    # origin, and it is the difference between a tide pool and some rocks.
    b0 = bkit.uv_sphere("RimRock", 1.0, segments=20, rings=10,
                        centre=(R_POOL + 16.0, 0.0, 40.0), mat=rock)
    b0.scale = (72.0, 62.0, 56.0)
    b0.name = "RimRock"
    # array_radial() reads obj.matrix_world to place its pivot, and the
    # depsgraph is lazy: without this flush the pivot comes from the pre-scale
    # matrix and the 18 boulders bunch into a single ring at half the radius.
    bpy.context.view_layer.update()
    bkit.array_radial(b0, SPEC["rim_rocks"], centre=(0.0, 0.0, 40.0))

    # ---- three smaller rocks inside the rim, on a station grid
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=300.0,
                                                   pitch_y=280.0)):
        ob = bkit.uv_sphere("InnerRock%d" % i, 1.0, segments=16, rings=8,
                            centre=(x, y, 30.0), mat=rock_w)
        ob.scale = (64.0, 56.0, 34.0)
        ob.name = "InnerRock%d" % i

    # ---- the life: weed patches and three anemones, all on the pool floor
    for i, (x, y) in enumerate(bkit.grid_positions(cols=3, rows=2,
                                                   pitch_x=140.0,
                                                   pitch_y=130.0)):
        ob = bkit.uv_sphere("Weed%d" % i, 1.0, segments=12, rings=6,
                            centre=(x, y, 24.0), mat=weed)
        ob.scale = (34.0, 30.0, 9.0)
        ob.name = "Weed%d" % i
    for i in range(3):
        a = math.radians(120.0 * i + 40.0)
        ob = bkit.uv_sphere("Anemone%d" % i, 1.0, segments=16, rings=8,
                            centre=(150.0 * math.cos(a), 150.0 * math.sin(a),
                                    28.0), mat=anemone)
        ob.scale = (22.0, 22.0, 16.0)
        ob.name = "Anemone%d" % i

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=4 + 1 + 4 + 6 + 3)


CHECKS = [
    dict(name="pool_diameter", mm=504.0, tol=2.52, how="diameter", part="Water"),
    dict(name="water_depth", mm=5.0, tol=0.6, how="bbox_z", part="Water"),
    dict(name="shelf_diameter", mm=740.0, tol=10.0, how="diameter", part="ShelfLip"),
    dict(name="rim_span", mm=150.2, tol=0.75, how="bbox_x", part="RimRock"),
]
