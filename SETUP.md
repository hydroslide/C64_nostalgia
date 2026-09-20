# Putting this on the Pi1541

Everything you need is in **`card/`**. This is what to do with it.

---

## 1. Rebuild the card (only if it isn't there)

`card/` is generated, not stored in git, so it may not exist on a fresh clone.
From `tools/`:

```
python3 harvest.py index D:\C64\tdd-groups-cd-2010-03-21 D:\C64\C64_Preservation_Project_10th_Anniversary_Collection_G64 downloads
python3 harvest.py match
python3 build.py
python3 diskart.py
```

That takes about five minutes, most of it the index. If `card/` already has 39
folders in it, skip this.

## 2. Prepare the SD card

Skip this if your Pi1541 already boots — you only need step 3.

Do this once, following [the official instructions](https://cbm-pi1541.firebaseapp.com/):

1. **Format** the SD card as **FAT32**. 32 GB or smaller.
2. **Raspberry Pi firmware** — from the Raspberry Pi firmware `boot` folder,
   copy `bootcode.bin`, `fixup.dat` and `start.elf` to the **root** of the card.
3. **Pi1541 itself** — unzip the Pi1541 release to the root. Download the build
   that matches your board: there are separate ones for **Pi 0/1**, **Pi 2**,
   and **Pi 3 / Zero 2**.
4. **A 1541 ROM** at the root, named exactly one of: `dos1541`, `d1541.rom`,
   `d1541II`, or `Jiffy.bin`. Pi1541 does not ship one — it's the drive's own
   firmware and you supply it. Without it nothing boots.
5. *(Optional, for a screen)* the C64 character ROM at the root, named exactly
   `chargen`.

Unzipping Pi1541 creates a **`1541` folder** on the card. **That is where disk
images live** — not the root.

## 3. Copy the disks across

Copy the **contents** of `card/` into the `1541` folder:

```
SD card
├── bootcode.bin, fixup.dat, start.elf     (Raspberry Pi firmware)
├── kernel*.img, options.txt, ...          (Pi1541)
├── d1541II                                (the 1541 ROM you supplied)
├── chargen                                (optional, for a screen)
└── 1541\
    ├── D01 Rambo, Commando, Green Beret, Time Pilot, Heli, Ghosts n\
    │   ├── D01-1 Commando, Green Beret.d64
    │   ├── D01-1 Commando, Green Beret.png
    │   ├── D01-1 Rambo First Blood Part II.g64
    │   └── ...
    ├── D02 World Games\
    ├── ... 39 folders, one per original floppy ...
    ├── DISKS.md
    ├── README.txt
    └── manifest.json
```

If you'd rather keep them together, put them in `1541\C64 Disks\` instead —
Pi1541 browses subfolders either way.

The `.png` files are 320×200 pictures of the floppy each image came from. They
are ignored unless you have a screen; see step 6.

## 4. Load a disk

On the Pi1541, browse to a folder and mount an image the way you normally do
(the on-screen browser, or `LOAD"*",8` on the C64 to bring up fb64 and navigate
from there).

Then on the C64:

| The image | Type this |
|---|---|
| a `.d64` with a menu (the letter-menu disks) | `LOAD"MENU",8,1` then `RUN` |
| any other `.d64` | `LOAD"*",8,1` then `RUN` |
| a `.g64` | `LOAD"*",8,1` then `RUN` |

On a menu disk you get a list of games with a letter each. **Press the letter**
— it loads the game and starts it on its own. Nothing else to type.

`1541\DISKS.md` on the card lists every image, what's on it, and which archive
each file came from, including the handful that couldn't be found.

## 5. What the file types mean

- **`.d64`** — a side rebuilt from single files, the way these disks were
  assembled in the first place. Menu disks are these.
- **`.g64`** — an original disk copied bit for bit, copy protection and all.
  These are games that were never cracked down to a single file, or that load
  more data while you play. This is exactly what a Pi1541 is for — a plain
  SD2IEC can't run them.
- **`(1 of 2)` / `(2 of 2)`** — that side's games no longer fit on one disk.
  The copies available today carry loader intros the originals didn't.

A few `.g64` files are genuine originals and may ask you for a word from the
manual. That's the protection doing its job, not a fault.

## 6. If you have a screen (optional)

The pictures only appear on a Pi1541 with HDMI output, which means a **Pi Zero
2 W or Pi 3** — the original Pi Zero has no HDMI in this firmware. With one of
those, edit `options.txt` at the root of the card and uncomment:

```
DisplayPNGIcons = 1
RotaryEncoderEnable = 1     // only if you've wired a KY-040 encoder
```

Then browsing the list shows each disk's photo. The PNGs must be exactly
320×200 or they're skipped silently — `diskart.py` already makes them that size.

The photos on the card now are cropped from the phone shots in
`photos/reference`, which hold two disks per frame. When you shoot the disks
properly — flat, one side per frame — drop them in a folder and run:

```
python3 diskart.py --from ../photos/archive
```

The names stay the same, so nothing else has to change.

## 7. If something doesn't work

- **Nothing boots at all** — almost always the 1541 ROM: it has to be at the
  root and named exactly `dos1541`, `d1541.rom`, `d1541II` or `Jiffy.bin`.
- **A menu disk shows the list but pressing a letter does nothing** — tell me
  which disk. The menu works out whether each game needs `RUN` or a `SYS` from
  the file's load address, and a file that lies about it would do this.
- **A game loads and hangs, or crashes** — it's likely a multi-load that needs
  a whole side. Tell me which one and I'll switch it to a whole image.
- **A game isn't the game you remember** — entirely possible; the scene
  collections are full of files whose name promises one thing and delivers
  another. Every one on the card has been booted and looked at, but the ones
  marked UNCONFIRMED in `DISKS.md` are the likeliest to be wrong.
