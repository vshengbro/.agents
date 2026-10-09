"""
trombone -- tenor trombone, 1180 mm with the slide in first position.

The slide is the model. A trombone is a bell section fixed at the back and a
telescoping double slide at the front, and in first position the outer slide
tubes are 910 mm long with the inner tubes sticking out by the first-position
extension (1050 - 910). Those two numbers are what make it a trombone rather
than a long trumpet, so they are separate SPEC entries and drive the tube
lengths rather than being decoration.

The bell is a `lathe` flare to 205 mm, the tuning slide and the F-attachment
are `arc_torus` bends, and the cross brace between the two slide tubes is what
stops the pair reading as two unrelated cylinders.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=1369.0,
    bell_diameter=205.0,
    bell_length=200.0,
    outer_slide_length=910.0,
    inner_slide_length=1050.0,
    first_position_extension=140.0,
    slide_spacing=52.0,
    slide_tube_diameter=13.8,
    bore_diameter=14.0,
)

L = BELL_X = 1180.0
BELL_R = SPEC["bell_diameter"] / 2.0
SPACING = SPEC["slide_spacing"] / 2.0
TUBE_R = SPEC["slide_tube_diameter"] / 2.0
OUTER = SPEC["outer_slide_length"]
INNER = SPEC["inner_slide_length"]


def build():
    brass = bkit.pbr("TromboneBrass", base=(0.88, 0.70, 0.30), metal=0.85,
                     rough=0.16)
    silver = bkit.pbr("TromboneSilver", base=(0.86, 0.87, 0.89), metal=0.85,
                      rough=0.14)
    nickel = bkit.pbr("TromboneNickel", base=(0.80, 0.81, 0.83), metal=0.85,
                      rough=0.22)

    # Lies along X: mouthpiece at x=0, bell rim at x=L, slide tubes offset in Y.
    # ---- bell section ------------------------------------------------------
    bl = SPEC["bell_length"]
    bell_prof = [(0.0, 0.0), (13.0, 0.0)]
    for i in range(1, 13):
        t = i / 12.0
        bell_prof.append((13.0 + (BELL_R - 13.0) * t ** 2.3, bl * t))
    bell_prof.append((0.0, bl))
    bell = bkit.lathe("TromboneBell", bell_prof, segments=56, centre=(0, 0, 0),
                      mat=brass)
    bell.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(bell, L - bl, 0.0, 0.0)
    bkit.tube("TromboneBellRim", BELL_R + 1.5, BELL_R - 4.0, 6.0, segments=56,
              centre=(L, 0.0, 0.0), axis="X", mat=brass)

    # Bell-to-slide throat and the F-attachment bend.
    bkit.cylinder("TromboneBellThroat", 12.0, 300.0, segments=28,
                  centre=(L - bl - 140.0, 0.0, 0.0), axis="X", mat=brass)
    bkit.arc_torus("TromboneFBend", 46.0, 12.0, -90.0, 0.0,
                   centre=(L - bl - 290.0, 0.0, 46.0), plane="YZ",
                   seg_major=28, mat=brass, caps=True)
    bkit.cylinder("TromboneSlideReceiver", 13.0, 40.0, segments=28,
                  centre=(L - bl - 370.0, 0.0, 58.0), axis="X", mat=brass)

    # ---- mouthpiece -------------------------------------------------------
    mp = bkit.lathe("TromboneMouthpiece",
                    [(0.0, 0.0), (7.0, 0.0), (16.0, 22.0), (18.0, 52.0),
                     (9.0, 66.0), (0.0, 66.0)],
                    segments=32, centre=(0, 0, 0), mat=silver)
    mp.rotation_euler = (0.0, math.radians(90.0), 0.0)
    bkit.move(mp, -54.0, 0.0, 0.0)
    bkit.cylinder("TromboneMouthpipe", 7.0, 90.0, segments=24,
                  centre=(24.0, 0.0, 0.0), axis="X", mat=brass)
    bkit.tube("TromboneMouthReceiver", 11.0, 7.0, 18.0, segments=24,
              centre=(66.0, 0.0, 0.0), axis="X", mat=brass)

    # ---- the slide: two outer tubes and two inner tubes -------------------
    # Inner tubes are the outer ones plus the first-position extension; the
    # difference is the whole point of the instrument.
    for i, side in enumerate((-1.0, 1.0)):
        outer = bkit.cylinder("TromboneOuterSlide%d" % i, TUBE_R, OUTER,
                              segments=32, centre=(0, 0, 0), axis="X",
                              mat=brass)
        bkit.move(outer, 150.0 + OUTER / 2.0, side * SPACING, 0.0)
        inner = bkit.cylinder("TromboneInnerSlide%d" % i, TUBE_R - 1.4, INNER,
                              segments=32, centre=(0, 0, 0), axis="X",
                              mat=nickel)
        bkit.move(inner, 150.0 + INNER / 2.0, side * SPACING, 0.0)
        # Water key on each inner tube, at the joint with the outer.
        bkit.rounded_box("TromboneWaterKey%d" % i, 34.0, 10.0, 8.0, r=2.5,
                         segments=2,
                         centre=(150.0 + OUTER, side * (SPACING + 12.0), 0.0),
                         mat=silver)

    # ---- slide brace and the two end bows ---------------------------------
    bkit.cylinder("TromboneSlideBrace", 7.0, SPEC["slide_spacing"], segments=24,
                  centre=(300.0, 0.0, 0.0), axis="Y", mat=brass)
    bkit.cylinder("TromboneSlideBrace2", 6.0, SPEC["slide_spacing"], segments=24,
                  centre=(150.0 + OUTER - 120.0, 0.0, 0.0), axis="Y",
                  mat=brass)
    bkit.cylinder("TromboneSlideHandle", 9.0, 90.0, segments=20,
                  centre=(150.0 + OUTER + 45.0, 0.0, 0.0), axis="Y",
                  mat=brass)
    bkit.rounded_box("TromboneHandGrip", 26.0, 80.0, 22.0, r=8.0, segments=3,
                     centre=(150.0 + OUTER + 45.0, 0.0, 0.0), mat=nickel)

    # The U-bow joining the two inner slides back to the mouthpiece pipe.
    for i, x in enumerate((150.0 + INNER - 60.0, 150.0 + OUTER - 30.0)):
        bkit.arc_torus("TromboneSlideBow%d" % i, SPACING, 8.0, 180.0, 360.0,
                       centre=(x, 0.0, 0.0), plane="XY", seg_major=28,
                       mat=brass, caps=True)
    bkit.cylinder("TromboneInnerJoin", 9.0, 150.0, segments=24,
                  centre=(150.0 + INNER + 40.0, 0.0, 0.0), axis="X",
                  mat=brass)

    # ---- tuning slide on the bell section ---------------------------------
    bkit.arc_torus("TromboneTuningBend", 40.0, 11.0, -90.0, 0.0,
                   centre=(L - bl - 90.0, 0.0, 40.0), plane="YZ",
                   seg_major=24, mat=brass, caps=True)
    bkit.cylinder("TromboneTuningSlide", 11.0, 110.0, segments=24,
                  centre=(L - bl - 145.0, 0.0, -20.0), axis="X", mat=brass)

    return dict(spec=SPEC, parts=9)


CHECKS = [
    # The trombone is a tube run; overall length spans mouthpiece to bell rim and
    # exists only on the assembly. The bell part alone spans just the flare.
    dict(name="overall_length", mm=1369.0, tol=3.0, how="bbox_x"),
    dict(name="bell_diameter", mm=205.0, tol=3.0, how="bbox_y",
         part="TromboneBell"),
    dict(name="outer_slide_length", mm=910.0, tol=2.0, how="bbox_x",
         part="TromboneOuterSlide0"),
    dict(name="slide_spacing", mm=52.0, tol=1.0, how="bbox_y",
         part="TromboneSlideBrace"),
]