"""Pure-Python reader for G64 images (GCR bitstream dumps of real disks).

The C64 Preservation Project ships its dumps as G64: a raw GCR bit image of
each half-track rather than decoded sectors. Most originals still keep an
ordinary directory on track 18, so decoding the GCR back into 256-byte
sectors makes them readable by `cbmimage`.

`to_d64()` decodes every track it can and lays the sectors out in .d64
order, filling unreadable sectors with zeros, so a protected original
degrades to "the parts that read cleanly" instead of failing outright.
"""
from __future__ import annotations

MAGIC = b"GCR-1541"

# 5 GCR bits -> 4 data bits. Everything else is invalid.
_GCR_DECODE = {
    0x0A: 0x0, 0x0B: 0x1, 0x12: 0x2, 0x13: 0x3,
    0x0E: 0x4, 0x0F: 0x5, 0x16: 0x6, 0x17: 0x7,
    0x09: 0x8, 0x19: 0x9, 0x1A: 0xA, 0x1B: 0xB,
    0x0D: 0xC, 0x1D: 0xD, 0x1E: 0xE, 0x15: 0xF,
}

SECTORS_PER_TRACK = [0] + [21] * 17 + [19] * 7 + [18] * 6 + [17] * 5  # 1..35


def d64_offset(track: int, sector: int) -> int:
    off = 0
    for t in range(1, track):
        off += SECTORS_PER_TRACK[t]
    return (off + sector) * 256


class G64Error(ValueError):
    pass


def _tracks(data: bytes):
    """Yield (track_number, gcr_bytes) for every half-track that holds data."""
    if data[:8] != MAGIC:
        raise G64Error("not a G64 image")
    n_half = data[9]
    for i in range(n_half):
        if i & 1:
            continue  # ignore half-tracks; nothing stores a directory there
        p = 12 + i * 4
        (off,) = (int.from_bytes(data[p:p + 4], "little"),)
        if off == 0 or off + 2 > len(data):
            continue
        length = int.from_bytes(data[off:off + 2], "little")
        blk = data[off + 2:off + 2 + length]
        if blk:
            yield i // 2 + 1, blk


def _decode_bits(bits: str) -> bytes:
    """Decode a run of 5-bit GCR groups. Stops at the first invalid group."""
    out = bytearray()
    for i in range(0, len(bits) - 9, 10):
        hi = _GCR_DECODE.get(int(bits[i:i + 5], 2))
        lo = _GCR_DECODE.get(int(bits[i + 5:i + 10], 2))
        if hi is None or lo is None:
            break
        out.append(hi << 4 | lo)
    return bytes(out)


def decode_track(gcr: bytes) -> dict[int, bytes]:
    """Return {sector: 256 bytes} for one track's GCR bitstream."""
    bits = "".join(f"{b:08b}" for b in gcr)
    bits += bits[:400]  # the track is a loop; let a block wrap the seam
    sectors: dict[int, bytes] = {}
    pending: int | None = None  # sector number from the last header block
    i, n = 0, len(bits) - 400
    while i < n:
        if bits[i] != "1":
            i += 1
            continue
        run = 0
        while i + run < len(bits) and bits[i + run] == "1":
            run += 1
        if run < 10:  # not a sync mark
            i += run
            continue
        i += run
        blk = _decode_bits(bits[i:i + 3250])
        if not blk:
            continue
        if blk[0] == 0x08 and len(blk) >= 6:
            pending = blk[2]
        elif blk[0] == 0x07 and len(blk) >= 258 and pending is not None:
            body = blk[1:257]
            chk = 0
            for b in body:
                chk ^= b
            if chk == blk[257]:
                sectors.setdefault(pending, body)
            pending = None
    return sectors


def to_d64(data: bytes, only_track: int | None = None) -> bytes:
    """Decode a G64 into a 35-track .d64 image (unread sectors left as zeros).

    `only_track` decodes just that one track, which is all the directory
    needs and makes indexing thousands of images cheap.
    """
    out = bytearray(174848)
    found = 0
    for track, gcr in _tracks(data):
        if track > 35 or (only_track is not None and track != only_track):
            continue
        for sector, body in decode_track(gcr).items():
            if sector >= SECTORS_PER_TRACK[track]:
                continue
            o = d64_offset(track, sector)
            out[o:o + 256] = body
            found += 1
    if not found:
        raise G64Error("no readable sectors")
    return bytes(out)
