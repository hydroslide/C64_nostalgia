#!/usr/bin/env python3
"""Index C64 disk-image collections and find candidate files for each game
listed in disk_catalog.json.

    python3 harvest.py index  /path/to/collection [/another ...]   -> index.jsonl
    python3 harvest.py match                                        -> candidates.json, report.md, selections.json (draft)

Indexing reads:
  * .d64/.d71/.d81 sector images (near-miss sizes are trimmed or padded);
  * .g64 GCR dumps, decoded back to sectors by `g64.py` — this is what makes
    the C64 Preservation Project set searchable;
  * loose .prg files, matched on their filename;
  * any of the above inside .zip archives (one level of nesting too).

Re-running `index` only re-reads files whose size/mtime changed.
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

import g64
from cbmimage import open_image

HERE = Path(__file__).resolve().parent
CATALOG = next(p for p in (HERE / "disk_catalog.json", HERE.parent / "disk_catalog.json") if p.exists())
IMAGE_EXT = {".d64", ".d71", ".d81"}
GCR_EXT = {".g64"}          # decoded back to sectors by g64.py
PRG_EXT = {".prg"}          # loose single-file games, matched on filename
SKIPPED_EXT = {".nib", ".nbz", ".g71", ".p64", ".d80", ".d82"}

# "..._s1[epyx_1984]" — which side of a multi-disk release a file is.
SIDE_RE = re.compile(r"[_ ]s(\d)(?=[\[(._ ]|$)", re.I)

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
    "B.C.'s Quest for Tires": ["bc quest", "quest for tires", "bcs quest"],
    "Mr. Robot and His Robot Factory": ["mr robot", "mrrobot"],
    "The Way of the Exploding Fist": ["exploding fist", "way of the exploding fist"],
    "Fist: The Legend Continues": ["fist ii", "fist 2", "fist2", "legend continues"],
    "Mr. Do!": ["mr do", "mister do"],
    "World Karate Championship": ["karate champ", "world karate"],
    "Boulder Dash II": ["boulderdash ii", "boulder dash 2", "boulderdash 2", "bd2"],
    "Robin of the Wood": ["robin wood", "robin of the wood"],
    "Beyond the Ice Palace": ["ice palace"],
    "Kermit's Electronic Storymaker": ["storymaker", "kermits electronic storymaker"],
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
    "Cohen's Towers": ["cohens towers", "cohns towers"],
    "Kung-Fu Master": ["kung fu master", "kungfu master"],
    "Dragon's Lair": ["dragons lair"],
    "Dragonskulle": ["dragon skull", "dragonskull"],
    "Wizard's Lair": ["wizards lair"],
    "Dragonriders of Pern": ["dragon riders", "pern"],
    "Big Top Barney": ["bigtop barney"],
    "WarGames": ["war games"],
    "Rocketball": ["rocket ball"],
    "The Dolphin's Rune": ["dolphins rune"],
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
def stem_title(name: str) -> str:
    """Turn a collection filename into something matchable.

    `world_games[epyx_1984](pal)(!).g64` becomes `world games`: the bracketed
    publisher/year and the parenthesised dump notes go, underscores become
    spaces.
    """
    s = name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    s = re.sub(r"\.[a-z0-9]{1,4}$", "", s, flags=re.I)
    s = SIDE_RE.sub("", s)
    s = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", s)
    return re.sub(r"\s+", " ", s.replace("_", " ").replace("-", " ")).strip()


def stem_side(name: str):
    m = SIDE_RE.search(name)
    return int(m.group(1)) if m else None


def prg_record(name: str, size: int) -> dict:
    """A loose .prg is indexed as a one-file pseudo-image."""
    return {"kind": "prg", "fmt": "prg", "disk_name": "", "disk_id": "",
            "files": [[stem_title(name).upper()[:16], "PRG", max(1, (size + 253) // 254)]]}


def describe(name: str, data: bytes) -> dict:
    ext = Path(name).suffix.lower()
    if ext in PRG_EXT:
        if len(data) < 3:
            raise ValueError("empty prg")
        return prg_record(name, len(data))
    if ext in GCR_EXT:
        # A heavily protected original often has no readable directory at
        # all. It still mounts and runs on a Pi1541, so keep it as something
        # we can offer whole, just with nothing to look inside.
        try:
            im = open_image(g64.to_d64(data, only_track=18))
        except Exception:
            im = None
        if im is None or not im.entries:
            return {"kind": "g64", "fmt": "g64", "disk_name": im.disk_name if im else "",
                    "disk_id": "", "files": []}
        kind = "g64"
    else:
        im = open_image(data, lenient=True)
        kind = "disk"
    return {"kind": kind, "fmt": im.fmt, "disk_name": im.disk_name, "disk_id": im.disk_id,
            "files": [[e.name, e.ftype, e.blocks] for e in im.entries]}


def iter_sources(root: Path):
    """Yield (path, how) for everything worth opening under `root`."""
    for dirpath, _, files in os.walk(root):
        for fn in files:
            p = Path(dirpath) / fn
            ext = p.suffix.lower()
            if ext in IMAGE_EXT or ext in GCR_EXT or ext in PRG_EXT:
                yield p, "direct"
            elif ext == ".zip":
                yield p, "zip"
            elif ext in SKIPPED_EXT:
                yield p, "skip"


def zip_members(data: bytes, prefix: str = ""):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            ext = Path(info.filename).suffix.lower()
            if ext in IMAGE_EXT or ext in GCR_EXT or ext in PRG_EXT:
                yield prefix + info.filename, z.read(info)
            elif ext == ".zip" and not prefix:
                yield from zip_members(z.read(info), prefix=info.filename + "::")


KIND_STAT = {"disk": "disks", "g64": "g64", "prg": "prgs"}


def cmd_index(args):
    out = Path(args.index)
    cache = {}
    if out.exists() and not args.rebuild:
        for line in out.open(encoding="utf-8"):
            r = json.loads(line)
            cache.setdefault((r["src"], r["stamp"]), []).append(r)
    records = []
    stats = {"disks": 0, "g64": 0, "prgs": 0, "zips": 0, "errors": 0, "skipped": 0, "cached": 0}
    seen = set()
    for root in args.roots:
        for path, how in iter_sources(Path(root).expanduser()):
            if str(path) in seen:
                continue
            seen.add(str(path))
            st = path.stat()
            stamp = f"{st.st_size}:{int(st.st_mtime)}"
            if (str(path), stamp) in cache:
                hit = cache[(str(path), stamp)]
                records += hit
                stats["cached"] += len(hit)
                continue
            if how == "skip":
                stats["skipped"] += 1
                continue
            try:
                if how == "zip":
                    stats["zips"] += 1
                    members = list(zip_members(path.read_bytes()))
                else:
                    members = [(None, path.read_bytes())]
            except Exception as e:  # noqa: BLE001
                stats["errors"] += 1
                if args.verbose:
                    print(f"  ! {path}: {e}", file=sys.stderr)
                continue
            for member, data in members:
                label = member or path.name
                try:
                    rec = describe(label, data)
                except Exception as e:  # noqa: BLE001
                    stats["errors"] += 1
                    if args.verbose:
                        where = f"{path}::{member}" if member else str(path)
                        print(f"  ! {where}: {e}", file=sys.stderr)
                    continue
                rec.update({"src": str(path), "member": member, "stamp": stamp,
                            "stem": stem_title(label), "side": stem_side(label)})
                records.append(rec)
                stats[KIND_STAT[rec["kind"]]] += 1
    with out.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"indexed {len(records)} sources -> {out}  {stats}")


# ---------------------------------------------------------------- matching --
def title_keys(title: str) -> list[str]:
    keys = {normalise(title)}
    base = re.split(r"[:(]", title)[0]
    keys.add(normalise(base))
    for a in ALIASES.get(title, []):
        keys.add(normalise(a))
    # two-letter keys ("BC") match half the collection; require three
    keys = {k for k in keys if len(k) >= 3}
    # C64 names are max 16 chars, so also try the truncated form
    keys |= {k[:14] for k in keys if len(k) > 14}
    return sorted(keys, key=len, reverse=True)


def norm_key(s: str) -> str:
    return normalise(clean_filename(s))


def scorer(keys: list[str], threshold: float):
    """Build a function that scores one already-normalised candidate string.

    difflib is by far the slowest part of a match run, so each key keeps its
    own SequenceMatcher (which caches the key side) and two exact upper
    bounds on `ratio` reject most pairs before difflib is asked at all.
    """
    prepared = []
    for k in keys:
        sm = difflib.SequenceMatcher(None)
        sm.set_seq2(k)
        prepared.append((k, len(k), sm))

    def run(c: str) -> float:
        if not c:
            return 0.0
        best, lc = 0.0, len(c)
        for k, lk, sm in prepared:
            if c == k:
                return 1.0
            r = 0.0
            if lk >= 4 and (c.startswith(k) or (k.startswith(c) and lc >= max(4, lk - 4))):
                r = 0.9
            elif lk >= 5 and k in c:
                r = 0.85
            # ratio() can never beat 2*min/total, and quick_ratio bounds it too
            if 2 * min(lk, lc) / (lk + lc) >= threshold:
                sm.set_seq1(c)
                if sm.quick_ratio() >= threshold:
                    r = max(r, sm.ratio())
            best = max(best, r)
        return best

    return run


# Junk that sits on cracked disks next to the game itself.
NOISE_RE = re.compile(r"(intro|note|doc|instr|readme|crack|trainer|loader|boot|cheat|"
                      r"hiscore|highscore|score|music|demo|preview|advert)", re.I)

# Copy-protection parameter and backup-tool disks. These carry a one-block
# file named after all but every game ever released - "GHOSTBUSTERS" on a
# Kracker Jax disk is a parameter for copying it, not the game. They score a
# perfect name match and are never what we want.
PARAM_SRC_RE = re.compile(r"(kracker.?jax|fast.?hack|hack.?em|param|maverick|"
                          r"renegade|di.?sector|burst.?nibbler|super.?kit|"
                          r"copy.?(ii|2|star)|nibbler|toolkit|unprotect|rapidlok)", re.I)

# Below this a "game" is almost always a parameter, a loader stub or a note.
MIN_GAME_BLOCKS = 12

VERIFIED_RE = re.compile(r"\(!\)")  # C64 Preservation Project: verified good dump


def file_penalty(name: str) -> float:
    """Push cracker intros and doc files below the real game."""
    return 0.06 if NOISE_RE.search(name) else 0.0


def is_param_source(rec: dict) -> bool:
    where = f"{rec.get('stem', '')} {rec['disk_name']} {rec.get('member') or ''} {rec['src']}"
    return bool(PARAM_SRC_RE.search(where))


def is_verified(rec: dict) -> bool:
    return bool(VERIFIED_RE.search(f"{rec.get('member') or ''}{rec['src']}"))


def source_rank(rec: dict) -> int:
    """Prefer sources that are easy to reuse. Higher is better.

    A cracked .d64 gives files that copy straight onto a menu disk; a loose
    .prg is one game with no directory to cross-check against; a .g64 is an
    unbroken original, perfect to mount whole but usually impossible to pull
    single files out of.
    """
    return {"disk": 3, "prg": 2, "g64": 1}[rec["kind"]]


class Lookup:
    """The index turned inside out: one entry per *distinct* name.

    The same filename shows up on hundreds of disks, so scoring names rather
    than (disk, file) pairs cuts the work by an order of magnitude.
    """

    def __init__(self, index: list):
        self.records = index
        self.files: dict[str, list] = {}
        self.wholes: dict[str, list] = {}
        for i, rec in enumerate(index):
            for name in {rec.get("stem", ""), rec["disk_name"]}:
                k = norm_key(name)
                if k:
                    self.wholes.setdefault(k, []).append(i)
            for fname, ftype, blocks in rec["files"]:
                if ftype not in ("PRG", "USR") or blocks == 0:
                    continue
                self.files.setdefault(norm_key(fname), []).append((i, fname, blocks))
        self.files.pop("", None)


def match_title(t: str, uncertain: bool, lookup: Lookup, args) -> dict:
    keys = title_keys(t)
    run = scorer(keys, args.threshold)

    whole_score: dict[int, float] = {}
    for k, idxs in lookup.wholes.items():
        s = run(k)
        if s >= args.threshold:
            for i in idxs:
                if s > whole_score.get(i, 0.0):
                    whole_score[i] = s

    image_hits = []
    for i, s in whole_score.items():
        rec = lookup.records[i]
        if rec["kind"] == "prg":
            continue
        image_hits.append({"score": round(s, 3), "stem": rec.get("stem", ""),
                           "disk_name": rec["disk_name"], "kind": rec["kind"],
                           "src": rec["src"], "member": rec["member"],
                           "side": rec.get("side"), "n_files": len(rec["files"]),
                           "rank": source_rank(rec), "ok_src": not is_param_source(rec),
                           "verified": is_verified(rec)})

    file_hits = []
    for k, occurrences in lookup.files.items():
        base = run(k)
        if base < args.threshold:
            continue
        for i, fname, blocks in occurrences:
            s = base - file_penalty(fname)
            if s < args.threshold:
                continue
            rec = lookup.records[i]
            file_hits.append({"score": round(s, 3), "file": fname, "blocks": blocks,
                              "src": rec["src"], "member": rec["member"], "kind": rec["kind"],
                              "disk_name": rec["disk_name"],
                              "disk_score": round(whole_score.get(i, 0.0), 3),
                              "n_files": len(rec["files"]), "rank": source_rank(rec),
                              "ok_src": not is_param_source(rec),
                              "big_enough": blocks >= MIN_GAME_BLOCKS})

    # Plausibility outranks similarity: a dozen disks hold a file with exactly
    # the right name, and the parameter disks among them all score 1.00.
    file_hits.sort(key=lambda h: (h["ok_src"], h["big_enough"], h["score"], h["rank"],
                                  h["disk_score"], h["blocks"]), reverse=True)
    image_hits.sort(key=lambda h: (h["ok_src"], h["score"], h["rank"], h["verified"],
                                   -(h["side"] or 1), h["n_files"]), reverse=True)
    return {"title": t, "uncertain": uncertain, "multiload": t.lower() in MULTILOAD,
            "keys": keys, "hits": file_hits[: args.top], "images": image_hits[: args.top]}


def cmd_match(args):
    catalog = json.loads(CATALOG.read_text())["disks"]
    index_path = Path(args.index)
    if not index_path.exists():
        sys.exit("no index yet - run: python3 harvest.py index <collection folders>")
    index = [json.loads(l) for l in index_path.open(encoding="utf-8")]
    lookup = Lookup(index)
    print(f"{len(index)} sources in index, "
          f"{len(lookup.files)} distinct filenames, {len(lookup.wholes)} distinct disk names")

    results = {}
    for disk in catalog:
        for side in disk["sides"]:
            sid = f'{disk["id"]}-{side["side"]}'
            items = [match_title(t.lstrip("?"), t.startswith("?"), lookup, args)
                     for t in side["match"]]
            results[sid] = {"disk": disk["id"], "side": side["side"], "menu": side.get("menu", False),
                            "labels": side["titles"], "load": side.get("load"), "items": items}

    (HERE / "candidates.json").write_text(json.dumps(results, indent=1))
    write_report(results)
    try:
        overrides = load_overrides(index)
    except OverrideError as e:
        sys.exit(f"overrides.json: {e}")
    print(f"{len(overrides)} hand-picked overrides")
    write_selection_draft(results, overrides)


# ------------------------------------------------------------- overrides --
OVERRIDES = HERE / "overrides.json"


class OverrideError(ValueError):
    pass


def load_overrides(index: list) -> dict:
    """Read overrides.json and resolve each entry against the index.

    Fuzzy matching gets a lot right and a few things confidently wrong: a
    Kracker Jax parameter named after the game, Rambo III for Rambo, Batman
    for Bagitman. Rather than hand-editing selections.json (which a re-match
    would overwrite), corrections live here and name their source by a piece
    of its path, so they stay readable and fail loudly if the collection
    moves.
    """
    if not OVERRIDES.exists():
        return {}
    raw = json.loads(OVERRIDES.read_text())
    out = {}
    for scope in ("by_title", "by_side"):
        for outer, entries in raw.get(scope, {}).items():
            for title, spec in entries.items() if scope == "by_side" else [(outer, entries)]:
                key = (scope, outer, title) if scope == "by_side" else (scope, title, None)
                out[key] = resolve_override(spec, index, f"{outer}/{title}")
    return out


def find_record(index: list, needle: str, label: str) -> dict:
    hay = needle.lower()
    hits = [r for r in index
            if hay in (r["src"] + "::" + (r["member"] or "")).lower().replace("\\", "/")]
    if not hits:
        raise OverrideError(f"{label}: nothing in the index matches {needle!r}")
    srcs = {(r["src"], r["member"]) for r in hits}
    if len(srcs) > 1:
        raise OverrideError(f"{label}: {needle!r} matches {len(srcs)} sources, e.g. "
                            + ", ".join(sorted(f"{a}::{b}" for a, b in srcs)[:3]))
    return hits[0]


def resolve_override(spec: dict, index: list, label: str) -> dict:
    item = {k: v for k, v in spec.items()
            if k in ("start", "as", "note", "skip", "title")}
    if "unavailable" in spec:
        item["todo"] = spec["unavailable"]
        return item
    if "image" in spec:
        rec = find_record(index, spec["image"], label)
        item["whole_image"] = {"src": rec["src"], "member": rec["member"],
                               "disk_name": rec["disk_name"], "kind": rec["kind"]}
        return item
    if "file" in spec:
        where, fname = spec["file"]
        rec = find_record(index, where, label)
        match = [f for f in rec["files"] if f[0] == fname]
        if not match:
            names = ", ".join(sorted(f[0] for f in rec["files"])[:12])
            raise OverrideError(f"{label}: no file {fname!r} on that source. Has: {names}")
        item.update({"src": rec["src"], "member": rec["member"],
                     "file": fname, "blocks": match[0][2]})
        return item
    raise OverrideError(f"{label}: needs one of 'image', 'file' or 'unavailable'")


def apply_override(overrides: dict, sid: str, title: str, item: dict) -> dict:
    for key in (("by_side", sid, title), ("by_title", title, None)):
        if key in overrides:
            fixed = dict(overrides[key])
            fixed.setdefault("title", title)
            return fixed
    return item


def write_report(results):
    lines = ["# Harvest report", "",
             "Top candidates per title. **M** = multi-load game (copy a whole image, not one file).",
             "Single files first, then whole images.", ""]
    found = total = 0
    for sid, r in results.items():
        lines.append(f"## {sid} - {', '.join(r['labels'])}" + ("  (menu disk)" if r["menu"] else ""))
        for it in r["items"]:
            total += 1
            flag = " **M**" if it["multiload"] else ""
            if not it["hits"] and not it["images"]:
                lines.append(f"- **{it['title']}**{flag}: _no candidates_")
                continue
            found += 1
            lines.append(f"- **{it['title']}**{flag}")
            for h in it["hits"][:5]:
                where = h["src"] + (f" :: {h['member']}" if h["member"] else "")
                warn = ("" if h["ok_src"] else " _(parameter disk)_") + \
                       ("" if h["big_enough"] else " _(too small)_")
                lines.append(f"    - file {h['score']:.2f}  `{h['file']}` ({h['blocks']} blk) "
                             f"on \"{h['disk_name']}\"{warn} - {where}")
            for h in it["images"][:4]:
                where = h["src"] + (f" :: {h['member']}" if h["member"] else "")
                warn = "" if h["ok_src"] else " _(parameter disk)_"
                lines.append(f"    - disk {h['score']:.2f}  [{h['kind']}] \"{h['disk_name']}\" "
                             f"({h['n_files']} files){warn} - {where}")
        lines.append("")
    lines.insert(2, f"Found candidates for {found} of {total} titles.\n")
    (HERE / "report.md").write_text("\n".join(lines))
    print(f"candidates for {found}/{total} titles -> report.md, candidates.json")


def write_selection_draft(results, overrides: dict):
    """Best guess per title, with overrides.json applied on top."""
    path = HERE / "selections.json"
    sel = {}
    for sid, r in results.items():
        items = [apply_override(overrides, sid, it["title"], draft_item(it))
                 for it in r["items"]]
        sel[sid] = {"menu": r["menu"], "disk_name": f"{r['disk']} side {r['side']}"[:16],
                    "disk_id": r["disk"][-2:], "items": items}
    path.write_text(json.dumps(sel, indent=1))
    todo = sum(1 for e in sel.values() for i in e["items"] if "todo" in i)
    print(f"selections -> {path.name}: {sum(len(e['items']) for e in sel.values())} titles, "
          f"{todo} with nothing to build")


def draft_item(it: dict) -> dict:
    # No "start" here on purpose: build.py reads the file's load address and
    # decides between RUN and SYS. Setting one in overrides.json wins.
    item = {"title": it["title"]}
    f = it["hits"][0] if it["hits"] else None
    im = it["images"][0] if it["images"] else None
    # a multi-load game needs a whole disk, and so does anything with no
    # single-file candidate at all
    if (it["multiload"] and im) or (im and not f):
        item["whole_image"] = {"src": im["src"], "member": im["member"],
                               "disk_name": im["disk_name"], "kind": im["kind"]}
    elif f:
        item.update({"src": f["src"], "member": f["member"], "file": f["file"], "blocks": f["blocks"]})
    else:
        item["todo"] = "no candidate found"
    return item


def cmd_find(args):
    """Ad-hoc search of the index, for checking a pick by hand."""
    index = [json.loads(l) for l in Path(args.index).open(encoding="utf-8")]
    needle = args.text.lower().replace("_", " ")
    rows = []
    for rec in index:
        tag = "P" if is_param_source(rec) else " "
        where = rec["src"] + (f"::{rec['member']}" if rec["member"] else "")
        hay = f'{rec.get("stem", "")} {rec["disk_name"]} {rec["src"]}'.lower().replace("_", " ")
        if needle in hay:
            rows.append((999, tag, "DISK", f'{rec["kind"]} "{rec["disk_name"]}"', where))
        for fname, ftype, blocks in rec["files"]:
            if needle in fname.lower().replace("_", " ") and ftype in ("PRG", "USR"):
                rows.append((blocks, tag, f"{blocks:>4}b", fname, where))
    rows.sort(key=lambda r: -r[0])
    for _, tag, blk, name, where in rows[: args.limit]:
        print(f"{tag} {blk}  {name:<24} {where}")
    print(f"-- {len(rows)} hits (P = parameter/copier disk)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", default=str(HERE / "index.jsonl"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("index")
    a.add_argument("roots", nargs="+")
    a.add_argument("-v", "--verbose", action="store_true")
    a.add_argument("--rebuild", action="store_true", help="ignore the existing index and re-read everything")
    c = sub.add_parser("find", help="search the index by substring")
    c.add_argument("text")
    c.add_argument("--limit", type=int, default=30)
    b = sub.add_parser("match")
    b.add_argument("--threshold", type=float, default=0.8)
    b.add_argument("--top", type=int, default=10)
    args = ap.parse_args()
    {"index": cmd_index, "match": cmd_match, "find": cmd_find}[args.cmd](args)


if __name__ == "__main__":
    main()
