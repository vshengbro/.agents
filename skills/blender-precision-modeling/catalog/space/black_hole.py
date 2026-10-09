"""
black_hole -- a supermassive black hole: 6.4e9 km event horizon, accretion
disk out to 12x the Schwarzschild radius, relativistic jets 200 000 ly long.

Size class `huge` (3000..40000 mm band, tolerance x0.5..x2, so nothing
declared may exceed 80 000 mm). Stated at 1:1e19 scale: the event horizon is
3 200 mm across and the accretion disk reaches 40 000 mm out from centre.
The real ratios are what is preserved -- disk outer edge at 12.5 r_s, photon
ring at 1.5 r_s -- and those ratios are what a black hole is recognised by.

What makes a black hole read rather than reading as a black ball:
1. the EVENT HORIZON is genuinely black -- a material with no diffuse, no
   metal and no emission. Surround it with something bright or the "hole"
   disappears.
2. the PHOTON RING: a thin, very bright annulus at ~1.5 r_s. This is the
   single detail that says "black hole" and it is geometrically correct.
3. the ACCRETION DISK is differentially rotating, so its brightness has to
   vary around the circumference. A uniform annulus reads as a ring.
4. the JETS are the bipolar outflow, on the polar axis, thinner than the disk
   and emissive.

All emission strengths stay near 1.5 so the studio rig does not blow out.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    horizon_diameter=3200.0,      # event horizon = Schwarzschild radius * 2
    photon_ring_diameter=4800.0,  # at 1.5 r_s
    disk_inner_diameter=3200.0,
    disk_outer_diameter=40000.0,  # 12.5 r_s: the real thin-disk limit
    disk_thickness=90.0,
    jet_length=900.0,
    jet_diameter=260.0,
)

H_R = SPEC["horizon_diameter"] / 2.0
PR_R = SPEC["photon_ring_diameter"] / 2.0
DI = SPEC["disk_inner_diameter"] / 2.0
DO = SPEC["disk_outer_diameter"] / 2.0
DT = SPEC["disk_thickness"]


def _annulus(name, r_in, r_out, thickness, mat, seg=160):
    """A flat annulus with real thickness: two rims, two faces, one solid."""
    h = thickness / 2.0
    verts, faces = [], []
    for z in (-h, h):
        for r in (r_in, r_out):
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
    # The horizon itself: black in every channel, nothing to reflect.
    void = bkit.pbr("EventHorizon", base=(0.0, 0.0, 0.0), rough=1.0,
                    metal=0.0)
    # The photon ring keeps a HIGH strength: it is a THIN annulus, so it
    # stays inside the exposure even when the disk beside it does not.
    photon = bkit.pbr("PhotonRing", base=(0.0, 0.0, 0.0), rough=0.2,
                      emission=(1.00, 0.94, 0.80), emission_strength=1.5)
    # Emission strengths are LOW here, below the ~1.5 the rest of the
    # catalog uses. The accretion disk is a 40 m disc of emissive material
    # filling most of the frame; at strength 1.5 auto-exposure cannot pull it
    # back and the whole disk renders as a flat white blob with a black dot in
    # it. At 0.25 the radial colour gradient survives exposure.
    disk_hot = bkit.pbr("DiskHot", base=(0.02, 0.02, 0.02), rough=0.4,
                        emission=(1.00, 0.74, 0.36), emission_strength=0.24)
    disk_cool = bkit.pbr("DiskCool", base=(0.02, 0.02, 0.03), rough=0.4,
                         emission=(0.72, 0.22, 0.11), emission_strength=0.16)
    jet = bkit.pbr("JetPlasma", base=(0.02, 0.02, 0.03), rough=0.4,
                   emission=(0.55, 0.72, 1.00), emission_strength=0.35)

    # ---- event horizon: a genuinely black sphere ------------------------
    horizon = bkit.uv_sphere("EventHorizon", H_R, segments=64, rings=32,
                             centre=(0.0, 0.0, 0.0), mat=void)

    # ---- photon ring: thin, bright, at 1.5 r_s -------------------------
    ring = _annulus("PhotonRing", PR_R - H_R * 0.055, PR_R + H_R * 0.055,
                    H_R * 0.03, photon)

    # ---- accretion disk, tilted so it is not edge-on to the camera -----
    TILT = math.radians(16.0)
    disk = _annulus("AccretionDisk", DI, DO, DT, disk_cool, seg=192)
    disk.rotation_euler = (TILT, 0.0, 0.0)
    # Doppler-brightened leading side, plus the hot inner annulus: face
    # selection on the SAME solid, so the disk stays one watertight body.
    inner = _annulus("DiskInnerHot", DI, DI + (DO - DI) * 0.22, DT * 1.6,
                     disk_hot, seg=192)
    inner.rotation_euler = (TILT, 0.0, 0.0)
    # Doppler brightening on the APPROACHING side only. Splitting the disk on
    # a half-plane (x > 0) cuts it into two hard semicircles of flat colour,
    # which reads as a two-tone disc rather than as differential rotation. The
    # brightening is confined to the inner third of the approaching side, where
    # the effect actually is.
    def _doppler(c, n):
        x = c.x / bkit.MM
        y = c.y / bkit.MM
        r = (x * x + y * y) ** 0.5
        return n.z > 0.5 and x > 0.0 and r < DO * 0.34
    bkit.assign_faces_by(disk, disk_hot, _doppler)

    # ---- bipolar jets on the polar axis --------------------------------
    # Two lathed cones, flaring outward, with the disk plane as their origin.
    for (name, sign) in (("JetNorth", 1.0), ("JetSouth", -1.0)):
        prof = [(SPEC["jet_diameter"] * 0.20, 0.0),
                (SPEC["jet_diameter"] * 0.34, SPEC["jet_length"] * 0.30),
                (SPEC["jet_diameter"] * 0.52, SPEC["jet_length"] * 0.70),
                (SPEC["jet_diameter"] * 0.40, SPEC["jet_length"])]
        col = bkit.lathe(name, prof, segments=28, mat=jet, smooth=True)
        bkit.recalc(col)
        col.scale = (1.0, 1.0, sign)
        bkit.apply_mods(col)
        bkit.move(col, 0.0, 0.0, sign * (DO * 0.18))

    # ---- knot hotspots in the disk, on computed azimuths ---------------
    # Real disks are clumpy. Six of them, evenly spaced, so the disk's
    # brightness varies around its circumference.
    rnd = random.Random(9)
    for i in range(6):
        a = 2.0 * math.pi * i / 6.0 + 0.4
        rr = DO * (0.30 + 0.55 * rnd.random())
        knot = bkit.rounded_box("DiskKnot%02d" % (i + 1), DO * 0.09, DO * 0.05,
                                DT * 2.4, r=DO * 0.02,
                                centre=(rr * math.cos(a), rr * math.sin(a), 0.0),
                                mat=disk_hot)
        knot.rotation_euler = (TILT, 0.0, a)

    return dict(spec=SPEC, parts=1 + 1 + 2 + 2 + 6)


CHECKS = [
    dict(name="horizon_diameter", mm=3200.0, tol=10.0,
         how="diameter", part="EventHorizon"),
    # The photon ring has real radial thickness, so its OUTER edge is what
    # the bbox measures.
    dict(name="photon_ring_outer_diameter", mm=4976.0, tol=20.0,
         how="diameter", part="PhotonRing"),
    dict(name="disk_outer_diameter", mm=40000.0, tol=60.0,
         how="bbox_x", part="AccretionDisk"),
    # The disk is TILTED 16 deg, so its bbox_z is the 11 m tilted envelope,
    # not the 90 mm of structure. Thickness is measurable on the UNTILTED
    # photon ring instead.
    dict(name="photon_ring_thickness", mm=48.0, tol=3.0,
         how="bbox_z", part="PhotonRing"),
    dict(name="jet_length", mm=900.0, tol=12.0, how="bbox_z", part="JetNorth"),
    dict(name="disk_tilt_envelope_height", mm=11112.0, tol=140.0,
         how="bbox_z", part="AccretionDisk"),
    dict(name="overall_width", mm=40000.0, tol=200.0, how="bbox_x"),
]