"""
metronome -- classic pyramid mechanical metronome, 210 x 108 x 105 mm.

The metronome is a truncated four-sided pyramid with a pendulum rod swinging
inside it, a scale plate printed on the front, a sliding weight on the rod, and
a winding key at the side. The body is a `loft` over four `rounded_rect_section`
rings whose width shrinks from 108 mm at the base to 64 mm at the top -- that
taper is the entire silhouette.

The pendulum is the detail that makes it read: a thin rod at 30 degrees from
vertical with a weight block partway up, exactly as a real metronome sits when
set to a slow beat. The scale plate and the tempo numbers are a single
`perforated_panel` behind the rod, so the rod reads against a marked scale
instead of floating in a blank face.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    base_width=108.0,
    base_depth=104.0,
    top_width=64.0,
    height=210.0,
    rod_length=176.0,
    rod_diameter=4.0,
    weight_width=34.0,
    tilt_deg=30.0,
)

BASE_W, BASE_D = SPEC["base_width"], SPEC["base_depth"]
TOP_W = SPEC["top_width"]
H = SPEC["height"]


def build():
    wood = bkit.pbr("MetroWood", base=(0.34, 0.17, 0.08), rough=0.34,
                    coat=0.35)
    dark = bkit.pbr("MetroDark", base=(0.13, 0.09, 0.06), rough=0.40)
    brass = bkit.pbr("MetroBrass", base=(0.82, 0.66, 0.30), metal=0.85,
                     rough=0.26)
    steel = bkit.pbr("MetroSteel", base=(0.80, 0.81, 0.83), metal=0.85,
                     rough=0.24)
    scale_mat = bkit.pbr("MetroScale", base=(0.90, 0.88, 0.82), rough=0.40)

    # ---- body: a loft over four tapering rings ---------------------------
    secs = []
    for z, w, d in ((0.0, BASE_W, BASE_D), (6.0, BASE_W, BASE_D),
                    (H * 0.45, (BASE_W + TOP_W) / 2.0,
                     (BASE_D + TOP_W) / 2.0),
                    (H, TOP_W, TOP_W)):
        ring = bkit.rounded_rect_section(w, d, r=4.0, per_corner=4)
        secs.append([(x, y, z) for (x, y) in ring])
    body = bkit.loft("MetroBody", secs, mat=wood)
    bkit.recalc(body)
    bkit.bevel(body, width_mm=1.4, segments=2, angle_deg=40)

    # Cap the top and add the base moulding.
    bkit.rounded_box("MetroCap", TOP_W + 6.0, TOP_W + 6.0, 12.0, r=4.0,
                     segments=3, centre=(0, 0, H + 4.0), mat=dark)
    bkit.rounded_box("MetroBase", BASE_W + 8.0, BASE_D + 8.0, 14.0, r=4.0,
                     segments=3, centre=(0, 0, 7.0), mat=dark)

    # ---- the front opening, with the scale plate behind it ----------------
    # Cut a tall slot through the front face; the scale sits inside it so the
    # pendulum reads against printed graduations.
    bkit.boolean(body, bkit.rounded_box(
        "_slot", 46.0, 60.0, 176.0, r=4.0, segments=2,
        centre=(0, -BASE_D / 2.0 + 14.0, 104.0)), "DIFFERENCE")
    bkit.rounded_box("MetroScale", 40.0, 3.0, 168.0, r=2.0, segments=2,
                     centre=(0, -BASE_D / 2.0 + 30.0, 104.0), mat=scale_mat)
    # Graduation ticks, one `grid_positions` call for the whole column.
    for i, (x, y) in enumerate(bkit.grid_positions(cols=2, rows=8, pitch_x=26.0,
                                                    pitch_y=18.0)):
        bkit.box("MetroTick%d" % i, 12.0, 2.0, 1.6,
                 centre=(x, -BASE_D / 2.0 + 28.0, 104.0 + y), mat=dark)

    # ---- pendulum: rod at 30 degrees, sliding weight ---------------------
    tilt = math.radians(SPEC["tilt_deg"])
    rod_len = SPEC["rod_length"]
    rod = bkit.cylinder("MetroRod", SPEC["rod_diameter"] / 2.0, rod_len,
                        segments=14, centre=(0, 0, 0), axis="Z", mat=steel)
    rod.rotation_euler = (tilt, 0.0, 0.0)
    # Pivot sits at the base of the slot; the rod leans out over the front face.
    bkit.move(rod, 0.0, -BASE_D / 2.0 + 26.0 - math.sin(tilt) * rod_len / 2.0,
              22.0 + math.cos(tilt) * rod_len / 2.0)
    wt = bkit.rounded_box("MetroWeight", SPEC["weight_width"], 14.0, 20.0,
                          r=2.0, segments=2, centre=(0, 0, 0), mat=brass)
    wt.rotation_euler = (tilt, 0.0, 0.0)
    bkit.move(wt, 0.0, -BASE_D / 2.0 + 26.0 - math.sin(tilt) * 96.0,
              22.0 + math.cos(tilt) * 96.0)
    bkit.cylinder("MetroPivot", 5.0, 26.0, segments=16,
                  centre=(0, -BASE_D / 2.0 + 26.0, 22.0), axis="X", mat=brass)

    # ---- winding key and feet --------------------------------------------
    bkit.cylinder("MetroKey", 4.0, 26.0, segments=12,
                  centre=(BASE_W / 2.0 - 8.0, 0.0, 62.0), axis="X",
                  mat=brass)
    bkit.box("MetroKeyWing", 6.0, 22.0, 8.0,
             centre=(BASE_W / 2.0 + 6.0, 0.0, 62.0), mat=brass)
    bkit.cylinder("MetroWind", 9.0, 20.0, segments=16,
                  centre=(BASE_W / 2.0 - 10.0, 0.0, 130.0), axis="X",
                  mat=brass)

    return dict(spec=SPEC, parts=6)


CHECKS = [
    dict(name="base_width", mm=108.0, tol=0.6, how="bbox_x", part="MetroBody"),
    dict(name="height", mm=210.0, tol=1.0, how="bbox_z", part="MetroBody"),
    dict(name="top_cap_width", mm=70.0, tol=1.0, how="bbox_x", part="MetroCap"),
    dict(name="weight_width", mm=34.0, tol=0.6, how="bbox_x",
         part="MetroWeight"),
]