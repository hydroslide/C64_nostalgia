import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
src = load_source()
def yhits(m, x, z):
    h = m.ray.intersects_location([[x, 0, z]], [[0, 1, 0]])[0]; return np.round(sorted(h[:, 1]), 2)[:2] if len(h) else None
for x in [-40, -10, 10]:
    print(f"x={x} back wall (inner,outer) bottom:", [(z, yhits(src["bottom"], x, z)) for z in [-15.5, -14, -13, -12, -10, -8, -6, -3, -0.5]])
    print(f"x={x} back wall (inner,outer) top   :", [(z, yhits(src["top"], x, z)) for z in [-0.5, 0.5, 2, 4, 6, 8, 12, 15.5]])
# top surface flatness where relocated vents would go
t = src["top"]
def ztop(x, y):
    h = t.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:, 2].max(), 3) if len(h) else None
print("top surface y sweep x=-20 (front half):", [(y, ztop(-20, y)) for y in [-28.5, -28, -27.5, -27.2, -27, -20, -13]])
print("vent groove y extent x=-23:", [(y, ztop(-23, y)) for y in [26.5, 27, 27.5, 28, 28.5, 29, 29.5, 30, 30.5]])
print("vent x extents at y=15:", [(round(x,2), ztop(x, 15)) for x in np.arange(-28.0, -26.5, 0.1)][:6], "...")
