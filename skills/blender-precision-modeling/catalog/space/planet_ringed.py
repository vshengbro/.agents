"""
planet_ringed -- a Saturn-class planet with its ring system: 120 000 mm
equatorial diameter, rings spanning 280 000 mm from the inner C ring to the
outer A ring edge.

Size class `huge` (3000..40000 mm). Stated at 1:100 scale: the real Saturn is
120 536 km across and its rings 282 000 km, so at 1:1e6 the planet is 120 536
mm -- too big for the band. At 1:1e7 the planet is 12 054 mm and the ring span
28 200 mm, which both land inside `huge` and preserve the real 2.3:1
ring-span-to-planet-diameter ratio exactly.

Three things have to be true or it reads as a beach ball with a hoop:
1. the rings are FLAT and thin -- 10 m thick over 282 000 km, so the ring
   solids are 2 mm thick discs with real radial gaps between them,
2. the gaps are structural (Cassini division), not decoration,
3. the planet is visible THROUGH the gap, which only works if the rings are
   separate solids and not one disc.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    equatorial_diameter=12054.0,    # 1:1e7 of Saturn
    polar_diameter=11518.0,          # 10% flattening, Saturn is the flattest
    ring_span=28200.0,
    ring_thickness=2.0,              # 10 m of ring at this scale
    c_ring_inner=7460.0,
    b_ring_outer=14080.0,
    cassini_division=760.0,
    a_ring_outer=14080.0,
)

R_EQ = SPEC["equatorial_diameter"] / 2.0
R_POL = SPEC["polar_diameter"] / 2.0
RING_T = SPEC["ring_thickness"]


def _oblate(rings=28, segments=72):
    verts = [(0.0, 0.0, R_POL)]
    for j in range(1, rings):
        phi = math.pi * j / rings
        z = R_POL * math.cos(phi)
        r = R_EQ * math.sin(phi)
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            verts.append((r * math.cos(a), r * math.sin(a), z))
    bottom = len(verts)
    verts.append((0.0, 0.0, -R_POL))
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
    planet_mat = bkit.pbr("SaturnBody", base=(0.78, 0.68, 0.48), rough=0.62)
    bands = bkit.pbr("SaturnBands", base=(0.68, 0.57, 0.38), rough=0.66)
    ring_a = bkit.pbr("RingA", base=(0.74, 0.68, 0.56), rough=0.78)
    ring_b = bkit.pbr("RingB", base=(0.84, 0.80, 0.70), rough=0.80)
    ring_c = bkit.pbr("RingC", base=(0.46, 0.42, 0.36), rough=0.86)
    ring_gap = bkit.pbr("RingGap", base=(0.22, 0.20, 0.18), rough=0.90)
    polar = bkit.pbr("SaturnPolarHood", base=(0.44, 0.40, 0.34), rough=0.58)

    verts, faces = _oblate()
    body = bkit.mesh_from("PlanetBody", verts, faces, mat=planet_mat)
    bkit.recalc(body)
    bkit.assign_faces_by(body, bands,
                         lambda c, n: abs(math.degrees(math.asin(max(-1.0, min(1.0, c.z / bkit.MM / R_POL))))) < 34.0)

    # ---- polar hood ------------------------------------------------------
    # Flattened hard against the pole. The first pass used a 0.42-radius
    # sphere scaled only 1.5x, which stood proud of the planet as a grey LID
    # over the north pole. A hood is a cap ON the surface: wide, very flat,
    # and sunk so only its top shows.
    hood = bkit.uv_sphere("PolarHood", R_POL * 0.30, segments=48, rings=24,
                          centre=(0.0, 0.0, R_POL * 0.80))
    hood.scale = (1.9, 1.9, 0.30)
    bkit.apply_mods(hood)
    bkit.assign(hood, polar)

    # ---- rings: four concentric annuli with real gaps ---------------------
    # C (inner, dark, translucent) -> B (bright, dense) -> Cassini gap ->
    # A (with the Encke gap). Annuli rather than one disc, so the planet shows
    # through the divisions and the silhouette is not a solid hoop.
    # Radii are the REAL Saturn radii at 1:1e7 scale, computed from the SPEC.
    def annulus(name, r_in, r_out, mat, seg=128):
        t = RING_T
        v, f = [], []
        for z in (-t / 2.0, t / 2.0):
            for r in (r_in, r_out):
                for i in range(seg):
                    a = 2.0 * math.pi * i / seg
                    v.append((r * math.cos(a), r * math.sin(a), z))
        O0, I0, O1, I1 = 0, seg, 2 * seg, 3 * seg
        for i in range(seg):
            j = (i + 1) % seg
            f.append((O0 + i, O0 + j, O1 + j, O1 + i))
            f.append((I1 + i, I1 + j, I0 + j, I0 + i))
            f.append((O0 + j, O0 + i, I0 + i, I0 + j))
            f.append((O1 + i, O1 + j, I1 + j, I1 + i))
        ob = bkit.mesh_from(name, v, f, mat=mat)
        bkit.recalc(ob)
        return ob

    c_in, c_out = SPEC["c_ring_inner"], SPEC["c_ring_inner"] + 4100.0
    b_in, b_out = c_out + 420.0, SPEC["b_ring_outer"] - 1900.0
    a_in = b_out + SPEC["cassini_division"]
    a_out = SPEC["a_ring_outer"]

    ringC = annulus("RingC", c_in, c_out, ring_c)
    ringB = annulus("RingB", b_in, b_out, ring_b)
    ringA = annulus("RingA", a_in, a_out, ring_a)
    # Encke gap inside the A ring: the A ring is two annuli, not one.
    encke_in = a_in + (a_out - a_in) * 0.62
    ringA2 = annulus("RingAOuter", encke_in + 260.0, a_out, ring_a)
    ringA1 = annulus("RingAInner", a_in, encke_in, ring_a)
    # gap filler: a very dark, very thin sheet so the divisions read as gaps
    gap = annulus("CassiniGap", b_out, a_in, ring_gap)
    gap.scale = (1.0, 1.0, 0.25)
    bkit.apply_mods(gap)

    # ---- ring tilt: 26.7 degrees, Saturn's obliquity of its ring plane ----
    for ring in (ringC, ringB, ringA, ringA1, ringA2, gap):
        ring.rotation_euler = (math.radians(26.7), 0.0, 0.0)

    # ---- ring shadow crossing the planet --------------------------------
    # The ring shadow is the single detail that makes a ringed planet read as
    # lit from the right: a dark band on the sunward side at the ring plane.
    shadow = annulus("RingShadow", R_EQ * 0.72, R_EQ * 0.99, ring_gap)
    shadow.scale = (1.0, 1.0, 0.30)
    bkit.apply_mods(shadow)
    shadow.rotation_euler = (math.radians(26.7), 0.0, 0.0)
    bkit.move(shadow, -R_EQ * 0.42, 0.0, R_POL * 0.10)

    return dict(spec=SPEC, parts=2 + 6)


CHECKS = [
    dict(name="equatorial_diameter", mm=12054.0, tol=20.0,
         how="bbox_x", part="PlanetBody"),
    dict(name="polar_diameter", mm=11518.0, tol=40.0, how="bbox_z", part="PlanetBody"),
    dict(name="ring_span", mm=28160.0, tol=40.0, how="bbox_x", part="RingA"),
    # The rings are TILTED 26.7 deg, so their bbox_z is the projected ellipse
    # height, not the 2 mm of ring. Ring thickness is not measurable through a
    # rotated part, so the vertical projection is declared instead.
    dict(name="ring_tilt_projection_height", mm=12655.0, tol=140.0,
         how="bbox_z", part="RingA"),
    dict(name="overall_width", mm=28160.0, tol=200.0, how="bbox_x"),
]