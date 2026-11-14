"""A small awk: enough for the one-liners people really use ('{print $1}', -F, conditions,
sums with END, counting with arrays). Not a full awk."""
import re

from .core import ShellError


class AwkExit(Exception):
    pass


class AwkNext(Exception):
    pass


class Lit(str):
    """A string typed in the program (compared as text, never as a number)."""


def to_num(v):
    if isinstance(v, (int, float)):
        return v
    m = re.match(r"\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?", v)
    if not m:
        return 0
    f = float(m.group(0))
    return int(f) if f == int(f) else f


def to_str(v):
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else f"{v:.6g}"
    return str(v)


def looks_numeric(v):
    if isinstance(v, (int, float)):
        return True
    return not isinstance(v, Lit) and bool(re.fullmatch(r"\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?\s*", v))


def truthy(v):
    if isinstance(v, str):
        return v != ""
    return v != 0


TOKEN = re.compile(r'''\s*(?:(?P<num>\d+\.?\d*|\.\d+)|(?P<str>"(?:[^"\\]|\\.)*")|(?P<name>[A-Za-z_]\w*)
    |(?P<op>\+\+|--|\+=|-=|\*=|/=|==|!=|<=|>=|&&|\|\||!~|[-+*/%<>=!~$(){}\[\];,?:]))''', re.X)


def tokenize(src):
    toks, i = [], 0
    while i < len(src):
        if src[i] in " \t":
            i += 1
            continue
        if src[i] == "\n":
            toks.append(("op", ";"))
            i += 1
            continue
        if src[i] == "#":
            while i < len(src) and src[i] != "\n":
                i += 1
            continue
        prev = toks[-1] if toks else None
        if src[i] == "/" and (prev is None or prev[0] == "op" and prev[1] in "(~{;,&|!=" or prev[1] in ("!~", "&&", "||", "==")):
            j = i + 1
            while j < len(src) and src[j] != "/":
                j += 2 if src[j] == "\\" else 1
            if j >= len(src):
                raise ShellError("awk: syntax error: unterminated regular expression", 2)
            toks.append(("re", src[i + 1:j]))
            i = j + 1
            continue
        m = TOKEN.match(src, i)
        if not m or m.end() == i:
            raise ShellError(f"awk: syntax error at source line 1\n context is\n\t>>> {src[i:i + 12]} <<<", 2)
        kind = m.lastgroup
        text = m.group(kind)
        if kind == "str":
            text = Lit(bytes(text[1:-1], "utf-8").decode("unicode_escape"))
        toks.append((kind, text))
        i = m.end()
    return toks


