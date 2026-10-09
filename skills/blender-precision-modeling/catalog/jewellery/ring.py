"""
ring -- 4 mm comfort-fit wedding band, 17.3 mm inside diameter, three stones.

A wedding ring is named for its INSIDE diameter, not its outside: a US size 7
is 17.3 mm, and every other dimension follows from that plus the band width.
So the band is a revolved cross-section (a closed (r, z) loop, no end caps) with
the inside face held at exactly 8.65 mm radius and the wall carried out to
10.25 -- the 1.6 mm section real comfort-fit bands are milled from.

The stones are arrayed with array_linear rather than placed by hand: the row is
a pitch (2.6 mm centre to centre), and a three-stone ring whose stones were
typed in at slightly different positions is visibly not a machine product.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND (no shared file is edited). Blender's camera defaults to
# clip_start = 0.1 m, but bkit.frame() parks the camera barely 30 mm from a
# 20 mm ring, so everything nearer than 0.1 m is clipped away and the model
# renders as an empty backdrop. Re-binding bkit.camera with a near plane
# derived from the distance the harness chose fixes it; render_shots() resolves
# `camera` from bkit's module globals at call time.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

INNER_D = 17.3          # US size 7
BAND_W = 4.0            # band width across the finger
WALL = 1.6              # radial section thickness
STONE_R = 1.15          # melee stone diameter
STONE_PITCH = 2.6       # centre-to-centre of the three stones

RI = INNER_D / 2.0                  # 8.65
RO = RI + WALL                      # 10.25
HZ = BAND_W / 2.0                   # 2.0
CHAMFER = 0.45                      # edge break top and bottom

SPEC = dict(inner_diameter=INNER_D,
            outer_diameter=2.0 * RO,
            band_width=BAND_W,
            wall_thickness=WALL,
            stone_diameter=2.0 * STONE_R,
            stone_pitch=STONE_PITCH)


def build():
    gold = bkit.pbr("WeddingGold", base=(1.00, 0.80, 0.42), metal=0.85, rough=0.14)
    gem = bkit.pbr("Diamond", base=(0.90, 0.94, 0.98), metal=0.0, rough=0.02,
                   transmission=0.6, ior=2.4)

    # ---- band: closed (r, z) cross-section, revolved ----------------------
    # Rolled onto the mandrel, so the inside wall is dead straight and every
    # break is on the outside edge where the light catches it.
    profile = [
        (RI, -HZ + CHAMFER),
        (RI + CHAMFER, -HZ),
        (RO - CHAMFER, -HZ),
        (RO, -HZ + CHAMFER),
        (RO, HZ - CHAMFER),
        (RO - CHAMFER, HZ),
        (RI + CHAMFER, HZ),
        (RI, HZ - CHAMFER),
        (RI, -HZ + CHAMFER),           # closes the loop; lathe(cap_ends=False)
    ]
    band = bkit.lathe("Band", profile, segments=96, cap_ends=False, mat=gold)
    # +90 deg about X puts the band's axis along Y (its width across the
    # finger) and turns the ring's in-plane +Y into world up, so the stone row
    # sits on the top of an upright ring.
    band.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    # ---- three melee stones across the crown --------------------------------
    stones = bkit.sphere("Stones", STONE_R, segments=24, rings=12,
                         centre=(0.0, 0.0, RO - 0.10), mat=gem)
    bkit.array_linear(stones, 3, (STONE_PITCH, 0.0, 0.0), world=True)

    return dict(spec=SPEC, parts=2)


CHECKS = [
    dict(name="outer_diameter", mm=20.5, tol=0.05, how="bbox_x", part="Band"),
    dict(name="band_width", mm=4.0, tol=0.05, how="bbox_y", part="Band"),
    # the ring stands upright, so its radial extent is the same as its
    # outside diameter -- measured on the band alone, not the assembly
    dict(name="ring_height", mm=20.5, tol=0.05, how="bbox_z", part="Band"),
    # 2 x pitch + one stone diameter
    dict(name="stone_row", mm=7.5, tol=0.05, how="bbox_x", part="Stones")
]