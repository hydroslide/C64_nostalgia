import trimesh, os, glob, numpy as np
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
for f in sorted(glob.glob(os.path.join(S, "zup_pi1541_zero*_case_*.stl"))):
    m = trimesh.load(f)
    bodies = m.split(only_watertight=False)
    print(f"{os.path.basename(f):45s} watertight={m.is_watertight} winding={m.is_winding_consistent} is_volume={m.is_volume} vol={m.volume:.0f} bodies={[round(b.volume,1) for b in bodies]}")
