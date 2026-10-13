#!/usr/bin/env python3
"""Pixel A/B diff for browser-render verification. Standard library only.

Two failure modes this exists to prevent:

1. Trusting a zero-pixel result from a debug toggle without proving the toggle
   removes pixels. Validate the mechanism on a target known to be on screen,
   and calibrate the noise floor -- if hiding the suspect changes the same
   number of pixels as hiding everything, the floor is the effect and the
   experiment is void. Invert it instead: render only the suspect, so any pixel
   in its box can only have come from it.
2. Concluding "invisible" from a whole-frame diff whose noise floor is the
   size of the effect. Scope the diff to the object's own box.

Usage:
    python3 pixel_ab.py base.png variant.png [--box X0,Y0,X1,Y1] [--tol 10]

`--box` is in image pixels, half-open, and is normally the object box the
engine itself reports. Prints whole-frame and boxed counts plus a verdict
that names the floor, so a reader cannot mistake "small" for "zero".
"""
from __future__ import annotations

import argparse
import struct
import sys
import zlib

# A whole-frame diff is dominated by animated content the object has nothing
# to do with. Below this many changed pixels, a whole-frame reading carries no
# information and the boxed number is the one to believe.
FLOOR_PIXELS = 1000


class Frame:
    """A decoded image as one luminance sample per pixel."""

    __slots__ = ("width", "height", "gray")

    def __init__(self, width: int, height: int, gray: list[float]) -> None:
        self.width = width
        self.height = height
        self.gray = gray

    def box(self, x0: int, y0: int, x1: int, y1: int) -> "Frame":
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(self.width, x1), min(self.height, y1)
        w, h = max(0, x1 - x0), max(0, y1 - y0)
        rows = []
        for y in range(y0, y1):
            start = y * self.width + x0
            rows.extend(self.gray[start:start + w])
        return Frame(w, h, rows)


def decode_png(data: bytes) -> Frame:
    """Decode 8-bit non-interlaced truecolour PNG to luminance.

    Hand-rolled because the harness runs with no third-party packages and the
    screenshots come straight off `Page.captureScreenshot`. Supports colour
    type 2 (RGB) and 6 (RGBA); anything else is a loud failure, not a guess.
    """
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, width, height, channels = 8, bytearray(), 0, 0, 0
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, color = struct.unpack(">IIBB", body[:10])
            if depth != 8 or color not in (2, 6):
                raise ValueError(f"unsupported PNG depth={depth} color={color}")
            channels = 3 if color == 2 else 4
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
        pos += 12 + length

    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    out: list[float] = []
    prev = bytearray(stride)
    p = 0
    for _ in range(height):
        filt = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if filt == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filt == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif filt == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif filt == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xFF
        elif filt != 0:
            raise ValueError(f"unsupported PNG filter {filt}")
        for x in range(width):
            i = x * channels
            out.append(0.2126 * line[i] + 0.7152 * line[i + 1] + 0.0722 * line[i + 2])
        prev = line
    return Frame(width, height, out)


def diff(a: Frame, b: Frame, tol: float = 10.0) -> tuple[int, float]:
    """Return (changed_pixels, max_abs_delta) over the two frames."""
    if (a.width, a.height) != (b.width, b.height):
        raise ValueError(f"size mismatch {a.width}x{a.height} vs {b.width}x{b.height}")
    changed, peak = 0, 0.0
    for x, y in zip(a.gray, b.gray):
        d = abs(x - y)
        if d > peak:
            peak = d
        if d > tol:
            changed += 1
    return changed, peak


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("base")
    ap.add_argument("variant")
    ap.add_argument("--box", help="X0,Y0,X1,Y1 in pixels; defaults to the whole frame")
    ap.add_argument("--tol", type=float, default=10.0, help="luma delta counted as changed")
    args = ap.parse_args()

    base = decode_png(open(args.base, "rb").read())
    variant = decode_png(open(args.variant, "rb").read())

    whole, peak = diff(base, variant, args.tol)
    total = base.width * base.height
    print(f"frame {base.width}x{base.height}  tol={args.tol:g}")
    print(f"  whole  changed={whole:8d} ({100 * whole / total:6.3f}%)  max={peak:6.1f}")
    if whole < FLOOR_PIXELS:
        print(f"  ^ below the {FLOOR_PIXELS}-pixel floor: this diff cannot decide anything.")
        print("    Either slow the world further or invert the A/B (hide everything")
        print("    EXCEPT the object) so its box can only contain its own pixels.")

    if args.box:
        x0, y0, x1, y1 = (int(v) for v in args.box.split(","))
        changed, peak = diff(base.box(x0, y0, x1, y1), variant.box(x0, y0, x1, y1), args.tol)
        area = max(1, (min(x1, base.width) - max(x0, 0)) * (min(y1, base.height) - max(y0, 0)))
        print(f"  box    changed={changed:8d} of {area:8d} ({100 * changed / area:6.2f}%)  max={peak:6.1f}")
        print("  -> 0 here is only conclusive when the whole-frame floor is small;")
        print("     otherwise it is the noise, not a rendering verdict.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
