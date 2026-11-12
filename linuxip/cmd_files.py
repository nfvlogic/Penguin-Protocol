"""File commands: pwd cd ls tree cat less echo mkdir rmdir touch cp mv rm chmod find du df."""
import re
import fnmatch

from .core import HOME, USER, ShellError, c


def perm_string(bits):
    """0o640 -> 'rw-r-----'"""
    return "".join(ch if bits & (1 << (8 - i)) else "-" for i, ch in enumerate("rwxrwxrwx"))


def apply_mode(bits, spec):
    """New permission bits after `chmod SPEC` (octal like 640, or symbolic like u+x,g-w)."""
    if spec.isdigit():
        return int(spec, 8)
    for clause in spec.split(","):
        m = re.fullmatch(r"([ugoa]*)([-+=])([rwx]*)", clause)
        who, op, what = m.group(1) or "a", m.group(2), m.group(3)
        mask = 0
        for w in ("ugo" if "a" in who else who):
            shift = {"u": 6, "g": 3, "o": 0}[w]
            mask |= sum(v << shift for ch, v in (("r", 4), ("w", 2), ("x", 1)) if ch in what)
        if op == "+":
            bits |= mask
        elif op == "-":
            bits &= ~mask
        else:
            clear = sum(7 << {"u": 6, "g": 3, "o": 0}[w] for w in ("ugo" if "a" in who else who))
            bits = (bits & ~clear) | mask
    return bits


def human(n):
    for unit in ("", "K", "M", "G"):
        if n < 1024 or unit == "G":
            return f"{n:.1f}{unit}" if unit and n < 10 else f"{int(n)}{unit}"
        n /= 1024


