import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
src = load_source()
def yo(m, x, z, side=-1):
    h = m.ray.intersects_location([[x, 60 * side, z]], [[0, -side, 0]])[0]
    if not len(h): return None
    return round(float(h[np.argmin(np.abs(h[:, 1] - 60 * side)), 1]), 3)
for name, m, zs in [("bottom", src["bottom"], np.arange(-17.4, 0.01, 0.2)), ("top", src["top"], np.arange(-0.9, 17.5, 0.2))]:
    prof = [(round(z, 1), yo(m, -20, z)) for z in zs]
    rec = [z for z, y in prof if y is not None and y > -29.7]
    print(f"{name}: panel face (y>-29.7) z-range at x=-20: {min(rec)}..{max(rec)}")
    for zz in ([-12, -7, -3] if name == "bottom" else [1.5, 4, 8, 10]):
        xs = np.arange(-50, 16, 0.1); ys = np.array([yo(m, x, zz) or -99 for x in xs]); r = xs[ys > -29.7]
        print(f"   z={zz}: panel x-range {r.min():.2f}..{r.max():.2f}")
t = src["top"]
print("top plain profile symmetry at x=30 (left outer vs -right outer):", [(z, yo(t, 30, z, -1), None if yo(t, 30, z, 1) is None else -yo(t, 30, z, 1)) for z in [-0.5, 1, 4, 8, 12, 15, 16.5]])
print("source top: panel face y at z=4:", yo(t, -20, 4), " inner:", end=" ")
h = t.ray.intersects_location([[-20, 0, 4]], [[0, -1, 0]])[0]; print(np.round(sorted(h[:, 1], reverse=True)[:2], 3))
