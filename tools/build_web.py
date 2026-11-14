#!/usr/bin/env python3
"""Build the web version into site/ : the web/ files plus the real penguin/ package (as penguin.zip).

Usage: python3 tools/build_web.py [OUTPUT_DIR]      (default: site)
Then serve it:  python3 -m http.server -d site
"""
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(out):
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "web"), out)
    version = ""
    with open(os.path.join(ROOT, "penguin", "core.py"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("VERSION"):
                version = line.split('"')[1]
    with zipfile.ZipFile(os.path.join(out, "penguin.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(os.path.join(ROOT, "penguin"))):
            if name.endswith(".py"):
                z.write(os.path.join(ROOT, "penguin", name), "penguin/" + name)
    # the service worker cache name changes with the version, so updates reach installed copies
    sw = os.path.join(out, "sw.js")
    with open(sw, encoding="utf-8") as f:
        text = f.read().replace("__VERSION__", version + "-" + str(int(os.path.getmtime(os.path.join(out, "penguin.zip")))))
    with open(sw, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"built {out}/ (Penguin Protocol {version})")


if __name__ == "__main__":
    build(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, "site"))
