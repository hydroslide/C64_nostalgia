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
import hashlib
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


# --------------------------------------------------------------- menus -----
# PETSCII colour codes, as CHR$ takes them.
BLACK, WHITE, CYAN, PURPLE, GREEN, BLUE, YELLOW = 144, 5, 159, 156, 30, 31, 158
ORANGE, LT_RED, DK_GREY, GREY, LT_GREEN, LT_BLUE, LT_GREY = 129, 150, 151, 152, 153, 154, 155
RVS_ON, RVS_OFF = 18, 146

# (border, background, title, item, letter, prompt). Backgrounds are kept dark
# and text light, so every one of these is actually readable on a CRT.
PALETTES = [
    (6, 0, YELLOW, WHITE, LT_GREEN, LT_BLUE),
    (11, 0, LT_GREEN, LT_GREY, WHITE, YELLOW),
    (14, 6, WHITE, YELLOW, LT_GREY, LT_GREEN),
    (2, 0, LT_RED, WHITE, YELLOW, CYAN),
    (5, 0, LT_GREEN, CYAN, WHITE, YELLOW),
    (12, 11, WHITE, YELLOW, LT_GREEN, LT_BLUE),
    (4, 0, CYAN, WHITE, PURPLE, YELLOW),
    (0, 6, CYAN, WHITE, YELLOW, LT_GREY),
    (9, 0, ORANGE, LT_GREY, YELLOW, WHITE),
    (3, 0, CYAN, LT_GREEN, WHITE, YELLOW),
]

STYLES = ["plain", "ruled", "boxed", "cracked"]


def assign_styles(side_ids: list[str]) -> dict[str, str]:
    """Deal the four styles round-robin across the sides that get a menu.

    Leaving it to the digest is fine in principle and poor in practice: there
    are only a handful of menu disks, and a hash happily gives three of them
    the same look. Dealing them out guarantees the variety.
    """
    return {sid: STYLES[i % len(STYLES)] for i, sid in enumerate(sorted(side_ids))}


def theme_for(side_id: str, style: str | None = None) -> dict:
    """Pick a look for one side, the same one every build.

    The disks did not all look alike - some had a plain typed list, some had
    whatever the cracking group had bolted on that month - so the menus
    should not either. A digest of the side id spreads the styles and
    palettes properly (adding up the characters of "D31" and "D40" gives the
    same number) and keeps a rebuild from reshuffling them.
    """
    h = int(hashlib.md5(side_id.encode()).hexdigest()[:8], 16)
    pal = PALETTES[(h >> 3) % len(PALETTES)]
    return {"style": style or STYLES[h % len(STYLES)],
            "border": pal[0], "background": pal[1],
            "title": pal[2], "item": pal[3], "letter": pal[4], "prompt": pal[5]}


def bar_line(ln: int, colour: int) -> str:
    """A solid 39-character bar in reverse video - the cheapest raster bar."""
    return f'{ln} printchr$({colour})chr$({RVS_ON});:fori=1to39:print" ";:next:printchr$({RVS_OFF})'


def header_lines(style: str, t: str, th: dict) -> list[str]:
    """Lines 20-29: whatever this disk's menu calls itself."""
    width = min(len(t), 30)
    if style == "plain":
        return [f'20 print"{{down}}   "chr$({th["title"]})"{t}"']
    if style == "ruled":
        return [f'20 print"{{down}}   "chr$({th["title"]})"{t}"',
                f'22 print"   ";:fori=1to{width}:print"{{CBM-T}}";:next:print']
    if style == "boxed":
        return [bar_line(20, th["title"]),
                f'22 print"{{down}}"chr$({th["title"]})"   {t}"',
                bar_line(24, th["title"]),
                '26 print']
    # cracked
    return [bar_line(20, th["letter"]),
            f'22 printchr$({th["title"]})"   *** {t} ***"',
            bar_line(24, th["letter"]),
            '26 print']


def prompt_lines(style: str, th: dict) -> list[str]:
    if style == "cracked":
        return ['60 print:printchr$(%d)"   < press a letter to load >"' % th["prompt"]]
    if style == "boxed":
        return ['60 print:printchr$(%d)"   select a game:"' % th["prompt"]]
    return ['60 print:printchr$(%d)"   press a letter"' % th["prompt"]]


def item_line(style: str, th: dict) -> str:
    sep = '")  "' if style in ("cracked", "boxed") else '"   "'
    return (f'50 printchr$({th["letter"]})"   "chr$(64+i)'
            f'chr$({th["item"]}){sep}t$(i):next')


