"""
trailer -- 40 ft skeletal cargo trailer, 13600 x 2440 x 2590 mm deck box.

A trailer has no body at all: it is a container sitting on a chassis, and the
chassis is what you read first. Everything here is a real component -- two
frame rails, cross members, a kingpin, landing legs, a rear tandem and an
underrun bar -- because a trailer modelled as a box on two cylinders reads as a
shipping container on a dolly.

Key figures:
  * ISO container 12192 x 2440 x 2590 mm, which is what sets the overall width
    and height exactly -- the container is the bounding object;
  * deck top at 1300 mm, which is also the trailer kingpin height;
  * tandem axles 1300 mm apart at the extreme rear, wheels 1050 mm on 315 mm
    tyres so the trailer carries its own load low;
  * the rear face at -6400 and the front bulkhead at +7200: 13600 mm overall.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))
sys.path.insert(0, _HERE)

import bkit
import _vehicles as V

SPEC = dict(
    length=13600.0,
    width=2440.0,
    height=2590.0,
    container_length=12190.0,
    deck_height=1300.0,
    axle_spacing=1300.0,
    wheel_diameter=1050.0,
    rim_diameter=508.0,
    tyre_width=315.0,
    track=2000.0,
)

CHECKS = [
    dict(name="length", mm=13600.0, tol=8.0, how="bbox_x", part=None),
    dict(name="width", mm=2440.0, tol=8.0, how="bbox_y", part="TrailerBox"),
    dict(name="container_height", mm=2590.0, tol=4.0, how="bbox_z",
         part="TrailerBox"),
    dict(name="container_length", mm=12190.0, tol=8.0, how="bbox_x",
         part="TrailerBox"),
    dict(name="frame_length", mm=13000.0, tol=8.0, how="bbox_x",
         part="TrailerFrameRail"),
    dict(name="wheel_diameter", mm=1050.0, tol=2.0, how="diameter", part="Wheel0"),
]

CONTAINER_X0, CONTAINER_X1 = -6100.0, 6090.0
DECK_Z = SPEC["deck_height"]


def build():
    shell_mat = bkit.pbr("ContainerPaint", base=(0.24, 0.40, 0.30), rough=0.52)
    rib_mat = bkit.pbr("ContainerRib", base=(0.19, 0.33, 0.25), rough=0.50)
    frame = bkit.pbr("TrailerFrame", base=(0.20, 0.21, 0.23), rough=0.46)
    steel = bkit.preset("dark_metal")
    rubber = bkit.preset("rubber")
    lamp_r = bkit.pbr("TrailerLamp", base=(0.50, 0.035, 0.030), rough=0.10,
                      transmission=0.3)

    box = bkit.rounded_box("TrailerBox", CONTAINER_X1 - CONTAINER_X0, 2440.0,
                           SPEC["height"], r=45.0, segments=2,
                           centre=(0.5 * (CONTAINER_X0 + CONTAINER_X1), 0.0,
                                   DECK_Z + SPEC["height"] / 2.0),
                           mat=shell_mat)
    # corrugation: eight vertical ribs laid out from a pitch, not hand-placed
    for i, (gx, _gy) in enumerate(bkit.grid_positions(cols=8, rows=1,
                                                       pitch_x=600.0,
                                                       pitch_y=0.0)):
        V.mirror_y(bkit.rounded_box("TrailerRib%02d" % i, 170.0, 26.0, 2200.0,
                                    r=10.0, segments=2,
                                    centre=(gx - 50.0, 1225.0,
                                            DECK_Z + 1295.0),
                                    mat=rib_mat))

    V.mirror_y(bkit.rounded_box("TrailerFrameRail", 13000.0, 180.0, 380.0,
                                r=28.0, segments=2,
                                centre=(100.0, 560.0, DECK_Z - 250.0),
                                mat=frame))
    for (x, _w) in bkit.lay_out([180.0] * 9, gap=1350.0, centre=True):
        bkit.rounded_box("TrailerCrossMember", 180.0, 2000.0, 240.0, r=20.0,
                         segments=2, centre=(x + 100.0, 0.0, DECK_Z - 230.0),
                         mat=frame)

    bkit.cylinder("TrailerKingpin", 140.0, 260.0, segments=32,
                  centre=(5700.0, 0.0, 1150.0), mat=steel)
    bkit.rounded_box("TrailerKingpinPlate", 700.0, 900.0, 60.0, r=18.0,
                     segments=2, centre=(5900.0, 0.0, 1290.0), mat=frame)
    V.mirror_y(bkit.rounded_box("TrailerLandingLeg", 200.0, 220.0, 1000.0,
                                r=18.0, segments=2,
                                centre=(4700.0, 720.0, 800.0), mat=steel))
    bkit.rounded_box("TrailerUnderrunBar", 140.0, 2200.0, 200.0, r=30.0,
                     segments=2, centre=(-6730.0, 0.0, 620.0), mat=frame)
    bkit.rounded_box("TrailerHeadboard", 240.0, 2400.0, 2400.0, r=35.0,
                     segments=2, centre=(6620.0, 0.0, DECK_Z + 1180.0),
                     mat=frame)
    bkit.rounded_box("TrailerNosePlate", 340.0, 900.0, 500.0, r=30.0,
                     segments=2, centre=(6630.0, 0.0, 1420.0), mat=frame)
    V.mirror_y(V.box_lamp("TrailerLamps", 80.0, 320.0, 200.0,
                          (-6740.0, 780.0, 760.0), lamp_r, r=20.0))
    bkit.rounded_box("TrailerMudflap", 40.0, 2000.0, 700.0, r=15.0, segments=2,
                     centre=(-5700.0, 0.0, 400.0), mat=rubber)

    w = V.wheel("TrailerWheel", SPEC["wheel_diameter"], SPEC["tyre_width"],
                SPEC["rim_diameter"], spokes=8, seg=56)
    r = SPEC["wheel_diameter"] / 2.0
    s = SPEC["axle_spacing"] / 2.0
    y = SPEC["track"] / 2.0
    V.place_wheels(w, [(-4400.0 + s, -y, r), (-4400.0 + s, y, r),
                       (-4400.0 - s, -y, r), (-4400.0 - s, y, r)],
                   names=["Wheel0", "Wheel1", "Wheel2", "Wheel3"])

    return dict(spec=SPEC, parts=9)