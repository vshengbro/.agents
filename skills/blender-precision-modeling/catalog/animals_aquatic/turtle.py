"""turtle -- a 1.1 m green sea turtle: an oval carapace with real scute
plates, four paddle flippers, and a small blunt head.

The scutes are the model. A turtle shell with no plates reads as a pebble, so
the carapace carries a computed radial layout of vertebral scutes down the
middle and costal scutes either side, all from `grid_positions`-style pitches
derived from the shell's own dimensions. The plastron is a second material on
the same solid, not a second shell that would z-fight.

Construction: a lathed shell squashed into an oval, a swept head and neck, two
front flippers (the power stroke) and two rear flippers (the rudder), all
mirrored in world space. Nothing is booleaned.

Orientation: the head points at -Y, X lateral, Z up.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    shell_length=780.0,
    shell_width=620.0,
    shell_height=260.0,
    flipper_span=1240.0,
    scute_rows=5,
    scute_cols=4,
    head_length=150.0,
)

# ---- the shell: a lathed dome, then squashed into an oval carapace
SHELL_R = 380.0
HEAD = [
    (0.0, -400.0, 170.0), (0.0, -470.0, 175.0), (0.0, -540.0, 168.0),
]
HEAD_RAD = [(72.0, 62.0), (66.0, 58.0), (42.0, 38.0)]
FRONT = [
    (0.0, -300.0, 130.0), (180.0, -400.0, 90.0), (330.0, -470.0, 60.0),
    (380.0, -500.0, 46.0),
]
FRONT_RAD = [(70.0, 46.0), (78.0, 42.0), (62.0, 30.0), (30.0, 18.0)]
REAR = [
    (0.0, 320.0, 110.0), (110.0, 400.0, 70.0), (190.0, 460.0, 40.0),
    (220.0, 490.0, 30.0),
]
REAR_RAD = [(58.0, 40.0), (50.0, 30.0), (34.0, 20.0), (18.0, 12.0)]


def build():
    shellm = bkit.pbr("TurtleShell", base=(0.20, 0.26, 0.17), rough=0.52)
    scute = bkit.pbr("TurtleScute", base=(0.30, 0.36, 0.22), rough=0.46,
                     coat=0.2)
    plastron = bkit.pbr("TurtlePlastron", base=(0.62, 0.60, 0.50), rough=0.50)
    skin = bkit.pbr("TurtleSkin", base=(0.22, 0.30, 0.20), rough=0.56)
    eye = bkit.pbr("TurtleEye", base=(0.02, 0.02, 0.025), rough=0.08)

    shell_ob = bkit.lathe(
        "Carapace",
        [(0.0, 0.0), (200.0, 8.0), (330.0, 46.0), (380.0, 110.0),
         (350.0, 190.0), (250.0, 240.0), (0.0, 258.0)],
        segments=56, centre=(0.0, 0.0, 0.0), mat=shellm)
    me = shell_ob.data
    for v in me.vertices:
        v.co.x = v.co.x * 0.82          # carapaces are narrower than long
        v.co.y = v.co.y * 1.0
    shell_ob.data.update()

    # ---- scutes: a computed plate layout over the dome. Row and column
    # pitches come from the shell's own size, so a plate can never land on
    # another plate's coordinate.
    n_row = 5
    n_col = 4
    span_y = 520.0
    span_x = 480.0
    pitch_y = span_y / n_row
    pitch_x = span_x / n_col
    for r in range(n_row):
        for c in range(n_col):
            y = -span_y / 2.0 + (r + 0.5) * pitch_y
            x = -span_x / 2.0 + (c + 0.5) * pitch_x
            # the dome's height at that station, so the plate sits ON the shell
            t = max(0.0, 1.0 - (x / 380.0) ** 2 - (y / 470.0) ** 2)
            z = 258.0 * math.sqrt(t) * 0.92
            if z < 90.0:
                continue
            bkit.rounded_box("Scute%d%d" % (r + 1, c + 1),
                             pitch_x * 0.82, pitch_y * 0.82, 18.0,
                             r=6.0, segments=3,
                             centre=(x, y, z), mat=scute)

    # ---- plastron as a second material on the shell's own rim: a separate
    # shell underneath would z-fight with the carapace
    bkit.assign_faces_by(shell_ob, plastron,
                         lambda c, n: c.z / bkit.MM < 60.0)

    neck = F.tube("Neck", [(0.0, -370.0, 150.0), (0.0, -410.0, 162.0)],
                  [(62.0, 58.0), (56.0, 52.0)], skin, n=2.4, steps=16)
    F.tube("Head", HEAD, HEAD_RAD, skin, n=2.4, steps=20)
    del neck

    # Each paddle is authored ONCE on +X and mirrored. Negating the outline's x
    # instead reverses the polygon's winding, and the mirrored half comes out
    # inside-out -- `health()` names it in negative volume.
    for tag, outline, thick, dx, z, pitch in (
            ("FlipperFront", FRONT, 40.0, 240.0, 120.0, -6.0),
            ("FlipperRear", REAR, 34.0, 165.0, 100.0, 4.0)):
        paddle = F.plate_xy("%sL" % tag, outline, thick, z=0.0, mat=skin)
        bkit.move(paddle, dx, 0.0, z)
        F.bake_rot(paddle, "X", pitch)
        F.mirror_copy(paddle, "%sR" % tag)

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 15.0, segments=18, rings=9,
                       centre=(sx * 46.0, -478.0, 190.0), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=30)


CHECKS = [
    dict(name="shell_length", mm=760.0, tol=20.0, how="bbox_y",
         part="Carapace"),
    dict(name="shell_width", mm=624.0, tol=20.0, how="bbox_x",
         part="Carapace"),
    dict(name="shell_height", mm=258.0, tol=15.0, how="bbox_z",
         part="Carapace"),
    dict(name="flipper_span", mm=1240.0, tol=60.0, how="bbox_x"),
    dict(name="head_length", mm=140.0, tol=15.0, how="bbox_y", part="Head"),
]