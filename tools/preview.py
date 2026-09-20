#!/usr/bin/env python3
"""Boot a disk image or program in VICE and save a screenshot of it.

    python3 preview.py out/*.d64 -o shots/            one shot each
    python3 preview.py game.prg --seconds 25          let it run longer
    python3 preview.py menu.d64 --keys a --seconds 20 press a key part-way

This is the only honest way to tell whether a rebuilt disk actually loads:
the cracked scene collections are full of files whose name promises one game
and whose contents are another. Nothing here touches the C64 side - VICE runs
headless in warp mode and writes a PNG on exit.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# ~985248 cycles per PAL frame-second; warp mode makes this quick regardless.
CYCLES_PER_SECOND = 985248


def find_vice() -> str:
    exe = shutil.which("x64sc")
    if exe:
        return exe
    guess = Path(os.environ.get("LOCALAPPDATA", "")) / (
        r"Microsoft\WinGet\Packages"
        r"\VICE-Team.VICE.SDL2_Microsoft.Winget.Source_8wekyb3d8bbwe"
        r"\SDL2VICE-3.10-win64\x64sc.exe")
    if guess.exists():
        return str(guess)
    sys.exit("x64sc not found - install VICE and put it on PATH")


def shoot(target: Path, out_png: Path, seconds: float, keys: str | None,
          key_delay: float, autostart_with_colon: bool, true_drive: bool,
          attach: bool = False) -> bool:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    cmd = [find_vice(), "-console", "-warp", "-silent", "-sounddev", "dummy",
           "-limitcycles", str(int(seconds * CYCLES_PER_SECOND)),
           "-exitscreenshot", str(out_png)]
    # Without true drive emulation VICE fakes the load and a 200-block game is
    # on screen in a second or two. Cracked games with their own fastloader
    # need the real drive, so --true-drive turns it back on.
    cmd.append("-drive8truedrive" if true_drive else "+drive8truedrive")
    if autostart_with_colon:
        cmd.append("-autostartwithcolon")
    if keys:
        # VICE types this into the keyboard buffer once the emulation is up.
        cmd += ["-keybuf", keys]
        cmd += ["-keybuf-delay", str(int(key_delay * CYCLES_PER_SECOND))]
    if attach:
        # Attaching and typing the LOAD by hand is what the real machine does,
        # and it keeps true drive emulation in play. VICE's autostart quietly
        # swaps in the virtual drive, which skips the SEARCHING/LOADING lines
        # a menu's screen arithmetic depends on.
        cmd += ["-8", str(target)]
    else:
        cmd += ["-autostart", str(target)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if not out_png.exists():
        sys.stderr.write(f"! {target.name}: no screenshot\n{r.stdout[-400:]}{r.stderr[-400:]}\n")
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+")
    ap.add_argument("-o", "--out", default=str(HERE / "shots"))
    ap.add_argument("--seconds", type=float, default=20.0, help="emulated seconds before the shot")
    ap.add_argument("--keys", help="text to push into the keyboard buffer")
    ap.add_argument("--key-delay", type=float, default=8.0, help="emulated seconds before the keys go in")
    ap.add_argument("--colon", action="store_true", help="autostart with RUN: instead of RUN")
    ap.add_argument("--attach", action="store_true",
                    help="attach the disk and type the LOAD, instead of autostarting")
    ap.add_argument("--true-drive", action="store_true",
                    help="emulate the 1541 cycle-exactly - slow, but needed by custom loaders")
    args = ap.parse_args()
    out = Path(args.out)
    ok = 0
    for t in args.targets:
        p = Path(t)
        png = out / (p.stem + ".png")
        if shoot(p, png, args.seconds, args.keys, args.key_delay, args.colon, args.true_drive, args.attach):
            ok += 1
            print(f"  + {png}")
    print(f"{ok}/{len(args.targets)} screenshots -> {out}")


if __name__ == "__main__":
    main()
