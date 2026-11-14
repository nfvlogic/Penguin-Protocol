"""File commands: pwd cd ls tree cat less echo mkdir rmdir touch cp mv rm chmod find du df."""
import re
import fnmatch

from .core import HOME, USER, ShellError, c, vlen


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
        if not self.access(p, 1):
            raise ShellError(f"bash: cd: {target}: Permission denied", 1,
                             tip="the folder has no execute (x) permission: see man chmod")
        self.oldpwd, self.cwd = self.cwd, p
        self.env["OLDPWD"], self.env["PWD"] = self.oldpwd, p
        return shown

    # ---------------------------------------------------------- listing
    def entry(self, full, name, is_dir, o):
        """Format one ls entry (short or long)."""
        if full in self.fs.links:
            target = self.fs.links[full]
            shown = c("1;36", name) + (" -> " + target if "l" in o else "")
            if "F" in o:
                shown = c("1;36", name) + "@"
            if "l" not in o:
                return shown
            return f"lrwxrwxrwx 1 {USER:<7} {USER:<7} {len(target):>5} Nov 12 09:00 {shown}"
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
        links = 2 + sum(1 for _, d in self.fs.children(full) if d) if is_dir else 1
        return f"{perm} {links} {owner:<7} {owner:<7} {size:>5} Nov 12 09:00 {shown}"

    def columns(self, items):
        """Short ls output: names in columns that fill the terminal, filled top to bottom like GNU ls."""
        if not items:
            return ""
        width, n = self.width(), len(items)
        for rows in range(1, n + 1):
            cols = [items[i:i + rows] for i in range(0, n, rows)]
            widths = [max(vlen(x) for x in col) + 2 for col in cols]
            if sum(widths) - 2 <= width or rows == n:
                break
        lines = []
        for r in range(rows):
            cells = [col[r] + " " * (widths[k] - vlen(col[r])) for k, col in enumerate(cols) if r < len(col)]
            lines.append("".join(cells).rstrip())
        return "\n".join(lines)

    def cmd_ls(self, args, stdin):
        o, targets = self.opts(args, "ls", "alhAF1dCRtSr")
        targets = targets or ["."]
        files, dirs = [], []
        for t in targets:
            p = self.path(t)
            raw = self.path(t, follow=False)
            if raw in self.fs.links and (not self.fs.isdir(p) or any(k in o for k in "lFd")):
                files.append((t, raw))     # ls -l shows the link itself (and a dangling link is never an error)
            elif self.fs.isfile(p) or ("d" in o and self.fs.isdir(p)):
                files.append((t, p))
            elif self.fs.isdir(p):
                if not self.access(p, 4):
                    self.warn(f"ls: cannot open directory '{t}': Permission denied",
                              "the folder has no read (r) permission: see man chmod" if self.writable(p)
                              else "this folder belongs to root: normal users cannot open it")
                    continue
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
        long_or_one = "l" in o or "1" in o or self.pipe_out

        def order(items):
            if "S" in o:
                items = sorted(items, key=lambda x: -(4096 if x[2] else len(self.fs.d.get(x[0], ""))))
            if "r" in o:
                items = items[::-1]
            return items

        def blocks(full, is_dir):
            return 4 if is_dir else (-(-len(self.fs.d.get(full, "")) // 4096) * 4)
        missing = self._failed          # a name that does not exist: GNU ls exits with 2
        blocks_out = []
        if files:
            ordered = order([(p, t, self.fs.isdir(p)) for t, p in files])
            shown = [self.entry(p, t, d, o) for p, t, d in ordered]
            blocks_out.append("\n".join(shown) if long_or_one else self.columns(shown))
        for t, p in dirs:
            items = []
            if "a" in o:
                items += [(p, ".", True), (self.fs.parent(p), "..", True)]
            items += [(self.fs.join(p, n), n, d) for n, d in self.fs.children(p)
                      if "a" in o or "A" in o or not n.startswith(".")]
            items = order(items)
            shown = [self.entry(full, n, d, o) for full, n, d in items]
            body = ""
            if "l" in o:
                body = "total " + str(sum(blocks(full, d) for full, _, d in items)) + ("\n" if shown else "")
            body += "\n".join(shown) if long_or_one else self.columns(shown)
            if len(targets) > 1 or "R" in o:
                body = f"{t}:\n{body}"
            blocks_out.append(body)
        if missing:
            self._status = 2
        return "\n\n".join(b for b in blocks_out if b)

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
        o, args = self.opts(args, "touch", "acm", with_value="dtr")
        if not args:
            raise ShellError("touch: missing file operand\nTry 'touch --help' for more information.", 1,
                             tip="example: touch todo.md")
        for n in args:
            p = self.path(n)
            if self.fs.exists(p) or "c" in o:
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

    def cmd_ln(self, args, stdin):
        o, names = self.opts(args, "ln", "sfnT")
        if len(names) < 2:
            raise ShellError(f"ln: missing {'file' if not names else 'destination file'} operand"
                             f"{' after ' + repr(names[0]) if names else ''}\nTry 'ln --help' for more information.", 1,
                             tip="example: ln -s /real/file shortcut")
        *sources, dest = names
        for s in sources:
            link = self.path(dest, follow=False)
            # without -n an existing link to a folder is followed: the new link goes INSIDE that folder
            if self.fs.isdir(self.path(dest)) and not ("n" in o and self.path(dest, follow=False) in self.fs.links):
                link = self.fs.join(self.path(dest), self.fs.base(self.path(s, follow=False)))
            if not self.writable(link) or not self.fs.isdir(self.fs.parent(link)):
                self.warn(f"ln: failed to create {'symbolic ' if 's' in o else 'hard '}link '{dest}': "
                          + ("Permission denied" if self.fs.isdir(self.fs.parent(link)) else "No such file or directory"))
            elif link in self.fs.links or self.fs.exists(link):
                if "f" in o:
                    self.fs.remove(link)
                else:
                    self.warn(f"ln: failed to create {'symbolic ' if 's' in o else 'hard '}link '{dest}': File exists",
                              "ln -sf replaces it")
                    continue
            if "s" in o:
                self.fs.links[link] = s
            else:
                src = self.path(s)
                if not self.fs.isfile(src):
                    self.warn(f"ln: failed to access '{s}': No such file or directory", self.missing_tip(s, "ln"))
                else:
                    self.fs.write(link, self.fs.d[src])   # a hard link looks like a second name for the same file
        return ""

    def cmd_readlink(self, args, stdin):
        o, names = self.opts(args, "readlink", "fem")
        if not names:
            raise ShellError("readlink: missing operand\nTry 'readlink --help' for more information.", 1)
        out = []
        for n in names:
            raw = self.path(n, follow=False)
            if "f" in o or "e" in o or "m" in o:
                target = self.fs.follow(raw)
                if self.fs.exists(target) or "m" in o or "f" in o:
                    out.append(target)
                else:
                    self._status = 1
            elif raw in self.fs.links:
                out.append(self.fs.links[raw])
            else:
                self._status = 1
        return "\n".join(out)

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
            src = self.path(s, follow=False)
            if src not in self.fs.links:
                src = self.path(s)
            if not self.fs.exists(src) and src not in self.fs.links:
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
            p = self.path(n, follow=False)
            if p in self.fs.links:
                self.fs.remove(p)
                continue
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
        while i < len(args) and not (args[i].startswith("-") or args[i] in ("!", "(", ")")):
            starts.append(args[i])
            i += 1
        expr = args[i:]
        pos, opts = [0], {"maxdepth": None, "mindepth": 0, "actions": False}

        def need(name):
            if pos[0] + 1 >= len(expr):
                raise ShellError(f"find: missing argument to `{name}'", 1)
            pos[0] += 1
            return expr[pos[0]]

        def primary():
            tok = expr[pos[0]]
            if tok in ("!", "-not"):
                pos[0] += 1
                return ("not", primary())
            if tok == "(":
                pos[0] += 1
                node = parse_or()
                if pos[0] >= len(expr) or expr[pos[0]] != ")":
                    raise ShellError("find: missing closing ')'", 1)
                pos[0] += 1
                return node
            if tok in ("-name", "-iname", "-path", "-ipath", "-wholename", "-type", "-size", "-mtime", "-mmin", "-atime",
                       "-ctime", "-perm", "-user", "-group", "-newer"):
                node = (tok, need(tok))
            elif tok in ("-maxdepth", "-mindepth"):
                val = need(tok)
                if not val.isdigit():
                    raise ShellError(f"find: Expected a positive decimal integer argument to `{tok}', but got `{val}'", 1)
                opts[tok[1:]] = int(val)
                node = ("true", None)
            elif tok in ("-empty", "-true", "-false", "-print", "-print0", "-delete", "-depth", "-readable", "-writable",
                         "-executable"):
                if tok in ("-print", "-print0", "-delete"):
                    opts["actions"] = True
                node = (tok, None)
            elif tok in ("-exec", "-execdir", "-ok"):
                cmd = []
                pos[0] += 1
                while pos[0] < len(expr) and expr[pos[0]] not in (";", "+"):
                    cmd.append(expr[pos[0]])
                    pos[0] += 1
                if pos[0] >= len(expr):
                    raise ShellError(f"find: missing argument to `{tok}'", 1,
                                     tip="end the command with \\; (a backslash and a semicolon)")
                opts["actions"] = True
                node = ("-exec", (cmd, expr[pos[0]] == "+"))
            elif tok.startswith("-"):
                raise ShellError(f"find: unknown predicate `{tok}'", 1,
                                 tip="supported: -name -iname -path -type -size -mtime -mmin -empty -perm -user -maxdepth "
                                     "-mindepth -exec -delete -print and ! ( ) -o")
            else:
                raise ShellError(f"find: paths must precede expression: `{tok}'", 1,
                                 tip='put wildcards in quotes so the shell does not expand them: find . -name "*.txt"')
            pos[0] += 1
            return node

        def parse_and():
            node = primary()
            while pos[0] < len(expr) and expr[pos[0]] not in ("-o", "-or", ")"):
                if expr[pos[0]] in ("-a", "-and"):
                    pos[0] += 1
                node = ("and", node, primary())
            return node

        def parse_or():
            node = parse_and()
            while pos[0] < len(expr) and expr[pos[0]] in ("-o", "-or"):
                pos[0] += 1
                node = ("or", node, parse_and())
            return node
        tree = ("true", None)
        if expr:
            tree = parse_or()
            if pos[0] < len(expr):
                raise ShellError(f"find: unexpected extra predicate `{expr[pos[0]]}'" if expr[pos[0]] != ")"
                                 else "find: unmatched ')'", 1)
        if not opts["actions"]:
            tree = ("and", tree, ("-print", None))
        out, batches = [], {}

        def owner_of(p):
            return "root" if not self.writable(p) and p != HOME else USER

        def test(node, ctx):
            kind = node[0]
            if kind == "and":
                return test(node[1], ctx) and test(node[2], ctx)
            if kind == "or":
                return test(node[1], ctx) or test(node[2], ctx)
            if kind == "not":
                return not test(node[1], ctx)
            p, name, shown = ctx["p"], ctx["name"], ctx["shown"]
            is_dir = self.fs.isdir(p)
            v = node[1]
            if kind in ("true", "-true", "-depth"):
                return True
            if kind == "-false":
                return False
            if kind == "-name":
                return fnmatch.fnmatchcase(name, v)
            if kind == "-iname":
                return fnmatch.fnmatchcase(name.lower(), v.lower())
            if kind in ("-path", "-ipath", "-wholename"):
                return fnmatch.fnmatchcase(shown if kind != "-ipath" else shown.lower(), v if kind != "-ipath" else v.lower())
            if kind == "-type":
                if v not in ("f", "d", "l"):
                    raise ShellError(f"find: Unknown argument to -type: {v}", 1, tip="-type f = files, -type d = folders")
                if v == "l":
                    return p in self.fs.links
                return (v == "d") == is_dir and p not in self.fs.links
            if kind == "-empty":
                return (not self.fs.children(p)) if is_dir else not self.fs.d.get(p)
            if kind == "-size":
                m = re.fullmatch(r"([+-]?)(\d+)([cwbkMG]?)", v)
                if not m:
                    raise ShellError(f"find: Invalid argument `{v}' to -size", 1, tip="example: -size +1k  (bigger than 1 KiB)")
                unit = {"c": 1, "w": 2, "b": 512, "": 512, "k": 1024, "M": 1024 ** 2, "G": 1024 ** 3}[m.group(3)]
                size = 4096 if is_dir else len(self.fs.d.get(p, ""))
                units = -(-size // unit)
                n = int(m.group(2))
                return units > n if m.group(1) == "+" else (units < n if m.group(1) == "-" else units == n)
            if kind in ("-mtime", "-atime", "-ctime", "-mmin"):
                m = re.fullmatch(r"([+-]?)(\d+)", v)
                if not m:
                    raise ShellError(f"find: Invalid argument `{v}' to {kind}", 1)
                n, age = int(m.group(2)), 0     # everything here was modified a moment ago
                return age > n if m.group(1) == "+" else (age < n if m.group(1) == "-" else age == n)
            if kind == "-perm":
                m = re.fullmatch(r"([-/]?)([0-7]{3,4})", v)
                if not m:
                    raise ShellError(f"find: Invalid mode `{v}'", 1, tip="example: -perm 644")
                want, bits = int(m.group(2), 8), self.fs.mode(p)
                return (bits & want) == want if m.group(1) == "-" else (bool(bits & want) if m.group(1) == "/" else bits == want)
            if kind in ("-user", "-group"):
                return owner_of(p) == v
            if kind in ("-readable", "-writable", "-executable"):
                bit = {"-readable": 0o400, "-writable": 0o200, "-executable": 0o100}[kind]
                return bool(self.fs.mode(p) & bit)
            if kind in ("-print", "-print0"):
                out.append(shown)
                return True
            if kind == "-delete":
                if p == base_path:
                    return True
                if not self.writable(p):
                    self.warn(f"find: cannot delete '{shown}': Permission denied")
                    return False
                if is_dir and self.fs.children(p):
                    self.warn(f"find: cannot delete '{shown}': Directory not empty")
                    return False
                self.fs.remove(p)
                return True
            if kind == "-exec":
                cmd, batch = v
                if batch:
                    batches.setdefault(id(node), (cmd, []))[1].append(shown)
                    return True
                argv = [shown if a == "{}" else a.replace("{}", shown) for a in cmd]
                self._status = None
                self._failed = False
                res = self.dispatch(argv, None)
                if res:
                    out.append(res)
                return (self._status if self._status is not None else (1 if self._failed else 0)) == 0
            raise ShellError(f"find: unknown predicate `{kind}'", 1)
        base_path = None
        for start in starts or ["."]:
            base_path = base = self.path(start)
            if not self.fs.exists(base):
                self.warn(f"find: '{start}': No such file or directory", self.missing_tip(start, "find"))
                continue
            paths = [base] + (self.fs.walk(base) if self.fs.isdir(base) else [])
            for p in paths:
                depth = 0 if p == base else p[len(base.rstrip("/")):].count("/")
                if opts["maxdepth"] is not None and depth > opts["maxdepth"] or depth < opts["mindepth"]:
                    continue
                shown = start if p == base else start.rstrip("/") + p[len(base.rstrip("/")):]
                name = self.fs.base(p) if p != base else (self.fs.base(base) if start not in (".", "./") else ".")
                test(tree, {"p": p, "name": name, "shown": shown})
        for cmd, shown_list in batches.values():
            argv = [a for a in cmd if a != "{}"] + shown_list if "{}" in cmd else cmd + shown_list
            res = self.dispatch(argv, None)
            if res:
                out.append(res)
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
                size = 4096 + sum(4096 if k.endswith("/") else -(-len(v) // 4096) * 4096
                                  for k, v in self.fs.d.items() if k.startswith(f + "/"))
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
