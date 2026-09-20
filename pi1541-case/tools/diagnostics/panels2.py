import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
src = load_source()
m = trimesh.util.concatenate([src["bottom"], src["top"]])
def yo(x, z):
    h = m.ray.intersects_location([[x, -60, z]], [[0, 1, 0]])[0]
    return round(float(h[:, 1].min()), 2) if len(h) else None
print("outer wall y vs z at x=-20 (panel region) and x=30 (plain):")
for z in np.arange(-17, 17.6, 0.5):
    print(f"  z={z:5.1f}: panel-region {yo(-20, z)}   plain {yo(30, z)}")
