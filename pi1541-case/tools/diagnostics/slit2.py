import os, numpy as np, trimesh
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
for n in ["lev_bez.stl", "zup_bezel_lever.stl"]:
    b = trimesh.load(os.path.join(S, n))
    def xf(y, z):
        h = np.atleast_2d(b.ray.intersects_location([[80, y, z]], [[-1, 0, 0]])[0]); return round(float(h[:, 0].max()), 2) if h.size else None
    vals = set(xf(y, z) for y in list(np.arange(-6.7, -5.95, 0.05)) + list(np.arange(5.95, 6.7, 0.05)) for z in np.arange(1.0, 2.2, 0.1))
    print(n, "face x values around old slits (should be only 58.0, or lever > 58):", sorted(vals))
