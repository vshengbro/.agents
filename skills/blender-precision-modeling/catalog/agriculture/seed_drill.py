"""
seed_drill -- a 4 m pneumatic seed drill: 3 hoppers, 12 coulters, 2 wheels.

A seed drill is a HOPPER over a METERING ROW over a COULTER, repeated along the
machine, and the repetition is the whole job: the row spacing fixes both the
number of coulters and the width of the implement, so they cannot disagree.

    row spacing  300 mm, 12 rows  -> a 3.3 m drill on a 3.6 m toolbar
    hopper       a moulded V, 700 x 700, 3 bays on the 1200 mm pitch
    coulter      400 mm double-disc, dished 40 mm, on a 12 mm square-section
                 shank, one per row
    metering     a cup wheel per row under the hopper outlet
    ground drive a 24-sprocket chain wheel, geared to the drive wheel

The coulters are the read: they have to sit ON the rows and be angled 7 deg
back, which is what puts seed in the ground rather than on it.
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _agri as A

SPEC = dict(
    rows=12,
    row_spacing=300.0,
    coulter_dia=400.0,
    coulter_dish=40.0,
    coulter_thickness=6.0,
    toolbar_width=3600.0,
    hoppers=3,
    hopper_pitch=1200.0,
    hopper_length=700.0,
    hopper_width=700.0,
    hopper_depth=520.0,
    wheel_dia=760.0,
    wheel_width=200.0,
    wheel_track=3000.0,
    overall_length=3600.0,
)

NR = SPEC["rows"]
RS = SPEC["row_spacing"]
CD = SPEC["coulter_dia"]
NH = SPEC["hoppers"]
HP = SPEC["hopper_pitch"]
WD = SPEC["wheel_dia"]
TRACK = SPEC["wheel_track"]

# the row centres, from the row spacing -- the coulter count IS the row count
ROW_X = [(-(NR - 1) / 2.0 + i) * RS for i in range(NR)]

# the three hopper bays
HOP_X = [(-(NH - 1) / 2.0 + i) * HP for i in range(NH)]

TOOLBAR_Z = 980.0

CHECKS = [
    dict(name="coulter_raked_width", mm=400.0, tol=4.0, how="bbox_y",
         part="DrillCoulter0"),
    dict(name="coulter_dia", mm=400.0, tol=4.0, how="bbox_y",
         part="DrillCoulter0"),
    dict(name="toolbar_width", mm=3600.0, tol=6.0, how="bbox_y",
         part="DrillToolbar"),
    dict(name="hopper_pitch_run", mm=3140.0, tol=8.0, how="bbox_x",
         part="DrillHopperLid0"),
    dict(name="hopper_length", mm=700.0, tol=3.0, how="bbox_x",
         part="DrillHopper0"),
    dict(name="wheel_dia", mm=760.0, tol=4.0, how="diameter", part="Wheel0"),
    dict(name="wheel_tread_on_floor", mm=0.0, tol=2.0, how="z_min", part="Wheel0"),
]


def build():
    paint = bkit.pbr("DrillPaint", base=(0.70, 0.31, 0.05), metal=0.28,
                     rough=0.38)
    steel = bkit.preset("dark_metal")
    edge = bkit.preset("brushed_metal")
    hopper_mat = bkit.pbr("DrillHopperMat", base=(0.86, 0.85, 0.80),
                          rough=0.40)

    # ---- the toolbar: the spine every row hangs from ---------------
    bkit.rounded_box("DrillToolbar", 160.0, SPEC["toolbar_width"], 140.0,
                     r=12.0, segments=2,
                     centre=(420.0, 0.0, TOOLBAR_Z), mat=paint)
    # the frame closes the toolbar into a rectangle and carries the wheels
    for sx in (-1, 1):
        bkit.rounded_box("DrillFrameRail%d" % (0 if sx < 0 else 1), 1400.0,
                         90.0, 120.0, r=8.0, segments=2,
                         centre=(200.0 + sx * 300.0, 0.0, TOOLBAR_Z - 90.0),
                         mat=paint)

    # ---- three moulded hoppers on the 1200 mm pitch -----------------
    # Each hopper is a loft: a wide rectangular mouth tapering to a narrow
    # outlet. A rectangular-to-rectangular taper needs an explicit ring, so the
    # sections are superellipses at a rising exponent.
    HL, HW, HD = SPEC["hopper_length"], SPEC["hopper_width"], SPEC["hopper_depth"]
    for i, hx in enumerate(HOP_X):
        secs = []
        for t, z in ((0.0, TOOLBAR_Z + 140.0 + HD),
                     (0.55, TOOLBAR_Z + 140.0 + HD * 0.45),
                     (1.0, TOOLBAR_Z + 140.0)):
            sx = HL + (240.0 - HL) * t
            sy = HW + (240.0 - HW) * t
            n = 6.0 + (2.5 - 6.0) * t
            ring = bkit.superellipse_section(sx, sy, n=n, steps=40)
            secs.append([(p[0], p[1], z) for p in ring])
        hp = bkit.loft("DrillHopper%d" % i, secs, mat=hopper_mat)
        bkit.recalc(hp)
        bkit.move(hp, hx, 0.0, 0.0)
        # the lid, a flat plate clipped over the mouth
        bkit.rounded_box("DrillHopperLid%d" % i, HL + 40.0, HW + 40.0, 25.0,
                         r=10.0, segments=1,
                         centre=(hx, 0.0, TOOLBAR_Z + 140.0 + HD + 12.0),
                         mat=paint)
    # one hopper array, so the pitch is a single measurable object
    lids = bpy_get("DrillHopperLid0")
    bkit.move(lids, HOP_X[0], 0.0, 0.0)
    bkit.array_linear(lids, NH, (HP, 0.0, 0.0))

    # ---- metering wheels under each hopper outlet -------------------
    for i, hx in enumerate(HOP_X):
        bkit.cylinder("DrillMeteringCup%d" % i, 90.0, 120.0, segments=24,
                      axis="Y", centre=(hx, 0.0, TOOLBAR_Z - 40.0),
                      mat=steel)

    # ---- 12 coulters, ONE PER ROW, on the row pitch ---------------
    # The coulter is a dished disc; it is angled 7 deg back from vertical, which
    # is what places the seed rather than merely opening a slot.
    for i, rx in enumerate(ROW_X):
        d = A.disc("DrillCoulter%d" % i, CD, SPEC["coulter_thickness"],
                   SPEC["coulter_dish"], mat=edge)
        d.rotation_euler = (math.radians(7.0), 0.0, math.pi / 2.0)
        bpy_update()
        bkit.move(d, 700.0, rx, CD / 2.0 + 30.0)
        # the shank: a square-section arm down from the toolbar to the coulter
        A.bar_between("DrillCoulterShank%d" % i,
                      (700.0, rx, CD / 2.0 + 30.0),
                      (520.0, rx, TOOLBAR_Z - 60.0),
                      40.0, 40.0, mat=steel, r=4.0)

    # ---- ground drive: a chain wheel geared to the drive wheel -----
    bkit.cylinder("DrillDriveWheel", 260.0, 40.0, segments=32, axis="Y",
                  centre=(0.0, TRACK / 2.0 - 300.0, 300.0), mat=steel)

    # ---- two ground wheels on a 3 m track, treads on z=0 ----------
    wr = WD / 2.0
    w = A.ground_wheel("Wheel0", WD, SPEC["wheel_width"])
    A.place_wheels(w, [(0.0, -TRACK / 2.0, wr), (0.0, TRACK / 2.0, wr)],
                   names=["Wheel0", "Wheel1"])

    return dict(spec=SPEC, parts=1 + 2 + 2 * NH + NH + 2 * NR + 1,
                rows=NR, coulters=NR, note=A.AGRI_NOTE)


def bpy_get(name):
    import bpy
    return bpy.data.objects.get(name)


def bpy_update():
    import bpy
    bpy.context.view_layer.update()