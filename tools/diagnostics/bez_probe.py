import os, numpy as np, trimesh
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
b = trimesh.load(os.path.join(S, "zup_bezel_lever.stl"))
def xf(y, z):
    h = np.atleast_2d(b.ray.intersects_location([[80, y, z]], [[-1, 0, 0]])[0]); return round(float(h[:, 0].max()), 2) if h.size else None
for y in [0, 5, 8]:
    print(f"y={y}: face x vs z:", [(round(z, 2), xf(y, z)) for z in np.arange(0.3, 3.3, 0.1)])
