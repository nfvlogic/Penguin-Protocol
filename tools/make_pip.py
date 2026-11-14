#!/usr/bin/env python3
"""Builds docs/pip.svg: Pip waving hello and Pip thinking, animated, for the README.

The pixels and the moves are the same as in the game (web/pip.js). The animation is plain SVG (no script),
so GitHub shows it inside the README.

Run from the project folder:  python3 tools/make_pip.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 10, 11
PAL = {"O": "#f5a031", "D": "#b8650f", "K": "#555c6c", "W": "#e8e8e8"}
BASE = ["...O...", ".OOOOO.", "OOOOOOO", "DWWWWWD", "KWWOWWK", "KWWWWWK", ".KWWWK.", ".O...O."]


def compose(mood, t):
    """The same drawing rules as web/pip.js, for the two moods shown in the README."""
    g = [[None] * W for _ in range(H)]

    def put(x, y, ch):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = ch

    def step(ms):
        return t // ms
    ox, oy, head, look, blink = 1, 2, 0, 0, False
    extra = []
    if mood == "think":
        look = [0, 1, 1, 0, -1, -1][step(300) % 6]
        head = 1 if step(1800) % 2 and step(300) % 6 > 2 else 0
    elif mood == "wave":
        up = step(220) % 2
        blink = t % 2200 >= 1980
        extra = [(ox + 7, oy + 4 - up, "K")] + ([(ox + 8, oy + 3 - up, "K")] if up else [])
    for y, row in enumerate(BASE):
        for x, ch in enumerate(row):
            if ch != ".":
                put(ox + x + (head if y <= 3 else 0), oy + y, ch)
    ey, h = oy + 3, ox + head
    if blink:
        put(h + 2, ey, "K"), put(h + 4, ey, "K")
    else:
        put(h + 2 + look, ey, None), put(h + 4 + look, ey, None)
    for x, y, ch in extra:
        put(x, y, ch)
    return g


def frames(mood, period, every):
    return [compose(mood, t) for t in range(0, period, every)]


def pip(x0, y0, scale, mood, period, every):
    """One animated Pip: every frame is a group that is visible during its own slice of the loop."""
    fs = frames(mood, period, every)
    n, out = len(fs), []
    for i, g in enumerate(fs):
        rects = "".join(f'<rect x="{x0 + x * scale}" y="{y0 + y * scale}" width="{scale}" height="{scale}" fill="{PAL[c]}"/>'
                        for y in range(H) for x in range(W) for c in [g[y][x]] if c)
        vis = ";".join("visible" if k == i else "hidden" for k in range(n))
        out.append(f'<g visibility="{"visible" if i == 0 else "hidden"}">{rects}'
                   f'<animate attributeName="visibility" values="{vis}" dur="{period / 1000}s" calcMode="discrete" '
                   f'repeatCount="indefinite"/></g>')
    return "".join(out)


def build():
    scale, gap = 12, 70
    size = W * scale
    width, height = size * 2 + gap + 80, size + 70
    left, right = 40, 40 + size + gap
    label = 'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="15" text-anchor="middle"'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
           f'role="img" aria-label="Pip, the pixel penguin from Penguin Protocol, waving hello and thinking">'
           f'<rect width="100%" height="100%" rx="14" fill="#050505"/>'
           + pip(left, 14, scale, "wave", 2200, 110) + pip(right, 14, scale, "think", 3600, 150)
           + f'<text x="{left + size / 2}" y="{height - 18}" fill="#f5a031" {label}>hello</text>'
           + f'<text x="{right + size / 2}" y="{height - 18}" fill="#f5a031" {label}>thinking</text></svg>')
    path = os.path.join(ROOT, "docs", "pip.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"docs/pip.svg written ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    build()
