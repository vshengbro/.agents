#!/usr/bin/env python3
"""Validate detached.py against cases whose answer is known in advance.

A detector that reports "clean" on everything is indistinguishable from one that
does not work at all -- and this one did report "clean" on an astrolabe whose
render plainly showed a padlock hanging in mid-air. So each fixture places a
part at a known distance from the body, where the correct answer is fixed:

    touching  (0.00 mm gap) -> clean, it is attached
    kissing   (0.10 mm gap) -> clean, it reads as attached in a render
    clearance (1.00 mm gap) -> clean, ordinary running clearance on a real part
    floating  (40   mm gap) -> FLAGGED
    speck     (200  mm gap) -> FLAGGED
    big_island (60% of the body's verts) -> clean: that is a modelling error,
                                            not a stray, and a different fix

Run:  blender -b --factory-startup -noaudio --python selftest_detached.py
"""
import os
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS)

import bpy      # noqa: E402
import bkit     # noqa: E402
import detached  # noqa: E402

BODY_TOP = 40.0        # the body spans z 0..40

# The island test is a FRACTION of the body's vertex count, so the fixtures have
# to control that fraction rather than assume it. A cube beside a cube is 50% of
# the model and is correctly excluded as a body, not a stray -- the first draft
# of this file made exactly that mistake and "passed" the clean cases for the
# wrong reason.
#
#   body: 96-segment cylinder  -> ~194 verts
#   chip: cube                 ->    8 verts  = ~4%  -> counts as a stray
#   isle: 192-segment cylinder -> ~386 verts  = ~67% -> a body, not a stray
BODY_SEG = 96

# (label, gap_mm, part, expect_flagged)
CASES = [
    ("touching_0.00mm", 0.0, ("cube", 10.0), False),
    ("kissing_0.10mm", 0.1, ("cube", 10.0), False),
    # 1 mm on a 40 mm body is ~10 px at render scale: it IS visibly floating,
    # so flagging it is correct and an earlier draft of this file was wrong to
    # expect "clean" here.
    ("clearance_1.00mm", 1.0, ("cube", 10.0), True),
    ("floating_40mm", 40.0, ("cube", 10.0), True),
    ("speck_200mm", 200.0, ("cube", 4.0), True),
    ("big_island_67pct", 60.0, ("cyl", 192), False),
]

fails = 0
print("%-22s %-10s %-10s %s" % ("case", "expected", "got", "result"))
print("-" * 62)
for label, gap, (kind, size), expect in CASES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bkit.reset()
    bkit.cylinder("Body", 20.0, 40.0, segments=BODY_SEG,
                  centre=(0.0, 0.0, 20.0), mat=bkit.preset("steel"))
    if kind == "cube":
        bkit.box("Chip", size, size, size,
                 centre=(0.0, 0.0, BODY_TOP + gap + size / 2.0),
                 mat=bkit.preset("steel"))
    else:
        bkit.cylinder("Chip", size, 40.0, segments=size,
                      centre=(0.0, 0.0, BODY_TOP + gap + 20.0),
                      mat=bkit.preset("steel"))
    r = detached.analyse_scene()
    got = bool(r.get("islands"))
    ok = (got == expect)
    fails += 0 if ok else 1
    detail = " (parts=%d)" % r.get("components", -1)
    if r.get("islands"):
        detail += " gap=%.1fmm frac=%.3f%%" % (r["islands"][0]["gap_mm"],
                                              r["islands"][0]["frac"] * 100)
    print("%-22s %-10s %-10s %s%s"
          % (label, "FLAGGED" if expect else "clean",
             "FLAGGED" if got else "clean", "ok" if ok else "FAIL", detail))

print("-" * 62)
print("selftest: %d/%d cases correct" % (len(CASES) - fails, len(CASES)))
sys.exit(1 if fails else 0)
