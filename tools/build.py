"""Build Pi1541 source case (Pi 3B shell) adapted for the Pi Zero board from the target case.

Frames: work in source Z-up frame (see common.py). Target->source placement is a pure translation (DX, DY, DZ).
Outputs are exported back to the source's original Y-up frame so they line up with the untouched front bezel.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from shapely.geometry import box as sbox
from shapely import affinity

OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- placement
DX, DY, DZ = -15.08, -10.56, -18.0   # floors aligned; board flush to front inner wall; 0.34 mm clear of corner screw post
EPS = 0.05

U = lambda ms: trimesh.boolean.union(ms, engine="manifold")
D = lambda a, b: trimesh.boolean.difference([a, b], engine="manifold")
I = lambda a, b: trimesh.boolean.intersection([a, b], engine="manifold")
BOX = lambda lo, hi: trimesh.creation.box(bounds=[lo, hi])
mv = lambda m, dx=DX, dy=DY, dz=DZ: m.copy().apply_translation([dx, dy, dz]) or m


def moved(m, dx=DX, dy=DY, dz=DZ):
    m = m.copy(); m.apply_translation([dx, dy, dz]); return m


def extrude_section(mesh, axis, at, clip2d, lo, hi):
    """Section `mesh` with the plane axis=at, clip the 2D profile to clip2d (shapely geom, in the two remaining
    world axes in increasing order), and extrude it along `axis` from lo to hi. Returns a mesh."""
    n = np.eye(3)[axis]
    polys, keep = section_polys(mesh, n * at, n)
    solids = []
    for p in polys:
        q = p.intersection(clip2d)
        for g in getattr(q, "geoms", [q]):
            if g.geom_type != "Polygon" or g.area < 1e-3:
                continue
            m = trimesh.creation.extrude_polygon(g, hi - lo)   # local XY = (keep[0], keep[1]), local Z = extrusion
            # map local (X,Y,Z) -> world, as a proper rotation
            M = np.zeros((4, 4)); M[3, 3] = 1
            if axis == 0:   # keep = (y, z); Z -> x
                M[:3, :3] = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]; M[:3, 3] = [lo, 0, 0]
            elif axis == 1:  # keep = (x, z); Z -> -y  (start at hi, extrude towards -y)
                M[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]; M[:3, 3] = [0, hi, 0]
            else:            # keep = (x, y); Z -> z
                M[:3, :3] = np.eye(3); M[:3, 3] = [0, 0, lo]
            m.apply_transform(M)
            solids.append(m)
    return U(solids) if len(solids) > 1 else solids[0]


def replace_region(shell, region_lo, region_hi, axis, donor_at):
    """Delete shell material inside the region box and refill it with the shell's own cross-section taken at
    `donor_at` along `axis`, extruded across the region. Keeps fillets/tapers/lips continuous."""
    lo = np.array(region_lo, float); hi = np.array(region_hi, float)
    keep = [i for i in range(3) if i != axis]
    clip = sbox(lo[keep[0]] - EPS, lo[keep[1]] - EPS, hi[keep[0]] + EPS, hi[keep[1]] + EPS)
    donor = extrude_section(shell, axis, donor_at, clip, lo[axis] - EPS, hi[axis] + EPS)
    return U([D(shell, BOX(lo, hi)), donor])


def through(c, d):
    """Prolong a cutter past a coincident surface (avoids zero-thickness films): union with a copy shifted by d."""
    return U([c, moved(c, *d)])


def negative(solid, lo, hi):
    """Empty space of `solid` inside box lo..hi (i.e. the exact shape of an opening, chamfers included)."""
    return D(BOX(lo, hi), solid)


src = load_source(); tgt = load_target()
tsolid = U([tgt["bottom"], tgt["lid"]])
report = {}

# ================================================================ BOTTOM
bot = src["bottom"]
# 1. front wall: fill Pi 3B micro-USB / HDMI / audio (profile from x=-31, which is hole-free, same recessed panel)
bot = replace_region(bot, [-43.8, -40, -18], [10.4, -28.0, 0.5], 0, -31.0)
# 2. -X end: fill SD U-notch, finger scoop and end-wall slot (profile from y=-17)
bot = replace_region(bot, [-60, -15.5, -20], [-33.0, 15.5, 0.5], 1, -17.0)
# 3. remove the 4 Pi 3B standoff bosses, re-close floor
for (bx, by) in [(-45.58, -25.08), (-45.58, 25.08), (12.42, -25.08), (12.42, 25.08)]:
    bot = D(bot, BOX([bx - 3.0, max(by - 3.0, -28.28), -16.0], [bx + 3.0, min(by + 3.0, 28.28), -5.0]))
    bot = U([bot, BOX([bx - 3.0, by - 3.0, -17.0], [bx + 3.0, min(by + 3.0, 28.2), -16.0])])
# 4. Zero posts + locating pins, copied from the target (includes 1 mm of floor so they weld in)
posts = []
for (px, py) in [(-30, -14.25), (28, -14.25), (-30, 8.75), (28, 8.75)]:
    cyl = trimesh.creation.cylinder(radius=3.2, segment=None, sections=64,
                                    transform=trimesh.transformations.translation_matrix([px, py, 4.25]), height=6.5)
    posts.append(moved(I(tgt["bottom"], cyl)))
bot = U([bot] + posts)
# 5. cut Zero ports (exact target openings; outer face aligned to the source panel face y=-29.65)
yshift = -29.65 - (-19.75 + DY)
ports = []
for (x0, x1, z0, z1) in [(-27.6, -14.6, 6.3, 11.3), (3.4, 12.4, 6.3, 10.3), (16.0, 25.0, 6.3, 10.3)]:
    ports.append(moved(negative(tgt["bottom"], [x0 - 1.5, -19.75, z0 - 1.5], [x1 + 1.5, -17.75, z1 + 1.5]), dy=DY + yshift))
bot = D(bot, through(U(ports), (0, -1.0, 0)))
# 6. SD slot through -X end wall (exact target opening; outer face placed at the source wall's outer face)
sd = negative(tgt["bottom"], [-35.5, -9.5, 3.5], [-33.5, 8.0, 12.0])
sd.apply_translation([-56.3 - (-35.5), DY, DZ])
sd = U([sd, moved(BOX([-35.5, -7.9, 6.3], [-33.0, 6.4, 9.2]), dx=-56.3 + 35.5 + 2.0)])  # make sure it goes fully through the 1.5 mm wall
bot = D(bot, sd)

# ================================================================ TOP (common part)
top = src["top"]
# 1. fill Pi 3B button holes in the front wall (profile from x=-31, between two buttons)
top = replace_region(top, [-39.3, -40, -2], [7.3, -28.0, 18.5], 0, -31.0)
# 2. fill the DIN socket opening (top plate + end wall) incl. its ~1 mm edge round-over, profile from y=-23.1
top = replace_region(top, [-60, -23.1, -2], [-32.6, 23.1, 20], 1, -23.1)
from ops import hollow_rear_wall
top = hollow_rear_wall(top)   # back to a 1.5 mm rear wall across the old opening (donor was the solid corner block)
# 3. close the old display window skin incl. its ~0.8 mm edge round-over (stops at y=4.08 where the vent grooves begin)
top = U([top, BOX([-29.1, -12.45, 15.9], [-0.35, 4.08, 17.5])])
# 4. light tube around the Zero display window: 1.5 mm walls from the Zero lid underside (z_t 26) up into the plate
win_in = np.array([[-20.2, -5.45], [4.7, 8.95]])
tube = BOX([win_in[0, 0] - 1.5 + DX, win_in[0, 1] - 1.5 + DY, 26.0 + DZ], [win_in[1, 0] + 1.5 + DX, win_in[1, 1] + 1.5 + DY, 16.2])
top = U([top, tube])
# 5. hat hold-downs / DIN connector channel / plateaus from the Zero lid (below the rim skirt), extended to the plate
lid_int = I(tgt["lid"], BOX([-33.5, -17.95, 18.4], [33.5, 17.75, 24.0]))
ext_top_t = 16.2 - DZ
polys, _ = section_polys(lid_int, [0, 0, 23.9], [0, 0, 1])
def hollow(p, wall=1.2):
    inner = p.buffer(-wall, join_style=2)
    return p if inner.is_empty or inner.area < 4 else p.difference(inner)
exts = []
for p in polys:
    if p.area <= 3:
        continue
    h = hollow(p)
    for g in getattr(h, "geoms", [h]):
        if g.area > 0.5:
            exts.append(trimesh.creation.extrude_polygon(g, ext_top_t - 23.9).apply_translation([0, 0, 23.9]))
internals = moved(U([lid_int] + exts))
top = U([top, internals])
# 6. button holes (exact lid notches), trimmed to start at z=2.0 so they sit inside the flat panel like the source's
btns = [moved(I(negative(tsolid, [xc - 2.7, -19.75, 20.0], [xc + 2.7, -17.75, 26.5]), BOX([xc - 2.05, -30, 0], [xc + 2.05, 0, 40])), dy=DY + yshift)   # exact 4.0-wide notch
        for xc in [-22.5, -11.75, -1.0, 9.75, 20.5]]
top = D(top, through(U(btns), (0, -1.0, 0)))
# 7. display window (exact lid window incl. outer chamfer, plate top aligned 28 -> 17.5) + through the tube
ZP = 17.5 - 28.0
win = through(moved(negative(tgt["lid"], [-21.5, -6.6, 26.0], [6.0, 10.1, 28.0]), dz=ZP), (0, 0, 1.0))
win = U([win, BOX([win_in[0, 0] + DX, win_in[0, 1] + DY, 7.0], [win_in[1, 0] + DX, win_in[1, 1] + DY, 16.5])])
top = D(top, win)
# 8. rotary encoder hole
enc = through(moved(negative(tgt["lid"], [-31.0, -6.75, 26.0], [-22.0, 2.25, 28.0]), dz=ZP), (0, 0, 1.0))
top = D(top, enc)
# 9. slot variant
slot = through(moved(negative(tgt["lid"], [24.0, -12.25, 26.0], [32.0, 7.25, 28.0]), dz=ZP), (0, 0, 1.0))
slot = U([slot, BOX([24.5 + DX, -11.75 + DY, 0.0], [31.5 + DX, 6.75 + DY, 16.5])])
top_slot = D(top, slot)
top_noslot = top

# ================================================================ export (back to the source's Y-up frame)
TO_YUP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], float)
parts = {"bottom": bot, "top_slot": top_slot, "top_noslot": top_noslot}
def clean(m):
    bodies = [b for b in m.split(only_watertight=False) if abs(b.volume) > 1.0]
    return bodies[0] if len(bodies) == 1 else trimesh.util.concatenate(bodies)
parts = {k: clean(v) for k, v in parts.items()}
for name, m in parts.items():
    e = m.copy(); e.apply_transform(TO_YUP)
    path = os.path.join(OUT, f"pi1541_zero_case_{name}.stl")
    e.export(path)
    m.export(os.path.join(WORK, f"zup_{name}.stl"))
    print(f"{name:11s}: watertight={m.is_watertight} bodies={len(m.split(only_watertight=False))} "
          f"volume={m.volume:.0f} mm3 faces={len(m.faces)} -> {path}")
import shutil
shutil.copy(os.path.join(SRC, "pi1541_case_front.stl"), os.path.join(OUT, "pi1541_zero_case_front.stl"))
internals.export(os.path.join(WORK, "zup_internals.stl"))
print("front bezel copied unchanged")







