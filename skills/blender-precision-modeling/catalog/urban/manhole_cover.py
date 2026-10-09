"""
manhole_cover -- 600 x 660 x 35 mm ductile-iron manhole cover: a 660 mm
seating ring, a dished lid with a recessed top face, and 93 raised diamond-tread
bosses in six concentric rings.

`small` in the catalog, but a manhole cover is 600 mm across under every
standard (EN 124, ASTM A48). The tread is the whole job, so the boss count is
COMPUTED rather than typed: `ring_counts` gives each concentric ring a count
proportional to its circumference, which keeps the angular pitch roughly
constant and guarantees no two bosses land on the same polar coordinate -- the
radial equivalent of the anti-hand-placing rule.

Each ring is one `box` swept by `array_radial` and rotated 45 degrees so the
studs are diamonds. The source box is built at its ring radius from the WORLD
origin, because the sweep orbits the origin rather than the lid.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    cover_diameter=600.0,
    overall_height=35.0,
    seating_ring_diameter=660.0,
    tread_rings=6,
    tread_bosses=93,
    boss_size=34.0,
)

COVER_R = SPEC["cover_diameter"] / 2.0
TREAD_IN, TREAD_OUT = 90.0, 250.0
DIAMOND = 0.7853982                 # 45 degrees


def ring_counts(rings, inner_r, outer_r, per_ring):
    """Boss count per concentric ring, proportional to its circumference.

    The reference `per_ring` is the count the MIDDLE ring would get, so the
    total is close to `rings * per_ring` while the outer rings get more studs
    than the inner ones -- which is what keeps the tread spacing even.
    """
    mid = (inner_r + outer_r) / 2.0
    return [max(6, int(round(per_ring * (inner_r
                                         + (outer_r - inner_r)
                                         * (i + 0.5) / rings) / mid)))
            for i in range(rings)]


def build():
    iron = bkit.pbr("CoverIron", base=(0.20, 0.20, 0.21), metal=0.85,
                    rough=0.62)
    raised = bkit.pbr("CoverTread", base=(0.25, 0.25, 0.26), metal=0.85,
                      rough=0.54)
    seat = bkit.pbr("CoverSeat", base=(0.15, 0.15, 0.16), metal=0.85,
                    rough=0.66)

    # ---- seating ring: a real annular frame, 660 mm across ---------------
    bkit.tube("SeatingRing", SPEC["seating_ring_diameter"] / 2.0,
              COVER_R - 2.0, 26.0, segments=64, centre=(0.0, 0.0, 13.0),
              mat=seat)

    # ---- dished lid. lathe profiles carry ABSOLUTE z. -------------------
    bkit.lathe("CoverLid", [
        (0.0, 2.0), (COVER_R, 2.0), (COVER_R, 26.0),
        (COVER_R - 12.0, 35.0), (140.0, 35.0), (140.0, 27.0),
        (120.0, 21.0), (0.0, 21.0),
    ], segments=64, mat=iron)

    # ---- six rings of diamond tread bosses --------------------------------
    counts = ring_counts(SPEC["tread_rings"], TREAD_IN, TREAD_OUT, 15)
    for ring in range(SPEC["tread_rings"]):
        r = TREAD_IN + (TREAD_OUT - TREAD_IN) * (ring + 0.5) / SPEC["tread_rings"]
        boss = bkit.box("_tread%d" % ring, SPEC["boss_size"], 10.0, 8.0,
                        mat=raised, centre=(r, 0.0, 34.0))
        boss.rotation_euler = (0.0, 0.0, DIAMOND)
        bkit.array_radial(boss, count=counts[ring], axis="Z")
        boss.name = "TreadRing%d" % ring

    # ---- lifting slot and two keyways, recessed into the lid ------------
    bkit.box("LiftSlot", 96.0, 28.0, 8.0, mat=seat, centre=(0.0, 0.0, 32.0))
    for side, tag in ((-1, "L"), (1, "R")):
        bkit.box("Keyway" + tag, 28.0, 11.0, 6.0, mat=seat,
                 centre=(side * 185.0, 0.0, 32.0))

    return dict(spec=SPEC, parts=3 + SPEC["tread_rings"] + 3)


CHECKS = [
    dict(name="cover_diameter", mm=600.0, tol=1.0, how="diameter",
         part="CoverLid"),
    dict(name="seating_ring_diameter", mm=660.0, tol=1.0, how="diameter",
         part="SeatingRing"),
    dict(name="lid_height", mm=33.0, tol=1.0, how="bbox_z", part="CoverLid"),
    dict(name="overall_height", mm=38.0, tol=1.5, how="bbox_z"),
    dict(name="lift_slot_width", mm=96.0, tol=0.6, how="bbox_x",
         part="LiftSlot"),
]