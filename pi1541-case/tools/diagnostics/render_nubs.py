import sys, os
P = r"H:\My Drive\3D printing\STLs\C64"
sys.path.insert(0, os.path.join(P, "tools"))
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from zrender import render
D = os.path.join(P, "docs", "renders")
render(os.path.join(P, "output", "pi1541_zero_rot_case_button_nub_medium.stl"), os.path.join(D, "nub_medium.png"), "z", 60,
       views=[("iso (stem up, cup down)", 30, -50), ("side", 0, 0), ("cup end", -90, -90)], title="button nub - medium")
fig, axs = plt.subplots(1, 3, figsize=(13, 5))
for ax, tag in zip(axs, ["short", "medium", "long"]):
    m = trimesh.load(os.path.join(P, "output", f"pi1541_zero_rot_case_button_nub_{tag}.stl"))
    sec = m.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    for e in sec.discrete:
        ax.plot(e[:, 0], e[:, 2], "k-", lw=1.2)
    ax.axhspan(3.0, 4.51, color="0.85", zorder=0)
    ax.text(3.6, 3.7, "case wall\n(1.5 mm)", fontsize=8, va="center")
    ax.set_aspect("equal"); ax.grid(alpha=.3); ax.set_title(f"{tag}: {m.bounds[1][2]:.1f} mm total")
    ax.set_xlabel("radius (mm)"); ax.set_ylabel("length (mm)")
fig.suptitle("button nubs: cup over the switch plunger (bottom), collar, stem with rounded-off top")
fig.savefig(os.path.join(D, "nub_sections.png"), dpi=90)
