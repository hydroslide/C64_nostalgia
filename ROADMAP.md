# C64 Nostalgia — recommendations and roadmap

Everything discussed that isn't built yet, in the order it makes sense to build it. Written 2026-09-20. Stages 1 and 2 stand on their own; 3 onward are the display/selection project and can be done in any order after 2.

Status of what already exists: `disk_catalog.json` (40 disks transcribed from the photos), `tools/` (index, match, build), `NOTES.md` (findings and sources).

---

## Stage 1 — Harvest the game files and rebuild the disks

**Where:** the machine that holds the pirate collections.

1. Install VICE for `c1541` and `petcat`: `brew install vice` on macOS, `apt install vice` on Raspberry Pi OS or Debian. Copy `tools/` and `disk_catalog.json` over, or clone the folder.
2. `python3 harvest.py index /path/to/set1 /path/to/set2 -v`. This reads every `.d64`, `.d71` and `.d81`, including inside zips, and writes `index.jsonl`.
3. `python3 harvest.py match` → `report.md`, `candidates.json`, `selections.json`.
4. Read `report.md` and fix `selections.json` by hand. Expect these problems:
   - **Near-miss titles.** Pitfall vs Pitfall II, the two Fist games, Leader Board vs Leader Board Tournament. Check the block count and the disk each file sits on.
   - **Cracker intros.** A file like `GHOSTBUSTERS INT` is the intro, not the game. Prefer the larger file.
   - **Nothing found.** Add spellings to the `ALIASES` table in `harvest.py` and re-run `match`; the draft goes to `selections.draft.json` so your edits survive.
5. `python3 build.py` → `out/` plus `out/manifest.json`.

**Recommendations while doing this**

