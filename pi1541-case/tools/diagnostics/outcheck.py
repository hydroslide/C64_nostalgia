import trimesh, numpy as np, os, glob
O = r"H:\My Drive\3D printing\STLs\C64\output"; R = r"H:\My Drive\3D printing\STLs\C64\real_files\source"
for f in sorted(glob.glob(os.path.join(O, "*.stl"))):
    m = trimesh.load(f); print(f"{os.path.basename(f):38s} {os.path.getsize(f)//1024:5d} KB watertight={m.is_watertight} bounds={np.round(m.bounds,2).tolist()}")
for n in ["top", "bottom"]:
    print(f"original {n:6s} bounds:", np.round(trimesh.load(os.path.join(R, f"pi1541_case_{n}.stl")).bounds, 2).tolist())
