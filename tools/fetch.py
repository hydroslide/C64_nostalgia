#!/usr/bin/env python3
"""Look for the titles no local collection has, on the Internet Archive.

    python3 fetch.py search                 # what is out there, for the titles
    python3 fetch.py search "Time Pilot"    # one title
    python3 fetch.py get <identifier> ...   # download those items

`search` reads the titles still marked as having no source in selections.json
and queries archive.org's C64 software library for each, trying a few spellings
because the catalogue writes names in its own way ("Mr. Wimpy: The Hamburger
Game", "H.E.R.O."). It only prints; nothing is downloaded until `get`.

`get` pulls the disk images out of the named items into `downloads/`, which
`harvest.py index` can then be pointed at like any other collection.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The wider library, not just _games: educational and childrens titles
# (Hey Diddle Diddle, Danger Mouse) only appear in the parent collection.
COLLECTION = "softwarelibrary_c64"
SEARCH = "https://archive.org/advancedsearch.php"
METADATA = "https://archive.org/metadata/"
WANTED_EXT = {".d64", ".d71", ".d81", ".g64", ".prg", ".t64", ".zip"}
UA = {"User-Agent": "c64-nostalgia/1.0 (personal disk-collection rebuild)"}

# Spellings the Internet Archive uses that a catalogue label does not.
EXTRA_TERMS = {
    "H.E.R.O.": ["hero activision", '"h.e.r.o."'],
    "Mr. Wimpy": ["wimpy hamburger"],
    "Danger Mouse in the Black Forest Chateau": ["danger mouse"],
    "The Game Show": ["game show advanced ideas"],
    "Sublogic Football": ["football sublogic"],
    "Mario's Brewery": ["mario brewery"],
    "Big Top Barney": ["big top barney"],
    "Hey Diddle Diddle": ["hey diddle"],
    "Jungle Hunt": ["jungle hunt atarisoft"],
    "Bagitman": ["bagitman", "bag it man"],
}


def get_json(url: str, tries: int = 3):
    for n in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            if n == tries - 1:
                raise
            print(f"    (retrying after {e})", file=sys.stderr)
            time.sleep(2 * (n + 1))


def query(terms: str, rows: int = 8) -> list[dict]:
    q = f"collection:{COLLECTION} AND ({terms})"
    url = SEARCH + "?" + urllib.parse.urlencode(
        [("q", q), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "year"),
         ("rows", rows), ("output", "json")])
    return get_json(url)["response"]["docs"]


def search_title(title: str) -> list[dict]:
    """Try the plain title, then the looser spellings, and merge the hits."""
    words = [w for w in re.split(r"[^A-Za-z0-9]+", title) if len(w) > 1]
    attempts = [f'title:({" AND ".join(words)})' if words else "",
                f'title:("{title}")']
    attempts += [f"title:({t})" for t in EXTRA_TERMS.get(title, [])]
    seen, out = set(), []
    for attempt in attempts:
        if not attempt:
            continue
        try:
            docs = query(attempt)
        except Exception as e:  # noqa: BLE001
            print(f"    ! {e}", file=sys.stderr)
            continue
        for d in docs:
            if d["identifier"] not in seen:
                seen.add(d["identifier"])
                out.append(d)
    return out


def missing_titles() -> list[str]:
    sel = json.loads((HERE / "selections.json").read_text())
    out = []
    for entry in sel.values():
        for it in entry["items"]:
            if "todo" in it and it["title"] not in out:
                out.append(it["title"])
    return out


def cmd_search(args):
    titles = args.titles or missing_titles()
    for title in titles:
        print(f"\n## {title}")
        docs = search_title(title)
        if not docs:
            print("   nothing found")
            continue
        for d in docs[: args.top]:
            year = d.get("year") or ""
            print(f"   {d['identifier']}\n      {str(d.get('title'))[:70]}  {year}")


def cmd_get(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    got = 0
    for ident in args.identifiers:
        meta = get_json(METADATA + ident)
        files = meta.get("files", [])
        server, d = meta.get("server"), meta.get("dir")
        if not files or not server:
            print(f"  ! {ident}: no files")
            continue
        picked = [f for f in files if Path(f["name"]).suffix.lower() in WANTED_EXT]
        if not picked:
            print(f"  ! {ident}: nothing that looks like a disk image")
            continue
        for f in picked:
            dest = out / f"{ident}__{Path(f['name']).name}"
            if dest.exists():
                print(f"  = {dest.name}")
                continue
            url = f"https://{server}{d}/{urllib.parse.quote(f['name'])}"
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                    dest.write_bytes(r.read())
            except Exception as e:  # noqa: BLE001
                print(f"  ! {dest.name}: {e}")
                continue
            got += 1
            print(f"  + {dest.name}  ({dest.stat().st_size} bytes)")
    print(f"\n{got} files -> {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("search")
    a.add_argument("titles", nargs="*")
    a.add_argument("--top", type=int, default=6)
    b = sub.add_parser("get")
    b.add_argument("identifiers", nargs="+")
    b.add_argument("--out", default=str(HERE / "downloads"))
    args = ap.parse_args()
    {"search": cmd_search, "get": cmd_get}[args.cmd](args)


if __name__ == "__main__":
    main()
