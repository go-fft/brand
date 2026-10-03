#!/usr/bin/env python3
"""Check that the brand kit is complete and well formed.

Every format the README promises must be there, at every size, and each file
must be what its path says: a PNG or JPG of that size, an ICO or ICNS by its
magic number, a 512-px avatar, a 1280x640 social preview. The white and black
SVG variants must carry no other colour. A kit once lived for a week with
three of its seven formats because every existing check looked at something
that was present; this counts the whole matrix instead.
"""
import os
import re
import struct
import sys

ORG = "go-fft"
SIZES = [16, 32, 48, 64, 128, 256, 512, 1024]
errors = []


def need(path):
    if not os.path.isfile(path):
        errors.append(f"missing: {path}")
        return None
    with open(path, "rb") as f:
        return f.read()


def png_size(b):
    if b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", b[16:24])


def jpg_size(b):
    if b[:2] != b"\xff\xd8":
        return None
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1
            continue
        marker = b[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return (w, h)
        i += 2 + struct.unpack(">H", b[i + 2:i + 4])[0]
    return None


def expect_size(path, got, want):
    if got is None:
        errors.append(f"not a valid image: {path}")
    elif tuple(got) != tuple(want):
        errors.append(f"{path}: {got[0]}x{got[1]}, want {want[0]}x{want[1]}")


for variant in ("color", "white", "black"):
    svg = need(f"svg/{variant}/{ORG}.svg")
    if svg is not None and variant != "color":
        mono = "#FFFFFF" if variant == "white" else "#000000"
        others = {c.upper() for c in re.findall(rb"#[0-9A-Fa-f]{6}", svg)} - {mono.encode()}
        if others:
            errors.append(f"svg/{variant}/{ORG}.svg carries other colours: {sorted(others)}")
    for s in SIZES:
        b = need(f"png/{variant}/{s}/{ORG}.png")
        if b is not None:
            expect_size(f"png/{variant}/{s}/{ORG}.png", png_size(b), (s, s))
for s in SIZES:
    b = need(f"jpg/{s}/{ORG}.jpg")
    if b is not None:
        expect_size(f"jpg/{s}/{ORG}.jpg", jpg_size(b), (s, s))
b = need(f"avatar/{ORG}.png")
if b is not None:
    expect_size(f"avatar/{ORG}.png", png_size(b), (512, 512))
b = need(f"social/{ORG}.png")
if b is not None:
    expect_size(f"social/{ORG}.png", png_size(b), (1280, 640))
b = need(f"ico/{ORG}.ico")
if b is not None and b[:4] != b"\x00\x00\x01\x00":
    errors.append(f"ico/{ORG}.ico is not an ICO file")
b = need(f"icns/{ORG}.icns")
if b is not None and b[:4] != b"icns":
    errors.append(f"icns/{ORG}.icns is not an ICNS file")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"brand kit complete: 3 SVG, {3 * len(SIZES)} PNG, {len(SIZES)} JPG, avatar, social, ICO, ICNS")
