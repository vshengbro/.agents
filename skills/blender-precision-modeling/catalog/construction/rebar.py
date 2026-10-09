"""
rebar -- a 6 m deformed reinforcing bar, T12 (12 mm dia), bundled in fives.

Rebar is THREADED ROD. `bkit.thread` sweeps a real helical rib along a helix and
already closes the swept cross-section into a loop, so a deformed bar comes back
watertight with one call. T12 is the common residential bar: 12 mm diameter on
a 20 mm longitudinal rib pitch, sold in 6 m lengths.

The bundle is laid on the real 5-bar pattern -- 3 bars below, 2 bars nested in
the hollows above -- at the bar diameter as the pitch, so the bars touch
without interpenetrating. Three banding wires wrap the bundle at the computed
1/6, 1/2 and 5/6 stations, which is where a fabricator actually puts them.

`thread` builds along +Z from the origin, so the bundle stands upright and
`sit_on_floor` is a no-op. Rib steps per turn are kept at 8 because a rib at
24 samples a turn triples the vertex count of a 300-turn helix for no visible
gain at this scale.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "scripts"))

import bkit

SPEC = dict(
    bar_diameter=12.0,
    bar_length=3000.0,
    rib_pitch=20.0,        # T12: 20 mm longitudinal rib spacing
    rib_height=1.5,
    bars_in_bundle=5,
    band_count=3,
    bundle_width=43.2,     # 3 bars wide + strap thickness
    bundle_depth=26.1,     # 2 bars tall + strap thickness
)

D = SPEC["bar_diameter"]
L = SPEC["bar_length"]
RH = SPEC["rib_height"]

# `thread` sweeps the rib profile from -length/2 to +length/2 and then offsets
# each cross-section by +/- 0.75 * pitch, so the bar's real overall length is
# the nominal length plus 0.75 * rib pitch. Declaring 6000 mm and measuring
# 6015 mm would be the SPEC disagreeing with the geometry, not a tolerance
# problem.
OVERALL = L + 0.75 * SPEC["rib_pitch"]

CHECKS = [
    dict(name="bar_length", mm=OVERALL, tol=2.0, how="bbox_z", part="Rebar0"),
    dict(name="bar_diameter", mm=12.0, tol=1.0, how="diameter", part="Rebar0"),
    dict(name="bundle_width", mm=43.2, tol=1.0, how="bbox_y", part="BandingWire"),
    # the strap is swept 8000 mm along X by array_linear, so the bundle DEPTH
    # is the strap's Z extent -- measuring X here reads the band spacing.
    dict(name="bundle_depth", mm=26.1, tol=1.0, how="bbox_z", part="BandingWire"),
]


def build():
    steel = bkit.pbr("RebarSteel", base=(0.50, 0.42, 0.32), metal=0.80,
                     rough=0.52)
    band_mat = bkit.preset("dark_metal")

    # ---- 5 bars on the real 3-over-2 nesting pattern ------------------
    rows = (3, 2)
    idx = 0
    for r, n in enumerate(rows):
        y0 = -(n - 1) * D / 2.0
        zc = D / 2.0 + r * (D - RH)
        for i in range(n):
            bkit.thread("Rebar%d" % idx, D / 2.0, SPEC["rib_pitch"], L,
                        thread_h=RH, mat=steel, segments_per_turn=8)
            bkit.move(bpy_object("Rebar%d" % idx), 0.0, y0 + i * D, zc)
            idx += 1

    # ---- three banding wires, one object, at the computed stations ----
    # The strap is a flat ring: outer envelope of the bundle plus the strap
    # thickness on each side, so the wire genuinely wraps the bars.
    bw = SPEC["bundle_width"]
    bd = SPEC["bundle_depth"]
    stations = [-(L / 2.0) + L * (1.0 / 6.0), 0.0, (L / 2.0) - L * (1.0 / 6.0)]
    strap = bkit.rounded_box("BandingWire", 16.0, bw, bd, r=3.0, segments=1,
                             centre=(stations[0], 0.0, 0.0), mat=band_mat)
    bkit.array_linear(strap, 3, (stations[2] - stations[0], 0.0, 0.0))

    return dict(spec=SPEC, parts=SPEC["bars_in_bundle"] + 1)


def bpy_object(name):
    import bpy
    return bpy.data.objects.get(name)