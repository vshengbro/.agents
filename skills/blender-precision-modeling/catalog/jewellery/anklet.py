"""
anklet -- 152 mm box-chain anklet, 36 links of 12 mm, with a lobster clasp.

Same construction as the necklace chain and for the same reason: a chain is a
run of identical links walked along a closed path, and the number of links and
their pitch are consequences of the path length, not free choices. Here the
path is a full circle of radius 70 mm, so the pitch is 2*pi*70/36 = 12.2 mm
against a 12.0 mm link -- the run is continuous with a 0.2 mm overlap, which is
what makes consecutive links interlock instead of float apart.

Every link is a duplicate of the first, alternating a quarter turn about the
path normal. The clasp is a real lobster claw: a body, a lever and a ring,
hung at the top of the circle where the circle's tangent is horizontal.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND -- see catalog/hardware/washer.py.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

PATH_R = 70.0
N_LINKS = 36
LINK_R = 5.40          # centreline radius -> 12.0 mm link across
WIRE_R = 0.60
CLASP_L = 16.0
CLASP_W = 7.0
RING_R = 3.2

SPEC = dict(anklet_outer_diameter=2.0 * (PATH_R + LINK_R + WIRE_R),
            link_diameter=2.0 * (LINK_R + WIRE_R),
            wire_diameter=2.0 * WIRE_R,
            link_count=N_LINKS,
            clasp_length=CLASP_L,
            overall_height=163.1,
            outer_diameter_x=149.87)


def build():
    gold = bkit.pbr("AnkletGold", base=(0.99, 0.80, 0.41), metal=0.85, rough=0.16)
    steel = bkit.pbr("AnkletClasp", base=(0.82, 0.84, 0.87), metal=0.85, rough=0.20)

    # ---- the run -----------------------------------------------------------
    # Path is the circle in the XZ plane, so links lie in XZ and the quarter
    # turn that alternates them is about the path normal, Y.
    #
    # bkit.duplicate() SETS rotation_euler from rot_deg; it does not compose
    # with the orientation place() already applied for axis="Y". So the 90 deg
    # about X that puts the ring in XZ has to be restated here for every copy --
    # passing (0, 0, 90*i) instead silently lays every copied link flat in XY.
    a0 = math.pi / 2.0
    first = bkit.torus("ChainLink", LINK_R, WIRE_R, seg_major=48, seg_minor=10,
                       centre=(PATH_R * math.cos(a0), 0.0, PATH_R * math.sin(a0)),
                       axis="Y", mat=gold)
    links = [first]
    for i in range(1, N_LINKS):
        a = a0 + 2.0 * math.pi * i / N_LINKS
        links.append(bkit.duplicate(
            first, "ChainLink",
            offset_mm=(PATH_R * math.cos(a), 0.0, PATH_R * math.sin(a)),
            rot_deg=(90.0, 0.0, 90.0 * (i % 2))))
    bkit.join(links, name="Chain")

    # ---- lobster-claw clasp, hanging at the top of the circle --------------
    cz = PATH_R + LINK_R + WIRE_R - 1.0
    body = bkit.rounded_box("ClaspBody", CLASP_L, CLASP_W, 4.6, r=2.0, segments=4,
                            centre=(0.0, 0.0, cz + 2.0), mat=steel)
    lever = bkit.rounded_box("ClaspLever", 11.0, 2.6, 1.8, r=0.8, segments=3,
                             centre=(0.0, 0.0, cz + 4.6), mat=steel)
    ring = bkit.torus("ClaspRing", RING_R, 0.9, seg_major=36, seg_minor=10,
                      centre=(0.0, 0.0, cz + 8.0), axis="Y", mat=steel)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    # 36 links on a 10 deg pitch: the even links (which lie in XZ) fall at
    # 90, 110 ... 350 degrees, so the X extreme is at 170 degrees, not 180.
    # 2 * (70*cos10 + 6) = 149.87
    dict(name="anklet_outer_diameter", mm=149.87, tol=0.1, how="bbox_x", part="Chain"),
    dict(name="anklet_outer_height", mm=152.0, tol=0.1, how="bbox_z", part="Chain"),
    dict(name="clasp_length", mm=16.0, tol=0.1, how="bbox_x", part="ClaspBody"),
    dict(name="clasp_ring_diameter", mm=8.2, tol=0.1, how="bbox_x", part="ClaspRing"),
    dict(name="overall_height", mm=163.1, tol=0.3, how="bbox_z", part=None)
]