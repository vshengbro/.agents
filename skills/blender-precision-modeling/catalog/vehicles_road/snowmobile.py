"""
snowmobile -- two-seat trail snowmobile, 2800 x 1150 x 1200 mm.

The read is all in the contact patches: two 1200 mm skis at the FRONT and one
1100 mm cleated track at the REAR, with the track's top surface carried 600 mm
off the ground in a tunnel between the bodywork. Get the skis too small or the
track too short and it stops being a snowmobile and becomes a motorbike.

Real figures: 1150 mm of width carried by 250 mm skis on a 900 mm track,
a 1250 mm seat height above the ground, and handlebars at 1200 mm -- only 400 mm
above the seat, which is why the machine looks "crouched".
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=2800.0,
    width=1150.0,
    height=1200.0,
    ski_length=1200.0,
    ski_track=900.0,
    track_length=1100.0,
    track_width=400.0,
    seat_height=780.0,
    bar_width=780.0,
)

CHECKS = [
    dict(name="length", mm=2800.0, tol=6.0, how="bbox_x", part=None),
    dict(name="width", mm=1150.0, tol=6.0, how="bbox_y", part=None),
    dict(name="height", mm=1200.0, tol=6.0, how="bbox_z", part=None),
    dict(name="ski_length", mm=1200.0, tol=4.0, how="bbox_x", part="SledSkis"),
    dict(name="track_length", mm=1100.0, tol=4.0, how="bbox_x",
         part="SledTrack"),
    dict(name="track_width", mm=400.0, tol=3.0, how="bbox_y", part="SledTrack"),
]


def build():
    paint = bkit.pbr("SledPaint", base=(0.05, 0.32, 0.52), rough=0.22,
                     metal=0.30, coat=0.7)
    seat = bkit.pbr("SledSeat", base=(0.06, 0.06, 0.07), rough=0.55)
    rubber = bkit.preset("rubber")
    dark = bkit.preset("dark_metal")
    alloy = bkit.preset("brushed_metal")
    glass = bkit.pbr("SledScreen", base=(0.62, 0.70, 0.76), rough=0.08,
                     transmission=0.5)

    # ---- rear track: a rounded slab with cleats laid out from a pitch ----
    bkit.rounded_box("SledTrack", SPEC["track_length"], SPEC["track_width"],
                     520.0, r=195.0, segments=4, centre=(-750.0, 0.0, 300.0),
                     mat=rubber)
    for i, (gx, _gy) in enumerate(bkit.grid_positions(cols=6, rows=1,
                                                     pitch_x=150.0,
                                                     pitch_y=0.0)):
        V.mirror_y(bkit.rounded_box("SledCleat%02d" % i, 60.0, 460.0, 60.0,
                                    r=15.0, segments=2,
                                    centre=(gx - 750.0, 0.0, 570.0),
                                    mat=dark))
    bkit.rounded_box("SledTunnel", 1300.0, 500.0, 260.0, r=60.0, segments=3,
                     centre=(-500.0, 0.0, 700.0), mat=paint)
    bkit.rounded_box("SledSuspension", 900.0, 320.0, 200.0, r=40.0,
                     segments=2, centre=(-450.0, 0.0, 640.0), mat=alloy)

    # ---- body: hood, tunnel, seat ----------------------------------------
    bkit.rounded_box("SledHood", 1300.0, 900.0, 520.0, r=180.0, segments=4,
                     centre=(620.0, 0.0, 800.0), mat=paint)
    bkit.rounded_box("SledNose", 420.0, 700.0, 380.0, r=150.0, segments=4,
                     centre=(1150.0, 0.0, 640.0), mat=paint)
    bkit.rounded_box("SledSeat", 900.0, 380.0, 140.0, r=60.0, segments=3,
                     centre=(-320.0, 0.0, 880.0), mat=seat)
    bkit.rounded_box("SledBackrest", 140.0, 420.0, 420.0, r=60.0, segments=3,
                     centre=(-730.0, 0.0, 990.0), mat=seat)

    # ---- skis and their spindles ------------------------------------------
    V.mirror_y(bkit.rounded_box("SledSkis", SPEC["ski_length"], 250.0, 90.0,
                                r=40.0, segments=3,
                                centre=(900.0, 450.0, 45.0), mat=dark))
    V.strut("SledSpindle", (900.0, 450.0, 90.0), (620.0, 300.0, 620.0),
            26.0, alloy, 14)
    V.mirror_y(V.strut("SledAarm", (900.0, 450.0, 120.0),
                          (500.0, 180.0, 640.0), 30.0, alloy, 14))
    bkit.rounded_box("SledFrontMount", 200.0, 700.0, 120.0, r=40.0, segments=2,
                     centre=(560.0, 0.0, 700.0), mat=alloy)

    # ---- bars and screen ---------------------------------------------------
    V.strut("SledSteering", (560.0, 0.0, 800.0), (700.0, 0.0, 1170.0), 24.0,
            dark, 14)
    bkit.rounded_box("SledBars", 60.0, 780.0, 60.0, r=25.0, segments=3,
                     centre=(700.0, 0.0, 1170.0), mat=dark)
    bkit.rounded_box("SledScreen", 40.0, 720.0, 380.0, r=90.0, segments=3,
                     centre=(760.0, 0.0, 1000.0), mat=glass)
    bkit.rounded_box("SledHeadlamp", 120.0, 260.0, 150.0, r=50.0, segments=3,
                     centre=(1210.0, 0.0, 780.0),
                     mat=bkit.pbr("SledLens", base=(0.86, 0.86, 0.90),
                                  rough=0.08, transmission=0.5))

    return dict(spec=SPEC, parts=17)