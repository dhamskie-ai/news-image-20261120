#!/usr/bin/env python3
"""The World — Friday 20 November 2026.

Copies the bundled newspaper image (entry.png, in this repository's root)
to /output/entry.png after validating it: PNG magic bytes, IHDR bit depth 8
and colour type 2/6, the CRC of every chunk, size at most 1 MiB, and the
embedded SHA-256. Standard library only, no network, deterministic: every
run writes the same bytes.
"""
import hashlib
import struct
import sys
import zlib
from pathlib import Path

EXPECTED_SHA256 = "ff387420c37923fd638d204e740ffa22d4fe6e9979095fb3985dacc1e289ce03"
MAX_BYTES = 1048576
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def validate_png(data: bytes) -> None:
    if len(data) > MAX_BYTES:
        raise ValueError(f"image is {len(data)} bytes, over the 1 MiB limit")
    if data[:8] != PNG_MAGIC:
        raise ValueError("not a PNG file (bad magic bytes)")
    pos = 8
    seen_ihdr = False
    seen_iend = False
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("truncated PNG chunk header")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        end = pos + 8 + length + 4
        if end > len(data):
            raise ValueError(f"truncated PNG chunk {ctype!r}")
        chunk_data = data[pos + 8:pos + 8 + length]
        stored_crc = struct.unpack(">I", data[pos + 8 + length:end])[0]
        actual_crc = zlib.crc32(ctype + chunk_data) & 0xFFFFFFFF
        if stored_crc != actual_crc:
            raise ValueError(f"bad CRC in PNG chunk {ctype!r}")
        if not seen_ihdr:
            if ctype != b"IHDR":
                raise ValueError("first PNG chunk is not IHDR")
            if length != 13:
                raise ValueError("IHDR has wrong length")
            width, height, bit_depth, colour_type = struct.unpack(
                ">IIBB", chunk_data[:10])
            if width > 1024 or height > 1024:
                raise ValueError(f"image is {width}x{height}, over 1024x1024")
            if bit_depth != 8:
                raise ValueError(f"IHDR bit depth is {bit_depth}, expected 8")
            if colour_type not in (2, 6):
                raise ValueError(f"IHDR colour type is {colour_type}, expected 2 or 6")
            seen_ihdr = True
        if ctype == b"IEND":
            seen_iend = True
            if length != 0:
                raise ValueError("IEND chunk must be empty")
            if end != len(data):
                raise ValueError("trailing bytes after IEND")
        pos = end
    if not seen_ihdr:
        raise ValueError("missing IHDR chunk")
    if not seen_iend:
        raise ValueError("missing IEND chunk")
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"SHA-256 mismatch: got {digest}")


def main() -> None:
    src = Path(__file__).resolve().parent / "entry.png"
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/output/entry.png")
    data = src.read_bytes()
    validate_png(data)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)


if __name__ == "__main__":
    main()
