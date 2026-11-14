"""Text commands: grep sort uniq cut head tail wc."""
import fnmatch
import re

from .core import ShellError, c


def bre_to_re(pattern):
    """Basic regular expression (grep default) -> Python regex.

    In BRE  + ? | ( ) { }  are plain characters; \\+ \\? \\| \\( \\) \\{ \\} are special.
    """
    out, i = [], 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\" and i + 1 < len(pattern):
            nxt = pattern[i + 1]
            out.append(nxt if nxt in "+?|(){}" else "\\" + nxt)
            i += 2
            continue
        if ch in "+?|(){}":
            out.append("\\" + ch)
        elif ch == "*" and (not out or out[-1] in ("^", "(", "|")):
            out.append("\\*")  # a leading * is literal in BRE
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def parse_list(spec, cmd):
    """'1,3' or '2-4' or '3-' -> function(index) -> bool (1-based)."""
    ranges = []
    for part in spec.split(","):
        a, dash, b = part.partition("-")
        try:
            lo = int(a) if a else 1
            hi = int(b) if b else (lo if not dash else 10 ** 6)
        except ValueError:
            raise ShellError(f"{cmd}: invalid field value '{part}'\nTry '{cmd} --help' for more information.", 1)
        if lo < 1:
            raise ShellError(f"{cmd}: fields and positions are numbered from 1", 1)
        ranges.append((lo, hi))
    return lambda k: any(lo <= k <= hi for lo, hi in ranges)


