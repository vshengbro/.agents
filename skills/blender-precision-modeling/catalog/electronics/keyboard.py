"""
keyboard -- full-size 104-key board, 440 x 126 x 28.5 mm.

The count and the layout are the model. A 104 is 61 keys across the five
alphanumeric rows, 13 in the escape/function row, 3 print-screen keys, 6
navigation keys, 17 numpad keys and 4 arrows: 104 in all, and the render only
reads as a keyboard if every one of them sits where a 104 puts it.

Nothing is hand-placed. One pitch (19.05 mm) and one cap gap (1.2 mm) drive
everything: an n-u cap is `n * pitch - gap` wide, the alphanumeric rows tile
their 15 u block exactly through `bkit.lay_out`, the 1 u keys are placed from
their unit offsets, and the two tall numpad keys are `2 * pitch - gap` deep
centred across two rows. There are no booleans in this file, so the caps are
placed geometry and joined -- a keyboard is the one object where 104 separate
solids is the correct topology, not a shortcut.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    width=440.0,
    depth=126.0,
    height=28.5,
    keys=104,
    pitch=19.05,
    cap_gap=1.2,
    cap_height=7.0,
    case_height=22.0,
)

CASE_W, CASE_D, CASE_H = SPEC["width"], SPEC["depth"], SPEC["case_height"]
PITCH, GAP, CAP_H = SPEC["pitch"], SPEC["cap_gap"], SPEC["cap_height"]

# Block origins in key units from the left edge of the typing area. Main 15 u,
# nav 3 u, numpad 4 u -> 22.5 u = 428.6 mm, which leaves 5.7 mm bezels.
U_MAIN, U_NAV, U_NUM = 0.0, 15.25, 18.5
TOTAL_U = 22.5
X0 = -(TOTAL_U * PITCH) / 2.0


def build():
    case_mat = bkit.pbr("KeyCase", base=(0.19, 0.20, 0.22), rough=0.40)
    alpha = bkit.pbr("KeyAlpha", base=(0.30, 0.31, 0.33), rough=0.36)
    mod = bkit.pbr("KeyMod", base=(0.44, 0.45, 0.47), rough=0.34)
    accent = bkit.pbr("KeyAccent", base=(0.68, 0.26, 0.08), rough=0.32)

    case = bkit.rounded_box("KeyboardCase", CASE_W, CASE_D, CASE_H, r=4.0,
                            segments=4, centre=(0, 0, CASE_H / 2.0),
                            mat=case_mat)

    # Six rows, one pitch apart, centred so the front and rear bezels match.
    ys = [48.0 - r * PITCH for r in range(6)]
    zc = CASE_H + CAP_H / 2.0 - 0.5

    main, nav, num = [], [], []

    def unit_keys(out, u_offsets, y, mat, tag, w_u=1.0, d_u=1.0):
        """1 u (or w_u x d_u) caps centred on their unit offsets."""
        w, d = w_u * PITCH - GAP, d_u * PITCH - GAP
        for i, u in enumerate(u_offsets):
            out.append(bkit.rounded_box(
                "%s%d" % (tag, i), w, d, CAP_H, r=1.5, segments=2,
                centre=(X0 + (u + w_u / 2.0) * PITCH, y, zc), mat=mat))

    def tiled_row(out, widths_u, mats, u_start, y, tag, d_u=1.0):
        """A row that tiles its block exactly: one lay_out, one gap."""
        d = d_u * PITCH - GAP
        for i, (x, w) in enumerate(bkit.lay_out(
                [u * PITCH - GAP for u in widths_u], gap=GAP, centre=False)):
            out.append(bkit.rounded_box(
                "%s%d" % (tag, i), w, d, CAP_H, r=1.5, segments=2,
                centre=(X0 + u_start * PITCH + x, y, zc), mat=mats[i]))

    # ---- row 0: Esc + F1..F12 (13), then print-screen, then numpad row ---
    # The function row does not tile at 1 u -- the groups are separated by a
    # spare key position -- so it is placed from unit offsets instead.
    unit_keys(main, [0.0, 2.0, 3.0, 4.0, 5.0, 6.5, 7.5, 8.5, 9.5,
                     11.0, 12.0, 13.0, 14.0], ys[0], mod, "kf")
    unit_keys(nav, [U_NAV, U_NAV + 1.0, U_NAV + 2.0], ys[0], mod, "kp0")
    unit_keys(num, [U_NUM, U_NUM + 1.0, U_NUM + 2.0, U_NUM + 3.0], ys[0],
              mod, "kn0")

    # ---- rows 1-5: the 61 alphanumeric keys, real widths ------------------
    A = [alpha] * 13 + [mod]                       # 1..= then Backspace
    B = [mod] + [alpha] * 12 + [mod]               # Tab, QWERTY..], \
    C = [mod] + [alpha] * 11 + [mod]               # Caps, ASDF..', Enter
    D = [mod] + [alpha] * 10 + [mod]               # Shift, ZXCV../, Shift
    E = [mod] * 8                                  # Ctrl Win Alt Space ...
    tiled_row(main, [1.0] * 13 + [2.0], A, U_MAIN, ys[1], "kr1")
    tiled_row(main, [1.5] + [1.0] * 12 + [1.5], B, U_MAIN, ys[2], "kr2")
    tiled_row(main, [1.75] + [1.0] * 11 + [2.25], C, U_MAIN, ys[3], "kr3")
    tiled_row(main, [2.25] + [1.0] * 10 + [2.75], D, U_MAIN, ys[4], "kr4")
    tiled_row(main, [1.25] * 3 + [6.25] + [1.25] * 4, E, U_MAIN, ys[5], "kr5")

    # ---- nav cluster: 6 keys, two rows of three --------------------------
    for r in (2, 4):
        unit_keys(nav, [U_NAV, U_NAV + 1.0, U_NAV + 2.0], ys[r], mod, "knv")
    # ---- arrow inverted-T in the space a tenkeyless board leaves empty ----
    unit_keys(nav, [U_NAV + 1.0], ys[4], mod, "kar")
    unit_keys(nav, [U_NAV, U_NAV + 1.0, U_NAV + 2.0], ys[5], mod, "kar")

    # ---- numpad: 15 square keys + the two that are two rows tall ---------
    unit_keys(num, [U_NUM, U_NUM + 1.0, U_NUM + 2.0], ys[1], alpha, "kn1")
    unit_keys(num, [U_NUM, U_NUM + 1.0, U_NUM + 2.0], ys[2], alpha, "kn2")
    unit_keys(num, [U_NUM, U_NUM + 1.0, U_NUM + 2.0], ys[3], alpha, "kn3")
    tiled_row(num, [2.0, 1.0], [alpha, alpha], U_NUM, ys[4], "kn4")
    for r in (1, 3):
        num.append(bkit.rounded_box(
            "knt%d" % r, PITCH - GAP, 2 * PITCH - GAP, CAP_H, r=1.5,
            segments=2,
            centre=(X0 + (U_NUM + 3.5) * PITCH, (ys[r] + ys[r + 1]) / 2.0, zc),
            mat=accent))

    bkit.join(main, name="KeyboardMainKeys")
    bkit.join(nav, name="KeyboardNavKeys")
    bkit.join(num, name="KeyboardNumpadKeys")

    return dict(spec=SPEC, parts=4, keys=len(main) + len(nav) + len(num))


CHECKS = [
    dict(name="width", mm=440.0, tol=0.6, how="bbox_x", part="KeyboardCase"),
    dict(name="depth", mm=126.0, tol=0.6, how="bbox_y", part="KeyboardCase"),
    dict(name="case_height", mm=22.0, tol=0.5, how="bbox_z",
         part="KeyboardCase"),
    dict(name="overall_height", mm=28.5, tol=0.5, how="bbox_z"),
]
