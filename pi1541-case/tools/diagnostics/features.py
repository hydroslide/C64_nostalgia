import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from shapely.geometry import Polygon

src = load_source(); tgt = load_target()
for k, m in src.items(): print("source", k, np.round(m.bounds, 2).tolist())
for k, m in tgt.items(): print("target", k, np.round(m.bounds, 2).tolist())

def holes(mesh, origin, normal, label, minarea=0.5):
    polys, keep = section_polys(mesh, origin, normal)
    ax = "xyz"
    print(f"\n== {label}: section at {origin} normal {normal}; 2D axes = {ax[keep[0]]},{ax[keep[1]]}")
    for p in polys:
        print("  material:", describe(p))
        for h in p.interiors:
            hp = Polygon(h)
            if hp.area > minarea: print("     hole:", describe(hp))
    return polys

# ---- target features
holes(tgt["bottom"], [0, 0, 3.5], [0, 0, 1], "TARGET bottom plan z=3.5 (posts)")
holes(tgt["bottom"], [0, 0, 6.5], [0, 0, 1], "TARGET bottom plan z=6.5 (pins?)")
holes(tgt["bottom"], [0, -18.75, 0], [0, 1, 0], "TARGET bottom front wall y=-18.75")
holes(tgt["lid"], [0, -18.75, 0], [0, 1, 0], "TARGET lid front wall y=-18.75")
holes(tgt["bottom"], [-34.3, 0, 0], [1, 0, 0], "TARGET bottom -X wall")
holes(tgt["lid"], [0, 0, 27], [0, 0, 1], "TARGET lid plate z=27")
holes(tgt["lid"], [0, 0, 26.2], [0, 0, 1], "TARGET lid plate z=26.2 (inner side)")
holes(tgt["lid"], [0, 0, 22], [0, 0, 1], "TARGET lid internals z=22")
# ---- source features
holes(src["bottom"], [0, 0, -10], [0, 0, 1], "SOURCE bottom plan z=-10")
holes(src["bottom"], [0, 0, -15.8], [0, 0, 1], "SOURCE bottom plan z=-15.8 (just above floor)")
holes(src["bottom"], [0, 0, -16.8], [0, 0, 1], "SOURCE bottom floor z=-16.8")
holes(src["top"], [0, 0, 10], [0, 0, 1], "SOURCE top plan z=10")
holes(src["top"], [0, 0, 16.8], [0, 0, 1], "SOURCE top plate z=16.8")
