"""
camera_lens -- 120 x 92 mm 24-70 mm zoom lens standing on its bayonet mount.

Optics is the lathed-barrel domain, and a lens is the purest case: one silhouette
revolved into a mount flange, a barrel, two knurled control rings and a filter
ring with a real internal thread. Every circular feature here is a single
`lathe` over a hand-written (radius, z) profile, and the two knurl bands are
`array_radial` sweeps -- the rib is placed AT the ring radius first, because
the sweep orbits the world origin, not the ring.

The filter thread is `bkit.thread`, a real helix of triangular section sitting
against the 82 mm bore wall. It reads as thread at every camera angle, which a
plain counterbore never does.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    overall_height=120.0,
    mount_diameter=92.0,
    barrel_diameter=88.0,
    filter_thread_diameter=82.0,
    front_element_diameter=76.0,
    focus_ring_ribs=56,
    zoom_ring_ribs=72,
)

LENS_H = SPEC["overall_height"]
MOUNT_R = SPEC["mount_diameter"] / 2.0        # 46
BARREL_R = SPEC["barrel_diameter"] / 2.0      # 44
BORE_R = SPEC["filter_thread_diameter"] / 2.0  # 41


def _knurl(name, radius, sx, sy, length, count, z, mat):
    """One rib at the ring radius, swept around Z. Returns the joined mesh."""
    rib = bkit.box("_rib", sx, sy, length, centre=(radius, 0.0, z), mat=mat)
    bkit.array_radial(rib, count=count, axis="Z")
    return rib


def build():
    dark = bkit.pbr("LensDark", base=(0.055, 0.056, 0.060), rough=0.38)
    rubber = bkit.pbr("LensGrip", base=(0.085, 0.085, 0.090), rough=0.74)
    steel = bkit.preset("brushed_metal")
    glass = bkit.pbr("LensCoating", base=(0.20, 0.30, 0.42), metal=0.25,
                     rough=0.05)
    label = bkit.pbr("LensLabel", base=(0.80, 0.80, 0.78), rough=0.30)

    # ---- bayonet mount flange, 8 mm tall, 92 mm across --------------------
    # NOTE on lathe: its profile z is ABSOLUTE mesh height and `centre` is a
    # FURTHER offset -- unlike cylinder/tube/box, which are origin-centred and
    # take `centre` as their only offset. Passing an absolute profile AND a
    # centre therefore doubles the offset: this 120 mm lens measured 230 mm tall
    # until every lathe centre was dropped. Profiles below carry world z.
    bkit.lathe("LensMount", [(0.0, 0.0), (MOUNT_R, 0.0), (MOUNT_R, 8.0),
                             (0.0, 8.0)], segments=72, mat=steel)

    # ---- main barrel, 8 -> 104 -------------------------------------------
    bkit.lathe("LensBarrel", [(0.0, 8.0), (BARREL_R, 8.0), (BARREL_R, 104.0),
                              (0.0, 104.0)], segments=72, mat=dark)

    # ---- focus ring 60 -> 84, 86 mm, with 56 swept ribs -------------------
    bkit.lathe("FocusRing", [(0.0, 60.0), (43.0, 60.0), (43.0, 84.0),
                             (0.0, 84.0)], segments=72, mat=dark)
    _knurl("FocusRingRibs", 43.4, 1.2, 2.4, 22.0, SPEC["focus_ring_ribs"], 72.0,
           rubber)

    # ---- zoom ring 86 -> 108, 90 mm, with 72 swept ribs -------------------
    bkit.lathe("ZoomRing", [(0.0, 86.0), (45.0, 86.0), (45.0, 108.0),
                            (0.0, 108.0)], segments=72, mat=dark)
    _knurl("ZoomRingRibs", 45.4, 1.2, 2.8, 20.0, SPEC["zoom_ring_ribs"], 97.0,
           rubber)

    # ---- filter ring with a real 82 mm bore and a 3 mm internal step ------
    bkit.lathe("FilterRing", [(0.0, 108.0), (44.0, 108.0), (44.0, 120.0),
                              (BORE_R, 120.0), (BORE_R, 110.0), (0.0, 110.0)],
               segments=72, mat=steel)

    # ---- the filter thread itself: a 9 mm helix on the bore wall ---------
    bkit.thread("FilterThread", 42.4, 3.2, 9.0, turns=3.0, thread_h=0.8,
                mat=steel)
    bkit.move(bpy.data.objects["FilterThread"], 0.0, 0.0, 114.0)

    # ---- front element, recessed 4 mm inside the bore ---------------------
    bkit.lathe("FrontElement", [(0.0, 110.0), (38.0, 110.0), (38.0, 114.0),
                                (0.0, 114.0)], segments=64, mat=glass)

    # ---- rear element, sunk into the mount face --------------------------
    bkit.lathe("RearElement", [(0.0, 8.5), (36.0, 8.5), (36.0, 11.0),
                               (0.0, 11.0)], segments=64, mat=glass)

    # ---- three bayonet lugs on the mount skirt ---------------------------
    lug = bkit.box("_lug", 4.0, 4.5, 2.2, centre=(45.0, 0.0, 9.6), mat=steel)
    bkit.array_radial(lug, count=3, axis="Z")

    # ---- printed distance-scale band on the barrel -----------------------
    bkit.tube("LensScaleBand", 44.6, 44.0, 9.0, segments=72,
              centre=(0.0, 0.0, 40.0), mat=label)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="overall_height", mm=120.0, tol=0.5, how="bbox_z"),
    dict(name="mount_diameter", mm=92.0, tol=0.5, how="diameter",
         part="LensMount"),
    dict(name="front_element_diameter", mm=76.0, tol=0.5, how="diameter",
         part="FrontElement"),
    dict(name="barrel_diameter", mm=88.0, tol=0.5, how="diameter",
         part="LensBarrel"),
]