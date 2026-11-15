"""Builds docs/demo.svg: an animated terminal that replays the first ticket with the game's real output,
in colour, with Pip drawn as pixel art and the answer bar the web version plays when you submit.

Run from the project folder:  python3 tools/make_demo.py
"""
import contextlib
import io
import os
import re
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
os.environ["PENGUIN_SAVE"] = os.path.join(ROOT, "docs", ".demo_save.json")
os.environ["PENGUIN_SEED"] = "0"
os.environ["PENGUIN_TTY"] = "1"       # colours on
os.environ["PENGUIN_WEB"] = "1"       # Pip as a marked spot that we draw ourselves
os.environ["PENGUIN_FIRSTS"] = "1"

from penguin.shell import Shell  # noqa: E402
import make_pip  # noqa: E402

COMMANDS = ["cat welcome.txt", "cd atlas", "cat README.md", "submit 5050"]
WIDTH_CHARS, FONT, LINE, CHAR = 76, 14, 21, 8.45
PX = 4                                   # one Pip pixel is 4 x 4 screen pixels
PAL = {"30": "#6e7681", "31": "#ff7b72", "32": "#3fb950", "33": "#f5a031", "34": "#58a6ff", "35": "#bc8cff",
       "36": "#39c5cf", "37": "#b1bac4", "90": "#8b949e", "91": "#ffa198", "92": "#56d364", "93": "#e3b341",
       "94": "#79c0ff", "95": "#d2a8ff", "96": "#56d4dd", "97": "#f0f6fc"}
FG = "#d8d8d8"
OSC = re.compile(r"\x1b\](?:pip;(\w+);\d|pip;end|[^\x07]*)\x07")
CSI = re.compile(r"\x1b\[([0-9;]*)m")


def segments(text):
    """[(colour, bold, text)] from a line with ANSI colour codes."""
    out, colour, bold, last = [], FG, False, 0
    for m in CSI.finditer(text):
        if m.start() > last:
            out.append((colour, bold, text[last:m.start()]))
        last = m.end()
        for code in (m.group(1) or "0").split(";"):
            if code in ("", "0"):
                colour, bold = FG, False
            elif code == "1":
                bold = True
            elif code in PAL:
                colour = PAL[code]
    if last < len(text):
        out.append((colour, bold, text[last:]))
    return out


def lines_of(raw):
    """[(segments, pip mood or None)] for the output of one command."""
    rows = []
    for line in raw.split("\n"):
        mood = None
        m = re.search(r"\x1b\]pip;(\w+);0\x07", line)
        if m and m.group(1) != "end":
            mood = m.group(1)
        line = OSC.sub("", line).rstrip()
        rows.append((segments(line), mood))
    return rows


def plain(segs):
    return "".join(t for _, _, t in segs)


def record():
    """[(kind, segs, pip, delay)] kind: card | prompt | out | bar"""
    shell = Shell()
    shell.width = lambda: 74
    rows = []
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        shell.start_level(1)
    for segs, mood in lines_of(buf.getvalue()):
        rows.append(("card", segs, mood, 0.05))
    for cmd in COMMANDS:
        prompt = shell.prompt()
        rows.append(("prompt", segments(prompt + cmd), None, 1.3))
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            shell.execute(cmd)
        out = lines_of(buf.getvalue())
        if cmd.startswith("submit"):
            rows.append(("bar", None, "think", 0.3))
        for segs, mood in out:
            if plain(segs).startswith("────"):
                break                      # stop before the next ticket card
            if cmd.startswith("submit") and mood and mood.endswith("win"):
                mood = None                # the answer bar already has Pip: one Pip only, like the game
            rows.append(("out", segs, mood, 0.12))
    return rows


def pip_art(x, y, mood):
    """Pip as little squares (the same drawing as the game), 10 x 11 pixels."""
    g = make_pip.compose("wave" if mood in ("win", "vaultwin", "wave") else "think", 0)
    return "".join(f'<rect x="{x + cx * PX}" y="{y + cy * PX}" width="{PX}" height="{PX}" fill="{make_pip.PAL[c]}"/>'
                   for cy in range(make_pip.H) for cx in range(make_pip.W) for c in [g[cy][cx]] if c)


