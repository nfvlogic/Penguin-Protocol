#!/bin/bash
# Double-click this file in Finder (or run ./PenguinProtocol.command) to start Penguin Protocol on macOS/Linux.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
    python3 penguin.py
else
    echo "Python 3 not found. Install it from python.org or run: xcode-select --install"
fi
echo
read -n 1 -s -r -p "Press any key to close..."
