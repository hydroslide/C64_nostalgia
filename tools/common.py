"""Shared loaders: everything in one Z-up frame.
Source: raw Y-up -> (x, -z, y). Front (buttons/ports) = -Y, SD/DIN end = -X, bezel = +X. Seam at z=0.
Target: recentred in XY, z from 0 (outer base). Lid flipped 180 deg about Y onto rim (z 26..28).
"""
import os
import numpy as np, trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # project root (this file lives in tools/)
SRC = os.path.join(ROOT, "real_files", "source")
TGT = os.path.join(ROOT, "real_files", "target")
WORK = os.path.join(ROOT, "work")          # intermediate meshes (regenerable; not tracked in git)
OUTPUT = os.path.join(ROOT, "output")      # print-ready STLs (tracked in git)
os.makedirs(WORK, exist_ok=True)


def yup_to_zup(m):
    return trimesh.Trimesh(np.column_stack([m.vertices[:, 0], -m.vertices[:, 2], m.vertices[:, 1]]), m.faces)


def load_source():
    return {n: yup_to_zup(trimesh.load(os.path.join(SRC, f"pi1541_case_{n}.stl"))) for n in ["top", "bottom", "front"]}


def load_target():
    tb = trimesh.load(os.path.join(TGT, "obj_1_Case Bottom.stl"))
    tl = trimesh.load(os.path.join(TGT, "obj_2_Assembly.stl"))
    parts = sorted(tl.split(only_watertight=False), key=lambda p: -len(p.faces))
    lid, logo = parts[0], parts[1]
    c = tb.bounds.mean(0)
    tb.apply_translation([-c[0], -c[1], -tb.bounds[0][2]])
    R = trimesh.transformations.rotation_matrix(np.pi, [0, 1, 0])
    for m in (lid, logo):
        m.apply_transform(R)
    off = [tb.bounds[0][0] - lid.bounds[0][0], tb.bounds[0][1] - lid.bounds[0][1], tb.bounds[1][2] + 2 - lid.bounds[1][2]]
    for m in (lid, logo):
        m.apply_translation(off)
    return {"bottom": tb, "lid": lid, "logo": logo}


def section_polys(mesh, origin, normal):
    """Planar section -> shapely polygons (material, with interiors = holes) in the 2 world axes other than the normal.
    Returns (polys, keep_axes)."""
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    ax = int(np.argmax(np.abs(np.array(normal, float))))
    keep = [i for i in range(3) if i != ax]
    if sec is None:
        return [], keep
    from shapely.geometry import Polygon
    rings = [Polygon(e[:, keep]).buffer(0) for e in sec.discrete if len(e) > 3]
    rings = [r for r in rings if r.area > 1e-4]
    rings.sort(key=lambda r: -r.area)
    depth = [sum(1 for j in range(i) if rings[j].contains(rings[i].representative_point())) for i in range(len(rings))]
    polys = []
    for i, r in enumerate(rings):
        if depth[i] % 2 == 0:
            hs = [rings[j] for j in range(len(rings)) if depth[j] == depth[i] + 1 and r.contains(rings[j].representative_point())]
            polys.append(Polygon(r.exterior, [h.exterior.coords for h in hs if h.geom_type == "Polygon"]))
    return polys, keep


def describe(poly):
    b = poly.bounds
    return f"x {b[0]:7.2f}..{b[2]:7.2f}  y {b[1]:7.2f}..{b[3]:7.2f}  ({b[2]-b[0]:5.2f} x {b[3]-b[1]:5.2f}) area {poly.area:7.1f}"


