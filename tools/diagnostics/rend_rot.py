import sys, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
sys.path.insert(0, S)
from common import *
from zrender import render
b = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_bottom.stl")); t = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_noslot.stl"))
trimesh.util.concatenate([b, t, load_source()["front"]]).export(os.path.join(S, "rot_asm_noslot.stl"))
render(os.path.join(S, "rot_asm_noslot.stl"), os.path.join(S, "rr_asm_noslot.png"), "z", 6)
render(os.path.join(S, "zup_pi1541_zero_rot_case_top_noslot.stl"), os.path.join(S, "rr_top_noslot.png"), "z", 7)
