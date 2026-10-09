"""
heater -- oil-filled convector room heater: enamelled steel cabinet lifted on
feet, a perforated inlet grille recessed into the lower front, louvred outlet
slots on top, and a thermostat knob.

400 x 200 x 600 mm is the common 2000 W convector format.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    body_width=400.0,       # X
    body_depth=200.0,       # Y
    body_height=580.0,      # cabinet only
    overall_height=604.0,   # on its feet, including the raised outlet louvres
    corner_radius=14.0,
    foot_height=20.0,
    grille_cols=19,
    grille_rows=2,
    grille_pitch_x=17.0,
    grille_pitch_y=18.0,
    grille_hole_diameter=7.0,
    outlet_slots=9,
    outlet_pitch=16.0,
    knob_diameter=44.0,
)

W = SPEC["body_width"]
D = SPEC["body_depth"]
H = SPEC["body_height"]
FOOT = SPEC["foot_height"]
R = SPEC["corner_radius"]
TOP = FOOT + H
FRONT = -(D / 2.0)                     # front face of the cabinet, y


def build():
    enamel = bkit.pbr("HeaterEnamel", base=(0.91, 0.91, 0.89),
                      metal=0.0, rough=0.24, coat=0.25)
    trim = bkit.preset("dark_metal")
    grille = bkit.preset("black_plastic")

    # ---- cabinet ----------------------------------------------------------
    body = bkit.rounded_box("HeaterCabinet", W, D, H, r=R, segments=6,
                            centre=(0.0, 0.0, FOOT + H / 2.0), mat=enamel)

    # ---- recessed inlet aperture -----------------------------------------
    # Cut the aperture FIRST, then put the perforated sheet inside it. A grille
    # laid on the surface of a solid surround is invisible: the surround hides
    # every hole.
    gz = FOOT + 82.0
    gw = (SPEC["grille_cols"] - 1) * SPEC["grille_pitch_x"] + 60.0
    gh = (SPEC["grille_rows"] - 1) * SPEC["grille_pitch_y"] + 60.0
    cut = bkit.rounded_box("_grille_cut", gw, 60.0, gh, r=8.0, segments=3,
                           centre=(0.0, FRONT + 10.0, gz))
    bkit.boolean(body, cut, "DIFFERENCE")
    bkit.recalc(body)
    bkit.health(body)

    # Dark backing plate closes the aperture so the holes read as a dark cavity
    # instead of a window into the (bright, enamelled) inside of the cabinet.
    bkit.rounded_box("GrilleBacking", gw - 6.0, 4.0, gh - 6.0, r=6.0, segments=2,
                     centre=(0.0, FRONT + 27.0, gz), mat=grille)

    # One mesh of real holes rather than 38 booleans: perforated_panel() builds
    # every hole wall in a single mesh, so this cannot fail the solver.
    front = bkit.perforated_panel(
        "InletGrille",
        cols=SPEC["grille_cols"], rows=SPEC["grille_rows"],
        pitch_x=SPEC["grille_pitch_x"], pitch_y=SPEC["grille_pitch_y"],
        hole_r=SPEC["grille_hole_diameter"] / 2.0,
        panel_sx=gw, panel_sy=gh, thickness=2.0, mat=grille)
    # perforated_panel() always builds in XY with its thickness along Z, so a
    # grille on a vertical face has to be rotated: +90 deg about X lays it flat
    # against -Y, the front.
    front.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    front.location = bkit.v(0.0, FRONT + 13.0, gz)
    bkit.recalc(front)

    # ---- outlet louvres on the top face -----------------------------------
    # The pitch comes from the real slot width plus the gap between slots, and
    # the row is centred, so it lands inside the 200 mm depth instead of
    # marching off the back of the cabinet.
    span = (SPEC["outlet_slots"] - 1) * SPEC["outlet_pitch"]
    assert span < D - 30.0, "outlet row must fit inside the cabinet depth"
    louvre = bkit.rounded_box("OutletLouvre", 250.0, 9.0, 5.0, r=2.0, segments=2,
                              centre=(0.0, -span / 2.0, TOP + 1.5), mat=grille)
    bkit.array_linear(louvre, SPEC["outlet_slots"],
                      (0.0, SPEC["outlet_pitch"], 0.0))

    # ---- thermostat knob --------------------------------------------------
    bkit.cylinder("ThermostatKnob", SPEC["knob_diameter"] / 2.0, 26.0, segments=48,
                  axis="Y",
                  centre=(-(W / 2.0) + 52.0, FRONT - 11.0, FOOT + 470.0), mat=trim)
    bkit.rounded_box("KnobPointer", 4.0, 10.0, 16.0, r=1.5, segments=2,
                     centre=(-(W / 2.0) + 52.0, FRONT - 19.0, FOOT + 482.0),
                     mat=bkit.preset("polished_metal"))

    # ---- feet -------------------------------------------------------------
    for ix, sx in ((0, -1.0), (1, 1.0)):
        for iy, sy in ((0, -1.0), (1, 1.0)):
            bkit.rounded_box("Foot_%d%d" % (ix, iy), 26.0, 26.0, FOOT, r=5.0,
                             segments=2,
                             centre=(sx * (W / 2.0 - 34.0),
                                     sy * (D / 2.0 - 30.0), FOOT / 2.0),
                             mat=bkit.preset("rubber"))

    # ---- rear cord outlet -------------------------------------------------
    bkit.rounded_box("CordOutlet", 42.0, 14.0, 30.0, r=4.0, segments=2,
                     centre=(W / 2.0 - 60.0, D / 2.0 + 2.0, FOOT + 40.0),
                     mat=trim)

    return dict(spec=SPEC, parts=11)


CHECKS = [
    dict(name="body_width", mm=400.0, tol=0.5, how="bbox_x", part="HeaterCabinet"),
    dict(name="body_depth", mm=200.0, tol=0.5, how="bbox_y", part="HeaterCabinet"),
    dict(name="body_height", mm=580.0, tol=0.5, how="bbox_z", part="HeaterCabinet"),
    dict(name="overall_height", mm=604.0, tol=0.5, how="bbox_z"),
    dict(name="knob_diameter", mm=44.0, tol=0.4, how="diameter",
         part="ThermostatKnob"),
]