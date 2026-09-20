import trimesh, numpy as np, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
t = trimesh.load(os.path.join(S, "zup_top_noslot.stl"))
def z(x, y):
    h = t.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:,2].max(), 3) if len(h) else None
print("vent grooves intact (x=-23 / -3.5, y 4.0..5.0):", [(round(y,1), z(-23, y), z(-3.5, y)) for y in np.arange(4.0, 5.01, 0.2)])
print("left/right window edge x sweep y=-8:", [(round(x,2), z(x, -8)) for x in [-29.3, -29.0, -28.6, -28.2, -0.8, -0.5, -0.2]])
