"""
Ocarina-themed case for the Dilemma DIY 3x5_2 (and 3x5_2_trackball).

mechanical/cases/3x5_2/thin/thin_v1_26.stl is only the dimensional base: from
it come the outline, wall and USB opening, the three M3 posts with nut pockets
(H1, H2, H5) and the PCB ledges along the wall. Everything else is new:

  * floor: triangle lattice (2.2 mm bars) ending in a solid 2 mm rim; partial
    cells smaller than half a full cell or narrower than 4 mm are filled
  * round medallion with an inlay recess on the underside
      - left half: three triangles in a ring
      - right half: an ocarina in a ring
  * zig-zag band of triangles engraved on the outer wall
  * round opening for the reset button (on the bottom face of both halves)
  * blind pockets from the top for the low-head screws of the trackball
    standoffs (H6-H9), invisible from below
  * the free-standing PCB rib of the thin case becomes a round pillar
  * rubber-foot recesses for 10 mm feet; the feet that sat on H6 and H8 moved

Outputs (written next to this script):
  case_left.stl / case_right.stl    case, with the inlay recess
  inlay_left.stl / inlay_right.stl  inlay, 0.08 mm smaller per side; print
                                    separately and glue into the recess

Requires: numpy, scipy, trimesh, manifold3d, shapely, networkx.
Run:  python build_ocarina_case.py
"""

import math
import os

import manifold3d as mf
import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "thin", "thin_v1_26.stl")

# --- dimensions (mm) --------------------------------------------------------
FLOOR_TOP = 1.5           # floor top of the original case
WALL_T = 1.83             # measured wall thickness
RIM = 2.0                 # solid floor strip along the wall; the lattice ends in it
STRUT = 2.2               # lattice bar width
GRID_H = 14.0             # distance between parallel lattice bars
MED_C = (-3.0, 12.0)      # medallion centre (left-half frame, top view)
MED_R = 18.0
INLAY_DEPTH = 0.6         # 3 layers at 0.2 mm
PRESSFIT = 0.08
FOOT_R = 5.25             # recess for 10 mm feet
FOOT_PAD_R = 7.0
FOOT_DEPTH = 1.0
BAND_DEPTH = 0.5          # outer wall engraving
BAND_Z0, BAND_Z1 = 1.1, 4.1

# PCB -> case frame: x = px - 173.03, y = 71.2 - py (fitted on H1, H2, H5)
def pcb(px, py):
    return (px - 173.03, 71.2 - py)

H6, H7, H8, H9 = pcb(234.53, 36.10), pcb(205.13, 68.10), pcb(236.13, 68.10), pcb(206.53, 36.10)
RESET = pcb(220.05, 54.07)
SCREW_CLEAR_R = 3.6       # low-head M3 (6 mm head) + margin
SCREW_POCKET = 1.0        # pocket depth from the floor top; 0.5 mm floor left
RESET_R = 5.5             # round opening: clears the 6x6 button and its legs
PILLAR_R = 2.2

FEET = [(55.0, -4.5), (48.0, 30.0), (30.0, -40.0), (5.0, -30.0),
        (-18.0, 42.0), (-59.11, 21.92), (-60.0, -20.0)]   # moved off H6 (59.6, 32.3) and H8 (60, -5)


# --- helpers ----------------------------------------------------------------
def polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


def to_cs(g):
    contours = []
    for p in polys(g):
        p = p.buffer(0)
        for q in polys(p):
            contours.append(np.asarray(q.exterior.coords)[:-1])
            contours += [np.asarray(i.coords)[:-1] for i in q.interiors]
    return mf.CrossSection(contours, mf.FillRule.EvenOdd)


def prism(g, z0, z1):
    return mf.Manifold.extrude(to_cs(g), z1 - z0).translate((0, 0, z0))


def to_manifold(tm):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                               tri_verts=np.asarray(tm.faces, np.uint32)))


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3],
                           np.asarray(mesh.tri_verts), process=True)


def tri(cx, cy, side, up=True):
    h = side * math.sqrt(3) / 2
    s = 1 if up else -1
    return Polygon([(cx - side / 2, cy - s * h / 3), (cx + side / 2, cy - s * h / 3),
                    (cx, cy + s * 2 * h / 3)])


# --- emblems (drawn as seen from BELOW; mirrored into model space later) -----
def ring(c, r_in, r_out):
    return Point(c).buffer(r_out, 128).difference(Point(c).buffer(r_in, 128))


def emblem_triangles(c):
    side = 24.0
    h = side * math.sqrt(3) / 2
    cx, cy = c
    base_y = cy - h / 3
    small = side / 2
    sh = small * math.sqrt(3) / 2
    parts = []
    for (x, y) in [(cx - small / 2, base_y + sh / 3), (cx + small / 2, base_y + sh / 3),
                   (cx, base_y + sh + sh / 3)]:
        parts.append(affinity.scale(tri(x, y, small), 0.9, 0.9, origin=(x, y)))
    dots = [Point(cx + 15.6 * math.cos(a), cy + 15.6 * math.sin(a)).buffer(0.9, 32)
            for a in np.radians([-90, 30, 150])]
    return unary_union(parts + [ring(c, 13.9, 15.0)] + dots)


