"""
crystal_cluster -- a druse of quartz points grown on a matrix plate.

Real object: a 96 mm cluster -- a flat grey-green schist plate with a dozen
terminated hexagonal prisms standing on it, splayed outward by growth
competition and longest in the middle. The splay is the read: a set of
identical vertical prisms reads as a barcode, a set of prisms tilted at
different angles reads as a cluster.

Layout is computed, never hand-placed: a `bkit.grid_positions` cell grid with
an explicit pitch, plus a deterministic per-cell jitter and tilt so no two
crystals are coincident and no two are the same size.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    plate_width=96.0,
    plate_thickness=13.0,
    tallest_crystal=72.0,
    crystal_diameter=13.0,
    crystal_count=12,
)

PITCH = 30.0                 # grid pitch, from the crystal diameter + gap
PLATE = SPEC["plate_width"]
CRYSTALS = SPEC["crystal_count"]


def _crystal(name, r, length, mat):
    """One terminated quartz point as a single watertight solid."""
    tip_frac = 0.30
    prism_h = length * (1.0 - tip_frac)
    hexa = [(r * math.cos(math.radians(60 * i)),
             r * math.sin(math.radians(60 * i))) for i in range(6)]
    prism = bkit.extrude_profile(name + "Prism", hexa, prism_h,
                                 centre=(0.0, 0.0, prism_h / 2.0), mat=mat)
    tip_h = length - prism_h + 1.0
    bkit.boolean(prism, bkit.cylinder(name + "Tip", r + 0.35, tip_h, r2=0.0,
                                      segments=6, centre=(0.0, 0.0,
                                      prism_h - 1.0 + tip_h / 2.0),
                                      smooth=False), "UNION")
    bkit.recalc(prism)
    prism.name = name
    return prism


def build():
    schist = bkit.pbr("ClusterMatrix", base=(0.33, 0.35, 0.32), rough=0.82)
    quartz = bkit.pbr("ClusterQuartz", base=(0.88, 0.90, 0.93), rough=0.07,
                      transmission=0.34, ior=1.55)
    smoky = bkit.pbr("ClusterSmoky", base=(0.52, 0.50, 0.51), rough=0.10,
                     transmission=0.26, ior=1.55)

    # ---- matrix plate ----------------------------------------------------
    plate = bkit.rounded_box("MatrixPlate", PLATE, PLATE * 0.86,
                             SPEC["plate_thickness"], r=2.5,
                             centre=(0.0, 0.0, SPEC["plate_thickness"] / 2.0),
                             mat=schist)

    # ---- crystals on a computed grid -------------------------------------
    # grid_positions gives a centred 4x3 lattice; the fixed-seed Random makes
    # the size/tilt variation reproducible without hard-coding 12 coordinates.
    rnd = random.Random(19)
    # 5x3 at a 30 mm pitch gives 15 cells with a true centre cell at (0, 0).
    # A 4x3 grid has NO centre cell, so the "tallest, middle crystal" lands on
    # a corner and measures 57 mm instead of 72.
    cells = list(bkit.grid_positions(cols=5, rows=3, pitch_x=PITCH, pitch_y=PITCH))
    # Centre cell first: growth competition makes the middle crystal the
    # tallest, and the catalog's tallest-crystal check has to point at it.
    # grid_positions gives row-major order, so cell 5 is the middle of a 4x3.
    cells.sort(key=lambda p: (math.hypot(p[0], p[1]), p[0], p[1]))
    n = 0
    for (x, y) in cells:
        if n >= CRYSTALS:
            break
        t = 1.0 - (math.hypot(x, y) / (PITCH * 1.6))     # biggest in the middle
        length = SPEC["tallest_crystal"] * (0.42 + 0.58 * max(0.15, t))
        dia = SPEC["crystal_diameter"] * (0.60 + 0.40 * t) * rnd.uniform(0.9, 1.1)
        mat = quartz if n % 3 else smoky
        c = _crystal("Crystal%02d" % n, dia / 2.0, length, mat)
        # Splay: lean away from the centre, capped at 22 deg. Growth
        # competition tilts crystals outward but never lays them down --
        # an uncapped atan(radius/height) put several of these on their sides.
        lean = min(22.0, math.degrees(math.atan2(math.hypot(x, y),
                                                 SPEC["plate_thickness"])))
        c.rotation_euler = (math.radians(lean) * (y / (abs(y) or 1.0)),
                            math.radians(-lean) * (x / (abs(x) or 1.0)),
                            math.radians(rnd.uniform(0.0, 60.0)))
        # Foot buried 3 mm into the plate: buried roots, never tangent bases.
        bkit.move(c, x + rnd.uniform(-2.5, 2.5), y + rnd.uniform(-2.5, 2.5),
                  SPEC["plate_thickness"] - 3.0)
        n += 1

    return dict(spec=SPEC, parts=1 + n)


CHECKS = [
    dict(name="plate_width", mm=96.0, tol=0.6, how="bbox_x", part="MatrixPlate"),
    dict(name="plate_thickness", mm=13.0, tol=0.6, how="bbox_z", part="MatrixPlate"),
    dict(name="tallest_crystal", mm=72.0, tol=4.0, how="bbox_z", part="Crystal00"),
    # Splayed crystals overhang the plate on both sides.
    dict(name="overall_width", mm=136.0, tol=3.0, how="bbox_x"),
    dict(name="overall_height", mm=82.0, tol=3.0, how="bbox_z"),
]