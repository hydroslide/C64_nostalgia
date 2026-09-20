# C64 Nostalgia — project notes

Last updated 2026-09-20.

## Where things stand

- All 34 photos in `photos/reference` are transcribed into `disk_catalog.json`: 40 disks, ~120 title entries, with load commands and menu-disk flags.
- No disk image online matches any of these disks as a whole. They were assembled file by file back then, so every copy came out different. Rebuilding them is the plan.
- `tools/` holds the scripts that do the rebuilding, and `card/` is what they produce. See `tools/README.md` for usage and `STATUS.md` for current coverage.
- 100 of the 120 catalog titles have a source in the local cache at `D:\C64`. 20 do not — see below.

## What the local cache actually holds

`D:\C64` has three collections, and they turned out to be good for different things:

| Set | What it is | What it is good for |
|---|---|---|
| `tdd-groups-cd-2010-03-21` | a scene CD: ~2,900 `.d64` plus ~3,400 loose `.prg` | cracked single files — exactly what a menu disk needs |
| `C64_Preservation_Project_..._G64` | ~6,000 `.g64` bitstream dumps of real originals | whole disks to mount; the only source for many titles |
| `C64_Preservation_Project_...` (`.nbz`) | the same set as compressed NIB | **not read** — proprietary compression, and the G64 set covers it |
| `rulez-plus4-game` | Commodore Plus/4 software | nothing; wrong machine |

A G64 is a raw GCR bit image rather than sectors, so nothing could search it until `tools/g64.py` was written to decode it back. That one step took coverage from 59 titles to 112.

The practical consequence: a game that was cracked down to a single file goes onto a rebuilt menu disk; a game that only survives as an original gets mounted whole as a `.g64`, which is precisely what a Pi1541 is for.

## Traps in these collections

- **Copy-protection parameter disks.** Kracker Jax, Fast Hack'em, Mirror, Ultrabyte and friends carry a one- to six-block file named after nearly every game ever released. They score a perfect name match and are never the game. `harvest.py` now sorts them below everything else.
- **Cracker intros.** A file called `GHOSTBUSTERS INT` is the intro, not the game.
- **Near-miss titles.** Rambo III for Rambo, Batman for Bagitman, Road Runner for Lode Runner, Upside Down for Up'n Down, Hero Quest for H.E.R.O.
- **Names that lie.** `L.HERO PRV.` turned out to be a *Little Hero* preview and `C.HERO+4FX` an Alpha Flight intro — both only visible by booting them. This is why `verify.py` exists.

## Labels still unidentified

| Disk | Label reads | Notes |
|---|---|---|
| D01 side 2 | "Heli" | Helikopter Jagd (1986) — a `helicopter jagd.prg` was found and is on the card. |
| D10 side 2 | "Mac Music" | No match found. |
| D18 side 2 | "Boxing" | Too generic to pin down. |
| D27 side 1 | "Rad Skater" | No C64 game by that name; Skate or Die is the likeliest. |
| D29 side 2 | "36 games" | No known 36-game C64 compilation found. |

## Titles no local collection has

These are real, identified games that none of the three collections contains. They are the targeted-hunting list:

**Time Pilot, H.E.R.O., Jungle Hunt, Bagitman, Mr. Wimpy, Mario's Brewery, Gyruss, Big Top Barney, Danger Mouse in the Black Forest Chateau, Haunted House, Hey Diddle Diddle, The Game Show, Sublogic Football, Caveman** (unconfirmed).

