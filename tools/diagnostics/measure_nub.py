import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
src = load_source(); tgt = load_target()
# Zero lid notch: vertical extent and the arc centre (= likely switch axis)
lid = tgt["lid"]
for xc in [-22.5, -1.0]:
    h = np.atleast_2d(lid.ray.intersects_location([[xc, -18.75, 18.0]], [[0, 0, 1]])[0])
    print(f"notch x_t={xc}: material above z_t=18 at {np.round(sorted(h[:,2]),2).tolist()[:3]}")
print("notch spans z_t 18.5..25.49 -> arc centre (radius 2) at z_t", 25.49 - 2)
# plain (unpanelled) right wall inner/outer y at button heights, from the ORIGINAL top (right side is plain)
t = src["top"]
def yr(x, z):
    h = np.atleast_2d(t.ray.intersects_location([[x, 60, z]], [[0, -1, 0]])[0])
    return np.round(sorted(h[:,1], reverse=True)[:2], 2).tolist() if h.size else None
for z in [6, 8, 9, 10, 12]:
    print(f"plain wall at z={z}: outer,inner y = {yr(0, z)}")
# lower panel extent (for the enlarged port holes) on the mirrored right side
b = trimesh.load(os.path.join(r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad", "zup_pi1541_zero_rot_case_bottom.stl"))
def yb(x, z):
    h = np.atleast_2d(b.ray.intersects_location([[x, 60, z]], [[0, -1, 0]])[0])
    return np.round(sorted(h[:,1], reverse=True)[:2], 2).tolist() if h.size else None
for z in [-2.5, -3, -5, -9, -12]:
    print(f"port panel at z={z}: outer,inner y = {yb(-20, z)}")
