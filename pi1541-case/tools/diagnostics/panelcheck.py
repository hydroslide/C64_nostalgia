import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
from ops import I
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
b = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_bottom.stl"))
t = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_noslot.stl"))
src = load_source()
def yl(m, x, z):
    h = m.ray.intersects_location([[x, -60, z]], [[0, 1, 0]])[0]; return np.round(sorted(h[:, 1])[:2], 3).tolist() if len(h) else None
ref = {z: yl(b, 30, z) for z in [-17, -16, -14, -10, -6, -2, -0.5]}
bad = 0
for x in np.arange(-48, 15, 0.25):
    for z, r in ref.items():
        v = yl(b, x, z)
        if v is None or abs(v[0] - r[0]) > 0.005 or abs(v[1] - r[1]) > 0.005:
            bad += 1; print(f"  differs at x={x:.2f} z={z}: {v} vs ref {r}")
print("left wall profile mismatches vs x=30 over x -48..15 at 7 heights:", bad)
print("bottom watertight:", b.is_watertight, " top∩bottom:", round(I(t, b).volume, 2), " bottom∩bezel:", round(I(b, src["front"]).volume, 2))
