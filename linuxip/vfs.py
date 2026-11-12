"""The simulated file system: a dict path -> text. Folder keys end with '/'.

Nothing here ever touches the real disk.
"""
import fnmatch

from .core import HOME, HOSTS


def sort_key(name):
    """Sort like 'ls' on Ubuntu: ignore case and leading dots."""
    return (name.lstrip(".").lower(), name)


class FS:
    def __init__(self):
        self.d, self.x, self.modes = {}, set(), {}   # x = executable files, modes = chmod'ed paths
        self.reset()

    def reset(self):
        self.d = {"/": "", "/etc/": "", "/etc/hosts": HOSTS, "/home/": "", HOME + "/": "",
                  "/tmp/": "", "/dev/": "", "/dev/null": "", "/usr/": "", "/usr/bin/": "",
                  "/var/": "", "/var/log/": ""}
        self.x, self.modes = set(), {}

    # ---------- paths ----------
    @staticmethod
    def norm(path, cwd):
        if path == "~" or path.startswith("~/"):
            path = HOME + path[1:]
        if not path.startswith("/"):
            path = cwd.rstrip("/") + "/" + path
        parts = []
        for p in path.split("/"):
            if p in ("", "."):
                continue
            if p == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(p)
        return "/" + "/".join(parts)

    @staticmethod
    def dkey(p):
        return "/" if p == "/" else p + "/"

    @staticmethod
    def parent(p):
        return p.rsplit("/", 1)[0] or "/"

    @staticmethod
    def base(p):
        return p.rsplit("/", 1)[-1] or "/"

    @staticmethod
    def join(folder, name):
        return folder.rstrip("/") + "/" + name

    # ---------- queries ----------
    def isdir(self, p):
        return self.dkey(p) in self.d

    def isfile(self, p):
        return p in self.d and not p.endswith("/")

    def exists(self, p):
        return self.isdir(p) or self.isfile(p)

    def children(self, p):
        """[(name, is_dir)] directly inside folder p, sorted like ls."""
        base, out = self.dkey(p), []
        for k in self.d:
            if k == base or not k.startswith(base):
                continue
            rest = k[len(base):]
            if "/" not in rest:
                out.append((rest, False))
            elif rest.index("/") == len(rest) - 1:
                out.append((rest[:-1], True))
        return sorted(out, key=lambda e: sort_key(e[0]))

    def walk(self, p):
        """Every path below folder p (files and folders), sorted."""
        base = self.dkey(p)
        return sorted(k.rstrip("/") for k in self.d if k.startswith(base) and k != base)

    def glob(self, pattern, cwd):
        """Expand * ? [..] like bash. Returns [] when nothing matches."""
        absolute = pattern.startswith("/")
        parts = [p for p in pattern.split("/") if p]
        found = [("/" if absolute else cwd, "/" if absolute else "")]
        for i, part in enumerate(parts):
            last, nxt = i == len(parts) - 1, []
            for real, shown in found:
                if not any(ch in part for ch in "*?["):
                    cand = self.norm(part, real)
                    if self.exists(cand) and (last or self.isdir(cand)):
                        nxt.append((cand, shown + part if shown in ("", "/") else shown + "/" + part))
                    continue
                for name, is_dir in self.children(real):
                    if name.startswith(".") and not part.startswith("."):
                        continue
                    if fnmatch.fnmatchcase(name, part) and (last or is_dir):
                        nxt.append((self.join(real, name),
                                    shown + name if shown in ("", "/") else shown + "/" + name))
            found = nxt
        return sorted(shown for _, shown in found)

    def mode(self, p):
        """Permission bits of a path (like 0o644). Default: 755 folders/scripts, 644 files."""
        if p in self.modes:
            return self.modes[p]
        return 0o755 if (self.isdir(p) or p in self.x) else 0o644

    def set_mode(self, p, bits):
        self.modes[p] = bits
        if self.isfile(p):
            (self.x.add if bits & 0o100 else self.x.discard)(p)

    # ---------- changes ----------
    def write(self, p, text):
        self.d[p] = text

    def mkdirs(self, p):
        while p != "/" and not self.isdir(p):
            self.d[p + "/"] = ""
            p = self.parent(p)

    def remove(self, p):
        if self.isdir(p):
            base = self.dkey(p)
            for k in [k for k in self.d if k.startswith(base)]:
                del self.d[k]
            self.x = {k for k in self.x if not k.startswith(base)}
            self.modes = {k: v for k, v in self.modes.items() if not k.startswith(base)}
        else:
            del self.d[p]
            self.x.discard(p)
            self.modes.pop(p, None)

    def copy_tree(self, src, dst):
        base = self.dkey(src)
        self.d[dst + "/"] = ""
        for k in [k for k in self.d if k.startswith(base) and k != base]:
            self.d[dst + "/" + k[len(base):]] = self.d[k]

    def rename(self, src, dst):
        if self.isdir(src):
            base = self.dkey(src)
            for k in [k for k in self.d if k.startswith(base)]:
                self.d[dst + "/" + k[len(base):]] = self.d.pop(k)
            self.x = {dst + "/" + k[len(base):] if k.startswith(base) else k for k in self.x}
            self.modes = {(dst + "/" + k[len(base):] if k.startswith(base) else k): v for k, v in self.modes.items()}
        else:
            self.d[dst] = self.d.pop(src)
            if src in self.modes:
                self.modes[dst] = self.modes.pop(src)
            if src in self.x:
                self.x.discard(src)
                self.x.add(dst)
