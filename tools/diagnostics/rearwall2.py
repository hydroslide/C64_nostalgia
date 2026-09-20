import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
t = load_source()["top"]
for y in [-24, 0, 24]:
    for z in [3, 8, 13]:
        h = t.ray.intersects_location([[-80, y, z]], [[1, 0, 0]])[0]
        print(f"orig top y={y} z={z}: all x hits", np.round(sorted(h[:, 0]), 2).tolist())
ps, _ = section_polys(t, [0, 0, 8], [0, 0, 1])
for p in ps:
    print("orig top @z=8:", describe(p), "holes:", [describe(__import__('shapely.geometry', fromlist=['Polygon']).Polygon(h)) for h in p.interiors][:4])
