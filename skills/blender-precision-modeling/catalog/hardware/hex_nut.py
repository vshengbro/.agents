"""
hex_nut -- ISO 4032 M10 hex nut with a real internal thread.

Dimensions are the ISO 4032 table values for M10 (across flats s = 17, height
m = 8.4), so this nut is visibly squatter and narrower than the M12 hex_bolt
head it mates with. The bore is a genuine helical feature: instead of sweeping a
helix (which leaves an open shell), the nut is cut by a solid of revolution
whose radius is a trapezoidal sawtooth. Subtracting it leaves a bore that is
narrowest across each thread crest and opens out to the nominal diameter at the
groove root -- an internal thread that is watertight by construction.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# ---------------------------------------------------------------------------
# HARNESS WORKAROUND (no shared file is edited). Blender's camera data defaults
# to clip_start = 0.1 m while bkit.frame() parks the camera at
# radius * 1.18 / tan(vfov/2) -- 77 mm from this 19 mm nut. Everything nearer
# than 0.1 m is discarded, so the model renders as an empty backdrop and
# auto_exposure reports "probe unreadable" (the calibration ball is clipped
# too, leaving every probe pixel transparent). render_shots() resolves
# `camera` from bkit's module globals at call time, so re-binding it with a
# near plane derived from the harness's own distance fixes small subjects.
# Needed for any item whose bounding radius is under ~13.5 mm.
# ---------------------------------------------------------------------------
_orig_camera = bkit.camera


def _camera(az_deg, el_deg, dist_m, lens=85.0, target=(0, 0, 0)):
    cam = _orig_camera(az_deg, el_deg, dist_m, lens, target)
    cam.data.clip_start = max(1e-5, dist_m * 0.02)
    return cam


bkit.camera = _camera

NOMINAL = 10.0          # D, nominal diameter
PITCH = 1.5             # coarse pitch
ACROSS_FLATS = 17.0     # s, ISO 4032
HEIGHT = 8.4            # m, ISO 4032
MINOR_D = 8.376         # d1 = D - 1.0825 * P, internal thread minor diameter

SPEC = dict(nominal_diameter=NOMINAL,
            pitch=PITCH,
            across_flats=ACROSS_FLATS,
            height=HEIGHT,
            minor_diameter=MINOR_D)


def hex_outline(across_flats, phase=30.0):
    """Hexagon with FLATS facing +/-X so across-flats lands on the bbox X axis."""
    r = (across_flats / 2.0) / math.cos(math.radians(30.0))
    return [(math.cos(math.radians(phase + 60.0 * i)) * r,
             math.sin(math.radians(phase + 60.0 * i)) * r) for i in range(6)]


def zinc_steel():
    """Zinc-plated nut steel that survives this studio.

    bkit's metal presets all use metal=1.0, which removes the diffuse term
    entirely; a pure metal only shows what it reflects, and this studio's world
    is dark except for a narrow bright band, so metal=1.0 hardware renders as a
    black blob. Holding metalness at 0.72 keeps the specular metal read while
    the residual diffuse keeps the silhouette visible.
    """
    return bkit.pbr("NutZinc", base=(0.78, 0.80, 0.83), metal=0.72, rough=0.26)


def threaded_bore_cutter(name, segments=72):
    """Sawtooth solid of revolution: the tool that cuts an internal thread.

    The radius runs r_crest -> r_root -> r_crest once per pitch, with the wide
    part spanning the groove bottom and the narrow part the thread top land.
    The bore therefore reads as a screw thread from any viewing angle and the
    cutter itself is a closed, watertight solid (both profile ends sit on the
    axis, so the lathe closes it with two pole fans).
    """
    r_crest = MINOR_D / 2.0            # narrowest: internal thread crest
    r_root = NOMINAL / 2.0             # widest: internal thread root
    turns = int(math.ceil(2.0 * HEIGHT / PITCH))
    span = turns * PITCH                # whole pitches, so the profile is monotonic
    prof = [(0.0, -span / 2.0)]
    for k in range(turns):
        z = -span / 2.0 + k * PITCH
        prof += [(r_crest, z),
                 (r_root, z + 0.10 * PITCH),
                 (r_root, z + 0.60 * PITCH),
                 (r_crest, z + 0.70 * PITCH)]
    prof.append((0.0, span / 2.0))
    return bkit.lathe(name, prof, segments=segments)


def build():
    steel = zinc_steel()

    body = bkit.extrude_profile("NutBody", hex_outline(ACROSS_FLATS), HEIGHT,
                                centre=(0, 0, 0), mat=steel)
    # Break the corners and chamfer both faces before the bore is cut: bevelling
    # after the boolean would also round the thread flanks and eat the profile.
    bkit.bevel(body, width_mm=0.55, segments=2, angle_deg=35)

    cutter = threaded_bore_cutter("BoreCutter")
    bkit.boolean(body, cutter, "DIFFERENCE")

    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="across_flats", mm=17.0, tol=0.05, how="bbox_x", part="NutBody"),
    # The theoretical across-corners of a 17 mm A/F hexagon is 19.63, but the
    # corners are broken by the 0.55 mm bevel a real nut carries, which trims
    # ~0.29 mm off the diagonal. The tolerance admits that chamfer, not error.
    dict(name="across_corners", mm=19.63, tol=0.35, how="bbox_y", part="NutBody"),
    dict(name="nut_height", mm=8.4, tol=0.05, how="bbox_z", part="NutBody"),
]