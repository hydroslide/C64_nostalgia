# Status

**Goal:** a folder that copies straight onto the Pi1541's SD card holding Ryan's
childhood disks, rebuilt as closely as today's archives allow.

Last updated: 2026-09-20.
Branch: `codex/disk-rebuild` (merges into `dev`; `main` stays release-ready).

---

## The short version

**`card/` is built and ready to copy.** 93 disk images across 40 folders, one
folder per original floppy, named the way its label reads. **115 of the 120
catalog titles** have a source. Every image has been booted in an emulator and
looked at.

**Read [`SETUP.md`](SETUP.md)** — that's what to do with the card.

## Where we are

| Stage | State |
|---|---|
| Environment (Python 3.12, VICE 3.10) | **done** |
| Index the local cache at `D:\C64` | **done** — 12,418 sources |
| Match the 120 catalog titles | **done** |
| Hand-review the picks | **done** — 41 corrections in `tools/overrides.json` |
| Fetch what no local collection had | **done** — 14 games off the Internet Archive |
| Build the card | **done** — 94 images |
| Menu disks boot and start a game | **done** — verified in VICE |
| Boot every image and review it | **done** — three wrong picks caught and fixed |
| Varied menu look per disk | **done** — 4 styles, 10 palettes |
| Test on the real Pi1541 | **yours to do** — see `SETUP.md` |
| Proper flat photos of the disks | **needs your photos** — see `SETUP.md` §6 |

## What is on the card

| | count |
|---|---|
| Whole images (`.g64` originals, cracked `.d64` sides) | 60 |
| Rebuilt sides assembled from single files | 28 |
| Of those, sides with a working `MENU` program | 5 |
| Titles with no source at all | 5 |

Each image also has a 320×200 `.png` of the floppy it came from, which the
Pi1541 shows while browsing if you have a screen.

## What booting them caught

Three picks were wrong in ways only a screen could show:

- `BC'S QUEST II` was **B.C. II: Grog's Revenge**, not Quest for Tires.
- `PINECREST MANOR` is a story *file*, not a program — it needs Scholastic's
  Tales of Mystery engine, so the whole side goes on.
- Dino Eggs' file loads at `$0400`, over screen memory — a loader stage, not
  the game.

And one wrong assumption about testing: VICE's autostart swaps in its virtual
drive, which reports `?LOAD ERROR` on perfectly good disks. Everything is now
driven the way the Pi1541 will be — attach the disk, type the `LOAD`, let the
real 1541 answer.

## Coverage, honestly

**Sixteen games were fetched from the Internet Archive.** Fourteen because no
local collection had them at all � Jungle Hunt, H.E.R.O., Sublogic Football,
Haunted House, Bagitman, Mario's Brewery, Mr. Wimpy, Gyruss, The Game Show, Big
Top Barney, Hey Diddle Diddle, Danger Mouse in the Black Forest Chateau, and
Skate or Die standing in for "Rad Skater" � and two, Rambo and Spelunker,
because the only local copies were originals that would not start.

**Five titles are still not on the card:**

| Title | Why |
|---|---|
| Time Pilot | No C64 release found anywhere — the arcade game seems never to have been ported. The label may mean a clone. |
| Caveman | The archive's "Caveman" is a 1990 *Compute!* type-in; "Crazy Caveman" doesn't look like the arcade game either. |
| Mac Music | Label never identified. |
| Boxing | Label too generic to identify. |
| 36-game compilation | Label never identified. |

**Two deliberate substitutes**, both marked as such in `card/DISKS.md`:

- **Boulder Dash II** (Rockford's Riot) isn't anywhere, so the first Boulder
  Dash stands in.
- **"Rad Skater"** isn't a C64 game; **Skate or Die** stands in as the likeliest
  thing the label meant.

**Two picks are unconfirmed**: `Centropods` (the disk boots a game called
CENTRIPOD, which is Centipede-like and plausible) and `Moon Patrol` (the file
sits on a disk labelled Tomahawk, but boots as Moon Patrol).

## Still open

1. **Pi Zero or Zero 2 W?** Decides whether the on-screen carousel is possible
   at all — the original Zero has no HDMI output under Pi1541. Everything else
   on the card works either way.
2. **Proper disk photos.** The current PNGs are cropped from the phone shots in
   `photos/reference`, which hold two disks per frame. Shoot them flat and
   re-run `diskart.py --from <folder>`; the names don't change.
3. **The five unknowns.** If any of those labels jogs your memory, say the word
   and I'll go looking again.
