#!/usr/bin/env python3
"""Rebuild the original disks from selections.json.

    python3 build.py [--only D05-1] [--out out/]

Needs VICE's `c1541` and `petcat` on PATH (macOS: `brew install vice`;
Debian/Raspberry Pi OS: `apt install vice`).

For each disk side in selections.json:
  * items with "whole_image" are copied out as their own image
    (multi-load games that need a full disk);
  * every other item is extracted from its source image and written onto a
    fresh .d64 named after the label; if the side is a menu disk (or has
    more than one game and --auto-menu is on) a BASIC "MENU" program is
    written first so LOAD"MENU",8,1 / RUN works like the originals.
A manifest.json maps every built image back to the catalog disk/side.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from cbmimage import open_image

HERE = Path(__file__).resolve().parent
DISK_BLOCKS = 664


def load_image_bytes(src: str, member: str | None) -> bytes:
    data = Path(src).read_bytes()
    if not member:
        return data
    parts = member.split("::")
    for part in parts:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            data = z.read(part)
    return data


def c64_name(s: str) -> str:
    """Lowercase ASCII becomes normal PETSCII capitals in c1541/petcat."""
    s = re.sub(r"[^a-z0-9 .\-!']", "", s.lower().replace("&", "and"))
    return s[:16].strip() or "untitled"


def safe_filename(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", s).strip()[:120]


def need(tool: str):
    if not shutil.which(tool):
        sys.exit(f"'{tool}' not found - install VICE (brew install vice / apt install vice)")


def menu_basic(title: str, games: list[tuple[str, str, str]]) -> str:
    """games = [(label, filename, start_cmd)]. Returns petcat -w2 source (lowercase)."""
    t = c64_name(title)[:30]
    lines = [
        '10 poke53280,6:poke53281,0:print chr$(147)chr$(158)',
        f'20 print "{{down}}   {t}":print"   " ;:fori=1to{min(len(t), 30)}:print"{{CBM-T}}";:next:print',
        f'30 n={len(games)}:dim t$(n),f$(n),s$(n)',
        '40 fori=1ton:readt$(i),f$(i),s$(i)',
        '50 printchr$(5)"   "chr$(64+i)chr$(158)"  "t$(i):next',
        '60 print:printchr$(154)"   press a letter"',
        '70 getk$:ifk$=""then70',
        '80 k=asc(k$)-64:ifk<1ork>nthen70',
        # classic keyboard-buffer trick: LOAD on row 0, start command on row 4
        # (rows 1-3 get SEARCHING / LOADING / READY.), two RETURNs queued.
        '90 printchr$(147)chr$(5)"load"chr$(34)f$(k)chr$(34)",8,1":print:print:print',
        '100 prints$(k):printchr$(19);:poke631,13:poke632,13:poke198,2:end',
    ]
    ln = 1000
    for label, fname, start in games:
        lab = c64_name(label)[:30]
        lines.append(f'{ln} data "{lab}","{fname}","{start}"')
        ln += 10
    return "\n".join(lines) + "\n"


def run(cmd: list[str]):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{r.stdout}{r.stderr}")
    return r.stdout


def build_side(sid: str, entry: dict, out: Path, auto_menu: bool, manifest: list, cache: dict):
    labels = entry.get("disk_name") or sid
    file_items, whole = [], []
    for it in entry["items"]:
        if it.get("skip"):
            continue
        if "whole_image" in it:
            whole.append(it)
        elif "src" in it:
            file_items.append(it)
        else:
            print(f"  - {sid}: '{it['title']}' has no source, skipped")

    for it in whole:
        w = it["whole_image"]
        data = load_image_bytes(w["src"], w.get("member"))
        fmt = open_image(data).fmt
        name = safe_filename(f"{sid} {it['title']}.{fmt}")
        (out / name).write_bytes(data)
        manifest.append({"side": sid, "title": it["title"], "image": name, "kind": "whole_image",
                         "from": w["src"] + (f"::{w['member']}" if w.get("member") else "")})
        print(f"  + {name}  (copied whole image)")

    if not file_items:
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        games, used, written = [], set(), []
        for it in file_items:
            key = (it["src"], it.get("member"))
            if key not in cache:
                cache[key] = open_image(load_image_bytes(it["src"], it.get("member")))
            img = cache[key]
            ent = next((e for e in img.entries if e.name == it["file"]), None)
            if ent is None:
                print(f"  ! {sid}: '{it['file']}' not in {it['src']}")
                continue
            data = img.read_file(ent)
            fname = c64_name(it.get("as") or it["title"])
            while fname in used:
                fname = fname[:14] + str(len(used))
            used.add(fname)
            host = tmp / f"f{len(written)}.prg"
            host.write_bytes(data)
            written.append((host, fname, (len(data) + 253) // 254))
            games.append((it["title"], fname, it.get("start", "run")))

        make_menu = entry.get("menu") or (auto_menu and len(games) > 1)
        if make_menu:
            bas = tmp / "menu.bas"
            bas.write_text(menu_basic(labels, games))
            prg = tmp / "menu.prg"
            run(["petcat", "-w2", "-o", str(prg), "--", str(bas)])
            written.insert(0, (prg, "menu", (prg.stat().st_size + 253) // 254))

        total = sum(b for _, _, b in written)
        if total > DISK_BLOCKS:
            print(f"  ! {sid}: {total} blocks > {DISK_BLOCKS}; will not fit on one side")
        name = safe_filename(f"{sid} {', '.join(g[0] for g in games)}")[:100] + ".d64"
        img_path = out / name
        disk_id = re.sub(r"[^a-z0-9]", "", str(entry.get("disk_id", "")).lower())[:2] or "00"
        cmd = ["c1541", "-format", f"{c64_name(labels)},{disk_id}", "d64", str(img_path)]
        for host, fname, _ in written:
            cmd += ["-write", str(host), fname]
        run(cmd)
        manifest.append({"side": sid, "title": ", ".join(g[0] for g in games), "image": name,
                         "kind": "menu" if make_menu else "files", "blocks": total})
        print(f"  + {name}  ({total} blocks{', menu' if make_menu else ''})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selections", default=str(HERE / "selections.json"))
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--only", nargs="*", help="build only these side ids, e.g. D05-1")
    ap.add_argument("--auto-menu", action="store_true", help="add a menu to any side with 2+ games")
    args = ap.parse_args()
    need("c1541"); need("petcat")
    sel = json.loads(Path(args.selections).read_text())
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    manifest, cache = [], {}
    for sid, entry in sel.items():
        if args.only and sid not in args.only:
            continue
        print(sid)
        try:
            build_side(sid, entry, out, args.auto_menu, manifest, cache)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {sid} failed: {e}")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"{len(manifest)} images -> {out}")


if __name__ == "__main__":
    main()
