import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from ops import U, D, I
from zrender import render
S = WORK
DXr, DYr, DZ = -46.6 + 31.5, 28.31 - 17.75 - 3.5, -14.5
L = lambda n: trimesh.load(os.path.join(S, f"zup_pi1541_zero_rot_case_{n}.stl"))
bot, ts, tn = L("bottom"), L("top_slot"), L("top_noslot")
src = load_source()
tgt = load_target()
from ops import BOX
cav = D(BOX([-33.5, -17.75, 2.0], [33.5, 17.75, 26.0]), U([tgt["bottom"], tgt["lid"]]))
cav.apply_transform(trimesh.transformations.translation_matrix([DXr, DYr, DZ]) @ trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))

print("== mating (originals: topâˆ©bottom 1.03, bezel 0)")
for name, t in [("top_slot", ts), ("top_noslot", tn)]:
    print(f"  {name} âˆ© bottom = {I(t, bot).volume:.2f} ; âˆ© bezel = {I(t, src['front']).volume:.2f}")
print(f"  bottom âˆ© bezel = {I(bot, src['front']).volume:.2f}")

print("== nothing outside the original shells (volume outside original convex hull)")
for name, m, o in [("bottom", bot, src["bottom"]), ("top_slot", ts, src["top"]), ("top_noslot", tn, src["top"])]:
    print(f"  {name}: {D(m, o.convex_hull).volume:.3f} mm3")

print("== material inside the Zero hardware space")
for name, m in [("bottom", bot), ("top_slot", ts), ("top_noslot", tn)]:
    c = I(cav, m); print(f"  {name}: {c.volume:.2f} mm3")
    for p in sorted(c.split(only_watertight=False), key=lambda p: -abs(p.volume))[:5]:
        if abs(p.volume) > 0.05:
            b = p.bounds; print(f"     {p.volume:6.2f} mm3 x {b[0][0]:.1f}..{b[1][0]:.1f} y {b[0][1]:.1f}..{b[1][1]:.1f} z {b[0][2]:.1f}..{b[1][2]:.1f}")

print("== openings on the right side (ray from outside, blocked if it hits the wall y>27)")
asm = U([bot, tn])
feats = [("mini-HDMI", -21.1, 8.8), ("micro-USB", 7.9, 8.3), ("micro-USB PWR", 20.5, 8.3)] + \
        [(f"button {i+1}", xc, 21.5) for i, xc in enumerate([-22.5, -11.75, -1.0, 9.75, 20.5])]
for k, xt, zt in feats:
    x, z = -xt + DXr, zt + DZ
    h = asm.ray.intersects_location([[x, 60, z]], [[0, -1, 0]])[0]
    print(f"  {k:14s} at x={x:6.2f} z={z:6.2f}: blocked={any(hh[1] > 27 for hh in h)}")
print("== top openings")
for name, m in [("slot", ts), ("no-slot", tn)]:
    for k, (xt, yt) in [("display", (-7.75, 1.75)), ("encoder", (-26.5, -2.25)), ("DIN slot", (28, -2.5))]:
        x, y = -xt + DXr, -yt + DYr
        h = m.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]
        print(f"  {name:8s} {k:8s} at ({x:6.2f},{y:6.2f}): open={len(h) == 0}")
print("== left side is blank now (old Pi 3B ports/buttons closed)")
for k, x, z in [("old micro-USB", -38.2, -10.6), ("old HDMI", -16.4, -9.1), ("old audio", 5.0, -9.1), ("old btn 1", -36.1, 4.8), ("old btn 5", 4.1, 4.8)]:
    h = asm.ray.intersects_location([[x, -60, z]], [[0, 1, 0]])[0]
    print(f"  {k:14s} closed={any(hh[1] < -27.5 for hh in h)}")
def ztop(m, x, y):
    h = m.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])[0]; return round(h[:, 2].max(), 3) if len(h) else None
print("== vents: old area (y 5..29) must be flat 17.5, back edge profile must match original")
print("  old vent area x=-23:", [(y, ztop(tn, -23, y)) for y in [5, 12, 20, 27]], "(display window may be open = None)")
print("  old vent area x=-26:", [(y, ztop(tn, -26, y)) for y in [5, 12, 20, 27, 29, 29.5, 30, 30.5]])
print("  original at x=-31  :", [(y, ztop(src['top'], -31, y)) for y in [29, 29.5, 30, 30.5]])
print("  new vents x=-23    :", [(y, ztop(tn, -23, y)) for y in [-27.5, -27, -26, -15, -5, -4.2, -3.8]])

for n, m in [("bottom", bot), ("top_noslot", tn), ("top_slot", ts)]:
    render(os.path.join(S, f"zup_pi1541_zero_rot_case_{n}.stl"), os.path.join(S, f"rr_{n}.png"), "z", 7)
trimesh.util.concatenate([bot, ts, src["front"]]).export(os.path.join(S, "rot_asm.stl"))
render(os.path.join(S, "rot_asm.stl"), os.path.join(S, "rr_asm.png"), "z", 6)




