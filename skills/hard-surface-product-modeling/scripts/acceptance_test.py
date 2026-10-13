"""
Template acceptance test for a dimensionally-exact hard-surface model.

Run inside Blender:
    blender --background --factory-startup --python scripts/acceptance_test.py

Copy into the model project and adapt:
  * SPEC          -- the manufacturer's published envelope, in millimetres
  * build module  -- imported for the layout helpers, so the test and the
                     geometry derive from ONE source of truth
  * feature sets  -- the authored L->R orders the real product is known to have
  * CONNECTOR_H   -- {class: opening height}; absent entries default to width,
                     which still catches a transposed slot in VERTICAL_SLOTS
  * RECESS_OBJECTS / RECESS_AXES -- object names to ray-probe, and the axis
                     ('X' or 'Y') the probe approaches from

Exits non-zero when any check fails, so it can gate a commit.
"""
import bpy
import bmesh
import math
import os
import sys

MM = 0.001
MODEL_DIR = os.environ.get("MODEL_DIR", "/tmp/mac-studio-blender")

# Manufacturer spec, millimetres.  Cite the source in a comment.
SPEC = dict(W=197.0, D=197.0, H=95.0)   # e.g. apple.com/<product>/specs
TOL = 0.05                               # mm

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name:44s} {detail}")


def min_gap(positions):
    """Smallest clear space between neighbouring features in a layout."""
    edges = sorted((c - w / 2.0, c + w / 2.0) for c, w, _ in positions)
    return min(edges[i + 1][0] - edges[i][1] for i in range(len(edges) - 1))


# Connector classes and the orientation each MUST have.  A transposed
# connector still renders as a plausible row of ports, so assert it.
VERTICAL_SLOTS = ("usbc", "tb5", "usba")     # taller than wide
HORIZONTAL = ("hdmi", "rj45", "ac")          # wider than tall


def check_aspect(positions, label):
    """Every connector must match its class's orientation."""
    bad = []
    for c, w, kind in positions:
        # positions() yields (centre, width, kind); height comes from the build
        # module so the test never asserts against its own assumption
        h = getattr(B, "CONNECTOR_H", {}).get(kind, w)
        if kind in VERTICAL_SLOTS and h <= w:
            bad.append(f"{kind} {w}x{h} should be vertical")
        if kind in HORIZONTAL and w <= h:
            bad.append(f"{kind} {w}x{h} should be horizontal")
    check(f"{label}: connector aspect matches class", not bad, "; ".join(bad))


def check_recess(ob, axis, far=400.0, steps=13, tol=0.3):
    """Ray-cast across a recessed feature: the hit distance must vary.

    A boolean that is tangent to, or buried inside, the skin applies cleanly and
    cuts nothing while the envelope still verifies.  A constant hit distance
    across the feature is the signature.
    """
    from mathutils import Vector
    dg = bpy.context.evaluated_depsgraph_get()
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    if axis == "X":
        d = Vector((1, 0, 0)); o0 = Vector((far, 0, 0))
        us = [p.y for p in pts]
    else:
        d = Vector((0, 1, 0)); o0 = Vector((0, far, 0))
        us = [p.x for p in pts]
    a, b_ = min(us), max(us)
    ds = []
    for i in range(steps):
        u = a + (b_ - a) * i / (steps - 1)
        o = Vector((o0.x + (u if axis != "X" else 0),
                    o0.y + (u if axis != "Y" else 0), o0.z))
        hit, loc, nrm, idx, hit_ob, mtx = bpy.context.scene.ray_cast(dg, o, d)
        if hit:
            ds.append((loc - o).length)
    spread = (max(ds) - min(ds)) if ds else 0.0
    check(f"{ob.name}: surface is recessed (not a no-op cut)", spread > tol,
          f"ray spread {spread:.3f} over {steps} samples")


