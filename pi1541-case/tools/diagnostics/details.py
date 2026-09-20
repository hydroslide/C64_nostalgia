import os, sys
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
sys.path.insert(0, os.path.dirname(__file__))
from zrender import render

S = os.path.dirname(__file__)
R = r"H:\My Drive\3D printing\STLs\C64\real_files"
yup = lambda m: trimesh.Trimesh(np.column_stack([m.vertices[:, 0], -m.vertices[:, 2], m.vertices[:, 1]]), m.faces)

# 1. tiny loose bodies in the lid
lid = trimesh.load(os.path.join(R, "target", "obj_2_Assembly.stl"))
parts = sorted(lid.split(only_watertight=False), key=lambda p: -len(p.faces))
lo = lid.bounds[0]
fig, ax = plt.subplots(figsize=(10, 6))
for i, p in enumerate(parts):
    t = p.triangles[:, :, :2] - lo[:2]
    ax.add_collection(PolyCollection(t, facecolors="lightgray" if i == 0 else "red", edgecolors="none", alpha=0.25 if i == 0 else 1))
    if i:
        print(f"loose body {i}: faces={len(p.faces)} watertight={p.is_watertight} "
              f"x={p.bounds[0][0]-lo[0]:.2f}..{p.bounds[1][0]-lo[0]:.2f} y={p.bounds[0][1]-lo[1]:.2f}..{p.bounds[1][1]-lo[1]:.2f} z={p.bounds[0][2]:.2f}..{p.bounds[1][2]:.2f}")
ax.set_xlim(0, 71); ax.set_ylim(0, 39.5); ax.set_aspect("equal"); ax.set_title("lid: loose bodies (red) over main body (gray), plan view from +Z")
fig.savefig(os.path.join(S, "lid_loose.png"), dpi=90)
# zoom
ax.set_xlim(8, 26); ax.set_ylim(8, 30); fig.savefig(os.path.join(S, "lid_loose_zoom.png"), dpi=90)

# 2. cross-sections
def section_plot(mesh, origin, normal, title, fn):
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    fig, ax = plt.subplots(figsize=(12, 4))
    if sec is not None:
        for e in sec.discrete:
            ax.plot(e[:, 0] if normal[0] == 0 else e[:, 1], e[:, 2] if normal[2] == 0 else e[:, 1], "k-", lw=0.8)
    ax.set_aspect("equal"); ax.grid(alpha=0.3); ax.set_title(title)
    fig.savefig(os.path.join(S, fn), dpi=90); plt.close(fig)

top = yup(trimesh.load(os.path.join(R, "source", "pi1541_case_top.stl")))
bot = yup(trimesh.load(os.path.join(R, "source", "pi1541_case_bottom.stl")))
fr = yup(trimesh.load(os.path.join(R, "source", "pi1541_case_front.stl")))
asm = trimesh.util.concatenate([top, bot, fr])
section_plot(asm, [ -18, 0, 0], [1, 0, 0], "source assembly, section X=-18 (through display + vents), YZ plane", "sec_src_x-18.png")
section_plot(asm, [0, 0, 0], [0, 1, 0], "source assembly, section Y=0 (long axis), XZ plane", "sec_src_y0.png")
tb = trimesh.load(os.path.join(R, "target", "obj_1_Case Bottom.stl"))
tl = trimesh.load(os.path.join(R, "target", "obj_2_Assembly.stl"))
# put lid on bottom as it would be assembled: flip lid upside down, align footprint, sit on top
tl2 = tl.copy()
tl2.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
tl2.apply_translation([tb.bounds[0][0] - tl2.bounds[0][0], tb.bounds[0][1] - tl2.bounds[0][1], tb.bounds[1][2] + 9.5 - tl2.bounds[1][2]])
# try both lid orientations about Z to see which fits the bottom's notch; report bounds
tasm = trimesh.util.concatenate([tb, tl2])
c = tb.bounds.mean(0)
section_plot(tasm, [c[0], c[1], 0], [1, 0, 0], "target: bottom + flipped lid stacked (lid Z offset guessed), section at X centre", "sec_tgt_x.png")
section_plot(tasm, [c[0], c[1], 0], [0, 1, 0], "target: section at Y centre", "sec_tgt_y.png")

# 3. wall thickness via ray casting from inside outward at mid-height
def wall(mesh, pt, d):
    loc, _, _ = mesh.ray.intersects_location([pt], [d])
    if len(loc) == 0: return 'miss (opening)'
    ds = np.sort(np.linalg.norm(loc - pt, axis=1))
    return np.round(ds[:4], 2)
print("source bottom wall hits (dist from centre at z=-8) +X,-X,+Y,-Y,-Z:",
      [wall(bot, np.array([-20, 0, -8.0]), np.array(d, float)) for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,-1)]])
print("source top wall hits (z=+8):",
      [wall(top, np.array([10, 0, 8.0]), np.array(d, float)) for d in [(0,1,0),(0,-1,0),(0,0,1)]])
cz = tb.bounds[0][2] + 12
print("target bottom hits from centre z=12: +X,-X,+Y,-Y,-Z:",
      [wall(tb, np.array([c[0], c[1], cz]), np.array(d, float)) for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,-1)]])

render(None, None) if False else None
asm.export(os.path.join(S, "src_assembly.stl"))
tasm.export(os.path.join(S, "tgt_assembly.stl"))

