# Status

**Goal:** a folder that copies straight onto the Pi1541's SD card holding Ryan's
childhood disks, rebuilt as closely as today's archives allow.

Last updated: 2026-09-20, after the first full build.
Branch: `codex/disk-rebuild` (merges into `dev`; `main` stays release-ready).

---

## The short version

**`card/` exists and builds.** 83 disk images across 39 folders, one folder per
original floppy, named the way its label reads. 100 of the 120 catalog titles
have a source. The menu disks have been booted and driven in an emulator and
they work — that took three separate fixes, none of which were visible without
actually running them.

Not yet done: a pass over every screenshot to catch games that are not what
their filename claims, and testing on the real Pi1541.

## Where we are

| Stage | State |
|---|---|
| Environment (Python 3.12, VICE 3.10) | **done** |
| Index the local cache at `D:\C64` | **done** — 12,158 sources |
| Match the 120 catalog titles | **done** — 100 have a source |
| Hand-review the picks | **done** — 39 corrections in `tools/overrides.json` |
| Build the card | **done** — 83 images in `card/` |
| Menu disks boot and start a game | **done** — verified in VICE |
| Screenshot every image and review it | in progress |
| Test on the real Pi1541 | yours to do |
| Disk photos → 320×200 PNGs for the carousel | needs your photos |

## What is on the card

| | count |
|---|---|
| Whole images (`.g64` originals and cracked `.d64` sides) | 55 |
| Rebuilt sides assembled from single files | 23 |
| Of those, sides with a working `MENU` program | 5 |
| Titles with no source at all | 20 |

Load a rebuilt side with `LOAD"MENU",8,1` then `RUN` if it has a menu, or
`LOAD"*",8,1` then `RUN` otherwise. `card/DISKS.md` lists every image, what is
on it, and which archive each file came from.

## What had to be fixed to make the menus work

The generated `MENU` had never been run. It failed in three ways:

1. `LOAD"MENU",8,1` — what the original sleeves say — loads the bytes without
   telling BASIC where the program ends, so `READ` found no `DATA` and the
   first variable would have overwritten the program.
2. The keyboard-buffer trick depended on the kernal printing exactly three
   lines between the `LOAD` and the start command.
3. `RUN` does not start a game that does not load at BASIC start, which is most
   games lifted off an original disk.

All three are fixed; `NOTES.md` has the detail.

## Coverage, honestly

**20 titles are not on the card.** Five were already unidentified labels
(`Mac Music`, `36 games`, `Boxing`, `Rad Skater`, `Hey Diddle Diddle`). The
rest are real games that none of these three collections contains:

> Time Pilot · H.E.R.O. · Jungle Hunt · Bagitman · Mr. Wimpy · Mario's Brewery ·
> Gyruss · Big Top Barney · Danger Mouse · Haunted House · The Game Show ·
> Sublogic Football · Caveman (unconfirmed)

**One deliberate substitute:** Boulder Dash II (Rockford's Riot) is not in the
cache, so the first Boulder Dash stands in. It is marked as a substitute.

**Two picks are unconfirmed** and will be checked in the screenshot pass:
`Centropods` (a Centipede-style game on a Keypunch compilation) and `Moon
Patrol` (the file sits on a disk labelled Tomahawk).

## Open questions for you

1. **Hunt the missing titles online?** `rbbs.be/bam` and archive.org have most
   of them, but that means fetching from the internet. Say the word and I will;
   otherwise the card stays at what the local cache supports.
2. **Menu look.** Right now it is a plain list with a coloured title and an
   underline. If the menus you remember looked like something specific,
   describe them and I will rebuild them that way.
3. **Pi Zero or Zero 2 W?** Decides whether the on-screen carousel is possible
   at all — the original Zero has no HDMI output under Pi1541.
