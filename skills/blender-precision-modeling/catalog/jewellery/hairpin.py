"""
hairpin -- 55 mm bobby pin: one folded wire, 1.44 mm section, crimped arms.

A bobby pin is a single wire folded in half, so the whole part is two features
that meet: a U bend and two crimped arms. The U is an arc_torus, and the arms
are lofts whose section radius carries the crimp -- the three shallow ridges
along a bobby pin arm are a function of the wire's thickness along its length,
not bumps stuck on afterwards.

The arms are the same loft duplicated with a 180 degree rotation about Z, which
mirrors it about the bend's axis. The right arm starts at x = 6.0 and the bend
ends at x = 7.0, so the two solids overlap by 1 mm rather than meeting exactly
flush: a butt joint between two solids is a tangency, and tangency is where
non-manifold edges come from.
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

BEND_R = 7.0           # centreline radius of the U
WIRE_R = 0.72          # 1.44 mm wire
HALF_LEN = 27.5        # half the overall length -> 55 mm overall
ARM_X0 = 6.0           # where the arm loft starts, inside the bend's end
ARM_SEG = 20           # wire cross-section points
ARM_STATIONS = 24      # stations along the arm
CRIMPS = 3             # crimp ridges per arm
BASE_R = 0.60          # wire radius between crimps
CRIMP_R = 0.92         # wire radius at a crimp
TIP_R = 0.16           # wire radius at the very tip

SPEC = dict(overall_length=2.0 * HALF_LEN,
            wire_diameter=2.0 * WIRE_R,
            bend_radius=BEND_R,
            crimps_per_arm=CRIMPS,
            arm_length=HALF_LEN - ARM_X0)


def build():
    steel = bkit.pbr("PinSteel", base=(0.80, 0.82, 0.85), metal=0.85, rough=0.22)

    # ---- the U bend: the upper half of a circle in the XZ plane -----------
    bend = bkit.arc_torus("Bend", BEND_R, WIRE_R, 0.0, 180.0, plane="XZ",
                          seg_major=44, seg_minor=ARM_SEG, mat=steel, caps=True)

    # ---- one crimped arm, lofted along +X ---------------------------------
    sections = []
    for i in range(ARM_STATIONS + 1):
        t = i / float(ARM_STATIONS)
        x = ARM_X0 + t * (HALF_LEN - ARM_X0)
        if t > 0.88:                      # round the tip off
            r = CRIMP_R + (TIP_R - CRIMP_R) * ((t - 0.88) / 0.12)
        else:
            r = BASE_R + (CRIMP_R - BASE_R) * (0.5 - 0.5 * math.cos(
                2.0 * math.pi * CRIMPS * t / 0.88))
        ring = []
        for j in range(ARM_SEG):
            a = 2.0 * math.pi * j / ARM_SEG
            ring.append((x, r * math.cos(a), r * math.sin(a)))
        sections.append(ring)
    arm = bkit.loft("Arm", sections, closed_loop=True, cap_start=True,
                    cap_end=True, mat=steel, smooth=True)

    # the second arm is the same loft turned about the bend's axis
    bkit.duplicate(arm, "Arm", offset_mm=(0.0, 0.0, 0.0),
                   rot_deg=(0.0, 0.0, 180.0))

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="overall_length", mm=55.0, tol=0.15, how="bbox_x", part=None),
    # the bend is a circle in XZ, so its Y extent is exactly the wire diameter
    dict(name="bend_wire_diameter", mm=1.44, tol=0.05, how="bbox_y", part="Bend"),
    dict(name="arm_length", mm=21.5, tol=0.15, how="bbox_x", part="Arm"),
    dict(name="arm_crimp_diameter", mm=1.84, tol=0.06, how="bbox_z", part="Arm")
]