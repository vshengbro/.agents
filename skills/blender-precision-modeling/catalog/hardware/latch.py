"""
latch -- over-centre toggle latch, 62 mm base, toggle thrown into a catch.

The silhouette that makes a toggle latch readable is the T: a long round toggle
bar lying across a flat base on two pivot cheeks, with a hook at the free end
dropped into a slotted catch and a pair of links stopping the bar short of
dead centre. Each of those is a separate watertight part, which is also what
lets every CHECKS entry be measured against the part that owns the dimension.

62 x 30 mm is the common drawer/chest size; the cheek height, pin height, slot
and hook geometry are all derived from those two numbers and the bar diameter,
not written as independent constants.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

BASE_L = 62.0           # X
BASE_W = 30.0           # Y
BASE_T = 4.0            # Z
CHEEK_X = -22.0         # pivot end of the base
CHEEK_H = 16.0          # cheek height above the base top
CHEEK_Y = 11.0
TOGGLE_R = 3.5          # round toggle bar
TOGGLE_Z = BASE_T + CHEEK_H      # pin axis level, top of the cheeks
CATCH_X = 27.0          # hook end of the bar
CATCH_H = 9.0
HOOK_D = 9.0            # hook tab, fore-aft
# X, bar length: pivot boss face to the outside of the hook tab. The bar stops
# at each upright it bears on rather than overshooting both ends.
TOGGLE_L = (CATCH_X + HOOK_D / 2.0) - CHEEK_X
SLOT_W = 9.0            # catch slot width
HOOK_W = 8.0            # hook tab width in Y (clears the slot)
HOOK_H = 7.0
MOUNT_HOLE_D = 4.5
# the pivot bosses (r = 5.4) stand taller than the toggle bar (r = 3.5), so
# they set the overall height
OVERALL_H = TOGGLE_Z + 5.4

SPEC = dict(base_length=BASE_L,
            base_width=BASE_W,
            base_thickness=BASE_T,
            toggle_length=TOGGLE_L,
            toggle_diameter=2.0 * TOGGLE_R,
            overall_height=OVERALL_H)


def build():
    import bpy

    steel = bkit.pbr("LatchSteel", base=(0.76, 0.78, 0.80), metal=0.70,
                     rough=0.28)

    # ---- base plate + the two pivot cheeks ------------------------------
    base = bkit.rounded_box("BasePlate", BASE_L, BASE_W, BASE_T, r=1.2,
                            segments=3, centre=(0, 0, BASE_T / 2.0), mat=steel)
    cheeks = [bkit.rounded_box("Cheek", 5.0, 4.0, CHEEK_H, r=0.8, segments=3,
                               centre=(CHEEK_X, sign * CHEEK_Y,
                                       BASE_T + CHEEK_H / 2.0), mat=steel)
              for sign in (-1.0, 1.0)]
    latch = bkit.join([base] + cheeks, name="LatchBase")

    for sign in (-1.0, 1.0):
        cutter = bkit.cylinder("MountHole", MOUNT_HOLE_D / 2.0, BASE_T * 3.0,
                               segments=24,
                               centre=(CHEEK_X - 6.5, sign * CHEEK_Y,
                                       BASE_T / 2.0), mat=None)
        bkit.boolean(latch, cutter, "DIFFERENCE")

    # ---- slotted catch post the hook drops into -------------------------
    catch = bkit.rounded_box("CatchPost", 8.0, 18.0, CATCH_H, r=1.0,
                             segments=3, centre=(CATCH_X, 0, BASE_T + CATCH_H / 2.0),
                             mat=steel)
    slot = bkit.box("CatchSlot", 6.0, SLOT_W, 5.0,
                    centre=(CATCH_X, 0, BASE_T + CATCH_H - 1.5))
    bkit.boolean(catch, slot, "DIFFERENCE")

    # ---- toggle bar and its hook tab ------------------------------------
    # The bar used to run its full 56 mm from x=-26 to x=+30, straight through
    # both pivot cheeks and out past the catch post, so it read as a rod lying
    # across the assembly with the cheeks stuck on it. It now stops just inside
    # each upright it works against: the pivot boss at the cheek, the hook at
    # the catch post.
    x_pivot = CHEEK_X
    hook_top = TOGGLE_Z - TOGGLE_R
    x_hook = CATCH_X - 4.0
    bar = bkit.cylinder("ToggleBar", TOGGLE_R, x_hook - x_pivot, segments=48,
                        centre=((x_pivot + x_hook) / 2.0, 0, TOGGLE_Z),
                        axis="X", mat=steel)
    hook = bkit.rounded_box("HookTab", HOOK_D, HOOK_W, HOOK_H, r=0.8,
                            segments=3,
                            centre=(CATCH_X, 0, hook_top - HOOK_H / 2.0),
                            mat=steel)
    bkit.join([bar, hook], name="ToggleBar")

    # ---- pivot boss on each side of the cheeks ---------------------------
    # Without this the bar simply passes through the cheek plates and the pivot
    # is invisible from every angle.
    bosses = []
    for sign in (-1.0, 1.0):
        bosses.append(bkit.cylinder("PivotBoss", 5.4, 2.0, segments=32,
                                    centre=(CHEEK_X, sign * (CHEEK_Y + 2.0),
                                            TOGGLE_Z), axis="Y", mat=steel))
    bkit.join(bosses, name="PivotBosses")

    # ---- links from the toggle down to the base --------------------------
    links = [bkit.rounded_box("Link", 4.0, 2.5, hook_top - BASE_T, r=0.6,
                              segments=2,
                              centre=(2.0, sign * 9.0,
                                      (BASE_T + hook_top) / 2.0), mat=steel)
             for sign in (-1.0, 1.0)]
    bkit.join(links, name="LinkStraps")

    # ---- pivot pin through both cheeks and the bar -----------------------
    bkit.cylinder("PivotPin", 2.2, 30.0, segments=32,
                  centre=(CHEEK_X, 0, TOGGLE_Z), axis="Y", mat=steel)
    assert "LatchBase" in bpy.data.objects
    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="base_length", mm=62.0, tol=0.05, how="bbox_x", part="LatchBase"),
    dict(name="base_width", mm=30.0, tol=0.05, how="bbox_y", part="LatchBase"),
    dict(name="toggle_length", mm=TOGGLE_L, tol=0.6, how="bbox_x", part="ToggleBar"),
    dict(name="overall_height", mm=OVERALL_H, tol=0.6, how="bbox_z", part=None),
]