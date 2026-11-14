#!/usr/bin/env python3
"""Penguin Protocol - Linux practice shell.

Start:  python3 penguin.py   (Windows: py -3 penguin.py, or double-click PenguinProtocol.bat)
Help:   python3 penguin.py --help

Python 3.10+, standard library only. All the code is in the penguin/ folder next to this file.
"""
import os
import sys

if sys.version_info < (3, 10):
    sys.exit("Penguin Protocol needs Python 3.10 or newer (this is %d.%d). Get it from python.org." % sys.version_info[:2])

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from penguin.shell import main  # noqa: E402

if __name__ == "__main__":
    main()
