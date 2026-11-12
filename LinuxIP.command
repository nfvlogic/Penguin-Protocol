#!/bin/bash
# Double-click this file in Finder (or run ./LinuxIP.command) to start LinuxIP on macOS/Linux.
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
    python3 linux_13.4.py
else
    echo "Python 3 not found. Install it from python.org or run: xcode-select --install"
fi
echo
read -n 1 -s -r -p "Press any key to close..."
