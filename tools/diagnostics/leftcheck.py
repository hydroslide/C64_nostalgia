import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
for part, zs in [("top_noslot", [-0.5, 1, 2.5, 5, 9, 13, 16, 17.2]), ("top_slot", [1, 5, 13]), ("bottom", [-17, -15, -10, -5, -2, -0.5])]:
    m = trimesh.load(os.path.join(S, f"zup_pi1541_zero_rot_case_{part}.stl"))
    def yl(x, z):
        h = m.ray.intersects_location([[x, -60, z]], [[0, 1, 0]])[0]; h = np.atleast_2d(h)
        return np.round(sorted(h[:, 1])[:2], 3).tolist() if h.size else None
    ref = {z: yl(30, z) for z in zs}; bad = 0
    for x in np.arange(-48, 15, 0.25):
        for z in zs:
            v = yl(x, z)
            if v is None or any(abs(a - b) > 0.005 for a, b in zip(v, ref[z])):
                bad += 1
                if bad < 4: print(f"   {part} differs x={x:.2f} z={z}: {v} vs {ref[z]}")
    print(f"{part}: left-wall mismatches vs plain profile (x -48..15): {bad}")