def emblem_ocarina(c):
    cx, cy = c
    body = affinity.scale(Point(0, 0).buffer(1, 128), 8.6, 6.0)
    mouth = LineString([(5.5, 2.0), (9.6, 4.6)]).buffer(1.7, cap_style=1)
    shape = unary_union([body, mouth])
    holes = [Point(x, y).buffer(r, 48) for x, y, r in
             [(-4.6, 1.2, 1.1), (-1.2, 2.7, 0.9), (2.0, 2.2, 0.9),
              (-3.0, -2.3, 0.8), (1.0, -2.9, 0.8)]]
    shape = shape.difference(unary_union(holes))
    shape = affinity.rotate(shape, -20, origin=(0, 0))
    shape = affinity.translate(shape, cx - 0.8, cy - 0.6)
    dots = [Point(cx + 15.6 * math.cos(a), cy + 15.6 * math.sin(a)).buffer(0.9, 32)
            for a in np.radians([-90, 30, 150])]
    return unary_union([shape, ring(c, 13.9, 15.0)] + dots)


# --- floor pattern ------------------------------------------------------------
def tri_lattice(region, origin):
    ox, oy = origin
    bars = []
    for ang in (0, 60, 120):
        a = math.radians(ang)
        d = np.array([math.cos(a), math.sin(a)])
        n = np.array([-d[1], d[0]])
        for k in range(-12, 13):
            p = np.array([ox, oy]) + n * k * GRID_H
            bars.append(LineString([p - d * 200, p + d * 200]).buffer(STRUT / 2, cap_style=2))
    return unary_union(bars).intersection(region)


def wall_band(outline, wall):
    """Alternating up/down triangles engraved on the outer wall."""
    ring_ = LineString(outline.exterior.coords)
    L = ring_.length
    pitch = 5.2
    base = 3.2
    cutters = []
    probe = wall.buffer(0.05)
    for i in range(int(L / (pitch / 2))):
        s = i * pitch / 2
        p = np.array(ring_.interpolate(s).coords[0])
        a = np.array(ring_.interpolate((s - 2.5) % L).coords[0])
        b = np.array(ring_.interpolate((s + 2.5) % L).coords[0])
        a2 = np.array(ring_.interpolate((s - 0.5) % L).coords[0])
        b2 = np.array(ring_.interpolate((s + 0.5) % L).coords[0])
        t1, t2 = p - a, b - p
        if np.linalg.norm(t1) < 2 or np.linalg.norm(t2) < 2:
            continue
        cosang = np.dot(t1, t2) / np.linalg.norm(t1) / np.linalg.norm(t2)
        if cosang < math.cos(math.radians(12)):
            continue
        t = (b2 - a2) / np.linalg.norm(b2 - a2)
        n = np.array([t[1], -t[0]])
        if outline.contains(Point(p + n * 0.5)):
            n = -n
        # must be real wall behind this point (skips the USB/TRRS opening)
        if not (probe.contains(Point(p - n * 0.9)) and probe.contains(Point(p - n * 0.3))):
            continue
        up = (i % 2 == 0)
        if up:
            prof = [(-base / 2, BAND_Z0), (base / 2, BAND_Z0), (0, BAND_Z1)]
        else:
            prof = [(-base / 2, BAND_Z1), (0, BAND_Z0), (base / 2, BAND_Z1)]
        cs = mf.CrossSection([np.array(prof)], mf.FillRule.EvenOdd)
        pr = mf.Manifold.extrude(cs, 2.0)       # (u, z) profile, extruded along +w
        # local (u, z, w) -> world (t, Z, -n); w runs 0..2, from outside the
        # wall to BAND_DEPTH inside it. Keep the frame right-handed.
        if np.linalg.det(np.array([[t[0], 0, -n[0]], [t[1], 0, -n[1]], [0, 1, 0]])) < 0:
            t = -t
        o = p + n * (2.0 - BAND_DEPTH)
        M = np.array([[t[0], 0, -n[0], o[0]],
                      [t[1], 0, -n[1], o[1]],
                      [0, 1, 0, 0]], dtype=float)
        cutters.append(pr.transform(M))
    return mf.Manifold.batch_boolean(cutters, mf.OpType.Add), len(cutters)


