"""rev-4 side-entry nubs: prove the board can be dropped straight down onto them.

Nub local frame: +z is outboard (out through the wall), z=0 is the original cup mouth, the board side is z<0, and
the cup's open side faces +x. In the case that maps to: local z -> world +y, local x -> world -z, i.e. the opening
looks at the case FLOOR. Installing the board moves each switch along -x, purely radially, so both the plunger and
the switch BODY have to sweep in from +x without touching nub material. That is what this checks.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
from common import ROOT, OUTPUT
from ops import U, I, BOX

WALL_IN_Y, SW_FACE_Y = 29.05, 26.81            # right wall inner face / switch body front face (dbg_sw.py)
COLLAR_L, BORE_R, BORE_DEEP = 3.0, 1.9, 2.5
SWITCH_W, PLUNGER_D, HOLE_R = 6.4, 3.5, 2.1
OVERLAP = COLLAR_L - (WALL_IN_Y - SW_FACE_Y)   # how far the cup mouth reached past the body face before rev 4
MOUTH_RELIEF = OVERLAP + 0.35                  # must match build_rot.py
SW, FAR = SWITCH_W / 2, 14.0                   # FAR: start each sweep well clear of the nub
TOL = 0.01
fails = []


def check(cond, msg):
    print(f"  {'OK  ' if cond else 'FAIL'}  {msg}")
    if not cond:
        fails.append(msg)


def report(tag):
    path = os.path.join(OUTPUT, f"pi1541_zero_rot_case_button_nub_{tag}.stl")
    m = trimesh.load(path)
    print()
    print(f"=== {tag} ===  watertight={m.is_watertight}  volume={m.volume:.2f} mm3")
    check(m.is_watertight and m.is_winding_consistent, "closed solid")

    # 1. the switch BODY sweeping in: 6.4 mm square section, everything on the board side of its front face
    v = I(BOX([-SW, -SW, -6.0], [SW + FAR, SW, OVERLAP]), m).volume
    check(v < TOL, f"switch body ({SWITCH_W} mm sq) sweeps in clear       clash {v:6.3f} mm3")

    # 2. the round plunger sweeping in, at the shallowest and deepest seatings the channel can hold
    r = PLUNGER_D / 2
    for lbl, z0 in [("shallowest", MOUTH_RELIEF + 0.05), ("deepest   ", BORE_DEEP - 0.45)]:
        z1 = BORE_DEEP - 0.05
        cyl = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=96,
                                        transform=trimesh.transformations.translation_matrix([0, 0, (z0 + z1) / 2]))
        v = I(U([cyl, BOX([0.0, -r, z0], [FAR, r, z1])]), m).volume
        check(v < TOL, f"plunger ({PLUNGER_D} dia) sweeps in clear, {lbl} clash {v:6.3f} mm3")

    # 3. the collar must still bear on the wall and not pull back through the 4.2 mm hole
    sec = m.section(plane_origin=[0, 0, COLLAR_L - 0.15], plane_normal=[0, 0, 1])
    span = sec.vertices[:, 1].max() - sec.vertices[:, 1].min() if sec is not None else 0.0
    check(span > HOLE_R * 2 + 0.5, f"collar spans {span:.2f} mm across the {HOLE_R * 2:.1f} mm hole")

    # 4. lips either side of the channel must remain, or the plunger would fall straight back out
    for z in [MOUTH_RELIEF + 0.15, (MOUTH_RELIEF + BORE_DEEP) / 2, BORE_DEEP - 0.3]:
        v = I(m, BOX([0.0, -SW, z - 0.05], [4.0, SW, z + 0.05])).volume
        check(v > 0.05, f"lips still hold the plunger at z={z:.2f}           {v:6.3f} mm3")


print(f"cup mouth used to reach {OVERLAP:.2f} mm past the switch body face; rev 4 cuts it back {MOUTH_RELIEF:.2f} mm")
for t in ["short", "medium", "long"]:
    report(t)
print()
print("ALL CHECKS PASSED" if not fails else f"{len(fails)} FAILED: " + "; ".join(fails))
sys.exit(1 if fails else 0)
