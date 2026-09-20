import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from zrender import render
S = WORK
DX, DY, DZ = -15.08, -10.56, -18.0
L = lambda n: trimesh.load(os.path.join(S, f"zup_{n}.stl"))
bot, ts, tn = L("bottom"), L("top_slot"), L("top_noslot")
src = load_source(); tgt = load_target()
U = lambda ms: trimesh.boolean.union(ms, engine="manifold")
I = lambda a, b: trimesh.boolean.intersection([a, b], engine="manifold")
D = lambda a, b: trimesh.boolean.difference([a, b], engine="manifold")

# 1. mating: new top vs new bottom, and vs bezel (originals: ~1.03 and 0)
for name, t in [("top_slot", ts), ("top_noslot", tn)]:
    print(f"{name} âˆ© bottom = {I(t, bot).volume:.2f} mm3 ; âˆ© bezel = {I(t, src['front']).volume:.2f} mm3")
print(f"bottom âˆ© bezel = {I(bot, src['front']).volume:.2f} mm3")

# 2. clash with the Zero's hardware space (target cavity = inner box minus target solids), moved into place
cav = D(trimesh.creation.box(bounds=[[-33.5, -17.75, 2.0], [33.5, 17.75, 26.0]]), U([tgt["bottom"], tgt["lid"]]))
cav.apply_translation([DX, DY, DZ])
for name, m in [("bottom", bot), ("top_slot", ts), ("top_noslot", tn)]:
    c = I(cav, m)
    print(f"\n{name}: material inside Zero hardware space = {c.volume:.2f} mm3")
    for p in sorted(c.split(only_watertight=False), key=lambda p: -abs(p.volume))[:6]:
        if abs(p.volume) > 0.05:
            b = p.bounds; print(f"   {p.volume:7.2f} mm3 x {b[0][0]:.1f}..{b[1][0]:.1f} y {b[0][1]:.1f}..{b[1][1]:.1f} z {b[0][2]:.1f}..{b[1][2]:.1f}")

# 3. every Zero opening must be open: probe rays through each opening centre
def open_through(mesh, p, d):
    return not mesh.ray.intersects_any([np.array(p, float) - np.array(d, float) * 30], [d])[0]
asm_s = U([bot, ts]); asm_n = U([bot, tn])
checks = {
    "mini-HDMI": ([-21.1 + DX, -25, 8.8 + DZ], [0, 1, 0]),
    "micro-USB 1": ([7.9 + DX, -25, 8.3 + DZ], [0, 1, 0]),
    "micro-USB 2 (PWR)": ([20.5 + DX, -25, 8.3 + DZ], [0, 1, 0]),
}
for i, xc in enumerate([-22.5, -11.75, -1.0, 9.75, 20.5]):
    checks[f"button {i+1}"] = ([xc + DX, -25, 21.5 + DZ], [0, 1, 0])
for k, (p, d) in checks.items():
    # ray from outside (front) towards inside, stop inside: test only the wall: use segment check
    o = np.array(p) - np.array([0, 10, 0]); hits = asm_n.ray.intersects_location([o], [d])[0]
    wall_hits = [h for h in hits if h[1] < -27.0]
    print(f"{k:18s} wall blocked: {len(wall_hits) > 0}")
# SD
o = np.array([-65, -11.3 + 0, 7.5 + DZ]); hits = asm_n.ray.intersects_location([o], [[1, 0, 0]])[0]
print(f"{'SD slot':18s} wall blocked: {any(h[0] < -53.5 for h in hits)}")
for name, m in [("slot version", ts), ("no-slot version", tn)]:
    for k, p in [("display", [-7.75 + DX, 1.75 + DY]), ("encoder", [-26.5 + DX, -2.25 + DY]), ("DIN slot", [28 + DX, -2.5 + DY])]:
        hits = m.ray.intersects_location([[p[0], p[1], 30]], [[0, 0, -1]])[0]
        print(f"{name:15s} {k:8s}: open through top = {len(hits) == 0 or hits[:,2].max() < 6}  (first hit z={hits[:,2].max() if len(hits) else None})")

# 4. old Pi 3B holes closed?
for k, p, d in [("old micro-USB", [-38.2, -35, -10.6], [0, 1, 0]), ("old HDMI", [-16.4, -35, -9.1], [0, 1, 0]),
                ("old audio", [5.0, -35, -9.1], [0, 1, 0]), ("old button 1", [-36.1, -35, 4.8], [0, 1, 0]),
                ("old button 5", [4.1, -35, 4.8], [0, 1, 0])]:
    hits = asm_n.ray.intersects_location([p], [d])[0]
    print(f"{k:14s} closed: {any(h[1] < -27.5 for h in hits)}")
for k, p in [("old display", [-15, -4]), ("old DIN opening", [-45, 10]), ("old SD notch (floor)", [-50, 0])]:
    hits = asm_n.ray.intersects_location([[p[0], p[1], 40]], [[0, 0, -1]])[0]
    print(f"{k:22s} closed from above: {len(hits) > 0}  z hits: {np.round(sorted(hits[:,2]),2)}")

# 5. renders
for n in ["bottom", "top_slot", "top_noslot"]:
    render(os.path.join(S, f"zup_{n}.stl"), os.path.join(S, f"r_{n}.png"), "z", 7)
a = trimesh.util.concatenate([bot, ts, src["front"]]); a.export(os.path.join(S, "zup_asm_slot.stl"))
render(os.path.join(S, "zup_asm_slot.stl"), os.path.join(S, "r_asm_slot.png"), "z", 6)

