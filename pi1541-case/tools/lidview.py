import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from zrender import look_rot
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm

def raster_colored(V, F, facecol, R, ppm=10, pad=4):
    P = V @ R.T
    lo = P[:, :2].min(0); hi = P[:, :2].max(0)
    W = int((hi[0]-lo[0])*ppm)+2*pad; H = int((hi[1]-lo[1])*ppm)+2*pad
    sx = (P[:, 0]-lo[0])*ppm+pad; sy = (hi[1]-P[:, 1])*ppm+pad; z = P[:, 2]
    zb = np.full((H, W), -np.inf); img = np.ones((H, W, 3))
    for i, (a, b, c) in enumerate(F):
        x = np.array([sx[a], sx[b], sx[c]]); y = np.array([sy[a], sy[b], sy[c]]); zz = np.array([z[a], z[b], z[c]])
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), W-1))
        y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), H-1))
        den = (y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
        if x1 < x0 or y1 < y0 or abs(den) < 1e-12: continue
        gx, gy = np.meshgrid(np.arange(x0, x1+1)+.5, np.arange(y0, y1+1)+.5)
        w0 = ((y[1]-y[2])*(gx-x[2])+(x[2]-x[1])*(gy-y[2]))/den
        w1 = ((y[2]-y[0])*(gx-x[2])+(x[0]-x[2])*(gy-y[2]))/den
        w2 = 1-w0-w1
        ins = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        d = w0*zz[0]+w1*zz[1]+w2*zz[2]
        sub = zb[y0:y1+1, x0:x1+1]; u = ins & (d > sub); sub[u] = d[u]
        img[y0:y1+1, x0:x1+1][u] = facecol[i]
    f = np.isfinite(zb); zz = np.where(f, zb, zb[f].min()-50)
    gy_, gx_ = np.gradient(zz); img[np.hypot(gx_, gy_) > 0.2] *= 0.3
    return img, lo, hi, pad

def height_view(mesh, zlo, zhi, views, out, title, ppm=10):
    V = mesh.vertices; F = mesh.faces; N = mesh.face_normals
    zc = mesh.triangles_center[:, 2]
    cmap = matplotlib.colormaps["turbo"]
    base = cmap(np.clip((zc - zlo) / (zhi - zlo), 0, 1))[:, :3]
    fig, axs = plt.subplots(1, len(views), figsize=(9*len(views), 7))
    for ax, (name, el, az) in zip(np.atleast_1d(axs), views):
        R = look_rot(el, az)
        light = np.array([-.3, .4, .85]); light /= np.linalg.norm(light)
        shade = 0.45 + 0.55*np.abs((N @ R.T) @ light)
        img, lo, hi, pad = raster_colored(V, F, base*shade[:, None], R, ppm)
        ax.imshow(img, extent=[lo[0]-pad/ppm, hi[0]+pad/ppm, lo[1]-pad/ppm, hi[1]+pad/ppm]); ax.set_title(name); ax.grid(alpha=.3)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(zlo, zhi)); fig.colorbar(sm, ax=axs, label="z (mm)")
    fig.suptitle(title); fig.savefig(out, dpi=75); plt.close(fig)

if __name__ == "__main__":
    tgt = load_target()
    S = WORK
    height_view(tgt["lid"], 18.5, 28, [("from below (looking +Z), x mirrored", -90, -90), ("iso from below, front-right", -35, -60), ("iso from below, back-left", -35, 120)],
                os.path.join(S, "lid_under.png"), "Zero lid, assembled orientation, coloured by height (18.5 blue -> 28 red)")


