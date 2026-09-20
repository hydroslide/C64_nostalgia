"""Renders the rev-4 side-entry button nubs: 3D views plus the two cross-sections that matter.

Along the slot (x-z) you see the open channel; across it (y-z) you see the C that still holds the plunger.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from zrender import render

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT, DOCS = os.path.join(ROOT, "output"), os.path.join(ROOT, "docs", "renders")
COLLAR_L, BORE_DEEP, MOUTH_RELIEF, SLOT_W, SWITCH_W = 3.0, 2.5, 1.11, 3.9, 6.4

render(os.path.join(OUT, "pi1541_zero_rot_case_button_nub_medium.stl"),
       os.path.join(DOCS, "nub_slot_medium.png"), "z", 60,
       views=[("iso, open side toward us", 25, 20), ("open side on", 0, 0), ("cup end", -90, -90)],
       title="button nub (medium) - side-entry cup")

fig, axs = plt.subplots(2, 3, figsize=(13, 8))
for col, tag in enumerate(["short", "medium", "long"]):
    m = trimesh.load(os.path.join(OUT, f"pi1541_zero_rot_case_button_nub_{tag}.stl"))
    for row, (normal, lbl) in enumerate([([0, 1, 0], "along the slot"), ([1, 0, 0], "across the slot")]):
        ax = axs[row][col]
        sec = m.section(plane_origin=[0, 0, 0], plane_normal=normal)
        for e in sec.discrete:
            ax.plot(e[:, 0 if row == 0 else 1], e[:, 2], "k-", lw=1.2)
        ax.axhspan(COLLAR_L, COLLAR_L + 1.51, color="0.85", zorder=0)
        ax.axhspan(-0.1, MOUTH_RELIEF, color="#ffd9d9", zorder=0)
        ax.axhline(BORE_DEEP, color="c", ls=":", lw=1)
        if row == 0:
            ax.text(3.6, COLLAR_L + 0.7, "case wall", fontsize=7, va="center")
            ax.text(-5.2, MOUTH_RELIEF / 2, "switch-body relief", fontsize=7, va="center", color="#a33")
        ax.set_aspect("equal"); ax.grid(alpha=.3)
        ax.set_title(f"{tag} - {lbl}", fontsize=9)
        ax.set_xlabel("mm"); ax.set_ylabel("length (mm)")
fig.suptitle(f"rev 4 side-entry cup: {SLOT_W} mm channel open on one side (top row = the opening), "
             f"mouth cut back {MOUTH_RELIEF} mm all round to clear the {SWITCH_W} mm switch body")
fig.tight_layout()
fig.savefig(os.path.join(DOCS, "nub_slot_sections.png"), dpi=90)
print("wrote nub_slot_medium.png, nub_slot_sections.png")
