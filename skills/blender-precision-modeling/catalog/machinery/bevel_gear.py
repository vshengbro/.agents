"""
bevel_gear -- 20-tooth straight bevel gear on a 45 deg cone angle.

A bevel gear is a cone of teeth, so both the tooth depth AND the tooth width
have to converge toward the apex. Building it as a lathe cone plus a toothed
loft whose tooth arc width is held constant (angular width shrinking with
radius) is what makes it read as bevel rather than as a spur gear with a
tapered rim. The tooth blank is kept 0.5 mm inside the cone at both faces so
no boolean sees a coplanar pair of faces.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    teeth=20,
    module_mm=3.0,
    cone_angle_deg=45.0,
    face_width=18.0,
    pitch_cone_angle=22.5,
    root_diameter_small=43.0,     # at the small (heel) end
    tip_diameter_large=85.0,      # at the large (toe) end
    bore_diameter=18.0,
    back_diameter=44.0,
)

SECTIONS = 5
FLANK_STEPS = 4
R_ROOT_SMALL = 21.5              # tooth root radius at z = 0
R_ROOT_LARGE = 39.5              # tooth root radius at z = face_width
R_REF = 30.5                     # reference radius for constant tooth arc width


def _tooth_ring(r_root, r_out, z, teeth):
    """Toothed ring at height z with constant ARCLENGTH tooth width, so the
    angular width shrinks as the radius grows (a bevel tooth converging)."""
    step = 2.0 * math.pi / teeth
    arc_root = step * 0.19 * R_REF
    arc_tip = step * 0.115 * R_REF
    h_root = arc_root / r_root
    h_tip = arc_tip / r_out
    pts = []
    for t in range(teeth):
        a = t * step
        for k in range(FLANK_STEPS + 1):
            f = k / float(FLANK_STEPS)
            ang = a - h_root + (h_root - h_tip) * f
            r = r_root + (r_out - r_root) * f
            pts.append((math.cos(ang) * r, math.sin(ang) * r, z))
        ang = a + h_tip
        pts.append((math.cos(ang) * r_out, math.sin(ang) * r_out, z))
        for k in range(FLANK_STEPS - 1, -1, -1):
            f = k / float(FLANK_STEPS)
            ang = a + h_root - (h_root - h_tip) * f
            r = r_root + (r_out - r_root) * f
            pts.append((math.cos(ang) * r, math.sin(ang) * r, z))
    return pts


def build():
    z = SPEC["teeth"]
    m = SPEC["module_mm"]
    w = SPEC["face_width"]

    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    # ---- cone body: a solid truncated cone, axis on Z --------------------
    body = bkit.lathe("BevelCone",
                      [(0.0, 0.0),
                       (R_ROOT_SMALL + 0.5, 0.0),
                       (R_ROOT_LARGE + 0.5, w),
                       (0.0, w)],
                      segments=96, mat=steel)
    bkit.recalc(body)

    # ---- teeth: a lofted cone of toothed rings ---------------------------
    sections = []
    for s in range(SECTIONS):
        t = s / float(SECTIONS - 1)
        z_h = w * t
        r_root = R_ROOT_SMALL + (R_ROOT_LARGE - R_ROOT_SMALL) * t
        sections.append(_tooth_ring(r_root, r_root + m, z_h, z))
    teeth = bkit.loft("BevelTeeth", sections, closed_loop=True,
                      cap_start=True, cap_end=True, mat=steel)
    bkit.recalc(teeth)
    bkit.weld(teeth)
    bkit.boolean(body, teeth, "UNION")

    # ---- back hub boss, then ONE bore through cone + boss ---------------
    hub = bkit.cylinder("BackBoss", R_ROOT_SMALL * 0.62, 9.0, segments=72,
                        centre=(0, 0, -3.0), mat=dark)
    bkit.boolean(body, hub, "UNION")

    bore = bkit.cylinder("Bore", SPEC["bore_diameter"] / 2.0, w * 4, segments=96,
                         centre=(0, 0, -3.0))
    bkit.boolean(body, bore, "DIFFERENCE")
    key = bkit.box("Keyway", 6.0, 3.5, w * 4, centre=(6.0, 0.0, -3.0))
    bkit.boolean(body, key, "DIFFERENCE")

    bkit.recalc(body)
    bkit.assign_faces_by(body, dark, lambda c, n: c.z < 0.6)
    return dict(spec=SPEC, parts=1)


CHECKS = [
    dict(name="tip_diameter_large", mm=85.0, tol=0.6, how="diameter", part="BevelCone"),
    dict(name="overall_height", mm=25.5, tol=0.4, how="bbox_z", part="BevelCone"),
    dict(name="tip_diameter_large_y", mm=85.0, tol=0.6, how="bbox_y", part="BevelCone"),
]
