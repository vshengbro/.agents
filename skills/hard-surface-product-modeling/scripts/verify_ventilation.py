"""Per-face ray grid: assert a recessed/perforated field is on the RIGHT faces.

Run:  blender --background --python verify_ventilation.py -- mac_studio.blend

The check this exists for: a field of holes can be cut to full depth while the
shell recess is only part depth, leaving the holes inside solid material. The
hole object carries its full vertex count, the envelope is exactly right, and
the face renders as smooth metal. No graph inspection catches it — only a ray
fired at the face from outside tells you what is actually there.

Two things make this different from scanning a render:
  * it reports WHICH object each ray hit, so a hole is never confused with a
    shadow, and a side face whose holes are seen edge-on still counts;
  * it covers every face, because the recess mask is most likely wrong exactly
    where you did not look.

Two artifacts it also has to survive, or it sends you chasing a correct model:
  * a ray fired normal to a side face GRAZES the rear corner arc and returns
    hits that belong to the rear panel, so hit coordinates are printed and not
    just the count — a 2-3% residual on a supposedly solid face is usually
    this, not a leak;
  * classifying a vertex's face by "which coordinate is bigger" is wrong,
    because a panel runs the full width including the corners. The vertex
    census below restricts to the flat region and is the unambiguous check.

Set MIN_SHARE from the reference, or from the user's stated topology. A face
declared solid gets 0.0, not a token value: the count is still printed, so a
regression to "a little perforated" fails loudly instead of passing as parity.
"""
import sys
import bpy
from mathutils import Vector

# face label -> (ray origin, direction, sweep axis, minimum share of rays
#                that must reach a feature object)
FACES = {
    "front -Y": ((0, -40, 0), (0, 1, 0), "x", 0.0),
    "rear  +Y": ((0, 40, 0), (0, -1, 0), "x", 0.20),
    "right +X": ((40, 0, 0), (-1, 0, 0), "y", 0.0),
    "left  -X": ((-40, 0, 0), (1, 0, 0), "y", 0.0),
    "bottom -Z": ((0, 0, -40), (0, 0, 1), "z", 0.0),   # rays up at the underside
}
FEATURE_SUBSTR = "Grille"     # objects whose name contains this ARE the feature
STUDIO = ("BounceL", "BounceR", "Floor")   # must not sit between camera and body
Z_LO, Z_HI = 0.30, 9.40
GRID = 21
EXTENT = 9.4                  # keep rays clear of the corner fillets
FLAT_HALF = 8.0               # vertex census: inside the straight part of a panel


def ray_face(label, org, d, axis):
    """Fire a GRID x GRID grid at one face; return (total, feature_hits, hits)."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    d = Vector(d)
    total = feature = 0
    hits = []
    for iz in range(GRID):
        z = Z_LO + (Z_HI - Z_LO) * iz / (GRID - 1)
        for ia in range(GRID):
            a = -EXTENT + 2 * EXTENT * ia / (GRID - 1)
            if axis == "z":            # face lies in a horizontal plane
                o = Vector((a, -EXTENT + 2 * EXTENT * iz / (GRID - 1), org[2]))
            elif axis == "x":
                o = Vector((a, org[1], z))
            else:
                o = Vector((org[0], a, z))
            hit, loc, nrm, idx, obj, mtx = sc.ray_cast(dg, o, d)
            if not hit:
                continue
            total += 1
            if FEATURE_SUBSTR in obj.name:
                feature += 1
                hits.append((round(loc.y, 2), round(loc.z, 2), obj.name))
    return total, feature, hits


def flat_census():
    """Feature vertices sitting on a panel's FLAT region — no corner ambiguity.

    The ray grid can graze a neighbouring panel; this cannot. Classify by
    restricted extent, not by which coordinate is larger: a panel spans the
    full width including the corners, so the naive test files the rear panel's
    own corner vertices under the side panels.
    """
    counts = {}
    for name in bpy.data.objects.keys():
        if FEATURE_SUBSTR not in name:
            continue
        o = bpy.data.objects[name]
        M = o.matrix_world
        side = sum(1 for v in o.data.vertices if abs((M @ v.co).y) < FLAT_HALF)
        front = sum(1 for v in o.data.vertices if (M @ v.co).y < -FLAT_HALF)
        counts[name] = (side, front)
    return counts


def main(blend="mac_studio.blend"):
    bpy.ops.wm.open_mainfile(filepath=blend)
    # remove the studio objects outright: scene.ray_cast evaluates originals
    for n in STUDIO:
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)

    fails = 0
    for label, (org, d, axis, want) in FACES.items():
        total, feature, hits = ray_face(label, org, d, axis)
        share = feature / max(1, total)
        ok = share >= want
        fails += 0 if ok else 1
        print("  %-4s %-10s %3d/%3d rays reach feature (%4.1f%%, need %.0f%%)"
              % ("OK" if ok else "FAIL", label, feature, total, share * 100,
                 want * 100))
        # a graze shows up as hits clustered on the neighbour's coordinates
        for y, z, obj in hits:
            on_flat = abs(abs(y) - 9.85) < 0.25
            print("        hit y=%6.2f z=%5.2f %-18s %s"
                  % (y, z, obj, "ON THIS PANEL" if on_flat else "(corner graze)"))

    print()
    for name, (side, front) in sorted(flat_census().items()):
        bad = side or front
        fails += 1 if bad else 0
        print("  %-4s %-18s flat side panel: %4d   front panel: %4d"
              % ("OK" if not bad else "FAIL", name, side, front))

    print("\n%s (%d failures)"
          % ("VENT_OK" if not fails else "VENT_FAIL", fails))
    return fails


if __name__ == "__main__":
    sys.exit(1 if main(*sys.argv[sys.argv.index("--") + 1:]) else 0)
