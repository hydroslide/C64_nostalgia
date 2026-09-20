#!/usr/bin/env python3
"""Boot every built image in VICE and tile the results into contact sheets.

    python3 verify.py                    # everything on the card
    python3 verify.py --only D05         # one disk
    python3 verify.py --sheets-only      # re-tile existing screenshots

Building a disk proves nothing - the scene collections are full of files
whose name promises one game and whose contents are another, and a menu
that types its own LOAD line either works on the real thing or does not.
So each image is autostarted in headless VICE and photographed, and the
photographs are tiled twenty to a sheet with their names underneath, which
is a practical number to actually look at.

A menu disk gets two shots: the menu itself, and the first game after the
menu has been sent an "a".
"""
from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw

from preview import shoot

HERE = Path(__file__).resolve().parent
TILE = (384, 272)          # VICE's PAL screenshot size
LABEL_H = 34
COLS, ROWS = 5, 4


def targets(out: Path, manifest: list, only: str | None):
    for m in manifest:
        if m["kind"] == "missing":
            continue
        if only and not m["side"].startswith(only):
            continue
        path = out / m["folder"] / m["image"]
        if path.exists():
            yield m, path


MENU_LOAD = 'load"menu",8,1\nrun\n'


def shots_for(m: dict, path: Path, shots: Path, seconds: float) -> list[dict]:
    """Screenshots to take for one image."""
    if m["kind"] == "menu":
        # Type the LOAD by hand against the real drive. Autostart swaps in
        # VICE's virtual drive, which skips the SEARCHING/LOADING lines the
        # menu's cursor arithmetic is built around - so autostarting would
        # test something the Pi1541 will never do.
        return [
            dict(png=shots / f"{path.stem}.png", caption=f"{m['side']}  {path.name}",
                 keys=MENU_LOAD, seconds=seconds * 3, true_drive=True, attach=True),
            dict(png=shots / f"{path.stem} [A].png", caption=f"{m['side']}  menu -> first game",
                 keys=MENU_LOAD + "a", seconds=seconds * 12, true_drive=True, attach=True),
        ]
    true_drive = path.suffix.lower() == ".g64"
    return [dict(png=shots / f"{path.stem}.png", caption=f"{m['side']}  {path.name}",
                 keys=None, seconds=seconds * (6 if true_drive else 1),
                 true_drive=true_drive, attach=False)]


def sheet(pngs: list[tuple[Path, str]], out_png: Path):
    w = TILE[0] * COLS
    h = (TILE[1] + LABEL_H) * ROWS
    canvas = Image.new("RGB", (w, h), (20, 20, 24))
    d = ImageDraw.Draw(canvas)
    for i, (png, caption) in enumerate(pngs):
        col, row = i % COLS, i // COLS
        x, y = col * TILE[0], row * (TILE[1] + LABEL_H)
        try:
            im = Image.open(png).convert("RGB").resize(TILE)
            canvas.paste(im, (x, y))
        except Exception:  # noqa: BLE001
            d.rectangle([x, y, x + TILE[0], y + TILE[1]], fill=(60, 20, 20))
            d.text((x + 8, y + 8), "no screenshot", fill=(255, 180, 180))
        text = caption if len(caption) <= 62 else caption[:59] + "..."
        d.text((x + 6, y + TILE[1] + 4), text, fill=(235, 235, 235))
        d.text((x + 6, y + TILE[1] + 18), f"#{i + 1}", fill=(150, 150, 160))
    canvas.save(out_png)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(HERE.parent / "card"))
    ap.add_argument("--shots", default=str(HERE / "shots"))
    ap.add_argument("--only", help="limit to side ids starting with this, e.g. D05")
    ap.add_argument("--seconds", type=float, default=15.0)
    ap.add_argument("--sheets-only", action="store_true", help="skip VICE, just re-tile")
    ap.add_argument("--workers", type=int, default=max(2, (os.cpu_count() or 4) - 1),
                    help="how many VICE instances to run at once")
    args = ap.parse_args()

    out, shots = Path(args.out), Path(args.shots)
    shots.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((out / "manifest.json").read_text())

    jobs = []
    for m, path in targets(out, manifest, args.only):
        for job in shots_for(m, path, shots, args.seconds):
            job["path"] = path
            jobs.append(job)

    if not args.sheets_only:
        # Each shot is one VICE process sitting on one core, so the wall
        # clock is just the queue divided by however many cores there are.
        def take(job):
            shoot(job["path"], job["png"], job["seconds"], job["keys"],
                  job["seconds"] * 0.06, False, job["true_drive"], job["attach"])
            print(f"  . {job['caption']}", flush=True)

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            list(pool.map(take, jobs))

    taken = [(j["png"], j["caption"]) for j in jobs]

    sheets = shots / "sheets"
    sheets.mkdir(exist_ok=True)
    per = COLS * ROWS
    for n in range(0, len(taken), per):
        sheet(taken[n:n + per], sheets / f"sheet{n // per + 1:02d}.png")
    print(f"{len(taken)} screenshots, {(len(taken) + per - 1) // per} sheets -> {sheets}")


if __name__ == "__main__":
    main()
