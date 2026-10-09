"""
pendant_lamp -- conical ceiling pendant: ceiling rose, a thin flex, and a wide
open-bottom shade with a real wall.

The identifying features of a pendant are all vertical relationships: the shade
hangs mouth-down, its top is much narrower than its rim, and it is separated
from the ceiling by a long thin cord rather than a rigid stem. Getting the cord
thin is the whole silhouette -- a 20 mm stem reads as a ceiling fixture.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    rose_diameter=120.0,     # ceiling rose / canopy
    rose_height=24.0,
    cord_diameter=8.0,
    # The catalog classes this item "small" (30-150 mm, scored out to 300 mm),
    # so the flex is a compact 150 mm rather than the 300 mm+ drop of a real
    # dining pendant. Total height 278 mm, shade mouth 280 mm.
    cord_length=150.0,
    shade_diameter=280.0,    # open mouth
    shade_height=120.0,
    shade_neck_diameter=70.0,
    overall_height=278.0,
)


def _shell(name, loop_profile, centre, mat, segments=96):
    """Lathe a CLOSED profile loop into a walled shell (see desk_lamp)."""
    prof = list(loop_profile) + [loop_profile[0]]
    ob = bkit.lathe(name, prof, segments=segments, centre=centre,
                    mat=mat, cap_ends=False)
    bkit.recalc(ob)
    return ob


def build():
    metal = bkit.preset("brushed_metal")
    cord_mat = bkit.preset("black_plastic")
    enamel = bkit.preset("white_plastic")
    lining = bkit.pbr("ShadeLining", base=(0.94, 0.92, 0.86), rough=0.22)
    glow = bkit.pbr("BulbGlow", base=(1.0, 0.93, 0.78), rough=0.30,
                    emission=(1.0, 0.89, 0.70), emission_strength=7.0)

    rose_h = SPEC["rose_height"]
    cord_len = SPEC["cord_length"]
    sh = SPEC["shade_height"]
    rim_r = SPEC["shade_diameter"] / 2.0
    neck_r = SPEC["shade_neck_diameter"] / 2.0

    # A pendant hangs DOWNWARD from the ceiling. Everything is therefore
    # authored into negative z with the ceiling face at z = 0; sit_on_floor
    # then lifts the assembly until the shade's mouth rests on z = 0, which
    # leaves the ceiling face on top as it should be. Authoring the rose at
    # positive z instead renders the lamp standing on its canopy.
    z_ceil = 0.0

    # ---- ceiling rose: a shallow dome flat against the ceiling -----------
    rose = bkit.lathe("PendantRose", [
        (0.0, 0.0),
        (56.0, 0.0),
        (60.0, 2.0),
        (60.0, 14.0),
        (54.0, 20.0),
        (30.0, rose_h),
        (10.0, rose_h - 2.0),      # boss the flex leaves through
        (10.0, rose_h - 8.0),
        (0.0, rose_h - 8.0),
    ], segments=72, centre=(0.0, 0.0, z_ceil - rose_h), mat=metal)

    # ---- flex: thin and long, the defining vertical proportion -----------
    cord = bkit.cylinder("PendantCord", SPEC["cord_diameter"] / 2.0, cord_len,
                         segments=24,
                         centre=(0.0, 0.0, z_ceil - rose_h - cord_len / 2.0 + 6.0),
                         mat=cord_mat)

    # ---- shade: mouth-down, so the wide rim is the LOWEST point ----------
    cord_bottom = z_ceil - rose_h - cord_len + 6.0
    shade_top = cord_bottom + 10.0                 # the narrow neck
    shade_bottom = shade_top - sh                 # the wide mouth
    shade = _shell("PendantShade", [
        (rim_r - 2.5, 0.0),                # inside of the mouth
        (neck_r - 2.5, sh),                # up the inside
        (neck_r, sh),                      # across the neck rim
        (rim_r, 0.0),                      # down the outside
    ], centre=(0.0, 0.0, shade_bottom), mat=enamel)

    bkit.assign_faces_by(shade, lining,
                         lambda c, n: (c.x ** 2 + c.y ** 2) ** 0.5 / bkit.MM
                         < rim_r - 1.4)

    # ---- lampholder + bulb, INSIDE the mouth --------------------------
    # Placed relative to the neck: the holder hangs below it and the bulb
    # below that. An absolute z put the bulb outside the shade entirely, where
    # it glowed into open air instead of lighting the shade interior.
    holder_top = shade_top - 14.0
    holder = bkit.lathe("PendantHolder", [
        (0.0, 0.0),
        (17.0, 0.0),
        (19.0, 4.0),
        (19.0, 26.0),
        (21.0, 30.0),
        (21.0, 34.0),
        (0.0, 34.0),
    ], segments=48, centre=(0.0, 0.0, holder_top - 34.0), mat=metal)

    bulb = bkit.lathe("PendantBulb", [
        (0.0, 0.0),
        (12.0, 2.0),
        (17.0, 10.0),
        (18.0, 22.0),
        (15.0, 34.0),
        (8.0, 42.0),
        (0.0, 45.0),
    ], segments=48, centre=(0.0, 0.0, holder_top - 92.0), mat=glow)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="rose_diameter", mm=120.0, tol=0.5, how="diameter", part="PendantRose"),
    dict(name="rose_height", mm=24.0, tol=0.4, how="bbox_z", part="PendantRose"),
    dict(name="cord_length", mm=150.0, tol=0.4, how="bbox_z", part="PendantCord"),
    dict(name="shade_diameter", mm=280.0, tol=0.6, how="diameter", part="PendantShade"),
    dict(name="shade_height", mm=120.0, tol=0.4, how="bbox_z", part="PendantShade"),
]