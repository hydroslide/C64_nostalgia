import glob, os, struct
import numpy as np
import trimesh

ROOT = r"H:\My Drive\3D printing\STLs\C64"
files = sorted(glob.glob(os.path.join(ROOT, "real_files", "*", "*.stl")))

for f in files:
    with open(f, "rb") as fh:
        header = fh.read(80)
        n = struct.unpack("<I", fh.read(4))[0]
        raw = np.frombuffer(fh.read(), dtype=np.dtype([("n", "<3f4"), ("v", "<3f4", (3,)), ("attr", "<u2")]))
    m = trimesh.load(f)
    print("=" * 90)
    print(os.path.relpath(f, ROOT))
    print(" header:", header.rstrip(b" \x00")[:60], " tris(header)=", n, " tris(body)=", len(raw),
          " size ok:", os.path.getsize(f) == 84 + 50 * n)
    print(" attr bytes nonzero:", int((raw["attr"] != 0).sum()), " unique:", np.unique(raw["attr"])[:8])
    print(" verts:", len(m.vertices), " faces:", len(m.faces))
    print(" bounds min:", np.round(m.bounds[0], 3), " max:", np.round(m.bounds[1], 3))
    print(" extents (mm):", np.round(m.extents, 3))
    print(" watertight:", m.is_watertight, " winding consistent:", m.is_winding_consistent,
          " volume:", round(m.volume, 1) if m.is_watertight else "n/a", " area:", round(m.area, 1))
    parts = m.split(only_watertight=False)
    print(" connected bodies:", len(parts))
    for i, p in enumerate(sorted(parts, key=lambda p: -len(p.faces))[:8]):
        print(f"   body {i}: faces={len(p.faces)} extents={np.round(p.extents,2)} min={np.round(p.bounds[0],2)}")
    # stored normals vs computed
    comp = m.face_normals
    stored = raw["n"].astype(float)
    ok = np.linalg.norm(stored, axis=1) > 0.5
    print(" stored normals nonzero:", int(ok.sum()), "/", len(stored))
    # dominant planes: area-weighted normal directions
    fn = np.round(comp, 3)
    axes = {"+X": (1, 0, 0), "-X": (-1, 0, 0), "+Y": (0, 1, 0), "-Y": (0, -1, 0), "+Z": (0, 0, 1), "-Z": (0, 0, -1)}
    tot = m.area_faces.sum()
    s = []
    for k, a in axes.items():
        mask = (comp @ np.array(a)) > 0.999
        s.append(f"{k}:{m.area_faces[mask].sum()/tot*100:.0f}%")
    print(" axis-aligned face area:", " ".join(s))
    # distinct Z levels of horizontal faces (useful for layered/extruded designs)
    horiz = np.abs(comp[:, 2]) > 0.999
    zs = np.round(m.triangles_center[horiz][:, 2], 2)
    zv, zc = np.unique(zs, return_counts=True)
    areas = [m.area_faces[horiz][zs == z].sum() for z in zv]
    print(" horizontal-face Z levels (z: area mm2):", ", ".join(f"{z}:{a:.0f}" for z, a in zip(zv, areas) if a > 5))
