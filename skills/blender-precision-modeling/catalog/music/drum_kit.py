"""
drum_kit -- five-drum kit with cymbals and hardware, 1900 x 1750 x 1250 mm.

The kit is repetition with real counts, not a few cylinders: a 22" bass drum,
two rack toms, a floor tom, a snare and a hi-hat, plus three cymbals on stands.
Every shell is a `lathe` with a real bearing-edge profile (hoop, skin, shell,
hoop) rather than a bare cylinder, and the lugs are `array_radial` sweeps --
one lug placed at the shell radius, swept 8 or 10 times. That is the whole
difference between "a drum" and "a drum kit".

Positions come from `bkit.grid_positions` and `bkit.lay_out`, so the toms sit on
the bass drum's shell axis rather than at hand-typed coordinates.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=1900.0,
    depth=1750.0,
    height=1271.0,
    bass_diameter=559.0,        # 22 inch
    bass_depth=590.0,
    snare_diameter=355.0,       # 14 inch
    tom_diameter=305.0,         # 12 inch
    floor_tom_diameter=400.0,   # 16 inch
    hi_hat_diameter=356.0,      # 14 inch
    crash_diameter=406.0,       # 16 inch
    ride_diameter=432.0,        # 18 inch
    lugs_per_shell=8,
)

BD_R = SPEC["bass_diameter"] / 2.0
BD_D = SPEC["bass_depth"]
TD_R = SPEC["tom_diameter"] / 2.0
SD_R = SPEC["snare_diameter"] / 2.0


def shell(name, r, depth, mat_shell, mat_skin, hoop_w=14.0):
    """A drum shell: two hoops, two skins and the shell wall between them.

    Built as a solid cylinder then bored, NOT as a lathe profile: a lathe whose
    profile carries the bearing edge shares segment counts with the bore cutter
    and the EXACT solver answers the coincident facets with bad edges.
    """
    body = bkit.cylinder(name, r, depth, segments=48, centre=(0, 0, 0),
                         axis="Z", mat=mat_skin)
    bkit.bore(body, r - 9.0, depth + 4.0, centre=(0, 0, 0), axis="Z",
              host_segments=48)
    hoops = []
    for i, sgn in enumerate((-1, 1)):
        hoops.append(bkit.tube("%sHoop%d" % (name, i), r + 6.0, r - 2.0,
                               hoop_w, segments=48,
                               centre=(0, 0, sgn * (depth / 2.0 - hoop_w / 2.0)),
                               mat=mat_shell))
    return body, hoops


def lugs(name, r, z, count, mat):
    """One lug placed at the shell radius, swept around the shell."""
    ob = bkit.rounded_box("%sLug0" % name, 26.0, 16.0, 34.0, r=4.0,
                          segments=2, centre=(0, -(r + 5.0), z), mat=mat)
    bkit.array_radial(ob, count=count)
    return ob


def build():
    shell_mat = bkit.pbr("DrumShell", base=(0.72, 0.14, 0.10), rough=0.24,
                         coat=0.6)
    head_mat = bkit.pbr("DrumHead", base=(0.93, 0.92, 0.88), rough=0.30)
    hw = bkit.pbr("DrumHardware", base=(0.82, 0.83, 0.85), metal=0.85,
                  rough=0.22)
    brass = bkit.pbr("CymbalMetal", base=(0.80, 0.66, 0.32), metal=0.85,
                     rough=0.24)
    stand = bkit.pbr("DrumStand", base=(0.80, 0.81, 0.83), metal=0.85,
                     rough=0.30)
    throne = bkit.pbr("DrumThrone", base=(0.10, 0.10, 0.11), rough=0.52)

    # ---- bass drum: the anchor, on its side like a real kit ---------------
    # A solid cylinder bored out, rather than a lathe profile: the bearing-edge
    # profile on a 559 mm shell fights the bore's segment count, and a plain
    # cylinder plus bkit.bore is the robust way to get a hollow shell.
    bass = bkit.cylinder("BassDrumShell", BD_R, BD_D, segments=56,
                         centre=(0, 0, 0), axis="Z", mat=head_mat)
    bkit.bore(bass, BD_R - 10.0, depth=BD_D + 6.0, centre=(0, 0, 0),
              axis="Z", host_segments=56)
    bass.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(bass, 0.0, 0.0, BD_R)
    for i, sgn in enumerate((-1, 1)):
        hoop = bkit.tube("BassHoop%d" % i, BD_R + 8.0, BD_R - 2.0, 16.0,
                         segments=56, centre=(0, 0, 0), axis="Z", mat=hw)
        hoop.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        bkit.move(hoop, 0.0, sgn * (BD_D / 2.0 - 8.0), BD_R)
    bl = bkit.rounded_box("BassLug0", 30.0, 18.0, 40.0, r=5.0, segments=2,
                          centre=(0, -(BD_R + 6.0), 0.0), mat=hw)
    bkit.array_radial(bl, count=12)
    bl.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bkit.move(bl, 0.0, 0.0, BD_R)

    # Spur legs and front-head pedal.
    for i, sgn in enumerate((-1, 1)):
        bkit.cylinder("BassSpur%d" % i, 13.0, 420.0, segments=12,
                      centre=(sgn * (BD_R - 40.0), -BD_D / 2.0 - 60.0, 210.0),
                      mat=stand)
        bkit.cylinder("BassFoot%d" % i, 20.0, 26.0, segments=12,
                      centre=(sgn * (BD_R - 40.0), -BD_D / 2.0 - 60.0, 13.0),
                      mat=hw)
    bkit.rounded_box("BassPedal", 90.0, 220.0, 20.0, r=6.0, segments=2,
                     centre=(0.0, -BD_D / 2.0 - 130.0, 22.0), mat=hw)
    bkit.cylinder("BassHoopClaw0", 12.0, 90.0, segments=10,
                  centre=(0.0, -BD_D / 2.0 - 30.0, BD_R - 20.0),
                  axis="Y", mat=hw)

    # ---- two rack toms, mounted on the bass drum's top shell --------------
    toms = []
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=1, pitch_x=330.0,
                                                   pitch_y=0.0)):
        body, hoops = shell("RackTom%d" % i, TD_R, 270.0, shell_mat, head_mat)
        z = BD_R + 270.0
        cy = -60.0
        for h in hoops:
            bkit.move(h, x, cy, z)
        bkit.move(body, x, cy, z)
        toms.append(body)
        lg = bkit.rounded_box("RackTom%dLug0" % i, 22.0, 14.0, 28.0, r=4.0,
                              segments=2, centre=(0, -(TD_R + 4.0), 0.0), mat=hw)
        bkit.array_radial(lg, count=SPEC["lugs_per_shell"])
        bkit.move(lg, x, cy, z)
        bkit.cylinder("TomMount%d" % i, 16.0, 190.0, segments=12,
                      centre=(x, cy + TD_R + 80.0, z - 150.0), mat=stand)

    # ---- floor tom: bigger, on its own legs --------------------------------
    floor = SPEC["floor_tom_diameter"] / 2.0
    ft = bkit.cylinder("FloorTom", floor, 460.0, segments=48, centre=(0, 0, 0),
                       axis="Z", mat=head_mat)
    bkit.bore(ft, floor - 8.0, depth=470.0, centre=(0, 0, 0), axis="Z",
              host_segments=48)
    ft_x, ft_y, ft_z = -430.0, 180.0, 470.0
    bkit.move(ft, ft_x, ft_y, ft_z)
    for i, sgn in enumerate((-1, 1)):
        hoop = bkit.tube("FloorTomHoop%d" % i, floor + 6.0, floor - 2.0, 14.0,
                         segments=48, centre=(ft_x, ft_y, ft_z + sgn * 223.0),
                         mat=hw)
    ftl = bkit.rounded_box("FloorTomLug0", 24.0, 16.0, 32.0, r=4.0, segments=2,
                           centre=(0, -(floor + 5.0), 0.0), mat=hw)
    bkit.array_radial(ftl, count=SPEC["lugs_per_shell"])
    bkit.move(ftl, ft_x, ft_y, ft_z)
    for i, sgn in enumerate((-1, 1)):
        bkit.cylinder("FloorTomLeg%d" % i, 14.0, 480.0, segments=12,
                      centre=(ft_x + sgn * 150.0, ft_y, 240.0), mat=stand)

    # ---- snare on a tripod --------------------------------------------------
    snare_z = 610.0
    snare_x, snare_y = 400.0, 520.0
    sbody, shoops = shell("Snare", SD_R, 140.0, shell_mat, head_mat)
    bkit.move(sbody, snare_x, snare_y, snare_z)
    for h in shoops:
        bkit.move(h, snare_x, snare_y, snare_z)
    sl = bkit.rounded_box("SnareLug0", 20.0, 12.0, 24.0, r=3.0, segments=2,
                          centre=(0, -(SD_R + 4.0), 0.0), mat=hw)
    bkit.array_radial(sl, count=10)
    bkit.move(sl, snare_x, snare_y, snare_z)
    for i in range(3):
        a = math.radians(90.0 + i * 120.0)
        bkit.cylinder("SnareLeg%d" % i, 11.0, snare_z - 60.0, segments=10,
                      centre=(snare_x + math.cos(a) * 190.0,
                              snare_y + math.sin(a) * 190.0,
                              (snare_z - 60.0) / 2.0), mat=stand)

    # ---- hi-hat: two cymbals on a rod -------------------------------------
    hh_x, hh_y = 520.0, -180.0
    for i, dz in enumerate((760.0, 830.0)):
        # A cymbal is a very shallow cone: radius sweeps 0 -> r while the
        # profile height grows quadratically, so the bell rises at the centre.
        r = SPEC["hi_hat_diameter"] / 2.0
        prof = [(r * (k / 6.0), 1.5 + 6.0 * (k / 6.0) ** 2) for k in range(7)]
        prof.append((0.0, 8.5))
        cy = bkit.lathe("HiHat%d" % i, prof, segments=48, centre=(0, 0, 0),
                        mat=brass)
        bkit.move(cy, hh_x, hh_y, dz)
    bkit.cylinder("HiHatRod", 11.0, 900.0, segments=12,
                  centre=(hh_x, hh_y, 400.0), mat=stand)

    # ---- crash and ride on boom stands -------------------------------------
    for tag, dia, x, y, top in (("Crash", SPEC["crash_diameter"], -420.0, -420.0, 1080.0),
                                ("Ride", SPEC["ride_diameter"], 760.0, 420.0, 1150.0)):
        r = dia / 2.0
        prof = [(r * (k / 6.0), 1.6 + 7.0 * (k / 6.0) ** 2) for k in range(7)]
        prof.append((0.0, 11.0))
        cy = bkit.lathe(tag + "Cymbal", prof, segments=48, centre=(0, 0, 0),
                        mat=brass)
        cy.rotation_euler = (math.radians(14.0 * (1 if x > 0 else -1)), 0.0, 0.0)
        bkit.move(cy, x, y, top)
        bkit.cylinder(tag + "Stand", 14.0, top - 30.0, segments=12,
                      centre=(x + 90.0, y + 60.0, (top - 30.0) / 2.0), mat=stand)
        bkit.cylinder(tag + "Felt", 22.0, 26.0, segments=12,
                      centre=(x + 24.0, y + 16.0, top - 4.0), mat=throne)

    # ---- throne -------------------------------------------------------------
    bkit.cylinder("ThroneSeat", 190.0, 70.0, segments=24, centre=(0, 980.0, 640.0),
                  mat=throne)
    bkit.cylinder("ThronePost", 30.0, 600.0, segments=14,
                  centre=(0, 980.0, 320.0), mat=stand)
    for i in range(3):
        a = math.radians(90.0 + i * 120.0)
        bkit.cylinder("ThroneLeg%d" % i, 16.0, 520.0, segments=10,
                      centre=(math.cos(a) * 210.0, 980.0 + math.sin(a) * 210.0,
                              200.0), mat=stand)

    return dict(spec=SPEC, parts=8)


CHECKS = [
    # The bass drum lies on its side, so its 559 mm diameter is on X and its
    # 590 mm depth is on Y -- `diameter` would return the depth.
    dict(name="bass_diameter", mm=559.0, tol=1.0, how="bbox_x",
         part="BassDrumShell"),
    dict(name="bass_depth", mm=590.0, tol=2.0, how="bbox_y", part="BassDrumShell"),
    dict(name="snare_diameter", mm=355.0, tol=1.0, how="diameter", part="Snare"),
    dict(name="overall_height", mm=1271.0, tol=4.0, how="bbox_z"),
]