One substitution was made deliberately: **Boulder Dash II (Rockford's Riot)** is not in the cache, so the first Boulder Dash stands in. It is marked as a substitute in `DISKS.md`.

## Where the missing files can come from

- **[rbbs.be/bam](https://www.rbbs.be/bam/)** — a Belgian cracking group's disk archive, with full directory listings per disk and downloadable zips. The CARDBOARD-5 set holds most of the rare singles: Cohen's Towers (#046), Centropods (#006), Bagitman (#030), Mr. Wimpy (#015), Big Top Barney (#117), Monster Smash (#051), Slamball (#027), Moon Shuttle (#005).
- **archive.org `cbm8-*` items** — dumps of real personal collections. [cbm8-mcginty-tx-backups](https://archive.org/details/cbm8-mcginty-tx-backups) is 68 disks from a Texas kid's backups, the closest in spirit to this collection.
- **[Lemon64](https://www.lemon64.com/)**, **[GameBase64](https://gb64.com/)**, **[CSDb](https://csdb.dk/)** — one game per entry, good for single titles. CSDb's search blocks automated fetching, so it has to be searched by hand.
- Starfire + Fire One (D05 side 1) was a real two-game Epyx disk, and the Epyx sampler in the preservation set covers both.

## How the original menus worked, and how this one does

`MENU` was an ordinary program on the disk. It printed the list of games, waited for a key, then loaded and started the one you picked.

The usual way to write that is to print a `LOAD` line at the top of the screen, print `RUN` a few rows down, and stuff two RETURNs into the keyboard buffer. Booting it showed three separate reasons that does not work here, and the generated menu now avoids all three:

1. **`LOAD"MENU",8,1` breaks BASIC.** A secondary address of 1 loads the bytes without telling BASIC where the program now ends, so `READ` finds no `DATA` and the first variable assigned lands on top of the program. The menu pokes the end-of-program pointer (measured at build time) and `CLR`s, so it behaves the same loaded either way. `LOAD"MENU",8,1` — what the sleeves actually say — works.
2. **The keyboard-buffer trick is fragile.** It depends on the kernal printing exactly three lines between the `LOAD` and the start command. The menu now loads from inside the program instead: BASIC restarts a program after a `LOAD`, so a game at BASIC start simply takes over, and anything else leaves a flag in the tape buffer that line 1 reads and `SYS`es into. No screen arithmetic at all.
3. **`RUN` does not start most of these games.** Files lifted off original disks do not load at `$0801`. `build.py` reads each file's load address and picks `RUN` or `SYS` accordingly.

Games that load more files while you play (World Games, Summer Games, Winter Games, Gauntlet, Flight Simulator II, Adventure Construction Set and others) can't share a menu disk, and neither can originals that were never cracked. The build copies a complete image for those instead.

## Hardware findings

**Pi1541 and the screen**

- On an original Pi Zero, Pi1541's HDMI output is switched off in the build; a Pi Zero 2 W or a Pi 3 is needed for any screen. Sources: [Pi1541 what's new](https://cbm-pi1541.firebaseapp.com/whatsnew.html), [main.cpp](https://github.com/pi1541/Pi1541/blob/master/src/main.cpp).
- [pottendo-Pi1541](https://github.com/pottendo/pottendo-Pi1541) is the fork that supports the Zero 2 W with HDMI, and adds a Wi-Fi web interface with a mountable URL (`mount-imgs.html?[MOUNT]&<path>`). It runs hotter and is slightly less compatible than the original firmware, so active cooling is recommended.
- `DisplayPNGIcons = 1` shows a 320×200 PNG with the same name as a disk image on the HDMI screen ([options.txt](https://github.com/pi1541/Pi1541/blob/master/options.txt)). That plus the built-in rotary encoder support gets most of the disk-photo carousel with no firmware changes.

**Screens** (must be plain HDMI with USB power; Pi1541 can't load screen drivers, and GPIO-header screens clash with the drive wiring)

| Screen | Resolution | Price | Notes |
|---|---|---|---|
| [Waveshare 4.3" (B)](https://www.waveshare.com/4.3inch-hdmi-lcd-b.htm) | 800×480 IPS | ~$50 | Easiest fit |
| [Waveshare 4" (C)](https://www.waveshare.com/4inch-hdmi-lcd-c.htm) | 720×720 IPS square | ~$67 | Needs `hdmi_timings` in config.txt; may stretch a 4:3 screen |
| [Elecrow 5"](https://www.elecrow.com/5-inch-hdmi-800-x-480-capacitive-touch-lcd-display-for-raspberry-pi-pc-sony-ps4.html) | 800×480 | ~$38 | Cheapest without GPIO conflict |

Avoid the Waveshare 3.5" and the non-C 4": both plug onto the GPIO header. Touch won't work on any of them under Pi1541.

**NFC cards**

- Prior art: [TeensyROM's NFC loader](https://github.com/SensoriumEmbedded/TeensyROM/blob/main/docs/NFC_Loader.md) (C64 cartridge, tag holds a file path) and [Zaparoo](https://zaparoo.org/) for MiSTer. Nothing exists for Pi1541 yet.
- Cleanest design: an ESP32 with a PN532 reader (~$24) inside the case, calling pottendo's mount URL over Wi-Fi. No Pi GPIO pins used and no interference with the drive's timing.
- Two NTAG215 tags per card, one near each edge (~100 mm apart on a 5.25"-wide card), with the reader at one side of the slot: flipping the card brings the other tag over the reader. Read ranges are a few centimeters, so only one tag is ever in the field. Write the image path and side onto the tag itself.

## Next steps

1. Copy `card/` onto the Pi1541's SD card and try a menu disk on the real thing. `D05-1` is the best first test.
2. Decide whether to hunt the fourteen missing titles online (`rbbs.be/bam` has most of them).
3. Take scan-quality photos of the disks, make 320×200 PNGs named to match each built image (`card/manifest.json` has the mapping).
4. Decide between the Pi Zero 2 W with a screen and the NFC card route. They aren't exclusive.
