"""Compound commands like bash: for / while / until / if, the test builtin ([ ] and test), read, let,
break and continue, command substitution ($(...)) and multi-line input (the > prompt)."""
import fnmatch
import re

from .core import HOME, USER, ShellError
from .parser import scan, split_top

OPEN = {"for", "while", "until", "if"}
CLOSE = {"done", "fi"}
HEAD = {"do", "then", "else"}
MAX_LOOP = 10000


class LoopControl(BaseException):
    """break / continue travelling up to the loop (BaseException: the crash guard must not catch it)."""

    def __init__(self, kind, levels=1):
        super().__init__(kind)
        self.kind, self.levels = kind, levels


def first_word(seg):
    parts = seg.split(None, 1)
    return parts[0] if parts else ""


def segments(line):
    """Split a script at top-level ; and newlines into simple segments. 'do', 'then' and 'else' are
    separated from the command that follows them, so  for x in a b; do echo $x; done  becomes
    ['for x in a b', 'do', 'echo $x', 'done']."""
    out = []
    for _, text in split_top(line, [";", "\n"]):
        text = text.strip()
        if not text:
            continue
        word = first_word(text)
        if word in HEAD and text != word:
            out += [word, text[len(word):].strip()]
        else:
            out.append(text)
    return out


def needs_more(text):
    """True if the typed text is unfinished (open quote, open $( ), trailing \\, | && ||, unclosed
    for/while/if): bash then shows the > prompt and waits for more lines."""
    last_quote, depth = None, 0
    for _, _, quote, d in scan(text + " "):   # the extra space shows the state after the last character
        last_quote, depth = quote, d
    if last_quote in ("'", '"') or depth:
        return True
    stripped = text.rstrip()
    if stripped.endswith("\\") or stripped.endswith(("|", "&&", "||")):
        return True
    open_count = 0
    for seg in segments(text):
        word = first_word(seg)
        if word in OPEN:
            open_count += 1
        elif word in CLOSE:
            open_count -= 1
    return open_count > 0


def syntax_error(token):
    return ShellError(f"bash: syntax error near unexpected token `{token}'", 2)


