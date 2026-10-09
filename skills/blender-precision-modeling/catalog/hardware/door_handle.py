"""
door_handle -- 128 mm lever handle on a 55 mm rose.

The three numbers that define a lever handle are rose diameter, projection and
the base diameter of the lever, and they are not independent: a 128 mm handle
is a 55 mm rose plus a 118 mm projection, and the lever is fattest where it
leaves the spindle boss and tapers to about two thirds of that at the tip.
Getting that taper wrong is what makes a render read as "door handle" instead
of "the right door handle".

The lever is a loft over superellipse (squircle) sections rather than rounded
rectangles: superellipse_section returns a closed ring with no duplicated seam
vertex, so the lofted tube has no zero-area faces, and n = 4 gives the soft
rectangular section a cast lever actually has.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

ROSE_D = 55.0           # rose diameter
ROSE_T = 11.0           # rose thickness
BOSS_D = 26.0           # spindle boss diameter
BOSS_L = 18.0           # boss projection beyond the rose face
LEVER_PROJ = 118.0      # projection from the rose face to the tip
LEVER_BASE = 20.0       # lever section at the boss
LEVER_TIP = 13.0        # lever section at the tip
LEVER_DROOP = 9.5       # how far the tip drops below the spindle axis

SPEC = dict(rose_diameter=ROSE_D,
            rose_thickness=ROSE_T,
            boss_diameter=BOSS_D,
            boss_length=BOSS_L,
            lever_projection=LEVER_PROJ,
            lever_base=LEVER_BASE,
            overall_length=148.0)


def build():
    nickel = bkit.pbr("SatinNickel", base=(0.84, 0.86, 0.88), metal=0.78,
                      rough=0.16)

    # ---- rose: turned disc with a rounded rim, axis along Y -------------
    rose = bkit.lathe("Rose",
                      [(0.0, 0.0), (ROSE_D / 2.0 - 2.0, 0.0),
                       (ROSE_D / 2.0, 1.2), (ROSE_D / 2.0, ROSE_T - 1.4),
                       (ROSE_D / 2.0 - 2.0, ROSE_T), (0.0, ROSE_T)],
                      segments=96, mat=nickel)
    rose.rotation_euler = (math.radians(-90.0), 0.0, 0.0)

    boss = bkit.cylinder("SpindleBoss", BOSS_D / 2.0, BOSS_L, segments=64,
                         centre=(0, ROSE_T + BOSS_L / 2.0 - 3.0, 0.0),
                         axis="Y", mat=nickel)

    # ---- lever: squircle sections along a drooping path ------------------
    # (x, section size, z) taken from the spindle axis outward. The tip tapers
    # through three shrinking sections so the lofted end is round, not a
    # sawn-off rectangle. superellipse_section returns a 2D ring, so it is
    # lifted into the YZ plane at each station to give loft a 3D section.
    y_axis = ROSE_T + BOSS_L - 6.0

    def ring(x, size, droop):
        section = bkit.superellipse_section(size, size, n=4.0, steps=32)
        return [(x, y_axis + u, droop + w) for (u, w) in section]

    stations = [(6.0, 1.00, 0.0), (18.0, 0.95, -0.7), (48.0, 0.85, -3.0),
                (78.0, 0.80, -5.8), (100.0, 0.75, -8.0), (110.0, 0.65, -9.0),
                (116.0, 0.40, -9.4), (119.0, 0.15, -LEVER_DROOP)]
    sections = [ring(x, LEVER_BASE * taper, droop)
                for (x, taper, droop) in stations]
    bkit.loft("Lever", sections, closed_loop=True, cap_start=True,
              cap_end=True, mat=nickel, smooth=True)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="rose_diameter", mm=55.0, tol=0.05, how="bbox_x", part="Rose"),
    # each loft ring lies in the YZ plane at a fixed x, so the lever's extent is
    # simply the station span: 6 mm (blended into the boss) to 119 mm (tip)
    dict(name="lever_length", mm=113.0, tol=0.20, how="bbox_x", part="Lever"),
    # rose half-width 27.5 beyond the origin, tip at 119
    dict(name="overall_length", mm=146.5, tol=0.30, how="bbox_x", part=None),
]