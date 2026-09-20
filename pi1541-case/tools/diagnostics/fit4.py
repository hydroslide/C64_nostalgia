"""Placement study v2: through-hole maps by ray casting + 3D clash of Zero cavity vs source solids."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

S = os.path.dirname(__file__)
src = load_source(); tgt = load_target()
DX, DY, DZ = -15.58, -10.56, -18.0
T = trimesh.transformations.translation_matrix([DX, DY, DZ])

def slab(mesh, axis, lo, hi):
    n = np.eye(3)[axis]
    m = mesh.slice_plane(n * lo, n, cap=True)
    return m.slice_plane(n * hi, -n, cap=True)

def through_map(mesh, axis, u_rng, v_rng, step=0.25):
    """Cast rays along `axis` through mesh; returns grid (v,u) True where ray passes WITHOUT hitting (a hole)."""
    ax2 = [i for i in range(3) if i != axis]
    us = np.arange(*u_rng, step); vs = np.arange(*v_rng, step)
    U, V = np.meshgrid(us, vs)
    O = np.zeros((U.size, 3)); O[:, ax2[0]] = U.ravel(); O[:, ax2[1]] = V.ravel(); O[:, axis] = -500
    D = np.zeros_like(O); D[:, axis] = 1
    hit = mesh.ray.intersects_any(O, D)
    return (~hit).reshape(U.shape), us, vs

# ---- 1. front wall maps (looking along +Y): source front slab y<-27.5 ; target front slab y_t<-17 moved
src_front = trimesh.util.concatenate([slab(src["bottom"], 1, -40, -27.6), slab(src["top"], 1, -40, -27.6)])
tgt_asm = trimesh.util.concatenate([tgt["bottom"], tgt["lid"]]); tgt_asm.apply_transform(T)
tgt_front = slab(tgt_asm, 1, -40, -17.75 + DY + 0.3)
sm, us, vs = through_map(src_front, 1, (-60, 60), (-19, 19))
tm, _, _ = through_map(tgt_front, 1, (-60, 60), (-19, 19))
# target outer outline region only (outside its box everything is 'through')
inside_t = (us[None, :] > -35.5 + DX + 0.5) & (us[None, :] < 35.5 + DX - 0.5) & (vs[:, None] > DZ + 0.5) & (vs[:, None] < 28 + DZ - 0.5)
tm &= inside_t
# drop target vent slots: keep holes wider than 3mm (ports) or in the button band
from scipy import ndimage
lab, n = ndimage.label(tm)
keep = np.zeros_like(tm)
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    w = (xs.max() - xs.min() + 1) * 0.25; h = (ys.max() - ys.min() + 1) * 0.25
    zc = vs[ys].mean()
    tag = "button" if zc > -1 else ("port" if w > 5 else "vent")
    print(f"target front opening: x {us[xs.min()]:.2f}..{us[xs.max()]:.2f} z {vs[ys.min()]:.2f}..{vs[ys.max()]:.2f} ({w:.2f}x{h:.2f}) -> {tag}")
    if tag != "vent": keep[lab == i] = True
fig, axs = plt.subplots(3, 1, figsize=(16, 16))
def show(ax, smap, tmap, us, vs, title, xl):
    img = np.ones(smap.shape + (3,))
    img[~smap] = [0.75, 0.75, 0.8]           # source material
    img[smap & tmap] = [1, 1, 1]
    img[tmap & ~smap] = [0.95, 0.35, 0.3]    # need to CUT (Zero opening over source material)
    img[smap & ~tmap & (tmap.shape == smap.shape)] = img[smap & ~tmap]
    ax.imshow(img, origin="lower", extent=[us[0], us[-1], vs[0], vs[-1]])
    ax.set_title(title); ax.grid(alpha=0.3); ax.set_xlabel(xl)
show(axs[0], sm, keep, us, vs, "FRONT (viewed from outside). grey=source material, white=existing source hole, red=Zero opening to cut", "x (mm)")
axs[0].axhline(0, color="b", ls=":", lw=0.8)

# ---- 2. -X end (looking along +X)
src_end = trimesh.util.concatenate([slab(src["bottom"], 0, -70, -50.5), slab(src["top"], 0, -70, -50.5)])
tgt_end = slab(tgt_asm, 0, -60, -33.5 + DX + 0.3)
sm2, us2, vs2 = through_map(src_end, 0, (-34, 34), (-19, 19))
tm2, _, _ = through_map(tgt_end, 0, (-34, 34), (-19, 19))
inside2 = (us2[None, :] > -19.75 + DY + 0.5) & (us2[None, :] < 19.75 + DY - 0.5) & (vs2[:, None] > DZ + 0.5) & (vs2[:, None] < 28 + DZ - 0.5)
tm2 &= inside2
lab, n = ndimage.label(tm2); keep2 = np.zeros_like(tm2)
for i in range(1, n + 1):
    ys, xs = np.where(lab == i); w = (xs.max() - xs.min() + 1) * .25
    if w > 5: keep2[lab == i] = True; print(f"target -X opening (SD): y {us2[xs.min()]:.2f}..{us2[xs.max()]:.2f} z {vs2[ys.min()]:.2f}..{vs2[ys.max()]:.2f}")
show(axs[1], sm2, keep2, us2, vs2, "-X END (viewed from outside is mirrored: this is looking +X from inside-out; y horizontal)", "y (mm)")
lab, n = ndimage.label(sm2 & (np.abs(us2[None, :]) < 31) )
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    if len(xs) > 8 and not (ys.min() == 0 or ys.max() == len(vs2) - 1): print(f"source -X end hole: y {us2[xs.min()]:.2f}..{us2[xs.max()]:.2f} z {vs2[ys.min()]:.2f}..{vs2[ys.max()]:.2f}")

# ---- 3. top plate (looking down -Z; ray along +Z from below)
src_topplate = slab(src["top"], 2, 14.5, 30)
sm3, us3, vs3 = through_map(src_topplate, 2, (-58, 58), (-32, 32))
tgt_top = slab(tgt_asm, 2, 26 + DZ - 0.01, 40)
tm3, _, _ = through_map(tgt_top, 2, (-58, 58), (-32, 32))
inside3 = (us3[None, :] > -35.5 + DX + 0.5) & (us3[None, :] < 35.5 + DX - 0.5) & (vs3[:, None] > -19.75 + DY + 0.5) & (vs3[:, None] < 19.75 + DY - 0.5)
tm3 &= inside3
show(axs[2], sm3, tm3, us3, vs3, "TOP plate from above. white = existing source openings (display skin counts as material), red = Zero lid openings", "x (mm)")
lab, n = ndimage.label(sm3 & (np.abs(us3[None, :]) < 55) & (np.abs(vs3[:, None]) < 29))
for i in range(1, n + 1):
    ys, xs = np.where(lab == i)
    if len(xs) > 8: print(f"source top opening: x {us3[xs.min()]:.2f}..{us3[xs.max()]:.2f} y {vs3[ys.min()]:.2f}..{vs3[ys.max()]:.2f}")
plt.tight_layout(); fig.savefig(os.path.join(S, "overlay2.png"), dpi=70)

# ---- 4. 3D clash: Zero cavity (inner box minus target solids) moved into source, intersect with source solids
cav = trimesh.creation.box(bounds=[[-33.5, -17.75, 2.0], [33.5, 17.75, 26.0]])
tsol = trimesh.util.concatenate([tgt["bottom"], tgt["lid"]])
tsol = trimesh.boolean.union([tgt["bottom"], tgt["lid"]], engine="manifold")
cav = trimesh.boolean.difference([cav, tsol], engine="manifold")
cav.apply_transform(T)
ssol = trimesh.boolean.union([src["bottom"], src["top"]], engine="manifold")
clash = trimesh.boolean.intersection([cav, ssol], engine="manifold")
print(f"\nZero cavity volume {cav.volume:.0f} mm3; source material inside it: {clash.volume:.1f} mm3")
if clash.volume > 0.01:
    for p in sorted(clash.split(only_watertight=False), key=lambda p: -p.volume)[:12]:
        b = p.bounds
        print(f"  clash piece {p.volume:7.1f} mm3  x {b[0][0]:.1f}..{b[1][0]:.1f}  y {b[0][1]:.1f}..{b[1][1]:.1f}  z {b[0][2]:.1f}..{b[1][2]:.1f}")
clash.export(os.path.join(S, "clash.stl"))
cav.export(os.path.join(S, "zero_cavity_in_source.stl"))
