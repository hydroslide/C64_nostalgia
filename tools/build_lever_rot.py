"""Rotating 1541 door lever (alt bezel), 3 printed parts:
  1. bezel: slot moved down 2.5 mm (real-1541 proportions + room for a pivot), pivot hole, detent ring on the back
  2. lever front: knob + arm, D socket in the knob back
  3. lever back: hub + shaft (round through the bezel, D tip into the knob socket) + curved leaf spring with a bump
The spring bump rides on the inside of the ring: clicks into a notch at horizontal (0 deg) and straight down (-90 deg),
drags on the ring in between (tension). Each notch has one steep wall = hard stop against over-travel.
Frame: Z-up source frame, bezel face at x=58 (normal +X). Face-view angles: 0 = pointing right (+Y), -90 = down (-Z).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from ops import *
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union

S = WORK
OUT = os.path.join(ROOT, "output")
FACE, BACK = 58.0, 53.5
SLOT_DZ = -2.5                     # new slot: z -3.0..-2.0
Y0, Z0 = -11.2, 0.4                # pivot (knob centre)
KNOB_R, KNOB_FRONT = 2.0, FACE + 3.55
ARM_LEN, ARM_HALF, ARM_FRONT = 9.0, 1.0, FACE + 2.35
LEV_BACK = FACE + 0.05             # lever front piece bears on the face
SHAFT_R, HOLE_R = 1.5, 1.7
D_FLAT = 1.0                       # D flat at 1.0 from the axis, on the lever's "up" side (+Z at 0 deg)
SOCK_R, SOCK_FLAT, SOCK_END = 1.55, 1.05, FACE + 2.55
CAM_X0, CAM_X1 = 51.8, BACK - 0.1  # hub/spring layer behind the bezel
RING_X0 = 51.8
HUB_R = 2.0
SPR_R0, SPR_R1, SPR_FROM, SPR_TO = 2.8, 3.6, -45.0, 105.0   # leaf spring arc (lever frame at 0 deg)
BUMP_A, BUMP_TIP, BUMP_W = -45.0, 4.75, 0.9                  # bump at the spring's free end
R_IN, R_OUT, NOTCH_R = 4.1, 5.1, 4.6                        # detent ring; notch floor 0.15 below the bump tip
NOTCH_A, NOTCH_B = -45.0, -135.0                            # bump positions at 0 deg and -90 deg


def P(r, a, y0=Y0, z0=Z0):
    a = np.radians(a); return (y0 + r * np.cos(a), z0 + r * np.sin(a))


def arc_poly(r0, r1, a0, a1, n=64):
    t = np.linspace(a0, a1, n)
    return Polygon([P(r1, a) for a in t] + [P(r0, a) for a in t[::-1]])


def prism_yz(poly, x0, x1):
    if poly.geom_type == "MultiPolygon":
        return U([prism_yz(g, x0, x1) for g in poly.geoms])
    m = trimesh.creation.extrude_polygon(poly, x1 - x0)
    M = np.eye(4); M[:3, :3] = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]; M[:3, 3] = [x0, 0, 0]
    m.apply_transform(M); return m


def beveled(poly, x0, x1, bevel):
    return U([prism_yz(poly, x0, x1 - bevel), prism_yz(poly.buffer(-bevel, resolution=32), x1 - bevel - EPS, x1)])


def dshape(r, flat):
    return Point(Y0, Z0).buffer(r, resolution=64).intersection(sbox(Y0 - 5, Z0 - 5, Y0 + 5, Z0 + flat))


def bump2d(chamfer=0.12):
    """Flat-sided bump (straight radial flanks = true stop against a notch's steep wall), tip corners chamfered."""
    a = np.radians(BUMP_A); u = np.array([np.cos(a), np.sin(a)]); v = np.array([-u[1], u[0]]); c = np.array([Y0, Z0])
    h = BUMP_W / 2
    pts = [(SPR_R1 - 0.2, -h), (BUMP_TIP - chamfer, -h), (BUMP_TIP, -h + chamfer), (BUMP_TIP, h - chamfer),
           (BUMP_TIP - chamfer, h), (SPR_R1 - 0.2, h)]
    return Polygon([tuple(c + r * u + s * v) for r, s in pts])


def rot_x(m, deg):
    """Rotate about the pivot axis; +deg = counter-clockwise in the face view."""
    T = trimesh.transformations.rotation_matrix(np.radians(deg), [1, 0, 0], [0, Y0, Z0])
    return xformed(m, T)


# ------------------------------------------------------------------ 1. bezel
orig = load_source()["front"]
bez = D(orig, BOX([FACE, -7.0, 0.55], [FACE + 3.0, 7.0, 3.5]))            # remove the centred pull-lip
bez = U([bez, BOX([56.4, -6.55, 0.95], [FACE, -6.15, 2.2]), BOX([56.4, 6.15, 0.95], [FACE, 6.55, 2.2])])   # fill the lip's flex slits
nolip = bez
bez = U([bez,                                                             # fill the old slot (+ its lip round-overs)
         BOX([55.9, -20.5, -1.05], [FACE, -6.2, 1.05]), BOX([55.9, 6.2, -1.05], [FACE, 20.5, 1.05]),
         BOX([55.9, -6.2, -0.55], [56.5, 6.2, 0.55])])
slot = moved(negative(nolip, [55.8, -21.0, -1.1], [FACE + 0.3, 21.0, 1.1]), dz=SLOT_DZ)
bez = D(bez, slot)                                                        # same slot profile, 2.5 mm lower
bez = D(bez, prism_yz(Point(Y0, Z0).buffer(HOLE_R, resolution=64), BACK - 1, FACE + 1))   # pivot hole


def notch(a, side):
    """side=+1: steep wall on the +angle side (stop), ramp towards -angle; side=-1 mirrored."""
    steep, flat_end, ramp_end = a + side * 7.5, a - side * 5.0, a - side * 22.0
    floor = [P(NOTCH_R, t) for t in np.linspace(steep, flat_end, 12)]
    return Polygon([P(R_IN - 0.3, steep)] + floor + [P(R_IN, ramp_end), P(R_IN - 0.3, ramp_end)]).buffer(0)


ring2d = arc_poly(R_IN, R_OUT, -170, -10).difference(notch(NOTCH_A, +1)).difference(notch(NOTCH_B, -1))
bez = U([bez, prism_yz(ring2d, RING_X0, BACK + EPS)])
bez = clean(bez)

# ------------------------------------------------------------------ 2. lever front (knob + arm), at 0 deg
knob2d = Point(Y0, Z0).buffer(KNOB_R, resolution=64)
arm2d = LineString([(Y0, Z0), (Y0 + ARM_LEN, Z0)]).buffer(ARM_HALF, cap_style=2).buffer(-0.2).buffer(0.2, resolution=16)
front = U([beveled(arm2d, LEV_BACK, ARM_FRONT, 0.3), beveled(knob2d, LEV_BACK, KNOB_FRONT, 0.4)])
front = D(front, prism_yz(dshape(SOCK_R, SOCK_FLAT), LEV_BACK - 0.1, SOCK_END))

# ------------------------------------------------------------------ 3. lever back (hub + spring + shaft), at 0 deg
spring2d = unary_union([
    arc_poly(SPR_R0, SPR_R1, SPR_FROM, SPR_TO),
    Polygon([P(HUB_R - 0.2, SPR_TO - 7), P(SPR_R0 + 0.1, SPR_TO - 7), P(SPR_R0 + 0.1, SPR_TO), P(HUB_R - 0.2, SPR_TO)]),  # root spoke
    bump2d(),                                                                                                             # bump
])
hub2d = Point(Y0, Z0).buffer(HUB_R, resolution=64)
back = U([prism_yz(unary_union([hub2d, spring2d]), CAM_X0, CAM_X1),
          prism_yz(Point(Y0, Z0).buffer(SHAFT_R, resolution=64), CAM_X1 - EPS, LEV_BACK + 0.05),
          prism_yz(dshape(SHAFT_R, D_FLAT), LEV_BACK, SOCK_END - 0.05)])

for name, m in [("bezel", bez), ("lever front", front), ("lever back", back)]:
    print(f"{name:12s} watertight={m.is_watertight} volume={m.volume:.1f} bounds={np.round(m.bounds, 2).tolist()}")

# ------------------------------------------------------------------ checks
bump3d = prism_yz(bump2d(), CAM_X0, CAM_X1)
back_nobump = prism_yz(unary_union([hub2d, arc_poly(SPR_R0, SPR_R1, SPR_FROM, SPR_TO - 7)]), CAM_X0, CAM_X1)
print("\n== detent: bump (undeflected) overlap with the ring -> spring deflection needed")
for th in [5, 2, 0, -20, -45, -70, -90, -92, -95]:
    b = rot_x(bump3d, th)
    ov = I(b, bez).volume
    # radial deflection needed = how far the bump tip sits beyond the ring surface along the bump axis
    a = BUMP_A + th
    rs = np.linspace(R_IN - 0.5, BUMP_TIP, 200)
    inside = [r for r in rs if bez.contains([[52.6, *P(r, a)]])[0]]
    need = BUMP_TIP - min(inside) if inside else 0.0
    print(f"   lever {th:4d} deg: overlap {ov:6.3f} mm3, radial deflection {need:.2f} mm")
print("== sweep clearance (should all be 0)")
worst = {"front piece vs bezel": 0, "back piece (no bump) vs bezel": 0}
for th in np.arange(0, -91, -10):
    worst["front piece vs bezel"] = max(worst["front piece vs bezel"], I(rot_x(front, th), bez).volume)
    worst["back piece (no bump) vs bezel"] = max(worst["back piece (no bump) vs bezel"],
                                                I(U([rot_x(back_nobump, th), rot_x(prism_yz(Point(Y0, Z0).buffer(SHAFT_R), CAM_X1, LEV_BACK), th)]), bez).volume)
for k, v in worst.items():
    print(f"   {k}: {v:.3f} mm3")
case = {}
for tag in ["pi1541_zero_case", "pi1541_zero_rot_case"]:
    for n in ["bottom", "top_noslot"]:
        p = os.path.join(S, f"zup_{tag}_{n}.stl")
        if os.path.exists(p):
            case[f"{tag}_{n}"] = trimesh.load(p)
case["original_bottom"] = load_source()["bottom"]; case["original_top"] = load_source()["top"]
sweep = U([rot_x(back, th) for th in np.arange(0, -91, -15)] + [rot_x(front, th) for th in np.arange(0, -91, -15)])
for k, m in case.items():
    print(f"   mechanism sweep vs {k}: {I(sweep, m).volume:.3f} mm3 ; alt bezel vs {k}: {I(bez, m).volume:.3f} mm3")

# ------------------------------------------------------------------ export: print orientation + assembled preview
FACE_DOWN = np.array([[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, 0], [0, 0, 0, 1]], float)   # x -> -z : face on the bed
BACK_DOWN = np.array([[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]], float)   # x -> +z : back on the bed


def to_bed(m, T):
    m = xformed(m, T); c = m.bounds
    m.apply_translation([-(c[0][0] + c[1][0]) / 2, -(c[0][1] + c[1][1]) / 2, -c[0][2]]); return m


files = {"front_1541lever_rotating_bezel": to_bed(bez, FACE_DOWN),
         "front_1541lever_rotating_lever_front": to_bed(front, BACK_DOWN),
         "front_1541lever_rotating_lever_back": to_bed(back, BACK_DOWN)}
for n, m in files.items():
    path = os.path.join(OUT, f"pi1541_zero_case_{n}.stl"); m.export(path)
    r = trimesh.load(path); assert r.is_watertight and r.is_winding_consistent, path
    print(f"-> {path}  (print-ready, {np.round(r.extents, 2).tolist()} mm)")
asm = trimesh.util.concatenate([bez, front, back]); asm.apply_transform(TO_YUP)
asm.export(os.path.join(OUT, "pi1541_zero_case_front_1541lever_rotating_ASSEMBLED_preview.stl"))
for n, m in [("bez", bez), ("front", front), ("back", back)]:
    m.export(os.path.join(S, f"lev_{n}.stl"))




