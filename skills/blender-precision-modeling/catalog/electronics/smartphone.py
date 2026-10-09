"""
smartphone -- 146 x 71.5 x 8.1 mm slab phone (6.1" class).

The corner radius is the whole silhouette here, and a uniform `rounded_box`
bevel cannot produce it: the bevel width is clamped by HALF THE THICKNESS, so a
phone would get a 4 mm radius instead of the 8 mm its outline needs. The body
is therefore an `extrude_profile` of a `rounded_rect_section` (2D radius, free
of the thickness clamp) with a small `bevel` afterwards to break the two rim
edges so it still reads as manufactured rather than as a cut sheet.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    length=146.0,
    width=71.5,
    height=8.1,
    corner_radius=8.0,
    screen_diagonal=155.0,
)

L, W, H = SPEC["length"], SPEC["width"], SPEC["height"]
R = SPEC["corner_radius"]


def build():
    # A graphite anodised frame, deliberately NOT near-black: the studio exposes
    # for an 18 % grey ball, so a 0.05 albedo body renders as a silhouette with
    # no form at all. 0.30 is what a real anodised frame measures.
    body_mat = bkit.pbr("PhoneBody", base=(0.30, 0.31, 0.34), rough=0.28,
                        coat=0.35)
    glass = bkit.pbr("PhoneGlass", base=(0.030, 0.033, 0.042), rough=0.06,
                     coat=0.8)
    btn_mat = bkit.pbr("PhoneButton", base=(0.55, 0.56, 0.58), rough=0.36)
    port_mat = bkit.pbr("PhonePort", base=(0.10, 0.10, 0.12), rough=0.5)

    # ---- shell: 2D corner radius, then a thin rim bevel -------------------
    body = bkit.extrude_profile(
        "PhoneBody", bkit.rounded_rect_section(L, W, R),
        H, centre=(0, 0, H / 2.0), mat=body_mat)
    bkit.bevel(body, 0.5, segments=2)

    # ---- display: a real 1.8 mm recess with the glass sitting in it ------
    # The cutter overshoots the top face by more than the recess depth so the
    # cut lands on curved-above-plane geometry; the glass is left 0.1 mm above
    # the recess floor so no two faces are coplanar.
    screen = bkit.extrude_profile(
        "PhoneScreen", bkit.rounded_rect_section(L - 15.0, W - 15.0, R - 3.0),
        1.4, centre=(0, 0, 7.1), mat=glass)
    cut = bkit.extrude_profile(
        "_scr", bkit.rounded_rect_section(L - 14.0, W - 14.0, R - 3.0),
        3.0, centre=(0, 0, 7.8))
    bkit.boolean(body, cut, "DIFFERENCE")

    # ---- side controls: three keys on one computed pitch ------------------
    btns = []
    for i, (x, w) in enumerate(bkit.lay_out([11.0, 11.0, 16.0], gap=5.0)):
        btns.append(bkit.rounded_box(
            "_b%d" % i, w, 2.4, 3.0, r=0.7,
            centre=(x, W / 2.0 - 0.2, 4.6), mat=btn_mat))
    bkit.join(btns, name="PhoneButtons")

    # ---- USB-C receptacle in the short edge ------------------------------
    port = bkit.rounded_box("_port", 3.4, 9.0, 2.6, r=1.2,
                            centre=(-L / 2.0 + 0.4, 0.0, 4.4), mat=port_mat)
    bkit.boolean(body, port, "DIFFERENCE")

    return dict(spec=SPEC, parts=4)


CHECKS = [
    dict(name="length", mm=146.0, tol=0.5, how="bbox_x", part="PhoneBody"),
    dict(name="width", mm=71.5, tol=0.5, how="bbox_y", part="PhoneBody"),
    dict(name="height", mm=8.1, tol=0.4, how="bbox_z", part="PhoneBody"),
]
