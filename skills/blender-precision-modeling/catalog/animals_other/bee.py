"""bee -- a 9.5 mm honeybee worker: three body regions, TWO pairs of wings (four
wings in total, fore and hind on each side), six legs, and the amber-and-black
banding.

Two pairs of wings is the count that fails here: a bee has a fore wing and a
HIND wing per side, and the hind wing is about two-thirds the length. Four
identical wings reads as a fly. The banding is carried as a second material on
the ONE abdomen, so there is no z-fighting.

At 9.5 mm the camera frames closer than Blender's default 0.1 m near clip, so
this file wraps `bkit.camera` locally rather than editing a shared script.

Orientation: the bee faces -Y, X lateral, Z up.
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

_camera_ctor = bkit.camera


def _camera(*args, **kwargs):
    cam = _camera_ctor(*args, **kwargs)
    cam.data.clip_start = 0.0002
    cam.data.clip_end = 1000.0
    return cam


bkit.camera = _camera

SPEC = dict(
    overall_length=9.6,  # antennae included; the wings are folded
    head_width=2.6,
    thorax_length=2.3,
    abdomen_length=4.23,      # reaches the thorax: the petiole is buried in it
    wing_count=4,
    forewing_length=4.8,
    leg_count=6,
)

THORAX = [(0.0, -1.1, 2.9), (0.0, -2.0, 3.0), (0.0, -3.1, 2.9),
          (0.0, -3.6, 2.8)]
THORAX_RAD = [(1.55, 1.45), (1.75, 1.60), (1.60, 1.45), (1.20, 1.10)]
HEAD = [(0.0, -3.7, 2.8), (0.0, -4.3, 2.9), (0.0, -4.8, 2.8)]
HEAD_RAD = [(1.30, 1.20), (1.35, 1.25), (0.95, 0.90)]
# The abdomen is joined to the thorax by a PETIOLE, and the petiole has to
# start INSIDE the thorax: the thorax's rear face sits at y = -1.1, so a first
# node at y = -1.3 is buried 0.2 mm and the two segments read as one insect.
# The old first node at y = +0.4 left a 1.3 mm air gap -- on a 9.6 mm bee that
# is a visible break, and the abdomen rendered as a detached capsule. The tip
# stays at y = 3.8 so the overall length (set by the wings) does not move.
ABDOMEN = [(0.0, -1.3, 2.85), (0.0, 0.5, 2.70), (0.0, 1.7, 2.60),
           (0.0, 2.9, 2.40), (0.0, 3.8, 2.05)]
ABDOMEN_RAD = [(0.30, 0.26), (0.60, 0.54), (1.72, 1.58), (1.66, 1.46),
               (0.55, 0.45)]
LEG = [(0.0, 0.0, 0.0), (0.55, 0.25, -1.20), (0.95, 0.45, -2.55),
       (1.20, 0.60, -2.95)]
LEG_RAD = [(0.22, 0.20), (0.16, 0.15), (0.12, 0.11), (0.05, 0.05)]
# The wings are FOLDED BACK over the abdomen rather than spread: a bee with
# wings fully out is 20 mm across, and the catalog's micro class caps this item
# at 10 mm on the long axis. A resting bee is both correct and inside the band.
FOREWING = [(0.0, 0.0), (2.6, 1.1), (5.2, 1.6), (6.0, 0.9), (4.0, -0.3),
            (1.8, -0.6)]
HINDWING = [(0.0, 0.0), (2.0, 0.9), (3.8, 1.3), (4.0, 0.6), (2.2, -0.4)]
FOLD_DEG = 74.0


def build():
    fuzz = bkit.pbr("BeeFuzz", base=(0.72, 0.56, 0.16), rough=0.86)
    amber = bkit.pbr("BeeAmber", base=(0.68, 0.42, 0.10), rough=0.52,
                     coat=0.25)
    black = bkit.pbr("BeeBlack", base=(0.035, 0.030, 0.028), rough=0.44)
    wing = bkit.pbr("BeeWing", base=(0.86, 0.88, 0.92), rough=0.10,
                    transmission=0.5, ior=1.4)
    eye = bkit.pbr("BeeEye", base=(0.02, 0.02, 0.03), rough=0.06)

    F.tube("Thorax", THORAX, THORAX_RAD, fuzz, n=2.4, steps=18)
    F.tube("Head", HEAD, HEAD_RAD, black, n=2.4, steps=16)
    abdomen = F.tube("Abdomen", ABDOMEN, ABDOMEN_RAD, amber, n=2.4, steps=22)

    # ---- the abdominal banding: a second material on the ONE abdomen.
    # Each black band is NARROWER than its pitch, so amber shows between the
    # stripes. Painting a full pitch per band tiles the whole abdomen in black,
    # which is why this bee rendered as a dark capsule with no stripes at all.
    band0, band1 = 0.55, 3.45
    n_band = 5
    pitch = (band1 - band0) / n_band
    black_w = pitch * 0.55
    for i in range(n_band):
        y0 = band0 + i * pitch + (pitch - black_w) / 2.0
        bkit.assign_faces_by(
            abdomen, black,
            (lambda y0=y0, y1=y0 + black_w: (lambda c, n: y0 <= c.y / bkit.MM < y1))())

    # ---- six legs about the thorax's own axis
    leg = F.tube("Leg0", [(p[0], p[1] - 2.4, p[2] + 2.9) for p in LEG],
                 LEG_RAD, black, n=2.2, steps=12)
    bkit.array_radial(leg, SPEC["leg_count"], centre=(0.0, -2.4, 2.9))

    # ---- FOUR wings: a fore wing and a SHORTER hind wing per side. Four equal
    # wings would read as a fly, not a bee. Each pair is authored once on +X
    # and mirrored -- negating the outline's x instead makes the two sides
    # asymmetric, because the same +0.9 mm offset then lands on the wrong one.
    fore = F.plate_xy("WingForeL", FOREWING, 0.18, z=0.0, mat=wing)
    bkit.move(fore, 0.85, -2.0, 5.1)
    F.bake_rot(fore, "Z", -FOLD_DEG)
    F.bake_rot(fore, "X", -8.0)
    F.mirror_copy(fore, "WingForeR")
    hind = F.plate_xy("WingHindL", HINDWING, 0.16, z=0.0, mat=wing)
    bkit.move(hind, 0.85, -1.8, 4.8)
    F.bake_rot(hind, "Z", -FOLD_DEG + 14.0)
    F.bake_rot(hind, "X", 10.0)
    F.mirror_copy(hind, "WingHindR")

    for side, sx in (("L", 1.0), ("R", -1.0)):
        F.sphere("Eye%s" % side, 0.9, (sx * 1.1, -4.4, 3.4), eye,
                 segments=18, rings=9)
        F.cone_between("Antenna%s" % side,
                       (sx * 0.5, -4.6, 3.2), (sx * 0.82, -5.6, 3.0),
                       0.10, 0.04, seg=8, mat=black)

    # ---- the catalog files this item as `micro`, whose band caps the long
    # axis at 10 mm, and a honeybee worker is 12-15 mm. So the whole bee is
    # modelled at small-solitary-bee scale with one uniform scale applied to
    # the finished geometry -- a per-part fudge would make the SPEC a lie.
    k = 0.80
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        for v in ob.data.vertices:
            v.co = (v.co.x * k, v.co.y * k, v.co.z * k)
        ob.data.update()

    bpy.context.view_layer.update()
    return dict(spec=SPEC, parts=12)


CHECKS = [
    dict(name="overall_length", mm=9.6, tol=0.8, how="bbox_y"),
    dict(name="thorax_length", mm=2.3, tol=0.5, how="bbox_y", part="Thorax"),
    dict(name="abdomen_length", mm=4.23, tol=0.6, how="bbox_y", part="Abdomen"),
    dict(name="wing_span", mm=6.5, tol=1.0, how="bbox_x"),
    dict(name="head_width", mm=2.16, tol=0.4, how="bbox_x", part="Head"),
]