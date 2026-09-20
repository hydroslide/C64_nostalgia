import sys, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
sys.path.insert(0, S)
from common import *
from zrender import render
b = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_bottom.stl"))
t = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_noslot.stl"))
trimesh.util.concatenate([b, t, load_source()["front"]]).export(os.path.join(S, "rev2_asm.stl"))
render(os.path.join(S, "rev2_asm.stl"), os.path.join(S, "rev2_asm.png"), "z", 7,
       views=[("iso from right-rear (vents + buttons)", 28, 55), ("iso from right-front", 25, -60),
              ("top", 90, -90), ("right side", 0, 0), ("front (bezel end)", 0, -90), ("rear", 0, 90)])
render(os.path.join(S, "zup_pi1541_zero_rot_case_bottom.stl"), os.path.join(S, "rev2_bottom.png"), "z", 7,
       views=[("iso", 30, -55), ("right side (ports)", 0, 0), ("top", 90, -90)])
