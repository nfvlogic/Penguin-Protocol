"""Shared constants, colours and the error type used by every module."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_FILE = os.environ.get("LINUXIP_SAVE") or os.path.join(ROOT, "linuxip_save.json")

USER, HOST, MY_IP = "analyst", "linuxip", "10.20.30.47"
HOME = "/home/analyst"
TOKEN = "atl-4821"
API = "http://atlas-api"
NOW = "Thu Nov 12 09:00:01 CET 2026"

HOSTS = """127.0.0.1     localhost
10.20.30.47   linuxip
10.20.30.1    gateway
10.20.30.11   atlas-db-01
10.20.30.12   atlas-db-02
10.20.30.13   atlas-db-03
10.20.30.20   atlas-api
10.20.30.31   atlas-tst
10.20.30.32   atlas-pre
10.20.30.33   atlas-prd
10.20.30.66   guest-laptop-07"""
ONLINE = {"127.0.0.1", "10.20.30.47", "10.20.30.1", "10.20.30.12", "10.20.30.20",
          "10.20.30.31", "10.20.30.33"}

# Real colours only in a real terminal; piped output (tests) stays plain.
TTY = sys.stdin.isatty() and sys.stdout.isatty()
ANSI = re.compile(r"\x1b\[[0-9;]*m")
RESET = "\x1b[0m"


def c(code, text):
    """Colour text with an ANSI code (only in a real terminal)."""
    return f"\x1b[{code}m{text}{RESET}" if TTY else text


def plain(text):
    return ANSI.sub("", text)


def vlen(text):
    return len(plain(text))


class ShellError(Exception):
    """A command failed. `msg` is the real Linux message, `tip` an optional learning tip."""

    def __init__(self, msg, status=1, tip=None):
        super().__init__(msg)
        self.status, self.tip = status, tip


def parse_requirements(text):
    """'Flask==3.0.3' lines -> {'flask': '3.0.3'}."""
    pkgs = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name, _, ver = line.partition("==")
            pkgs[name.strip().lower()] = ver.strip() or "latest"
    return pkgs
