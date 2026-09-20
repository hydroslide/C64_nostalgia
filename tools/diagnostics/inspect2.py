import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
src = load_source(); tgt = load_target()
def show(mesh, o, n, label):
    ps, keep = section_polys(mesh, o, n)
    print(f"\n== {label}")
    for p in ps:
        print("  mat:", describe(p), "holes:", len(p.interiors))
for z in [25.5, 24, 21, 19]:
    show(tgt["lid"], [0, 0, z], [0, 0, 1], f"target lid z_t={z}")
for z in [15.5, 12, 6, 2, 0.5, -0.5]:
    show(src["top"], [0, 0, z], [0, 0, 1], f"source top z={z}")
# front panel extent: probe y of front surface along x at z=-8 and z=4
for zz in [-8, 4]:
    row = []
    for x in np.arange(-56, 56, 1.0):
        loc, _, _ = trimesh.util.concatenate([src["bottom"], src["top"]]).ray.intersects_location([[x, -60, zz]], [[0, 1, 0]])
        row.append((x, round(loc[:, 1].min(), 2) if len(loc) else None))
    print(f"\nfront surface y at z={zz}:", [r for r in row if r[1] is not None and r[1] > -30.2][:3], "...", [r for r in row if r[1] is not None and r[1] > -30.2][-3:])
    xs = [r[0] for r in row if r[1] is not None and -29.8 < r[1] < -29.5]
    print("   recessed panel x-range approx:", min(xs) if xs else None, max(xs) if xs else None)
