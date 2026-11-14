#!/usr/bin/env python3
"""Penguin Protocol - Linux practice shell. Start: py -3 linux_13.4.py  (or double-click PenguinProtocol.bat)

Python 3.9+, standard library only. All the code is in the linuxip/ folder next to this file.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from linuxip.shell import main  # noqa: E402

if __name__ == "__main__":
    main()
