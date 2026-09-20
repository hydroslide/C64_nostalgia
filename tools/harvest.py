#!/usr/bin/env python3
"""Index C64 disk-image collections and find candidate files for each game
listed in disk_catalog.json.

    python3 harvest.py index  /path/to/collection [/another ...]   -> index.jsonl
    python3 harvest.py match                                        -> candidates.json, report.md, selections.json (draft)

Indexing reads .d64/.d71/.d81 files, including ones inside .zip archives
(one level of nesting inside a zip is also handled). Re-running `index` only
re-reads files whose size/mtime changed.
"""
from __future__ import annotations

import argparse
import difflib
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path

from cbmimage import open_image

HERE = Path(__file__).resolve().parent
CATALOG = next(p for p in (HERE / "disk_catalog.json", HERE.parent / "disk_catalog.json") if p.exists())
IMAGE_EXT = {".d64", ".d71", ".d81"}
SKIPPED_EXT = {".g64", ".nib", ".g71", ".p64"}  # GCR formats: not parsed (yet)

# Games that load extra files while running, or need a whole disk/side to
# themselves. For these the best move is to copy a complete cracked image
# rather than pulling one file onto a shared disk.
MULTILOAD = {
    "world games", "summer games", "summer games ii", "winter games",
    "gauntlet", "gauntlet: the deeper dungeons", "flight simulator ii",
    "adventure construction set", "f-15 strike eagle", "dragon's lair",
    "mail order monsters", "lords of conquest", "hacker ii",
    "dragonriders of pern", "kermit's electronic storymaker", "songwriter",
    "leader board", "double dragon", "robocop", "the factory",
    "mystery at pinecrest manor", "stickybear typing", "donald duck's playground",
    "the dolphin's rune", "shadowfire", "fist: the legend continues",
    "raid over moscow", "druid", "paperboy", "wargames", "hat trick",
    "10th frame", "spelunker", "hesgames", "star wars",
}

# Extra spellings seen in real C64 directories (all compared after normalise()).
ALIASES = {
    "H.E.R.O.": ["hero"],
    "Ghosts'n Goblins": ["ghostsngoblins", "ghostsgoblins", "gng", "ghosts n gob"],
    "Rambo: First Blood Part II": ["rambo", "rambo ii", "rambo 2", "first blood"],
    "Pitfall II: Lost Caverns": ["pitfall ii", "pitfall 2", "pitfall2"],
    "Pitfall!": ["pitfall"],
    "B.C.'s Quest for Tires": ["bc quest", "quest for tires", "bcs quest", "bc"],
    "Mr. Robot and His Robot Factory": ["mr robot", "mrrobot"],
    "The Way of the Exploding Fist": ["exploding fist", "way of the exploding fist", "fist"],
    "Fist: The Legend Continues": ["fist ii", "fist 2", "fist2", "legend continues"],
    "Mr. Do!": ["mr do", "mister do"],
    "World Karate Championship": ["karate champ", "karate", "world karate"],
    "Boulder Dash II": ["boulderdash ii", "boulder dash 2", "boulderdash 2", "bd2"],
    "Robin of the Wood": ["robin wood", "robin of the wood"],
    "Beyond the Ice Palace": ["ice palace"],
    "Kermit's Electronic Storymaker": ["kermit", "storymaker"],
    "Gauntlet: The Deeper Dungeons": ["deeper dungeons", "gauntlet dd"],
    "Mystery at Pinecrest Manor": ["pinecrest", "pinecrest manor"],
    "Flight Simulator II": ["flight sim", "flight simulator", "fs2", "fsii"],
    "Dino Eggs": ["dinoeggs", "dino egg"],
    "Donkey Kong": ["dkong", "donkeykong"],
    "Mario Bros.": ["mario bros", "mariobros"],
    "Mario's Brewery": ["marios brewery"],
    "Mr. Wimpy": ["mr wimpy", "wimpy"],
    "Up'n Down": ["up n down", "upndown", "up and down"],
    "Danger Mouse in the Black Forest Chateau": ["danger mouse", "dangermouse", "d mouse"],
    "Stickybear Typing": ["stickybear", "sticky bear"],
    "Leader Board": ["leaderboard", "leader board golf"],
    "10th Frame": ["tenth frame", "10th frame"],
    "Hat Trick": ["hattrick"],
    "Slap Shot": ["slapshot"],
    "Pharaoh's Curse": ["pharaohs curse", "pharos curse"],
    "Cohen's Towers": ["cohens towers", "cohns towers", "cohen"],
    "Kung-Fu Master": ["kung fu master", "kungfu master"],
    "Dragon's Lair": ["dragons lair"],
    "Dragonskulle": ["dragon skull", "dragonskull"],
    "Wizard's Lair": ["wizards lair"],
    "Dragonriders of Pern": ["dragon riders", "pern"],
    "Big Top Barney": ["bigtop barney", "barney"],
    "WarGames": ["war games"],
    "Rocketball": ["rocket ball"],
    "The Dolphin's Rune": ["dolphins rune", "dolphin"],
    "Turtle Toyland Jr.": ["turtle toyland", "toyland"],
    "Summer Games II": ["summer games 2", "summergames2"],
}

