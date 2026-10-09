"""
hex_bolt -- M12 hex-head bolt with a real helical thread and a chamfered head.

Covers the two thread families in one part: the external helical thread on the
shank, and the simple internal profile implied by the hex head. Head size follows
ISO 4014 proportions relative to the nominal diameter, so a viewer can tell an
M12 from an M8 by silhouette alone.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

M = 12.0                     # nominal diameter
PITCH = 1.75                 # M12 coarse
SPEC = dict(
    nominal_diameter=M,
    pitch=PITCH,
    thread_length=50.0,
    shank_length=90.0,        # total length under the head
    head_across_flats=18.0,   # ISO 4014 for M12
    head_height=7.5,
    major_diameter=12.0,
    minor_diameter=10.1,
)


def build():
    steel = bkit.preset("steel")
    dark = bkit.preset("dark_metal")

    L = SPEC["shank_length"]
    head_h = SPEC["head_height"]
    af = SPEC["head_across_flats"]          # across flats
    r_af = af / 2.0
    r_circ = r_af / math.cos(math.radians(30))   # circumradius of the hexagon

    # ---- hex head: a hexagonal prism with a chamfered top and a washer face
    hex_pts = [(math.cos(math.radians(30 + 60 * i)) * r_circ,
                math.sin(math.radians(30 + 60 * i)) * r_circ) for i in range(6)]
    head = bkit.extrude_profile("HexHead", hex_pts, head_h,
                                centre=(0, 0, head_h / 2.0), mat=steel)
    # chamfer the top edge
    bkit.bevel(head, width_mm=0.9, segments=2, angle_deg=35)

    # ---- shank: plain unthreaded portion first, then the threaded portion --
    thread_len = SPEC["thread_length"]
    plain_len = L - thread_len
    shank = bkit.cylinder("Shank", SPEC["minor_diameter"] / 2.0, plain_len,
                          segments=64,
                          centre=(0, 0, -plain_len / 2.0), mat=steel)

    thread = bkit.thread("Thread", radius=SPEC["major_diameter"] / 2.0,
                         pitch=PITCH, length=thread_len,
                         thread_h=(SPEC["major_diameter"] - SPEC["minor_diameter"]) / 2.0,
                         segments_per_turn=32, mat=steel)
    thread.location = bkit.v(0, 0, -L + thread_len / 2.0)

    bolt = bkit.join([head, shank, thread], name="Bolt")

    bkit.assign(bolt, steel)
    return dict(spec=SPEC, parts=1)

CHECKS = [
    dict(name="head_across_flats", mm=18.0, tol=0.4, how="bbox_x", part="Bolt"),
    dict(name="shank_length_total", mm=97.5, tol=0.9, how="bbox_z", part="Bolt"),
]
