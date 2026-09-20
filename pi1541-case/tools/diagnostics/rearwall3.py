import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
t = load_source()["top"]
def hits(y, z):
    h = t.ray.intersects_location([[-80, y, z]], [[1, 0, 0]])[0]
    h = np.atleast_2d(h); return np.round(sorted(h[:, 0]), 2).tolist()[:4] if h.size else []
for y in [0, 10, -22.3]:
    print(f"y={y}:", [(z, hits(y, z)) for z in [-0.8, -0.3, 0.3, 0.8, 1.2, 1.6, 2.0]])
def zdown(x, y):
    h = t.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; h = np.atleast_2d(h); return np.round(sorted(h[:, 2], reverse=True), 2).tolist()[:4] if h.size else []
print("donor y=-22.3, vertical hits at x=-52:", zdown(-52, -22.3), " x=-50:", zdown(-50, -22.3), " x=-48:", zdown(-48, -22.3))
