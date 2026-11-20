#!/usr/bin/env python3
"""Validate the bundled news image and copy it to the output path.

The program is intentionally small and deterministic: it reads the
``entry.png`` that ships next to this file, runs a series of structural
checks over the PNG byte stream, verifies the file against its known
SHA-256 digest, and finally writes the exact same bytes out again.

Only the Python standard library is used, and no network access happens.

Usage:
    python3 main.py [output-path]

The output defaults to ``/output/entry.png`` when no path is given.
"""

import hashlib
import struct
import sys
import zlib
from pathlib import Path

# The exact digest of the entry image this program is allowed to emit.
EXPECTED_SHA256 = "ff387420c37923fd638d204e740ffa22d4fe6e9979095fb3985dacc1e289ce03"

# A news image must stay small enough to bundle comfortably.
MAX_FILE_SIZE = 1_048_576  # 1 MiB

# The eight magic bytes every PNG file starts with.
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# The image must fit inside a 1024 x 1024 box.
MAX_DIMENSION = 1024

# Colour types the entry image may use: 2 = truecolour, 6 = truecolour+alpha.
ALLOWED_COLOUR_TYPES = (2, 6)

DEFAULT_OUTPUT = Path("/output/entry.png")


def fail(message: str) -> None:
    """Abort with a clear, single-line error message."""
    raise SystemExit(f"error: {message}")


def find_entry_image() -> Path:
    """Locate entry.png next to this script (or in the working directory)."""
    here = Path(__file__).resolve().parent
    for candidate in (here / "entry.png", Path.cwd() / "entry.png"):
        if candidate.is_file():
            return candidate
    fail("entry.png not found next to main.py or in the working directory")


def check_crc(chunk_type: bytes, payload: bytes, stored_crc: int) -> None:
    """Verify one chunk's CRC covers its type code plus its payload."""
    actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    if actual_crc != stored_crc:
        fail(
            f"bad CRC in {chunk_type.decode('latin-1')!r} chunk: "
            f"stored {stored_crc:#010x}, computed {actual_crc:#010x}"
        )


def walk_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    """Parse every chunk, checking CRCs, and stop exactly at IEND.

    Returns the list of (type, payload) pairs in file order. Raises if
    the stream is truncated, a chunk is corrupt, IEND is missing, IEND
    carries a payload, or any bytes follow IEND.
    """
    if data[: len(PNG_MAGIC)] != PNG_MAGIC:
        fail("not a PNG file: bad magic bytes")

    chunks: list[tuple[bytes, bytes]] = []
    pos = len(PNG_MAGIC)
    while pos < len(data):
        if pos + 8 > len(data):
            fail("truncated chunk header")
        (length,) = struct.unpack_from(">I", data, pos)
        chunk_type = data[pos + 4 : pos + 8]
        body_end = pos + 8 + length
        if body_end + 4 > len(data):
            fail(f"truncated {chunk_type.decode('latin-1')!r} chunk")
        payload = data[pos + 8 : body_end]
        (stored_crc,) = struct.unpack_from(">I", data, body_end)
        check_crc(chunk_type, payload, stored_crc)
        chunks.append((chunk_type, payload))
        pos = body_end + 4
        if chunk_type == b"IEND":
            if length != 0:
                fail("IEND chunk must be empty")
            if pos != len(data):
                fail("trailing bytes after IEND chunk")
            return chunks
    fail("missing IEND chunk")


def check_ihdr(chunks: list[tuple[bytes, bytes]]) -> None:
    """Validate the first chunk: IHDR, 13 bytes, sane dimensions."""
    if not chunks or chunks[0][0] != b"IHDR":
        fail("first chunk must be IHDR")
    ihdr = chunks[0][1]
    if len(ihdr) != 13:
        fail(f"IHDR chunk must be 13 bytes, got {len(ihdr)}")
    width, height = struct.unpack_from(">II", ihdr, 0)
    bit_depth = ihdr[8]
    colour_type = ihdr[9]
    if width == 0 or height == 0:
        fail("IHDR width and height must be positive")
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        fail(
            f"image is {width}x{height}, larger than the "
            f"{MAX_DIMENSION}x{MAX_DIMENSION} limit"
        )
    if bit_depth != 8:
        fail(f"bit depth must be 8, got {bit_depth}")
    if colour_type not in ALLOWED_COLOUR_TYPES:
        fail(
            f"colour type must be 2 (RGB) or 6 (RGBA), got {colour_type}"
        )


def check_idat(chunks: list[tuple[bytes, bytes]]) -> None:
    """A PNG with no image data is not a picture: require an IDAT chunk."""
    idat_chunks = [payload for chunk_type, payload in chunks if chunk_type == b"IDAT"]
    if not idat_chunks:
        fail("no IDAT chunk found: image carries no pixel data")
    if any(len(payload) == 0 for payload in idat_chunks):
        fail("empty IDAT chunk found")


def check_digest(data: bytes) -> None:
    """The file must be byte-for-byte the expected entry image."""
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        fail(f"SHA-256 mismatch: got {digest}, expected {EXPECTED_SHA256}")


def main(argv: list[str]) -> int:
    source = find_entry_image()
    data = source.read_bytes()

    if len(data) > MAX_FILE_SIZE:
        fail(f"entry.png is {len(data)} bytes, over the {MAX_FILE_SIZE} byte limit")

    chunks = walk_chunks(data)
    check_ihdr(chunks)
    check_idat(chunks)
    check_digest(data)

    output = Path(argv[1]) if len(argv) > 1 else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(f"wrote {len(data)} bytes to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
