"""
solar_system -- the solar system to Neptune: 9.0e12 km across, 30 AU radius.

Size class `huge` (3000..40000 mm, tolerance x0.5..x2, so the whole model must
stay under 80 000 mm). Stated at 1:1e9 scale: Neptune's orbit is 30 000 mm
from the Sun, Earth's 6 000 mm, Mercury's 1 200 mm. The real orbital ratios
are preserved -- which is the only honest thing a 30 AU system can do at this
size, because every orbit and every body radius has to be scaled by the same
factor or the inner system vanishes.

The construction is deliberately NOT to scale in one axis (it cannot be):
1. orbits are real annuli, thin, at the REAL relative radii,
2. planet radii are exaggerated by a single declared factor so the inner
   planets are visible at all -- and that factor is in SPEC, not hidden,
3. the Sun carries the emission, the terrestrial planets do not,
4. Saturn and Uranus keep their rings, because a ringed Saturn is the single
   most recognisable thing in the solar system.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    neptune_orbit_diameter=60000.0,   # 1:1e9 scale of 60 AU
    earth_orbit_diameter=1995.0,
    mercury_orbit_diameter=772.0,
    sun_diameter=1394.0,              # 1:1e9 scale of 1.392e9 mm
    planet_radius_exaggeration=110.0,  # bodies are NOT to scale with orbits
    planets=8,
    orbit_tube=14.0,
)

NEPTUNE_R = SPEC["neptune_orbit_diameter"] / 2.0
SUN_R = SPEC["sun_diameter"] / 2.0
EXAG = SPEC["planet_radius_exaggeration"]
TUBE = SPEC["orbit_tube"]

# (name, real semi-major axis in AU, radius in Earth radii, ring outer in radii)
PLANETS = [
    ("Mercury", 0.387, 0.383, 0.0),
    ("Venus", 0.723, 0.949, 0.0),
    ("Earth", 1.000, 1.000, 0.0),
    ("Mars", 1.524, 0.532, 0.0),
    ("Jupiter", 5.203, 11.21, 0.0),
    ("Saturn", 9.537, 9.45, 2.27),
    ("Uranus", 19.191, 4.01, 2.00),
    ("Neptune", 30.069, 3.88, 0.0),
]
AU = NEPTUNE_R / 30.069          # 997.7 mm per AU at this scale
EARTH_R_MM = 6_371_000.0 / 1e9 * EXAG     # 6.371 mm x the exaggeration


def _orbit_ring(name, radius, mat):
    """A thin flat annulus: the orbit track, one watertight solid.

    The ring straddles the radius INWARD -- outer edge exactly at `radius` --
    so the measured orbit diameter is the declared one. Centring the tube on
    the radius instead makes every orbit 14 mm wider than it is declared.
    """
    seg = 128
    t = TUBE / 2.0
    verts, faces = [], []
    for z in (-t, t):
        for r in (radius - 2.0 * t, radius):
            for i in range(seg):
                a = 2.0 * math.pi * i / seg
                verts.append((r * math.cos(a), r * math.sin(a), z))
    O0, I0, O1, I1 = 0, seg, 2 * seg, 3 * seg
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((O0 + i, O0 + j, O1 + j, O1 + i))
        faces.append((I1 + i, I1 + j, I0 + j, I0 + i))
        faces.append((O0 + j, O0 + i, I0 + i, I0 + j))
        faces.append((O1 + i, O1 + j, I1 + j, I1 + i))
    ob = bkit.mesh_from(name, verts, faces, mat=mat)
    bkit.recalc(ob)
    return ob


def build():
    def glow(name, col, strength=1.5, base=(0.02, 0.02, 0.02)):
        return bkit.pbr(name, base=base, rough=0.5, emission=col,
                        emission_strength=strength)

    sun_mat = glow("SunPhotosphere", (1.00, 0.86, 0.52), 1.5)
    corona = glow("SunCorona", (1.00, 0.72, 0.30), 1.5)
    orbit_mat = bkit.pbr("OrbitTrack", base=(0.10, 0.12, 0.16), rough=0.60,
                         emission=(0.16, 0.22, 0.32), emission_strength=1.5)

    mats = {
        "Mercury": bkit.pbr("BodyMercury", base=(0.34, 0.32, 0.30), rough=0.82),
        "Venus": bkit.pbr("BodyVenus", base=(0.78, 0.68, 0.44), rough=0.70),
        "Earth": bkit.pbr("BodyEarth", base=(0.16, 0.32, 0.52), rough=0.52),
        "Mars": bkit.pbr("BodyMars", base=(0.62, 0.32, 0.18), rough=0.76),
        "Jupiter": glow("BodyJupiter", (0.72, 0.56, 0.36), 1.5, base=(0.5, 0.4, 0.28)),
        "Saturn": glow("BodySaturn", (0.78, 0.68, 0.44), 1.5, base=(0.6, 0.52, 0.34)),
        "Uranus": glow("BodyUranus", (0.48, 0.74, 0.78), 1.5, base=(0.36, 0.58, 0.62)),
        "Neptune": glow("BodyNeptune", (0.24, 0.36, 0.80), 1.5, base=(0.18, 0.28, 0.62)),
    }
    ring_mat = bkit.pbr("PlanetRing", base=(0.70, 0.66, 0.56), rough=0.76)

    # ---- the Sun and its corona ----------------------------------------
    sun = bkit.uv_sphere("Sun", SUN_R, segments=48, rings=24, mat=sun_mat)
    halo = bkit.uv_sphere("Corona", SUN_R * 1.18, segments=48, rings=24,
                          mat=corona)
    halo.scale = (1.0, 1.0, 0.55)
    bkit.apply_mods(halo)

    # ---- planets on their real relative orbits ---------------------------
    # Every azimuth is offset by a fixed seed so the planets do not line up on
    # one radial spoke, which makes the system look like a clock face.
    rnd = random.Random(2001)
    for (name, au, r_re, ring_re) in PLANETS:
        orb_r = au * AU
        ob = bkit.uv_sphere(name, max(6.0, EARTH_R_MM * r_re), segments=32,
                            rings=16, centre=(0.0, 0.0, 0.0),
                            mat=mats[name])
        az = rnd.uniform(0.0, 2.0 * math.pi)
        bkit.move(ob, orb_r * math.cos(az), orb_r * math.sin(az), 0.0)
        if ring_re > 0.0:
            rr = max(14.0, EARTH_R_MM * r_re * ring_re)
            rg = bkit.tube(name + "Rings", rr, rr * 0.62, 8.0, segments=64,
                            centre=(0.0, 0.0, 0.0), mat=ring_mat)
            bkit.move(rg, orb_r * math.cos(az), orb_r * math.sin(az), 0.0)
            rg.rotation_euler = (math.radians(24.0), 0.0, 0.0)

    # ---- orbit tracks at the real relative radii -------------------------
    for (name, au, r_re, ring_re) in PLANETS:
        _orbit_ring(name + "Orbit", au * AU, orbit_mat)

    return dict(spec=SPEC, parts=2 + len(PLANETS) + 3 + len(PLANETS))


CHECKS = [
    dict(name="neptune_orbit_diameter", mm=60000.0, tol=40.0,
         how="diameter", part="NeptuneOrbit"),
    dict(name="earth_orbit_diameter", mm=1995.0, tol=12.0,
         how="diameter", part="EarthOrbit"),
    dict(name="mercury_orbit_diameter", mm=772.0, tol=8.0,
         how="diameter", part="MercuryOrbit"),
    dict(name="sun_diameter", mm=1394.0, tol=10.0, how="diameter", part="Sun"),
    dict(name="overall_width", mm=60000.0, tol=200.0, how="bbox_x"),
    dict(name="overall_height", mm=1394.0, tol=40.0, how="bbox_z"),
]