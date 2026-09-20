import trimesh, numpy as np, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
t = trimesh.load(os.path.join(S, "zup_top_noslot.stl"))
for p in sorted(t.split(only_watertight=False), key=lambda p:-p.volume):
    print("top body", round(p.volume,1), np.round(p.bounds,2).tolist())
src = trimesh.load(r"H:\My Drive\3D printing\STLs\C64\real_files\source\pi1541_case_top.stl")
v = src.vertices; src = trimesh.Trimesh(np.column_stack([v[:,0], -v[:,2], v[:,1]]), src.faces)
for z in [1, 3, 5]:
    loc, _, _ = src.ray.intersects_location([[-31, 0, z]], [[0, -1, 0]])
    print(f"source top front wall at x=-31 z={z}: y hits", np.round(sorted(loc[:,1]),2))
