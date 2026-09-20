# C64 Nostalgia

Rebuilding my childhood Commodore 64 floppy collection as clean, working disk
images — matched from the original hand-labeled disks (now just photos) against
public C64 archive/collection dumps, then reassembled into disks that load and
play the way they did in the 80s.

The end product is [`card/`](#the-card): a folder that copies onto a Pi1541's SD
card, one folder per original floppy.

## Contents

- **`STATUS.md`** — where the project is right now, and what needs a decision.
- **`disk_catalog.json`** — one entry per physical disk, transcribed from the
  photos in `photos/reference/`: label text, disk ID, and the games on each
  side, plus a normalized title used for matching (`?` marks an uncertain
  reading).
- **`photos/reference/`** — photos of the original disks and sleeves that the
  catalog was transcribed from.
- **`tools/`** — the Python pipeline that turns the catalog into built disk
  images:
  - `harvest.py` — indexes disk-image collections (`.d64`/`.d71`/`.d81`,
    `.g64`, loose `.prg`, and anything inside zips) and fuzzy-matches catalog
    titles against them. `harvest.py find <text>` searches the index by hand.
  - `g64.py` — decodes a G64 GCR bitstream back into sectors, which is what
    makes the C64 Preservation Project's dumps searchable at all.
  - `cbmimage.py` — reads the CBM disk-image formats the other scripts use.
  - `overrides.json` — the hand-picked corrections, each saying why.
  - `build.py` — rebuilds each catalog side into `card/`, adding a menu disk
    where the original had one.
  - `preview.py` / `verify.py` — boot the built images in headless VICE and
    tile the screenshots, so a pick is checked rather than assumed.

  See [`tools/README.md`](tools/README.md) for the full index → match →
  correct → build → verify workflow.

- **`pi1541-case/`** — 3D-printable case models for a Pi1541 (cycle-exact
  1541 floppy emulator) build, converted from donor designs to fit a
  Raspberry Pi Zero. See [`pi1541-case/README.md`](pi1541-case/README.md).

## The card

`card/` is not checked in — it is rebuilt from the catalog, the overrides and
whatever collections are on hand. Inside it:

- one folder per original floppy, named the way its label reads;
- a `.d64` per rebuilt side, with a `MENU` program on the sides that had one;
- a `.d64` or `.g64` alongside for games that need a whole disk to themselves —
  multi-load games, and originals nobody ever cracked down to a single file;
- `DISKS.md` and `manifest.json` recording where every single file came from,
  and `README.txt` explaining the card to whoever is holding it.

## Requirements

- Python 3.9+ (plus Pillow, only for `verify.py`'s contact sheets)
- [VICE](https://vice-emu.sourceforge.io/): `c1541` and `petcat` to build
  disks, `x64sc` to check them. `brew install vice` on macOS, `apt install
  vice` on Debian/Raspberry Pi OS, `winget install VICE-Team.VICE.SDL2` on
  Windows.

## Status

The card builds and the menu disks have been booted and driven in VICE — see
`STATUS.md` for coverage, the titles no local collection has, and the open
questions. The built images and `manifest.json` feed the planned photo /
carousel / NFC-card layer; `ROADMAP.md` covers that.
