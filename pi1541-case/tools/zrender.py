"""Occlusion-correct z-buffer STL renderer (numpy + matplotlib only for PNG output).

usage: python zrender.py <stl> <out.png> [up=z|y] [size]
Views are orthographic; image is annotated with mm scale ticks.
"""
import sys, os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def look_rot(elev, azim):
    e, a = np.radians(elev), np.radians(azim)
    fwd = -np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])  # camera looks along fwd
    up = np.array([0, 0, 1.0]) if abs(elev) < 89 else np.array([0, 1.0, 0]) * (1 if elev > 0 else -1)
    right = np.cross(fwd, up); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return np.stack([right, up, -fwd])  # rows: screen x, screen y, depth(toward camera)


def raster(V, F, N, R, px_per_mm, pad=4):
    P = V @ R.T
    lo = P[:, :2].min(0); hi = P[:, :2].max(0)
    W = int((hi[0] - lo[0]) * px_per_mm) + 2 * pad
    H = int((hi[1] - lo[1]) * px_per_mm) + 2 * pad
    sx = (P[:, 0] - lo[0]) * px_per_mm + pad
    sy = (hi[1] - P[:, 1]) * px_per_mm + pad
    z = P[:, 2]
    zbuf = np.full((H, W), -np.inf)
    img = np.ones((H, W, 3))
    ncam = N @ R.T
    light = np.array([-0.35, 0.45, 0.82]); light /= np.linalg.norm(light)
    lam = np.abs(ncam @ light)  # two-sided so inside walls are visible
    front = ncam[:, 2] >= 0
    base = np.where(front[:, None], np.array([0.45, 0.62, 0.90]), np.array([0.90, 0.55, 0.45]))  # back faces orange
    col = base * (0.25 + 0.75 * lam[:, None])
    for i, (a, b, c) in enumerate(F):
        x = np.array([sx[a], sx[b], sx[c]]); y = np.array([sy[a], sy[b], sy[c]]); zz = np.array([z[a], z[b], z[c]])
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), W - 1))
        y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), H - 1))
        if x1 < x0 or y1 < y0:
            continue
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        depth = w0 * zz[0] + w1 * zz[1] + w2 * zz[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (depth > sub)
        sub[upd] = depth[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = col[i]
    # edge darkening from depth discontinuities -> crisp outlines
    zb = np.where(np.isfinite(zbuf), zbuf, zbuf[np.isfinite(zbuf)].min() - 50 if np.isfinite(zbuf).any() else 0)
    gy_, gx_ = np.gradient(zb)
    edge = np.hypot(gx_, gy_) > 0.6 / px_per_mm * 3
    img[edge] *= 0.35
    return img, lo, hi, pad


VIEWS = [("iso front-right", 30, -60), ("iso back-left", 30, 120), ("iso underside", -30, -60),
         ("top (looking -Z)", 90, -90), ("bottom (looking +Z)", -90, -90),
         ("front (looking +Y)", 0, -90), ("back (looking -Y)", 0, 90),
         ("right (looking -X)", 0, 0), ("left (looking +X)", 0, 180)]


def render(path, out, up="z", px_per_mm=8, views=VIEWS, title=None):
    m = trimesh.load(path)
    V = m.vertices.copy()
    if up == "y":
        V = np.column_stack([V[:, 0], -V[:, 2], V[:, 1]])
    V = V - (V.min(0) + V.max(0)) / 2
    mm = trimesh.Trimesh(V, m.faces, process=False)
    N = mm.face_normals
    imgs = []
    for name, el, az in views:
        R = look_rot(el, az)
        imgs.append((name, raster(V, mm.faces, N, R, px_per_mm)))
    cols = 3
    rows = int(np.ceil(len(imgs) / cols))
    fig, axs = plt.subplots(rows, cols, figsize=(7 * cols, 5 * rows))
    for ax, (name, (img, lo, hi, pad)) in zip(axs.flat, imgs):
        ax.imshow(img, extent=[lo[0] - pad / px_per_mm, hi[0] + pad / px_per_mm,
                               lo[1] - pad / px_per_mm, hi[1] + pad / px_per_mm])
        ax.set_title(name, fontsize=10)
        ax.tick_params(labelsize=7)
    for ax in list(axs.flat)[len(imgs):]:
        ax.axis("off")
    fig.suptitle(title or os.path.basename(path), fontsize=13)
    plt.tight_layout()
    fig.savefig(out, dpi=80)
    plt.close(fig)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], up=sys.argv[3] if len(sys.argv) > 3 else "z",
           px_per_mm=float(sys.argv[4]) if len(sys.argv) > 4 else 8)
