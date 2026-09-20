"""Checks for rotated rev 2: raise, board back-off, nub holes, enlarged ports, crested vents, tunnel, assembly path."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from ops import U, D, I, BOX, moved
S = WORK
L = lambda n: trimesh.load(os.path.join(S, f"zup_pi1541_zero_rot_case_{n}.stl"))
bot, ts, tn = L("bottom"), L("top_slot"), L("top_noslot")
src = load_source(); tgt = load_target()
RAISE, BACKOFF = 3.5, 3.5
DXr, DYr, DZ = -46.6 + 31.5, 28.31 - 17.75 - BACKOFF, -18.0 + RAISE
T = trimesh.transformations.translation_matrix([DXr, DYr, DZ]) @ trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
BTN_X = [-22.5, -11.75, -1.0, 9.75, 20.5]
BTN_Z = 23.49 + DZ
BOARD_EDGE = 28.31 - BACKOFF


def hits(m, o, d):
    h = m.ray.intersects_location([o], [d])[0]
    return np.atleast_2d(h) if np.size(h) else np.zeros((0, 3))


print("== basics")
for n, m in [("bottom", bot), ("top_slot", ts), ("top_noslot", tn)]:
    print(f"   {n:11s} watertight={m.is_watertight} vol={m.volume:.0f}")
print(f"   topâˆ©bottom = {I(ts, bot).volume:.2f} (orig 1.03) ; bottomâˆ©bezel = {I(bot, src['front']).volume:.2f}")
print(f"   outside original shells: bottom {D(bot, src['bottom'].convex_hull).volume:.3f}, top {D(tn, src['top'].convex_hull).volume:.3f}")

print("== Zero hardware space (cavity) vs case")
cav = D(BOX([-33.5, -17.75, 2.0], [33.5, 17.75, 26.0]), U([tgt["bottom"], tgt["lid"]]))
cav.apply_transform(T)
for n, m in [("bottom", bot), ("top_noslot", tn)]:
    print(f"   {n}: {I(cav, m).volume:.2f} mm3")

print("== assembly: can the top drop straight down past the switches / encoder?")
sw = U([BOX([-x + DXr - 3.2, BOARD_EDGE - 0.5, BTN_Z - 3.2], [-x + DXr + 3.2, BOARD_EDGE + 2.5, BTN_Z + 3.2]) for x in BTN_X])
sw_sweep = U([moved(sw, dz=-d) for d in np.arange(0, 14.1, 2.0)])   # as the top descends, hardware rises in its frame -> sweep down
print(f"   switch envelope swept upward vs top: {I(sw_sweep, tn).volume:.3f} mm3")
enc_c = trimesh.transformations.translation_matrix([DXr, DYr, 0]) @ trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
ec = (np.array([-26.5, -2.25, 0, 1]) @ enc_c.T)[:2]
enc = trimesh.creation.cylinder(radius=3.6, height=26, sections=48)
enc.apply_translation([ec[0], ec[1], 4 + 13])
print(f"   encoder shaft/bush (7.2 dia) column vs top: {I(enc, tn).volume:.3f} mm3")

print("== nub holes (5) open through the wall?")
for i, x in enumerate(BTN_X):
    xs = -x + DXr
    h = hits(tn, [xs, 60, BTN_Z], [0, -1, 0])
    ys = sorted(h[:, 1], reverse=True)[:2]
    print(f"   button {i+1} at x={xs:6.2f}: wall hits y={np.round(ys, 2).tolist()} -> open={len(h) == 0 or all(y < 28 for y in ys)}")
op = [round(z, 2) for z in np.arange(4, 14, 0.1) if not any(hh[1] > 28 for hh in hits(tn, [-14.1 + 0, 60, z], [0, -1, 0]))]

print("== port holes: size and clear opening")
for name, (x0t, x1t, z0t, z1t) in zip(["mini-HDMI", "micro-USB", "micro-USB PWR"],
                                      [(-27.6, -14.6, 6.3, 11.3), (3.4, 12.4, 6.3, 10.3), (16.0, 25.0, 6.3, 10.3)]):
    xs = sorted([-x0t + DXr, -x1t + DXr]); zc = (z0t + z1t) / 2 + DZ
    xr = [round(x, 2) for x in np.arange(xs[0] - 3, xs[1] + 3, 0.1) if not any(h[1] > 28 for h in hits(bot, [x, 60, zc], [0, -1, 0]))]
    zr = [round(z, 2) for z in np.arange(z0t + DZ - 3, z1t + DZ + 3, 0.1) if not any(h[1] > 28 for h in hits(bot, [(xs[0] + xs[1]) / 2, 60, z], [0, -1, 0]))]
    print(f"   {name:14s}: open x {min(xr):.1f}..{max(xr):.1f} ({max(xr)-min(xr):.1f} wide), z {min(zr):.1f}..{max(zr):.1f} ({max(zr)-min(zr):.1f} tall); panel top edge z=-2")
print(f"   socket face now sits {29.65 - (BOARD_EDGE + 1.5):.2f} mm behind the panel face")

print("== light tunnel")
tz = [round(z, 2) for z in np.arange(8, 18, 0.1) if not any(h for h in hits(tn, [-7.35 + 0, 8.81 - BACKOFF, z], [0, 0, -1]))]
print(f"   display sits at z={26.0 + DZ:.1f}, plate underside z=16.0 -> depth {16.0 - (26.0 + DZ):.1f} mm (was 8.0)")
print(f"   encoder shaft gains {RAISE} mm of protrusion")

print("== vents: groove floor should follow the surface over both side edges")
def zt(m, x, y):
    h = hits(m, [x, y, 40], [0, 0, -1]); return round(h[:, 2].max(), 2) if len(h) else None
gx = -50.0 + 6 * 2.0 + 0.5
print("   groove x=%.1f:" % gx, [(y, zt(tn, gx, y)) for y in [0, 20, 26, 27, 28, 29, 29.5, 30, -27, -29, -30]])
print("   ridge  x=%.1f:" % (gx + 1.0), [(y, zt(tn, gx + 1.0, y)) for y in [26, 28, 29, 30, -29, -30]])



