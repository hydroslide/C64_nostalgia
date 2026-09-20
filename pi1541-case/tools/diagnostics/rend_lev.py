import sys, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
sys.path.insert(0, S)
import numpy as np, trimesh
from zrender import render
Y0, Z0 = -11.2, 0.4
L = lambda n: trimesh.load(os.path.join(S, f"lev_{n}.stl"))
bez, fr, bk = L("bez"), L("front"), L("back")
def rot(m, d):
    m = m.copy(); m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(d), [1, 0, 0], [0, Y0, Z0])); return m
for d, tag in [(0, "up"), (-90, "down")]:
    trimesh.util.concatenate([bez, rot(fr, d), rot(bk, d)]).export(os.path.join(S, f"lev_asm_{tag}.stl"))
v1 = [("face (looking -X)", 0, 0), ("iso front-left", 25, -35)]
render(os.path.join(S, "lev_asm_up.stl"), os.path.join(S, "lev_up.png"), "z", 24, views=v1, title="rotating lever - horizontal (0 deg)")
render(os.path.join(S, "lev_asm_down.stl"), os.path.join(S, "lev_down.png"), "z", 24, views=v1, title="rotating lever - down (-90 deg)")
render(os.path.join(S, "lev_asm_up.stl"), os.path.join(S, "lev_back.png"), "z", 30, views=[("back (looking +X), lever at 0 deg", 0, 180), ("iso back", 30, 150)], title="bezel back: detent ring + spring")
O = r"H:\My Drive\3D printing\STLs\C64\output"
for n in ["lever_front", "lever_back"]:
    render(os.path.join(O, f"pi1541_zero_case_front_1541lever_rotating_{n}.stl"), os.path.join(S, f"print_{n}.png"), "z", 40,
           views=[("iso", 35, -50), ("top", 90, -90)], title=f"{n} (print orientation)")
