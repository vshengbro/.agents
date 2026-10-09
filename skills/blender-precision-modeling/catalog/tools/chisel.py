"""
chisel -- 215 mm bench chisel, 25 mm blade with a ground bevel.

Handle down, blade up, so sit_on_floor rests it on the butt and the side
render shows the whole tool in profile.

The blade is a loft of three rectangular rings: the last ring keeps the full
25 mm width but drops the thickness from 3 mm to 0.8 mm. A constant-thickness
extrusion would give a chisel with a 25 x 6 mm rectangular tip, which reads
as a cold chisel with no bevel at all.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    overall_length=215.0,
    handle_diameter=31.0,
    handle_length=96.0,
    blade_width=25.0,
    blade_thickness=6.0,
)


def _ring(hw, ht, z):
    return [(-hw, -ht, z), (hw, -ht, z), (hw, ht, z), (-hw, ht, z)]


def build():
    wood = bkit.preset("wood")
    steel = bkit.pbr("ChiselSteel", base=(0.68, 0.70, 0.74), metal=0.30,
                     rough=0.28)

    handle = bkit.lathe("ChiselHandle",
                        [(0, 0), (13, 0), (15.5, 8), (14.5, 26),
                         (12.0, 52), (10.5, 74), (10.0, 88), (10.0, 96),
                         (0, 96)], segments=64, mat=wood)
    bkit.recalc(handle)

    ferrule = bkit.tube("ChiselFerrule", 11.0, 9.6, 18.0, segments=48,
                        centre=(0, 0, 105.0), mat=steel)

    blade = bkit.loft("ChiselBlade",
                      [_ring(12.5, 3.0, 114.0), _ring(12.5, 3.0, 175.0),
                       _ring(12.5, 0.8, 215.0)], mat=steel)
    bkit.recalc(blade)
    bkit.bevel(blade, width_mm=0.5, segments=1, angle_deg=40)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="handle_diameter", mm=31.0, tol=0.5, how="diameter",
         part="ChiselHandle"),
    dict(name="blade_width", mm=25.0, tol=0.5, how="bbox_x",
         part="ChiselBlade"),
    dict(name="overall_length", mm=215.0, tol=1.5, how="bbox_z"),
]