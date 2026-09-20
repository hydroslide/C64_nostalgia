import os, numpy as np, trimesh
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
m = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_noslot.stl"))
def yl(x, z, n):
    h = np.atleast_2d(m.ray.intersects_location([[x, -60, z]], [[0, 1, 0]])[0]); return np.round(sorted(h[:, 1])[:n], 3).tolist()
bad_all = sum(1 for x in np.arange(-48, 15, 0.25) for z in [-0.5, 1, 2.5, 5, 9, 13, 16] if yl(x, z, 2) != yl(30, z, 2))
bad_outer = sum(1 for x in np.arange(-48, 15, 0.25) if yl(x, 17.2, 1) != yl(30, 17.2, 1))
print("top_noslot left wall: mismatches below z=17 (outer+inner):", bad_all, "| outer surface at z=17.2:", bad_outer)
