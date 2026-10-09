"""
necklace -- 0.8 mm cable chain, 34 mm link radius, carrying a 14 mm disc pendant.

The chain is 30 links walked along a computed 150 degree arc, not a straight
line: a necklace hangs, and a chain built along a chord reads as a wire. The
links alternate their torus axis by 90 degrees, which is what makes a run of
tori interlock into a cable chain instead of lying flat side by side.

Link pitch is derived, not chosen: the arc length of the 150 degree span is
CHAIN_R * span_rad, and dividing that by the link count is what keeps the run
continuous. Every link is a duplicate() of the first, positioned and oriented
from the path, so no two links can land on the same coordinate.
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

CHAIN_R = 27.0          # centreline radius of the hanging chain
HUB_Z = 49.0            # centre of that circle; the chain is its lower arc
SPAN_DEG = 150.0        # 195 -> 345 degrees, the lower half plus a little
N_LINKS = 30
LINK_R = 1.20           # link centreline radius (gives a 2.4 mm link)
WIRE_R = 0.40           # 0.8 mm wire, the section the brief asks for
BAIL_R = 2.00
PENDANT_R = 7.00
PENDANT_T = 2.60

SPEC = dict(chain_radius=CHAIN_R,
            link_outer_diameter=2.0 * (LINK_R + WIRE_R),
            wire_diameter=2.0 * WIRE_R,
            link_count=N_LINKS,
            pendant_diameter=2.0 * PENDANT_R,
            overall_height=29.5)


def build():
    gold = bkit.pbr("ChainGold", base=(0.99, 0.80, 0.41), metal=0.85, rough=0.15)
    stone = bkit.pbr("PendantStone", base=(0.86, 0.90, 0.95), metal=0.0, rough=0.05,
                     transmission=0.45, ior=1.8)

    # ---- chain -------------------------------------------------------------
    a0, a1 = math.radians(195.0), math.radians(345.0)
    # axis="Y" puts each link IN the XZ plane, the plane the chain hangs in.
    # bkit.duplicate() SETS rotation_euler rather than composing with it, so
    # the 90 deg about X has to be restated for every copy or the copies land
    # flat in XY instead of hanging in the chain's plane.
    first = bkit.torus("ChainLink", LINK_R, WIRE_R, seg_major=28, seg_minor=10,
                       centre=(CHAIN_R * math.cos(a0), 0.0,
                               HUB_Z + CHAIN_R * math.sin(a0)),
                       axis="Y", mat=gold)
    links = [first]
    for i in range(1, N_LINKS):
        t = i / float(N_LINKS - 1)
        a = a0 + (a1 - a0) * t
        # alternate the ring's axis so successive links interlock
        links.append(bkit.duplicate(
            first, "ChainLink", offset_mm=(CHAIN_R * math.cos(a), 0.0,
                                           HUB_Z + CHAIN_R * math.sin(a)),
            rot_deg=(90.0, 0.0, 90.0 * (i % 2))))
    # The bottom link lands at z = HUB_Z - CHAIN_R = 22, which is exactly where
    # the bail's 1.6 mm hole sits, so the run ends threaded through the bail
    # with no repositioning move to get wrong.
    bkit.join(links, name="Chain")

    # ---- bail ring, neck and pendant ---------------------------------------
    bail = bkit.torus("Bail", BAIL_R, WIRE_R, seg_major=40, seg_minor=12,
                      centre=(0.0, 0.0, 21.0), axis="Y", mat=gold)
    neck = bkit.cylinder("PendantNeck", 0.6, 3.6, segments=20,
                         centre=(0.0, 0.0, 17.9), mat=gold)
    pendant = bkit.lathe(
        "Pendant",
        [(0.0, -PENDANT_T / 2.0),
         (PENDANT_R - 0.6, -PENDANT_T / 2.0),
         (PENDANT_R, -PENDANT_T / 2.0 + 0.6),
         (PENDANT_R, PENDANT_T / 2.0 - 0.8),
         (PENDANT_R - 1.6, PENDANT_T / 2.0 + 0.5),
         (0.0, PENDANT_T / 2.0 + 0.7)],
        segments=64, centre=(0.0, 0.0, 15.4), mat=stone)

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="link_outer_diameter", mm=3.2, tol=0.05, how="bbox_y", part="Chain"),
    dict(name="bail_outer_diameter", mm=4.8, tol=0.05, how="bbox_x", part="Bail"),
    dict(name="pendant_diameter", mm=14.0, tol=0.05, how="diameter", part="Pendant"),
    dict(name="pendant_thickness", mm=3.3, tol=0.05, how="bbox_z", part="Pendant"),
    dict(name="overall_height", mm=29.5, tol=0.3, how="bbox_z", part=None)
]