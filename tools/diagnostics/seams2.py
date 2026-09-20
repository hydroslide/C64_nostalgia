import trimesh, numpy as np, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
def L(p):
    o = trimesh.load(p); v = o.vertices; return trimesh.Trimesh(np.column_stack([v[:,0], -v[:,2], v[:,1]]), o.faces)
R = r"H:\My Drive\3D printing\STLs\C64\real_files\source"
ot, ob = L(os.path.join(R, "pi1541_case_top.stl")), L(os.path.join(R, "pi1541_case_bottom.stl"))
nt, nb = trimesh.load(os.path.join(S, "zup_top_noslot.stl")), trimesh.load(os.path.join(S, "zup_bottom.stl"))
def first(m, o, d):
    h = m.ray.intersects_location([o], [d])[0]
    if not len(h): return None
    k = np.argmin(np.linalg.norm(h - np.array(o), axis=1)); return np.round(h[k], 3)
print("orig top surface near DIN edge, y sweep x=-45:", [(y, first(ot, [-45, y, 40], [0,0,-1])[2]) for y in [-23.4, -23.1, -22.8, -22.5, -22.2, 22.4, 22.7, 23.0, 23.1]])
print("orig top surface near DIN edge, x sweep y=10:", [(x, first(ot, [x, 10, 40], [0,0,-1])[2]) for x in [-34.0, -33.6, -33.2, -32.9, -32.6]])
print("orig -X end x at y=-23.1 (z=3,8,14):", [first(ot, [-80, -23.1, z], [1,0,0])[0] for z in [3, 8, 14]])
# front panel face y across fill region boundaries (new parts), at hole-free heights
for name, m, xs, z in [("bottom", nb, [-44.5, -44.0, -43.8, -43.6, -43.2, 10.0, 10.3, 10.5, 10.8], -4.0),
                       ("bottom", nb, [-44.0, -43.8, -43.6, 10.2, 10.5], -14.0),
                       ("top", nt, [-40, -39.5, -39.3, -39.1, 7.1, 7.3, 7.5, 8], 8.5), ("top", nt, [-40, -39.3, -39.1, 7.3, 7.5], 1.2)]:
    print(f"{name} front face y at z={z}:", [(x, first(m, [x, -60, z], [0,1,0])[1]) for x in xs])
# floor top across the -X end fill boundary
print("bottom floor top z, y sweep at x=-45:", [(y, first(nb, [-45, y, 20], [0,0,-1])[2]) for y in [-17, -15.7, -15.5, -15.3, 15.3, 15.5, 15.7, 17]])
print("bottom floor top z, x sweep at y=0:", [(x, first(nb, [x, 0, 20], [0,0,-1])[2]) for x in [-34, -33.2, -33.0, -32.8, -30]])
