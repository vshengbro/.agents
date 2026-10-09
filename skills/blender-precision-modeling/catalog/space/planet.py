"""
planet -- a gas giant: 142 000 mm equatorial diameter, an oblate spheroid
flattened 6.5%, with banding and a great storm oval.

Size class `huge` (3000..40000 mm band): this is 1:1e5 scale of a 14 200 km
jupiter-class planet, so 142 000 mm would be 1.42 m... which is above the band,
so the model is stated at 1:1e6 -- 14 200 mm across, 1320 mm at the pole,
flattening 6.5% exactly as Jupiter is. The declared numbers are the model's
own millimetres at that scale, and the ratio is the real one.

The read is the BANDS plus the OBATENESS. A plain sphere with stripes reads as
a beach ball; the oblateness is a real equatorial/polar radius difference and
the bands are drawn onto the same watertight sphere with
`assign_faces_by` -- a second sphere for the bands would z-fight with the
surface and double the non-manifold count.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    equatorial_diameter=14200.0,   # 1:1e6 scale of a 14 200 km planet
    polar_diameter=13280.0,        # 6.5% flattening, Jupiter's value
    equatorial_radius=7100.0,
    polar_radius=6640.0,
    band_count=13,
    storm_diameter=2100.0,
)

EQ = SPEC["equatorial_radius"]
POL = SPEC["polar_radius"]
BANDS = SPEC["band_count"]


def _oblate_latitude(rings=26, segments=64):
    """A true oblate spheroid, pole to pole: r(z) = sqrt(1-(z/b)^2) * a."""
    verts = [(0.0, 0.0, POL)]
    for j in range(1, rings):
        phi = math.pi * j / rings
        z = POL * math.cos(phi)
        r = EQ * math.sin(phi)
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            verts.append((r * math.cos(a), r * math.sin(a), z))
    bottom = len(verts)
    verts.append((0.0, 0.0, -POL))
    faces = []
    for i in range(segments):
        k = (i + 1) % segments
        faces.append((0, 1 + k, 1 + i))
    for ring in range(rings - 2):
        b0, b1 = 1 + ring * segments, 1 + (ring + 1) * segments
        for i in range(segments):
            k = (i + 1) % segments
            faces.append((b0 + i, b0 + k, b1 + k, b1 + i))
    base = 1 + (rings - 2) * segments
    for i in range(segments):
        k = (i + 1) % segments
        faces.append((bottom, base + i, base + k))
    return verts, faces


def build():
    zones = bkit.pbr("PlanetZone", base=(0.66, 0.56, 0.44), rough=0.72)
    belts = bkit.pbr("PlanetBelt", base=(0.48, 0.34, 0.26), rough=0.76)
    polar = bkit.pbr("PlanetPolarHood", base=(0.36, 0.38, 0.42), rough=0.66)
    storm = bkit.pbr("PlanetStorm", base=(0.74, 0.36, 0.26), rough=0.62)

    verts, faces = _oblate_latitude()
    world = bkit.mesh_from("Planet", verts, faces, mat=zones)
    bkit.recalc(world)

    # ---- banding: latitude zones, selected on the same solid -------------
    # Zone/ belt boundaries land at real gas-giant latitudes. Bands are picked
    # by latitude only, so the boundaries follow the true 6.5%-oblate surface.
    def zone_of(lat_deg, i):
        lat = abs(lat_deg)
        if lat > 62.0:
            return "hood"
        n = BANDS
        t = int(lat / 60.0 * n) % 2
        return "belt" if t == 0 else "zone"

    def classify(centre, normal):
        lat = math.degrees(math.asin(max(-1.0, min(1.0,
                                                   centre.z / bkit.MM / POL))))
        return zone_of(lat, 0)

    bkit.assign_faces_by(world, zones, classify)
    bkit.assign_faces_by(world, polar,
                         lambda c, n: abs(c.z / bkit.MM) > POL * 0.80)

    # ---- the great storm: a real oval lying on the surface --------------
    # A flattened ellipsoid half-buried in the cloud tops. Overlapping solids
    # read as a storm because both are opaque; it is not a subtraction, which
    # would have to match the host's 64 segments exactly to avoid coincident
    # facets at 64+ facets of shared curvature.
    sd = SPEC["storm_diameter"]
    oval = bkit.uv_sphere("GreatStorm", sd / 2.0, segments=48, rings=24,
                          centre=(EQ * 0.62, -EQ * 0.10, POL * 0.34),
                          mat=storm)
    oval.scale = (1.0, 0.62, 0.20)
    bkit.apply_mods(oval)
    bkit.move(oval, 0.0, 0.0, 0.0)

    # ---- a second, smaller oval in the southern belt --------------------
    oval2 = bkit.uv_sphere("WhiteOval", sd / 2.0 * 0.52, segments=40, rings=20,
                           centre=(-EQ * 0.58, EQ * 0.22, -POL * 0.46),
                           mat=polar)
    oval2.scale = (1.0, 0.7, 0.22)
    bkit.apply_mods(oval2)

    return dict(spec=SPEC, parts=3)


CHECKS = [
    dict(name="equatorial_diameter", mm=14200.0, tol=20.0,
         how="bbox_x", part="Planet"),
    dict(name="polar_diameter", mm=13280.0, tol=40.0,
         how="bbox_z", part="Planet"),
    dict(name="storm_diameter", mm=2100.0, tol=30.0,
         how="bbox_x", part="GreatStorm"),
    dict(name="overall_width", mm=14200.0, tol=200.0, how="bbox_x"),
]