#!/usr/bin/env python3
"""Penguin Protocol - Linux practice shell.

Start:  python3 penguin.py   (Windows: py -3 penguin.py, or double-click PenguinProtocol.bat)
Help:   python3 penguin.py --help

Python 3.9+, standard library only. All the code is in the penguin/ folder next to this file.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from penguin.shell import main  # noqa: E402

if __name__ == "__main__":
    main()
