import sys, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
sys.path.insert(0, S)
from zrender import render
render(os.path.join(S, "zup_bezel_lever.stl"), os.path.join(S, "bezel_lever2.png"), "z", 28,
       views=[("face (looking -X)", 0, 0), ("iso from front-left, above", 30, -35)], title="bezel with 1541 lever v2")
