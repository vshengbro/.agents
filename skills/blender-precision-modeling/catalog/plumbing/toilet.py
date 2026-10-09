"""
toilet -- close-coupled two-piece WC: vitreous china bowl with a real wall
thickness, an oval seat ring with a real hole, and a cistern on the back deck.

The numbers that make a toilet a toilet: 400 mm to the top of the seat, a
700 mm projection measured from the cistern face, and a bowl that is WIDER at
the rim than at the foot. Sections that all share one footprint read as a
bucket.

Two construction notes learned the hard way:

* A ring (a toilet seat) is `tube`, not a closed-profile lathe. `lathe` caps
  every profile end whose radius is off-axis, so a profile that returns to its
  first point gets two coincident caps and one non-manifold edge per segment
  -- 64 bad edges on a 64-segment ring. `tube` builds the annulus directly.
* A rectangular ANNULUS cannot be made by handing `loft` four sections:
  `loft` bridges section i to i+1 and never wraps the last one back to the
  first, so the inner-bottom ring is left open. Build it round and scale it --
  `bbox()` reads matrix_world, so a non-uniform scale measures correctly.
"""
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import bkit

# --- real-world spec, millimetres -------------------------------------------
SPEC = dict(
    length=700.0,            # cistern face to the front of the bowl
    width=380.0,             # widest point of the bowl
    height=800.0,            # floor to the top of the cistern lid
    bowl_height=400.0,       # floor to the rim: the standard 400 mm seat height
    bowl_length=520.0,       # the ceramic bowl alone, behind the cistern
    rim_width=52.0,          # ceramic rim, front to back
    wall=18.0,               # vitreous china wall thickness
    foot_width=250.0,
    foot_length=420.0,
    cistern_width=380.0,
    cistern_length=180.0,
    seat_thickness=45.0,
)

BOWL_RIM_Z = SPEC["bowl_height"]
W = SPEC["width"]
L = SPEC["bowl_length"]
WALL = SPEC["wall"]
RIM = SPEC["rim_width"]

# The bowl occupies the FRONT of the 700 mm projection; the cistern takes the
# 180 mm behind it. Bowl centre in y is derived from those two numbers so the
# 700 mm overall projection is a consequence, not a hand-placed constant.
CISTERN_L = SPEC["cistern_length"]
BOWL_Y0 = CISTERN_L                       # bowl front edge of the cistern
BOWL_CY = BOWL_Y0 + L / 2.0


def _ring(sx, sy, r, z, cy):
    """One rounded-rect loft section at height z, centred at y = cy."""
    return [(x, y + cy, z) for (x, y) in
            bkit.rounded_rect_section(sx, sy, r, per_corner=6)]


def build():
    china = bkit.preset("ceramic")
    seat_mat = bkit.pbr("ToiletSeat", base=(0.94, 0.94, 0.92), rough=0.14,
                        coat=0.5)
    lid_mat = bkit.pbr("CisternLid", base=(0.91, 0.92, 0.91), rough=0.16,
                       coat=0.4)

    # ---- bowl: fold-back loft, so the wall is real geometry ----------------
    # Outer wall up, across the rim, back down the inside, in to the bowl
    # floor. cap_start closes the underside and cap_end the bowl floor.
    fw, fl = SPEC["foot_width"], SPEC["foot_length"]
    bowl = bkit.loft("Bowl", [
        _ring(fw, fl, 70.0, 0.0, BOWL_CY),                  # foot
        _ring(fw + 46.0, fl + 50.0, 88.0, 95.0, BOWL_CY),    # pedestal flare
        _ring(W - 24.0, L - 40.0, 102.0, 285.0, BOWL_CY),    # outer wall
        _ring(W, L, 110.0, BOWL_RIM_Z - 14.0, BOWL_CY),     # rim, outer
        _ring(W, L, 110.0, BOWL_RIM_Z, BOWL_CY),            # rim top, outer
        _ring(W - RIM * 0.55, L - RIM, 88.0, BOWL_RIM_Z, BOWL_CY),  # across rim
        _ring(W - RIM - WALL, L - RIM - WALL * 2.0, 80.0, BOWL_RIM_Z - 8.0,
              BOWL_CY),
        _ring(W - 118.0, L - 180.0, 92.0, 215.0, BOWL_CY),   # inner wall down
        _ring(W - 216.0, L - 290.0, 80.0, 168.0, BOWL_CY),   # bowl floor slope
    ], closed_loop=True, cap_start=True, cap_end=True, mat=china)
    bkit.recalc(bowl)

    # ---- back deck: the shelf the cistern stands on ------------------------
    # Spans y 0 .. 210: it starts exactly ON the cistern face, because nothing
    # may cross y = 0 or the 700 mm projection grows, and it overlaps the
    # bowl's back by 30 mm. A deck flush with the bowl wall would be tangent
    # along a face and render as a seam; the overlap interlocks the solids.
    deck = bkit.rounded_box("BackDeck", W + 10.0, CISTERN_L + 30.0, 44.0,
                            r=12.0, segments=3,
                            centre=(0.0, (CISTERN_L + 30.0) / 2.0,
                                    BOWL_RIM_Z - 14.0),
                            mat=china)

    # ---- cistern + lid ------------------------------------------------------
    cw, cl = SPEC["cistern_width"], CISTERN_L
    cistern = bkit.rounded_box("Cistern", cw, cl, 344.0, r=18.0, segments=3,
                               centre=(0.0, cl / 2.0, BOWL_RIM_Z + 8.0 + 172.0),
                               mat=china)
    # The lid overhangs by 7 mm a side, so it is shifted 7 mm BACK to keep its
    # rear face on y = 0 rather than behind it -- the same rule as the deck.
    over = 7.0
    lid = bkit.rounded_box("CisternLid", cw + 2 * over, cl + 2 * over, 32.0,
                           r=10.0, segments=3,
                           centre=(0.0, cl / 2.0 + over, 800.0 - 16.0), mat=lid_mat)

    # ---- seat: a round annulus scaled into an oval --------------------------
    # 392 mm across, scaled along y to the bowl's 520 mm length. Scaled in
    # OBJECT space and measured through matrix_world, so bbox() reports it.
    seat = bkit.tube("Seat", 196.0, 140.0, SPEC["seat_thickness"],
                     segments=96, centre=(0.0, BOWL_CY, BOWL_RIM_Z + 4.0),
                     mat=seat_mat)
    seat.scale = (1.0, L / 392.0, 1.0)
    bpy_view_layer_update()
    return dict(spec=SPEC, parts=5)


def bpy_view_layer_update():
    """Non-uniform object scale is cached in matrix_world like a move is."""
    import bpy
    bpy.context.view_layer.update()


CHECKS = [
    dict(name="bowl_width", mm=380.0, tol=0.5, how="bbox_x", part="Bowl"),
    dict(name="bowl_height", mm=400.0, tol=0.5, how="bbox_z", part="Bowl"),
    dict(name="bowl_length", mm=520.0, tol=0.5, how="bbox_y", part="Bowl"),
    dict(name="overall_length", mm=700.0, tol=0.5, how="bbox_y"),
    dict(name="overall_height", mm=800.0, tol=0.5, how="bbox_z"),
]
