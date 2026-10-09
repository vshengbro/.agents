"""
t_shirt -- a size M short-sleeve cotton jersey tee, 700 mm hem-to-shoulder.

Clothing is the thin-shell case: a garment is a surface, not a volume, so a
solid loft would read as a mannequin torso. Every panel here is therefore built
as `outer loft - inner cavity loft`, which is a real wall thickness AND, because
the cavity is deliberately run out through an opening, gives that opening a real
visible edge thickness instead of a paper cut.

The cavity is the trick that carries the whole model:
  * torso cavity  exits through the top  -> the crew neckline
  * sleeve cavity exits through the cuff -> an open cuff with a wall you can see
and the hem gets a rib band instead of a hole, because a t-shirt hem is closed.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres (size M tee, laid flat) -------------------
SPEC = dict(
    body_length=700.0,        # hem to shoulder, flat-lay length
    chest_width=516.0,        # flat width across the chest
    body_depth=262.0,         # front to back through the chest
    shoulder_drop=45.0,       # neck height down to the shoulder seam
    sleeve_length=220.0,      # shoulder seam to cuff
    sleeve_span=968.0,        # cuff tip to cuff tip
    neck_opening=188.0,       # inside width of the crew neck
    rib_height=16.0,          # hem rib band height
    fabric_thickness=3.0,     # modelled wall; jersey is thinner but 3 keeps
    #                            booleans honest at this scale
)

N = 3.2                      # torso section exponent: squarish, not a tube
SN = 2.4                     # sleeve exponent: rounder, an arm is a limb
STEPS = 56
INNER_STEPS = 37             # deliberately != STEPS so cavity facets never
#                             land on the outer facets (coincident-facet trap)


# ---------------------------------------------------------------------------
# geometry helpers, local to this file so no shared module is touched
# ---------------------------------------------------------------------------

def ring(z, a, b, n=N, steps=STEPS):
    """A closed superellipse ring of half-extents (a, b) lifted to height z."""
    return [(x, y, z) for (x, y) in
            bkit.superellipse_section(2 * a, 2 * b, n=n, steps=steps)]


def axis_frame(d):
    """An orthonormal (u, v) pair spanning the plane perpendicular to d.

    A vertical run takes u = +X directly; `d x (0,0,1)` is degenerate there and
    the naive cross product silently swaps the two half-extents, which turns a
    trouser leg 300 mm wide instead of 300 mm deep.
    """
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


def limb(name, path, half, n=SN, steps=STEPS, mat=None):
    """Loft a tapered tube down an arbitrary 3D polyline.

    `path` is a list of centre points, `half` a list of (a, b) half-extents, one
    per centre. A sleeve, a trouser leg and a drawstring are all this function
    at different lengths and tapers, which is why it takes the direction from
    the path rather than assuming +Z.
    """
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
    """A real-walled panel: closed outer solid minus a strictly-inside cavity.

    `cavity` may run past the end of `outer` on purpose -- that is what turns the
    cavity into an opening with a visible wall thickness rather than a void.
    Both arguments are finished objects, so the torso passes a plain loft and a
    sleeve passes the `limb()` sweep without duplicating this logic.
    """
    bkit.boolean(outer, cavity, "DIFFERENCE")
    bkit.recalc(outer)
    return outer


# --- panel definitions ------------------------------------------------------
# (z, half_x, half_y) from hem to shoulder. The waist really is narrower than
# both the hem and the chest, and the shoulder line is narrower than both -- that
# pair of ratios is what stops the tee reading as a straight barrel.
TORSO = [
    (0.0, 252.0, 122.0),      # hem
    (100.0, 254.0, 128.0),
    (220.0, 238.0, 116.0),    # waist
    (360.0, 248.0, 126.0),
    (480.0, 258.0, 131.0),    # chest
    (570.0, 250.0, 124.0),
    (625.0, 236.0, 112.0),    # armpit line, where the sleeve leaves the body
    (655.0, 222.0, 96.0),     # shoulder seam, 45 mm below the neck
    (680.0, 168.0, 78.0),     # shoulder slope
    (694.0, 128.0, 66.0),     # neck rib anchor
    (700.0, 104.0, 58.0),     # neck lip: this cap is what the cavity opens
]
# The cavity is the torso inset by the wall thickness, and its last two sections
# climb ABOVE the neck lip, so the difference punches a real crew neckline out of
# the shoulder rather than leaving a sealed pot.
TORSO_CAV = [
    (3.0, 249.0, 119.0),
    (100.0, 251.0, 125.0),
    (220.0, 235.0, 113.0),
    (360.0, 245.0, 123.0),
    (480.0, 255.0, 128.0),
    (570.0, 247.0, 121.0),
    (625.0, 233.0, 109.0),
    (650.0, 218.0, 93.0),
    (668.0, 160.0, 74.0),
    (686.0, 100.0, 50.0),
    (750.0, 94.0, 44.0),      # above the neck lip -> opens the neckline
]

# Sleeve: root buried deep inside the torso, cuff 220 mm out along a path that
# drops ~17 degrees, which is the dropped shoulder of a modern tee.
SLEEVE_PATH = [(60.0, 0.0, 580.0), (236.0, 0.0, 555.0), (330.0, 0.0, 520.0),
               (410.0, 0.0, 483.0), (455.0, 0.0, 459.0)]
SLEEVE_HALF = [(95.0, 106.0), (94.0, 100.0), (88.0, 84.0), (79.0, 68.0),
               (75.0, 62.0)]
# Overshot by 28 mm so the cuff is open, and inset by more than the 1 mm
# tangency margin everywhere it is still inside the sleeve.
SLEEVE_CAV_PATH = [(100.0, 0.0, 576.0), (238.0, 0.0, 553.0), (332.0, 0.0, 518.0),
                   (412.0, 0.0, 481.0), (483.0, 0.0, 453.0)]
SLEEVE_CAV_HALF = [(88.0, 98.0), (87.0, 93.0), (81.0, 77.0), (72.0, 61.0),
                   (69.0, 55.0)]


def _mm(vec):
    """A face centre or normal from assign_faces_by, in millimetres."""
    return vec / bkit.MM


def build():
    jersey = bkit.pbr("JerseyCotton", base=(0.855, 0.845, 0.815), rough=0.95)
    jersey_in = bkit.pbr("JerseyLining", base=(0.735, 0.725, 0.700), rough=0.96)
    rib = bkit.pbr("CottonRib", base=(0.775, 0.768, 0.745), rough=0.93)
    print_ink = bkit.pbr("PrintInk", base=(0.155, 0.235, 0.360), rough=0.72)

    # ---- torso: closed outer minus cavity -> a walled garment with a neckline
    torso = shell(
        bkit.loft("TeeBody", [ring(z, a, b) for (z, a, b) in TORSO],
                  smooth=True, mat=jersey),
        bkit.loft("TeeBody_cavity",
                  [ring(z, a, b, steps=INNER_STEPS)
                   for (z, a, b) in TORSO_CAV]),
    )

    # A chest graphic as a second material on the real solid: a separate
    # decal-shaped object would z-fight the shell and double the bad-edge count.
    bkit.assign_faces_by(
        torso, print_ink,
        lambda c, n: _mm(c.y) < -95.0 and abs(_mm(c.x)) < 150.0
        and 300.0 < _mm(c.z) < 520.0 and _mm(n.y) < -0.5,
    )
    # The inside of the garment is the set of faces whose normal points back
    # toward the axis -- the difference keeps the cavity's own outward normal.
    # That is what gives the neckline and the cuffs depth instead of a flat cut.
    bkit.assign_faces_by(
        torso, jersey_in,
        lambda c, n: (_mm(c.x) * _mm(n.x) + _mm(c.y) * _mm(n.y)) < -0.3,
    )

    # ---- two sleeves, same recipe mirrored about X -------------------------
    for i, sx in enumerate((1.0, -1.0)):
        path = [(sx * x, y, z) for (x, y, z) in SLEEVE_PATH]
        cav = [(sx * x, y, z) for (x, y, z) in SLEEVE_CAV_PATH]
        shell(limb("TeeSleeve%d" % (i + 1), path, SLEEVE_HALF, mat=jersey),
              limb("_TeeSleeve%d_cavity" % (i + 1), cav, SLEEVE_CAV_HALF))

    # ---- neckline rib, riding on the shoulder slope just outside the shell --
    # Hollowed like every other panel: a capped band here would drop a lid
    # straight over the neckline the torso cavity just opened.
    shell(bkit.loft("TeeCollarRib", [
        ring(672.0, 176.0, 86.0),
        ring(688.0, 136.0, 74.0),
        ring(700.0, 110.0, 64.0),
        ring(708.0, 96.0, 52.0),
    ], smooth=True, mat=rib),
        bkit.loft("_TeeCollarRib_cavity", [
            ring(660.0, 168.0, 78.0, steps=INNER_STEPS),
            ring(688.0, 128.0, 66.0, steps=INNER_STEPS),
            ring(700.0, 100.0, 54.0, steps=INNER_STEPS),
            ring(760.0, 88.0, 44.0, steps=INNER_STEPS),  # out the top -> open
        ]))

    # ---- hem rib: closed band, because a tee hem is sewn shut ---------------
    bkit.recalc(bkit.loft("TeeHemRib", [
        ring(0.0, 258.0, 128.0),
        ring(8.0, 260.0, 131.0),
        ring(16.0, 259.0, 132.0),
    ], smooth=True, mat=rib))

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="body_length", mm=700.0, tol=1.0, how="bbox_z", part="TeeBody"),
    dict(name="chest_width", mm=516.0, tol=1.5, how="bbox_x", part="TeeBody"),
    dict(name="body_depth", mm=262.0, tol=1.5, how="bbox_y", part="TeeBody"),
    dict(name="sleeve_span", mm=968.0, tol=2.0, how="bbox_x"),
    dict(name="rib_height", mm=16.0, tol=1.0, how="bbox_z", part="TeeHemRib"),
    dict(name="collar_rib_height", mm=36.0, tol=1.0, how="bbox_z",
         part="TeeCollarRib"),
]