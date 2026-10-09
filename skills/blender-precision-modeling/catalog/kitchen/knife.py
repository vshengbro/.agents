"""knife -- 205 mm chef's knife: flat-ground blade, three-rivet handle.

Presented edge-on: the blade profile is cut in the world YZ plane and extruded
through its 2.4 mm thickness along X, so the silhouette every product shot of a
knife is judged on is the silhouette the camera actually sees. `axis="X"` maps
a polygon point (px, py) to world (thickness, py, -px), which is why the
profiles below are written as (-z, y).

The blade is left un-bevelled on purpose: a cutting edge is sharp, and a bevel
would shrink the bounding box the dimensions are measured from. Only the handle
gets broken edges.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    knife_length=323.0,     # butt of the handle to the tip
    blade_length=205.0,
    blade_width=42.0,       # spine height at the heel
    blade_thickness=2.4,
    handle_length=118.0,
    handle_thickness=15.5,
)

BLADE_THK = SPEC["blade_thickness"]
HANDLE_THK = SPEC["handle_thickness"]

# blade outline in (z = spine height, y = distance from the heel)
BLADE = [
    (3.0, 0.0),
    (0.0, 34.0),            # heel, cutting edge
    (0.0, 148.0),
    (3.5, 182.0),           # the edge lifts into the tip
    (12.0, 205.0),
    (21.0, 197.0),
    (33.0, 168.0),
    (39.0, 120.0),
    (42.0, 40.0),           # spine
    (40.0, 2.0),
]

# handle outline: up the top edge, back down the bottom edge
HANDLE = [
    (13.0, -118.0),
    (14.0, -110.0),
    (13.2, -80.0),
    (11.6, -40.0),
    (8.6, 2.0),
    (6.2, 6.0),
    (2.0, 6.0),
    (2.6, -40.0),
    (4.4, -80.0),
    (5.4, -112.0),
    (5.0, -118.0),
]


def _profile(name, shape, thickness, mat):
    ob = bkit.extrude_profile(name, [(-z, y) for (z, y) in shape],
                              thickness, centre=(0.0, 0.0, 0.0),
                              axis="X", mat=mat)
    # extrude_profile does not orient the winding, and the sign of the signed
    # volume follows the polygon's winding. One recalc settles it either way.
    return bkit.recalc(ob)


def build():
    # A mirror metal reflects this dark studio and renders black. Dropping the
    # metallic fraction to 0.65 keeps a diffuse component for the key light to
    # land on, which is what makes cutlery read as steel instead of a silhouette.
    steel = bkit.pbr("CutlerySteel", base=(0.82, 0.83, 0.85), metal=0.65,
                     rough=0.22)
    scales = bkit.preset("black_plastic")

    blade = _profile("KnifeBlade", BLADE, BLADE_THK, steel)
    handle = _profile("KnifeHandle", HANDLE, HANDLE_THK, scales)
    # Broken edges read as a moulded handle; the blade's edges stay sharp.
    bkit.bevel(handle, width_mm=1.2, segments=3, angle_deg=30)

    # two rivets through the scales, on the flat faces
    for i, y in enumerate((-88.0, -40.0)):
        bkit.cylinder("KnifeRivet%d" % (i + 1), 3.2, HANDLE_THK + 1.2,
                      segments=24, centre=(0.0, y, 8.5), axis="X",
                      mat=bkit.preset("brushed_metal"))

    return dict(spec=SPEC, parts=4)


# The handle is bevelled, which pulls its butt in by one bevel width; the
# assembly length check carries a tolerance wide enough for that and nothing
# else. The blade is unbeveled, so its two dimensions are exact.
CHECKS = [
    dict(name="blade_length", mm=205.0, tol=0.3, how="bbox_y", part="KnifeBlade"),
    dict(name="blade_width", mm=42.0, tol=0.3, how="bbox_z", part="KnifeBlade"),
    dict(name="knife_length", mm=323.0, tol=1.6, how="bbox_y"),
]
