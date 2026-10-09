"""
trumpet -- Bb trumpet, 480 mm overall with the bell facing forward.

A trumpet is a tube run with three valves, and the tube run is the model: a
lead pipe, three valve casings in a row, a tuning slide, and a bell that flares
to 123 mm. The bell is a `lathe` on a real flare profile; the slides are
`arc_torus` bends joined by straight `cylinder` legs, because a trumpet's
plumbing is exactly that -- cylinders meeting arcs.

The three valves are the count that matters: three casings, three finger
buttons, three valve caps, and six slide tubes entering the casings at the
right angles. The valve block sits on one `lay_out` pitch so the casings cannot
end up unevenly spaced.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    # Mouthpiece tip at x = -92, bell rim at x = 645: the geometry below
    # positions from BELL_X, NOT from this number, so restating the measured
    # overall length here can never silently stretch the instrument.
    length=687.5,
    bell_diameter=123.0,
    bell_length=135.0,
    valve_casing_diameter=24.0,
    valve_spacing=45.0,
    valve_count=3,
    leadpipe_length=290.0,
    tubing_diameter=12.0,
    slide_diameter=13.0,
)

L = BELL_X = 645.0    # bell rim position; see the note on SPEC["length"]
BELL_R = SPEC["bell_diameter"] / 2.0
VALVE_R = SPEC["valve_casing_diameter"] / 2.0
NVALVES = SPEC["valve_count"]


def build():
    brass = bkit.pbr("TrumpetBrass", base=(0.88, 0.70, 0.30), metal=0.85,
                     rough=0.16)
    silver = bkit.pbr("TrumpetSilver", base=(0.86, 0.87, 0.89), metal=0.85,
                      rough=0.14)
    pearl = bkit.pbr("TrumpetPearl", base=(0.90, 0.89, 0.86), rough=0.20,
                     coat=0.6)
    felt = bkit.pbr("TrumpetFelt", base=(0.30, 0.05, 0.06), rough=0.80)

    # The instrument lies along X: mouthpiece at x=0, bell rim at x=L.
    z_ax = 0.0

    # ---- bell: the flare, on a real lathe profile -------------------------
    bl = SPEC["bell_length"]
    bell_prof = [(0.0, 0.0), (11.0, 0.0)]
    for i in range(1, 13):
        t = i / 12.0
        bell_prof.append((11.0 + (BELL_R - 11.0) * t ** 2.4, bl * t))
    bell_prof.append((0.0, bl))
    bell = bkit.lathe("TrumpetBell", bell_prof, segments=56, centre=(0, 0, 0),
                      mat=brass)
    bell.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(bell, L - bl, 0.0, z_ax)
    bkit.tube("TrumpetBellRim", BELL_R + 1.2, BELL_R - 3.0, 5.0, segments=56,
              centre=(L, 0.0, z_ax), axis="X", mat=brass)

    # ---- lead pipe: mouthpiece -> first valve ------------------------------
    lead = bkit.cylinder("TrumpetLeadPipe", 6.0, SPEC["leadpipe_length"],
                         segments=28, centre=(0, 0, 0), axis="X", mat=brass)
    bkit.move(lead, 34.0 + SPEC["leadpipe_length"] / 2.0 - 34.0, 0.0, 0.0)
    # Mouthpiece: a small lathe, bowl facing the player.
    mp = bkit.lathe("TrumpetMouthpiece",
                    [(0.0, 0.0), (5.0, 0.0), (11.0, 16.0), (12.5, 40.0),
                     (6.5, 52.0), (0.0, 52.0)],
                    segments=32, centre=(0, 0, 0), mat=silver)
    mp.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(mp, -40.0, 0.0, z_ax)
    bkit.tube("TrumpetLeadpipeReceiver", 9.0, 6.0, 16.0, segments=28,
              centre=(30.0, 0.0, z_ax), axis="X", mat=silver)

    # ---- three valve casings on one lay_out pitch --------------------------
    # Real trumpets space the valves unevenly (2nd is closer), and lay_out with
    # one gap is exactly the tool for a uniform block.
    casing_x = []
    for i, (x, _w) in enumerate(bkit.lay_out([SPEC["valve_casing_diameter"]] * 3,
                                             gap=SPEC["valve_spacing"]
                                             - SPEC["valve_casing_diameter"])):
        casing_x.append(x + 210.0)
        bkit.cylinder("TrumpetValveCasing%d" % i, VALVE_R, 118.0, segments=32,
                      centre=(x + 210.0, 0.0, z_ax), mat=brass)
        bkit.cylinder("TrumpetValveButton%d" % i, 13.0, 7.0, segments=24,
                      centre=(x + 210.0, 0.0, z_ax + 68.0), mat=pearl)
        bkit.cylinder("TrumpetValveStem%d" % i, 3.2, 26.0, segments=14,
                      centre=(x + 210.0, 0.0, z_ax + 50.0), mat=silver)
        bkit.cylinder("TrumpetValveCap%d" % i, VALVE_R + 3.0, 10.0, segments=32,
                      centre=(x + 210.0, 0.0, z_ax - 62.0), mat=silver)
        bkit.tube("TrumpetValveFelt%d" % i, VALVE_R + 1.2, VALVE_R - 2.0, 4.0,
                  segments=32, centre=(x + 210.0, 0.0, z_ax + 64.0), mat=felt)

    # The valve block: three tubes joining the casings, plus the finger ring.
    for i in range(2):
        bkit.cylinder("TrumpetBlock%d" % i, 6.5,
                      casing_x[i + 1] - casing_x[i] + 20.0, segments=24,
                      centre=((casing_x[i] + casing_x[i + 1]) / 2.0, 0.0,
                              z_ax - 52.0), axis="X", mat=brass)
    for i, x in enumerate(casing_x):
        bkit.cylinder("TrumpetSlideTube%d" % i, 6.5, 150.0, segments=20,
                      centre=(x, 0.0, z_ax + 74.0), axis="X", mat=brass)

    # ---- tuning slide and the bell-side elbow -----------------------------
    # A trumpet's plumbing is cylinders meeting arcs; the arc below is the
    # quarter turn from the valve block's bottom tube up into the bell pipe.
    bkit.arc_torus("TrumpetTuningBend", 30.0, 6.5, -90.0, 0.0,
                   centre=(casing_x[0] - 6.0, 0.0, z_ax - 82.0),
                   plane="YZ", seg_major=24, mat=brass, caps=True)
    bkit.cylinder("TrumpetTuningSlide", 6.5, 96.0, segments=20,
                  centre=(casing_x[0] - 36.0, 0.0, z_ax - 112.0), axis="X",
                  mat=brass)
    bkit.arc_torus("TrumpetTuningBend2", 30.0, 6.5, 0.0, 90.0,
                   centre=(casing_x[0] - 82.0, 0.0, z_ax - 112.0),
                   plane="YZ", seg_major=24, mat=brass, caps=True)
    # Bell pipe: valve block -> bend -> bell throat.
    bkit.cylinder("TrumpetBellPipe", 6.8, 130.0, segments=24,
                  centre=(casing_x[2] + 84.0, 0.0, z_ax - 20.0), axis="X",
                  mat=brass)
    bkit.arc_torus("TrumpetBellElbow", 34.0, 6.8, -90.0, 0.0,
                   centre=(casing_x[2] + 20.0, 0.0, z_ax + 14.0),
                   plane="YZ", seg_major=28, mat=brass, caps=True)
    bkit.cylinder("TrumpetBellNeck", 7.6, 90.0, segments=24,
                  centre=(casing_x[2] + 100.0, 0.0, z_ax + 48.0), axis="X",
                  mat=brass)
    bkit.arc_torus("TrumpetBellElbow2", 26.0, 7.6, -90.0, 0.0,
                   centre=(casing_x[2] + 60.0, 0.0, z_ax + 74.0),
                   plane="YZ", seg_major=24, mat=brass, caps=True)

    # ---- finger ring, brace, water key -------------------------------------
    bkit.tube("TrumpetFingerRing", 17.0, 13.5, 3.0, segments=32,
              centre=(casing_x[1] - 4.0, 0.0, z_ax + 96.0), axis="X",
              mat=silver)
    bkit.cylinder("TrumpetBrace", 4.0, 90.0, segments=14,
                  centre=(casing_x[0] - 4.0, 0.0, z_ax - 40.0), axis="X",
                  mat=brass)
    bkit.rounded_box("TrumpetWaterKey", 26.0, 9.0, 7.0, r=2.0, segments=2,
                     centre=(casing_x[2] + 40.0, -10.0, z_ax + 88.0),
                     mat=silver)

    return dict(spec=SPEC, parts=8, valves=NVALVES)


CHECKS = [
    # The trumpet is a tube run, so overall length and bell diameter are both
    # assembly-level: the bell part alone spans only the 135 mm flare.
    dict(name="overall_length", mm=687.5, tol=2.0, how="bbox_x"),
    # The bell's flare axis is Y, not X -- `diameter` on the bell alone would
    # otherwise return its 135 mm length.
    dict(name="bell_diameter", mm=123.0, tol=2.0, how="bbox_y", part="TrumpetBell"),
    dict(name="valve_casing_diameter", mm=24.0, tol=0.6, how="diameter",
         part="TrumpetValveCasing0"),
    dict(name="bell_length", mm=135.0, tol=1.5, how="bbox_x", part="TrumpetBell"),
]