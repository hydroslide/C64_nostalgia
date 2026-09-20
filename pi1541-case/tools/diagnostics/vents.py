import trimesh, numpy as np
o = trimesh.load(r"H:\My Drive\3D printing\STLs\C64\real_files\source\pi1541_case_top.stl"); v = o.vertices
o = trimesh.Trimesh(np.column_stack([v[:,0], -v[:,2], v[:,1]]), o.faces)
def z(x, y):
    h = o.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:,2].max(), 3) if len(h) else None
for x in [-28.8, -27.5, -23, -10, -3.5, -2.8]:
    print(f"x={x}:", [(round(y,1), z(x, y)) for y in np.arange(3.2, 6.2, 0.2)])
print("x sweep y=10 (vents extent):", [(round(x,1), z(x, 10)) for x in list(np.arange(-30.5, -27, 0.25)) + list(np.arange(-4.5, -1, 0.25))])
