# Status

**Goal:** a folder that copies straight onto the Pi1541 SD card holding Ryan's
childhood disks, rebuilt as closely as today's archives allow.

Last updated: 2026-09-20, after the matching pass.
Branch: `codex/disk-rebuild` (merges into `dev`; `main` stays release-ready).

---

## Where we are

| Stage | State |
|---|---|
| Environment (Python 3.12, VICE 3.10) | **done** |
| Index the local ROM cache at `D:\C64` | **done** — 12,158 sources |
| Match the 120 catalog titles | **done** — 100 have a source, 20 do not |
| Hand-review the picks | **done** — 39 corrections in `tools/overrides.json` |
| Build the disks | next |
| Verify each built disk boots | next |
| Assemble the Pi1541 root folder | next |
| Disk photos → 320×200 PNGs for the carousel | needs your photos |

## What was built along the way

- `tools/g64.py` — decodes G64 GCR dumps back into sectors, which is what made
  the 6,000-image C64 Preservation Project set searchable at all.
- `tools/preview.py` — boots any disk or program in VICE headless and saves a
  screenshot. This is how a pick gets checked rather than assumed.
- `tools/overrides.json` — the curated corrections, each one saying why.
- `harvest.py find <text>` — ad-hoc search of the whole cache.

## Coverage, honestly

100 of 120 catalog titles have a source. Of those, roughly half are single
files that go onto a rebuilt disk; the rest need a whole disk of their own
(multi-load games, and originals that were never cracked into a single file).

**20 titles are not in the local cache at all.** Five were already unidentified
labels (`Mac Music`, `36 games`, `Boxing`, `Rad Skater`, `Hey Diddle Diddle`).
The other fifteen are real games that these three collections simply do not
contain — most notably **Time Pilot, H.E.R.O., Bagitman, Mr. Wimpy, Gyruss,
Jungle Hunt, Danger Mouse** and **Big Top Barney**. They are in `NOTES.md` as
the targeted-hunting list; `rbbs.be/bam` has several of them.

**One deliberate substitute:** Boulder Dash II (Rockford's Riot) is not in the
cache, so the first Boulder Dash stands in. It is marked as a substitute.

**Two picks are unconfirmed** and want a look on screen: `Centropods`
(a Centipede-style game on a Keypunch compilation) and `Moon Patrol`
(the file sits on a disk labelled Tomahawk).

## Open questions for you

1. **Hunt the missing fifteen online?** `rbbs.be/bam` and archive.org have
   most of them, but that means fetching from the internet — say the word and
   I will, or leave the collection as what the local cache supports.
2. **Menu look.** The generated menu is a plain list with a coloured title.
   If the menus you remember looked like something specific, describe them.
3. **Pi Zero or Zero 2 W?** Decides whether the on-screen carousel is possible
   at all (the original Zero has no HDMI under Pi1541).
