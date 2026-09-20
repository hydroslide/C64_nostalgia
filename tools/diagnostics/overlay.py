"""Overlay target (Pi Zero) features onto source (Pi 3B) walls at a proposed placement."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
from shapely import affinity
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

S = os.path.dirname(__file__)
src = load_source(); tgt = load_target()

# Proposed placement: Zero board's SD/front corner where the Pi 3B board's corner was; floors aligned.
DX, DY, DZ = float(sys.argv[1]) if len(sys.argv) > 1 else -15.58, -10.56, -18.0
print("placement dx,dy,dz =", DX, DY, DZ)

def union_section(meshes, origin, normal):
    ps = []
    for m in meshes:
        p, keep = section_polys(m, origin, normal)
        ps += p
    return unary_union(ps), keep

def holes_of(geom, minarea=0.5):
    out = []
    for g in getattr(geom, "geoms", [geom]):
        out += [Polygon(h) for h in g.interiors if Polygon(h).area > minarea]
    return out

def draw(ax, geom, **kw):
    for g in getattr(geom, "geoms", [geom]):
        x, y = g.exterior.xy; ax.fill(x, y, alpha=kw.get("alpha", 0.35), color=kw.get("color", "gray"), lw=0)
        ax.plot(x, y, color=kw.get("edge", "k"), lw=0.7)
        for h in g.interiors:
            x, y = zip(*h.coords); ax.fill(x, y, color="white"); ax.plot(x, y, color=kw.get("edge", "k"), lw=0.7)

def draw_outline(ax, polys, color="red", lw=1.4, label=None):
    for i, p in enumerate(polys):
        x, y = p.exterior.xy; ax.plot(x, y, color=color, lw=lw, label=label if i == 0 else None)

fig, axs = plt.subplots(2, 2, figsize=(20, 12))

# 1. FRONT WALL (XZ). source: bottom+top at y=-29.0 ; target: bottom+lid at y=-18.75, shifted
sf, _ = union_section([src["bottom"], src["top"]], [0, -29.0, 0], [0, 1, 0])
tf, _ = union_section([tgt["bottom"], tgt["lid"]], [0, -18.75, 0], [0, 1, 0])
th = [affinity.translate(h, DX, DZ) for h in holes_of(tf)]
ax = axs[0, 0]; draw(ax, sf); draw_outline(ax, th, label="Zero openings (cut)")
ax.axhline(0, color="b", ls=":", lw=0.8); ax.set_title("FRONT wall (looking at it from outside, X horizontal, Z up). grey=source wall w/ holes, red=Zero openings")
ax.set_aspect("equal"); ax.grid(alpha=.3); ax.legend(loc="upper right")
print("\nSOURCE front holes (x..x, z..z):"); [print("  ", describe(h)) for h in holes_of(sf)]
print("ZERO front openings moved:"); [print("  ", describe(h)) for h in th]

# 2. -X END WALL (YZ)
se, _ = union_section([src["bottom"], src["top"]], [-55.3, 0, 0], [1, 0, 0])
te, _ = union_section([tgt["bottom"], tgt["lid"]], [-34.3, 0, 0], [1, 0, 0])
teh = [affinity.translate(h, DY, DZ) for h in holes_of(te) if h.area > 30]
ax = axs[0, 1]; draw(ax, se); draw_outline(ax, teh)
ax.axhline(0, color="b", ls=":", lw=0.8); ax.set_title("-X END wall (SD end; Y horizontal, Z up). red = Zero SD opening")
ax.set_aspect("equal"); ax.grid(alpha=.3)
print("\nSOURCE -X end holes:"); [print("  ", describe(h)) for h in holes_of(se)]
print("ZERO SD opening moved:"); [print("  ", describe(h)) for h in teh]

# 3. PLAN: source floor + posts at z=-15, board outline, Zero posts
sp, _ = union_section([src["bottom"]], [0, 0, -14.0], [0, 0, 1])
tposts, _ = union_section([tgt["bottom"]], [0, 0, 3.5], [0, 0, 1])
posts = [affinity.translate(g, DX, DY) for g in getattr(tposts, "geoms", []) if g.area < 50]
board = affinity.translate(box(-33.5, -17.75, 31.5, 12.25).buffer(-3).buffer(3), DX, DY)
pi3 = box(-49.08, -28.58, 35.92, 27.42).buffer(-3).buffer(3)
ax = axs[1, 0]; draw(ax, sp)
draw_outline(ax, [board], "red", label="Pi Zero board 65x30 (proposed)")
draw_outline(ax, posts, "red")
draw_outline(ax, [pi3], "green", 1, label="Pi 3B board (original)")
ax.set_title("PLAN at z=-14 (above floor). grey = source bottom walls/posts/bosses"); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.legend(loc="upper right")
print("\nSOURCE bottom plan features z=-14:"); [print("  ", describe(g)) for g in getattr(sp, "geoms", [sp])]
print("board moved:", describe(board))
clash = [g for g in getattr(sp, "geoms", [sp]) if g.intersects(board)]
print("board footprint vs source material at z=-14 overlap area:", round(sum(g.intersection(board).area for g in clash), 2))

# 4. TOP PLATE plan: source top at z=16.8, Zero lid holes at z=27
st, _ = union_section([src["top"]], [0, 0, 16.8], [0, 0, 1])
tl, _ = union_section([tgt["lid"]], [0, 0, 27.0], [0, 0, 1])
tlh = [affinity.translate(h, DX, DY) for h in holes_of(tl)]
lg, _ = union_section([tgt["logo"]], [0, 0, 27.75], [0, 0, 1])
ax = axs[1, 1]; draw(ax, st); draw_outline(ax, tlh, label="Zero lid openings")
draw_outline(ax, [affinity.translate(g, DX, DY) for g in getattr(lg, "geoms", [lg])], "orange", 1, label="Zero logo")
draw_outline(ax, [board], "red", 0.6)
ax.set_title("TOP plate plan (z=16.8). grey = source top incl. display window, DIN opening, logo"); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.legend(loc="upper right")
print("\nSOURCE top-plate holes:"); [print("  ", describe(h)) for h in holes_of(st)]
print("ZERO lid openings moved:"); [print("  ", describe(h)) for h in tlh]
plt.tight_layout(); fig.savefig(os.path.join(S, "overlay.png"), dpi=75)

# notch top height (button holes) in target lid
for x in [-22.5, -11.75, -1, 9.75, 20.5]:
    loc, _, _ = tgt["lid"].ray.intersects_location([[x, -18.75, 18.0]], [[0, 0, 1]])
    print(f"button notch at x_t={x}: first material above z=18 at z_t={loc[:,2].min() if len(loc) else None}")
# top-shell internal features that hang below z=10 (bosses etc.)
tp, _ = union_section([src["top"]], [0, 0, 8], [0, 0, 1])
print("\nSOURCE top shell features at z=8:"); [print("  ", describe(g)) for g in getattr(tp, "geoms", [tp])]