def tspans(segs):
    return "".join(f'<tspan fill="{c}"{" font-weight=\"bold\"" if b else ""}>{escape(t.replace(chr(32), chr(160)))}</tspan>' for c, b, t in segs)


def build(rows):
    t, times = 0.4, []
    for kind, *_rest, delay in rows:
        t += delay
        times.append(t)
    bar_frames = 17
    extra = 0.1 * bar_frames + 1.0        # the answer bar plays for about 2 seconds in the real game
    total = t + extra + 4.0
    height = len(rows) * LINE + 80
    width = 12 + WIDTH_CHARS * CHAR + 24
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
           f'aria-label="Penguin Protocol: solving the first mission, with Pip">',
           '<rect width="100%" height="100%" rx="10" fill="#050505"/>',
           '<rect width="100%" height="34" rx="10" fill="#1a1a1a"/><rect y="20" width="100%" height="14" fill="#1a1a1a"/>',
           '<circle cx="20" cy="17" r="6" fill="#ff7b72"/><circle cx="40" cy="17" r="6" fill="#e3b341"/><circle cx="60" cy="17" r="6" fill="#3fb950"/>',
           f'<text x="{width / 2:.0f}" y="22" fill="#8b949e" font-family="Menlo,Consolas,monospace" font-size="12" text-anchor="middle">'
           'Penguin Protocol</text>',
           f'<g font-family="Menlo,Consolas,\'DejaVu Sans Mono\',monospace" font-size="{FONT}" xml:space="preserve" style="white-space:pre">']
    shift = 0.0                            # time added by the answer bar, for every row after it
    for i, ((kind, segs, mood, _), at) in enumerate(zip(rows, times)):
        y = 58 + i * LINE
        start = at + shift
        f = start / total

        def show(markup, f0, f1=None):
            keys = f"0;{f0:.4f};{min(f0 + 0.0005, 0.99):.4f};0.985;1" if f1 is None else \
                   f"0;{f0:.4f};{min(f0 + 0.0005, 0.99):.4f};{f1:.4f};{min(f1 + 0.0005, 0.99):.4f};1"
            vals = "0;0;1;1;0" if f1 is None else "0;0;1;1;0;0"
            return (f'<g opacity="0">{markup}<animate attributeName="opacity" values="{vals}" keyTimes="{keys}" '
                    f'dur="{total:.1f}s" repeatCount="indefinite"/></g>')
        if kind == "bar":
            for k in range(bar_frames):
                at_k = start + 0.1 * k + (0.0 if k else 0.0)
                end_k = start + 0.1 * (k + 1) + (1.0 if k == bar_frames - 1 else 0.0)
                if k < 6:
                    txt = [("#f5a031", False, "sending answer to Control ... "), ("#8b949e", False, "·+✳❄✳+"[k])]
                else:
                    n = k - 6
                    done = n >= 10
                    txt = [("#f5a031", False, "verifying ATL-101 [" + "#" * min(n, 10) + "-" * (10 - min(n, 10)) + "] "),
                           ("#3fb950" if done else "#d8d8d8", done, "PASSED" if done else f"{n * 10:3d}%")]
                body = f'<text x="{12 + 7 * CHAR:.0f}" y="{y + 4}">{tspans(txt)}</text>' + pip_art(12, y - 16, "think" if k < bar_frames - 1 else "win")
                out.append(show(body, at_k / total, None if k == bar_frames - 1 else end_k / total))   # the last frame stays
            shift += extra - 0.1                # everything after the bar waits for it
            continue
        pip = pip_art(12, y - 16, mood) if mood else ""
        out.append(show(f'<text x="12" y="{y}">{tspans(segs)}</text>{pip}', f))
    out.append("</g></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    svg = build(record())
    with open(os.path.join(ROOT, "docs", "demo.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    leftover = os.path.join(ROOT, "docs", ".demo_save.json")
    if os.path.exists(leftover):
        os.remove(leftover)
    print(f"docs/demo.svg written ({len(svg) // 1024} KB)")
