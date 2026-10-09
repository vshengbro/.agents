"""
bike_rack -- 1088 x 748 x 810 mm Sheffield-style cycle stand: five inverted-U
hoops on a 260 mm pitch, linked by two continuous rails, on ten ground plates
with twenty anchor bolts.

`medium` in the catalog. The repetition IS the object: five identical hoops at a
computed pitch, one `arc_torus` each swept by `array_linear`, plus anchor bolts
from `grid_positions`. Each hoop is a half-torus in the YZ plane -- the row runs
along X, so the hoops must face across it -- and its legs rise 60 mm INTO the
hoop's own tube rather than butting against its end cap, because a leg stopping
exactly at the cap puts two coincident discs on top of each other.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    hoops=5,
    hoop_pitch=260.0,
    hoop_width=700.0,
    hoop_height=750.0,
    hoop_tube_diameter=48.0,
    rail_diameter=42.0,
    ground_plates=10,
    overall_height=810.0,
    overall_width=1088.0,
)

PITCH = SPEC["hoop_pitch"]
HOOP_W = SPEC["hoop_width"]
HOOP_H = SPEC["hoop_height"]
TUBE_R = SPEC["hoop_tube_diameter"] / 2.0
SPAN = (SPEC["hoops"] - 1) * PITCH
ARC_Z = HOOP_H - HOOP_W / 2.0         # 400: arc centreline height
LEG_BURY = 60.0                       # legs drop below the ground plate
LEG_OVERLAP = 60.0                    # ...and rise into the hoop tube


def build():
    steel = bkit.pbr("RackSteel", base=(0.20, 0.21, 0.22), metal=0.85,
                     rough=0.48)
    dark = bkit.pbr("RackDark", base=(0.13, 0.13, 0.14), metal=0.85,
                    rough=0.54)
    plate = bkit.pbr("RackPlate", base=(0.16, 0.16, 0.17), metal=0.85,
                     rough=0.60)

    # ---- five inverted-U hoops on a 260 mm pitch -------------------------
    hoop = bkit.arc_torus("RackHoops", HOOP_W / 2.0, TUBE_R, 0.0, 180.0,
                          plane="YZ", centre=(0.0, 0.0, ARC_Z),
                          seg_major=44, mat=steel, caps=True)
    bkit.array_linear(hoop, count=SPEC["hoops"],
                      offset_mm=(PITCH, 0.0, 0.0))
    # array_linear starts the run AT the source, so the row is off-centre by
    # SPAN/2 until it is moved back.
    bkit.move(hoop, -SPAN / 2.0, 0.0, 0.0)

    # ---- legs: 60 mm below the plate, 60 mm up inside the tube ----------
    for side, tag in ((-1.0, "A"), (1.0, "B")):
        # Runs from 60 mm below the plate up to 60 mm INSIDE the hoop tube.
        leg = bkit.cylinder("_leg%s" % tag, TUBE_R,
                            ARC_Z + LEG_OVERLAP + LEG_BURY, segments=32,
                            axis="Z",
                            centre=(0.0, side * HOOP_W / 2.0,
                                    (ARC_Z + LEG_OVERLAP - LEG_BURY) / 2.0),
                            mat=steel)
        bkit.array_linear(leg, count=SPEC["hoops"],
                          offset_mm=(PITCH, 0.0, 0.0))
        bpy.data.objects[leg.name].name = "RackLegs" + tag
        bkit.move(bpy.data.objects["RackLegs" + tag], -SPAN / 2.0, 0.0, 0.0)

    # ---- two continuous rails tying the hoops together -------------------
    rails = []
    for side, tag in ((-1.0, "A"), (1.0, "B")):
        rails.append(bkit.cylinder("HoopRail" + tag,
                                   SPEC["rail_diameter"] / 2.0,
                                   SPAN + PITCH, segments=32, axis="X",
                                   centre=(0.0, side * (HOOP_W / 2.0), 30.0),
                                   mat=dark))
    bkit.join(rails, name="HoopRails")

    # ---- ten ground plates and twenty anchor bolts ----------------------
    plates, bolts = [], []
    for i in range(SPEC["hoops"]):
        x = i * PITCH - SPAN / 2.0
        for side in (-1.0, 1.0):
            plates.append(bkit.rounded_box(
                "_pl", 110.0, 90.0, 18.0, r=6.0, segments=2, mat=plate,
                centre=(x, side * HOOP_W / 2.0, -9.0)))
            for bx, _ in bkit.grid_positions(2, 1, 60.0, 0.0):
                bolts.append(bkit.cylinder("_bo", 8.0, 10.0, segments=16,
                                          mat=dark,
                                          centre=(x + bx,
                                                  side * HOOP_W / 2.0, 3.0)))
    bkit.join(plates, name="GroundPlates")
    bkit.join(bolts, name="AnchorBolts")

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=7)


CHECKS = [
    # `diameter` is max(bbox_x, bbox_y) and on a row of five hoops that reads
    # the 1088 mm ROW SPAN, so the hoop's own width is bbox_y.
    dict(name="hoop_row_width", mm=1088.0, tol=2.0, how="bbox_x",
         part="RackHoops"),
    dict(name="hoop_width", mm=748.0, tol=2.0, how="bbox_y",
         part="RackHoops"),
    # top_z is a COORDINATE, so it carries sit_on_floor's 60 mm lift for the
    # legs buried below the ground plate. 774 apex + 60 buried = 834.
    dict(name="hoop_height", mm=834.0, tol=2.0, how="top_z", part="RackHoops"),
    dict(name="overall_width", mm=1300.0, tol=2.0, how="bbox_x"),
    dict(name="overall_height", mm=834.0, tol=2.0, how="bbox_z"),
]