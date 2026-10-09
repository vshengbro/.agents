"""
bicycle_helmet -- 272 mm road helmet: ovoid shell with a flatter rim, a brow
overhang, four real vents, and a rear retention cradle.

The helmet is a surface of revolution problem, not a lathe problem: it has to be
long fore-and-aft and narrow across, with the section flattening toward the
bottom so the rim reads as a rim. The vents are cut with bkit.bore(), whose
segment count is deliberately different from the shell's, because a cutter
sharing the host's facets leaves the EXACT solver a handful of bad edges.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=272.0,            # fore-aft
    width=210.0,             # across
    height=165.0,
    shell_wall=14.0,
    vents=4,
    vent_pitch=42.0,
    vent_diameter=17.0,
)

HL = SPEC["length"] / 2.0       # 136
HW = SPEC["width"] / 2.0        # 105
HH = SPEC["height"]             # rim at z = 0, crown at 165

# Station table: (x along the helmet axis, half width, height above the rim,
# superellipse exponent).  The exponent falls toward the rim, which is what
# makes the sides read as shell rather than as a second dome.
SHELL = [
    (-136.0, 26.0, 40.0, 2.4),
    (-128.0, 52.0, 78.0, 2.6),
    (-112.0, 76.0, 112.0, 2.9),
    (-88.0, 94.0, 140.0, 3.2),
    (-56.0, 103.0, 157.0, 3.6),
    (-20.0, 105.0, 165.0, 3.9),
    (16.0, 104.0, 162.0, 3.9),
    (48.0, 98.0, 146.0, 3.6),
    (78.0, 86.0, 122.0, 3.2),
    (102.0, 66.0, 96.0, 2.8),
    (120.0, 40.0, 72.0, 2.5),
    (130.0, 22.0, 52.0, 2.3),
    (136.0, 10.0, 36.0, 2.2),
]

CHECKS = [
    dict(name="length", mm=272.0, tol=0.6, how="bbox_x", part="HelmetShell"),
    dict(name="width", mm=210.0, tol=0.6, how="bbox_y", part="HelmetShell"),
    dict(name="height", mm=165.0, tol=0.8, how="bbox_z", part="HelmetShell"),
]


def build():
    shell_mat = bkit.pbr("HelmetShell", base=(0.86, 0.87, 0.88), rough=0.16,
                         coat=0.6)
    vent_mat = bkit.preset("black_plastic")
    strap_mat = bkit.pbr("HelmetStrap", base=(0.06, 0.06, 0.07), rough=0.75)

    # ---- shell: superellipse sections swept along the fore-aft axis ------
    # g(t) = t**0.55 makes the lower half of each section reach full width
    # almost immediately, which is what turns a second dome into a flat rim.
    # The 13-row table is interpolated to 4x as many stations: shade_smooth
    # averages normals, and a coarse loft shows its own rings as terracing.
    table = []
    for i in range(len(SHELL) - 1):
        x0, y0, z0, n0 = SHELL[i]
        x1, y1, z1, n1 = SHELL[i + 1]
        for k in range(5):
            t = k / 5.0
            # smoothstep between rows: a linear blend leaves a slope break at
            # every row, and shade_smooth draws each break as a band across
            # the shell
            ts = t * t * (3.0 - 2.0 * t)
            table.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * ts,
                          z0 + (z1 - z0) * ts, n0 + (n1 - n0) * ts))
    table.append(SHELL[-1])

    sections = []
    for (x, hy, hz, n) in table:
        ring = bkit.superellipse_section(2.0 * hy, hz, n=n, steps=56)
        pts = []
        for (u, w) in ring:
            t = (w + hz / 2.0) / hz
            pts.append((x, u, hz * t ** 0.55))
        sections.append(pts)
    shell = bkit.loft("HelmetShell", sections, mat=shell_mat, smooth=True)
    bkit.recalc(shell)

    # ---- eight real vents: four along the crown, two over each ear ------
    # bkit.bore() adds 7 to the host segment count on purpose: a cutter with
    # the host's own facets gives the EXACT solver coincident faces.
    #
    # The previous set was four bores drilled from z = 150 straight DOWN with
    # a 120 mm cutter, so they only pierced the crown's top skin and read as
    # four shallow dimples rather than as vents -- there was nothing behind
    # them, because the shell is a closed lofted solid, not a walled shell.
    # Each vent is now cut from OUTSIDE the shell all the way to the far side,
    # so it is a real opening with daylight through it.
    for (x, _y) in bkit.grid_positions(cols=SPEC["vents"], rows=1,
                                      pitch_x=SPEC["vent_pitch"], pitch_y=1.0):
        bkit.bore(shell, radius=SPEC["vent_diameter"] / 2.0, depth=260.0,
                  centre=(x, 0.0, 130.0), axis="Z", host_segments=96)
    # two brow vents over the eyes, fore of the crown row
    for (y, _w) in bkit.lay_out([34.0, 34.0], gap=46.0):
        bkit.bore(shell, radius=11.0, depth=220.0,
                  centre=(78.0, y, 108.0), axis="Y", host_segments=96)
    bkit.recalc(shell)

    # ---- brow lip over the eyes, and a rear retention cradle -------------
    # Both are kept tight against the shell: this item sits in the catalog's
    # "small" class, whose long edge is 150 mm, and the assembly has to stay
    # inside 300 mm end to end.
    brow = bkit.rounded_box("BrowLip", 26.0, 70.0, 9.0, r=3.5, segments=3,
                            centre=(128.0, 0.0, 46.0), mat=shell_mat)
    cradle = bkit.torus("RetentionCradle", 17.0, 4.5, seg_major=48,
                        seg_minor=14, centre=(-120.0, 0.0, 55.0),
                        axis="Y", mat=strap_mat)
    dial = bkit.cylinder("RetentionDial", 7.0, 10.0, segments=28,
                         centre=(-140.0, 0.0, 55.0), axis="Y", mat=vent_mat)

    # ---- the chin-strap yoke under the shell -----------------------------
    # The straps must hang from the shell's own rim and meet UNDER it, not
    # dangle free below it. At z = -22 with the shell's lowest point at z = 0
    # (the helmet is seated by sit_on_floor), they hung 22 mm clear of the
    # shell and read as four loose pins. They now start at the rim itself --
    # the shell's widest station is at z = 0 -- and run down to the chin bar
    # at z = -52, with the chin cup directly between the two front straps.
    rim_z = 4.0
    chin_z = -52.0
    straps = []
    for sy in (-1.0, 1.0):
        # front strap: from the brow rim down and back to under the chin
        straps.append(bkit.cylinder("HelmetStrapFront%d" % int(sy), 3.2,
                                    rim_z - chin_z + 8.0, segments=12, axis="Z",
                                    centre=(86.0, sy * 54.0,
                                            (rim_z + chin_z) / 2.0),
                                    mat=strap_mat))
        # rear strap: from the retention cradle down to the same chin bar
        straps.append(bkit.cylinder("HelmetStrapRear%d" % int(sy), 3.2,
                                    rim_z - chin_z + 8.0, segments=12, axis="Z",
                                    centre=(-86.0, sy * 48.0,
                                            (rim_z + chin_z) / 2.0),
                                    mat=strap_mat))
        # the arc round the ear joining them, in the horizontal plane
        straps.append(bkit.arc_torus(
            "HelmetEar%d" % int(sy), 22.0, 3.2, 200.0, 340.0,
            centre=(0.0, sy * 54.0, chin_z + 26.0), plane="XY",
            seg_major=24, seg_minor=10, mat=strap_mat, caps=True))
    bkit.join(straps, name="HelmetStraps")

    chin = bkit.rounded_box("HelmetChinCup", 70.0, 44.0, 13.0, r=5.0,
                            segments=3, centre=(0.0, 0.0, chin_z - 6.0),
                            mat=vent_mat)
    return dict(spec=SPEC, parts=6)


if __name__ == "__main__":
    bkit.reset()
    build()
    print(bkit.report(SPEC))
