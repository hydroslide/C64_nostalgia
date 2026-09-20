import os, numpy as np, trimesh
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
t = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_noslot.stl"))
def surf(x, y):
    h = np.atleast_2d(t.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]); return round(h[:,2].max(), 2) if h.size else None
def wall(x, z, side=1):
    h = np.atleast_2d(t.ray.intersects_location([[x, 60*side, z]], [[0, -side, 0]])[0]); return round(float(max(h[:,1]*side)), 2) if h.size else None
gx, rx = -37.5, -36.5   # groove centre / ridge centre
print("depth around the edge (groove vs ridge):")
for y in [24, 26, 28, 29, 29.5, 29.9]:
    print(f"   y={y:5.1f}: groove z={surf(gx, y)}  ridge z={surf(rx, y)}")
print("down the side wall (outer y, groove vs ridge; groove should be ~0.9 further in, fading):")
for z in [14.5, 14, 13, 12, 11.5, 11, 10.5]:
    print(f"   z={z:5.1f}: groove y={wall(gx, z)}  ridge y={wall(rx, z)}  -> depth {None if (wall(gx,z) is None or wall(rx,z) is None) else round(wall(rx,z)-wall(gx,z), 2)}")
print("left side mirror check at z=12:", wall(gx, 12, -1), wall(rx, 12, -1))
