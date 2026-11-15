#!/usr/bin/env python3
"""Builds docs/pip.svg: Pip waving hello, animated, for the README.

The pixels and the moves are the same as in the game (web/pip.js). The animation is plain SVG (no script),
so GitHub shows it inside the README.

Run from the project folder:  python3 tools/make_pip.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 10, 11
PAL = {"O": "#f5a031", "D": "#b8650f", "K": "#555c6c", "W": "#e8e8e8", "G": "#ffd166"}
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


def pose(look=0, head=0, blink=False, hat=0, arm=None, key=0):
    """One still frame of Pip (the same pixels as the game). arm: None, 0 (down) or 1 (up); key: 0 none, 1 or 2 turning."""
    g = [[None] * W for _ in range(H)]
    ox, oy = 1, 2

    def put(x, y, ch):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = ch
    for y, row in enumerate(BASE):
        for x, ch in enumerate(row):
            if ch != ".":
                put(ox + x + (head if y <= 3 else 0), oy + y - (hat if y <= 2 else 0), ch)
    ey, h = oy + 3, ox + head
    if blink:
        put(h + 2, ey, "K"), put(h + 4, ey, "K")
    else:
        put(h + 2 + look, ey, None), put(h + 4 + look, ey, None)
    if arm is not None:
        put(ox + 7, oy + 4 - arm, "K")
        if arm:
            put(ox + 8, oy + 3, "K")
    if key:
        put(ox + 8, oy + 3, "G"), put(ox + 8, oy + 4, "G")
        put(*((ox + 9, oy + 3) if key == 1 else (ox + 8, oy + 5)), "G")
    return g


def seq_wave():
    out = []
    for k in range(10):
        out.append((pose(arm=k % 2, blink=k == 9), 220))
    return out


def seq_look(d):
    return [(pose(look=d), 1500), (pose(), 700), (pose(blink=True), 140), (pose(look=d), 1000)]


def seq_tip():
    return [(pose(), 1500), (pose(hat=1), 450), (pose(), 1000), (pose(blink=True), 140), (pose(), 600)]


def seq_think():
    out = []
    for k, look in enumerate([0, 1, 1, 0, -1, -1]):
        out.append((pose(look=look, head=1 if k > 2 else 0), 300))
    return out + [(pose(), 1200)]


def seq_blink():
    return [(pose(), 1200), (pose(look=-1), 500), (pose(), 600), (pose(blink=True), 140), (pose(look=1), 500), (pose(), 800)]


def seq_key():
    out = []
    for k in range(8):
        out.append((pose(look=1, key=1 + k % 2), 260))
    return out + [(pose(look=1, key=1, blink=True), 140), (pose(look=1, key=2), 500)]


SEQUENCES = {"wave": seq_wave, "right": lambda: seq_look(1), "left": lambda: seq_look(-1), "tip": seq_tip,
             "think": seq_think, "blink": seq_blink, "key": seq_key}


def paths(g, scale):
    """One <path> per colour, horizontal runs merged: small enough for a README."""
    by = {}
    for y in range(H):
        x = 0
        while x < W:
            c = g[y][x]
            if not c:
                x += 1
                continue
            x0 = x
            while x < W and g[y][x] == c:
                x += 1
            by.setdefault(c, []).append(f"M{x0 * scale} {y * scale}h{(x - x0) * scale}v{scale}h-{(x - x0) * scale}z")
    return "".join(f'<path fill="{PAL[c]}" d="{"".join(d)}"/>' for c, d in by.items())


def write_small():
    """docs/pip-NAME.svg: a small looping Pip (plain SVG animation, so GitHub shows it in the README)."""
    scale = 4
    for name, make in SEQUENCES.items():
        steps = make()
        total = sum(ms for _, ms in steps)
        uniq, groups = [], []
        for g, _ in steps:
            if g not in uniq:
                uniq.append(g)
        t, marks = 0, []                       # [(frame index, start, end)]
        for g, ms in steps:
            marks.append((uniq.index(g), t, t + ms))
            t += ms
        for n, g in enumerate(uniq):
            kt, vals = ["0"], []
            spans = [(a, b) for k, a, b in marks if k == n]
            # visibility: a list of (time, value) switches, as discrete keyTimes over [0, 1]
            sw = []
            for a, b in spans:
                sw += [(a, "visible"), (b, "hidden")]
            sw.sort()
            times, values = [0.0], ["hidden" if (not spans or spans[0][0] > 0) else "visible"]
            for tm, v in sw:
                if tm >= total:
                    continue
                if tm == times[-1]:
                    values[-1] = v
                else:
                    times.append(tm)
                    values.append(v)
            keytimes = ";".join(f"{tm / total:.4f}" for tm in times)
            groups.append(f'<g visibility="{values[0]}">{paths(g, scale)}<animate attributeName="visibility" '
                          f'values="{";".join(values)}" keyTimes="{keytimes}" dur="{total / 1000}s" calcMode="discrete" '
                          f'repeatCount="indefinite"/></g>')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * scale}" height="{H * scale}" viewBox="0 0 {W * scale} {H * scale}" '
               f'role="img" aria-label="Pip">{"".join(groups)}</svg>')
        with open(os.path.join(ROOT, "docs", f"pip-{name}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
    print(f"docs/pip-*.svg written ({len(SEQUENCES)} animated loops)")


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
    scale = 12
    size = W * scale
    width, height = size + 160, size + 70
    left = (width - size) // 2
    label = 'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="15" text-anchor="middle"'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
           f'role="img" aria-label="Pip, the pixel penguin from Penguin Protocol, waving hello">'
           f'<rect width="100%" height="100%" rx="14" fill="#050505"/>'
           + pip(left, 14, scale, "wave", 2200, 110)
           + f'<text x="{width / 2}" y="{height - 18}" fill="#f5a031" {label}>hello</text></svg>')
    path = os.path.join(ROOT, "docs", "pip.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"docs/pip.svg written ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    build()
    write_small()
