"""door_stop -- a 55 mm wall-mounted door stop: the rubber bumper, the chromed
rose, and the domed cap the door actually strikes.

The rose and the bumper are the model. A wall stop is a domed rubber bumper
screwed to a chromed rose -- so the dome is a real swept profile (not a
cylinder), the rose is a separate turned ring behind it, and the dome's
curvature is what absorbs the impact.

Construction: the rose is a lathed ring, the bumper is a lathed dome whose
profile returns to the axis, and the three screw bosses are placed at a pitch
derived from the boss count.

Orientation: the bumper's dome points at -Y (out of the wall), the rose
against the wall at y=0, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    rose_diameter=48.0,
    bumper_diameter=26.0,
    overall_depth=48.0,
    dome_height=20.0,
    screw_bosses=3,
)

ROSE_R = 24.0
BUMP_R = 13.0


def build():
    chrome = bkit.pbr("StopChrome", base=(0.78, 0.80, 0.84), metal=0.85,
                      rough=0.18)
    rubber = bkit.pbr("StopRubber", base=(0.055, 0.055, 0.058), rough=0.76)
    steel = bkit.pbr("StopSteel", base=(0.60, 0.62, 0.66), metal=0.85,
                     rough=0.30)

    # ---- the rose: a turned ring with a real bore, lying against the wall
    rose = bkit.lathe("Rose",
                      [(8.0, 0.0), (ROSE_R, 0.0), (ROSE_R, 4.0),
                       (BUMP_R + 1.0, 6.0), (BUMP_R + 1.0, 9.0),
                       (BUMP_R - 0.6, 9.0), (BUMP_R - 0.6, 6.0),
                       (8.0, 4.0)],
                      segments=56, centre=(0.0, 4.5, 0.0), mat=chrome)
    del rose

    # ---- the bumper: a dome whose profile returns to the axis, so it is a
    # closed solid with the real curvature of an impact bumper
    prof = []
    n = 20
    for i in range(n + 1):
        t = i / float(n)
        a = math.pi / 2.0 * t
        prof.append((BUMP_R * math.sin(a),
                     9.0 + 20.0 * (1.0 - math.cos(a))))
    bkit.lathe("Bumper", prof, segments=48, centre=(0.0, 4.5, 0.0),
               mat=rubber)

    # ---- the dome's flat back, seated into the rose's mouth
    bkit.cylinder("Back", BUMP_R - 0.6, 5.0, segments=48,
                  centre=(0.0, 4.5 + 9.0 - 2.5, 0.0), mat=rubber)

    # ---- three screw bosses around the rose, at a pitch from the boss count
    n_b = SPEC["screw_bosses"]
    for i in range(n_b):
        a = 2.0 * math.pi * i / n_b
        bkit.lathe("Boss%d" % i,
                   [(0.0, 0.0), (3.4, 0.0), (3.4, 3.2), (0.0, 3.2)],
                   segments=20,
                   centre=(17.0 * math.cos(a), 0.0, 17.0 * math.sin(a)),
                   mat=chrome)
        boss = bpy.data.objects["Boss%d" % i]
        bkit.cylinder("Screw%d" % i, 1.3, 4.0, segments=16,
                      centre=(17.0 * math.cos(a), 1.6,
                              17.0 * math.sin(a)), axis="Y", mat=steel)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=8)


CHECKS = [
    dict(name="rose_diameter", mm=48.0, tol=1.5, how="bbox_x", part="Rose"),
    dict(name="bumper_diameter", mm=26.0, tol=1.0, how="bbox_x",
         part="Bumper"),
    dict(name="overall_depth", mm=48.0, tol=2.0, how="bbox_y"),
    dict(name="overall_height", mm=45.0, tol=2.0, how="bbox_z"),
    dict(name="boss_diameter", mm=6.8, tol=1.0, how="bbox_x", part="Boss0"),
]