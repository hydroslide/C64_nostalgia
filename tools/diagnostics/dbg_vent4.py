import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
from ops import *
o = load_source()["top"]
def zs(m, x, y):
    h = m.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return np.round(sorted(h[:, 2], reverse=True), 3).tolist()
g = through(negative(o, [-27.6, 4.0, 16.3], [-1.95, 27.0, 17.45]), (0, 0, 1.0))
gm = moved(g, dy=-31.1)
t1 = D(o, gm)
for x in [-23.5, -20.5, -26.0]:
    print(x, "cutter z hits:", zs(gm, x, -15), " result z hits:", zs(t1, x, -15))
print("cutter y extent at x=-23.5:", [(y, zs(gm, -23.5, y)) for y in [-27.5, -26.5, -15, -4.5, -3.5]])
