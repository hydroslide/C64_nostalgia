import os, sys
import numpy as np, trimesh
sys.path.insert(0, os.path.dirname(__file__))
from zrender import render
S = os.path.dirname(__file__)
R = r"H:\My Drive\3D printing\STLs\C64\real_files"
yup = lambda m: trimesh.Trimesh(np.column_stack([m.vertices[:, 0], -m.vertices[:, 2], m.vertices[:, 1]]), m.faces)
top = yup(trimesh.load(os.path.join(R, "source", "pi1541_case_top.stl")))

def hits(mesh, x, y):
    loc, _, _ = mesh.ray.intersects_location([[x, y, 50]], [[0, 0, -1]])
    if len(loc) == 0: return []
    return sorted(np.round(loc[:, 2], 3).tolist(), reverse=True)
for (x, y, what) in [(-15, -4, "display window centre"), (-40, 0, "DIN opening"), (20, 0, "logo area"),
                     (-22, 12, "vent groove?"), (-23, 12, "vent ridge?"), (30, -20, "plain top")]:
    print(f"source top, ray down at ({x},{y}) [{what}]: z hits = {hits(top, x, y)}")

# target: assemble with lid flipped about X, plate resting on the bottom's rim (z=26..28)
tb = trimesh.load(os.path.join(R, "target", "obj_1_Case Bottom.stl"))
tl = trimesh.load(os.path.join(R, "target", "obj_2_Assembly.stl"))
tl.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
tl.apply_translation([tb.bounds[0][0] - tl.bounds[0][0], tb.bounds[0][1] - tl.bounds[0][1], tb.bounds[1][2] + 2 - tl.bounds[1][2]])
# interference check between lid and bottom (should be ~0 if the fit is right)
main = sorted(tl.split(only_watertight=False), key=lambda p: -len(p.faces))[0]
inter = tb.intersection(main) if hasattr(tb, "intersection") else None
try:
    print("lid/bottom overlap volume (mm3):", round(inter.volume, 2))
except Exception as e:
    print("overlap check unavailable:", e)
asm = trimesh.util.concatenate([tb, tl])
asm.export(os.path.join(S, "tgt_assembly.stl"))
render(os.path.join(S, "tgt_assembly.stl"), os.path.join(S, "z_tgt_assembly.png"), "z", 8)
src = trimesh.util.concatenate([top, yup(trimesh.load(os.path.join(R, "source", "pi1541_case_bottom.stl"))),
                                yup(trimesh.load(os.path.join(R, "source", "pi1541_case_front.stl")))])
src.export(os.path.join(S, "src_assembly.stl"))
render(os.path.join(S, "src_assembly.stl"), os.path.join(S, "z_src_assembly.png"), "z", 6)

