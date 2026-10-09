"""
speaker -- 190 x 180 x 306 mm two-way bookshelf monitor on a bass reflex port.

Three things carry this object and all three are counted rather than implied:

* a real perforated grille -- 14 x 22 = 308 holes at a 9 mm pitch, cut as a
  single `perforated_panel` mesh and stood in a 6 mm baffle recess. Only the
  two driver apertures are cut out of it, so the grille stays a plausible
  part instead of a decorative stripe;
* two drivers, each a lathed cone-plus-flange profile, with bores behind them
  so the cone is genuinely recessed rather than buried in the cabinet;
* a flared bass port, bored with `bkit.bore` so the cutter's segment count is
  deliberately not the host's.

`perforated_panel` ignores its `panel_sx/panel_sy` arguments -- the sheet is
exactly the hole field -- so the real size is `(cols-1)*pitch + 2*hole_r` and
the cols/rows here are solved backwards from the baffle instead.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=190.0,
    depth=180.0,
    height=306.0,
    grille_cols=14,
    grille_rows=22,
    grille_pitch=9.0,
    grille_hole_r=2.5,
    woofer_diameter=92.0,
    tweeter_diameter=40.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]
GC, GR = SPEC["grille_cols"], SPEC["grille_rows"]
GP, GHR = SPEC["grille_pitch"], SPEC["grille_hole_r"]
FRONT = D / 2.0

# The grille is the hole field, so its true size is derived, not declared.
GRILLE_W = (GC - 1) * GP + 2 * GHR
GRILLE_H = (GR - 1) * GP + 2 * GHR
GRILLE_Z = 158.0
GRILLE_Y = 85.2

WOOFER_Z, TWEETER_Z, PORT_Z = 110.0, 205.0, 35.0


def _driver(name, r_flange, r_cone, depth, mat_rim, mat_cone):
    """Cone + flange as one lathe, then swung to face +Y and positioned.

    Rotated -90 degrees about X so the lathe's +Z axis becomes world +Y:
    `place(obj, ..., "Y")` would point it backwards, and a driver that faces
    the cabinet interior is a driver you cannot see. The cone material is
    chosen while the lathe is still axis-aligned, so the predicate reads
    local z -- a lathe is rotationally symmetric about Z, so `c.y` is zero on
    every face and would select nothing.
    """
    prof = [(0.0, 0.0), (r_cone, -depth), (r_cone + 4.0, -depth),
            (r_flange - 8.0, 2.0), (r_flange, 2.0), (r_flange, 5.0),
            (0.0, 5.0)]
    ob = bkit.lathe(name, prof, segments=64, mat=mat_rim)
    bkit.assign_faces_by(ob, mat_cone,
                         lambda c, n: c.z / bkit.MM < -depth * 0.35)
    ob.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    return ob


def build():
    veneer = bkit.pbr("SpeakerVeneer", base=(0.30, 0.24, 0.17), rough=0.52)
    baffle = bkit.pbr("SpeakerBaffle", base=(0.14, 0.14, 0.16), rough=0.44)
    rim = bkit.pbr("SpeakerRim", base=(0.62, 0.63, 0.66), metal=0.45,
                   rough=0.28)
    cone = bkit.pbr("SpeakerCone", base=(0.38, 0.38, 0.42), rough=0.60)
    mesh = bkit.preset("dark_metal")
    cavity = bkit.pbr("SpeakerCavity", base=(0.06, 0.06, 0.07), rough=0.80)
    foot = bkit.preset("rubber")

    cab = bkit.rounded_box("SpeakerCabinet", W, D, 300.0, r=6.0, segments=4,
                           centre=(0, 0, 156.0), mat=veneer)

    # ---- 6 mm baffle recess, one cut for the whole grille aperture -------
    bkit.boolean(cab, bkit.rounded_box(
        "_recess", GRILLE_W + 8.0, 8.0, GRILLE_H + 8.0, r=3.0, segments=3,
        centre=(0, FRONT - 2.0, GRILLE_Z)), "DIFFERENCE")

    # ---- perforated grille, with only the two driver apertures removed ---
    grille = bkit.perforated_panel("SpeakerGrille", cols=GC, rows=GR,
                                   pitch_x=GP, pitch_y=GP, hole_r=GHR,
                                   panel_sx=GRILLE_W, panel_sy=GRILLE_H,
                                   thickness=2.0, mat=mesh)
    # Bores go in while the panel is still flat in XY, so the driver centre is
    # expressed in panel-local y. Standing the panel up rotates local +y onto
    # world -z, hence the sign: the grid is symmetric, the drivers are not.
    for (z, r) in ((WOOFER_Z, 40.0), (TWEETER_Z, 16.0)):
        bkit.bore(grille, radius=r, depth=8.0,
                  centre=(0.0, GRILLE_Z - z, 0.0), host_segments=64)
    # Stand the panel up: perforated_panel builds it flat in XY.
    grille.rotation_euler = (math.radians(-90.0), 0.0, 0.0)
    bkit.move(grille, 0.0, GRILLE_Y, GRILLE_Z)

    # ---- woofer: bore, then the lathed cone-and-flange driver -----------
    bkit.bore(cab, radius=40.0, depth=30.0, centre=(0, FRONT - 4.0, WOOFER_Z),
              host_segments=64)
    woofer = _driver("SpeakerWoofer", 46.0, 30.0, 12.0, rim, cone)
    bkit.move(woofer, 0.0, FRONT - 2.0, WOOFER_Z)

    # ---- tweeter: a shallow dome, so it needs no bore at all -------------
    tw = _driver("SpeakerTweeter", 20.0, 9.0, 3.0, rim, cone)
    bkit.move(tw, 0.0, FRONT - 1.0, TWEETER_Z)

    # ---- flared bass reflex port ----------------------------------------
    bkit.bore(cab, radius=20.0, depth=70.0, centre=(0, FRONT - 20.0, PORT_Z),
              host_segments=64)
    bkit.tube("SpeakerPort", r_out=26.0, r_in=20.0, height=5.0, segments=48,
              axis="Y", centre=(0, FRONT + 1.5, PORT_Z), mat=cavity)

    # ---- four feet, on one computed grid --------------------------------
    feet = []
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=2,
                                                   pitch_x=W - 40.0,
                                                   pitch_y=D - 40.0)):
        feet.append(bkit.cylinder("_f%d" % i, 11.0, 6.0, segments=28,
                                  centre=(x, y, 3.0), mat=foot))
    bkit.join(feet, name="SpeakerFeet")

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="width", mm=190.0, tol=0.8, how="bbox_x", part="SpeakerCabinet"),
    dict(name="depth", mm=180.0, tol=0.8, how="bbox_y", part="SpeakerCabinet"),
    dict(name="overall_height", mm=306.0, tol=0.8, how="bbox_z"),
]
