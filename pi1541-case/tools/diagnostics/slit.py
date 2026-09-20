import sys, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
sys.path.insert(0, S)
from common import *
o = load_source()["front"]; b = trimesh.load(os.path.join(S, "lev_bez.stl"))
def xf(m, y, z):
    h = np.atleast_2d(m.ray.intersects_location([[80, y, z]], [[-1, 0, 0]])[0]); return round(float(h[:, 0].max()), 2) if h.size else None
for z in [1.0, 1.5, 2.0]:
    print(f"z={z}: orig", [(round(y, 2), xf(o, y, z)) for y in np.arange(5.9, 7.0, 0.1)])
    print(f"      new ", [(round(y, 2), xf(b, y, z)) for y in np.arange(5.9, 7.0, 0.1)])
print("slit z extent at y=6.45 (new):", [(round(z, 2), xf(b, 6.45, z)) for z in np.arange(0.5, 3.0, 0.1)])
