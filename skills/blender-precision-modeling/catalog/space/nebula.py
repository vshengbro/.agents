"""
nebula -- an emission nebula: 46 light-years across, roughly 2.4e40 mm, stated
at 1:1e36 scale as 24 000 mm of glowing gas.

Size class `huge` (3000..40000 mm).

A nebula is volumetric, so the whole construction is CLUSTERS of overlapping
emissive solids at varied scale, never one primitive:
- a bright core (the O-type star's ionisation front) as nested shells,
- a molecular cloud as a radial array of lobes on computed angles, each a
  different scale, which is what gives a nebula its clumpy silhouette,
- dark dust lanes as opaque non-emissive blobs inside the glow, because a
  nebula with no dark intrusions reads as a coloured cotton ball.

Emission strength is kept near 1.5: the studio rig is calibrated for solid
objects, and a nebula at strength 8 is a white disc.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

SPEC = dict(
    span=24000.0,          # widest extent of the glowing region
    core_diameter=5200.0,
    lobes=22,
    dust_clouds=9,
    star_diameter=520.0,
)

SPAN = SPEC["span"]
HALF = SPAN / 2.0


def build():
    # Emission strengths here are ~0.5, a third of the catalog default, and
    # that is deliberate: a nebula is 24 000 mm of OVERLAPPING emissive solids
    # filling most of the frame. At strength 1.5 the lobes stack, auto-exposure
    # pulls back for the halo's rim, and every lobe saturates to flat white --
    # a white cloud with a coloured fringe. At 0.5 the stack stays inside the
    # exposure and the internal colour gradient survives.
    def glow(name, col, strength=0.5):
        return bkit.pbr(name, base=(0.02, 0.02, 0.03), rough=0.5,
                        emission=col, emission_strength=strength)

    core_hot = glow("NebulaCoreHot", (1.00, 0.93, 0.80), 0.70)
    core = glow("NebulaCore", (1.00, 0.32, 0.46), 0.50)
    shell_a = glow("NebulaShellA", (0.86, 0.16, 0.38), 0.42)
    shell_b = glow("NebulaShellB", (0.94, 0.46, 0.24), 0.42)
    shell_c = glow("NebulaShellC", (0.42, 0.34, 0.92), 0.38)
    star = bkit.pbr("NebulaStar", base=(0.0, 0.0, 0.0), rough=0.1,
                    emission=(1.0, 0.97, 0.90), emission_strength=0.85)

    # ---- central star and its ionisation cavity -------------------------
    s = bkit.uv_sphere("CentralStar", SPEC["star_diameter"] / 2.0, segments=32,
                       rings=16, centre=(0.0, 0.0, 0.0), mat=star)
    s.scale = (1.0, 1.0, 1.25)

    # Nested cavity shells: each bigger and cooler, so the core reads as a
    # gradient rather than as a hard-edged sphere. The outer shell is only
    # 2x the core, NOT 3x: at 3x it swallowed the lobe cluster entirely.
    for (name, r, mat) in (("CavityInner", SPEC["core_diameter"] * 0.17, core_hot),
                           ("CavityMid", SPEC["core_diameter"] * 0.26, core),
                           ("CavityOuter", SPEC["core_diameter"] * 0.34, shell_a)):
        sh = bkit.uv_sphere(name, r, segments=32, rings=16, mat=mat)
        sh.scale = (1.0, 1.0, 0.62)
        bkit.apply_mods(sh)

    # ---- molecular cloud lobes on computed angles ------------------------
    # A radial array gives equal angular spacing, but real nebulae are
    # lopsided, so each lobe also gets its own radius, scale and squash from
    # a fixed seed. One radial array + per-lobe variation, never a hand list.
    # Lobes push OUT past the halo, so the cluster is the silhouette and the
    # halo is only the glow behind it.
    rnd = random.Random(404)
    n = SPEC["lobes"]
    mats = [shell_a, shell_b, shell_c, core]
    # Lobes are placed on a SHELL, not a ring: radius is drawn from a power
    # law so most sit near the mid-radius and a few sit far out, and the
    # vertical spread is small. A single radius ring with tall spheres gave a
    # ring of upright eggs -- a flower, not a cloud.
    for i in range(n):
        a = 2.0 * math.pi * (i / float(n)) ** 0.85 * n / n + 0.35 * i
        a = math.atan2(math.sin(a), math.cos(a))
        rad = HALF * (0.16 + 0.84 * (rnd.random() ** 0.55))
        lobe_r = SPAN * (0.085 + 0.105 * rnd.random())
        mat = mats[i % len(mats)]
        lobe = bkit.uv_sphere("Lobe%02d" % (i + 1), lobe_r, segments=24,
                              rings=14,
                              centre=(rad * math.cos(a), rad * math.sin(a),
                                      HALF * 0.22 * (rnd.random() - 0.5)),
                              mat=mat)
        # squashed hard in z: a lobe is a PUFF, not an egg
        lobe.scale = (1.15 + 0.55 * rnd.random(), 0.80 + 0.45 * rnd.random(),
                      0.30 + 0.26 * rnd.random())
        lobe.rotation_euler = (rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25),
                               rnd.uniform(0.0, 3.14))
        bkit.apply_mods(lobe)

    # ---- outer halo: the part that fills the frame -----------------------
    # Thin and very dim. A fat, brighter halo engulfs every lobe and renders
    # the whole model as ONE smooth lavender ellipsoid -- the lobes stop
    # being visible as separate structures, which is the only thing the
    # cluster was for. Its job is only to stop the model ending in mid-air.
    # Emission 0.05, z-squashed to 0.13. The halo is the ONE part whose size
    # sets the declared span, so it cannot simply be deleted -- but at 0.12 it
    # rendered as an opaque lavender disc with the lobes poking through it,
    # which reads as a planet with bumps. At 0.05 it is a faint glow the lobes
    # clearly sit in front of, which is what a halo is.
    halo = bkit.uv_sphere("Halo", HALF, segments=40, rings=20,
                          mat=glow("NebulaHalo", (0.24, 0.20, 0.55), 0.05))
    halo.scale = (1.0, 0.92, 0.13)
    bkit.apply_mods(halo)

    # ---- dark dust lanes -------------------------------------------------
    # OPAQUE, non-emissive blobs sitting inside the glow. Without them the
    # render is a smooth coloured ball; with them it reads as gas and dust,
    # which is what a nebula actually is.
    dust = bkit.pbr("NebulaDust", base=(0.020, 0.017, 0.024), rough=0.95)
    for i in range(SPEC["dust_clouds"]):
        a = 2.0 * math.pi * i / SPEC["dust_clouds"] + 0.9
        rad = HALF * (0.18 + 0.55 * rnd.random())
        bkit.uv_sphere("DustCloud%02d" % (i + 1), SPAN * (0.03 + 0.05 * rnd.random()),
                       segments=20, rings=12,
                       centre=(rad * math.cos(a), rad * math.sin(a),
                               HALF * 0.22 * (rnd.random() - 0.5)),
                       mat=dust)

    return dict(spec=SPEC, parts=2 + 3 + n + 1 + SPEC["dust_clouds"])


CHECKS = [
    dict(name="span", mm=24000.0, tol=60.0, how="diameter", part="Halo"),
    dict(name="core_diameter", mm=3536.0, tol=40.0,
         how="diameter", part="CavityOuter"),
    dict(name="star_diameter", mm=520.0, tol=6.0,
         how="diameter", part="CentralStar"),
    dict(name="overall_width", mm=29349.0, tol=200.0, how="bbox_x"),
    dict(name="overall_height", mm=6287.0, tol=150.0, how="bbox_z"),
]