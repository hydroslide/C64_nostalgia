import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
from zrender import render
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
t = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_noslot.stl"))
def z(x, y):
    h = t.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:, 2].max(), 3) if len(h) else None
print("rear edge (x sweep, y=0):", [(round(x,1), z(x, 0)) for x in np.arange(-57, -50, 0.5)])
print("side edges (y sweep, x=-40):", [(round(y,1), z(-40, y)) for y in list(np.arange(-31.5, -26.5, 0.5)) + list(np.arange(27, 31.6, 0.5))])
print("existing source groove cross-section at y=15 (x sweep):", [(round(x,2), z(x, 15)) for x in np.arange(-27.6, -21.5, 0.1)] if False else "")
o = load_source()["top"]
def zo(x, y):
    h = o.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:, 2].max(), 3) if len(h) else None
xs = np.arange(-28, -1.8, 0.05); zz = np.array([zo(x, 15) for x in xs]); g = zz < 17.0
edges = xs[1:][np.diff(g.astype(int)) != 0]
print("source groove edges at y=15:", np.round(edges, 2).tolist())
fr = load_source()["front"]
print("bezel bounds (Z-up):", np.round(fr.bounds, 2).tolist())
fr.export(os.path.join(S, "bezel_zup.stl"))