class CompoundCommands:
    # ---------------------------------------------------------- command substitution
    def capture(self, text):
        """Run a command line and return what it printed (for $(...))."""
        buf = []
        self.capture_stack.append(buf)
        try:
            self.run_line(text)
        finally:
            self.capture_stack.pop()
        return "\n".join(buf).rstrip("\n")

    # ---------------------------------------------------------- running a line
    def run_line(self, line):
        word = first_word(line)
        if word in CLOSE | HEAD or word == "elif":
            e = syntax_error(word)
            self.show_error(str(e), e.tip)
            self.status = e.status
            return
        multi = "\n" in line
        segs = segments(line) if (multi or any(w in line for w in OPEN)) else None
        if segs is None or (not multi and not any(first_word(s) in OPEN for s in segs)):
            return self.run_simple(line)
        try:
            self.exec_segments(segs)
        except ShellError as e:
            self.show_error(str(e), e.tip)
            self.status = e.status
        except LoopControl:
            pass

    def exec_segments(self, segs):
        i = 0
        while i < len(segs) and self.running:
            word = first_word(segs[i])
            if word in OPEN:
                j = self.find_end(segs, i)
                self.exec_compound(segs[i:j + 1])
                i = j + 1
            elif word in CLOSE | HEAD or word == "elif":
                raise syntax_error(word)
            else:
                self.run_simple(segs[i])
                i += 1

    @staticmethod
    def find_end(segs, start):
        depth = 0
        for k in range(start, len(segs)):
            word = first_word(segs[k])
            if word in OPEN:
                depth += 1
            elif word in CLOSE:
                depth -= 1
                if depth == 0:
                    return k
        raise ShellError("bash: syntax error: unexpected end of file", 2,
                         tip="for needs done at the end, and if needs fi")

    def run_cond(self, segs):
        self.exec_segments(segs)
        return self.status == 0

    def loop_body(self, body):
        """Run a loop body once. Returns 'break' to stop the loop."""
        try:
            self.exec_segments(body)
        except LoopControl as lc:
            if lc.levels > 1:
                raise LoopControl(lc.kind, lc.levels - 1)
            return lc.kind if lc.kind == "break" else None
        return None

    def exec_compound(self, segs):
        word = first_word(segs[0])
        if segs[-1].split()[0] not in CLOSE:
            raise syntax_error(segs[-1].split()[0])
        if word == "for":
            m = re.fullmatch(r"for\s+([A-Za-z_]\w*)(?:\s+in\s*(.*))?", segs[0], re.S)
            if not m:
                raise syntax_error("for")
            if len(segs) < 3 or segs[1] != "do":
                raise syntax_error(segs[1] if len(segs) > 1 else "newline")
            words = self.words_of(m.group(2)) if m.group(2) is not None else self.env.get("@", "").split()
            body = segs[2:-1]
            for item in words:
                self.env[m.group(1)] = item
                if self.loop_body(body) == "break":
                    break
        elif word in ("while", "until"):
            cond, k = [segs[0][len(word):].strip()], 1
            cond = [c for c in cond if c]
            while k < len(segs) and segs[k] != "do":
                cond.append(segs[k])
                k += 1
            if k >= len(segs) - 1:
                raise syntax_error(segs[-1].split()[0])
            body, count = segs[k + 1:-1], 0
            while self.run_cond(cond) == (word == "while"):
                count += 1
                if count > MAX_LOOP:
                    self.show_error(f"bash: loop stopped after {MAX_LOOP} rounds (this practice shell cannot wait for Ctrl+C)",
                                    "a while loop needs something that eventually becomes false")
                    break
                if self.loop_body(body) == "break":
                    break
        else:  # if
            branches, else_body, cur, mode, depth = [], None, [segs[0][2:].strip()], "cond", 0
            cond, body = [c for c in cur if c], []
            for seg in segs[1:-1]:
                w = first_word(seg)
                if w in OPEN:
                    depth += 1
                elif w in CLOSE:
                    depth -= 1
                if depth == 0 and w == "then" and mode == "cond":
                    mode = "body"
                elif depth == 0 and w == "elif" and mode == "body":
                    branches.append((cond, body))
                    cond, body, mode = [seg[4:].strip()] if seg[4:].strip() else [], [], "cond"
                elif depth == 0 and w == "else" and mode == "body":
                    branches.append((cond, body))
                    cond, body, mode = None, [], "else"
                elif mode == "cond":
                    cond.append(seg)
                else:
                    body.append(seg)
            if mode == "cond":
                raise syntax_error("fi")
            if mode == "else":
                else_body = body
            else:
                branches.append((cond, body))
            for cond, body in branches:
                if self.run_cond(cond):
                    self.exec_segments(body)
                    return
            if else_body is not None:
                self.exec_segments(else_body)
                return
            self.status = 0

    def words_of(self, text):
        """The words after 'for x in': variables, $(...), braces and globs are expanded like bash."""
        from .parser import tokenize
        tokens = tokenize(text, self.env, self.status, self)
        return self.expand([(t[1], t[2]) for t in tokens if t[0] == "word"])

    # ---------------------------------------------------------- builtins
    def cmd_break(self, args, stdin):
        raise LoopControl("break", int(args[0]) if args and args[0].isdigit() else 1)

    def cmd_continue(self, args, stdin):
        raise LoopControl("continue", int(args[0]) if args and args[0].isdigit() else 1)

    def cmd_test(self, args, stdin, name="test"):
        def number(x):
            try:
                return int(x)
            except ValueError:
                raise ShellError(f"bash: {name}: {x}: integer expression expected", 2)

        def unary(op, x):
            p = self.path(x)
            return {"-f": lambda: self.fs.isfile(p), "-d": lambda: self.fs.isdir(p), "-e": lambda: self.fs.exists(p),
                    "-s": lambda: self.fs.isfile(p) and bool(self.fs.d.get(p)),
                    "-r": lambda: self.fs.exists(p) and self.access(p, 4),
                    "-w": lambda: self.fs.exists(p) and self.access(p, 2),
                    "-x": lambda: self.fs.exists(p) and self.access(p, 1),
                    "-L": lambda: self.path(x, False) in self.fs.links, "-h": lambda: self.path(x, False) in self.fs.links, "-z": lambda: x == "", "-n": lambda: x != ""}[op]()

        def evaluate(a):
            if not a:
                return False
            for idx, tok in enumerate(a):
                if tok == "-o" and 0 < idx < len(a) - 1:
                    return evaluate(a[:idx]) or evaluate(a[idx + 1:])
            for idx, tok in enumerate(a):
                if tok == "-a" and 0 < idx < len(a) - 1:
                    return evaluate(a[:idx]) and evaluate(a[idx + 1:])
            if a[0] == "!":
                return not evaluate(a[1:])
            if len(a) == 1:
                return a[0] != ""
            if len(a) == 2 and a[0] in ("-f", "-d", "-e", "-s", "-r", "-w", "-x", "-L", "-h", "-z", "-n"):
                return unary(a[0], a[1])
            if len(a) == 3:
                x, op, y = a
                if op in ("=", "=="):
                    return fnmatch.fnmatchcase(x, y) if name == "[[" else x == y
                if op == "!=":
                    return x != y
                if op == "<":
                    return x < y
                if op == ">":
                    return x > y
                if op in ("-eq", "-ne", "-lt", "-gt", "-le", "-ge"):
                    p, q = number(x), number(y)
                    return {"-eq": p == q, "-ne": p != q, "-lt": p < q, "-gt": p > q, "-le": p <= q, "-ge": p >= q}[op]
            if len(a) > 3 or (a and a[0].startswith("-")):
                raise ShellError(f"bash: {name}: too many arguments" if len(a) > 3 else f"bash: {name}: {a[0]}: unary operator expected", 2,
                                 tip="put variables in quotes: [ -f \"$FILE\" ]")
            raise ShellError(f"bash: {name}: {a[1] if len(a) > 1 else a[0]}: binary operator expected", 2,
                             tip="put variables in quotes: [ \"$A\" = \"$B\" ]")
        closer = {"[": "]", "[[": "]]"}.get(name)
        if closer:
            if not args or args[-1] != closer:
                raise ShellError(f"bash: {name}: missing `{closer}'", 2, tip=f"close it with a space before: {name} -f file {closer}")
            args = args[:-1]
        self._status = 0 if evaluate(list(args)) else 1
        return ""

    def cmd_read(self, args, stdin):
        prompt, names, i = "", [], 0
        while i < len(args):
            if args[i] == "-p" and i + 1 < len(args):
                prompt, i = args[i + 1], i + 2
            elif args[i] == "-r":
                i += 1
            else:
                names.append(args[i])
                i += 1
        try:
            text = stdin if stdin is not None else input(prompt)
        except EOFError:
            self._status = 1
            return ""
        names = names or ["REPLY"]
        parts = text.split(None, len(names) - 1) if len(names) > 1 else [text.strip()]
        for k, n in enumerate(names):
            self.env[n] = parts[k] if k < len(parts) else ""
        return ""

    def cmd_let(self, args, stdin):
        from .arith import evaluate
        result = 0
        for a in args:
            m = re.fullmatch(r"([A-Za-z_]\w*)(\+=|-=|\*=|/=|=)(.*)", a)
            if m:
                value = evaluate(m.group(3), self.env)
                if m.group(2) != "=":
                    value = evaluate(f"{self.env.get(m.group(1), '0') or 0}{m.group(2)[0]}({value})", self.env)
                self.env[m.group(1)] = str(value)
                result = value
            else:
                result = evaluate(a, self.env)
        self._status = 0 if result else 1
        return ""


for _name in ("[", "[["):
    setattr(CompoundCommands, "cmd_" + _name, lambda self, args, stdin, _n=_name: self.cmd_test(args, stdin, _n))
