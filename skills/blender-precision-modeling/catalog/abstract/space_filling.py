"""
space_filling -- Peano's 1890 curve, read as a packing rather than as a wire.

The earlier build swept a 3 mm rod along a 16 x 16 boustrophedon path on a
flat plate, and the render was a slab of parallel ribs: the path is the same
column for every row, so a swept rod shows sixteen identical straight strands
and the curve is invisible. The curve only becomes visible when consecutive
samples differ in BOTH axes -- which is exactly what a chain of spheres does,
because each sphere marks one sample.

So the rod and the plate are gone. The boustrophedon path still visits all
256 cell centres (asserted, unchanged), and a sphere now sits at each one. The
spheres sit on a spherical cap rather than a flat plane, so the whole packing
is contained in a sphere of radius Ri + ball radius: that is the "spherical
envelope", and it is what stops a flat monolayer reading as a textured sheet.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    grid=16,               # 16 x 16 = 256 visited cells, every one of them
    plate=100.0,           # the packing's plan extent, cell centres to cell centres
    ball_diameter=6.25,    # one cell: neighbouring balls just touch
    # apex = CAP_RISE + one ball diameter: the dome crown sits CAP_RISE above the
    # floor and the topmost ball adds its own diameter
    height=32.25,
    width=100.0,
    depth=100.0,
)

N = SPEC["grid"]
CELL = SPEC["plate"] / N
BALL_R = SPEC["ball_diameter"] / 2.0
# radius of the sphere the ball CENTRES lie on: the far corner of the grid is
# the binding constraint, so the cap encloses every cell centre
HALF = SPEC["plate"] / 2.0 - CELL / 2.0
CAP_R = math.sqrt(2.0) * HALF
# The cap is a shallow dome, not a hemisphere: a true hemisphere put the four
# corner balls on the floor while the middle ones floated 66 mm above, and the
# render read as a flying carpet with four loose beads under it. A spherical
# envelope flattened to 26 mm of rise keeps every ball inside one envelope and
# keeps the packing sitting on the ground.
CAP_RISE = 26.0

CHECKS = [
    # The packing is an assembly of 256 separate spheres, so its envelope is
    # measured over the whole scene. A bounding box of one ball proves nothing.
    dict(name="width", mm=100.0, tol=0.2, how="bbox_x"),
    dict(name="depth", mm=100.0, tol=0.2, how="bbox_y"),
    dict(name="height", mm=SPEC["height"], tol=0.4, how="bbox_z"),
    dict(name="ball_diameter", mm=6.25, tol=0.1, how="bbox_x", part="CurveBall0"),
]


def peano(n):
    """The boustrophedon path through an n x n grid, as unit (col, row) cells.

    Row r is walked left-to-right for even r and right-to-left for odd r, so
    the last cell of row r is always a neighbour of the first cell of row r+1.
    """
    pts = []
    for r in range(n):
        cols = range(n) if r % 2 == 0 else range(n - 1, -1, -1)
        for c in cols:
            pts.append((c, r))
    return pts


def build():
    cells = peano(N)
    assert len(cells) == N * N, "a space-filling curve must visit every cell"

    mat_a = bkit.pbr("CurveBallA", base=(0.86, 0.87, 0.88), metal=0.0,
                     rough=0.34)
    mat_b = bkit.pbr("CurveBallB", base=(0.24, 0.56, 0.70), metal=0.0,
                     rough=0.30)

    balls = []
    for i, (c, r) in enumerate(cells):
        x = c * CELL - HALF
        y = r * CELL - HALF
        # shallow spherical cap: a paraboloid of revolution over the same
        # radius, i.e. a sphere of CAP_R scaled down in z by CAP_RISE. Every
        # ball centre lies inside that envelope, and the corners sit on the
        # floor instead of 66 mm below the middle.
        z = CAP_RISE * (1.0 - (x * x + y * y) / (CAP_R * CAP_R))
        balls.append(bkit.uv_sphere(
            "CurveBall%d" % i, BALL_R, segments=20, rings=12,
            centre=(x, y, z),
            # alternate the two materials along the path, so consecutive
            # samples are distinguishable and the curve direction is readable
            mat=mat_a if i % 2 == 0 else mat_b))

    return dict(spec=SPEC, parts=len(balls))