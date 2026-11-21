#!/usr/bin/env python3
"""news-image-20261120 round 2: copy the entry image to /output/entry.png.

The entry is a program that writes one image of Friday 20 November 2026's
crypto news to /output/entry.png. The image itself (entry.png, next to this
file) is drawn programmatically by draw.py (Pillow, no network); this
program only copies it after validating it byte-for-byte: PNG magic, IHDR
(1024x1024, bit depth 8, colour type 2/6), a CRC check on every chunk, at
least one non-empty IDAT chunk, an empty IEND chunk as the last chunk with
no trailing bytes, at most 1 MiB, and the exact SHA-256 of the final image.
Deterministic: two runs write identical bytes.
"""
import hashlib
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "entry.png"
OUT = Path("/output/entry.png")
MAX_BYTES = 1048576
EXPECTED_SHA256 = "e7930b088015d095afd47e37a0d93994215ea4ef1950ed227af0ab3ba1cb3c32"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def fail(message):
    raise ValueError(message)


def read_chunks(data):
    """Yield (type, payload) for every PNG chunk after the 8-byte magic."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail("not a PNG file (bad magic bytes)")
    pos = 8
    seen_iend = False
    while pos < len(data):
        if seen_iend:
            fail("trailing bytes after IEND")
        if pos + 8 > len(data):
            fail("truncated chunk header")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        end = pos + 8 + length + 4
        if end > len(data):
            fail(f"truncated chunk {ctype!r}")
        payload = data[pos + 8:pos + 8 + length]
        crc_stored = struct.unpack(">I", data[pos + 8 + length:end])[0]
        crc_actual = zlib.crc32(ctype + payload) & 0xFFFFFFFF
        if crc_stored != crc_actual:
            fail(f"bad CRC in chunk {ctype!r}")
        if ctype == b"IEND" and length != 0:
            fail("IEND chunk must be empty")
        yield ctype, payload
        if ctype == b"IEND":
            seen_iend = True
        pos = end
    if not seen_iend:
        fail("missing IEND chunk")


def check_ihdr(payload):
    if len(payload) != 13:
        fail("IHDR chunk must be 13 bytes")
    width, height, depth, colour = struct.unpack(">IIBB", payload[:10])
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        fail(f"expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}, got {width}x{height}")
    if depth != 8:
        fail(f"expected bit depth 8, got {depth}")
    if colour not in (2, 6):
        fail(f"expected colour type 2 or 6, got {colour}")


def check_idat(chunks):
    """Every IDAT chunk must carry image data; an empty one is corrupt."""
    idats = [payload for ctype, payload in chunks if ctype == b"IDAT"]
    if not idats:
        fail("no IDAT chunk found")
    if any(len(payload) == 0 for payload in idats):
        fail("empty IDAT chunk found")


def main():
    data = SRC.read_bytes()
    if len(data) > MAX_BYTES:
        fail(f"entry.png is {len(data)} bytes, over the 1 MiB limit")
    chunks = list(read_chunks(data))
    if not chunks or chunks[0][0] != b"IHDR":
        fail("first chunk must be IHDR")
    check_ihdr(chunks[0][1])
    if chunks[-1][0] != b"IEND":
        fail("last chunk must be IEND")
    check_idat(chunks)
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        fail(f"SHA-256 mismatch: got {digest}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"wrote {OUT} ({len(data)} bytes, sha256 {digest})")


if __name__ == "__main__":
    main()
