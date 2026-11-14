#!/usr/bin/env python3
"""Draw the app icons (a glossy terminal prompt on a dark square) with the standard library only -> web/icon-*.png"""
import os
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def seg(u, v, a, b):
    """Distance from point (u, v) to the segment a-b."""
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((u - ax) * dx + (v - ay) * dy) / (dx * dx + dy * dy)))
    return ((u - ax - t * dx) ** 2 + (v - ay - t * dy) ** 2) ** .5


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


R = .062   # stroke half-width


def glyph_distance(u, v):
    """Distance to the prompt  >_  (a chevron and a cursor bar); <= R means inside."""
    d = min(seg(u, v, (.29, .30), (.53, .50)), seg(u, v, (.53, .50), (.29, .70)))
    d = min(d, seg(u, v, (.58, .72), (.74, .72)))
    return d


def pixel(u, v):
    """u, v in 0..1 -> RGB. Minimal and glossy: a green terminal prompt on a dark glass square."""
    col = mix((34, 46, 66), (7, 10, 16), v * 1.15)                    # background gradient
    d = glyph_distance(u, v)
    col = mix(col, (40, 220, 140), max(0.0, .5 - d * 2.6) * .55)      # soft glow around the prompt
    if d <= R:
        top = mix((140, 255, 190), (14, 150, 100), (v - .28) / .48)   # glyph gradient
        col = top
        if d > R - .012:
            col = mix(col, (230, 255, 240), .45)                      # rim light
        if v < .5 and d < R - .012:                                   # glass highlight on the upper half of each stroke
            col = mix(col, (255, 255, 255), .28 * (1 - (v - .25) / .3))
    if v < .46 and ((u - .5) / 1.2) ** 2 + ((v + .55) / .98) ** 2 <= 1:   # glass shine over the whole icon
        col = mix(col, (255, 255, 255), .10)
    return tuple(int(x) for x in col)


pixel_full = pixel


def png(size, path):
    rows = []
    ss = 3
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            acc = [0, 0, 0]
            for sy in range(ss):
                for sx in range(ss):
                    p = pixel_full((x + (sx + .5) / ss) / size, (y + (sy + .5) / ss) / size)
                    for i in range(3):
                        acc[i] += p[i]
            row += bytes(a // (ss * ss) for a in acc)
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "web"), exist_ok=True)
    for s in (180, 192, 512):
        png(s, os.path.join(ROOT, "web", f"icon-{s}.png"))
    print("icons written to web/")