TAG_RE = re.compile(r"(/|\s-\s|\s+by\s+|\s\+\d|\+\d).*$")  # cracker / trainer tags


def normalise(s: str) -> str:
    s = s.lower().replace("&", "and")
    s = re.sub(r"\bthe\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def clean_filename(name: str) -> str:
    """Drop cracker tags like 'GREEN BERET/TCN' or 'GHOSTS'N'GOB/FBG'."""
    return TAG_RE.sub("", name.strip().lower())


# ---------------------------------------------------------------- indexing --
def iter_images(root: Path):
    for dirpath, _, files in os.walk(root):
        for fn in files:
            p = Path(dirpath) / fn
            ext = p.suffix.lower()
            if ext in IMAGE_EXT:
                yield p, None, lambda p=p: p.read_bytes()
            elif ext == ".zip":
                yield p, "__zip__", None
            elif ext in SKIPPED_EXT:
                yield p, "__skip__", None


def zip_members(data: bytes, prefix: str = ""):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            ext = Path(info.filename).suffix.lower()
            if ext in IMAGE_EXT:
                yield prefix + info.filename, z.read(info)
            elif ext == ".zip" and not prefix:
                yield from zip_members(z.read(info), prefix=info.filename + "::")


def describe(data: bytes) -> dict:
    im = open_image(data)
    return {
        "fmt": im.fmt, "disk_name": im.disk_name, "disk_id": im.disk_id,
        "files": [[e.name, e.ftype, e.blocks] for e in im.entries],
    }


def cmd_index(args):
    out = HERE / "index.jsonl"
    cache = {}
    if out.exists():
        for line in out.open():
            r = json.loads(line)
            cache.setdefault((r["src"], r["stamp"]), []).append(r)
    records, stats = [], {"images": 0, "zips": 0, "errors": 0, "skipped_gcr": 0, "cached": 0}
    for root in args.roots:
        for path, kind, _ in iter_images(Path(root).expanduser()):
            st = path.stat()
            stamp = f"{st.st_size}:{int(st.st_mtime)}"
            key = (str(path), stamp)
            if key in cache:
                records += cache[key]
                stats["cached"] += 1
                continue
            if kind == "__skip__":
                stats["skipped_gcr"] += 1
                continue
            try:
                if kind == "__zip__":
                    stats["zips"] += 1
                    for member, data in zip_members(path.read_bytes()):
                        try:
                            records.append({"src": str(path), "member": member, "stamp": stamp, **describe(data)})
                            stats["images"] += 1
                        except Exception as e:  # noqa: BLE001
                            stats["errors"] += 1
                            if args.verbose:
                                print(f"  ! {path}::{member}: {e}", file=sys.stderr)
                else:
                    records.append({"src": str(path), "member": None, "stamp": stamp, **describe(path.read_bytes())})
                    stats["images"] += 1
            except Exception as e:  # noqa: BLE001
                stats["errors"] += 1
                if args.verbose:
                    print(f"  ! {path}: {e}", file=sys.stderr)
    with out.open("w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"indexed {len(records)} images -> {out}  {stats}")


# ---------------------------------------------------------------- matching --
def title_keys(title: str) -> list[str]:
    keys = {normalise(title)}
    base = re.split(r"[:(]", title)[0]
    keys.add(normalise(base))
    for a in ALIASES.get(title, []):
        keys.add(normalise(a))
    keys = {k for k in keys if len(k) >= 2}
    # C64 names are max 16 chars, so also try the truncated form
    keys |= {k[:14] for k in keys if len(k) > 14}
    return sorted(keys, key=len, reverse=True)


def score(keys: list[str], cand: str) -> float:
    c = normalise(clean_filename(cand))
    if not c:
        return 0.0
    best = 0.0
    for k in keys:
        if c == k:
            return 1.0
        r = difflib.SequenceMatcher(None, k, c).ratio()
        if len(k) >= 4 and (c.startswith(k) or k.startswith(c) and len(c) >= max(4, len(k) - 4)):
            r = max(r, 0.9)
        elif len(k) >= 5 and k in c:
            r = max(r, 0.85)
        best = max(best, r)
    return best


def cmd_match(args):
    catalog = json.loads(CATALOG.read_text())["disks"]
    if not (HERE / "index.jsonl").exists():
        sys.exit("no index.jsonl yet - run: python3 harvest.py index <collection folders>")
    index = [json.loads(l) for l in (HERE / "index.jsonl").open()]
    print(f"{len(index)} images in index")

    results = {}
    for disk in catalog:
        for side in disk["sides"]:
            sid = f'{disk["id"]}-{side["side"]}'
            items = []
            for title in side["match"]:
                t = title.lstrip("?")
                keys = title_keys(t)
                hits = []
                for rec in index:
                    ds = score(keys, rec["disk_name"])
                    for fname, ftype, blocks in rec["files"]:
                        if ftype not in ("PRG", "USR") or blocks == 0:
                            continue
                        s = score(keys, fname)
                        if s >= args.threshold:
                            hits.append({"score": round(s, 3), "file": fname, "blocks": blocks,
                                         "src": rec["src"], "member": rec["member"],
                                         "disk_name": rec["disk_name"], "disk_score": round(ds, 3),
                                         "n_files": len(rec["files"])})
                # rank: score, then disk-name agreement, then prefer bigger files (the game, not the intro)
                hits.sort(key=lambda h: (h["score"], h["disk_score"], h["blocks"]), reverse=True)
                items.append({"title": t, "uncertain": title.startswith("?"),
                              "multiload": t.lower() in MULTILOAD, "keys": keys,
                              "hits": hits[: args.top]})
            results[sid] = {"disk": disk["id"], "side": side["side"], "menu": side.get("menu", False),
                            "labels": side["titles"], "items": items}

    (HERE / "candidates.json").write_text(json.dumps(results, indent=1))
    write_report(results)
    write_selection_draft(results)


def write_report(results):
    lines = ["# Harvest report", "",
             "Top candidates per title. **M** = multi-load game (copy a whole image, not one file).", ""]
    found = total = 0
    for sid, r in results.items():
        lines.append(f"## {sid}  —  {', '.join(r['labels'])}" + ("  (menu disk)" if r["menu"] else ""))
        for it in r["items"]:
            total += 1
            flag = " **M**" if it["multiload"] else ""
            if not it["hits"]:
                lines.append(f"- **{it['title']}**{flag}: _no candidates_")
                continue
            found += 1
            lines.append(f"- **{it['title']}**{flag}")
            for h in it["hits"][:5]:
                where = h["src"] + (f" :: {h['member']}" if h["member"] else "")
                lines.append(f"    - {h['score']:.2f}  `{h['file']}` ({h['blocks']} blk) on \"{h['disk_name']}\" — {where}")
        lines.append("")
    lines.insert(2, f"Found candidates for {found} of {total} titles.\n")
    (HERE / "report.md").write_text("\n".join(lines))
    print(f"candidates for {found}/{total} titles -> report.md, candidates.json")


def write_selection_draft(results):
    """Best guess per title. Edit selections.json by hand, then run build.py."""
    path = HERE / "selections.json"
    if path.exists():
        path = HERE / "selections.draft.json"
    sel = {}
    for sid, r in results.items():
        entry = {"menu": r["menu"], "disk_name": f"{r['disk']} side {r['side']}"[:16], "disk_id": r["disk"][-2:], "items": []}
        for it in r["items"]:
            h = it["hits"][0] if it["hits"] else None
            item = {"title": it["title"], "start": "run"}
            if h is None:
                item["todo"] = "no candidate found"
            elif it["multiload"]:
                item["whole_image"] = {"src": h["src"], "member": h["member"], "disk_name": h["disk_name"]}
            else:
                item.update({"src": h["src"], "member": h["member"], "file": h["file"], "blocks": h["blocks"]})
            entry["items"].append(item)
        sel[sid] = entry
    path.write_text(json.dumps(sel, indent=1))
    print(f"draft selections -> {path.name} (review before building)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("index"); a.add_argument("roots", nargs="+"); a.add_argument("-v", "--verbose", action="store_true")
    b = sub.add_parser("match"); b.add_argument("--threshold", type=float, default=0.8); b.add_argument("--top", type=int, default=10)
    args = ap.parse_args()
    {"index": cmd_index, "match": cmd_match}[args.cmd](args)


if __name__ == "__main__":
    main()
