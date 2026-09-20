# C64 disk rebuild tools

Rebuild the childhood floppies listed in `../disk_catalog.json` from files found in big pirate/scene collections.

Needs Python 3.9+ and nothing else for indexing and matching. Building needs VICE's `c1541` and `petcat`: `brew install vice` on macOS, `apt install vice` on Raspberry Pi OS or Debian.

## 1. Index your collections

```
python3 harvest.py index /path/to/collection1 /path/to/collection2 -v
```

- Reads every `.d64`, `.d71` and `.d81`, including ones inside `.zip` files and zips inside zips.
- Records each image's disk name, ID and directory into `index.jsonl`.
- Re-running only re-reads files that changed.
- GCR images (`.g64`, `.nib`) are counted but not parsed yet.

## 2. Match against the catalog

```
python3 harvest.py match            # --threshold 0.8  --top 10
```

This writes three files:

- `report.md`: the top candidates for every title on every disk side, for you to read.
- `candidates.json`: the same results, machine-readable.
- `selections.json`: a first-guess pick for each title. If `selections.json` already exists, the draft goes to `selections.draft.json` instead, so your edits are never overwritten.

Matching is fuzzy:

- It ignores case and punctuation.
- It strips cracker tags like `GREEN BERET/TCN`.
- It allows for the 16-character name limit.
- It uses the `ALIASES` table for known short forms (`HERO`, `GNG`, `FIST2` and so on).

Titles marked **M** in the report load extra files while you play. For those the draft picks the whole source image, not a single file.

## 3. Review selections.json

Each disk side has a `disk_name` (up to 16 characters), a `disk_id`, a `menu` flag and a list of `items`. Each item takes one of these forms:

```json
{"title": "Bagitman", "src": "/coll/pans06.d64", "member": null, "file": "BAGITMAN", "start": "sys 16384"}
{"title": "World Games", "whole_image": {"src": "/coll/epyx.zip", "member": "world games.d64"}}
{"title": "Ghost Manor", "todo": "no candidate found"}
```

- `start` is typed after the game loads. It defaults to `run`; some games need a `sys` address instead.
- `as` renames the file on the new disk.
- `"skip": true` leaves an item out.

## 4. Build

```
python3 build.py                 # or: --only D05-1 D05-2   --auto-menu
```

Everything goes into `out/`:

- **Menu disks.** Sides marked as menu disks get a `MENU` program written first, so `LOAD"MENU",8,1` then `RUN` works like the originals. Press a letter and the menu types the `LOAD` line and the start command for you, using the keyboard-buffer trick.
- **Whole-image games.** These are copied out as their own image.
- **Size check.** The build warns if a side goes over 664 blocks.
- **`out/manifest.json`** maps every built image back to its catalog disk and side. That mapping is what the photo, carousel and NFC-card layer will use.

**Not yet tested:** the menu program hasn't been run on a real C64 or in an emulator. Test it on the Pi1541 first.
