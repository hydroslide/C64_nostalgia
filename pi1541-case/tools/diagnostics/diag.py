import trimesh, numpy as np, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
it = trimesh.load(os.path.join(S, "zup_internals.stl"))
print("internals volume", round(it.volume,1), "bounds", np.round(it.bounds,2).tolist())
for p in sorted(it.split(only_watertight=False), key=lambda p:-p.volume):
    print("  piece", round(p.volume,1), np.round(p.bounds,2).tolist())
b = trimesh.load(os.path.join(S, "zup_bottom.stl"))
for p in sorted(b.split(only_watertight=False), key=lambda p:-p.volume):
    print("bottom body", round(p.volume,1), np.round(p.bounds,2).tolist())
