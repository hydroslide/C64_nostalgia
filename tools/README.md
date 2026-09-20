# C64 disk rebuild tools

Rebuild the childhood floppies listed in `../disk_catalog.json` from files found
in big pirate/scene and preservation collections, into a folder that copies
straight onto a Pi1541's SD card.

Needs Python 3.9+ for indexing and matching. Building needs VICE's `c1541` and
`petcat`; checking the result needs VICE's `x64sc` and Pillow.

```
brew install vice                         # macOS
apt install vice                          # Debian / Raspberry Pi OS
winget install VICE-Team.VICE.SDL2        # Windows
python3 -m pip install pillow             # only for verify.py's contact sheets
```

## 1. Index your collections

```
python3 harvest.py index /path/to/collection1 /path/to/collection2 -v
```

Reads, including inside `.zip` archives (and one level of zip nesting):

- `.d64` / `.d71` / `.d81` sector images. Near-miss sizes — a few junk bytes
  appended, or a truncated last track — are trimmed or padded rather than
  thrown away.
- `.g64` GCR bitstream dumps, decoded back into sectors by `g64.py`. This is
  what makes the C64 Preservation Project's set searchable; only track 18 is
  decoded, which is all a directory needs, so 6,000 images take a few minutes.
  A dump too protected to read a directory from is still recorded, because a
  Pi1541 will mount and run it regardless.
- Loose `.prg` files, indexed under their filename.

Results go to `index.jsonl`. Re-running only re-reads files whose size or mtime
changed; `--rebuild` forces a full pass.

## 2. Match against the catalog

```
python3 harvest.py match            # --threshold 0.8  --top 10
```

Writes `report.md` (to read), `candidates.json` (the same, machine-readable)
and `selections.json` (the picks that `build.py` uses).

Matching is fuzzy: it ignores case and punctuation, strips cracker tags like
`GREEN BERET/TCN`, allows for the 16-character name limit, and knows the short
forms in the `ALIASES` table. Each title gets both **single-file** candidates
and **whole-image** ones, because plenty of games need a side to themselves.

Two things make the ranking usable rather than merely plausible:

- **Parameter disks lose.** Kracker Jax, Fast Hack'em and friends carry a
  one-block file named after nearly every game ever released. Those score a
  perfect 1.00 on name alone, so a source that looks like a copier, or a file
  too small to be a game, sorts below everything else and is flagged in the
  report.
- **Whole images for multi-load games.** Titles in the `MULTILOAD` set, and
  anything with no single-file candidate, get a whole disk drafted instead.

## 3. Correct the picks

Fuzzy matching still gets a few confidently wrong — Rambo III for Rambo, Batman
for Bagitman, Road Runner for Lode Runner. Corrections go in `overrides.json`,
not by hand-editing `selections.json`, so that re-running `match` does not throw
the review away:

```json
"Lode Runner":  {"image": "lode_runner[br0derbund_1983](lr)(yellow_label)(!)",
                 "note": "the fuzzy match picked Road Runner"},
"Battlezone":   {"file": ["htl.battlezone+.prg", "HTL.BATTLEZONE+"]},
"Time Pilot":   {"unavailable": "not in the local cache"}
```

Each source is named by any unique piece of its path, and an entry that no
longer resolves fails the run loudly. `by_title` applies wherever the title
appears; `by_side` overrides one side only.

To look around the index by hand:

```
python3 harvest.py find "lode runner"
```

## 4. Build

```
python3 build.py                 # or: --only D05-1 D05-2   --auto-menu
```

Everything lands in `../card/`, one folder per physical disk:

- **Rebuilt sides.** Files are extracted onto a fresh `.d64`. A side marked as
  a menu disk gets a `MENU` program written first.
- **Whole images.** Copied out as `.d64` or `.g64` next to the rebuilt side.
- **Oversized sides** are split into `(1 of 2)` / `(2 of 2)`; today's copies
  carry loader intros the originals did not, so a side that once fit may not.
- **`DISKS.md`, `manifest.json`, `README.txt`** record what is on the card and
  where every file came from.

### About the menu program

`LOAD"MENU",8,1` — what the original sleeves say — puts the bytes in memory
without telling BASIC where the program now ends. `READ` then finds no `DATA`,
and the first variable assigned lands on top of the program. The generated menu
pokes the end-of-program pointer measured at build time, so it behaves the same
loaded either way.

It also does not use the print-the-LOAD-line-and-stuff-the-keyboard-buffer
trick, which depends on the kernal printing exactly three lines between the
LOAD and the start command. Instead it loads from inside the program: BASIC
restarts a program after a `LOAD`, so a game that lives at BASIC start simply
takes over, and anything else leaves a flag in the tape buffer that line 1
reads and `SYS`es into. `build.py` reads each file's load address to decide
which of the two applies.

## 5. Check it actually works

```
python3 verify.py                # everything;  --only D05;  --sheets-only
```

Boots every built image in headless VICE and tiles the screenshots, twenty to a
sheet with names underneath, into `shots/sheets/`. Menu disks get two shots —
the menu, and the first game after an `a` — and are driven by attaching the disk
and typing the `LOAD`, because VICE's autostart quietly swaps in a virtual drive
and skips the real 1541 behaviour the Pi1541 will have.

This is not optional polish. The scene collections are full of files whose name
promises one game and whose contents are another; `L.HERO` turned out to be a
*Little Hero* preview, and `C.HERO` an Alpha Flight intro.

`preview.py` does one image at a time if you want a closer look:

```
python3 preview.py "../card/D05 .../D05-1 Slamball, Starfire, Fire One.d64" \
    --attach --true-drive --keys 'load"menu",8,1
run
a' --seconds 200
```
