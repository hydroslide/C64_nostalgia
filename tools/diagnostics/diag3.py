import trimesh, numpy as np, os
S = r"C:\Users\rscanlon\AppData\Local\Temp\claude\h--My-Drive-3D-printing-STLs-C64\daf08743-8a9b-4f9d-b7c1-5ea3871daa8f\scratchpad"
DX, DY, DZ = -15.08, -10.56, -18.0
bot = trimesh.load(os.path.join(S, "zup_bottom.stl")); top = trimesh.load(os.path.join(S, "zup_top_noslot.stl"))
for name, m, x, z in [("hdmi", bot, -21.1 + DX, 8.8 + DZ), ("usb1", bot, 7.9 + DX, 8.3 + DZ), ("pwr", bot, 20.5 + DX, 8.3 + DZ),
                      ("btn1", top, -22.5 + DX, 21.5 + DZ), ("btn3", top, -1 + DX, 21.5 + DZ)]:
    h = m.ray.intersects_location([[x, -45, z]], [[0, 1, 0]])[0]
    print(name, "x=%.2f z=%.2f" % (x, z), "hits y:", np.round(sorted(h[:, 1]), 2)[:6])