class Parser:
    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self, k=0):
        return self.t[self.i + k] if self.i + k < len(self.t) else (None, None)

    def eat(self, val=None):
        tok = self.peek()
        if tok[0] is None or (val is not None and tok[1] != val):
            raise ShellError(f"awk: syntax error: expected '{val}'", 2)
        self.i += 1
        return tok

    def is_op(self, val):
        return self.peek()[0] == "op" and self.peek()[1] == val

    def skip_semis(self):
        while self.is_op(";"):
            self.i += 1

    def program(self):
        items = []
        self.skip_semis()
        while self.peek()[0] is not None:
            if self.peek() == ("name", "BEGIN"):
                self.i += 1
                items.append(("BEGIN", None, self.block()))
            elif self.peek() == ("name", "END"):
                self.i += 1
                items.append(("END", None, self.block()))
            else:
                pat = None if self.is_op("{") else self.expr()
                body = self.block() if self.is_op("{") else [("print", [])]
                items.append(("RULE", pat, body))
            self.skip_semis()
        return items

    def block(self):
        self.eat("{")
        stmts = []
        self.skip_semis()
        while not self.is_op("}"):
            stmts.append(self.stmt())
            self.skip_semis()
        self.eat("}")
        return stmts

    def stmt(self):
        kind, val = self.peek()
        if kind == "op" and val == "{":
            return ("block", self.block())
        if kind == "name" and val in ("print", "printf"):
            self.i += 1
            args = []
            if not (self.is_op(";") or self.is_op("}") or self.peek()[0] is None):
                args.append(self.expr())
                while self.is_op(","):
                    self.i += 1
                    args.append(self.expr())
            return (val, args)
        if kind == "name" and val == "next":
            self.i += 1
            return ("next",)
        if kind == "name" and val == "exit":
            self.i += 1
            return ("exit",)
        if kind == "name" and val == "delete":
            self.i += 1
            name = self.eat()[1]
            key = None
            if self.is_op("["):
                self.i += 1
                key = self.expr()
                self.eat("]")
            return ("delete", name, key)
        if kind == "name" and val == "if":
            self.i += 1
            self.eat("(")
            cond = self.expr()
            self.eat(")")
            self.skip_semis()
            then = self.stmt()
            self.skip_semis()
            other = None
            if self.peek() == ("name", "else"):
                self.i += 1
                self.skip_semis()
                other = self.stmt()
            return ("if", cond, then, other)
        if kind == "name" and val == "for":
            self.i += 1
            self.eat("(")
            var = self.eat()[1]
            if self.peek() != ("name", "in"):
                raise ShellError("awk: only 'for (key in array)' loops are supported here", 2)
            self.i += 1
            arr = self.eat()[1]
            self.eat(")")
            self.skip_semis()
            return ("forin", var, arr, self.stmt())
        return ("expr", self.expr())

    # expressions, lowest precedence first
    def expr(self):
        return self.assign()

    def assign(self):
        left = self.ternary()
        if self.peek()[0] == "op" and self.peek()[1] in ("=", "+=", "-=", "*=", "/=") and left[0] in ("var", "field", "index"):
            op = self.eat()[1]
            return ("assign", op, left, self.assign())
        return left

    def ternary(self):
        cond = self.or_()
        if self.is_op("?"):
            self.i += 1
            a = self.assign()
            self.eat(":")
            return ("ternary", cond, a, self.assign())
        return cond

    def or_(self):
        left = self.and_()
        while self.is_op("||"):
            self.i += 1
            left = ("or", left, self.and_())
        return left

    def and_(self):
        left = self.match()
        while self.is_op("&&"):
            self.i += 1
            left = ("and", left, self.match())
        return left

    def match(self):
        left = self.compare()
        while self.peek()[0] == "op" and self.peek()[1] in ("~", "!~"):
            op = self.eat()[1]
            left = ("match", op, left, self.compare())
        return left

    def compare(self):
        left = self.concat()
        while self.peek()[0] == "op" and self.peek()[1] in ("==", "!=", "<", ">", "<=", ">="):
            op = self.eat()[1]
            left = ("cmp", op, left, self.concat())
        if self.peek() == ("name", "in"):
            self.i += 1
            left = ("in", left, self.eat()[1])
        return left

    def concat(self):
        left = self.add()
        while self.starts_value():
            left = ("concat", left, self.add())
        return left

    def starts_value(self):
        kind, val = self.peek()
        return kind in ("num", "str", "name", "re") and val not in ("in",) or (kind == "op" and val in ("$", "(", "!"))

    def add(self):
        left = self.mul()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.eat()[1]
            left = ("bin", op, left, self.mul())
        return left

    def mul(self):
        left = self.unary()
        while self.peek()[0] == "op" and self.peek()[1] in ("*", "/", "%"):
            op = self.eat()[1]
            left = ("bin", op, left, self.unary())
        return left

    def unary(self):
        if self.is_op("!"):
            self.i += 1
            return ("not", self.unary())
        if self.is_op("-"):
            self.i += 1
            return ("neg", self.unary())
        if self.is_op("+"):
            self.i += 1
            return self.unary()
        return self.postfix()

    def postfix(self):
        node = self.primary()
        if node[0] in ("var", "field", "index") and self.peek()[0] == "op" and self.peek()[1] in ("++", "--"):
            return ("post", self.eat()[1], node)
        return node

    def primary(self):
        kind, val = self.peek()
        if kind == "num":
            self.i += 1
            f = float(val)
            return ("const", int(f) if f == int(f) else f)
        if kind == "str":
            self.i += 1
            return ("const", val)
        if kind == "re":
            self.i += 1
            return ("regex", val)
        if kind == "op" and val == "$":
            self.i += 1
            return ("field", self.primary())
        if kind == "op" and val == "(":
            self.i += 1
            node = self.expr()
            self.eat(")")
            return node
        if kind == "name":
            self.i += 1
            if self.is_op("["):
                self.i += 1
                key = self.expr()
                self.eat("]")
                return ("index", val, key)
            if self.is_op("(") and val in ("length", "substr", "toupper", "tolower", "int", "sprintf", "sub", "gsub",
                                           "split", "index", "match", "sqrt"):
                self.i += 1
                args = []
                if not self.is_op(")"):
                    args.append(self.expr())
                    while self.is_op(","):
                        self.i += 1
                        args.append(self.expr())
                self.eat(")")
                return ("call", val, args)
            if val == "length":
                return ("call", "length", [])
            return ("var", val)
        raise ShellError("awk: syntax error: unexpected end of program" if kind is None
                         else f"awk: syntax error near '{val}'", 2)


