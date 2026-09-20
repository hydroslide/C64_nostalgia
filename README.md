# C64 Nostalgia

Rebuilding my childhood Commodore 64 floppy collection as clean, working disk
images — matched from the original hand-labeled disks (now just photos) against
public C64 archive/collection dumps, then reassembled into disks that load and
play the way they did in the 80s.

## Contents

- **`disk_catalog.json`** — one entry per physical disk, transcribed from the
  photos in `photos/reference/`: label text, disk ID, and the games on each
  side, plus a normalized title used for matching (`?` marks an uncertain
  reading).
- **`photos/reference/`** — photos of the original disks and sleeves that the
  catalog was transcribed from.
- **`tools/`** — the Python pipeline that turns the catalog into built disk
  images:
  - `harvest.py` — indexes disk-image collections and fuzzy-matches catalog
    titles against them.
  - `build.py` — rebuilds each catalog side into a `.d64`, adding a menu disk
    where the original had one.
  - `cbmimage.py` — reads/writes the CBM disk-image formats used by the other
    two scripts.

See [`tools/README.md`](tools/README.md) for the full index → match → review →
build workflow.

- **`pi1541-case/`** — 3D-printable case models for a Pi1541 (cycle-exact
  1541 floppy emulator) build, converted from donor designs to fit a
  Raspberry Pi Zero. See [`pi1541-case/README.md`](pi1541-case/README.md).

## Requirements

- Python 3.9+
- [VICE](https://vice-emu.sourceforge.io/)'s `c1541` and `petcat` on `PATH`
  for building disks (`brew install vice` on macOS, `apt install vice` on
  Debian/Raspberry Pi OS).

## Status

Catalog transcription and matching are in active use; the generated menu
disks haven't been tested on real hardware or in an emulator yet (see
`tools/README.md`). Built images and manifests will feed a planned photo /
carousel / NFC-card layer for browsing the collection.
