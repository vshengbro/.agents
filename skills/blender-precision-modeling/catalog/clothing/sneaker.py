"""
sneaker -- a size 10 running shoe, 305 mm long, 118 mm to the collar.

A sneaker is three stacked parts and the silhouette only works if all three are
present: a full-length sole with a real toe spring, a midsole, and an upper that
is a separate hollowed shell over the foot. The tongue and the laces are what
stop the upper reading as a sock.

The lace rows and the eyelet pairs come from grid_positions(), so eight eyelets
sit on a real pitch instead of eight hand-typed coordinates.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=305.0,             # heel to toe
    width=105.0,              # widest across the ball of the foot
    collar_height=118.0,
    outsole_thickness=30.0,    # 18 mm at the midfoot; the toe spring lifts the tip
    midsole_thickness=26.0,
    toe_spring=22.0,          # how far the toe lifts off the ground
    lace_rows=4,
    eyelets=8,
    eyelet_pitch=26.0,
)

N = 3.0
STEPS = 48
INNER = 31


def ring(z, a, b, n=N, steps=STEPS, cx=0.0, cy=0.0):
    return [(x + cx, y + cy, z) for (x, y) in
            bkit.superellipse_section(2 * a, 2 * b, n=n, steps=steps)]


def axis_frame(d):
    ln = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 1.0
    d = (d[0] / ln, d[1] / ln, d[2] / ln)
    if abs(d[2]) > 0.9:
        u = (1.0, 0.0, 0.0)
    else:
        u = (d[1] * 1.0 - d[2] * 0.0, d[2] * 0.0 - d[0] * 1.0,
             d[0] * 0.0 - d[1] * 0.0)
        ln = math.sqrt(u[0] ** 2 + u[1] ** 2 + u[2] ** 2) or 1.0
        u = (u[0] / ln, u[1] / ln, u[2] / ln)
    v = (d[1] * u[2] - d[2] * u[1],
         d[2] * u[0] - d[0] * u[2],
         d[0] * u[1] - d[1] * u[0])
    return u, v


def sweep(name, path, half, steps=STEPS, n=2.6, mat=None):
    secs = []
    for i, c in enumerate(path):
        if i == 0:
            d = (path[1][0] - c[0], path[1][1] - c[1], path[1][2] - c[2])
        elif i == len(path) - 1:
            d = (c[0] - path[i - 1][0], c[1] - path[i - 1][1],
                 c[2] - path[i - 1][2])
        else:
            d = (path[i + 1][0] - path[i - 1][0],
                 path[i + 1][1] - path[i - 1][1],
                 path[i + 1][2] - path[i - 1][2])
        u, v = axis_frame(d)
        a, b = half[i]
        secs.append([(c[0] + u[0] * px + v[0] * py,
                      c[1] + u[1] * px + v[1] * py,
                      c[2] + u[2] * px + v[2] * py)
                     for (px, py) in
                     bkit.superellipse_section(2 * a, 2 * b, n=n, steps=steps)])
    ob = bkit.loft(name, secs, smooth=True, mat=mat)
    bkit.recalc(ob)
    return ob


def shell(outer, cavity):
    bkit.boolean(outer, cavity, "DIFFERENCE")
    bkit.recalc(outer)
    return outer


# The shoe is built along +X, toe at +x. Sections are (x, half_y, z_bottom,
# z_top) so the sole lifts at the toe while the upper stays a foot-shaped tube.
def sole_ring(x, a, z0, z1, steps=STEPS, n=N):
    """A vertical slab section: flat bottom at z0, top at z1, half-width a."""
    pts = []
    n_pts = steps
    for i in range(n_pts):
        t = 2.0 * math.pi * i / n_pts
        ct, st = math.cos(t), math.sin(t)
        # superellipse mapped into (y, z) then squashed into the slab
        y = math.copysign(abs(ct) ** (2.0 / n), ct) * a
        zm = (z0 + z1) / 2.0
        zh = (z1 - z0) / 2.0
        z = zm + math.copysign(abs(st) ** (2.0 / n), st) * zh
        pts.append((x, y, z))
    return pts


def build_sections(profile, steps=STEPS):
    return [sole_ring(*p, steps=steps) for p in profile]


# x, half-width, bottom z, top z. The toe (x = +150) is lifted 22 mm: a sole
# that meets the floor dead flat is the single clearest "this is a brick" tell.
OUTSOLE = [
    (-150.0, 34.0, 6.0, 18.0),     # heel
    (-110.0, 40.0, 2.0, 18.0),
    (-40.0, 46.0, 0.0, 18.0),
    (40.0, 50.0, 0.0, 18.0),
    (100.0, 48.0, 0.0, 18.0),
    (140.0, 40.0, 4.0, 18.0),
    (155.0, 24.0, 22.0, 30.0),     # toe spring, lifting clear of the floor
]
MIDSOLE = [
    (-152.0, 36.0, 18.0, 40.0),
    (-112.0, 43.0, 18.0, 44.0),
    (-40.0, 49.0, 18.0, 46.0),
    (40.0, 53.0, 18.0, 46.0),
    (102.0, 51.0, 18.0, 42.0),
    (144.0, 42.0, 20.0, 38.0),
    (158.0, 26.0, 30.0, 40.0),
]

# Upper: a foot-shaped tube from heel to toe, hollowed with a cavity that runs
# out of the collar so the shoe has a real opening you can see into.
UPPER_PATH = [
    (-138.0, 0.0, 74.0),
    (-110.0, 0.0, 82.0),
    (-60.0, 0.0, 86.0),
    (0.0, 0.0, 84.0),
    (60.0, 0.0, 78.0),
    (110.0, 0.0, 68.0),
    (145.0, 0.0, 56.0),
]
UPPER_HALF = [(38.0, 34.0), (42.0, 36.0), (44.0, 34.0), (46.0, 31.0),
              (44.0, 27.0), (38.0, 22.0), (26.0, 15.0)]
UPPER_CAV_PATH = [
    (-138.0, 0.0, 70.0),
    (-110.0, 0.0, 76.0),
    (-60.0, 0.0, 78.0),
    (0.0, 0.0, 76.0),
    (60.0, 0.0, 70.0),
    (110.0, 0.0, 60.0),
    (152.0, 0.0, 46.0),
]
UPPER_CAV_HALF = [(34.0, 30.0), (38.0, 32.0), (40.0, 30.0), (42.0, 27.0),
                  (40.0, 23.0), (34.0, 18.0), (21.0, 10.0)]


def _mm(v):
    return v / bkit.MM


def build():
    rubber = bkit.pbr("SneakerRubber", base=(0.845, 0.840, 0.815), rough=0.72)
    foam = bkit.pbr("SneakerFoam", base=(0.905, 0.895, 0.860), rough=0.80)
    mesh = bkit.pbr("SneakerMesh", base=(0.290, 0.320, 0.360), rough=0.90)
    suede = bkit.pbr("SneakerSuede", base=(0.700, 0.680, 0.640), rough=0.95)
    lace = bkit.pbr("SneakerLace", base=(0.930, 0.925, 0.900), rough=0.88)
    metal = bkit.preset("brushed_metal")

    outsole = bkit.loft("SneakerOutsole", build_sections(OUTSOLE, STEPS),
                        smooth=True, mat=rubber)
    bkit.recalc(outsole)
    midsole = bkit.loft("SneakerMidsole", build_sections(MIDSOLE, STEPS),
                        smooth=True, mat=foam)
    bkit.recalc(midsole)

    upper = shell(sweep("SneakerUpper", UPPER_PATH, UPPER_HALF, mat=mesh),
                  sweep("_SneakerUpper_cavity", UPPER_CAV_PATH,
                        UPPER_CAV_HALF, INNER))
    bkit.assign_faces_by(
        upper, suede,
        lambda c, n: _mm(c.x) < -95.0,       # suede heel counter
    )

    # ---- collar and tongue ------------------------------------------------
    shell(sweep("SneakerCollar", [
        (-134.0, 0.0, 96.0), (-100.0, 0.0, 104.0), (-60.0, 0.0, 102.0),
    ], [(41.0, 36.0), (45.0, 38.0), (45.0, 36.0)], mat=suede),
        sweep("_SneakerCollar_cavity", [
            (-134.0, 0.0, 88.0), (-100.0, 0.0, 96.0), (-55.0, 0.0, 94.0),
        ], [(36.0, 31.0), (40.0, 33.0), (40.0, 31.0)], INNER))

    # ---- tongue: a flat padded flap rising out of the throat --------------
    bkit.rounded_box("SneakerTongue", 92.0, 58.0, 16.0, r=6.0, segments=3,
                     centre=(-12.0, 0.0, 108.0), mat=mesh)

    # ---- eyelets and laces on a stated pitch, via grid_positions() --------
    pitch = SPEC["eyelet_pitch"]
    for i, (x, y) in enumerate(
            bkit.grid_positions(cols=SPEC["lace_rows"], rows=2,
                                pitch_x=pitch, pitch_y=34.0)):
        bkit.tube("SneakerEyelet%d" % (i + 1), 6.0, 3.0, 5.0, segments=18,
                  centre=(x, y, 108.0), axis="Z", mat=metal)
    # laces: one cross-over per gap between rows, plus the toe bar
    for i, (x, _y) in enumerate(
            bkit.grid_positions(cols=SPEC["lace_rows"], rows=1,
                                pitch_x=pitch, pitch_y=0.0)):
        for j, sy in enumerate((1.0, -1.0)):
            bkit.cylinder("SneakerLace%d%d" % (i + 1, j + 1), 2.6, 40.0,
                          segments=10, centre=(x, sy * 17.0, 110.0),
                          axis="Y", mat=lace)

    return dict(spec=SPEC, parts=20)


CHECKS = [
    dict(name="length", mm=310.0, tol=3.0, how="bbox_x"),
    dict(name="outsole_thickness", mm=30.0, tol=2.0, how="bbox_z",
         part="SneakerOutsole"),
    dict(name="width", mm=106.0, tol=2.0, how="bbox_y", part="SneakerMidsole"),
    dict(name="collar_height", mm=73.0, tol=2.0, how="bbox_z",
         part="SneakerCollar"),
    dict(name="tongue_length", mm=92.0, tol=1.0, how="bbox_x",
         part="SneakerTongue"),
]