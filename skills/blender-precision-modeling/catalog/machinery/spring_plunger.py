"""
spring_plunger -- 12 mm spring plunger: body, plunger, exposed coil spring.

Two things here are built rather than bought. The body is a single revolved
profile that already contains the pin bore AND the wider spring chamber -- one
lathe, no booleans, so it cannot go non-manifold. The spring is a real helix
swept by lofting a circular section along the helix, framing each ring with the
local tangent, which is what makes the wire lie flat against the coil instead
of skewing.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_diameter=12.0,
    body_height=9.0,
    chamber_diameter=10.4,
    chamber_depth=6.5,
    pin_bore_diameter=5.2,
    plunger_stem_diameter=4.8,
    plunger_shoulder_diameter=10.0,
    plunger_nose_diameter=6.0,
    plunger_length=24.0,
    spring_coil_diameter=8.4,
    spring_wire_diameter=1.4,
    spring_turns=8.0,
    overall_height=27.0,
)

WIRE_SEG = 10
STEPS_PER_TURN = 14


def _coil(z0, z1, r_coil, r_wire, turns):
    """Loft a circular section along a helix. The section plane is spanned by
    the radial direction and tangent x radial, so the wire stays square to the
    coil at every step."""
    n = int(turns * STEPS_PER_TURN)
    pitch = (z1 - z0) / turns
    sections = []
    for s in range(n + 1):
        t = s / float(n)
        a = 2.0 * math.pi * turns * t
        c, s_ = math.cos(a), math.sin(a)
        cx, cy, cz = r_coil * c, r_coil * s_, z0 + (z1 - z0) * t
        tx = -r_coil * s_
        ty = r_coil * c
        tz = pitch
        tl = math.sqrt(tx * tx + ty * ty + tz * tz)
        tx, ty, tz = tx / tl, ty / tl, tz / tl
        ux, uy, uz = c, s_, 0.0                     # radial, already unit
        vx = ty * uz - tz * uy
        vy = tz * ux - tx * uz
        vz = tx * uy - ty * ux                       # tangent x radial
        ring = []
        for j in range(WIRE_SEG):
            p = 2.0 * math.pi * j / WIRE_SEG
            cp, sp = math.cos(p), math.sin(p)
            ring.append((cx + r_wire * (cp * ux + sp * vx),
                         cy + r_wire * (cp * uy + sp * vy),
                         cz + r_wire * (cp * uz + sp * vz)))
        sections.append(ring)
    return sections


def build():
    r_b = SPEC["body_diameter"] / 2.0
    h = SPEC["body_height"]
    r_ch = SPEC["chamber_diameter"] / 2.0
    r_pin = SPEC["pin_bore_diameter"] / 2.0
    z_floor = h - SPEC["chamber_depth"]

    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    # ---- body: bore + chamber in one revolved profile ------------------
    body = bkit.lathe("Body",
                      [(0.0, 0.0), (r_b, 0.0), (r_b, h), (r_pin, h),
                       (r_pin, h - 1.0), (r_ch, h - 1.0), (r_ch, z_floor),
                       (0.0, z_floor)],
                      segments=96, mat=dark)
    bkit.recalc(body)

    # ---- plunger: stem + shoulder + nose, one solid -------------------
    z_shoulder = 20.0
    plunger = bkit.cylinder("Plunger", SPEC["plunger_stem_diameter"] / 2.0,
                            z_shoulder - 3.0, segments=48,
                            centre=(0.0, 0.0, (z_shoulder + 3.0) / 2.0), mat=steel)
    sh = bkit.cylinder("Shoulder", SPEC["plunger_shoulder_diameter"] / 2.0, 4.0,
                       segments=64, centre=(0.0, 0.0, z_shoulder), mat=steel)
    bkit.boolean(plunger, sh, "UNION")
    nose = bkit.cylinder("Nose", SPEC["plunger_nose_diameter"] / 2.0, 5.0,
                         segments=48, centre=(0.0, 0.0, z_shoulder + 4.5), mat=steel)
    bkit.boolean(plunger, nose, "UNION")
    bkit.recalc(plunger)

    # ---- spring: a real helix, exposed above the body ------------------
    spring = bkit.loft("Spring",
                       _coil(z_floor + 0.3, z_shoulder - 0.2,
                             SPEC["spring_coil_diameter"] / 2.0,
                             SPEC["spring_wire_diameter"] / 2.0,
                             SPEC["spring_turns"]),
                       closed_loop=True, cap_start=True, cap_end=True, mat=steel)
    bkit.recalc(spring)

    return dict(spec=SPEC, parts=3, spring_turns=SPEC["spring_turns"])


CHECKS = [
    dict(name="body_diameter", mm=12.0, tol=0.3, how="diameter", part="Body"),
    dict(name="plunger_length", mm=24.0, tol=0.4, how="bbox_z", part="Plunger"),
    dict(name="spring_outer_diameter", mm=9.8, tol=0.4, how="diameter", part="Spring"),
    dict(name="overall_height", mm=27.0, tol=0.4, how="bbox_z", part=None),
]
