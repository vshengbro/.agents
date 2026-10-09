"""
staircase -- a straight 13-tread timber flight: treads and risers swept from a
computed pitch, two stringers, a handrail on balusters, and a newel post.

Large size class (600..3000 mm). The pitch is the contract: 190 mm rise /
280 mm going is the building-regulation stair, and a 13-step flight of it is
1.86 x 2.47 m. The treads are ONE array, not thirteen boxes.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    steps=13,
    rise=190.0,            # building regs: 175..210 mm
    going=280.0,           # building regs: 250..300 mm
    width=1100.0,
    tread_thickness=45.0,
    stringer_width=60.0,
    stringer_depth=320.0,
    handrail_height=900.0,
    handrail_radius=28.0,
    newel_height=1050.0,
    baluster_spacing=140.0,
)

N = SPEC["steps"]
RISE = SPEC["rise"]
GO = SPEC["going"]
W = SPEC["width"]

RISE_TOTAL = N * RISE
GO_TOTAL = N * GO


def build():
    timber = bkit.pbr("StairTread", base=(0.46, 0.32, 0.18), rough=0.52)
    stringer_mat = bkit.pbr("StairStringer", base=(0.38, 0.25, 0.14), rough=0.60)
    rail_mat = bkit.pbr("StairRail", base=(0.52, 0.36, 0.20), rough=0.44)

    # ---- treads: one swept array, offset by the going -------------------
    # Seeded on the first tread at the foot of the flight and swept upward and
    # back by (going, rise) per step, so the count and the pitch cannot
    # disagree.
    tread = bkit.rounded_box("StairTreads", GO + 32.0, W,
                             SPEC["tread_thickness"], r=8.0, segments=2,
                             centre=(GO / 2.0, 0.0,
                                     RISE - SPEC["tread_thickness"] / 2.0),
                             mat=timber)
    bkit.array_linear(tread, N, (GO, 0.0, RISE), apply=True)

    # ---- risers: a closed panel between each pair of treads -------------
    riser = bkit.rounded_box("StairRisers", 26.0, W - 20.0, RISE, r=4.0,
                             segments=1, centre=(0.0, 0.0, RISE / 2.0),
                             mat=timber)
    bkit.array_linear(riser, N, (GO, 0.0, RISE), apply=True)

    # ---- stringers: two, raking at the pitch angle ---------------------
    sd = SPEC["stringer_depth"]
    sw = SPEC["stringer_width"]
    angle = math.atan2(RISE, GO)
    run = math.hypot(GO_TOTAL, RISE_TOTAL)
    for sy, tag in ((-1, "L"), (1, "R")):
        st = bkit.rounded_box("StairStringer%s" % tag, run, sw, sd, r=10.0,
                              segments=2,
                              centre=(GO_TOTAL / 2.0,
                                      sy * (W / 2.0 + sw / 2.0),
                                      RISE_TOTAL / 2.0 - sd / 2.0 + 40.0),
                              mat=stringer_mat)
        st.rotation_euler = (0.0, -angle, 0.0)
        bpy_update()

    # ---- handrail + balusters, on a computed spacing -------------------
    rh = SPEC["handrail_height"]
    rail = bkit.rounded_box("StairHandrail", run + 240.0, 90.0,
                            SPEC["handrail_radius"] * 2.0, r=16.0, segments=2,
                            centre=(GO_TOTAL / 2.0 - 120.0, 0.0,
                                    RISE_TOTAL / 2.0 + rh + 40.0),
                            mat=rail_mat)
    rail.rotation_euler = (0.0, -angle, 0.0)
    bpy_update()

    nb = max(2, int(run / SPEC["baluster_spacing"]))
    for i in range(nb + 1):
        f = i / float(nb)
        x = GO_TOTAL * f
        z = RISE_TOTAL * f + rh - rh * 0.5
        bkit.rounded_box("Baluster%d" % i, 44.0, 44.0, rh, r=12.0, segments=2,
                         centre=(x, W / 2.0 - 60.0, z), mat=rail_mat)

    # ---- newel post at the foot ----------------------------------------
    bkit.rounded_box("StairNewel", 150.0, 150.0, SPEC["newel_height"],
                     r=18.0, segments=3,
                     centre=(-90.0, W / 2.0 - 60.0,
                             SPEC["newel_height"] / 2.0), mat=rail_mat)

    return dict(spec=SPEC, parts=4 + nb, steps=N, balusters=nb + 1)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()


CHECKS = [
    dict(name="total_rise", mm=2470.0, tol=8.0, how="bbox_z", part="StairRisers"),
    dict(name="width", mm=1100.0, tol=8.0, how="bbox_y", part="StairTreads"),
    dict(name="newel_height", mm=1050.0, tol=6.0, how="bbox_z", part="StairNewel"),
    dict(name="tread_run", mm=3672.0, tol=20.0, how="bbox_x", part="StairTreads"),
]
