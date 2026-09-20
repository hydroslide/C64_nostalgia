import trimesh, os, numpy as np
from collections import Counter
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
m = trimesh.load(os.path.join(S, "zup_pi1541_zero_rot_case_bottom.stl"))
e = np.sort(m.edges, axis=1); c = Counter(map(tuple, e))
bad = [k for k, v in c.items() if v != 2]
print("bad edges:", len(bad), "counts:", Counter(c[k] for k in bad))
pts = m.vertices[np.array(bad).ravel()]
print("locations (min/max):", np.round(pts.min(0), 3).tolist(), np.round(pts.max(0), 3).tolist())
for k in bad[:12]:
    print("  ", np.round(m.vertices[list(k)], 4).tolist(), "len", round(float(np.linalg.norm(m.vertices[k[0]] - m.vertices[k[1]])), 5))
