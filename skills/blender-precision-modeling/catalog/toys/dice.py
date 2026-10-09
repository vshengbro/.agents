"""
dice -- a pair of 16 mm casino dice with correctly arranged pips.

A die is a rounded cube; what makes it a die is the pip layout. Each face gets
the standard arrangement, drilled with one `bore()` per pip, and opposite faces
sum to seven (1-6, 2-5, 3-4) exactly as on a real die. The pips are RECESSED
dimples cut into the body rather than pucks stuck on the surface, because a
raised pip changes the silhouette and reads as a stud, not a pip.

Each cutter is placed so that it starts outside the die and ends 0.9 mm below
the surface: a cutter that stops exactly at the face is tangent, and tangency
is what leaves the EXACT solver a handful of non-manifold edges.

The two dice carry different pip tables, so the pair shows two different
counts from any one camera angle -- a detail that is invisible in a bounding
box and obvious in a render.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    die_edge=16.0,          # standard 16 mm casino / board-game die
    corner_radius=2.2,
    pip_radius=1.15,
    pip_depth=0.9,
    pip_offset=4.4,         # corner pips this far from the face centre
    pips_per_die=21,        # 1+2+3+4+5+6
    dice_in_pair=2,
)

EDGE = SPEC["die_edge"]
HALF = EDGE / 2.0
PR = SPEC["pip_radius"]
PD = SPEC["pip_depth"]
PO = SPEC["pip_offset"]
CUT = 5.0                  # cutter length; only PD of it is inside the die

# (axis, sign, pip count). Opposite faces always sum to seven.
LAYOUT_A = ((0, 1, 4), (0, -1, 3), (1, 1, 2), (1, -1, 5), (2, 1, 1), (2, -1, 6))
LAYOUT_B = ((0, 1, 5), (0, -1, 2), (1, 1, 6), (1, -1, 1), (2, 1, 3), (2, -1, 4))

# (u, v) offsets for 1..6 pips in the face plane, in units of pip_offset.
PIP_GRID = {
    1: [(0, 0)],
    2: [(-1, -1), (1, 1)],
    3: [(-1, -1), (0, 0), (1, 1)],
    4: [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    5: [(-1, -1), (-1, 1), (0, 0), (1, -1), (1, 1)],
    6: [(-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1)],
}


def _pip_centres(origin, layout):
    """World millimetre centre of every pip on one die, with its face axis."""
    out = []
    for (axis, sign, count) in layout:
        inplane = [k for k in (0, 1, 2) if k != axis]
        for (u, v) in PIP_GRID[count]:
            p = list(origin)
            # OFFSET from the die's own centre, not an absolute. Writing
            # p[axis] = HALF * sign puts the +Z pips at the die's mid-plane
            # whenever the die is not centred on z=HALF, so the cutter lands
            # wholly inside the solid and leaves an invisible internal void.
            # The mesh still reports watertight and the render still shows a
            # blank face.
            p[axis] = origin[axis] + HALF * sign
            p[inplane[0]] += u * PO
            p[inplane[1]] += v * PO
            out.append((tuple(p), axis))
    return out


def _pip_material_predicate(pips, origin, reach):
    """True for a face that is a pip wall or a pip floor.

    A pip surface lies INSIDE the die, and "inside" has to be measured from the
    die's own centre -- the die is not at the world origin, so testing
    `abs(p[axis]) < HALF` against world coordinates silently skips every pip on
    a face that points away from the origin. That is how a die ends up with
    6 inked pips on one side and a blank top: the bores are all there, the
    ink is not.
    """
    reach2 = reach * reach
    c0, c1, c2 = origin

    def pred(centre, normal):
        p = (centre.x / bkit.MM, centre.y / bkit.MM, centre.z / bkit.MM)
        d = (p[0] - c0, p[1] - c1, p[2] - c2)
        if max(abs(d[0]), abs(d[1]), abs(d[2])) > HALF - 0.35:
            return False                     # one of the outer flat faces
        for (q, axis) in pips:
            if sum((p[i] - q[i]) ** 2 for i in range(3)) <= reach2:
                return True
        return False
    return pred


def build():
    ivory = bkit.pbr("DiceIvory", base=(0.90, 0.87, 0.79), rough=0.16, coat=0.5)
    ink = bkit.pbr("DicePipInk", base=(0.42, 0.035, 0.030), rough=0.24)

    for idx, (x, y, layout) in enumerate(((-12.0, 0.0, LAYOUT_A),
                                          (12.0, 3.0, LAYOUT_B))):
        origin = (x, y, HALF)
        die = bkit.rounded_box("Die%d" % (idx + 1), EDGE, EDGE, EDGE,
                               r=SPEC["corner_radius"], segments=6,
                               centre=origin, mat=ivory)
        for (axis, sign, count) in layout:
            for (q, _a) in _pip_centres(origin, ((axis, sign, count),)):
                # the cutter crosses the surface: it extends CUT/2 - PD above
                # the face and (CUT/2 + PD) below it.
                c = list(q)
                c[axis] += sign * (CUT / 2.0 - PD)
                bkit.bore(die, PR, CUT, centre=tuple(c),
                          axis="XYZ"[axis], host_segments=32)
        bkit.recalc(die)
        bkit.assign_faces_by(die, ink,
                             _pip_material_predicate(
                                 _pip_centres(origin, layout), origin, PR * 1.9))

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="die_edge", mm=16.0, tol=0.2, how="bbox_x", part="Die1"),
    dict(name="die_height", mm=16.0, tol=0.2, how="bbox_z", part="Die1"),
    dict(name="die_two_edge", mm=16.0, tol=0.2, how="bbox_x", part="Die2"),
    dict(name="pair_width", mm=40.0, tol=0.6, how="bbox_x"),
]
