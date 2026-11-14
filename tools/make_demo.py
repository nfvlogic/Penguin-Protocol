"""Builds docs/demo.svg: an animated terminal that replays the first ticket with the game's real output.

Run from the project folder:  python3 tools/make_demo.py
"""
import contextlib
import io
import os
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ["PENGUIN_SAVE"] = os.path.join(ROOT, "docs", ".demo_save.json")
os.environ["PENGUIN_SEED"] = "0"

from penguin.core import plain  # noqa: E402
from penguin.shell import Shell  # noqa: E402

COMMANDS = ["cat welcome.txt", "cd atlas", "cat README.md", "submit 5050"]
WIDTH_CHARS, FONT, LINE = 76, 14, 21


def record():
    """[(kind, text, delay)] kind: card | prompt | out"""
    shell = Shell()
    shell.width = lambda: 74
    rows = []
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        shell.start_level(1)
    for line in plain(buf.getvalue()).splitlines():
        rows.append(("card", line.rstrip(), 0.05))
    for cmd in COMMANDS:
        rows.append(("prompt", plain(shell.prompt()) + cmd, 1.3))
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            shell.execute(cmd)
        for line in plain(buf.getvalue()).splitlines():
            if line.startswith("────"):
                break                      # stop before the next ticket card
            rows.append(("out", line.rstrip(), 0.12))
    return rows


def build(rows):
    t, times = 0.4, []
    for kind, _, delay in rows:
        t += delay
        times.append(t)
    total = t + 4.0
    height = len(rows) * LINE + 70
    width = 12 + WIDTH_CHARS * 8.6 + 24
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height}" viewBox="0 0 {width:.0f} {height}" role="img" '
           f'aria-label="Penguin Protocol: solving the first ticket">',
           '<rect width="100%" height="100%" rx="10" fill="#1e1e2e"/>',
           '<rect width="100%" height="34" rx="10" fill="#313244"/><rect y="20" width="100%" height="14" fill="#313244"/>',
           '<circle cx="20" cy="17" r="6" fill="#f38ba8"/><circle cx="40" cy="17" r="6" fill="#f9e2af"/><circle cx="60" cy="17" r="6" fill="#a6e3a1"/>',
           f'<text x="{width / 2:.0f}" y="22" fill="#a6adc8" font-family="Menlo,Consolas,monospace" font-size="12" text-anchor="middle">'
           'penguin.py</text>',
           f'<g font-family="Menlo,Consolas,\'DejaVu Sans Mono\',monospace" font-size="{FONT}" xml:space="preserve">']
    for i, ((kind, text, _), at) in enumerate(zip(rows, times)):
        y = 58 + i * LINE
        if kind == "prompt":
            who, _, rest = text.partition(":")
            where, _, cmd = rest.partition("$ ")
            body = (f'<tspan fill="#a6e3a1" font-weight="bold">{escape(who)}</tspan><tspan fill="#cdd6f4">:</tspan>'
                    f'<tspan fill="#89b4fa" font-weight="bold">{escape(where)}</tspan><tspan fill="#cdd6f4">$ </tspan>'
                    f'<tspan fill="#f5e0dc">{escape(cmd)}</tspan>')
        elif kind == "card":
            colour = "#6c7086" if text.startswith("────") else ("#f9e2af" if text.strip() in ("DESCRIPTION", "RESOLVED WHEN") or "COMMANDS" in text else "#cdd6f4")
            body = f'<tspan fill="{colour}">{escape(text)}</tspan>'
        else:
            colour = "#a6e3a1" if text.startswith("✓") else ("#89dceb" if text.startswith("Password") else "#cdd6f4")
            body = f'<tspan fill="{colour}">{escape(text)}</tspan>'
        f = at / total
        out.append(f'<text x="12" y="{y}" opacity="0">{body}'
                   f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;{f:.4f};{min(f + 0.0005, 0.99):.4f};0.985;1" '
                   f'dur="{total:.1f}s" repeatCount="indefinite"/></text>')
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
