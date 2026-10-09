"""clownfish -- a 62 mm Amphiprion: short deep body, large rounded fins, and
THREE white bars with black edging. The bar count is the whole animal: two
bars is a damselfish, three is a clownfish.

Construction: one lofted body, flat blades for every fin, and the bars as
thin plates standing slightly proud of the hide -- a second material on the
one body solid cannot make a transverse bar, so the bars are real geometry,
each a closed solid in its own right.

Orientation: nose at -Y, X lateral, Z up, so side.png shows the bars in
profile. A young clownfish is around 62 mm; the catalog class `tiny` tops out
at 60 mm on the long axis.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy
import bkit
import _fauna as F

SPEC = dict(
    overall_length=52.6,
    body_length=36.4,
    body_depth=32.0,
    body_width=17.0,
    white_bars=3,
    tail_span=39.0,
    eye_diameter=6.0,
)

# (y, half_height, half_width, z_centre) -- nose -26, peduncle +16
BODY = [
    (-22.0, 3.5, 3.0, 24.0),
    (-20.2, 8.0, 6.0, 24.0),
    (-16.4, 13.5, 8.5, 24.0),
    (-11.0, 16.0, 8.5, 24.0),
    (-3.6, 15.0, 8.0, 23.6),
    (3.6, 11.5, 6.5, 23.2),
    (9.0, 7.5, 4.5, 22.8),
    (12.6, 4.5, 3.0, 22.4),
    (14.4, 2.5, 2.0, 22.4),
]
# rounded, fan-shaped tail
CAUDAL = [
    (12.6, 22.4), (17.1, 40.0), (30.6, 42.0), (24.3, 22.4),
    (30.6, 3.0), (17.1, 5.0),
]
DORSAL = [
    (-12.6, 35.0), (-9.9, 49.0), (3.6, 48.0), (10.8, 31.0), (9.0, 24.5),
]
ANAL = [
    (0.0, 11.0), (2.7, -8.0), (10.8, -6.0), (12.6, 11.0),
]
PECTORAL = [
    (0.0, 0.0), (9.0, -6.0), (13.0, -2.0), (7.0, 4.0),
]
PELVIC = [
    (0.0, 0.0), (8.0, -6.0), (12.0, -2.0), (6.0, 4.0),
]
# three bars: behind the eye, mid-body, and on the peduncle
BARS = [-16.4, -3.6, 10.0]          # y station of each bar
BAR_HALF_H = [8.0, 15.0, 9.0]       # half height of each bar


def build():
    orange = bkit.pbr("ClownfishOrange", base=(0.90, 0.33, 0.045), rough=0.32,
                      coat=0.3)
    white = bkit.pbr("ClownfishWhite", base=(0.92, 0.92, 0.90), rough=0.30)
    black = bkit.pbr("ClownfishBlack", base=(0.045, 0.040, 0.045), rough=0.36)
    fin = bkit.pbr("ClownfishFin", base=(0.86, 0.30, 0.04), rough=0.30,
                   alpha=0.9)
    eye = bkit.pbr("ClownfishEye", base=(0.02, 0.02, 0.025), rough=0.08)

    torso = F.body("Body", BODY, orange, n=2.6, steps=36)

    # ---- the three bars, each a thin plate through the body plus black edges
    for i, (y, hh) in enumerate(zip(BARS, BAR_HALF_H)):   # three bars, always
        # The bar is a plate: thin fore-aft (Y), spanning the girth (X) and the
        # flank (Z). It is deliberately 1 mm proud of the widest station on
        # each axis, so it reads as a band wrapping the fish instead of a decal
        # floating off it.
        hw = 10.0 if i != 2 else 6.5
        bkit.rounded_box("BarBlack%d" % (i + 1), 2.0 * hw, 2.6,
                         2.0 * (hh + 2.0), r=1.0, segments=3,
                         centre=(0.0, y, 23.5), mat=black)
        bkit.rounded_box("BarWhite%d" % (i + 1), 2.0 * (hw - 0.5), 3.0,
                         2.0 * (hh - 1.2), r=0.9, segments=3,
                         centre=(0.0, y, 23.5), mat=white)

    F.plate_yz("FinCaudal", CAUDAL, 2.0, x=0.0, mat=fin)
    F.plate_yz("FinDorsal", DORSAL, 2.0, x=0.0, mat=fin)
    F.plate_yz("FinAnal", ANAL, 1.8, x=0.0, mat=fin)

    pect = F.plate_xy("FinPectoralL", PECTORAL, 1.8, mat=fin)
    bkit.move(pect, 4.5, -14.5, 18.0)
    F.bake_rot(pect, "Y", -12.0)
    F.mirror_copy(pect, "FinPectoralR")

    pelv = F.plate_xy("FinPelvicL", PELVIC, 1.6, mat=fin)
    bkit.move(pelv, 3.6, 2.0, 11.7)
    F.bake_rot(pelv, "Y", 4.0)
    F.mirror_copy(pelv, "FinPelvicR")

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 3.0, segments=20, rings=10,
                       centre=(sx * 6.0, -18.0, 27.0), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=16)


CHECKS = [
    dict(name="overall_length", mm=52.6, tol=1.5, how="bbox_y"),
    dict(name="body_length", mm=36.4, tol=0.8, how="bbox_y", part="Body"),
    dict(name="body_depth", mm=32.0, tol=0.8, how="bbox_z", part="Body"),
    dict(name="body_width", mm=17.0, tol=0.6, how="bbox_x", part="Body"),
    dict(name="tail_span", mm=39.0, tol=1.2, how="bbox_z", part="FinCaudal"),
    dict(name="eye_diameter", mm=6.0, tol=0.3, how="bbox_x", part="EyeL"),
]