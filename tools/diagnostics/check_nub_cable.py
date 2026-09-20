import sys, os
P = r"H:\My Drive\3D printing\STLs\C64"
sys.path.insert(0, os.path.join(P, "tools"))
from common import *
from ops import U, D, I, BOX
import numpy as np, trimesh
# nub geometry checks
for tag in ["short", "medium", "long"]:
    m = trimesh.load(os.path.join(P, "output", f"pi1541_zero_rot_case_button_nub_{tag}.stl"))
    b = m.bounds
    # stem diameter near the tip, collar diameter near the base, bore depth
    sec = m.section(plane_origin=[0, 0, b[1][2] - 1.5], plane_normal=[0, 0, 1])
    stem_d = 2 * max(np.linalg.norm(v[:2]) for v in sec.vertices) if sec else None
    sec2 = m.section(plane_origin=[0, 0, 1.0], plane_normal=[0, 0, 1])
    coll_d = 2 * max(np.linalg.norm(v[:2]) for v in sec2.vertices)
    bore = [round(z, 2) for z in np.arange(0, 3.5, 0.05) if not m.contains([[0, 0, z]])[0]]
    print(f"{tag:7s}: total {b[1][2]:.2f}, collar d={coll_d:.2f}, stem d={stem_d:.2f}, bore open 0..{max(bore):.2f}, watertight={m.is_watertight}")
# hole vs stem
print("wall hole dia 4.2 -> stem clearance 0.10 mm per side; collar 6.5 cannot pass")
# DIN cable path: straight shot from inside the channel out through the rear window?
tn = trimesh.load(os.path.join(P, "work", "zup_pi1541_zero_rot_case_top_noslot.stl"))
print("\nDIN cable path (no-slot top): rays from inside the channel toward the rear")
for z in [5.5, 7, 9, 11.5]:
    for y in [3, 9.8, 17]:
        h = np.atleast_2d(tn.ray.intersects_location([[-43.0, y, z]], [[-1, 0, 0]])[0])
        blocked = [round(float(v), 1) for v in sorted(h[:, 0], reverse=True)] if h.size else []
        print(f"   z={z:4.1f} y={y:4.1f}: obstacles at x={blocked}  -> {'CLEAR' if not blocked else 'blocked'}")
print("\nchannel interior and window:")
print("   channel walls x -48.6..-46.6 (rear) and -39.6..-37.6; window x -60..-46, y 0.56..19.06, z 5.0..12.0")
