import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from ops import *
S = os.path.dirname(__file__)
src = load_source(); tgt = load_target()
RAISE, BACKOFF = 3.5, 3.5
DXr, DYr, DZ = -46.6 + 31.5, 28.31 - 17.75 - BACKOFF, -18.0 + RAISE
MIRROR_Y = np.diag([1.0, -1.0, 1.0, 1.0])
CREST_X = (-27.3, -25.8); VENT_W = 1.0

crest_donor = D(BOX([CREST_X[0], 26.0, 12.0], [CREST_X[1], 33.0, 19.0]), src["top"])
crest_slab = I(crest_donor, BOX([CREST_X[0] + 0.25, 26.0, 12.0], [CREST_X[0] + 0.25 + VENT_W, 33.0, 19.0]))
print("crest slab volume", round(crest_slab.volume, 2), "bounds", np.round(crest_slab.bounds, 2).tolist())
for p in sorted(crest_slab.split(only_watertight=False), key=lambda p: -p.volume):
    print("   piece", round(p.volume, 2), np.round(p.bounds, 2).tolist())

top_noVents = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_slot.stl"))  # has vents, but used only for side profile
# rebuild the plain-sided top quickly: source top with the left side smoothed the same way the build does
t = fill_top_common(src["top"])
t = replace_region(t, [-27.7, 3.9, 14.0], [-1.85, 32.5, 18.5], 0, -31.0)
print("\nleft vs right side profile of the build's top (should be mirror-equal):")
def yl(m, x, z, side):
    h = np.atleast_2d(m.ray.intersects_location([[x, 60 * side, z]], [[0, -side, 0]])[0])
    return np.round(sorted(h[:, 1], key=lambda v: -side * v)[:2], 3).tolist() if h.size else None
for z in [12, 13, 14, 15, 16, 17]:
    print(f"   z={z}: right {yl(t, -37, z, 1)}  left {yl(t, -37, z, -1)}")
gx = -37.5
c = moved(crest_slab, dx=gx - (CREST_X[0] + 0.25))
cm = xformed(c, MIRROR_Y)
for tag, cut in [("+Y crest", c), ("-Y crest", cm)]:
    x = I(cut, t)
    print(f"\n{tag}: cuts {x.volume:.2f} mm3 from the top; bounds {np.round(x.bounds, 2).tolist() if x.volume > 0 else None}")
