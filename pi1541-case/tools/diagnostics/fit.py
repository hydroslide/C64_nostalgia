import numpy as np, trimesh, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
R = r"H:\My Drive\3D printing\STLs\C64\real_files"
tb = trimesh.load(os.path.join(R, "target", "obj_1_Case Bottom.stl"))
tl = trimesh.load(os.path.join(R, "target", "obj_2_Assembly.stl"))
main = sorted(tl.split(only_watertight=False), key=lambda p: -len(p.faces))[0]
print("lid main body watertight:", main.is_watertight, "volume:", round(main.volume, 1))
main.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
for dz in [2.0, 1.5, 2.5]:
    m = main.copy()
    m.apply_translation([tb.bounds[0][0]-m.bounds[0][0], tb.bounds[0][1]-m.bounds[0][1], tb.bounds[1][2]+dz-m.bounds[1][2]])
    inter = trimesh.boolean.intersection([tb, m], engine="manifold")
    print(f"lid top at bottom_rim+{dz}: overlap volume = {inter.volume:.2f} mm3, lid z {m.bounds[0][2]:.2f}..{m.bounds[1][2]:.2f}")
# snap bumps on lid vs grooves in bottom
m = main.copy(); m.apply_translation([tb.bounds[0][0]-m.bounds[0][0], tb.bounds[0][1]-m.bounds[0][1], tb.bounds[1][2]+2-m.bounds[1][2]])
gap = trimesh.proximity.signed_distance(tb, m.vertices[::5])
print("lid verts inside bottom (>0.01mm):", int((gap > 0.01).sum()), " closest clearance stats (mm): min |d| =", round(float(np.abs(gap).min()),3))