class Interp:
    def __init__(self, fs_sep, assigns):
        self.vars = {"FS": fs_sep, "OFS": " ", "NR": 0, "NF": 0}
        self.vars.update(assigns)
        self.arrays, self.out, self.fields = {}, [], [""]

    def set_record(self, line):
        fs = self.vars["FS"]
        if fs == " ":
            parts = line.split()
        elif len(fs) == 1:
            parts = line.split(fs)
        else:
            parts = re.split(fs, line)
        self.fields = [line] + parts
        self.vars["NF"] = len(parts)

    def field(self, n):
        n = int(to_num(n))
        return self.fields[n] if 0 <= n < len(self.fields) else ""

    def regex(self, node):
        return re.compile(node[1] if node[0] == "regex" else to_str(self.ev(node)))

    def ev(self, n):
        k = n[0]
        if k == "const":
            return n[1]
        if k == "var":
            return self.vars.get(n[1], "")
        if k == "field":
            return self.field(self.ev(n[1]))
        if k == "index":
            return self.arrays.setdefault(n[1], {}).get(to_str(self.ev(n[2])), "")
        if k == "regex":
            return 1 if re.search(n[1], self.fields[0]) else 0
        if k == "in":
            return 1 if to_str(self.ev(n[1])) in self.arrays.get(n[2], {}) else 0
        if k == "call":
            if n[1] in ("sub", "gsub"):
                return self.substitute(n[1], n[2])
            if n[1] == "split":
                text = to_str(self.ev(n[2][0]))
                sep = to_str(self.ev(n[2][2])) if len(n[2]) > 2 else self.vars["FS"]
                parts = text.split() if sep == " " else (text.split(sep) if len(sep) == 1 else re.split(sep, text))
                self.arrays[n[2][1][1]] = {str(k + 1): v for k, v in enumerate(parts)}
                return len(parts)
            return self.call(n[1], [self.ev(a) for a in n[2]])
        if k == "neg":
            return -to_num(self.ev(n[1]))
        if k == "not":
            return 0 if truthy(self.ev(n[1])) else 1
        if k == "and":
            return 1 if truthy(self.ev(n[1])) and truthy(self.ev(n[2])) else 0
        if k == "or":
            return 1 if truthy(self.ev(n[1])) or truthy(self.ev(n[2])) else 0
        if k == "ternary":
            return self.ev(n[2]) if truthy(self.ev(n[1])) else self.ev(n[3])
        if k == "concat":
            return to_str(self.ev(n[1])) + to_str(self.ev(n[2]))
        if k == "match":
            hit = bool(self.regex(n[3]).search(to_str(self.ev(n[2]))))
            return 1 if hit == (n[1] == "~") else 0
        if k == "cmp":
            a, b = self.ev(n[2]), self.ev(n[3])
            if looks_numeric(a) and looks_numeric(b):
                a, b = to_num(a), to_num(b)
            else:
                a, b = to_str(a), to_str(b)
            return 1 if {"==": a == b, "!=": a != b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[n[1]] else 0
        if k == "bin":
            a, b = to_num(self.ev(n[2])), to_num(self.ev(n[3]))
            if n[1] in "/%" and b == 0:
                raise ShellError("awk: division by zero", 2)
            r = {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b,
                 "/": lambda: a / b, "%": lambda: a % b}[n[1]]()
            return int(r) if isinstance(r, float) and r == int(r) and n[1] != "/" else r
        if k == "assign":
            val = self.ev(n[3])
            if n[1] != "=":
                cur, val = to_num(self.ev(n[2])), to_num(val)
                val = {"+=": cur + val, "-=": cur - val, "*=": cur * val, "/=": cur / val if val else 0}[n[1]]
            self.store(n[2], val)
            return val
        if k == "post":
            cur = to_num(self.ev(n[2]))
            self.store(n[2], cur + (1 if n[1] == "++" else -1))
            return cur
        raise ShellError("awk: unsupported expression", 2)

    def store(self, target, val):
        if target[0] == "var":
            self.vars[target[1]] = val
        elif target[0] == "index":
            self.arrays.setdefault(target[1], {})[to_str(self.ev(target[2]))] = val
        else:
            self.set_field(int(to_num(self.ev(target[1]))), to_str(val))

    def set_field(self, n, text):
        if n == 0:
            self.set_record(text)
            return
        while len(self.fields) <= n:
            self.fields.append("")
        self.fields[n] = text
        self.vars["NF"] = len(self.fields) - 1
        self.fields[0] = self.vars["OFS"].join(self.fields[1:])

    def substitute(self, name, args):
        pattern = args[0]
        rx = re.compile(pattern[1] if pattern[0] == "regex" else to_str(self.ev(pattern)))
        repl = to_str(self.ev(args[1]))
        target = args[2] if len(args) > 2 else ("field", ("const", 0))

        def one(m):
            return re.sub(r"\\&|&", lambda x: "&" if x.group(0) == "\\&" else m.group(0), repl)
        new, count = rx.subn(one, to_str(self.ev(target)), 0 if name == "gsub" else 1)
        if count:
            self.store(target, new)
        return count

    def call(self, name, a):
        if name == "length":
            return len(to_str(a[0]) if a else self.fields[0])
        if name == "toupper":
            return to_str(a[0]).upper()
        if name == "tolower":
            return to_str(a[0]).lower()
        if name == "int":
            return int(to_num(a[0]))
        if name == "substr":
            s, start = to_str(a[0]), int(to_num(a[1]))
            start = max(start, 1)
            return s[start - 1:start - 1 + int(to_num(a[2]))] if len(a) > 2 else s[start - 1:]
        if name == "sprintf":
            return self.fmt(a)
        if name == "index":
            return to_str(a[0]).find(to_str(a[1])) + 1
        if name == "sqrt":
            return to_num(a[0]) ** 0.5
        if name == "match":
            m = re.search(to_str(a[1]), to_str(a[0]))
            self.vars["RSTART"], self.vars["RLENGTH"] = (m.start() + 1, m.end() - m.start()) if m else (0, -1)
            return self.vars["RSTART"]
        return ""

    def fmt(self, a):
        pattern, vals = to_str(a[0]), a[1:]
        out, k = [], 0

        def one(m):
            nonlocal k
            spec = m.group(0)
            if spec == "%%":
                return "%"
            v = vals[k] if k < len(vals) else ""
            k += 1
            if spec[-1] in "di":
                return (spec[:-1] + "d") % int(to_num(v))
            if spec[-1] in "feg":
                return spec % float(to_num(v))
            return spec % to_str(v)
        return re.sub(r"%[-+ 0#]*\d*(?:\.\d+)?[dsifeg%]", one, pattern.replace("\\n", "\n"))

    def run(self, stmts):
        for st in stmts:
            k = st[0]
            if k == "block":
                self.run(st[1])
            elif k == "print":
                parts = [to_str(self.ev(a)) for a in st[1]] or [self.fields[0]]
                self.out.append(self.vars["OFS"].join(parts) + "\n")
            elif k == "printf":
                self.out.append(self.fmt([self.ev(a) for a in st[1]]))
            elif k == "expr":
                self.ev(st[1])
            elif k == "next":
                raise AwkNext()
            elif k == "exit":
                raise AwkExit()
            elif k == "delete":
                if st[2] is None:
                    self.arrays[st[1]] = {}
                else:
                    self.arrays.get(st[1], {}).pop(to_str(self.ev(st[2])), None)
            elif k == "if":
                if truthy(self.ev(st[1])):
                    self.run([st[2]])
                elif st[3]:
                    self.run([st[3]])
            elif k == "forin":
                for key in sorted(self.arrays.get(st[2], {}), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else 0, x)):
                    self.vars[st[1]] = key
                    self.run([st[3]])


def run_awk(program, texts, fs=" ", assigns=None):
    """Run an awk program over the given texts (one per file) and return the output text."""
    items = Parser(tokenize(program)).program()
    it = Interp(fs, assigns or {})
    done = False
    try:
        for typ, _, body in items:
            if typ == "BEGIN":
                it.run(body)
    except AwkExit:
        done = True
    for text in texts:
        if done:
            break
        for line in (text[:-1] if text.endswith("\n") else text).split("\n") if text else []:
            it.vars["NR"] += 1
            it.set_record(line)
            try:
                for typ, pat, body in items:
                    if typ == "RULE" and (pat is None or truthy(it.ev(pat))):
                        it.run(body)
            except AwkNext:
                continue
            except AwkExit:
                done = True
                break
    try:
        for typ, _, body in items:
            if typ == "END":
                it.run(body)
    except AwkExit:
        pass
    text = "".join(it.out)
    return text[:-1] if text.endswith("\n") else text   # the shell adds the final newline
