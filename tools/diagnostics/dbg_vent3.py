import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
from ops import *
o = load_source()["top"]
def z(m, x, y):
    h = m.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:, 2].max(), 2) if len(h) else None
g = through(negative(o, [-27.6, 4.0, 16.3], [-1.95, 27.0, 17.45]), (0, 0, 1.0))
gm = moved(g, dy=-31.1)
print("moved grooves bounds", np.round(gm.bounds, 2).tolist(), "vol", round(gm.volume, 1), "is_volume", gm.is_volume)
t1 = D(o, gm)
print("orig minus grooves: vol change", round(o.volume - t1.volume, 1), " probe x=-23,y=-15:", z(t1, -23, -15), " x=-22.2:", z(t1, -22.2, -15))
print("probe orig grooves at y=15 x sweep:", [(round(x,1), z(o, x, 15)) for x in np.arange(-24, -20, 0.25)])
