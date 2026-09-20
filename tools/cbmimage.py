"""Minimal pure-Python reader for Commodore disk images (.d64 .d71 .d81).

No dependencies. Reads the directory and extracts files by following the
track/sector chain. Works on raw bytes, so images inside .zip archives can
be read without unpacking them to disk.
"""
from __future__ import annotations

from dataclasses import dataclass, field

FILE_TYPES = {0: "DEL", 1: "SEQ", 2: "PRG", 3: "USR", 4: "REL"}


def _d64_spt(track: int) -> int:
    if track <= 17:
        return 21
    if track <= 24:
        return 19
    if track <= 30:
        return 18
    return 17


def petscii_to_str(raw: bytes) -> str:
    """Convert a PETSCII directory name to a readable ASCII string."""
    out = []
    for b in raw.rstrip(b"\xa0"):
        if 0x41 <= b <= 0x5A:
            out.append(chr(b))  # unshifted letters -> uppercase
        elif 0xC1 <= b <= 0xDA:
            out.append(chr(b - 0x80))  # shifted letters
        elif 0x61 <= b <= 0x7A:
            out.append(chr(b - 0x20))
        elif 0x20 <= b <= 0x3F or b == 0x40:
            out.append(chr(b))
        elif b == 0xA0:
            out.append(" ")
        else:
            out.append("?")
    return "".join(out)


@dataclass
class DirEntry:
    name: str
    raw_name: bytes
    ftype: str
    blocks: int
    track: int
    sector: int
    closed: bool = True


@dataclass
class CbmImage:
    data: bytes
    fmt: str  # d64 | d71 | d81
    tracks: int
    disk_name: str = ""
    disk_id: str = ""
    entries: list[DirEntry] = field(default_factory=list)

    # ---- geometry -------------------------------------------------------
    def _offset(self, track: int, sector: int) -> int:
        if self.fmt == "d81":
            return ((track - 1) * 40 + sector) * 256
        if self.fmt == "d71" and track > 35:
            return 683 * 256 + self._d64_offset(track - 35, sector)
        return self._d64_offset(track, sector)

    @staticmethod
    def _d64_offset(track: int, sector: int) -> int:
        off = 0
        for t in range(1, track):
            off += _d64_spt(t)
        return (off + sector) * 256

    def block(self, track: int, sector: int) -> bytes:
        o = self._offset(track, sector)
        if o + 256 > len(self.data):
            raise ValueError(f"T{track} S{sector} outside image")
        return self.data[o:o + 256]

    # ---- reading --------------------------------------------------------
    def read_file(self, entry: DirEntry, max_blocks: int = 3200) -> bytes:
        out = bytearray()
        t, s = entry.track, entry.sector
        seen = set()
        while t != 0 and len(seen) < max_blocks:
            if (t, s) in seen:
                raise ValueError(f"loop in chain of {entry.name}")
            seen.add((t, s))
            blk = self.block(t, s)
            nt, ns = blk[0], blk[1]
            if nt == 0:
                out += blk[2:ns + 1]
            else:
                out += blk[2:]
            t, s = nt, ns
        return bytes(out)


SIZES = {
    174848: ("d64", 35), 175531: ("d64", 35),
    196608: ("d64", 40), 197376: ("d64", 40),
    205312: ("d64", 42), 206114: ("d64", 42),
    349696: ("d71", 70), 351062: ("d71", 70),
    819200: ("d81", 80), 822400: ("d81", 80),
}


def coerce_size(data: bytes) -> bytes:
    """Round a near-miss image to a real one.

    Scene collections are full of .d64s with a few bytes of junk appended or
    a truncated last track. Both still hold a good directory, so trim or
    zero-pad to the nearest standard size rather than discarding the disk.
    """
    if len(data) in SIZES:
        return data
    for size in sorted(SIZES, reverse=True):
        if size <= len(data) < size * 1.15:
            return data[:size]
    for size in sorted(SIZES):
        if size * 0.97 <= len(data) < size:
            return data + bytes(size - len(data))
    raise ValueError(f"unrecognised image size {len(data)}")


def open_image(data: bytes, lenient: bool = False) -> CbmImage:
    if lenient:
        data = coerce_size(data)
    if len(data) not in SIZES:
        raise ValueError(f"unrecognised image size {len(data)}")
    fmt, tracks = SIZES[len(data)]
    img = CbmImage(data=data, fmt=fmt, tracks=tracks)
    if fmt == "d81":
        hdr = img.block(40, 0)
        img.disk_name = petscii_to_str(hdr[0x04:0x14])
        img.disk_id = petscii_to_str(hdr[0x16:0x18])
        t, s = hdr[0], hdr[1] or 3
        if t == 0:
            t, s = 40, 3
    else:
        hdr = img.block(18, 0)
        img.disk_name = petscii_to_str(hdr[0x90:0xA0])
        img.disk_id = petscii_to_str(hdr[0xA2:0xA4])
        t, s = 18, 1
    seen = set()
    while t != 0 and (t, s) not in seen and len(seen) < 40:
        seen.add((t, s))
        try:
            blk = img.block(t, s)
        except ValueError:
            break
        for i in range(8):
            e = blk[i * 32:(i + 1) * 32]
            typ = e[2]
            if typ == 0:
                continue  # scratched / empty
            raw = e[5:21]
            img.entries.append(DirEntry(
                name=petscii_to_str(raw), raw_name=bytes(raw),
                ftype=FILE_TYPES.get(typ & 7, "???"),
                blocks=e[30] | (e[31] << 8), track=e[3], sector=e[4],
                closed=bool(typ & 0x80)))
        t, s = blk[0], blk[1]
    return img


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        im = open_image(open(p, "rb").read())
        print(f'0 "{im.disk_name:<16}" {im.disk_id}   [{im.fmt}]')
        for e in im.entries:
            print(f'{e.blocks:<5}"{e.name}"'.ljust(24), e.ftype)
