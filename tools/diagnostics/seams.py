import trimesh, numpy as np, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
t = trimesh.load(os.path.join(S, "zup_top_noslot.stl"))
o = trimesh.load(r"H:\My Drive\3D printing\STLs\C64\real_files\source\pi1541_case_top.stl"); v = o.vertices
o = trimesh.Trimesh(np.column_stack([v[:,0], -v[:,2], v[:,1]]), o.faces)
def ztop(m, x, y):
    h = m.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:,2].max(), 3) if len(h) else None
print("top surface z across old DIN edge (y sweep at x=-45):", [(y, ztop(t, -45, y)) for y in [18, 20, 21.5, 22.0, 22.5, 23, 25]])
print("top surface z across x=-33.5 seam (x sweep at y=15):", [(x, ztop(t, x, 15)) for x in [-36, -34, -33.4, -33, -31, -25]])
print("original top z at same pts:", [(x, ztop(o, x, 15)) for x in [-33, -31, -25]], [(y, ztop(o, -45, y)) for y in [22.5, 23, 25]])
print("old display area:", [(x, ztop(t, x, -5)) for x in [-5, -2, -1.1, -0.5, 2]])
def xend(m, y, z):
    h = m.ray.intersects_location([[-80, y, z]], [[1, 0, 0]])[0]; return round(h[:,0].min(), 3) if len(h) else None
for z in [3, 8, 14]:
    print(f"-X end wall outer x at z={z}:", [(y, xend(t, y, z)) for y in [-26, -24, -22.5, -22.2, -20, 0, 20, 22.2, 22.5, 24]], " orig:", [(y, xend(o, y, z)) for y in [-24, 24]])
