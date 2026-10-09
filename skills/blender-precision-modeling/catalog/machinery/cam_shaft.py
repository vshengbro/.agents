"""
cam_shaft -- 4-lobe overhead camshaft on five journals, with a timing sprocket.

Counting is the whole job here. Four lobes on four equally spaced journals, and
the sprocket teeth on top, so a viewer counting either feature gets the right
answer. Each lobe is a real cam profile -- base circle plus a smooth lift raised
to 1.5 so the flank has an inflection, not a sinusoid -- phased 90 deg from its
neighbour, which is what makes the lobes read as a camshaft and not as four
identical donuts.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    lobes=4,
    journals=5,
    shaft_diameter=22.0,
    journal_diameter=30.0,
    lobe_base_diameter=28.0,
    lobe_nose_diameter=44.0,
    lobe_width=16.0,
    journal_length=20.0,
    lobe_phase_deg=90.0,
    timing_sprocket_teeth=12,
    timing_sprocket_module=3.0,
    overall_length=156.0,
    lobe_envelope=44.0,
)

LOBE_POINTS = 72


def _lobe_section(x, phase_deg, r_base, r_nose):
    """One lobe cross-section in the YZ plane: r(psi) = base + lift * ramp."""
    lift = r_nose - r_base
    pts = []
    for k in range(LOBE_POINTS):
        psi = 2.0 * math.pi * k / LOBE_POINTS + math.radians(phase_deg)
        ramp = (0.5 + 0.5 * math.cos(psi - math.radians(phase_deg))) ** 1.5
        r = r_base + lift * ramp
        pts.append((x, r * math.cos(psi), r * math.sin(psi)))
    return pts


def build():
    r_shaft = SPEC["shaft_diameter"] / 2.0
    r_journal = SPEC["journal_diameter"] / 2.0
    r_base = SPEC["lobe_base_diameter"] / 2.0
    r_nose = SPEC["lobe_nose_diameter"] / 2.0
    w = SPEC["lobe_width"]

    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)

    # ---- axial layout, overlapped ---------------------------------------
    widths = []
    for i in range(2 * SPEC["lobes"] + 1):
        widths.append(SPEC["journal_length"] if i % 2 == 0 else w)
    slots = bkit.lay_out(widths, gap=-2.0)
    x_journal = [slots[i][0] for i in range(0, len(slots), 2)]
    x_lobe = [slots[i][0] for i in range(1, len(slots), 2)]
    total = sum(widths) + (-2.0) * (len(widths) - 1)

    shaft = bkit.cylinder("Shaft", r_shaft, total, segments=64, axis="X", mat=steel)
    for i, x in enumerate(x_journal):
        j = bkit.cylinder("Journal%d" % (i + 1), r_journal,
                          SPEC["journal_length"], segments=64, axis="X",
                          centre=(x, 0.0, 0.0), mat=steel)
        bkit.boolean(shaft, j, "UNION")

    # ---- lobes, phased 90 deg apart ------------------------------------
    for i, x in enumerate(x_lobe):
        phase = i * SPEC["lobe_phase_deg"]
        a = _lobe_section(x - w / 2.0, phase, r_base, r_nose)
        b = _lobe_section(x + w / 2.0, phase, r_base, r_nose)
        lobe = bkit.loft("Lobe%d" % (i + 1), [a, b], closed_loop=True,
                         cap_start=True, cap_end=True, mat=dark)
        bkit.recalc(lobe)
        bkit.weld(lobe)
        bkit.boolean(shaft, lobe, "UNION")

    # ---- timing sprocket on the front end ------------------------------
    spr = bkit.gear("TimingSprocket", teeth=SPEC["timing_sprocket_teeth"],
                    module_mm=SPEC["timing_sprocket_module"], thickness=10.0,
                    bore_r=0.0, mat=dark)
    bkit.place(spr, (x_journal[0] - SPEC["journal_length"] / 2.0 - 2.0, 0.0, 0.0), "X")
    bkit.boolean(shaft, spr, "UNION")

    # ---- rear flange ----------------------------------------------------
    fl = bkit.cylinder("RearFlange", 18.0, 8.0, segments=64, axis="X",
                       centre=(x_journal[-1] + SPEC["journal_length"] / 2.0 - 3.0,
                               0.0, 0.0), mat=steel)
    bkit.boolean(shaft, fl, "UNION")

    bkit.recalc(shaft)
    shaft.name = "CamShaft"
    # Lay the shaft along Y so the studio's side elevation (az=2, i.e. almost
    # straight down +X) shows the lobe count instead of the end of the shaft.
    # Composed in world space: the object still carries place()'s axis="X"
    # rotation, so rotation_euler cannot simply be overwritten.
    bkit.move(shaft, 0.0, 0.0, 0.0)          # flush the cached matrix_world
    shaft.matrix_world = (bkit.Matrix.Rotation(math.radians(90.0), 4, "Z")
                          @ shaft.matrix_world)
    return dict(spec=SPEC, parts=1, lobes=SPEC["lobes"],
                journals=SPEC["journals"])


CHECKS = [
    dict(name="overall_length", mm=156.0, tol=0.8, how="bbox_y", part="CamShaft"),
    dict(name="lobe_envelope", mm=44.0, tol=0.6, how="bbox_x", part="CamShaft"),
    dict(name="lobe_envelope_z", mm=44.0, tol=0.6, how="bbox_z", part="CamShaft"),
]
