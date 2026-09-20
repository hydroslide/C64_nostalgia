import trimesh, numpy as np, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
t = trimesh.load(os.path.join(S, "zup_top_noslot.stl"))
o = trimesh.load(r"H:\My Drive\3D printing\STLs\C64\real_files\source\pi1541_case_top.stl"); v = o.vertices
o = trimesh.Trimesh(np.column_stack([v[:,0], -v[:,2], v[:,1]]), o.faces)
def z(m, x, y):
    h = m.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:,2].max(), 3) if len(h) else None
for lab, pts in [("y sweep x=-5", [(-5, y) for y in np.arange(2.8, 4.8, 0.2)]), ("x sweep y=-8", [(x, -8) for x in np.arange(-1.8, 0.4, 0.2)]),
                 ("y sweep x=-5 lower", [(-5, y) for y in np.arange(-12.6, -10.6, 0.2)])]:
    print(lab, "new:", [z(t, *p) for p in pts]); print(" " * len(lab), "old:", [z(o, *p) for p in pts])
