"""tuna -- a 1.1 m bluefin: the classic fusiform "torpedo", crescent lunate tail
that is the fastest-caudal shape in the water, and the finlets: a row of eight
small blades behind the second dorsal and five behind the anal.

Those finlets are the species cue. A tuna with a smooth peduncle reads as any
large fish; a tuna with two finlet combs reads unmistakably as a tuna. They are
built with `grid_positions` on an explicit pitch rather than hand-placed, so
the comb is even and no two blades land on the same coordinate.

Construction: one lofted body, flat blades for every fin, and each paired part
built once then mirrored in world space. Every part is a closed solid, so
nothing is booleaned and the mesh stays watertight part by part.

Orientation: nose at -Y, X lateral, Z up, so side.png shows the profile.
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
    overall_length=1100.0,
    body_length=780.0,
    body_depth=300.0,
    body_width=180.0,
    caudal_span=380.0,
    dorsal_finlets=8,
    anal_finlets=5,
)

# (y, half_height, half_width, z_centre) -- nose -560, peduncle +220
BODY = [
    (-560.0, 16.0, 12.0, 260.0),
    (-535.0, 55.0, 36.0, 260.0),
    (-480.0, 100.0, 62.0, 260.0),
    (-400.0, 138.0, 86.0, 260.0),
    (-290.0, 150.0, 90.0, 260.0),
    (-150.0, 140.0, 84.0, 258.0),
    (-20.0, 112.0, 68.0, 255.0),
    (90.0, 78.0, 48.0, 252.0),
    (170.0, 52.0, 32.0, 250.0),
    (220.0, 30.0, 20.0, 250.0),
]
# lunate caudal: two equal crescents, the trailing edge a deep notch
CAUDAL = [
    (200.0, 250.0), (290.0, 430.0), (540.0, 440.0), (430.0, 250.0),
    (540.0, 60.0), (290.0, 70.0),
]
DORSAL1 = [
    (-320.0, 380.0), (-270.0, 470.0), (-170.0, 470.0), (-160.0, 350.0),
    (-250.0, 350.0),
]
DORSAL2 = [
    (-40.0, 320.0), (0.0, 390.0), (80.0, 375.0), (60.0, 300.0),
]
ANAL1 = [
    (60.0, 180.0), (100.0, 80.0), (170.0, 90.0), (170.0, 180.0),
]
PECTORAL = [
    (0.0, 0.0), (105.0, -95.0), (175.0, -70.0), (120.0, 25.0),
]
PELVIC = [
    (0.0, 0.0), (75.0, -55.0), (115.0, -40.0), (80.0, 15.0),
]
KEEL = [
    (0.0, 0.0), (70.0, -60.0), (110.0, -45.0), (75.0, 12.0),
]


def build():
    back = bkit.pbr("TunaBack", base=(0.045, 0.085, 0.175), rough=0.28,
                    coat=0.3)
    flank = bkit.pbr("TunaFlank", base=(0.55, 0.60, 0.66), rough=0.34)
    belly = bkit.pbr("TunaBelly", base=(0.86, 0.87, 0.88), rough=0.38)
    fin = bkit.pbr("TunaFin", base=(0.06, 0.10, 0.18), rough=0.30)
    finlet = bkit.pbr("TunaFinlet", base=(0.10, 0.14, 0.22), rough=0.30)
    eye = bkit.pbr("TunaEye", base=(0.02, 0.02, 0.025), rough=0.08)

    torso = F.body("Body", BODY, back, n=2.8, steps=40)
    # two materials on ONE solid: a second shell would z-fight with the hide
    bkit.assign_faces_by(torso, belly,
                         lambda c, n: c.z / bkit.MM < 218.0)
    bkit.assign_faces_by(torso, flank,
                         lambda c, n: 218.0 <= c.z / bkit.MM < 300.0)

    F.plate_yz("FinCaudal", CAUDAL, 14.0, x=0.0, mat=fin)
    F.plate_yz("FinDorsal1", DORSAL1, 12.0, x=0.0, mat=fin)
    F.plate_yz("FinDorsal2", DORSAL2, 10.0, x=0.0, mat=fin)
    F.plate_yz("FinAnal", ANAL1, 10.0, x=0.0, mat=fin)

    pect = F.plate_xy("FinPectoralL", PECTORAL, 10.0, mat=fin)
    bkit.move(pect, 62.0, -280.0, 150.0)
    F.bake_rot(pect, "Y", -10.0)
    F.mirror_copy(pect, "FinPectoralR")

    pelv = F.plate_xy("FinPelvicL", PELVIC, 8.0, mat=fin)
    bkit.move(pelv, 34.0, 60.0, 190.0)
    F.bake_rot(pelv, "Y", 6.0)
    F.mirror_copy(pelv, "FinPelvicR")

    # ---- the finlet combs: the tuna's signature. Each comb's span and blade
    # count are real, so the pitch is DERIVED (span / count) instead of typed in
    # eight times -- eight hand-placed constants are exactly how a comb ends up
    # with two blades on one coordinate.
    dorsal_span, dorsal_n = 182.0, 8
    dorsal_pitch = dorsal_span / (dorsal_n - 1)
    for j in range(dorsal_n):
        F.plate_yz("FinletD%d" % (j + 1),
                   [(0.0, 0.0), (-6.0, 20.0), (0.0, 25.0)], 5.0,
                   x=0.0, mat=finlet)
        ob = bpy.data.objects["FinletD%d" % (j + 1)]
        F.bake_rot(ob, "Z", 90.0)
        bkit.move(ob, 0.0, -60.0 + j * dorsal_pitch, 316.0)

    anal_span, anal_n = 96.0, 5
    anal_pitch = anal_span / (anal_n - 1)
    for j in range(anal_n):
        F.plate_yz("FinletA%d" % (j + 1),
                   [(0.0, 0.0), (-5.0, 18.0), (0.0, 22.0)], 5.0,
                   x=0.0, mat=finlet)
        ob = bpy.data.objects["FinletA%d" % (j + 1)]
        F.bake_rot(ob, "Z", -90.0)
        bkit.move(ob, 0.0, 196.0 + j * anal_pitch, 210.0)

    # lateral keels either side of the tail base
    keel = F.plate_xy("KeelL", KEEL, 6.0, mat=finlet)
    bkit.move(keel, 40.0, 230.0, 220.0)
    F.mirror_copy(keel, "KeelR")

    for side, sx in (("L", 1.0), ("R", -1.0)):
        bkit.uv_sphere("Eye%s" % side, 26.0, segments=20, rings=12,
                       centre=(sx * 44.0, -486.0, 300.0), mat=eye)

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=32)


CHECKS = [
    dict(name="overall_length", mm=1100.0, tol=25.0, how="bbox_y"),
    dict(name="body_length", mm=780.0, tol=15.0, how="bbox_y", part="Body"),
    dict(name="body_depth", mm=300.0, tol=12.0, how="bbox_z", part="Body"),
    dict(name="body_width", mm=180.0, tol=8.0, how="bbox_x", part="Body"),
    dict(name="caudal_span", mm=380.0, tol=12.0, how="bbox_z",
         part="FinCaudal"),
    dict(name="pectoral_span", mm=470.0, tol=15.0, how="bbox_x"),
]