"""Front bezel (drive door insert) with a 1541-style door lever: round pivot knob at the left end of the disk slot and a
straight arm running right, above the slot (per straight-on photo). The original centred pull-lip above the door recess is removed.
Z-up source frame: face at x=58 (normal +X), slot at z -0.5..0.5, viewer's left = -Y. LED hole (y=-14.5) kept.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from ops import *
from shapely.geometry import Point
from shapely.ops import unary_union

S = WORK
FACE = 58.0
# proportions taken from a straight-on photo of a real 1541: lever sits ABOVE the slot, knob ~25% in from the left,
# arm is a straight horizontal bar ~2/3 the knob diameter, squared tip, ending where the door's raised block begins
KNOB_Y, KNOB_Z, KNOB_R = -11.2, 2.2, 1.6   # fits between the slot top (z=0.5) and the bezel top edge (z=4.1)
TIP_Y, ARM_Z0, ARM_Z1 = -2.2, 0.75, 2.65  # arm: horizontal bar from the knob to TIP_Y, bottom just above the slot
ARM_TOP, KNOB_TOP, BEVEL = FACE + 2.1, FACE + 2.8, 0.3


def prism_yz(poly, x0, x1):
    """Extrude a (y,z) polygon along +X from x0 to x1."""
    m = trimesh.creation.extrude_polygon(poly, x1 - x0)
    M = np.eye(4); M[:3, :3] = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]; M[:3, 3] = [x0, 0, 0]
    m.apply_transform(M)
    return m


def beveled(poly, x0, x1, bevel):
    """Prism with a stepped bevel on its outer edge (outer 'bevel' mm inset by 'bevel')."""
    return U([prism_yz(poly, x0, x1 - bevel), prism_yz(poly.buffer(-bevel, resolution=32), x1 - bevel - EPS, x1)])


bez = load_source()["front"]
# 1. remove the centred pull-lip that sticks out above the door recess (y -6.2..6.2, x > 58)
bez = D(bez, BOX([FACE, -7.0, 0.55], [FACE + 3.0, 7.0, 3.5]))
bez = U([bez, BOX([56.4, -6.55, 0.95], [FACE, -6.15, 2.2]), BOX([56.4, 6.15, 0.95], [FACE, 6.55, 2.2])])   # fill the lip's flex slits
# 2. lever: horizontal arm + knob
from shapely.geometry import LineString
arm = LineString([(KNOB_Y, (ARM_Z0 + ARM_Z1) / 2), (TIP_Y, (ARM_Z0 + ARM_Z1) / 2)]).buffer((ARM_Z1 - ARM_Z0) / 2, cap_style=2).buffer(-0.2).buffer(0.2, resolution=16)
knob = Point(KNOB_Y, KNOB_Z).buffer(KNOB_R, resolution=64)
lever = U([beveled(arm, FACE - 0.1, ARM_TOP, BEVEL), beveled(knob, FACE - 0.1, KNOB_TOP, BEVEL)])
bez = U([bez, lever])
bez = clean(bez)
print("bezel: watertight", bez.is_watertight, "volume", round(bez.volume, 1), "bounds", np.round(bez.bounds, 2).tolist())
bez.export(os.path.join(S, "zup_bezel_lever.stl"))
out = os.path.join(ROOT, "output", "pi1541_zero_case_front_1541lever.stl")
e = bez.copy(); e.apply_transform(TO_YUP); e.export(out)
r = trimesh.load(out); assert r.is_watertight and r.is_winding_consistent
print("->", out)
# clearance: lever vs case parts (the lever must not touch the case)
src = load_source()
for n in ["top", "bottom"]:
    print(f"lever âˆ© original {n}: {I(lever, src[n]).volume:.3f} mm3")




