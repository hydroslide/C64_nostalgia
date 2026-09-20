#!/usr/bin/env python3
"""Give every image on the card a 320x200 PNG of the floppy it came from.

    python3 diskart.py                # from photos/reference, as catalogued
    python3 diskart.py --from photos/archive

Pi1541 shows a 320x200 PNG with the same name as a disk image while you are
browsing (`DisplayPNGIcons = 1` in options.txt), which is the whole carousel
with no code. This writes one per built image, named to match.

The reference photos are phone shots holding two disks at once, so a disk
catalogued as "top" or "bottom" gets that part of the frame cropped out.
They are a placeholder: shoot the disks flat, one side per frame, drop them
in and re-run, and the names stay the same.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ICON = (320, 200)

# Where in the frame a disk sits when the photo holds more than one.
BANDS = {"top": (0.05, 0.42), "bottom": (0.38, 0.75), None: (0.10, 0.70)}


def crop_band(im: Image.Image, position: str | None) -> Image.Image:
    lo, hi = BANDS.get(position, BANDS[None])
    return im.crop((0, int(im.height * lo), im.width, int(im.height * hi)))


def fit(im: Image.Image) -> Image.Image:
    """Letterbox onto a 320x200 black field, keeping the aspect ratio."""
    out = Image.new("RGB", ICON, (0, 0, 0))
    scale = min(ICON[0] / im.width, ICON[1] / im.height)
    small = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))),
                      Image.LANCZOS)
    out.paste(small, ((ICON[0] - small.width) // 2, (ICON[1] - small.height) // 2))
    return out


def caption(im: Image.Image, text: str) -> Image.Image:
    d = ImageDraw.Draw(im)
    text = text if len(text) <= 46 else text[:43] + "..."
    d.rectangle([0, ICON[1] - 13, ICON[0], ICON[1]], fill=(0, 0, 0))
    d.text((3, ICON[1] - 11), text, fill=(200, 200, 210))
    return im


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--card", default=str(ROOT / "card"))
    ap.add_argument("--from", dest="src", default=str(ROOT / "photos" / "reference"))
    ap.add_argument("--no-caption", action="store_true")
    args = ap.parse_args()

    card, src = Path(args.card), Path(args.src)
    catalog = {d["id"]: d for d in json.loads((ROOT / "disk_catalog.json").read_text())["disks"]}
    manifest = json.loads((card / "manifest.json").read_text())

    cache: dict[tuple[str, str | None], Image.Image] = {}
    made = missing = 0
    for m in manifest:
        if m["kind"] == "missing":
            continue
        disk_id = m["side"].split("-")[0]
        disk = catalog.get(disk_id)
        photo = disk and disk.get("photo")
        if not photo or not (src / photo).exists():
            missing += 1
            continue
        key = (photo, disk.get("position"))
        if key not in cache:
            cache[key] = fit(crop_band(Image.open(src / photo).convert("RGB"),
                                       disk.get("position")))
        icon = cache[key].copy()
        if not args.no_caption:
            icon = caption(icon, re.sub(r"\.(d64|g64|d71|d81)$", "", m["image"], flags=re.I))
        icon.save(card / m["folder"] / (Path(m["image"]).stem + ".png"))
        made += 1
    print(f"{made} icons written into {card}"
          + (f"; {missing} images had no photo" if missing else ""))


if __name__ == "__main__":
    main()
