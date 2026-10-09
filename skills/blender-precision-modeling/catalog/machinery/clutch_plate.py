"""
clutch_plate -- 200 mm friction disc: friction band, six damper windows, hub,
twelve rivets.

A clutch disc is a plate that has to be light in the middle and strong at the
rim, so the geometry is graded: full thickness at the friction band, six
damper windows cut on a 60 deg pitch at 72 mm radius, a splined hub, and 12
rivets on a single circle. The rivets are one joined object of 12 separate
shells, each watertight on its own -- that is cheaper and more robust than 12
EXACT booleans and looks identical.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    outside_diameter=200.0,
    friction_band_thickness=4.0,
    window_count=6,
    window_pitch_deg=60.0,
    window_radius=72.0,
    window_radial=14.0,
    window_tangential=30.0,
    hub_diameter=60.0,
    hub_length=28.0,
    bore_diameter=44.0,
    rivet_count=12,
    rivet_diameter=8.0,
    rivet_circle_diameter=180.0,
    overall_thickness=28.0,
)


def build():
    r_out = SPEC["outside_diameter"] / 2.0
    t = SPEC["friction_band_thickness"] / 2.0

    steel = bkit.pbr("machined_steel", base=(0.66, 0.67, 0.70), metal=0.55, rough=0.30)
    dark = bkit.pbr("cast_iron", base=(0.34, 0.35, 0.37), metal=0.40, rough=0.48)
    hz = SPEC["hub_length"] / 2.0
    r_hub = SPEC["hub_diameter"] / 2.0

    # ---- plate AND hub in one revolved profile -------------------------
    # The hub boss is written into the section instead of unioned on. A union
    # of a hub cylinder with the plate followed by a bore cut was the only
    # sequence EXACT could not keep manifold here; as part of the profile the
    # whole disc is one surface of revolution and the boolean count drops to
    # the six windows, the bore and the spline.
    plate = bkit.lathe("ClutchPlate",
                       [(0.0, -hz), (r_hub, -hz), (r_hub, -t), (r_out, -t),
                        (r_out, t), (r_hub, t), (r_hub, hz), (0.0, hz)],
                       segments=144, mat=steel)
    bkit.recalc(plate)

    # ---- damper windows, on a computed 60 deg pitch ---------------------
    win = bkit.rounded_box("Window", SPEC["window_radial"], SPEC["window_tangential"],
                           t * 4.0, r=4.0, segments=2,
                           centre=(SPEC["window_radius"], 0.0, 0.0), mat=None)
    for k in range(1, SPEC["window_count"]):
        cp = bkit.duplicate(win, "Window%d" % k,
                            rot_deg=(0.0, 0.0, k * SPEC["window_pitch_deg"]))
        bkit.boolean(plate, cp, "DIFFERENCE")
    bkit.boolean(plate, win, "DIFFERENCE")

    # ---- bore, at a different segment count from the lathe, then spline --
    bore = bkit.cylinder("Bore", SPEC["bore_diameter"] / 2.0,
                         SPEC["hub_length"] * 2.0, segments=96)
    bkit.boolean(plate, bore, "DIFFERENCE")
    spline = bkit.box("Spline", 5.0, 5.0, SPEC["hub_length"] * 2.0,
                      centre=(SPEC["bore_diameter"] / 2.0 - 2.0, 0.0, 0.0))
    bkit.boolean(plate, spline, "DIFFERENCE")
    bkit.recalc(plate)

    # ---- rivets: 12 separate shells, joined, evenly on one circle ------
    r_rivet = SPEC["rivet_circle_diameter"] / 2.0
    rivets = []
    for k in range(SPEC["rivet_count"]):
        a = 2.0 * math.pi * k / SPEC["rivet_count"]
        rivets.append(bkit.cylinder(
            "Rivet%02d" % (k + 1), SPEC["rivet_diameter"] / 2.0,
            SPEC["friction_band_thickness"] * 2.0, segments=24,
            centre=(r_rivet * math.cos(a), r_rivet * math.sin(a), 0.0), mat=dark))
    joined = bkit.join(rivets, name="Rivets")

    return dict(spec=SPEC, parts=2, rivets=SPEC["rivet_count"])


CHECKS = [
    dict(name="outside_diameter", mm=200.0, tol=0.6, how="diameter", part="ClutchPlate"),
    dict(name="overall_thickness", mm=28.0, tol=0.4, how="bbox_z", part="ClutchPlate"),
    dict(name="outside_diameter_y", mm=200.0, tol=0.6, how="bbox_y", part="ClutchPlate"),
]
