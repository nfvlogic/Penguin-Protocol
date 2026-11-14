"""Pip, your partner inside Atlas: a tiny pixel penguin in a detective hat.

He is drawn with half-block characters (one character = one pixel wide, two pixels tall), so he lives in
the terminal like any other text. In a real terminal he is a still picture in 256 colours. On the web page
each of his rows is wrapped in a private marker (\\x1b]pip;MOOD;ROW\\x07 ... \\x1b]pip;end\\x07) and
web/app.js draws him there, animated for a moment, then still.
"""
import os
import textwrap

from .core import TTY, c

W, H = 9, 4                   # pixels; on screen that is 9 characters wide and 2 rows tall
ROWS = H // 2
GAP = "  "
BASE = [
    ".OOOOO.",    # deerstalker
    "DWWWWWD",    # ear flaps and white face (the eyes are cut out below)
    "KWWOWWK",    # beak, dark tuxedo sides
    ".O...O."]    # feet
COLORS = {"O": 214, "D": 130, "K": 240, "W": 254, "G": 220}
MOODS = ("wave", "idle", "think", "hint", "win", "fail", "sleep", "vault", "vaultwin")


def web():
    return os.environ.get("PENGUIN_WEB") == "1"


def frame(mood):
    """The still picture for a mood, as an H x W grid of colour letters (None = empty)."""
    g = [[None] * W for _ in range(H)]

    def put(x, y, ch):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = ch
    ox = 1
    for y, row in enumerate(BASE):
        for x, ch in enumerate(row):
            if ch != ".":
                put(ox + x, y, ch)
    if mood == "sleep":
        put(ox + 2, 1, "K"), put(ox + 4, 1, "K"), put(ox + 7, 0, "O")
    else:
        put(ox + 2, 1, None), put(ox + 4, 1, None)
    if mood == "wave":
        put(ox + 7, 1, "K")
    if mood == "hint":
        for y in (0, 1, 3):
            put(ox + 7, y, "O")
    if mood == "vault":             # holding the golden key
        put(ox + 7, 2, "G"), put(ox + 7, 3, "G")
    if mood == "vaultwin":          # gold everywhere
        put(0, 0, "G"), put(ox + 7, 0, "G"), put(ox + 7, 2, "G")
    return g


WEB_W = 5                     # on the web page Pip is two text lines tall and 5 characters wide


def art(mood):
    """Pip as rows of text: 2 rows of half-blocks in a terminal, one marked row on the web page."""
    if web():   # the page draws him there (web/pip.js); the spaces are only a placeholder
        return [f"\x1b]pip;{mood};0\x07" + " " * WEB_W + "\x1b]pip;end\x07", " " * WEB_W]
    g, rows = frame(mood), []
    for y in range(0, H, 2):
        s = ""
        for x in range(W):
            a, b = g[y][x], g[y + 1][x]
            if not a and not b:
                s += " "
            elif not TTY:
                s += "█" if a and b else ("▀" if a else "▄")
            elif a and b:
                s += f"\x1b[38;5;{COLORS[a]};48;5;{COLORS[b]}m▀\x1b[0m"
            else:
                s += f"\x1b[38;5;{COLORS[a or b]}m{'▀' if a else '▄'}\x1b[0m"
        rows.append(s)
    return rows


def say(mood, paras, width):
    """Pip with a few short lines next to him. `paras`: strings or (colour, string) pairs, wrapped to fit."""
    pic = art(mood)
    left_w = WEB_W if web() else W
    tw = max(16, width - left_w - len(GAP) - 1)
    text = []
    for p in paras:
        code, s = p if isinstance(p, tuple) else (None, p)
        text += [c(code, t) if code else t for t in (textwrap.wrap(s, tw) or [""])]
    lines = []
    for i in range(max(len(pic), len(text))):
        left = pic[i] if i < len(pic) else " " * left_w
        right = text[i] if i < len(text) else ""
        lines.append((left + GAP + right) if right else left)
    return "\n".join([""] + lines + [""])     # an empty line above and below, so Pip never feels crowded
