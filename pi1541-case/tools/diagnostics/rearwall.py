import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
t = load_source()["top"]
def xh(y, z):
    h = t.ray.intersects_location([[-80, y, z]], [[1, 0, 0]])[0]; return np.round(sorted(h[:, 0])[:2], 2).tolist() if len(h) else None
for y in [-24, -23.1, -22.6, -22.3, -22.0, -21.5, 22.0, 22.3, 22.6, 23.1, 24]:
    print(f"y={y:6.1f}: rear wall x (outer, inner) at z=3,8,13:", [xh(y, z) for z in [3, 8, 13]])
def zt(x, y):
    h = t.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:, 2].max(), 3) if len(h) else None
print("top surface near DIN opening -y side at x=-45:", [(y, zt(-45, y)) for y in [-22.6, -22.3, -22.1, -21.9]])
