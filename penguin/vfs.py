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
        self.d, self.x, self.modes, self.links = {}, set(), {}, {}   # x = executable files, modes = chmod'ed paths, links = symlinks
        self.reset()

    def reset(self):
        passwd = ("root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
                  "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\nmysql:x:114:121:MySQL Server,,,:/nonexistent:/bin/false\n"
                  "sshd:x:106:65534::/run/sshd:/usr/sbin/nologin\nanalyst:x:1000:1000:analyst,,,:/home/analyst:/bin/bash")
        self.d = {"/": "", "/etc/": "", "/etc/hosts": HOSTS, "/home/": "", HOME + "/": "",
                  "/tmp/": "", "/dev/": "", "/dev/null": "", "/usr/": "", "/usr/bin/": "", "/usr/sbin/": "", "/usr/lib/": "",
                  "/usr/local/": "", "/usr/local/bin/": "", "/usr/share/": "", "/var/": "", "/var/log/": "", "/var/lib/": "",
                  "/var/tmp/": "", "/opt/": "", "/srv/": "", "/root/": "", "/boot/": "", "/mnt/": "", "/media/": "", "/run/": "",
                  "/proc/": "", "/sys/": "", "/lib/": "",
                  "/etc/passwd": passwd, "/etc/group": "root:x:0:\nusers:x:100:analyst\nanalyst:x:1000:",
                  "/etc/shadow": "root:!:20000:0:99999:7:::\nanalyst:$y$j9T$redacted:20000:0:99999:7:::",
                  "/etc/hostname": "penguin", "/etc/os-release": 'PRETTY_NAME="Ubuntu 24.04.1 LTS"\nNAME="Ubuntu"\nVERSION_ID="24.04"\n'
                  'VERSION="24.04.1 LTS (Noble Numbat)"\nID=ubuntu\nID_LIKE=debian',
                  "/etc/shells": "/bin/sh\n/bin/bash\n/usr/bin/bash", "/etc/resolv.conf": "nameserver 10.20.30.1\nsearch corp.local",
                  "/var/log/syslog": "Nov 12 08:55:01 penguin CRON[2210]: (root) CMD (command -v debian-sa1)",
                  "/var/log/auth.log": "Nov 12 08:55:20 penguin sshd[2301]: Accepted publickey for analyst from 10.20.30.5",
                  "/proc/cpuinfo": "processor\t: 0\nmodel name\t: Intel(R) Xeon(R) CPU\ncpu cores\t: 4",
                  "/proc/meminfo": "MemTotal:        8056240 kB\nMemFree:         4296904 kB\nMemAvailable:    5878928 kB"}
        self.x, self.links = set(), {"/bin": "usr/bin", "/sbin": "usr/sbin", "/lib64": "usr/lib"}
        self.modes = {"/root": 0o700, "/etc/shadow": 0o640, "/var/log/syslog": 0o640, "/var/log/auth.log": 0o640,
                      "/boot": 0o755, "/etc/passwd": 0o644}
        from .manual import MAN, PRACTICE
        for name in MAN:           # every real command is a file in /usr/bin
            if name not in PRACTICE and name not in ("cd", "export", "unset", "source", "history", "type", "exit", "help", "alias",
                                                   "unalias", "read", "let", "break", "continue", "umask", "pushd", "popd", "dirs",
                                                   "[[", "deactivate", "ll", "dir"):
                self.d["/usr/bin/" + name] = ""
                self.x.add("/usr/bin/" + name)

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

    def follow(self, p):
        """Resolve symbolic links in a path (up to 20 hops, like the kernel)."""
        for _ in range(20):
            parts = p.strip("/").split("/") if p != "/" else []
            for k in range(1, len(parts) + 1):
                prefix = "/" + "/".join(parts[:k])
                if prefix in self.links:
                    target = self.links[prefix]
                    base = self.norm(target, self.parent(prefix))
                    p = base + ("/" + "/".join(parts[k:]) if parts[k:] else "")
                    break
            else:
                return p
        return p

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
        out += [(k[len(base):], False) for k in self.links if k.startswith(base) and "/" not in k[len(base):]]
        return sorted(out, key=lambda e: sort_key(e[0]))

    def walk(self, p):
        """Every path below folder p (files and folders), sorted."""
        base = self.dkey(p)
        return sorted([k.rstrip("/") for k in self.d if k.startswith(base) and k != base] +
                      [k for k in self.links if k.startswith(base)])

    def glob(self, pattern, cwd):
        """Expand * ? [..] like bash. Returns [] when nothing matches."""
        absolute = pattern.startswith("/")
        dirs_only = pattern.endswith("/") and len(pattern) > 1
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
        if dirs_only:
            return sorted(shown + "/" for real, shown in found if self.isdir(real))
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
        if p in self.links:
            del self.links[p]
            return
        if self.isdir(p):
            base = self.dkey(p)
            for k in [k for k in self.d if k.startswith(base)]:
                del self.d[k]
            self.x = {k for k in self.x if not k.startswith(base)}
            self.modes = {k: v for k, v in self.modes.items() if not k.startswith(base)}
            self.links = {k: v for k, v in self.links.items() if not k.startswith(base)}
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
        if src in self.links:
            self.links[dst] = self.links.pop(src)
        elif self.isdir(src):
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
