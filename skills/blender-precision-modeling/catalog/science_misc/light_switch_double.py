"""light_switch_double -- an 86 mm double light switch: the plate with its
rounded corners and the two real rocker mechanisms, the two rockers at their
real rocker angles, and the screw holes.

The rockers are the model. A rocker switch is not a button -- each rocker is
tilted so its top edge is pressed in, and the tilt is what makes it read as a
switch. Here each rocker is a wedge tilted about its long axis by the real
rocker angle, and the pair sits at the real spacing on a standard 1-gang plate.

Construction: the plate is a rounded box with two rocker apertures cut through
it, each rocker is a wedge tilted about Y by the rocker angle, and the fixings
are two screw holes cut through the plate.

Orientation: the plate in the X-Z plane on the wall at y=0, rockers standing
proud toward -Y, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))

import bpy
import bkit

SPEC = dict(
    plate_width=86.0,
    plate_height=86.0,
    plate_depth=8.0,
    rocker_width=28.0,
    rocker_height=44.0,
    rocker_spacing=44.0,
    rocker_angle=7.0,
)

PW, PH, PD = 86.0, 86.0, 8.0
RW, RH = 28.0, 44.0
SPACING = 44.0
ANGLE = 7.0


def build():
    plate_m = bkit.pbr("SwitchPlate", base=(0.90, 0.89, 0.87), rough=0.30)
    rocker_m = bkit.pbr("SwitchRocker", base=(0.93, 0.93, 0.91), rough=0.22,
                        coat=0.3)
    dark = bkit.pbr("SwitchDark", base=(0.10, 0.10, 0.11), rough=0.50)

    plate = bkit.rounded_box("Plate", PW, PD, PH, r=4.0, segments=4,
                             centre=(0.0, 0.0, 0.0), mat=plate_m)

    # ---- the two rocker apertures. Each cutter is 1 mm proud of the plate on
    # every side, so the two surfaces CROSS instead of ending flush -- a cutter
    # exactly the aperture size touches tangentially and leaves bad edges.
    for side, sx in (("L", -1.0), ("R", 1.0)):
        bkit.boolean(plate, bkit.rounded_box(
            "_ap%s" % side, RW + 2.0, PD + 8.0, RH + 2.0, r=2.0, segments=3,
            centre=(sx * SPACING / 2.0, 0.0, 0.0)), "DIFFERENCE")

    # ---- the two rocker mechanisms behind the plate
    for side, sx in (("L", -1.0), ("R", 1.0)):
        bkit.rounded_box("Body%s" % side, RW + 3.0, 12.0, RH + 3.0, r=1.6,
                         segments=3, centre=(sx * SPACING / 2.0, 4.0, 0.0),
                         mat=dark)

        # ---- the rocker itself: a wedge tilted about its long (Z) axis by
        # the real rocker angle, which is what makes it read as a switch
        rocker = bkit.rounded_box("Rocker%s" % side, RW, 5.0, RH, r=1.2,
                                  segments=3, centre=(0.0, 0.0, 0.0),
                                  mat=rocker_m)
        for v in rocker.data.vertices:
            x, y, z = v.co.x, v.co.y, v.co.z
            a = math.radians(ANGLE)
            ca, sa = math.cos(a), math.sin(a)
            v.co = (x + bkit.u(sx * SPACING / 2.0),
                    y * ca + z * sa + bkit.u(-1.6),
                    -y * sa + z * ca)
        rocker.data.update()
        bkit.recalc(rocker)

    # ---- the two fixing screws, at the plate's real 60 mm centres
    for side, sx in (("L", -1.0), ("R", 1.0)):
        bkit.bore(plate, radius=1.6, depth=PD + 8.0,
                  centre=(sx * 30.0, 0.0, 0.0), axis="Y", host_segments=48)
        bkit.cylinder("Screw%s" % side, 1.4, 1.6, segments=16,
                      centre=(sx * 30.0, -PD / 2.0 - 0.6, 0.0), axis="Y",
                      mat=dark)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=10)


CHECKS = [
    dict(name="plate_width", mm=86.0, tol=1.0, how="bbox_x", part="Plate"),
    dict(name="plate_height", mm=86.0, tol=1.0, how="bbox_z", part="Plate"),
    dict(name="plate_depth", mm=8.0, tol=0.6, how="bbox_y", part="Plate"),
    dict(name="rocker_width", mm=28.0, tol=0.8, how="bbox_x",
         part="RockerL"),
    dict(name="rocker_height", mm=44.0, tol=0.8, how="bbox_z",
         part="RockerL"),
    dict(name="overall_width", mm=86.0, tol=1.5, how="bbox_x"),
]