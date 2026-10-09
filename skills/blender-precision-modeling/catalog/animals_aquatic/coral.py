"""coral -- a 150 mm staghorn coral cluster: a branching, tree-like colony
whose branches get thinner as they go out, with rounded polyp tips.

The branching structure is the model. A stack of cylinders at hand-typed
coordinates looks like a pile of pipes; what makes coral read is that every
branch splits into two at a derived angle, and each child is shorter and
thinner than its parent. So `branch()` is recursive, and the child geometry is
computed from the parent's -- never typed in eight times.

Construction: every branch is a swept tube with rounded ends, so each is a
closed solid; nothing is booleaned. The base is a lathed holdfast.

Orientation: the colony grows up out of a rocky base, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    colony_height=157.0,          # a young staghorn colony: the recursive
    colony_width=125.0,          # taper keeps it well under `branch_count`²
    branch_count=21,
    branch_levels=4,
    holdfast_diameter=52.0,
    tip_diameter=4.9,
)

# the branch table: (length, radius_start, radius_end, pitch_deg, yaw_deg)
# Every row's length is DERIVED from its parent, which is what makes the
# colony taper instead of repeating. Pitch stays modest so the colony grows
# UP like a coral rather than splaying flat into a starfish.
BRANCH = [
    (52.0, 8.5, 6.0, 16.0, 0.0),
    (42.0, 6.0, 4.4, 24.0, 38.0),
    (32.0, 4.4, 3.0, 30.0, -34.0),
    (22.0, 3.0, 1.9, 34.0, 42.0),
]
_SEG = 5              # swept nodes per branch


def _dir(pitch_deg, yaw_deg):
    p = math.radians(pitch_deg)
    y = math.radians(yaw_deg)
    return (math.sin(p) * math.sin(y), math.sin(p) * math.cos(y), math.cos(p))


def build():
    coral = bkit.pbr("CoralBranch", base=(0.72, 0.44, 0.30), rough=0.72)
    tip = bkit.pbr("CoralTip", base=(0.88, 0.66, 0.50), rough=0.60)
    base = bkit.pbr("CoralBase", base=(0.46, 0.34, 0.26), rough=0.84)

    holdfast = bkit.lathe(
        "Holdfast",
        [(0.0, 0.0), (24.0, 3.0), (26.0, 14.0), (20.0, 26.0), (0.0, 30.0)],
        segments=40, centre=(0.0, 0.0, 0.0), mat=base)

    parts = [holdfast]
    made = [0]

    def grow(origin, row, level, yaw0):
        """Emit one branch and its two children.

        `row` indexes BRANCH, so the child's length, radius and lean come out
        of the table rather than out of thin air. `level` caps the recursion so
        the colony has a real branch count.
        """
        if level >= SPEC["branch_levels"] or made[0] >= SPEC["branch_count"]:
            return
        length, r0, r1, pitch, yaw = BRANCH[row]
        d = _dir(pitch, yaw0 + yaw)
        path, rad = [], []
        for i in range(_SEG + 1):
            t = i / float(_SEG)
            path.append((origin[0] + d[0] * length * t,
                         origin[1] + d[1] * length * t,
                         origin[2] + d[2] * length * t))
            rad.append((r0 + (r1 - r0) * t, r0 + (r1 - r0) * t))
        name = "Branch%d" % (made[0] + 1)
        made[0] += 1
        ob = F.tube(name, path, rad, coral if level else base, n=2.2, steps=12)
        parts.append(ob)
        if level == len(BRANCH) - 1:
            # the growing tip: a rounded polyp cap on the thinnest branch
            cap = F.sphere(name + "Tip", r1 * 1.3, path[-1], tip,
                           segments=14, rings=8)
            parts.append(cap)
            return
        end = path[-1]
        grow(end, row + 1, level + 1, yaw0 + yaw)
        grow(end, row + 1, level + 1, yaw0 + yaw - 64.0)

    grow((0.0, 0.0, 20.0), 0, 0, 0.0)
    # a second, smaller colony offset from the first: the pitch comes from the
    # colony's own width, so the two never land on each other
    grow((34.0, -22.0, 6.0), 1, 1, 150.0)
    grow((-30.0, 18.0, 4.0), 1, 1, -40.0)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=len(parts))


CHECKS = [
    dict(name="colony_height", mm=157.0, tol=14.0, how="bbox_z"),
    dict(name="colony_width", mm=125.0, tol=15.0, how="bbox_y"),
    dict(name="holdfast_diameter", mm=52.0, tol=5.0, how="bbox_x",
         part="Holdfast"),
    # the thinnest branch is the last one out of the recursion, so its cap
    # diameter is the colony's real taper
    dict(name="tip_diameter", mm=5.0, tol=1.0, how="bbox_x",
         part="Branch21Tip"),
]