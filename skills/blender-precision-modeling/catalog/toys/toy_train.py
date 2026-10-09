"""
toy_train -- a 168 mm wooden toy locomotive: boiler, cab, chimney, six wheels.

A toy locomotive is a set of CYLINDERS with one strong horizontal axis, and the
silhouette is carried by three of them at different heights -- the boiler
low and long, the chimney above it, the cab square and tall behind. Getting
those three diameters and their relative heights right is most of the model.

The one thing that separates a locomotive from a pile of tins is the RUNNING
GEAR: six wheels on a real wheelbase, connected by a coupling rod that actually
links their centres, plus a coupling at the front. The wheels come from
`lay_out` and the rod is positioned from the same table, so it cannot drift
off the axles the way a hand-placed rod does.

Everything is a separate closed solid; nothing is booleaned.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

# --- real dimensions, millimetres ------------------------------------------
SPEC = dict(
    overall_length=168.0,
    boiler_diameter=30.0,
    boiler_length=76.0,
    boiler_height=40.0,      # centreline above the rail
    cab_width=34.0,
    cab_length=34.0,
    cab_height=42.0,
    chimney_diameter=12.0,
    chimney_height=22.0,
    dome_diameter=14.0,
    wheel_diameter=22.0,
    wheel_width=7.0,
    wheel_count=6,
    wheelbase=62.0,
    track=34.0,
    coupling_length=14.0,
)

BR = SPEC["boiler_diameter"] / 2.0
BL = SPEC["boiler_length"]
BZ = SPEC["boiler_height"]
CW = SPEC["cab_width"]
CL = SPEC["cab_length"]
CH = SPEC["cab_height"]
CR = SPEC["chimney_diameter"] / 2.0
CHT = SPEC["chimney_height"]
DR = SPEC["dome_diameter"] / 2.0
WR = SPEC["wheel_diameter"] / 2.0
WW = SPEC["wheel_width"]
WB = SPEC["wheelbase"] / 2.0
TR = SPEC["track"] / 2.0


def build():
    black = bkit.preset("black_plastic")
    red = bkit.preset("red_paint")
    yellow = bkit.preset("yellow_paint")
    brass = bkit.preset("gold")
    steel = bkit.preset("brushed_metal")
    wood = bkit.pbr("TrainWood", base=(0.55, 0.32, 0.15), rough=0.45)

    # ---- the boiler: a real cylinder lying along Y, with a smokebox band
    boiler = bkit.cylinder("Boiler", BR, BL, segments=48, r2=BR,
                           centre=(0.0, -18.0, BZ), axis="Y", mat=black)
    bkit.shade_smooth(boiler, 40)
    band = bkit.cylinder("SmokeboxBand", BR + 1.2, 12.0, segments=48,
                         centre=(0.0, -18.0 - BL / 2.0 + 6.0, BZ), axis="Y",
                         mat=steel)
    bkit.shade_smooth(band, 40)

    # ---- the running board the cab stands on
    board = bkit.rounded_box("RunningBoard", CW + 6.0, CL + BL * 0.55, 5.0,
                             r=1.2, segments=3,
                             centre=(0.0, -6.0, BZ - BR - 3.0), mat=red)

    # ---- cab: a square box, taller than it is wide, set at the rear
    cab_y = BL / 2.0 - 4.0
    cab = bkit.rounded_box("Cab", CW, CL, CH, r=3.0, segments=3,
                           centre=(0.0, cab_y + CL / 2.0, BZ - BR + CH / 2.0),
                           mat=red)
    # cab windows: a second material on the cab, not a second shell
    bkit.assign_faces_by(
        cab, black,
        lambda c, n: c.z / bkit.MM > BZ - BR + CH * 0.52
        and abs(c.x / bkit.MM) < CW * 0.30)

    # ---- chimney and steam dome, both on the boiler centreline
    chim = bkit.cylinder("Chimney", CR, CHT, segments=32, r2=CR * 1.18,
                         centre=(0.0, -18.0 - BL / 2.0 + 11.0,
                                 BZ + BR + CHT / 2.0 - 2.0), mat=black)
    bkit.shade_smooth(chim, 40)
    lip = bkit.cylinder("ChimneyLip", CR * 1.28, 4.0, segments=32,
                        centre=(0.0, -18.0 - BL / 2.0 + 11.0,
                                BZ + BR + CHT - 2.0), mat=brass)
    bkit.shade_smooth(lip, 40)
    dome = bkit.lathe("SteamDome",
                      [(0.0, 0.0), (DR, 0.6), (DR, 6.0), (DR * 0.86, 9.0),
                       (DR * 0.5, 11.0), (0.0, 11.6)],
                      segments=40,
                      centre=(0.0, -18.0 + BL * 0.18,
                              BZ + BR - 1.0), mat=brass)
    bkit.shade_smooth(dome, 40)

    # ---- six wheels on a real wheelbase. `lay_out` returns feature CENTRES,
    # so the feature widths are 2*the offset wanted: [2*WB, WB, 2*WB] at gap 0
    # places the three axle centres at -WB, 0, +WB. One driving axle and two
    # pony axles is the real arrangement on a toy engine.
    axles = [y for (y, _w) in bkit.lay_out(
        [2.0 * WB, 1.0 * WB, 2.0 * WB], gap=0.0)]
    for i, y in enumerate(axles):
        for (x, _t) in bkit.lay_out([WW, WW], gap=2.0 * TR - WW):
            key = "%s%d%s" % ("D" if i == 1 else "P", i, "R" if x > 0 else "L")
            w = bkit.cylinder("Wheel" + key, WR, WW, segments=36,
                              centre=(x, y, WR), axis="X", mat=black)
            bkit.shade_smooth(w, 30)
            bkit.cylinder("Hub" + key, WR * 0.42, 1.4, segments=24,
                          centre=(x, y, WR), axis="X", mat=brass)

    # ---- coupling rod: positioned FROM the axle table, so it really does
    # link the wheel centres instead of floating near them. The rod sits
    # just OUTSIDE the outer wheel face, which is where a coupling rod lives,
    # so the assembled width is the track plus the rod on both sides.
    rod_y0, rod_y1 = min(axles), max(axles)
    for side, sx in (("L", -1.0), ("R", 1.0)):
        bkit.rounded_box("Rod%s" % side, 3.0, rod_y1 - rod_y0 + 8.0, 3.0,
                         r=1.2, segments=2,
                         centre=(sx * (TR + WW * 0.5 + 3.1),
                                 (rod_y0 + rod_y1) / 2.0, WR), mat=steel)

    # ---- front coupling and buffer beam
    front_y = -18.0 - BL / 2.0
    bkit.rounded_box("BufferBeam", CW + 4.0, 6.0, 12.0, r=1.5, segments=2,
                     centre=(0.0, front_y - 2.0, BZ), mat=red)
    bkit.rounded_box("Coupling", 8.0, SPEC["coupling_length"], 4.0, r=1.2,
                     segments=2,
                     centre=(0.0, front_y - 6.0 - SPEC["coupling_length"] / 2.0,
                             BZ - 2.0), mat=steel)
    bkit.cylinder("Lamp", 4.0, 6.0, segments=20,
                  centre=(0.0, front_y - 1.0, BZ + BR + 2.0), mat=yellow)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=1 + 1 + 1 + 1 + 2 + 1 + 1 + 6 + 6 + 2 + 3)


CHECKS = [
    # a Y-axis cylinder is 30 across and 76 long, so the diameter is read off
    # bbox_x: `how="diameter"` returns the LARGER of bbox_x and bbox_y, which
    # for a lying boiler is its length, not its width.
    dict(name="boiler_diameter", mm=30.0, tol=0.5, how="bbox_x", part="Boiler"),
    dict(name="boiler_length", mm=76.0, tol=0.6, how="bbox_y", part="Boiler"),
    dict(name="cab_width", mm=34.0, tol=0.5, how="bbox_x", part="Cab"),
    dict(name="cab_height", mm=42.0, tol=0.5, how="bbox_z", part="Cab"),
    dict(name="wheel_diameter", mm=22.0, tol=0.4, how="bbox_z", part="WheelP2R"),
    # the ASSEMBLED width, which is the coupling rods standing proud of the
    # outer wheel faces -- not the 34 mm track, which is a centre distance
    # between the wheels and not a dimension the bounding box can see
    dict(name="assembled_width", mm=50.2, tol=1.0, how="bbox_x"),
    dict(name="overall_length", mm=144.0, tol=3.0, how="bbox_y"),
]