- Keep the whole folder in git, including `selections.json`. The selections are the real work product — they're the record of which copy of each game you chose.
- Don't chase perfection on the first pass. Build the five menu disks and a handful of singles, test them, then do the rest.
- Track the ones you can't find in a short list at the bottom of `NOTES.md`. Those are the candidates for targeted hunting (Ghost Manor, Rocketball, Dolphin's Rune and the unidentified labels).
- **Consider dumping the physical disks too.** Your own floppies are the primary source, and they're 40 years old. A [ZoomFloppy](https://store.go4retro.com/zoomfloppy/) plus a real 1541 with [OpenCBM and nibtools](https://github.com/OpenCBM/nibtools) reads them as `.d64` or `.g64`. A real 1541 is also the only easy way to read both sides of a flipped disk: PC 5.25" drives can't read the flip side, and [Greaseweazle's own docs](https://github.com/keirf/greaseweazle/wiki/Yann-Serra-Tutorial) call out both that limitation and the awkwardness of GCR timing on PC drives. Even a partial dump settles what "Heli" and "36 games" actually were.

## Stage 2 — Verify on the Pi1541

The generated `MENU` program has not been run on real hardware. Test it before building all 40 disks.

1. Copy one built menu disk (D05 side 1 is the best test: five games) to the Pi1541's SD card and mount it.
2. `LOAD"MENU",8,1` then `RUN`. Press a letter.
3. What should happen: the screen clears, a `LOAD` line appears at the top, `SEARCHING`/`LOADING`/`READY.` follow, and the start command runs by itself.

**If it misbehaves**

- Nothing happens after the load: the start command landed on the wrong screen row. The row positions are in `menu_basic()` in `build.py`; add or remove a blank `print`.
- The game loads but sits at `READY.`: it needs a `SYS` address instead of `RUN`. Put that in the item's `start` field, e.g. `"start": "sys 16384"` for Bagitman, which the original label actually says.
- A game crashes on load: it's probably multi-part. Add its title to the `MULTILOAD` set in `harvest.py` and give it a whole image.

**Worth doing once it works:** make the menu match what you remember. Right now it's a plain list with a colored title. If the original menus you're picturing had a particular look, describe it and it can be rewritten — a machine-code menu with a custom character set is also an option if BASIC feels too plain.

## Stage 3 — Photograph and pair the disks

**Goal:** every built image has a picture of the physical disk that produced it.

- **Shoot flat.** A phone directly overhead on a tripod with even light beats a scanner for a floppy with a warped label, but a flatbed scan at 600 dpi is sharper and more consistent if the disks lie flat. Either is fine; consistency matters more than resolution.
- **Shoot both sides**, since most of these disks are two different disks in practice.
- **Keep two copies of each photo:** an archival full-resolution one in `photos/archive/`, and a 320×200 PNG for the Pi1541, since that's the size it displays ([options.txt](https://github.com/pi1541/Pi1541/blob/master/options.txt)).
- **Name the PNG exactly like the disk image** it belongs to, minus the extension. That's the only linkage Pi1541 needs. `out/manifest.json` already maps side IDs to image names, so a small script can rename a batch of photos from it — worth writing once you have the photos.
- Add the disk ID (`D05-1`) into the catalog's photo field as you go, so the catalog, the photo and the image all point at each other.

## Stage 4 — On-screen carousel

**First: check which Pi you have.** On an original Pi Zero, Pi1541 has no HDMI output at all ([source](https://github.com/pi1541/Pi1541/blob/master/src/main.cpp)). A Pi Zero 2 W is the cheap fix.

1. Move to [pottendo-Pi1541](https://github.com/pottendo/pottendo-Pi1541), which supports the Zero 2 W with HDMI. Add a small heatsink or fan; the README says it runs hotter than the original firmware.
2. Set `DisplayPNGIcons = 1` and `RotaryEncoderEnable = 1` in `options.txt`. With the PNGs from stage 3, spinning the encoder through the image list shows each disk's photo. That's most of the carousel with no code.
3. Screen: the [Waveshare 4.3" (B)](https://www.waveshare.com/4.3inch-hdmi-lcd-b.htm) (800×480 IPS, USB powered, ~$50) is the safe pick. Avoid anything that plugs onto the GPIO header — those pins carry the drive wiring. Touch won't work under Pi1541 either way.
4. Set the screen mode in `config.txt` (`hdmi_group`/`hdmi_mode`, or `hdmi_cvt` for 800×480). The graphics chip reads that file before the firmware starts, so it applies to bare-metal Pi1541 too.

**If the built-in browser isn't enough** — if you want a real cover-flow with big artwork — that means modifying the firmware, which is GPL C++ built with `arm-none-eabi` GCC. Doable, but treat it as its own project, and only after the stock browser proves too plain.

## Stage 5 — NFC cards

Nobody has done this on a Pi1541 yet, so this is the part with real unknowns. Prior art to borrow from: [TeensyROM's NFC loader](https://github.com/SensoriumEmbedded/TeensyROM/blob/main/docs/NFC_Loader.md) and [Zaparoo](https://zaparoo.org/).

**Recommended shape:** keep NFC entirely out of Pi1541. An ESP32 with a PN532 reader sits in the case, reads the tag, and calls pottendo's mount URL over Wi-Fi (`http://<pi>/mount-imgs.html?[MOUNT]&<path>`). No GPIO pins are borrowed from the drive and nothing interferes with its timing.

**Cards**

- Print the disk photo from stage 3 at 5.25" square on cardstock, one side of the card per side of the disk, so the card reads like the floppy.
- Two NTAG215 stickers per card, each about 10–15 mm in from opposite edges, so they're ~100 mm apart. The reader mounts behind one side of the slot; flipping the card brings the other tag over it. Read range is a few centimeters, so only one tag is ever in the field — that part should work, though I haven't tested it.
- Write the image path and the side onto the tag itself rather than relying on the tag's serial number. Then a reprinted card needs no lookup table.
- Put a physical stop in the slot so the card lands in the same place every time, and keep the antenna a centimeter or so away from the Pi and the screen's metal back.

**Build order:** get one tag reading and mounting one image before printing 40 cards. Debounce the removal event, or a quick flip will mount and unmount repeatedly.

## Stage 6 — Case and hardware

- Pi Zero 2 W needs a mini-HDMI cable for the screen; account for the plug depth in the case.
- Power: the screen is USB powered, so budget for a second supply or a powered hub. Screens and a Pi Zero 2 W on one shared supply is where brownouts come from.
- Leave airflow for the Pi if you go with the pottendo firmware.
- If you add an OLED as well as HDMI, note that the pottendo README warns that HDMI and LCD output together can cause problems.

## Stage 7 — Preservation

Worth doing regardless of how the front end turns out.

- Keep `out/` and the photos in a versioned backup, not only on the SD card.
- Write a short README per rebuilt disk, or extend `manifest.json`, recording where each file came from. In ten years the provenance is the interesting part.
- Consider sharing the catalog method back: the lack of any searchable index of what's inside scene disk images is exactly the gap `harvest.py` fills, and the Lemon64 forum and CSDb crowd would use it.

---

## Open questions

1. Original Pi Zero or Zero 2 W? Decides whether stage 4 needs a new board.
2. How faithful should the menu look — plain list, or a recreation of a specific menu you remember?
3. Carousel, NFC cards, or both? They don't conflict: the carousel is firmware settings, the cards are a separate box.
4. Dump the physical disks with a ZoomFloppy, or rebuild purely from the collections?
