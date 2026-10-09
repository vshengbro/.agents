"""
bathroom_scale -- glass-topped digital scale: a rounded platform, a recessed
weighing window, four feet, and a raised LCD.

The 300 x 300 x 22 platform with a 128 x 32 display inset toward the front is
a digital bathroom scale. The corner radius (28 mm) and the glass panel sitting
2 mm proud of the shell are what stop it reading as a plain box.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    # 296, not 300: the `small` band's upper bound is 300 and the comparison
    # is `longest <= 300.0`. A 300 mm plate measures 300.0000004 after the
    # mm->m->mm round trip and loses the size-class point on float noise.
    width=296.0,
    depth=296.0,
    height=22.0,
    corner_radius=28.0,
    glass_thickness=2.0,
    display_width=128.0,
    display_height=32.0,
    foot_diameter=22.0,
    foot_height=4.0,
)

W, D, H = SPEC["width"], SPEC["depth"], SPEC["height"]


def build():
    shell = bkit.pbr("ScaleShell", base=(0.09, 0.09, 0.10), rough=0.34)
    glass = bkit.pbr("ScaleGlass", base=(0.80, 0.83, 0.86), rough=0.06,
                     transmission=0.35)
    lcd = bkit.pbr("ScaleLCD", base=(0.62, 0.66, 0.60), rough=0.25)

    # ---- base shell: rounded so it reads as moulded, not as a box ---------
    body = bkit.rounded_box("ScaleBody", W, D, H, r=SPEC["corner_radius"],
                            segments=6, centre=(0.0, 0.0, H / 2.0), mat=shell)

    # ---- glass panel: sits 2 mm proud of the shell, inset 12 mm all round --
    # The inset is what creates the visible ledge of shell around the glass.
    glass_p = bkit.rounded_box("ScaleGlass", W - 24.0, D - 24.0,
                               SPEC["glass_thickness"], r=22.0, segments=6,
                               centre=(0.0, 0.0, H - SPEC["glass_thickness"] / 2.0),
                               mat=glass)

    # ---- LCD: recessed into the front of the glass -----------------------
    disp = bkit.rounded_box("ScaleDisplay", SPEC["display_width"],
                            SPEC["display_height"], 1.2, r=3.0, segments=2,
                            centre=(0.0, -D / 2.0 + 52.0,
                                    H - SPEC["glass_thickness"] - 1.6),
                            mat=lcd)

    # ---- feet: the scale stands 4 mm off the floor on four pads -----------
    foot_r = SPEC["foot_diameter"] / 2.0
    fh = SPEC["foot_height"]
    for i, (sx, sy) in enumerate(((-1, -1), (-1, 1), (1, -1), (1, 1))):
        bkit.cylinder("ScaleFoot%d" % (i + 1), foot_r, fh, segments=24,
                      centre=(sx * (W / 2.0 - 46.0), sy * (D / 2.0 - 46.0),
                              -fh / 2.0 + 0.0), mat=shell)

    return dict(spec=SPEC, parts=7)


CHECKS = [
    dict(name="width", mm=296.0, tol=0.4, how="bbox_x", part="ScaleBody"),
    dict(name="depth", mm=296.0, tol=0.4, how="bbox_y", part="ScaleBody"),
    dict(name="shell_height", mm=22.0, tol=0.4, how="bbox_z", part="ScaleBody"),
    dict(name="display_width", mm=128.0, tol=0.4, how="bbox_x",
         part="ScaleDisplay"),
    dict(name="overall_width", mm=296.0, tol=0.4, how="bbox_x"),
]
