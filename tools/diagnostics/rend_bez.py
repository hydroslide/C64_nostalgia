import sys, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
sys.path.insert(0, S)
from zrender import render
views = [("face (looking -X)", 0, 0), ("iso front-left", 25, -35), ("iso front-right", 25, 35), ("top (looking -Z)", 90, 0)]
render(os.path.join(S, "zup_bezel_lever.stl"), os.path.join(S, "bezel_lever.png"), "z", 22, views=views, title="bezel with 1541 lever")
