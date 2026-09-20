import sys, os
sys.path.insert(0, r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad")
from common import *
from ops import *
t = load_source()["top"]
g = negative(t, [-27.6, 4.0, 16.3], [-1.95, 27.0, 17.45])
print("groove negative volume", round(g.volume, 1), "bodies", len(g.split(only_watertight=False)), "bounds", np.round(g.bounds, 2).tolist())
print("expected approx: 10 grooves x ~1.2 wide x 23 long x 0.85 deep =", 10 * 1.2 * 23 * 0.85)
b = BOX([-27.6, 4.0, 16.3], [-1.95, 27.0, 17.45])
print("box volume", round(b.volume, 1), " box∩top", round(I(b, t).volume, 1))
