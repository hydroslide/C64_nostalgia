import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from render import render
R = r"H:\My Drive\3D printing\STLs\C64\real_files"
OUT = os.path.dirname(__file__)
jobs = [
    ("source/pi1541_case_bottom.stl", "y"), ("source/pi1541_case_top.stl", "y"),
    ("source/pi1541_case_front.stl", "y"),
    ("target/obj_1_Case Bottom.stl", "z"), ("target/obj_2_Assembly.stl", "z"),
]
for rel, up in jobs:
    out = os.path.join(OUT, os.path.basename(rel).replace(" ", "_").replace(".stl", ".png"))
    render(os.path.join(R, rel), out, up=up, title=rel)
    print("wrote", out)
