import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
b = load_source()["bottom"]
def ylh(x, z):   # outer, inner y of left wall
    h = b.ray.intersects_location([[x, -60, z]], [[0, 1, 0]])[0]; return np.round(sorted(h[:, 1])[:2], 3) if len(h) else None
def yrh(x, z):   # outer, inner y of right wall
    h = b.ray.intersects_location([[x, 60, z]], [[0, -1, 0]])[0]; return np.round(sorted(h[:, 1], reverse=True)[:2], 3) if len(h) else None
for z in [-13.5, -12, -7, -2, -1.2]:
    xs = np.arange(-52, 16, 0.1); outer = np.array([ylh(x, z)[0] for x in xs])
    rec = xs[outer > -29.9]
    print(f"z={z}: recessed x {rec.min():.2f}..{rec.max():.2f}" if len(rec) else f"z={z}: no recess")
xs = np.arange(-20, -10, 1.0)
zs = np.arange(-17.4, 0.1, 0.1); outer = np.array([ylh(-20, z)[0] if ylh(-20, z) is not None else np.nan for z in zs])
rz = zs[outer > -29.9]; print(f"recess z-range at x=-20: {rz.min():.2f}..{rz.max():.2f}")
print("\nleft wall at x=30 vs mirrored right wall at x=30 (outer, inner):")
for z in [-17, -16, -14, -10, -6, -2, -0.5]:
    print(f"  z={z:6.1f} left {ylh(30, z)}  right(mirrored) {None if yrh(30, z) is None else -yrh(30, z)}")
