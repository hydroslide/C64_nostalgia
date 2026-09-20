import sys, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
sys.path.insert(0, S)
from common import *
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fr = load_source()["front"]
fig, axs = plt.subplots(1, 5, figsize=(22, 6))
for ax, y in zip(axs, [0, -3, -14.5, -18, 15]):
    ps, keep = section_polys(fr, [0, y, 0], [0, 1, 0])
    for p in ps:
        x, z = p.exterior.xy; ax.fill(x, z, alpha=.4, color="steelblue"); ax.plot(x, z, "k-", lw=.8)
        for h in p.interiors:
            hx, hz = zip(*h.coords); ax.fill(hx, hz, color="white"); ax.plot(hx, hz, "k-", lw=.8)
    ax.set_title(f"bezel section y={y} (x right = outward face)"); ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_xlim(52.5, 61); ax.set_ylim(-15, 5)
fig.savefig(os.path.join(S, "bezel_sections.png"), dpi=70)
def xface(y, z):
    h = fr.ray.intersects_location([[80, y, z]], [[-1, 0, 0]])[0]; h = np.atleast_2d(h); return round(float(h[:, 0].max()), 2) if h.size else None
print("face x (outermost) along z at y=-18:", [(round(z,1), xface(-18, z)) for z in np.arange(-13.8, 4.1, 0.5)])
print("face x along z at y=0:", [(round(z,1), xface(0, z)) for z in np.arange(-13.8, 4.1, 0.5)])
print("face x along y at z=-5:", [(round(y,1), xface(y, -5)) for y in np.arange(-22.4, 22.5, 1.0)])
print("face x along y at z=0.2:", [(round(y,1), xface(y, 0.2)) for y in np.arange(-22.4, 22.5, 1.0)])
