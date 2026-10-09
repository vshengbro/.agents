"""
dinner_plate -- shallow ceramic plate with a raised rim and a foot ring.

A plate is the clearest test of lathe profiles: the whole shape is one closed
cross-section, and every error in it (a rim that thins to nothing, a foot that
floats, a wall that flares the wrong way) shows up immediately in the side view.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    diameter=270.0,
    height=24.0,
    rim_width=32.0,
    well_depth=15.0,
    wall=5.0,
    foot_diameter=110.0,
    foot_height=6.0,
)


def build():
    R = SPEC["diameter"] / 2.0
    H = SPEC["height"]
    W = SPEC["wall"]
    rw = SPEC["rim_width"]
    Rf = SPEC["foot_diameter"] / 2.0

    ceramic = bkit.preset("ceramic")
    glaze = bkit.pbr("PlateGlaze", base=(0.90, 0.90, 0.88), rough=0.10, coat=0.5)

    # Walk the cross-section: centre of the underside, out to the rim, over the
    # rim edge, back along the well, across the well floor. Every coordinate is
    # derived from the spec so the wall thickness is real all the way round.
    prof = [
        (0.0, 0.0),
        (Rf - 6.0, 0.0),
        (Rf, 1.2),                         # outer edge of the foot ring
        (Rf, SPEC["foot_height"]),         # foot wall
        (Rf + 8.0, SPEC["foot_height"]),   # step out of the foot
        (Rf + 10.0, 2.0),
        (R - rw * 0.55, 3.4),              # underside sweeping out
        (R - 4.0, H * 0.72),
        (R, H - 3.0),                      # outer wall
        (R, H),                            # rim edge, outer
        (R - rw, H),                       # across the rim
        (R - rw, H - 3.0),                 # inner rim wall
        (R - rw - 9.0, SPEC["well_depth"]),# well slope
        (0.0, SPEC["well_depth"] + W),     # well floor
    ]
    plate = bkit.lathe("Plate", prof, segments=128, mat=ceramic)

    # Glaze the eating surface only; the foot ring stays unglazed matte ceramic,
    # which is exactly how a real plate is finished and it stops the underside
    # reading as one flat tone.
    bkit.assign_faces_by(
        plate, glaze,
        lambda c, n: (c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM < (R - rw)
        and c.z / bkit.MM > SPEC["well_depth"] - 1.0,
    )
    return dict(spec=SPEC, parts=1)

CHECKS = [
    dict(name="diameter", mm=270.0, tol=0.4, how="diameter", part="Plate"),
    dict(name="height", mm=24.0, tol=0.4, how="bbox_z", part="Plate"),
    dict(name="longest", mm=270.0, tol=0.4, how="longest"),
]
