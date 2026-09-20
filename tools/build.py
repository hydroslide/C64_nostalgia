#!/usr/bin/env python3
"""Rebuild the original disks from selections.json into a Pi1541-ready folder.

    python3 build.py [--only D05-1] [--out ../card]

Needs VICE's `c1541` and `petcat` on PATH (macOS: `brew install vice`;
Debian/Raspberry Pi OS: `apt install vice`; Windows: `winget install
VICE-Team.VICE.SDL2`).

Everything lands in `card/` at the top of the repo - that whole folder is
what goes on the Pi1541's SD card. One folder per physical disk, named the
way the label reads, so the Pi1541's own browser reads like the shoebox:

    card/D05 River Raid, Slamball, Star Fire.../
        D05-1 Slamball, Starfire, Fire One.d64   <- rebuilt side, MENU first
        D05-1 Moon Shuttle.g64                   <- needed a disk of its own

Items with "whole_image" are copied out whole - multi-load games, and
originals that were never cracked down to a single file. Everything else is
extracted from its source and written onto a fresh .d64; if the side was a
menu disk a BASIC MENU program is written first, so LOAD"MENU",8,1 and RUN
work the way they did.

card/manifest.json records where every single file came from; DISKS.md is
the same for a human, including what could not be found, and README.txt
explains the card to whoever is holding it.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import g64
from cbmimage import open_image

HERE = Path(__file__).resolve().parent
CATALOG = next(p for p in (HERE / "disk_catalog.json", HERE.parent / "disk_catalog.json") if p.exists())
DISK_BLOCKS = 664


def load_image_bytes(src: str, member: str | None) -> bytes:
    data = Path(src).read_bytes()
    if not member:
        return data
    for part in member.split("::"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            data = z.read(part)
    return data


def open_source(src: str, member: str | None):
    """Open a source as a readable disk, decoding a G64 in full if need be.

    Indexing only decodes track 18, which is enough for a directory. Pulling
    a file off the disk needs every track, so a G64 source is decoded whole
    here. Protected originals will come back with holes; that is what the
    screenshot pass is for.
    """
    data = load_image_bytes(src, member)
    if (member or src).lower().endswith(".g64"):
        data = g64.to_d64(data)
    return open_image(data, lenient=True)


def image_ext(src: str, member: str | None, data: bytes) -> str:
    """What to call a whole image on the SD card.

    A .g64 is a raw bitstream, not sectors, so it cannot be opened as a disk
    image - but a Pi1541 mounts it happily, which is the whole point of the
    thing. Anything else gets its format read out of the data.
    """
    name = (member or src).lower()
    if name.endswith(".g64"):
        return "g64"
    try:
        return open_image(data, lenient=True).fmt
    except ValueError:
        return Path(name).suffix.lstrip(".") or "d64"


def c64_name(s: str) -> str:
    """Lowercase ASCII becomes normal PETSCII capitals in c1541/petcat."""
    s = re.sub(r"[^a-z0-9 .\-!']", "", s.lower().replace("&", "and"))
    return s[:16].strip() or "untitled"


def safe_filename(s: str, limit: int = 60) -> str:
    s = re.sub(r'[\\/:*?"<>|]', "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s[:limit].strip(" .") or "untitled"


def need(tool: str):
    if not shutil.which(tool):
        sys.exit(f"'{tool}' not found - install VICE (brew install vice / apt install vice)")


def menu_basic(title: str, games: list, vartab: int = 0) -> str:
    """games = [(label, filename, sys_addr)]. Returns petcat -w2 source.

    The usual way to write one of these is to print a LOAD line at the top
    of the screen, print the start command a few rows down, and stuff two
    RETURNs into the keyboard buffer. It works, but it depends on the kernal
    printing exactly three lines (SEARCHING / LOADING / READY.) between
    them, which it does on real hardware and does not under an emulator's
    virtual drive - and it breaks entirely if a filename wraps.

    This menu loads from inside the program instead. BASIC restarts a
    program after a LOAD, keeping memory below it intact, so:

      * a game that lives at BASIC start is loaded with ",8" and simply
        takes over - BASIC restarts and the game is the program now;
      * anything else is loaded with ",8,1", BASIC restarts *this* program,
        line 1 sees the flag left in the tape buffer and SYSes into it.

    The tape buffer at 828 is used for the flag rather than a variable
    because line 2 has to CLR (see below) and that would wipe a variable.

    Line 2 exists because LOAD"MENU",8,1 - which is what the original
    sleeves say - puts the bytes in memory without telling BASIC where the
    program now ends. READ then finds no DATA and the first variable
    assigned lands on top of the program. Poking the end-of-program pointer
    measured at build time fixes both. The digits are zero-padded so filling
    them in cannot change the program's length.
    """
    t = c64_name(title)[:30]
    lines = [
        '1 ifpeek(828)=73thenpoke828,0:sys peek(829)+256*peek(830)',
        f'2 poke45,{vartab & 0xFF:03d}:poke46,{vartab >> 8:03d}:clr',
        '10 poke53280,6:poke53281,0:print chr$(147)chr$(158)',
        f'20 print "{{down}}   {t}":print"   " ;:fori=1to{min(len(t), 30)}:print"{{CBM-T}}";:next:print',
        f'30 n={len(games)}:dim t$(n),f$(n),a(n)',
        '40 fori=1ton:readt$(i),f$(i),a(i)',
        '50 printchr$(5)"   "chr$(64+i)chr$(158)"  "t$(i):next',
        '60 print:printchr$(154)"   press a letter"',
        '70 getk$:ifk$=""then70',
        '80 k=asc(k$)-64:ifk<1ork>nthen70',
        '85 printchr$(147)chr$(158):print"{down}   loading ";t$(k)',
        '90 ifa(k)=0thenload f$(k),8',
        '95 poke828,73:poke829,a(k)-int(a(k)/256)*256:poke830,int(a(k)/256)',
        '96 load f$(k),8,1',
    ]
    ln = 1000
    for label, fname, sysaddr in games:
        lines.append(f'{ln} data "{c64_name(label)[:30]}","{fname}",{sysaddr}')
        ln += 10
    return "\n".join(lines) + "\n"


BASIC_START = 0x0801
MENU_BLOCKS = 4  # the generated MENU program, rounded up generously


def pack(items: list, budget: int) -> list[list]:
    """Split a side's games across as many disks as they need, in order.

    Keeping the original order matters: the label lists the games in the
    order they were on the disk, and that is the order to keep.
    """
    groups, current, used = [], [], 0
    for item in items:
        blocks = item[0][2]
        if current and used + blocks > budget:
            groups.append(current)
            current, used = [], 0
        current.append(item)
        used += blocks
    if current:
        groups.append(current)
    return groups


def build_menu_prg(label: str, games: list, tmp: Path, tag: str) -> Path:
    """Tokenise the menu twice: once to measure it, once to bake in its size."""
    bas, prg = tmp / f"menu{tag}.bas", tmp / f"menu{tag}.prg"

    def tokenise(vartab: int) -> int:
        bas.write_text(menu_basic(label, games, vartab), newline="\n")
        run(["petcat", "-w2", "-o", str(prg), "--", str(bas)])
        return BASIC_START + prg.stat().st_size - 2  # less the 2-byte load address

    first = tokenise(0)
    second = tokenise(first)
    if second != first:
        raise RuntimeError(f"menu length moved while baking in its own size: {first} -> {second}")
    return prg


def run(cmd: list[str]):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{r.stdout}{r.stderr}")
    return r.stdout


# --------------------------------------------------------------- catalog ---
def disk_folders() -> dict[str, str]:
    """One folder name per physical disk, reading like its label did."""
    catalog = json.loads(CATALOG.read_text())["disks"]
    out = {}
    for disk in catalog:
        titles = []
        for side in disk["sides"]:
            for t in side["titles"]:
                t = re.sub(r"^[A-Z]=", "", t).strip()
                if t not in titles:
                    titles.append(t)
        out[disk["id"]] = safe_filename(f"{disk['id']} {', '.join(titles)}")
    return out


# ----------------------------------------------------------------- build ---
def build_side(sid: str, entry: dict, folder: Path, auto_menu: bool,
               manifest: list, cache: dict):
    file_items, whole, missing = [], [], []
    for it in entry["items"]:
        if it.get("skip"):
            continue
        if "whole_image" in it:
            whole.append(it)
        elif "src" in it:
            file_items.append(it)
        else:
            missing.append(it)
            manifest.append({"side": sid, "title": it["title"], "kind": "missing",
                             "why": it.get("todo", "no source")})

    if file_items or whole:
        folder.mkdir(parents=True, exist_ok=True)

    for it in whole:
        w = it["whole_image"]
        data = load_image_bytes(w["src"], w.get("member"))
        ext = image_ext(w["src"], w.get("member"), data)
        name = safe_filename(f"{sid} {it['title']}", 56) + f".{ext}"
        (folder / name).write_bytes(data)
        manifest.append({"side": sid, "title": it["title"], "image": name,
                         "folder": folder.name, "kind": "whole_image",
                         "note": it.get("note"),
                         "from": w["src"] + (f"::{w['member']}" if w.get("member") else "")})
        print(f"  + {name}  (whole image)")

    if not file_items:
        return

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        games, used, written, sources = [], set(), [], []
        for it in file_items:
            key = (it["src"], it.get("member"))
            if (it.get("member") or it["src"]).lower().endswith(".prg"):
                # A loose .prg is the game itself, with no disk around it.
                data = load_image_bytes(it["src"], it.get("member"))
            else:
                if key not in cache:
                    cache[key] = open_source(it["src"], it.get("member"))
                img = cache[key]
                ent = next((e for e in img.entries if e.name == it["file"]), None)
                if ent is None:
                    print(f"  ! {sid}: '{it['file']}' not in {it['src']}")
                    manifest.append({"side": sid, "title": it["title"], "kind": "missing",
                                     "why": f"file {it['file']!r} vanished from its source"})
                    continue
                data = img.read_file(ent)
            # A file that loads at $0801 is a BASIC stub and RUN starts it.
            # Anything else was lifted off an original disk and has to be
            # entered at the address it loads to.
            load_addr = data[0] | data[1] << 8
            # 0 means "lives at BASIC start, just load it and let it run";
            # anything else is the address to SYS into after loading.
            sysaddr = 0 if load_addr == BASIC_START else load_addr
            override = (it.get("start") or "").strip().lower()
            if override.startswith("sys"):
                sysaddr = int(re.sub(r"[^0-9]", "", override) or sysaddr)
            elif override == "run":
                sysaddr = 0
            start = "run" if sysaddr == 0 else f"sys {sysaddr}"
            fname = c64_name(it.get("as") or it["title"])
            while fname in used:
                fname = fname[:14] + str(len(used))
            used.add(fname)
            host = tmp / f"f{len(written)}.prg"
            host.write_bytes(data)
            written.append((host, fname, (len(data) + 253) // 254))
            games.append((it["title"], fname, sysaddr))
            sources.append({"title": it["title"], "file": fname, "note": it.get("note"),
                            "blocks": (len(data) + 253) // 254,
                            "load_addr": f"${load_addr:04x}", "start": start,
                            "from": it["src"] + (f"::{it['member']}" if it.get("member") else "")
                                    + f" :: {it['file']}"})
        if not games:
            return

        make_menu = entry.get("menu") or (auto_menu and len(games) > 1)
        label = entry.get("disk_name") or sid
        disk_id = re.sub(r"[^a-z0-9]", "", str(entry.get("disk_id", "")).lower())[:2] or "00"
        # The originals held these games uncracked; the copies we have carry
        # loader intros and are fatter, so a side that used to fit may not.
        budget = DISK_BLOCKS - (MENU_BLOCKS if make_menu else 0)
        groups = pack(list(zip(written, games, sources)), budget)
        if len(groups) > 1:
            print(f"  . {sid}: {sum(b for (_, _, b), _, _ in zip(written, games, sources))}"
                  f" blocks of games, splitting across {len(groups)} images")

        for n, group in enumerate(groups, 1):
            parts = [f for f, _, _ in group]
            gs = [g for _, g, _ in group]
            srcs = [c for _, _, c in group]
            if make_menu:
                prg = build_menu_prg(label, gs, tmp, str(n))
                parts = [(prg, "menu", (prg.stat().st_size + 253) // 254)] + parts
            total = sum(b for _, _, b in parts)
            suffix = f" ({n} of {len(groups)})" if len(groups) > 1 else ""
            stem = safe_filename(f"{sid} {', '.join(g[0] for g in gs)}", 56 - len(suffix))
            name = stem + suffix + ".d64"
            cmd = ["c1541", "-format", f"{c64_name(label)},{disk_id}", "d64", str(folder / name)]
            for host, fname, _ in parts:
                cmd += ["-write", str(host), fname]
            run(cmd)
            manifest.append({"side": sid, "title": ", ".join(g[0] for g in gs), "image": name,
                             "folder": folder.name, "kind": "menu" if make_menu else "files",
                             "blocks": total,
                             "load": 'LOAD"MENU",8,1' if make_menu else 'LOAD"*",8,1',
                             "contents": srcs})
            print(f"  + {name}  ({total} blocks{', menu' if make_menu else ''})")


def write_disks_md(manifest: list, out: Path):
    by_folder: dict[str, list] = {}
    for m in manifest:
        by_folder.setdefault(m.get("folder", "(not built)"), []).append(m)
    lines = ["# What is on the card", "",
             "One folder per original disk. `.d64` sides were rebuilt from single files;",
             "`.g64` and standalone `.d64` files are whole disks that needed a side to",
             "themselves - multi-load games, and originals nobody ever cracked down to one",
             "file. Every line says where the bytes came from.", ""]
    for folder in sorted(by_folder):
        lines.append(f"## {folder}")
        for m in by_folder[folder]:
            if m["kind"] == "missing":
                lines.append(f"- **{m['title']}** — not built: {m['why']}")
                continue
            head = f"- `{m['image']}`"
            if m["kind"] == "whole_image":
                lines.append(f"{head} — **{m['title']}**, whole image")
                lines.append(f"    - from `{m['from']}`")
                if m.get("note"):
                    lines.append(f"    - {m['note']}")
            else:
                kind = "menu disk" if m["kind"] == "menu" else "rebuilt side"
                lines.append(f"{head} — {kind}, {m['blocks']} blocks, `{m['load']}`")
                for c in m["contents"]:
                    lines.append(f"    - **{c['title']}** as `{c['file']}` ({c['blocks']} blk) "
                                 f"from `{c['from']}`")
                    if c.get("note"):
                        lines.append(f"        - {c['note']}")
        lines.append("")
    built = sum(1 for m in manifest if m["kind"] != "missing")
    gone = sum(1 for m in manifest if m["kind"] == "missing")
    lines.insert(2, f"{built} images built, {gone} titles with no source.\n")
    (out / "DISKS.md").write_text("\n".join(lines), encoding="utf-8")


CARD_README = """How to use this card
====================