def menu_basic(title: str, games: list, theme: dict, vartab: int = 0) -> str:
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

    The tape buffer at 828 holds the flag rather than a variable because
    line 2 has to CLR, which would wipe a variable.

    Line 2 exists because LOAD"MENU",8,1 - which is what the original
    sleeves say - puts the bytes in memory without telling BASIC where the
    program now ends. READ then finds no DATA and the first variable
    assigned lands on top of the program. Poking the end-of-program pointer
    measured at build time fixes both. The digits are zero-padded so filling
    them in cannot change the program's length.
    """
    t = c64_name(title)[:30]
    style = theme["style"]
    lines = [
        '1 ifpeek(828)=73thenpoke828,0:sys peek(829)+256*peek(830)',
        f'2 poke45,{vartab & 0xFF:03d}:poke46,{vartab >> 8:03d}:clr',
        f'10 poke53280,{theme["border"]}:poke53281,{theme["background"]}:print chr$(147)',
    ]
    lines += header_lines(style, t, theme)
    lines += [
        f'30 n={len(games)}:dim t$(n),f$(n),a(n)',
        '40 fori=1ton:readt$(i),f$(i),a(i)',
        item_line(style, theme),
    ]
    lines += prompt_lines(style, theme)
    lines += [
        '70 getk$:ifk$=""then70',
        '80 k=asc(k$)-64:ifk<1ork>nthen70',
        f'85 printchr$(147)chr$({theme["title"]}):print"{{down}}   loading ";t$(k)',
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


def build_menu_prg(label: str, games: list, theme: dict, tmp: Path, tag: str) -> Path:
    """Tokenise the menu twice: once to measure it, once to bake in its size."""
    bas, prg = tmp / f"menu{tag}.bas", tmp / f"menu{tag}.prg"

    def tokenise(vartab: int) -> int:
        bas.write_text(menu_basic(label, games, theme, vartab), newline="\n")
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
FOLDER_LIMIT = 58


def disk_folders() -> dict[str, str]:
    """One folder name per physical disk, reading like its label did.

    Some labels list eight games, which is longer than anything wants to
    show. Rather than cutting mid-word, titles are added while they fit and
    the rest are counted - "D03 Action Biker, Battlezone, Decathlon +5 more"
    reads like a label; a hard truncation does not.
    """
    catalog = json.loads(CATALOG.read_text())["disks"]
    out = {}
    for disk in catalog:
        titles = []
        for side in disk["sides"]:
            for t in side["titles"]:
                t = re.sub(r"^[A-Z]=", "", t).strip()
                if t and t not in titles:
                    titles.append(t)
        name, shown = disk["id"], 0
        for t in titles:
            candidate = f"{name}{',' if shown else ''} {t}"
            if len(candidate) > FOLDER_LIMIT:
                break
            name, shown = candidate, shown + 1
        if shown < len(titles):
            name += f" +{len(titles) - shown} more"
        out[disk["id"]] = safe_filename(name, 70)
    return out


def whole_image_load(data: bytes, ext: str) -> dict:
    """Work out what to actually type to start a whole image.

    LOAD"*",8,1 gets the first file onto the machine; whether RUN then starts
    it depends on where that file lives. A file at BASIC start is a stub and
    RUN is right; anything else needs a SYS, and telling someone to type RUN
    when it cannot work is worse than saying nothing.
    """
    if ext == "g64":
        # A GCR image is usually a protected original with its own loader;
        # there is nothing dependable to read a load address out of.
        return {"load": 'LOAD"*",8,1', "start": "run"}
    try:
        img = open_image(data, lenient=True)
        first = next(e for e in img.entries if e.ftype == "PRG" and e.blocks)
        body = img.read_file(first)
        addr = body[0] | body[1] << 8
    except Exception:  # noqa: BLE001
        return {"load": 'LOAD"*",8,1', "start": "run"}
    if addr == BASIC_START:
        return {"load": f'LOAD"{first.name}",8', "start": "run"}
    if 0x0300 <= addr <= 0x0334:
        # Loading over the BASIC vectors at $0300 is the old autostart
        # trick: the next thing BASIC does goes through the vector and into
        # the loader, so the LOAD itself starts the game.
        return {"load": f'LOAD"{first.name}",8,1', "start": "(starts by itself)"}
    return {"load": f'LOAD"{first.name}",8,1', "start": f"sys {addr}"}


# ----------------------------------------------------------------- build ---
def build_side(sid: str, entry: dict, folder: Path, auto_menu: bool,
               manifest: list, cache: dict, style: str | None = None):
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
                             "folder": folder.name,
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
                         **whole_image_load(data, ext),
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
                    manifest.append({"side": sid, "title": it["title"], "kind": "missing", "folder": folder.name,
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
                prg = build_menu_prg(label, gs, theme_for(sid, style), tmp, str(n))
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
                             "menu_style": theme_for(sid, style)["style"] if make_menu else None,
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
                cmd = m.get("load") or 'LOAD"*",8,1'
                start = m.get("start", "run")
                lines.append(f"    - `{cmd}`" +
                             (f" - {start}" if start.startswith("(")
                              else f" then `{start}`"))
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

DISKS.md lists every image, what is on it, the exact line to type to start
it, and which archive each file came from. Check it for the whole-disk
images: a few do not load at BASIC start, so RUN does nothing and they want
a SYS instead. manifest.json is the same thing for a program to read - the
disk photos and the NFC cards key off it.

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
    styles = assign_styles([sid for sid, e in sel.items()
                            if e.get("menu") or (args.auto_menu and len(e["items"]) > 1)])
    for sid, entry in sel.items():
        if args.only and sid not in args.only:
            continue
        print(sid)
        folder = out / folders.get(sid.split("-")[0], sid.split("-")[0])
        try:
            build_side(sid, entry, folder, args.auto_menu, manifest, cache, styles.get(sid))
        except Exception as e:  # noqa: BLE001
            print(f"  ! {sid} failed: {e}")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    write_disks_md(manifest, out)
    (out / "README.txt").write_text(CARD_README, encoding="utf-8")
    built = sum(1 for m in manifest if m["kind"] != "missing")
    print(f"\n{built} images -> {out}   ({sum(1 for m in manifest if m['kind'] == 'missing')} titles had no source)")


if __name__ == "__main__":
    main()
