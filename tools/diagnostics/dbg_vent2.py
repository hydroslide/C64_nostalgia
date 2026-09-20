import trimesh, numpy as np, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
t = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_top_noslot.stl"))
def z(x, y):
    h = t.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:, 2].max(), 2) if len(h) else None
print("new top, x sweep at y=-15:", [(round(x,1), z(x, -15)) for x in np.arange(-28, -1.5, 0.5)])
print("new top, x sweep at y=15 :", [(round(x,1), z(x, 15)) for x in np.arange(-28, -1.5, 0.5)])
