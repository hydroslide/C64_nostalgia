# C64 Nostalgia — project notes

Last updated 2026-09-20.

## Where things stand

- All 34 photos in `photos/reference` are transcribed into `disk_catalog.json`: 40 disks, ~120 title entries, with load commands and menu-disk flags.
- No disk image online matches any of these disks as a whole. They were assembled file by file back then, so every copy came out different. Rebuilding them is the plan.
- `tools/` holds the scripts that do the rebuilding. See `tools/README.md` for usage.

## Labels still unidentified

| Disk | Label reads | Notes |
|---|---|---|
| D01 side 2 | "Heli" | Possibly Helikopter Jagd (1986). Unconfirmed. |
| D10 side 2 | "Mac Music" | No match found. |
| D18 side 2 | "Boxing" | Too generic to pin down. |
| D27 side 1 | "Rad Skater" | No C64 game by that name; Skate or Die is the likeliest. |
| D29 side 2 | "36 games" | No known 36-game C64 compilation found. |

## Where the game files can come from

- **[rbbs.be/bam](https://www.rbbs.be/bam/)** — a Belgian cracking group's disk archive, with full directory listings per disk and downloadable zips. The CARDBOARD-5 set holds most of the rare singles: Cohen's Towers (#046), Centropods (#006), Bagitman (#030), Mr. Wimpy (#015), Big Top Barney (#117), Monster Smash (#051), Slamball (#027), Moon Shuttle (#005).
- **archive.org `cbm8-*` items** — dumps of real personal collections. [cbm8-mcginty-tx-backups](https://archive.org/details/cbm8-mcginty-tx-backups) is 68 disks from a Texas kid's backups, the closest in spirit to this collection.
- **[Lemon64](https://www.lemon64.com/)**, **[GameBase64](https://gb64.com/)**, **[CSDb](https://csdb.dk/)** — one game per entry, good for single titles. CSDb's search blocks automated fetching, so it has to be searched by hand.
- Starfire + Fire One (D05 side 1) was a real two-game Epyx disk, so an original dump covers both.

## How the original menus worked

`MENU` was an ordinary program on the disk. It printed the list of games, waited for a key, then loaded and started the one you picked. Nothing special about the disk itself. `tools/build.py` generates an equivalent in BASIC: it prints the `LOAD` line and the start command on screen and queues two RETURNs in the keyboard buffer, which is how the originals did it.

Games that load more files while you play (World Games, Summer Games, Winter Games, Gauntlet, Flight Simulator II, Adventure Construction Set and others) can't share a menu disk. The build script copies a complete image for those instead.

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

1. Run `tools/harvest.py index` on the machine holding the pirate collections, then `match`, and review `report.md`.
2. Edit `selections.json`, run `build.py`, and test the menu disks on the Pi1541. The generated menu has not been tested on real hardware yet.
3. Take scan-quality photos of the disks, make 320×200 PNGs named to match each built image (`out/manifest.json` has the mapping).
4. Decide between the Pi Zero 2 W with a screen and the NFC card route. They aren't exclusive.
