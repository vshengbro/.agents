"""
erlenmeyer_flask -- 250 ml conical (Erlenmeyer) flask: 108 mm base, 138 mm tall,
38 mm neck, 2 mm wall.

The cone is not a straight triangle: the shoulder leaves the base and runs into
a short cylindrical neck land, which is the difference between a lab flask and
a funnel. The 250 ml line is found by bisecting the real frustum volume
V = pi*h/3*(R1^2 + R1*R2 + R2^2) of the bore, so the mark is calibrated instead
of placed by eye; the mark and the white label patch are engraved steps in the
revolve profile, not a decal.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_diameter=108.0,     # outside diameter of the foot
    overall_height=138.0,    # table to top of the rim
    neck_diameter=38.0,      # outside diameter of the neck (documentation only)
    wall=2.0,                # borosilicate
    volume_ml=250.0,
    label_band_height=20.0,
)

BR = SPEC["base_diameter"] / 2.0
H = SPEC["overall_height"]
NR = SPEC["neck_diameter"] / 2.0
WALL = SPEC["wall"]
FLOOR = 3.0                 # inside floor
FOOT_Z = 4.0                # where the cone leaves the foot
SHOULDER_Z = 78.0           # cone meets the neck land


def r_out(z):
    """Outside radius of the cone at height z (clamped to the neck land)."""
    if z <= FOOT_Z:
        return BR
    if z >= SHOULDER_Z:
        return NR
    return BR + (NR - BR) * (z - FOOT_Z) / (SHOULDER_Z - FOOT_Z)


def r_in(z):
    return r_out(max(z, FOOT_Z)) - WALL


def volume_to(z):
    """Bore volume (mm^3) from the inside floor up to height z."""
    h = max(0.0, min(z, SHOULDER_Z) - FLOOR)
    r1, r2 = r_in(FLOOR), r_in(FLOOR + h)
    return math.pi * h / 3.0 * (r1 * r1 + r1 * r2 + r2 * r2)


def fill_height(vol_ml):
    """Bisect the bore volume for the height that holds `vol_ml`."""
    target = vol_ml * 1000.0
    lo, hi = FLOOR, SHOULDER_Z
    for _ in range(48):
        mid = 0.5 * (lo + hi)
        if volume_to(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def build():
    glass = bkit.pbr("FlaskGlass", base=(0.88, 0.91, 0.91), rough=0.05,
                     transmission=0.72, ior=1.47, coat=0.5)
    ink = bkit.pbr("FlaskInk", base=(0.08, 0.08, 0.09), rough=0.45)
    label = bkit.pbr("FlaskLabel", base=(0.90, 0.89, 0.86), rough=0.42)

    z_mark = fill_height(SPEC["volume_ml"])
    z_lab = z_mark + 6.0
    lab_h = SPEC["label_band_height"]

    # ---- outer surface: foot -> calibrated mark -> label -> cone -> neck ---
    prof = [
        (0.0, 0.0),
        (BR - 6.0, 0.0),
        (BR - 1.0, 1.6),                    # rounded foot edge
        (BR, FOOT_Z),
        # 250 ml graduation line
        (r_out(z_mark), z_mark),
        (r_out(z_mark) - 0.45, z_mark),
        (r_out(z_mark) - 0.45, z_mark + 1.2),
        (r_out(z_mark), z_mark + 1.2),
        # white ceramic label patch, engraved 0.35 mm into the glass
        (r_out(z_lab), z_lab),
        (r_out(z_lab) - 0.35, z_lab),
        (r_out(z_lab) - 0.35, z_lab + lab_h),
        (r_out(z_lab), z_lab + lab_h),
        (NR, SHOULDER_Z + 6.0),              # cone -> neck land
        (NR, H - 2.0),
        (NR - 0.6, H),                       # rolled rim
        (NR - WALL, H),                      # across the rim
        (NR - WALL, H - 4.0),                # down the neck bore
    ]

    # ---- inner surface: neck bore -> inside of the cone -> bore floor ------
    steps = 8
    for i in range(steps + 1):
        z = (H - 4.0) + (FLOOR - (H - 4.0)) * i / steps
        prof.append((r_in(z), z))
    prof.append((r_in(FLOOR) - 8.0, FLOOR))
    prof.append((0.0, FLOOR))

    flask = bkit.lathe("FlaskBody", prof, segments=128, mat=glass)

    # Recessed faces sit strictly inside the cone radius; the outer wall faces
    # sit exactly on it, so a radius test selects the engraving and nothing else.
    def _engraved(c):
        r, z = _rad(c) / bkit.MM, c.z / bkit.MM
        if not (z_mark - 0.1 <= z <= z_mark + 1.3) and \
           not (z_lab - 0.1 <= z <= z_lab + lab_h + 0.1):
            return False
        return r < r_out(max(z, FOOT_Z)) + 0.05

    bkit.assign_faces_by(flask, ink, lambda c, n: _engraved(c)
                         and (z_mark - 0.1 <= c.z / bkit.MM <= z_mark + 1.3))
    bkit.assign_faces_by(flask, label, lambda c, n: _engraved(c)
                         and (z_lab - 0.1 <= c.z / bkit.MM <= z_lab + lab_h + 0.1))

    return dict(spec=SPEC, parts=1)


def _rad(c):
    return (c.x ** 2 + c.y ** 2) ** 0.5


CHECKS = [
    dict(name="base_diameter", mm=108.0, tol=0.3, how="diameter", part="FlaskBody"),
    dict(name="overall_height", mm=138.0, tol=0.3, how="bbox_z", part="FlaskBody"),
    dict(name="assembly_height", mm=138.0, tol=0.3, how="bbox_z"),
]