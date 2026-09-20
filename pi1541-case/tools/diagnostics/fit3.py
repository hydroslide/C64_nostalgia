import numpy as np, trimesh, os, itertools
R = r"H:\My Drive\3D printing\STLs\C64\real_files\source"
P = {n: trimesh.load(os.path.join(R, f"pi1541_case_{n}.stl")) for n in ["top", "bottom", "front"]}
for a, b in itertools.combinations(P, 2):
    i = trimesh.boolean.intersection([P[a], P[b]], engine="manifold")
    d = trimesh.proximity.closest_point(P[b], P[a].vertices[::7])[1].min()
    print(f"{a} vs {b}: overlap {i.volume:.3f} mm3, min vertex gap {d:.3f} mm")
