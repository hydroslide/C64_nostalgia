"""Shared mesh operations + the fills common to every Pi Zero conversion of the source case (Z-up source frame)."""
import os
import numpy as np, trimesh
from shapely.geometry import box as sbox
from common import section_polys, ROOT, SRC

EPS = 0.05
U = lambda ms: trimesh.boolean.union(ms, engine="manifold")
D = lambda a, b: trimesh.boolean.difference([a, b], engine="manifold")
I = lambda a, b: trimesh.boolean.intersection([a, b], engine="manifold")
BOX = lambda lo, hi: trimesh.creation.box(bounds=[lo, hi])


def moved(m, dx=0.0, dy=0.0, dz=0.0):
    m = m.copy(); m.apply_translation([dx, dy, dz]); return m


def xformed(m, T):
    m = m.copy(); m.apply_transform(T); return m


def extrude_section(mesh, axis, at, clip2d, lo, hi):
    """Section `mesh` at plane axis=at, clip the 2D profile, extrude it along `axis` from lo to hi."""
    n = np.eye(3)[axis]
    polys, keep = section_polys(mesh, n * at, n)
    solids = []
    for p in polys:
        q = p.intersection(clip2d)
        for g in getattr(q, "geoms", [q]):
            if g.geom_type != "Polygon" or g.area < 1e-3:
                continue
            m = trimesh.creation.extrude_polygon(g, hi - lo)
            M = np.eye(4)
            if axis == 0:
                M[:3, :3] = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]; M[:3, 3] = [lo, 0, 0]
            elif axis == 1:
                M[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]; M[:3, 3] = [0, hi, 0]
            else:
                M[:3, 3] = [0, 0, lo]
            m.apply_transform(M)
            solids.append(m)
    return U(solids) if len(solids) > 1 else solids[0]


def replace_region(shell, region_lo, region_hi, axis, donor_at):
    """Delete material inside the region box and refill it with the shell's own cross-section at donor_at."""
    lo = np.array(region_lo, float); hi = np.array(region_hi, float)
    keep = [i for i in range(3) if i != axis]
    clip = sbox(lo[keep[0]] - EPS, lo[keep[1]] - EPS, hi[keep[0]] + EPS, hi[keep[1]] + EPS)
    donor = extrude_section(shell, axis, donor_at, clip, lo[axis] - EPS, hi[axis] + EPS)
    return U([D(shell, BOX(lo, hi)), donor])


def negative(solid, lo, hi):
    """Empty space of `solid` inside box lo..hi (exact opening shape, chamfers included)."""
    return D(BOX(lo, hi), solid)


def through(c, *shifts):
    """Prolong a cutter: union with copies shifted by each given (dx,dy,dz)."""
    return U([c] + [moved(c, *s) for s in shifts])


def hollow_extrusions(polys, z0, height, wall=1.2, min_area=3.0):
    out = []
    for p in polys:
        if p.area <= min_area:
            continue
        inner = p.buffer(-wall, join_style=2)
        h = p if inner.is_empty or inner.area < 4 else p.difference(inner)
        for g in getattr(h, "geoms", [h]):
            if g.area > 0.5:
                out.append(trimesh.creation.extrude_polygon(g, height).apply_translation([0, 0, z0]))
    return out


def clean(m):
    bodies = [b for b in m.split(only_watertight=False) if abs(b.volume) > 1.0]
    return bodies[0] if len(bodies) == 1 else trimesh.util.concatenate(bodies)


TO_YUP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)


def export(parts, prefix, scratch):
    out = os.path.join(ROOT, "output"); os.makedirs(out, exist_ok=True)
    for name, m in parts.items():
        m = clean(m)
        m.export(os.path.join(scratch, f"zup_{prefix}_{name}.stl"))
        e = m.copy(); e.apply_transform(TO_YUP)
        path = os.path.join(out, f"{prefix}_{name}.stl"); e.export(path)
        r = trimesh.load(path)   # verify the file itself, after STL round-trip
        assert r.is_watertight and r.is_winding_consistent, f"{path} is not a closed solid after reload"
        print(f"{name:11s}: watertight={m.is_watertight} volume={m.volume:.0f} mm3 faces={len(m.faces)} -> {path}")


# ------------------------------------------------------------------ fills shared by all Zero variants
PI3_BOSSES = [(-45.58, -25.08), (-45.58, 25.08), (12.42, -25.08), (12.42, 25.08)]


def fill_bottom_common(bot):
    # front wall: Pi 3B micro-USB / HDMI / audio (profile from hole-free x=-31 inside the same recessed panel)
    bot = replace_region(bot, [-43.8, -40, -18], [10.4, -28.0, 0.5], 0, -31.0)
    # -X end: SD U-notch, finger scoop, end-wall slot (profile from y=-17)
    bot = replace_region(bot, [-60, -15.5, -20], [-33.0, 15.5, 0.5], 1, -17.0)
    # Pi 3B standoff bosses -> flat floor
    for (bx, by) in PI3_BOSSES:
        bot = D(bot, BOX([bx - 3.0, max(by - 3.0, -28.28), -16.0], [bx + 3.0, min(by + 3.0, 28.28), -5.0]))
        bot = U([bot, BOX([bx - 3.0, max(by - 3.0, -28.2), -17.0], [bx + 3.0, min(by + 3.0, 28.2), -16.0])])
    return bot


def hollow_rear_wall(top):
    """The DIN fill copies the profile of the solid 7.5 mm rear corner blocks. Across the old opening, pocket it back to
    a 1.5 mm wall following the outer slope (x_out = -56.68 + 0.105 (z-3)), above the original 1.5 mm sill,
    up to the plate underside (z=16). y range = the original opening (-21.25..21.75)."""
    from shapely.geometry import Polygon
    xin = lambda z: -56.68 + 0.105 * (z - 3.0) + 1.5
    prof = Polygon([(xin(1.5), 1.5), (-49.2, 1.5), (-49.2, 16.0), (xin(16.0), 16.0)])
    y0, y1 = -21.25, 21.75
    m = trimesh.creation.extrude_polygon(prof, y1 - y0)
    M = np.eye(4); M[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]; M[:3, 3] = [0, y1, 0]
    m.apply_transform(M)
    return D(top, m)


def fill_top_common(top):
    # Pi 3B button holes in the front wall (profile from x=-31, between two buttons)
    top = replace_region(top, [-39.3, -40, -2], [7.3, -28.0, 18.5], 0, -31.0)
    # DIN socket opening (top plate + end wall) incl. its ~1 mm edge round-over, profile from y=-23.1
    top = replace_region(top, [-60, -23.1, -2], [-32.6, 23.1, 20], 1, -23.1)
    top = hollow_rear_wall(top)
    # old display window skin incl. its ~0.8 mm round-over (stops at y=4.08 where the vent grooves begin)
    top = U([top, BOX([-29.1, -12.45, 15.9], [-0.35, 4.08, 17.5])])
    return top

