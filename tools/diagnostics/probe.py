import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
src = load_source(); tgt = load_target()
b = tgt["bottom"]
for x, y in [(-30, -14.25), (28, 8.75)]:
    loc, _, _ = b.ray.intersects_location([[x, y, 40]], [[0, 0, -1]])
    loc2, _, _ = b.ray.intersects_location([[x + 1.8, y, 40]], [[0, 0, -1]])
    print(f"target post ({x},{y}): pin top z={loc[:,2].max():.2f}; post shoulder z={loc2[:,2].max():.2f}")
# corner post outer radius in source bottom around (-52.05,-26.55): probe rays toward the post from inside at z=-12
c = np.array([-52.05, -26.55, -12.0])
for ang in [0, 45, 90]:
    d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang)), 0])
    loc, _, _ = src["bottom"].ray.intersects_location([c + d * 10], [-d])
    r = sorted(np.linalg.norm(loc[:, :2] - c[:2], axis=1))
    print(f"source corner post, direction {ang} deg: surfaces at r = {np.round(r,2)}")
# top-shell corner boss: how low does it hang?
loc, _, _ = src["top"].ray.intersects_location([[-52.05 + 2.2, -26.55, -5]], [[0, 0, 1]])
print("top shell corner boss bottom z (just outside hole):", np.round(sorted(loc[:, 2]), 2))
# Zero board corner vs post: board corner arc centre
bc = np.array([-49.08 + 3, -28.31 + 3])
print("board corner arc centre to post centre:", round(float(np.linalg.norm(bc - c[:2])), 2), "-> edge clearance = that - 3 - post_r")
