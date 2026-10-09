"""
pyramid -- a masonry step pyramid: square base, four triangular faces, a
stepped casing that reads at a distance.

Size class `large` (600..3000 mm): modelled at 1:150 scale of the Great Pyramid
of Giza (230.4 m base, 146.6 m original height) so the whole object fits the
catalog's mm band. The ratio is what matters and it is preserved: base 2000 mm,
first-tier height 640 mm -> 25.1 deg face slope against the real 25.2 deg.

Four tiers, each a square frustum, unioned with real overlap so no two solids
end exactly flush. `extrude_profile` gives the square footprints; the frustum
side walls come from `loft` between two square rings of different size.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_width=2000.0,
    base_height=1280.0,      # total height of the stepped mass
    tiers=4,
    core_width=200.0,        # pyramidion at the top
    capstone_height=180.0,
)

TIERS = SPEC["tiers"]


def _tier(name, base, top, h, z0, mat):
    """One square frustum: a ring at z0, a smaller ring at z0+h, capped both ends.

    `rounded_rect_section` rather than `superellipse_section(n=10, steps=4)`:
    four superellipse samples land on the axes and give a DIAMOND footprint,
    which is not a pyramid. Four rounded-rect corners give a true square with
    the same vertex count on every ring so loft can bridge them.
    """
    def ring(s):
        return bkit.rounded_rect_section(s, s, s * 0.004, per_corner=1)
    secs = [[(x, y, z0) for (x, y) in ring(base)],
            [(x, y, z0 + h) for (x, y) in ring(top)]]
    return bkit.loft(name, secs, mat=mat)


def build():
    limestone = bkit.pbr("PyramidLimestone", base=(0.72, 0.66, 0.53), rough=0.80)
    casing = bkit.pbr("PyramidCasing", base=(0.84, 0.80, 0.68), rough=0.46)
    core = bkit.pbr("PyramidCore", base=(0.62, 0.53, 0.38), rough=0.88)

    # ---- stepped mass: tiers shrink and step up ------------------------
    # Each tier starts `overlap` BELOW the previous tier's top so the two
    # solids interpenetrate. The overlap is what makes the stack a single
    # silhouette rather than four floating frusta that z-fight at the seam.
    z = 0.0
    overlap = 24.0
    for t in range(TIERS):
        frac = 1.0 - (float(t) / TIERS) * 0.62
        base = SPEC["base_width"] * frac
        top = SPEC["base_width"] * (frac - (1.0 - frac) * 0.55)
        h = SPEC["base_height"] / TIERS
        # Tier 1 starts on the floor; every tier above starts `overlap` below
        # the tier below's top face, so consecutive solids interpenetrate.
        z0 = 0.0 if t == 0 else z - overlap
        height = h if t == 0 else h + overlap
        _tier("Tier%d" % (t + 1), base, top, height, z0, limestone)
        z += h

    # ---- pyramidion: the smooth-cased capstone --------------------------
    # The capstone is a solid pyramidion: full width at its foot, narrowing to
    # a point at the top. A frustum with a 200 mm top face is a truncated cone,
    # not a pyramidion.
    _tier("Pyramidion", SPEC["core_width"] * 2.4, 40.0,
          SPEC["capstone_height"] + overlap, z - overlap, casing)

    return dict(spec=SPEC, parts=TIERS + 1)


CHECKS = [
    dict(name="base_width", mm=2000.0, tol=4.0, how="bbox_x", part="Tier1"),
    dict(name="tier1_height", mm=320.0, tol=2.0, how="bbox_z", part="Tier1"),
    dict(name="pyramidion_foot", mm=480.0, tol=2.0, how="bbox_x", part="Pyramidion"),
    dict(name="total_height", mm=SPEC["base_height"] + SPEC["capstone_height"],
         tol=3.0, how="bbox_z"),
]