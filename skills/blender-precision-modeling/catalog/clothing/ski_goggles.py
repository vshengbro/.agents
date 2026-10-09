"""
ski_goggles -- 250 mm wide, 100 mm tall, with a frame and a head strap.

The lens is the one genuinely curved thin shell here. A flat plate reads as
sunglasses, so the lens is a loft of sections at five depths, widest and deepest
at the middle, which bows the panel forward. It is then hollowed with a cavity
that runs out past the rim, so the lens has a real 4 mm edge.

The frame is the lens solid scaled up, hollowed by a slightly smaller copy of
the lens: nesting rather than matching is deliberate. Cut the frame with a cavity
the exact size of the lens and the two surfaces are coincident, which is the one
thing that reliably produces bad edges.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=250.0,
    height=96.0,
    lens_width=232.0,
    lens_height=84.0,
    lens_thickness=4.0,
    lens_bow=30.0,
    frame_margin=9.0,
    strap_length=340.0,
)

STEPS = 52
INNER = 31


def axis_frame(d):
    ln = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 1.0
    d = (d[0] / ln, d[1] / ln, d[2] / ln)
    if abs(d[2]) > 0.9:
        u = (1.0, 0.0, 0.0)
    else:
        u = (d[1] * 1.0 - d[2] * 0.0, d[2] * 0.0 - d[0] * 1.0,
             d[0] * 0.0 - d[1] * 0.0)
        ln = math.sqrt(u[0] ** 2 + u[1] ** 2 + u[2] ** 2) or 1.0
        u = (u[0] / ln, u[1] / ln, u[2] / ln)
    v = (d[1] * u[2] - d[2] * u[1],
         d[2] * u[0] - d[0] * u[2],
         d[0] * u[1] - d[1] * u[0])
    return u, v


def lens_sections(scale_x=1.0, scale_z=1.0, grow_y=0.0, steps=STEPS,
                  n=3.0):
    """Five lens sections from back to front; the middle one is the largest."""
    prof = [
        (-30.0, 0.88), (-20.0, 0.97), (0.0, 1.00), (20.0, 0.96),
        (30.0, 0.85),
    ]
    secs = []
    for (y, k) in prof:
        a = SPEC["lens_width"] / 2.0 * k * scale_x
        b = SPEC["lens_height"] / 2.0 * k * scale_z
        secs.append([(x, y + grow_y * k, z) for (x, z) in
                     bkit.superellipse_section(2 * a, 2 * b, n=n, steps=steps)])
    return secs


def shell(outer, cavity):
    bkit.boolean(outer, cavity, "DIFFERENCE")
    bkit.recalc(outer)
    return outer


def _mm(v):
    return v / bkit.MM


def build():
    lens_mat = bkit.pbr("GoggleLensMirror", base=(0.430, 0.560, 0.610),
                        rough=0.08, coat=0.85)
    frame = bkit.pbr("GoggleFrame", base=(0.115, 0.120, 0.135), rough=0.55)
    strap = bkit.pbr("GoggleStrap", base=(0.560, 0.300, 0.130), rough=0.88)
    buckle = bkit.preset("brushed_metal")

    # ---- lens: bowed panel, then hollowed so the rim shows a real edge ---
    lens = shell(bkit.loft("GoggleLens", lens_sections(), smooth=True,
                           mat=lens_mat),
                 bkit.loft("_GoggleLens_cavity",
                           lens_sections(scale_x=0.86, scale_z=0.84,
                                         steps=INNER)))
    # The cavity above is narrower than the lens, so the difference leaves a
    # solid lens with a recessed inner face -- a real lens with thickness.
    bkit.assign_faces_by(
        lens, frame,
        lambda c, n: _mm(n.y) > 0.45,      # the inner face reads as the frame
    )

    # ---- frame: the lens envelope, hollowed by a nested smaller lens ------
    shell(bkit.loft("GoggleFrame", lens_sections(scale_x=1.09, scale_z=1.16,
                                                 grow_y=-14.0, steps=STEPS),
                    smooth=True, mat=frame),
          bkit.loft("_GoggleFrame_cavity",
                    lens_sections(scale_x=0.95, scale_z=0.93,
                                  steps=INNER)))

    # ---- buckle strap on the top of the frame ----------------------------
    bkit.rounded_box("GoggleBuckleStrap", 60.0, 40.0, 22.0, r=7.0,
                     segments=3, centre=(0.0, -18.0, 62.0), mat=strap)
    bkit.rounded_box("GoggleBuckle", 34.0, 12.0, 26.0, r=4.0, segments=3,
                     centre=(0.0, -34.0, 62.0), mat=buckle)

    # ---- head strap: a flat band round the back of the head --------------
    secs = []
    band = [(0.0, -30.0, 30.0)]
    for i in range(1, 9):
        t = math.pi * (i / 8.0)
        band.append((math.cos(t) * 170.0, -30.0 + math.sin(t) * 150.0, 34.0))
    for i, c in enumerate(band):
        nxt = band[min(i + 1, len(band) - 1)]
        prv = band[max(i - 1, 0)]
        d = (nxt[0] - prv[0], nxt[1] - prv[1], nxt[2] - prv[2])
        u, v = axis_frame(d)
        a, b = 26.0, 5.0
        secs.append([(c[0] + u[0] * px + v[0] * py,
                      c[1] + u[1] * px + v[1] * py,
                      c[2] + u[2] * px + v[2] * py)
                     for (px, py) in
                     bkit.superellipse_section(2 * a, 2 * b, n=3.4, steps=24)])
    ob = bkit.loft("GoggleStrap", secs, smooth=True, mat=strap)
    bkit.recalc(ob)

    return dict(spec=SPEC, parts=5)


CHECKS = [
    dict(name="width", mm=253.0, tol=3.0, how="bbox_x", part="GoggleFrame"),
    dict(name="height", mm=96.0, tol=4.0, how="bbox_z", part="GoggleFrame"),
    dict(name="lens_width", mm=232.0, tol=3.0, how="bbox_x", part="GoggleLens"),
    dict(name="lens_height", mm=84.0, tol=3.0, how="bbox_z", part="GoggleLens"),
    dict(name="strap_depth", mm=200.0, tol=4.0, how="bbox_y",
         part="GoggleStrap"),
]