def main():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(MODEL_DIR, "model.blend"))
    sys.path.insert(0, os.path.join(MODEL_DIR, "scripts"))
    import build_model as B          # the geometry module under test

    body = bpy.data.objects[B.BODY_NAME]
    pts = [body.matrix_world @ v.co for v in body.data.vertices]

    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    w = (max(xs) - min(xs)) / MM
    d = (max(ys) - min(ys)) / MM
    h = (max(zs) - min(zs)) / MM
    box = SPEC['W'] * SPEC['D'] * SPEC['H']

    print("=" * 74)
    print("1:1 ACCEPTANCE TEST")
    print("=" * 74)

    print("\n1. ENVELOPE")
    for k, got in (("W", w), ("D", d), ("H", h)):
        check(f"{k} = {SPEC[k]:.2f} mm", abs(got - SPEC[k]) < TOL, f"got {got:.3f}")

    print("\n2. MESH HEALTH")
    bm = bmesh.new(); bm.from_mesh(body.data)
    nonman = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    vol = bm.calc_volume(signed=True) / (MM ** 3)
    bm.free()
    check("watertight (0 non-manifold edges)", nonman == 0, f"{nonman} found")
    check("outward normals (positive volume)", vol > 0, f"{vol:,.0f} mm^3")
    check("volume plausible (50-100% of box)", 0.5 * box < vol < box,
          f"{vol / box * 100:.1f}% of box")

    print("\n3. FEATURE LAYOUT")
    # Authored order must equal the order read off the real product.
    front = [k for _, _, k in B.front_positions()]
    rear = [k for _, _, k in B.rear_positions()]
    check("front order L->R matches reference", front == B.EXPECTED_FRONT_ORDER,
          str(front))
    check("rear order L->R matches reference", rear == B.EXPECTED_REAR_ORDER,
          str(rear))

    # First entry must land on the viewer's left, which flips between faces.
    fx = sorted(c for c, _, _ in B.front_positions())
    check("front first entry is smallest X (viewer's left)",
          B.front_positions()[0][0] == fx[0])
    rx = sorted(c for c, _, _ in B.rear_positions())
    check("rear first entry is largest X (viewer's left)",
          B.rear_positions()[0][0] == rx[-1])

    # Degenerate gaps are what silently empty a boolean.  Assert, don't assume.
    for nm, pos in (("front", B.front_positions()), ("rear", B.rear_positions())):
        g = min_gap(pos)
        check(f"{nm}: no overlapping/zero-gap features", g > 0.01,
              f"min gap {g:.2f} mm")

    # Orientation per connector class — a transposed port still looks like a port.
    check_aspect(B.front_positions(), "front")
    check_aspect(B.rear_positions(), "rear")

    total = sum(x[1] for x in B.rear_positions()) \
        + B.REAR_GAP * (len(B.rear_positions()) - 1)
    check("feature row fits inside the chassis", total < SPEC['W'],
          f"span {total:.1f} mm")

    print("\n4. MATERIALS")
    names = {m.name for o in bpy.data.objects if o.type == 'MESH'
             for m in o.data.materials}
    for n in B.REQUIRED_MATERIALS:
        check(f"material '{n}' assigned", n in names)

    print("\n5. RECESSES (ray-cast)")
    # Any boolean/loft recess must be probed.  A cut that silently did nothing
    # still passes every check above, including the envelope.
    for nm in getattr(B, "RECESS_OBJECTS", []):
        o = bpy.data.objects.get(nm)
        if o is None:
            check(f"{nm} exists", False, "object missing")
            continue
        axis = getattr(B, "RECESS_AXES", {}).get(nm, "Y")
        check_recess(o, axis)

    n_pass = sum(1 for _, ok, _ in results if ok)
    print("\n" + "=" * 74)
    print(f"RESULT: {n_pass}/{len(results)} checks passed")
    print("=" * 74)
    if n_pass != len(results):
        for n, ok, dt in results:
            if not ok:
                print(f"  FAILED: {n}  {dt}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