One folder per original floppy, named the way its label reads. Inside a
folder, each file is one side of that disk.

  *.d64   a rebuilt side. Mount it, then:
            LOAD"MENU",8,1   and   RUN      if the side had a menu
            LOAD"*",8,1      and   RUN      otherwise
          A menu lists its games with a letter each; press the letter and
          the game loads and starts by itself.

  *.g64   an original disk, bit for bit, copy protection and all. These are
          games that were never cracked down to a single file, or that load
          more data while you play. Mount and:
            LOAD"*",8,1      and   RUN
          A few of these are the real original and may ask for something
          from the manual.

A side that came to more than one disk's worth is split into "(1 of 2)"
and "(2 of 2)" images, because the copies available today carry loader
intros the originals did not.

DISKS.md lists every image, what is on it, and which archive each file came
from. manifest.json is the same thing for a program to read - the disk
photos and the NFC cards will key off it.

Titles that could not be found are listed in DISKS.md too, so the gaps are
visible rather than silently missing.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selections", default=str(HERE / "selections.json"))
    ap.add_argument("--out", default=str(HERE.parent / "card"),
                    help="the folder to copy onto the Pi1541's SD card")
    ap.add_argument("--only", nargs="*", help="build only these side ids, e.g. D05-1")
    ap.add_argument("--auto-menu", action="store_true", help="add a menu to any side with 2+ games")
    args = ap.parse_args()
    need("c1541")
    need("petcat")
    sel = json.loads(Path(args.selections).read_text())
    folders = disk_folders()
    out = Path(args.out)
    if out.exists() and not args.only:
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    manifest, cache = [], {}
    for sid, entry in sel.items():
        if args.only and sid not in args.only:
            continue
        print(sid)
        folder = out / folders.get(sid.split("-")[0], sid.split("-")[0])
        try:
            build_side(sid, entry, folder, args.auto_menu, manifest, cache)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {sid} failed: {e}")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    write_disks_md(manifest, out)
    (out / "README.txt").write_text(CARD_README, encoding="utf-8")
    built = sum(1 for m in manifest if m["kind"] != "missing")
    print(f"\n{built} images -> {out}   ({sum(1 for m in manifest if m['kind'] == 'missing')} titles had no source)")


if __name__ == "__main__":
    main()
