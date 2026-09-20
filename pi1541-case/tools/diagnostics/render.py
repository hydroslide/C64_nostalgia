"""Render an STL from several viewpoints with simple Lambert shading (matplotlib, no GPU)."""
import sys, os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def render(path, out, up="z", views=None, title=None):
    m = trimesh.load(path)
    v = m.vertices.copy()
    if up == "y":  # convert Y-up to Z-up for viewing: (x, y, z) -> (x, -z, y)
        v = np.column_stack([v[:, 0], -v[:, 2], v[:, 1]])
        m = trimesh.Trimesh(v, m.faces, process=False)
    v = m.vertices - m.bounds.mean(axis=0)
    tris = v[m.faces]
    n = m.face_normals
    views = views or [("iso front-right", 25, -55), ("iso back-left", 25, 125), ("top", 90, -90),
                      ("bottom", -90, -90), ("front (-Y)", 0, -90), ("right (+X)", 0, 0)]
    cols = 3
    rows = int(np.ceil(len(views) / cols))
    fig = plt.figure(figsize=(6 * cols, 5 * rows))
    r = np.abs(v).max()
    for i, (name, elev, azim) in enumerate(views):
        ax = fig.add_subplot(rows, cols, i + 1, projection="3d")
        e, a = np.radians(elev), np.radians(azim)
        cam = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
        light = cam + np.array([0.3, 0.2, 0.6]); light /= np.linalg.norm(light)
        shade = np.clip(n @ light, 0, 1) * 0.75 + 0.25
        # painter's sort handled by mpl; reduce clutter by dropping back faces
        front = (n @ cam) > -0.05
        colors = np.column_stack([shade * 0.55, shade * 0.7, shade * 0.95, np.ones_like(shade)])
        pc = Poly3DCollection(tris[front], facecolors=colors[front], edgecolors="none", linewidths=0)
        ax.add_collection3d(pc)
        ax.set_xlim(-r, r); ax.set_ylim(-r, r); ax.set_zlim(-r, r)
        ax.set_box_aspect((1, 1, 1))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(name)
    fig.suptitle(title or os.path.basename(path), fontsize=14)
    plt.tight_layout()
    fig.savefig(out, dpi=90)
    plt.close(fig)

if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], up=sys.argv[3] if len(sys.argv) > 3 else "z")
