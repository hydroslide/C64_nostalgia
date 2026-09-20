import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
from ops import U, D, I, BOX, moved
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
tn = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_noslot.stl"))
DXr, DYr, DZ = -46.6 + 31.5, 28.31 - 17.75 - 3.5, -14.5
BTN_X = [-22.5, -11.75, -1.0, 9.75, 20.5]; BTN_Z = 23.49 + DZ; BOARD_EDGE = 28.31 - 3.5
sw = U([BOX([-x + DXr - 3.2, BOARD_EDGE - 0.5, BTN_Z - 3.2], [-x + DXr + 3.2, BOARD_EDGE + 2.5, BTN_Z + 3.2]) for x in BTN_X])
print("switches at final position vs top (0 = OK):", round(I(sw, tn).volume, 3))
for d in [2, 4, 6, 8, 12]:
    x = I(moved(sw, dz=-d), tn)
    b = np.round(x.bounds, 1).tolist() if x.volume > 0.001 else None
    print(f"   lifted {d:2d} mm: {x.volume:7.2f} mm3  bounds {b}")

