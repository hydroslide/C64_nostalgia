import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
from ops import *
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
it = trimesh.load(os.path.join(S, "rot_internals.stl"))
ts = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_slot.stl"))
win = BOX([-60.0, 4.06, 4.5], [-46.0, 22.56, 11.5])
print("internals solid?", it.is_volume)
x = I(ts, win); print("top material inside rear-window box:", round(x.volume, 1))
for p in sorted(x.split(only_watertight=False), key=lambda p: -abs(p.volume))[:6]:
    b = p.bounds; print(f"  {p.volume:7.1f} x {b[0][0]:.1f}..{b[1][0]:.1f} y {b[0][1]:.1f}..{b[1][1]:.1f} z {b[0][2]:.1f}..{b[1][2]:.1f}")
# plan section of internals at z=8 near the rear
ps, _ = section_polys(it, [0, 0, 8], [0, 0, 1])
for p in ps:
    b = p.bounds
    if b[0] < -35: print("internals @z=8:", describe(p), "holes", len(p.interiors))