# --- build ------------------------------------------------------------------
def main():
    src = trimesh.load(SRC)
    src.merge_vertices(digits_vertex=4)   # STL has duplicated vertices
    orig = to_manifold(src)
    assert orig.status() == mf.Error.NoError, orig.status()

    def sl(z):
        p, _ = src.section([0, 0, 1], [0, 0, z]).to_2D(to_2D=np.eye(4))
        return unary_union(p.polygons_full)

    outline = Polygon(max(polys(sl(0.25)), key=lambda g: g.area).exterior)
    wall = sl(4.0)
    # replace the whole old floor up to the wall, so no voronoi leftovers remain
    region = outline.buffer(-(WALL_T + 0.1), join_style=2)
    rim = outline.difference(outline.buffer(-(WALL_T + RIM), join_style=2))

    raised = [g for g in polys(sl(2.0).difference(wall.buffer(0.3))) if g.area > 0.5]
    # a rib that touches neither the wall nor a screw is replaced by a pillar
    ribs = [g for g in raised if not g.interiors and g.distance(wall) > 0.5]
    kept = [g for g in raised if g not in ribs]
    pillars = unary_union([g.centroid.buffer(PILLAR_R, 48) for g in ribs])
    # exterior only: the post rings enclose the nut pockets, which must stay empty
    keep = unary_union([Polygon(g.exterior).buffer(0.05) for g in kept])
    voids = unary_union([Polygon(i) for g in kept for i in g.interiors])
    pads = unary_union([Polygon(g.exterior).buffer(1.5) for g in kept] + [pillars.buffer(1.5)])
    cut = region.difference(keep)

    screws = unary_union([Point(p).buffer(SCREW_CLEAR_R, 64) for p in (H6, H7, H8, H9)])
    reset = Point(RESET).buffer(RESET_R, 64)
    med = Point(MED_C).buffer(MED_R + 1.6, 128)
    feet_pads = unary_union([Point(f).buffer(FOOT_PAD_R, 64) for f in FEET])
    feet_rec = unary_union([Point(f).buffer(FOOT_R, 64) for f in FEET])

    floor = unary_union([tri_lattice(region, MED_C), med, feet_pads, pads, rim,
                         screws.buffer(1.8), reset.buffer(1.8)])
    floor = floor.intersection(outline)
    # close gaps under 1.2 mm, then fill partial cells where the lattice meets
    # the rim or a pad: holes under half a full cell or narrower than 4 mm
    floor = floor.buffer(0.6, join_style=1).buffer(-0.6, join_style=1)
    cell = (2 * GRID_H / math.sqrt(3)) * (1 - STRUT * math.sqrt(3) / GRID_H)  # hole side
    min_hole = 0.5 * cell * cell * math.sqrt(3) / 4

    def keep_hole(r):
        h = Polygon(r)
        return h.area >= min_hole and not h.buffer(-2.0).is_empty

    floor = unary_union([Polygon(p.exterior, [i for i in p.interiors if keep_hole(i)])
                         for p in polys(floor)])
    floor = floor.intersection(outline).difference(reset).difference(voids.buffer(0.05))

    body = orig - prism(cut, -1, FLOOR_TOP + 0.1)
    if ribs:
        body = body - prism(unary_union(ribs).buffer(0.05), -1, 6)
    body = body + prism(floor, 0, FLOOR_TOP) + prism(pillars, 0, 3.5)
    body = body - prism(feet_rec, -1, FOOT_DEPTH)
    body = body - prism(reset, -1, FLOOR_TOP + 0.5)
    body = body - prism(screws, FLOOR_TOP - SCREW_POCKET, FLOOR_TOP + 0.5)

    band, nband = wall_band(outline, wall)
    body = body - band
    print("wall triangles:", nband)

    # emblems: drawn as seen from below, so mirror x into model space
    def model(g, mirror_x):
        return affinity.scale(g, -1, 1, origin=(MED_C[0], MED_C[1])) if mirror_x else g

    out = {}
    # left half: model frame = original
    emb_l = model(emblem_triangles(MED_C), True)
    case_l = body - prism(emb_l, -1, INLAY_DEPTH)
    out["left"] = (case_l, emb_l)

    # right half: mirror whole body across x, emblem centre moves to (-cx, cy)
    body_r = body.mirror((1, 0, 0))
    c_r = (-MED_C[0], MED_C[1])
    emb_r = emblem_ocarina(c_r)
    emb_r = affinity.scale(emb_r, -1, 1, origin=c_r)
    case_r = body_r - prism(emb_r, -1, INLAY_DEPTH)
    out["right"] = (case_r, emb_r)

    for side, (case, emb) in out.items():
        # drop zero-volume slivers that the booleans leave at tangent edges
        case = mf.Manifold.compose([q for q in case.decompose() if q.volume() > 1.0])
        tm_case = to_trimesh(case)
        tm_inlay = to_trimesh(prism(emb.buffer(-PRESSFIT, join_style=2), 0, INLAY_DEPTH))
        tm_case.export(os.path.join(HERE, f"case_{side}.stl"))
        tm_inlay.export(os.path.join(HERE, f"inlay_{side}.stl"))
        parts = len(to_manifold(tm_case).decompose())
        print(f"{side}: volume={tm_case.volume:.0f}mm3 "
              f"bodies={parts} inlay_area={emb.area:.0f}mm2 bounds={tm_case.bounds.round(2).tolist()}")


if __name__ == "__main__":
    main()
