#!/usr/bin/env python3
"""Compare an orthographic face render against a vendor reference image.

Answers "how far is this face from the real one?" with numbers instead of an
opinion. Both images are cropped to their own chassis and reduced to
dark-pixel share per horizontal band and per vertical column; the comparison is
then position- and scale-independent, so the only thing that can move a number
is a real difference in the model.

Use with `blender_ortho_faces.py`, which produces the render side. A beauty
render cannot be used here: perspective and bounding-box auto-framing report a
19.7 x 9.5 cm chassis at h/w 0.75, and every number derived from that frame is
confidently wrong.

    python3 face_diff.py renders/ortho/rear.png reference/hw_back.jpg rear

Two harness traps this script already handles, both of which otherwise yield a
plausible-looking wrong answer:

  * Background disagreement. Vendor diagrams sit on white, ortho renders on
    whatever world colour was set. Thresholding "bright = object" captures the
    whole frame on the second. The background side is decided from the border
    median, then a narrow band is taken on the other side of it — a wide
    window around the metal swallows both (world 175, lit aluminium 163).
  * Silent crop failure. The chassis h/w is printed first and compared to the
    published proportion. If it disagrees, the crop failed and no band number
    from that run means anything.
"""
import sys

import numpy as np
from PIL import Image

BANDS = 20
#: fraction of the shorter axis a row/column must cover to count as chassis
COVER = 0.10
#: published proportions, cm, of the reference part: (width, depth, height)
DEFAULT_SPEC = (19.70, 19.70, 9.50)
#: bands differing by more than this many points are called out
TOLERANCE = 12.0


def chassis_crop(path, dark=95, metal_lo=150, metal_hi=172, cover=COVER):
    """Return (grayscale, dark-mask, (width_px, height_px)) for the chassis."""
    a = np.asarray(Image.open(path).convert("L"), float)
    h, w = a.shape

    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = float(np.median(border))
    if bg > 200:
        # white paper behind the object
        obj = a < bg - 12
    else:
        # flat world colour behind the object; the metal sits just below it
        obj = (a >= metal_lo) & (a <= metal_hi)

    rows = np.where(obj.sum(axis=1) > w * cover)[0]
    cols = np.where(obj.sum(axis=0) > h * cover)[0]
    if not len(rows) or not len(cols):
        raise SystemExit("no chassis found in %s (bg median %.0f)" % (path, bg))
    y0, y1, x0, x1 = rows[0], rows[-1], cols[0], cols[-1]

    sub = a[y0:y1 + 1, x0:x1 + 1]
    return sub, sub < dark, (x1 - x0, y1 - y0)


def profile(mask, axis=0, n=BANDS):
    out = []
    extent = mask.shape[axis]
    for i in range(n):
        lo, hi = int(extent * i / n), int(extent * (i + 1) / n)
        seg = mask[lo:hi] if axis == 0 else mask[:, lo:hi]
        out.append(seg.mean() * 100.0)
    return out


def _table(title, mine, apple):
    step = 100 // BANDS
    print("\ndark-pixel share per %d%% %s" % (step, title))
    print("  band     ref      mine     diff")
    worst = 0.0
    for i, (a, m) in enumerate(zip(apple, mine)):
        d = m - a
        worst = max(worst, abs(d))
        flag = "  <-- off" if abs(d) > TOLERANCE else ""
        print("  %2d-%2d%%  %6.1f  %6.1f  %+6.1f%s"
              % (i * step, (i + 1) * step, a, m, d, flag))
    return worst


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    mine_p, ref_p = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else "face"
    spec = DEFAULT_SPEC

    _, m_mask, m_size = chassis_crop(mine_p)
    _, r_mask, r_size = chassis_crop(ref_p)

    # the canary: an aspect far from spec means the crop failed, not the model
    want = spec[2] / spec[0]
    m_ratio = m_size[1] / m_size[0]
    r_ratio = r_size[1] / r_size[0]
    print("== %s ==" % label)
    print("mine  %4dx%4d px   h/w = %.4f" % (m_size[0], m_size[1], m_ratio))
    print("ref   %4dx%4d px   h/w = %.4f" % (r_size[0], r_size[1], r_ratio))
    print("spec  %.2f x %.2f      h/w = %.4f" % (spec[0], spec[2], want))
    for name, ratio in (("mine", m_ratio), ("ref", r_ratio)):
        gap = abs(ratio - want)
        print("  %s proportion error %+.4f  %s"
              % (name, gap, "OK" if gap < 0.02 else "<-- CROP OR MODEL WRONG"))
    if abs(m_ratio - want) >= 0.02:
        print("\nrefusing to report bands: chassis aspect does not match spec.")
        print("Either the crop failed or the model's proportions are wrong.")
        return 1

    worst_b = _table("band, top -> bottom", profile(m_mask, 0), profile(r_mask, 0))
    _table("column, left -> right", profile(m_mask, 1), profile(r_mask, 1))
    print("\nworst band deviation: %.1f points" % worst_b)
    return 0 if worst_b <= TOLERANCE else 1


if __name__ == "__main__":
    sys.exit(main())