class FileCommands:
    # ---------------------------------------------------------- navigation
    def cmd_pwd(self, args, stdin):
        return self.cwd

    def cmd_cd(self, args, stdin):
        if len(args) > 1:
            raise ShellError("bash: cd: too many arguments", 1, tip="folder names with spaces need quotes")
        target = args[0] if args else HOME
        shown = None
        if target == "-":
            target = shown = self.oldpwd
        p = self.path(target)
        if self.fs.isfile(p):
            raise ShellError(f"bash: cd: {target}: Not a directory", 1, tip=f"{target} is a file: read it with cat")
        if not self.fs.isdir(p):
            tip = ("your home folder is ~ (type cd ~ or just cd)" if target == "home"
                   else self.missing_tip(target, "cd"))
            raise ShellError(f"bash: cd: {target}: No such file or directory", 1, tip=tip)
        self.oldpwd, self.cwd = self.cwd, p
        self.env["OLDPWD"], self.env["PWD"] = self.oldpwd, p
        return shown

    # ---------------------------------------------------------- listing
    def entry(self, full, name, is_dir, o):
        """Format one ls entry (short or long)."""
        exe = full in self.fs.x
        shown = c("1;34", name) if is_dir else (c("1;32", name) if exe else name)
        if "F" in o:
            shown += "/" if is_dir else ("*" if exe else "")
        if "l" not in o:
            return shown
        perm = ("d" if is_dir else "-") + perm_string(self.fs.mode(full))
        owner = "root" if not self.writable(full) and full != HOME else USER
        size = 4096 if is_dir else len(self.fs.d.get(full, ""))
        size = human(size) if "h" in o else str(size)
        links = 2 if is_dir else 1
        return f"{perm} {links} {owner:<7} {owner:<7} {size:>5} Nov 12 09:00 {shown}"

    def cmd_ls(self, args, stdin):
        o, targets = self.opts(args, "ls", "alhAF1dCR")
        targets = targets or ["."]
        files, dirs = [], []
        for t in targets:
            p = self.path(t)
            if self.fs.isfile(p) or ("d" in o and self.fs.isdir(p)):
                files.append((t, p))
            elif self.fs.isdir(p):
                dirs.append((t, p))
            else:
                self.warn(f"ls: cannot access '{t}': No such file or directory", self.missing_tip(t, "ls"))
        if "R" in o:  # -R: every folder is followed by the folders inside it
            def expand(t, p):
                yield t, p
                for n, d in self.fs.children(p):
                    if d and ("a" in o or "A" in o or not n.startswith(".")):
                        yield from expand(t.rstrip("/") + "/" + n, self.fs.join(p, n))
            dirs = [pair for t, p in dirs for pair in expand(t, p)]
        sep = "\n" if ("l" in o or "1" in o or self.pipe_out) else "  "
        blocks = []
        if files:
            blocks.append(sep.join(self.entry(p, t, self.fs.isdir(p), o) for t, p in files))
        for t, p in dirs:
            items = []
            if "a" in o:
                items += [(p, ".", True), (self.fs.parent(p), "..", True)]
            items += [(self.fs.join(p, n), n, d) for n, d in self.fs.children(p)
                      if "a" in o or "A" in o or not n.startswith(".")]
            lines = [self.entry(full, n, d, o) for full, n, d in items]
            body = ("total " + str(4 * len(items)) + ("\n" if lines else "")) if "l" in o else ""
            body += sep.join(lines)
            if len(targets) > 1 or "R" in o:
                body = f"{t}:\n{body}"
            blocks.append(body)
        return "\n\n".join(b for b in blocks if b)

    def cmd_dir(self, args, stdin):
        self.tip("dir works on Linux too, but everybody uses ls")
        return self.cmd_ls(args, stdin)

    def cmd_tree(self, args, stdin):
        o, pos = self.opts(args, "tree", "ad")
        start = pos[0] if pos else "."
        root = self.path(start)
        if not self.fs.isdir(root):
            return f"{start} [error opening dir]\n\n0 directories, 0 files"
        lines, counts = [c("1;34", start)], [0, 0]

        def walk(p, prefix):
            kids = [(n, d) for n, d in self.fs.children(p) if ("a" in o or not n.startswith("."))
                    and (d or "d" not in o)]
            for i, (n, d) in enumerate(kids):
                last = i == len(kids) - 1
                lines.append(prefix + ("└── " if last else "├── ") + (c("1;34", n) if d else n))
                counts[0 if d else 1] += 1
                if d:
                    walk(self.fs.join(p, n), prefix + ("    " if last else "│   "))
        walk(root, "")
        files = f", {counts[1]} files" if "d" not in o else ""
        return "\n".join(lines + ["", f"{counts[0]} directories{files}"])

    # ---------------------------------------------------------- reading
    def cmd_cat(self, args, stdin):
        o, files = self.opts(args, "cat", "nA")
        text = self.gather(files, stdin, "cat", "cat notes.md")
        if "A" in o:  # show hidden characters: $ = end of line, ^M = Windows carriage return, ^I = tab
            text = "\n".join(l.replace("\r", "^M").replace("\t", "^I") + "$" for l in text.split("\n"))
        if "n" in o:
            text = "\n".join(f"{i:>6}\t{l}" for i, l in enumerate(text.split("\n"), 1))
        return text

    def cmd_less(self, args, stdin):
        self.tip("in real Linux, less opens a viewer: arrows to scroll, / to search, q to quit")
        return self.gather(args, stdin, "less", "less server.log")

    cmd_more = cmd_less

    def cmd_echo(self, args, stdin):
        while args and args[0] in ("-n", "-e", "-E"):
            args = args[1:]
        return " ".join(args)

    # ---------------------------------------------------------- creating
    def cmd_mkdir(self, args, stdin):
        o, names = self.opts(args, "mkdir", "pv")
        if not names:
            raise ShellError("mkdir: missing operand\nTry 'mkdir --help' for more information.", 1,
                             tip="example: mkdir reports")
        for n in names:
            p = self.path(n)
            if self.fs.exists(p):
                if not ("p" in o and self.fs.isdir(p)):
                    self.warn(f"mkdir: cannot create directory '{n}': File exists")
            elif not self.writable(p):
                self.warn(f"mkdir: cannot create directory '{n}': Permission denied")
            elif not self.fs.isdir(self.fs.parent(p)) and "p" not in o:
                self.warn(f"mkdir: cannot create directory '{n}': No such file or directory",
                          "the parent folder does not exist; mkdir -p also creates the missing parents")
            else:
                self.fs.mkdirs(p)

    def cmd_rmdir(self, args, stdin):
        for n in [a for a in args if not a.startswith("-")]:
            p = self.path(n)
            if not self.fs.isdir(p):
                self.warn(f"rmdir: failed to remove '{n}': " +
                          ("Not a directory" if self.fs.isfile(p) else "No such file or directory"))
            elif self.fs.children(p):
                self.warn(f"rmdir: failed to remove '{n}': Directory not empty",
                          "rmdir only removes empty folders; rm -r removes a folder with everything inside")
            else:
                self.fs.remove(p)

    def cmd_touch(self, args, stdin):
        if not args:
            raise ShellError("touch: missing file operand\nTry 'touch --help' for more information.", 1,
                             tip="example: touch todo.md")
        for n in args:
            p = self.path(n)
            if self.fs.exists(p):
                continue
            if not self.fs.isdir(self.fs.parent(p)):
                self.warn(f"touch: cannot touch '{n}': No such file or directory",
                          "the folder does not exist yet (see man mkdir)")
            elif not self.writable(p):
                self.warn(f"touch: cannot touch '{n}': Permission denied")
            else:
                self.fs.write(p, "")

    # ---------------------------------------------------------- copy / move / delete
    def dest_for(self, cmd, src, dest_arg, many):
        """Where src ends up for cp/mv. Raises the real error when impossible."""
        dst = self.path(dest_arg)
        if self.fs.isdir(dst):
            return self.fs.join(dst, self.fs.base(src))
        if many:
            raise ShellError(f"{cmd}: target '{dest_arg}' is not a directory", 1)
        if dest_arg.endswith("/") or not self.fs.isdir(self.fs.parent(dst)):
            msg = (f"cp: cannot create regular file '{dest_arg}': No such file or directory" if cmd == "cp"
                   else f"mv: cannot move '{self.fs.base(src)}' to '{dest_arg}': No such file or directory")
            raise ShellError(msg, 1, tip="the destination folder does not exist (see man mkdir)")
        return dst

    def cmd_cp(self, args, stdin):
        o, names = self.opts(args, "cp", "rRfvi")
        if not names:
            raise ShellError("cp: missing file operand\nTry 'cp --help' for more information.", 1,
                             tip="example: cp report.txt archive/")
        if len(names) == 1:
            raise ShellError(f"cp: missing destination file operand after '{names[0]}'\n"
                             "Try 'cp --help' for more information.", 1, tip="cp needs a source and a destination")
        *sources, dest = names
        for s in sources:
            src = self.path(s)
            if not self.fs.exists(src):
                self.warn(f"cp: cannot stat '{s}': No such file or directory", self.missing_tip(s, "cp"))
                continue
            if self.fs.isdir(src) and not ("r" in o or "R" in o):
                self.warn(f"cp: -r not specified; omitting directory '{s}'", "to copy a folder use cp -r")
                continue
            dst = self.dest_for("cp", src, dest, len(sources) > 1)
            if not self.writable(dst):
                self.warn(f"cp: cannot create regular file '{dest}': Permission denied")
            elif self.fs.isdir(src):
                if dst == src or dst.startswith(src + "/"):
                    self.warn(f"cp: cannot copy a directory, '{s}', into itself, '{dest}'")
                else:
                    self.fs.copy_tree(src, dst)
            elif self.fs.isdir(dst):
                self.warn(f"cp: cannot overwrite directory '{dest}' with non-directory")
            else:
                self.fs.write(dst, self.fs.d[src])

    def cmd_mv(self, args, stdin):
        o, names = self.opts(args, "mv", "fvin")
        if len(names) < 2:
            raise ShellError("mv: missing file operand\nTry 'mv --help' for more information." if not names else
                             f"mv: missing destination file operand after '{names[0]}'\n"
                             "Try 'mv --help' for more information.", 1, tip="example: mv old.txt new.txt")
        *sources, dest = names
        for s in sources:
            src = self.path(s)
            if not self.fs.exists(src):
                self.warn(f"mv: cannot stat '{s}': No such file or directory", self.missing_tip(s, "mv"))
                continue
            dst = self.dest_for("mv", src, dest, len(sources) > 1)
            if not (self.writable(src) and self.writable(dst)) or (HOME + "/").startswith(src + "/"):
                self.warn(f"mv: cannot move '{s}' to '{dest}': Permission denied")
            elif dst == src or dst.startswith(src + "/"):
                self.warn(f"mv: cannot move '{s}' to a subdirectory of itself, '{dest}'")
            else:
                if self.fs.exists(dst):
                    self.fs.remove(dst)
                self.fs.rename(src, dst)

    def cmd_rm(self, args, stdin):
        o, names = self.opts(args, "rm", "rRfivd", longs=("--no-preserve-root",))
        recursive, force = "r" in o or "R" in o, "f" in o
        if not names:
            if force:
                return ""
            raise ShellError("rm: missing operand\nTry 'rm --help' for more information.", 1,
                             tip="example: rm old.txt")
        for n in names:
            p = self.path(n)
            if p == "/" and recursive:
                self.warn("rm: it is dangerous to operate recursively on '/'\n"
                          "rm: use --no-preserve-root to override this failsafe")
                continue
            if not self.fs.exists(p):
                if not force:
                    self.warn(f"rm: cannot remove '{n}': No such file or directory", self.missing_tip(n, "rm"))
                continue
            if self.fs.isdir(p) and not recursive:
                self.warn(f"rm: cannot remove '{n}': Is a directory", "to delete a folder and everything in it use rm -r")
                continue
            if not self.writable(p) or (HOME + "/").startswith(p + "/") or p == HOME:
                self.warn(f"rm: cannot remove '{n}': Permission denied",
                          "the practice shell protects your home folder and the system folders")
                continue
            self.fs.remove(p)

    def cmd_chmod(self, args, stdin):
        args = [a for a in args if a != "-R"]
        if len(args) < 2:
            raise ShellError(f"chmod: missing operand{' after ' + repr(args[0]) if args else ''}\n"
                             "Try 'chmod --help' for more information.", 1, tip="example: chmod +x run.sh")
        spec, names = args[0], args[1:]
        if not re.fullmatch(r"[0-7]{3,4}|([ugoa]*[-+=][rwx]*)(,[ugoa]*[-+=][rwx]*)*", spec):
            raise ShellError(f"chmod: invalid mode: '{spec}'\nTry 'chmod --help' for more information.", 1,
                             tip="use letters (u+x, g-w, o-rwx) or 3 digits like 755 / 644 / 600")
        for n in names:
            p = self.path(n)
            if not self.fs.exists(p):
                self.warn(f"chmod: cannot access '{n}': No such file or directory", self.missing_tip(n, "chmod"))
            elif not self.writable(p) or p == HOME:
                self.warn(f"chmod: changing permissions of '{n}': Operation not permitted")
            else:
                self.fs.set_mode(p, apply_mode(self.fs.mode(p), spec))

    # ---------------------------------------------------------- searching / disk
    def cmd_find(self, args, stdin):
        starts, i = [], 0
        while i < len(args) and not args[i].startswith("-"):
            starts.append(args[i])
            i += 1
        tests = []
        while i < len(args):
            a = args[i]
            if a in ("-name", "-iname", "-type"):
                if i + 1 >= len(args):
                    raise ShellError(f"find: missing argument to `{a}'", 1)
                tests.append((a, args[i + 1]))
                i += 2
            elif a.startswith("-"):
                raise ShellError(f"find: unknown predicate `{a}'", 1, tip="this shell supports -name, -iname and -type")
            else:
                raise ShellError(f"find: paths must precede expression: `{a}'", 1,
                                 tip='put wildcards in quotes so the shell does not expand them: find . -name "*.txt"')
        out = []
        for start in starts or ["."]:
            base = self.path(start)
            if not self.fs.exists(base):
                self.warn(f"find: '{start}': No such file or directory", self.missing_tip(start, "find"))
                continue
            paths = [base] + (self.fs.walk(base) if self.fs.isdir(base) else [])
            for p in paths:
                name = self.fs.base(p) if p != base else self.fs.base(base) if start not in (".", "./") else "."
                ok = True
                for t, v in tests:
                    if t == "-name":
                        ok = ok and fnmatch.fnmatchcase(name, v)
                    elif t == "-iname":
                        ok = ok and fnmatch.fnmatchcase(name.lower(), v.lower())
                    else:
                        ok = ok and ((v == "d") == self.fs.isdir(p))
                if ok:
                    out.append(start if p == base else start.rstrip("/") + p[len(base.rstrip("/")):])
        return "\n".join(out)

    def cmd_du(self, args, stdin):
        o, names = self.opts(args, "du", "shac")
        rows = []
        for n in names or ["."]:
            p = self.path(n)
            if not self.fs.exists(p):
                self.warn(f"du: cannot access '{n}': No such file or directory")
                continue
            folders = [p] if "s" in o or self.fs.isfile(p) else \
                [q for q in self.fs.walk(p) if self.fs.isdir(q)][::-1] + [p]
            for f in folders:
                size = 4096 + sum(len(v) + 4096 for k, v in self.fs.d.items() if k.startswith(f + "/"))
                shown = n if f == p else n.rstrip("/") + f[len(p):]
                rows.append(f"{human(size) if 'h' in o else size // 1024}\t{shown}")
        return "\n".join(rows)

    def cmd_df(self, args, stdin):
        o, _ = self.opts(args, "df", "hT")
        if "h" in o:
            return ("Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        63G   26G   37G  42% /\n"
                    "tmpfs           3.9G     0  3.9G   0% /dev/shm")
        return ("Filesystem     1K-blocks     Used Available Use% Mounted on\n"
                "/dev/sda1       65712536 27069440  38643096  42% /\ntmpfs            4049920        0   4049920   0% /dev/shm")