class TextCommands:
    LONG_GREP = {"--ignore-case": "-i", "--invert-match": "-v", "--count": "-c", "--line-number": "-n",
                 "--recursive": "-r", "--dereference-recursive": "-R", "--files-with-matches": "-l",
                 "--files-without-match": "-L", "--word-regexp": "-w", "--line-regexp": "-x",
                 "--extended-regexp": "-E", "--fixed-strings": "-F", "--perl-regexp": "-P",
                 "--only-matching": "-o", "--quiet": "-q", "--silent": "-q", "--no-filename": "-h",
                 "--with-filename": "-H", "--no-messages": "-s"}
    LONG_GREP_VALUE = {"--regexp": "-e", "--max-count": "-m", "--after-context": "-A", "--before-context": "-B",
                       "--context": "-C"}

    def cmd_grep(self, args, stdin):
        includes, excludes, fixed = [], [], []
        for a in args:
            if a.startswith("--include="):
                includes.append(a.split("=", 1)[1])
            elif a.startswith("--exclude="):
                excludes.append(a.split("=", 1)[1])
            elif a.startswith("--color") or a == "--no-color" or a.startswith("--exclude-dir"):
                continue
            elif re.fullmatch(r"-\d+", a):
                fixed += ["-C", a[1:]]
            elif a in self.LONG_GREP:
                fixed.append(self.LONG_GREP[a])
            elif a.split("=")[0] in self.LONG_GREP_VALUE and "=" in a:
                fixed += [self.LONG_GREP_VALUE[a.split("=")[0]], a.split("=", 1)[1]]
            else:
                fixed.append(a)
        o, pos = self.opts(fixed, "grep", "ivcnrRlLwEFPhHoqsx", with_value="emABC")
        # -e may be repeated: opts keeps the last one, so collect all of them again
        patterns = [fixed[k + 1] for k, a in enumerate(fixed[:-1]) if a == "-e"]
        if "e" in o and not patterns:
            patterns = [o["e"]]
        if not patterns:
            if not pos:
                raise ShellError("Usage: grep [OPTION]... PATTERNS [FILE]...\nTry 'grep --help' for more information.",
                                 2, tip="example: grep WARN server.log")
            patterns, pos = pos[0].split("\n"), pos[1:]
        files = pos
        if "F" in o:
            parts = [re.escape(p) for p in patterns]
        elif "E" in o or "P" in o:
            parts = patterns
        else:
            parts = [bre_to_re(p) for p in patterns]
        src = "|".join(f"(?:{p})" for p in parts) if len(parts) > 1 else parts[0]
        if "x" in o:
            src = r"^(?:" + src + r")$"
        elif "w" in o:
            src = r"(?<!\w)(?:" + src + r")(?!\w)"
        try:
            rx = re.compile(src, re.IGNORECASE if "i" in o else 0)
        except re.error:
            raise ShellError("grep: Unmatched ( or \\(" if "(" in "".join(patterns) else "grep: Invalid regular expression", 2,
                             tip="special characters like [ ( . * need a backslash, or use grep -F for plain text")
        try:
            after = int(o.get("A", o.get("C", 0)))
            before = int(o.get("B", o.get("C", 0)))
            limit = int(o["m"]) if "m" in o else None
        except ValueError:
            raise ShellError("grep: invalid context length argument", 2)
        recursive = "r" in o or "R" in o
        sources = []
        quiet_files = "s" in o

        def missing(f):
            if not quiet_files:
                self.warn(f"grep: {f}: No such file or directory", self.missing_tip(f, "grep WORD"))
            else:
                self._failed = True

        def wanted(name):
            base = name.rsplit("/", 1)[-1]
            if includes and not any(fnmatch.fnmatchcase(base, g) for g in includes):
                return False
            return not any(fnmatch.fnmatchcase(base, g) for g in excludes)
        if recursive:
            for f in files or ["."]:
                base = self.path(f)
                if self.fs.isfile(base):
                    sources.append((f, self.read_text(f, "grep")))
                elif self.fs.isdir(base):
                    for p in self.fs.walk(base):
                        if self.fs.isfile(p) and wanted(p):
                            name = (p[len(base.rstrip("/")) + 1:] if f in (".", "./")
                                    else f.rstrip("/") + p[len(base.rstrip("/")):])
                            sources.append((name, self.fs.d[p]))
                else:
                    missing(f)
        elif files:
            for f in files:
                p = self.path(f)
                if self.fs.isdir(p):
                    self.warn(f"grep: {f}: Is a directory", "to search inside a folder use grep -r")
                elif not self.fs.isfile(p):
                    missing(f)
                else:
                    try:
                        sources.append((f, self.read_text(f, "grep")))
                    except ShellError as e:
                        self.warn(str(e).replace("grep: ", "grep: ", 1), e.tip)
        else:
            if stdin is None:
                raise ShellError("grep: reading from the keyboard is not supported in this practice shell", 2,
                                 tip="give a file (grep WORD FILE) or use a pipe (... | grep WORD)")
            sources.append(("(standard input)", stdin))
        show_name = ("H" in o or len(sources) > 1 or recursive) and "h" not in o
        color = not self.pipe_out
        context = bool(before or after)
        invert = "v" in o
        out, total, printed_before = [], 0, False
        for name, text in sources:
            lines = text.split("\n")
            if text == "":
                lines = []
            hits = [k for k, line in enumerate(lines) if bool(rx.search(line)) != invert]
            if limit is not None:
                hits = hits[:limit]
            total += len(hits)
            label = (c("35", name) if show_name else "")

            def prefix(k, sep):
                return ((label + c("36", sep)) if show_name else "") + (c("32", str(k + 1)) + c("36", sep) if "n" in o else "")
            if "c" in o:
                out.append((label + c("36", ":") if show_name else "") + str(len(hits)))
                continue
            if "l" in o:
                if hits:
                    out.append(label or c("35", name))
                continue
            if "L" in o:
                if not hits:
                    out.append(label or c("35", name))
                continue
            if "q" in o:
                continue
            shown_upto = -1
            for k in hits:
                lo = max(k - before, shown_upto + 1)
                if context and printed_before and lo > shown_upto + 1 and lo == k - before:
                    out.append(c("36", "--"))
                elif context and printed_before and shown_upto == -1:
                    out.append(c("36", "--"))
                for j in range(lo, min(k + after, len(lines) - 1) + 1):
                    if j < k and j in hits:
                        continue
                    is_hit = j in hits
                    line = lines[j]
                    if is_hit and "o" in o and not invert:
                        for m in rx.finditer(line):
                            if m.group(0):
                                out.append(prefix(j, ":") + (c("1;31", m.group(0)) if color else m.group(0)))
                    else:
                        if is_hit and color and not invert:
                            line = rx.sub(lambda m: c("1;31", m.group(0)), line)
                        out.append(prefix(j, ":" if is_hit else "-") + line)
                    shown_upto = max(shown_upto, j)
                printed_before = True
        self._status = 2 if self._failed and not total else (0 if total else 1)
        return "" if "q" in o else "\n".join(out)

    def cmd_sort(self, args, stdin):
        o, files = self.opts(args, "sort", "nrufbh", with_value="tk")
        text = self.gather(files, stdin, "sort", "sort names.txt",
                           msg="sort: cannot read: {name}: No such file or directory")
        lines = text.split("\n") if text else []
        sep = o.get("t")
        if sep is not None and len(sep) != 1:
            raise ShellError("sort: multi-character tab '" + sep + "'", 2)
        key_field = None
        if "k" in o:
            try:
                key_field = int(str(o["k"]).split(",")[0].rstrip("nr"))
            except ValueError:
                raise ShellError(f"sort: invalid number at field start: invalid count at start of '{o['k']}'", 2)
            if "n" in str(o["k"]):
                o["n"] = True

        def key_text(line):
            if key_field is None:
                return line
            parts = line.split(sep) if sep else line.split()
            return parts[key_field - 1] if len(parts) >= key_field else ""

        def key(line):
            k = key_text(line)
            if "h" in o:
                m = re.match(r"\s*(-?\d+(?:\.\d+)?)([KMGTPkmgtp]?)", k)
                scale = {"": 1, "K": 1e3, "M": 1e6, "G": 1e9, "T": 1e12, "P": 1e15}
                return (float(m.group(1)) * scale[m.group(2).upper()] if m else 0.0, line)
            if "n" in o:
                m = re.match(r"\s*(-?\d+(?:\.\d+)?)", k)
                return (float(m.group(1)) if m else 0.0, line)
            return (k.lower(), k) if "f" in o else (k, "")
        lines.sort(key=key, reverse="r" in o)
        if "u" in o:
            seen, uniq = set(), []
            for line in lines:
                k = key_text(line)
                if k not in seen:
                    seen.add(k)
                    uniq.append(line)
            lines = uniq
        return "\n".join(lines)

    def cmd_uniq(self, args, stdin):
        o, files = self.opts(args, "uniq", "cdui")
        text = self.gather(files[:1], stdin, "uniq", "sort names.txt | uniq -c")
        groups = []
        for line in (text.split("\n") if text else []):
            same = groups and (groups[-1][0].lower() == line.lower() if "i" in o else groups[-1][0] == line)
            if same:
                groups[-1][1] += 1
            else:
                groups.append([line, 1])
        if "u" in o:
            groups = [g for g in groups if g[1] == 1]
        if "d" in o:
            groups = [g for g in groups if g[1] > 1]
        return "\n".join(f"{n:>7} {l}" if "c" in o else l for l, n in groups)

    def cmd_cut(self, args, stdin):
        o, files = self.opts(args, "cut", "s", with_value="dfc")
        if "f" not in o and "c" not in o:
            raise ShellError("cut: you must specify a list of bytes, characters, or fields\n"
                             "Try 'cut --help' for more information.", 1, tip='example: cut -d "," -f 2 data.csv')
        sep = o.get("d", "\t")
        if len(sep) != 1:
            raise ShellError("cut: the delimiter must be a single character\nTry 'cut --help' for more information.", 1)
        text = self.gather(files, stdin, "cut", 'cut -d "," -f 2 data.csv')
        out = []
        for line in (text.split("\n") if text else []):
            if "c" in o:
                want = parse_list(str(o["c"]), "cut")
                out.append("".join(ch for k, ch in enumerate(line, 1) if want(k)))
            elif sep not in line:
                if "s" not in o:
                    out.append(line)  # real cut prints lines without the delimiter unchanged
            else:
                want = parse_list(str(o["f"]), "cut")
                out.append(sep.join(p for k, p in enumerate(line.split(sep), 1) if want(k)))
        return "\n".join(out)

    def head_tail(self, args, stdin, cmd):
        o, files = self.opts(args, cmd, "qvf", with_value="nc")
        by_bytes = "c" in o
        spec = str(o.get("c" if by_bytes else "n", "10"))
        if not re.fullmatch(r"[+-]?\d+", spec):
            raise ShellError(f"{cmd}: invalid number of {'bytes' if by_bytes else 'lines'}: '{spec}'", 1,
                             tip=f"example: {cmd} -n 5 server.log")
        n = int(spec.lstrip("+-"))
        plus, minus = spec.startswith("+"), spec.startswith("-")
        msg = cmd + ": cannot open '{name}' for reading: No such file or directory"

        def cut(text):
            items = list(text) if by_bytes else (text.split("\n") if text else [])
            if cmd == "head":
                kept = items[:-n] if minus and n else (items[:0] if minus else items[:n])
            else:
                kept = items[n - 1:] if plus and n else (items if plus else (items[-n:] if n else []))
            return "".join(kept) if by_bytes else "\n".join(kept)
        if "f" in o:
            self.tip("tail -f keeps waiting for new lines until you press Ctrl+C: here it shows the end and stops")
        if (len(files) > 1 or "v" in o) and "q" not in o:
            blocks = []
            for f in files:
                try:
                    blocks.append(f"==> {f} <==\n" + cut(self.read_text(f, cmd, msg)))
                except ShellError as e:
                    self.warn(str(e), e.tip)
            return "\n\n".join(blocks)
        if len(files) > 1:
            texts = []
            for f in files:
                try:
                    texts.append(cut(self.read_text(f, cmd, msg)))
                except ShellError as e:
                    self.warn(str(e), e.tip)
            return "\n".join(texts)
        return cut(self.gather(files, stdin, cmd, f"{cmd} -n 5 server.log", msg))

    def cmd_head(self, args, stdin):
        return self.head_tail(args, stdin, "head")

    def cmd_tail(self, args, stdin):
        return self.head_tail(args, stdin, "tail")

    def cmd_wc(self, args, stdin):
        o, files = self.opts(args, "wc", "lwcm")
        wanted = [k for k in "lwc" if k in o or (k == "c" and "m" in o)] or ["l", "w", "c"]

        def counts(text):
            lines = text.count("\n") + (1 if text else 0)
            return {"l": lines, "w": len(text.split()), "c": len(text) + (1 if text else 0)}
        rows, total = [], {"l": 0, "w": 0, "c": 0}
        sources = []
        if files:
            for f in files:
                try:
                    sources.append((f, self.read_text(f, "wc")))
                except ShellError as e:
                    self.warn(str(e), e.tip)
        else:
            sources.append(("", self.gather([], stdin, "wc", "wc -l server.log")))
        if len(wanted) == 1 and len(sources) == 1:
            width = 1                       # like GNU wc: a single number is not padded
        elif files:
            width = len(str(sum(counts(t)["c"] for _, t in sources)))  # GNU wc pads to the total size
        else:
            width = 7
        for name, text in sources:
            cn = counts(text)
            for k in total:
                total[k] += cn[k]
            rows.append(" ".join(f"{cn[k]:>{width}}" for k in wanted) + (f" {name}" if name else ""))
        if len(sources) > 1:
            rows.append(" ".join(f"{total[k]:>{width}}" for k in wanted) + " total")
        return "\n".join(rows)
