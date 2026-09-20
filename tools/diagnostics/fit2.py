import numpy as np, trimesh, os
R = r"H:\My Drive\3D printing\STLs\C64\real_files"
tb = trimesh.load(os.path.join(R, "target", "obj_1_Case Bottom.stl"))
tl = trimesh.load(os.path.join(R, "target", "obj_2_Assembly.stl"))
parts = sorted(tl.split(only_watertight=False), key=lambda p: -len(p.faces))
main, logo = parts[0], parts[1]
T = trimesh.transformations
for name, M in [("flip about X", T.rotation_matrix(np.pi, [1,0,0])), ("flip about Y", T.rotation_matrix(np.pi, [0,1,0]))]:
    m = main.copy(); m.apply_transform(M)
    off = [tb.bounds[0][0]-m.bounds[0][0], tb.bounds[0][1]-m.bounds[0][1], tb.bounds[1][2]+2-m.bounds[1][2]]
    m.apply_translation(off)
    inter = trimesh.boolean.intersection([tb, m], engine="manifold")
    lg = logo.copy(); lg.apply_transform(M); lg.apply_translation(off)
    # logo: where is the C's opening? the flags sit on the opening side
    c = lg.bounds.mean(0); fl = parts[2].copy(); fl.apply_transform(M); fl.apply_translation(off)
    side = "+X" if fl.bounds.mean(0)[0] > c[0] else "-X"
    print(f"{name}: overlap={inter.volume:.2f} mm3; logo flags on {side} side when viewed from above (correct logo = flags on the right = +X)")
