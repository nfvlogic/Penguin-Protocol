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
    def cmd_grep(self, args, stdin):
        includes = [a.split("=", 1)[1] for a in args if a.startswith("--include=")]
        args = [a for a in args if not a.startswith("--include=")]
        o, pos = self.opts(args, "grep", "ivcnrRlLwEFhHoqs")
        if not pos:
            raise ShellError("Usage: grep [OPTION]... PATTERNS [FILE]...\nTry 'grep --help' for more information.",
                             2, tip="example: grep WARN server.log")
        pattern, files = pos[0], pos[1:]
        src = re.escape(pattern) if "F" in o else (pattern if "E" in o else bre_to_re(pattern))
        if "w" in o:
            src = r"(?<!\w)(?:" + src + r")(?!\w)"
        try:
            rx = re.compile(src, re.IGNORECASE if "i" in o else 0)
        except re.error:
            raise ShellError("grep: Unmatched ( or \\(" if "(" in pattern else "grep: Invalid regular expression", 2,
                             tip="special characters like [ ( . * need a backslash, or use grep -F for plain text")
        recursive = "r" in o or "R" in o
        sources = []
        if recursive:
            for f in files or ["."]:
                base = self.path(f)
                if self.fs.isfile(base):
                    sources.append((f, self.fs.d[base]))
                elif self.fs.isdir(base):
                    for p in self.fs.walk(base):
                        if self.fs.isfile(p) and (not includes or any(
                                fnmatch.fnmatchcase(self.fs.base(p), g) for g in includes)):
                            name = (p[len(base.rstrip("/")) + 1:] if f in (".", "./")
                                    else f.rstrip("/") + p[len(base.rstrip("/")):])
                            sources.append((name, self.fs.d[p]))
                else:
                    self.warn(f"grep: {f}: No such file or directory", self.missing_tip(f, "grep -r WORD"))
        elif files:
            for f in files:
                p = self.path(f)
                if self.fs.isdir(p):
                    self.warn(f"grep: {f}: Is a directory", "to search inside a folder use grep -r")
                elif not self.fs.isfile(p):
                    self.warn(f"grep: {f}: No such file or directory", self.missing_tip(f, f"grep {pattern}"))
                else:
                    sources.append((f, self.fs.d[p]))
        else:
            if stdin is None:
                raise ShellError("grep: reading from the keyboard is not supported in this practice shell", 2,
                                 tip="give a file (grep WORD FILE) or use a pipe (... | grep WORD)")
            sources.append(("(standard input)", stdin))
        show_name = ("H" in o or len(sources) > 1 or recursive) and "h" not in o
        color = not self.pipe_out
        out, total = [], 0
        for name, text in sources:
            count = 0
            for no, line in enumerate(text.split("\n"), 1):
                if bool(rx.search(line)) == ("v" in o):
                    continue
                count += 1
                if "c" in o or "l" in o or "L" in o or "q" in o:
                    continue
                shown = rx.sub(lambda m: c("1;31", m.group(0)), line) if color and "v" not in o else line
                if "o" in o and "v" not in o:
                    shown = "\n".join(c("1;31", m.group(0)) if color else m.group(0) for m in rx.finditer(line))
                prefix = ((c("35", name) + c("36", ":") if show_name else "") +
                          (c("32", str(no)) + c("36", ":") if "n" in o else ""))
                out.append(prefix + shown)
            total += count
            if "c" in o:
                out.append((c("35", name) + c("36", ":") if show_name else "") + str(count))
            elif "l" in o and count:
                out.append(c("35", name))
            elif "L" in o and not count:
                out.append(c("35", name))
        self._status = 2 if self._failed and not total else (0 if total else 1)
        return "" if "q" in o else "\n".join(out)

    def cmd_sort(self, args, stdin):
        o, files = self.opts(args, "sort", "nrufb", with_value="tk")
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
        o, files = self.opts(args, cmd, "qv", with_value="n")
        n = str(o.get("n", "10"))
        if not n.lstrip("+-").isdigit():
            raise ShellError(f"{cmd}: invalid number of lines: '{n}'", 1, tip=f"example: {cmd} -n 5 server.log")
        n = int(n.lstrip("+-"))
        msg = cmd + ": cannot open '{name}' for reading: No such file or directory"

        def cut(text):
            lines = text.split("\n") if text else []
            return "\n".join(lines[:n] if cmd == "head" else (lines[-n:] if n else []))
        if len(files) > 1:
            blocks = []
            for f in files:
                try:
                    blocks.append(f"==> {f} <==\n" + cut(self.read_text(f, cmd, msg)))
                except ShellError as e:
                    self.warn(str(e), e.tip)
            return "\n\n".join(blocks)
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
