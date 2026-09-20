"""Rotated variant, rev 2 (after the first test print).

Pi Zero turned 180 deg about Z, non-SD end at the REAR (-X, old DIN end), ports/buttons on the RIGHT side (+Y).
Changes from rev 1, all from print feedback:
  * board RAISED 3.5 mm  -> light tunnel 8.0 -> 4.5 mm deep, 3.5 mm more encoder shaft. Limit: the ports must stay
    inside the lower panel (top edge z=-2) and below the seam.
  * board moved BACK 3.5 mm from the right wall so the top can drop straight down (the switches stick ~2 mm past the
    board edge and used to foul the wall). Buttons are now separate NUBS pushed through the holes from the inside.
  * upper right panel removed (plain sloped wall + round nub holes); lower (port) panel kept, port holes enlarged
    (+1.0 each side, +0.5 up, +1.0 down) because the sockets now sit ~3.3 mm behind the panel face.
  * vent grooves crest over both side edges, using the crest shape of the source's own vents.
  * light tunnel gets a chamfer at its inner bottom edge.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from ops import *
from shapely.geometry import Point, Polygon

S = WORK
PREFIX = "pi1541_zero_rot_case"

RAISE, BACKOFF = 3.5, 3.5
DXr = -46.6 + 31.5
DYr = 28.31 - 17.75 - BACKOFF      # board edge now 3.5 mm off the right wall
DZ = -18.0 + RAISE                 # floors no longer aligned: board sits 3.5 mm higher
ZP = 17.5 - 28.0
R180 = trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1])
MIRROR_Y = np.diag([1.0, -1.0, 1.0, 1.0])

PANEL_X, PANEL_DX = (-46.6, 13.4), 2.8          # lower (port) panel, mirrored from the original left side
BTN_X = [-22.5, -11.75, -1.0, 9.75, 20.5]       # target-frame button centres
BTN_Z = 23.49 + DZ                              # notch arc centre = switch axis
BTN_HOLE_R, NUB_STEM_R, NUB_FLANGE_R = 2.1, 2.0, 3.25
NUB_BODIES = {"short": 1.44, "medium": 1.94, "long": 2.44}   # flange length: wall inner (29.05) - switch face (26.81)
PORTS_T = [(-27.6, -14.6, 6.3, 11.3), (3.4, 12.4, 6.3, 10.3), (16.0, 25.0, 6.3, 10.3)]
VENT_X0, VENT_N, VENT_PITCH, VENT_W, VENT_Y = -50.0, 13, 2.0, 1.0, 26.2
CREST_X = (-27.3, -25.8)                        # one original vent groove, used as the crest donor
WIN_Z = (5.0, 12.0)                             # rear window (no-slot version), inside the DIN channel
win_in = [[-20.2, -5.45], [4.7, 8.95]]          # display window (target frame)


def place(m, dz=DZ):
    return xformed(m, trimesh.transformations.translation_matrix([DXr, DYr, dz]) @ R180)


def mirror_panel(dst, donor_shell, zlo, zhi):
    x0, x1 = PANEL_X
    piece = I(donor_shell, BOX([x0 - EPS, -40, zlo], [x1 + EPS, -28.0 + EPS, zhi]))
    piece = xformed(piece, trimesh.transformations.translation_matrix([PANEL_DX, 0, 0]) @ MIRROR_Y)
    return U([D(dst, BOX([x0 + PANEL_DX, 28.0, zlo], [x1 + PANEL_DX, 40, zhi])), piece])


def prism_y(poly, y0, y1):
    """Extrude an (x,z) polygon along +Y."""
    m = trimesh.creation.extrude_polygon(poly, y1 - y0)
    M = np.eye(4); M[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]; M[:3, 3] = [0, y1, 0]
    m.apply_transform(M); return m


def prism_x(poly, x0, x1):
    """Extrude a (y,z) polygon along +X."""
    m = trimesh.creation.extrude_polygon(poly, x1 - x0)
    M = np.eye(4); M[:3, :3] = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]; M[:3, 3] = [x0, 0, 0]
    m.apply_transform(M); return m


def rrect(x0, x1, z0, z1, r=1.0):
    return sbox(x0 + r, z0 + r, x1 - r, z1 - r).buffer(r, resolution=24)


src = load_source(); tgt = load_target()
tsolid = U([tgt["bottom"], tgt["lid"]])

# ================================================================ BOTTOM
bot0 = fill_bottom_common(src["bottom"])
bot = replace_region(bot0, [-46.6, -40, -18], [13.4, -28.0, 0.5], 0, 30.0)     # left side smooth
bot = mirror_panel(bot, bot0, -20, 0.5)                                        # right side: port panel only
posts = []
for (px, py) in [(-30, -14.25), (28, -14.25), (-30, 8.75), (28, 8.75)]:
    cyl = trimesh.creation.cylinder(radius=3.2, height=6.5, sections=64,
                                    transform=trimesh.transformations.translation_matrix([px, py, 4.25]))
    p = place(I(tgt["bottom"], cyl))
    b = p.bounds
    h = (b[0][2] + 0.5) - (-17.0)
    stem = trimesh.creation.cylinder(radius=2.5, height=h, sections=64)          # extend the post down to the floor
    stem.apply_translation([(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2, -17.0 + h / 2])
    posts += [p, stem]
bot = U([bot] + posts)
ports = []
for (x0t, x1t, z0t, z1t) in PORTS_T:                                            # enlarged port holes
    xs = sorted([-x0t + DXr, -x1t + DXr]); zs = [z0t + DZ, z1t + DZ]
    ports.append(prism_y(rrect(xs[0] - 1.0, xs[1] + 1.0, zs[0] - 1.0, zs[1] + 0.5), 26.0, 33.0))
bot = D(bot, U(ports))

# ================================================================ TOP
top0 = fill_top_common(src["top"])
top = replace_region(top0, [-27.7, 3.9, 14.0], [-1.85, 32.5, 18.5], 0, -31.0)   # remove the source's vent grooves
top = replace_region(top, [-46.6, -40, -2.0], [13.4, -28.0, 18.5], 0, 30.0)     # left side: smooth plain wall
# (no panel on the upper right any more either - the nubs bridge the gap to the switches)
tube = BOX([win_in[0][0] - 1.5, win_in[0][1] - 1.5, 26.0], [win_in[1][0] + 1.5, win_in[1][1] + 1.5, 16.2 - DZ])
top = U([top, place(tube)])
lid_int = I(tgt["lid"], BOX([-33.5, -17.2, 18.4], [33.5, 17.75, 24.0]))   # trimmed clear of the switches (board edge)
polys, _ = section_polys(lid_int, [0, 0, 23.9], [0, 0, 1])
internals = place(U([lid_int] + hollow_extrusions(polys, 23.9, (16.2 - DZ) - 23.9)))
top = U([top, internals])
# round button holes for the nubs, through the plain sloped wall
btns = [prism_y(Point(-xc + DXr, BTN_Z).buffer(BTN_HOLE_R, resolution=48), 26.0, 33.0) for xc in BTN_X]
top = D(top, U(btns))
# display window + tunnel bore, with a chamfer at the tunnel's inner bottom (display) edge; encoder hole
win = through(negative(tgt["lid"], [-21.5, -6.6, 26.0], [6.0, 10.1, 28.0]), (0, 0, 1.0))
tube_bore = place(BOX([win_in[0][0], win_in[0][1], 25.0], [win_in[1][0], win_in[1][1], 34.5]))
mouth = trimesh.util.concatenate([
    place(BOX([win_in[0][0], win_in[0][1], 25.9], [win_in[1][0], win_in[1][1], 26.0])),
    place(BOX([win_in[0][0] - 0.8, win_in[0][1] - 0.8, 25.0], [win_in[1][0] + 0.8, win_in[1][1] + 0.8, 25.1]))]).convex_hull
top = D(top, U([place(win, ZP), tube_bore, mouth]))
enc = through(negative(tgt["lid"], [-31.0, -6.75, 26.0], [-22.0, 2.25, 28.0]), (0, 0, 1.0))
top = D(top, place(enc, ZP))

# ---- vents: straight grooves across the top + a band that follows the shell around the side edge and down the wall
def edge_band(depth=0.9, fade=2.0, z_end=11.0, probe_x=-40.0):
    """Cutter profile in (y,z): a constant-depth channel following the shell's own surface from the flat top,
    around the side edge and down the sloped wall, fading out over the last `fade` mm (like the real 1541)."""
    t = src["top"]
    pts = []
    for y in np.arange(24.0, 30.4, 0.04):                      # over the flat top and the edge round-over
        h = np.atleast_2d(t.ray.intersects_location([[probe_x, y, 40]], [[0, 0, -1]])[0])
        if h.size and h[:, 2].max() > 13.5:
            pts.append((y, h[:, 2].max()))
    for z in np.arange(pts[-1][1] - 0.04, z_end, -0.04):        # down the side wall
        h = np.atleast_2d(t.ray.intersects_location([[probe_x, 60, z]], [[0, -1, 0]])[0])
        if h.size:
            pts.append((max(h[:, 1]), z))
    pts = np.array(pts)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    tang = np.gradient(pts, axis=0); tang /= np.linalg.norm(tang, axis=1)[:, None]
    norm = np.column_stack([-tang[:, 1], tang[:, 0]])           # outward normal
    d = depth * np.clip((s[-1] - s) / fade, 0, 1)               # fade out at the far end
    inner = pts - norm * d[:, None]
    outer = pts + norm * 2.0
    return Polygon(np.vstack([outer, inner[::-1]]))


band2d = edge_band()
grooves = []
for k in range(VENT_N):
    gx = VENT_X0 + k * VENT_PITCH
    grooves.append(BOX([gx, -VENT_Y, 16.6], [gx + VENT_W, VENT_Y, 18.5]))
    b = prism_x(band2d, gx, gx + VENT_W)
    grooves += [b, xformed(b, MIRROR_Y)]
grooves = U(grooves)

slot = through(negative(tgt["lid"], [24.0, -12.25, 26.0], [32.0, 7.25, 28.0]), (0, 0, 1.0))
slot = U([place(slot, ZP), place(BOX([24.5, -11.75, 18.0], [31.5, 6.75, 34.5]))])
sb = slot.bounds
grooves_bay = D(grooves, BOX([sb[0][0] - 1.5, sb[0][1] - 1.5, 15], [sb[1][0] + 1.5, 40, 20]))
top_slot = D(D(top, grooves_bay), slot)
BOARD_YC = (28.31 - BACKOFF) - 15.0
rear_win = BOX([-60.0, BOARD_YC - 9.25, WIN_Z[0]], [-46.0, BOARD_YC + 9.25, WIN_Z[1]])
top_noslot = D(D(top, grooves), rear_win)

# ================================================================ button nubs (pushed in from the inside)
WALL_Y, PROUD = 1.51, 1.2
nubs = {}
for tag, body in NUB_BODIES.items():
    flange = trimesh.creation.cylinder(radius=NUB_FLANGE_R, height=body, sections=64)
    flange.apply_translation([0, 0, body / 2])
    sh = WALL_Y + PROUD - NUB_STEM_R + 0.2
    stem = trimesh.creation.cylinder(radius=NUB_STEM_R, height=sh, sections=64)
    stem.apply_translation([0, 0, body + sh / 2 - 0.1])
    dome = trimesh.creation.icosphere(subdivisions=3, radius=NUB_STEM_R)
    dome.apply_translation([0, 0, body + WALL_Y + PROUD - NUB_STEM_R])
    nubs[f"button_nub_{tag}"] = U([flange, stem, dome])
    print(f"nub {tag:7s}: total {nubs[f'button_nub_{tag}'].bounds[1][2]:.2f} mm "
          f"(flange {body} + wall {WALL_Y} + {PROUD} proud)")

print(f"\nboard raised {RAISE} mm, moved {BACKOFF} mm off the right wall; tunnel depth {16.0 - (26.0 + DZ):.1f} mm; "
      f"button axis z={BTN_Z:.2f}; rear window z {WIN_Z}")
export({"bottom": bot, "top_slot": top_slot, "top_noslot": top_noslot}, PREFIX, S)
for name, m in nubs.items():
    path = os.path.join(ROOT, "output", f"{PREFIX}_{name}.stl"); m.export(path)
    r = trimesh.load(path); assert r.is_watertight and r.is_winding_consistent
    print(f"-> {path}")
internals.export(os.path.join(S, "rot_internals.stl"))



