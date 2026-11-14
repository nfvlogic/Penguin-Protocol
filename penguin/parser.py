"""Turn a command line into commands, like bash does.

Supports: 'single' and "double" quotes, backslash escapes, $VAR ${VAR} $?,
~ at the start of a word, globs (* ? [..]) only when NOT quoted, # comments,
and the operators  |  >  >>  <  2>  2>>  ;  &&  ||
"""
import random
import re

from .arith import evaluate
from .core import HOME, ShellError

OPERATORS = ["2>&1", "1>&2", "&>>", "2>>", "&>", ">&2", "&&", "||", ">>", "<<", "2>", "|", ">", "<", ";", "&"]
REDIRECTS = {">", ">>", "<", "<<", "2>", "2>>", "&>", "&>>"}
NO_TARGET = {"2>&1", "1>&2", ">&2"}   # redirect one stream into the other


def brace_expand(word):
    """a{b,c}d -> abd acd ;  f{1..3} -> f1 f2 f3 (nested braces work too)."""
    depth, start = 0, None
    for k, ch in enumerate(word):
        if ch == "{":
            if depth == 0:
                start = k
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0:
                inner = word[start + 1:k]
                parts, d, cur = [], 0, ""
                for x in inner:
                    if x == "{":
                        d += 1
                    elif x == "}":
                        d -= 1
                    if x == "," and d == 0:
                        parts.append(cur)
                        cur = ""
                    else:
                        cur += x
                parts.append(cur)
                seq = re.fullmatch(r"(-?\d+)\.\.(-?\d+)|([a-zA-Z])\.\.([a-zA-Z])", inner)
                if seq and len(parts) == 1:
                    if seq.group(1) is not None:
                        a, b = int(seq.group(1)), int(seq.group(2))
                        width = max(len(seq.group(1)), len(seq.group(2))) if seq.group(1).lstrip("-").startswith("0") or seq.group(2).lstrip("-").startswith("0") else 0
                        step = 1 if b >= a else -1
                        parts = [str(v).zfill(width) for v in range(a, b + step, step)]
                    else:
                        a, b = ord(seq.group(3)), ord(seq.group(4))
                        step = 1 if b >= a else -1
                        parts = [chr(v) for v in range(a, b + step, step)]
                elif len(parts) == 1:
                    continue
                out = []
                for part in parts:
                    out += brace_expand(word[:start] + part + word[k + 1:])
                return out
    return [word]


def matching_paren(line, i):
    """Index of the ')' that closes the '(' just before line[i] (quotes and nesting respected)."""
    depth, quote = 1, None
    while i < len(line):
        ch = line[i]
        if quote:
            if ch == quote:
                quote = None
            elif ch == "\\" and quote == '"':
                i += 1
        elif ch in "'\"":
            quote = ch
        elif ch == "\\":
            i += 1
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ShellError("bash: unexpected EOF while looking for matching `)'", 2, tip="every $( needs a closing )")


def tokenize(line, env, status, shell=None):
    """Return a list of ('op', text) and ('word', text, can_glob) tokens.

    `shell` runs $(...) command substitutions; without it they are only syntax-checked."""
    tokens, i, n = [], 0, len(line)
    buf, has_word, glob, plain_word = [], False, False, True

    def flush():
        nonlocal buf, has_word, glob, plain_word
        if has_word:
            word = "".join(buf)
            if plain_word and "{" in word and ("," in word or ".." in word):
                for w in brace_expand(word):
                    tokens.append(("word", w, glob or any(c in w for c in "*?[")))
            else:
                tokens.append(("word", word, glob))
        buf, has_word, glob, plain_word = [], False, False, True

    def variable(j):
        """Expand $NAME ${NAME} $? $$ $# $1 $(cmd) $((expr)) `cmd` starting at line[j]. -> (text, size)."""
        rest = line[j:]
        if rest.startswith("$(("):
            end = matching_paren(line, j + 2)
            if end - 1 > j + 2 and line[end - 1] == ")":
                expr = line[j + 3:end - 1]
                return (str(evaluate(expr, env)) if shell else "0"), end + 1 - j
        if rest.startswith("$("):
            end = matching_paren(line, j + 2)
            return (shell.capture(line[j + 2:end]) if shell else "x"), end + 1 - j
        if rest.startswith("`"):
            end = line.find("`", j + 1)
            if end < 0:
                raise ShellError("bash: unexpected EOF while looking for matching ``'", 2)
            return (shell.capture(line[j + 1:end]) if shell else "x"), end + 1 - j
        m = re.match(r"\$(\?|\$|#|@|\*|\{([^}]*)\}|(\w+))", rest)
        if not m:
            return "$", 1
        g = m.group(1)
        if g == "?":
            return str(status), 2
        if g == "$":
            return "1021", 2
        if g in ("#", "@", "*"):
            return (env.get(g, "0" if g == "#" else "")), 2
        name = m.group(2) if m.group(2) is not None else m.group(3)
        return lookup(name), m.end()

    def lookup(name):
        if name == "RANDOM":
            return str(random.randint(0, 32767))
        if name.startswith("#") and len(name) > 1:
            return str(len(env.get(name[1:], "")))
        m2 = re.fullmatch(r"(\w+)(:?[-=+?])(.*)", name)
        if m2:
            val, op, word = env.get(m2.group(1), ""), m2.group(2), m2.group(3)
            if op in (":-", "-"):
                return val if (val or (op == "-" and m2.group(1) in env)) else word
            if op in (":=", "="):
                if not val:
                    env[m2.group(1)] = word
                    return word
                return val
            if op in (":+", "+"):
                return word if val else ""
        return env.get(name, "")

    def expand_text(text):
        """Variables inside $((...)) are plain names; just return the text."""
        return text

    def unquoted(text):
        """An unquoted expansion is split into words (empty ones vanish), like bash."""
        nonlocal has_word, glob
        if text == "":
            return
        if any(c in text for c in "*?["):
            glob = True
        parts = text.split()
        if not parts:
            flush()
            return
        if text[0] in " \t\n":
            flush()
        for k, part in enumerate(parts):
            buf.append(part)
            has_word = True
            if k < len(parts) - 1:
                flush()
        if text[-1] in " \t\n":
            flush()

    while i < n:
        ch = line[i]
        if ch in " \t":
            flush()
            i += 1
        elif ch == "#" and not has_word:
            break
        elif ch == "'":
            end = line.find("'", i + 1)
            if end < 0:
                raise ShellError("bash: unexpected EOF while looking for matching `''", 2,
                                 tip="every ' needs a closing ', e.g. echo 'hi there'")
            buf.append(line[i + 1:end])
            has_word, i = True, end + 1
            plain_word = False
        elif ch == '"':
            i += 1
            has_word = True
            plain_word = False
            while True:
                if i >= n:
                    raise ShellError("bash: unexpected EOF while looking for matching `\"'", 2,
                                     tip='every " needs a closing ", e.g. echo "hi there"')
                if line[i] == '"':
                    i += 1
                    break
                if line[i] == "\\" and i + 1 < n and line[i + 1] in '"\\$`':
                    buf.append(line[i + 1])
                    i += 2
                elif line[i] in "$`":
                    text, size = variable(i)
                    buf.append(text)
                    i += size
                else:
                    buf.append(line[i])
                    i += 1
        elif ch == "\\":
            if i + 1 < n:
                buf.append(line[i + 1])
            has_word, i = True, i + 2
            plain_word = False
        elif ch in "$`":
            text, size = variable(i)
            if text == "$" and size == 1:
                buf.append("$")
                has_word = True
            else:
                unquoted(text)
            i += size
        elif ch == "~" and not has_word and (i + 1 == n or line[i + 1] in "/ \t;|&<>"):
            buf.append(HOME)
            has_word, i = True, i + 1
        else:
            op = next((o for o in OPERATORS if line.startswith(o, i)), None)
            if op and op[0] in "12" and has_word:
                op = None  # the digit is part of a word, e.g. file2>x
            if op:
                flush()
                tokens.append(("op", op))
                i += len(op)
            else:
                if ch in "*?[":
                    glob = True
                buf.append(ch)
                has_word, i = True, i + 1
    flush()
    return tokens


def parse(tokens):
    """Tokens -> [(connector, pipeline)], connector is None, ';', '&&' or '||'.

    pipeline = [ {"argv": [(text, can_glob)], "redirs": [(op, target)]} ]
    """
    if not tokens:
        return []
    lists, pipeline, cmd, connector = [], [], {"argv": [], "redirs": []}, None
    i = 0

    def unexpected(tok):
        raise ShellError(f"bash: syntax error near unexpected token `{tok}'", 2)

    while i < len(tokens):
        tok = tokens[i]
        if tok[0] == "word":
            cmd["argv"].append((tok[1], tok[2]))
        elif tok[1] in NO_TARGET:
            cmd["redirs"].append((tok[1], None))
        elif tok[1] in REDIRECTS:
            if i + 1 >= len(tokens) or tokens[i + 1][0] != "word":
                unexpected(tokens[i + 1][1] if i + 1 < len(tokens) else "newline")
            cmd["redirs"].append((tok[1], tokens[i + 1][1]))
            i += 1
        elif tok[1] == "&":
            raise ShellError("bash: background jobs (&) are not supported in this practice shell", 2,
                             tip="did you mean && (run the next command only if this one worked)?")
        elif tok[1] == "|":
            if not cmd["argv"]:
                unexpected("|")
            pipeline.append(cmd)
            cmd = {"argv": [], "redirs": []}
            if i + 1 >= len(tokens):
                raise ShellError("bash: syntax error: unexpected end of file", 2,
                                 tip="a pipe needs a command on both sides, e.g. ls | sort")
        else:  # ; && ||
            if not cmd["argv"]:
                unexpected(tok[1])
            pipeline.append(cmd)
            lists.append((connector, pipeline))
            pipeline, cmd, connector = [], {"argv": [], "redirs": []}, tok[1]
            if i + 1 >= len(tokens) and tok[1] != ";":
                raise ShellError("bash: syntax error: unexpected end of file", 2,
                                 tip=f"{tok[1]} needs a command after it, e.g. mkdir x {tok[1]} cd x")
        i += 1
    if cmd["argv"] or cmd["redirs"]:
        if not cmd["argv"]:
            raise ShellError("bash: syntax error near unexpected token `newline'", 2)
        pipeline.append(cmd)
    if pipeline:
        lists.append((connector, pipeline))
    return lists


def scan(line):
    """Yield (index, char, quote, depth) for every character: quote is the open quote (or None),
    depth counts open $( ) so operators inside a command substitution are left alone."""
    quote, depth, i, n = None, 0, 0, len(line)
    while i < n:
        ch = line[i]
        if ch == ")" and depth and quote is None:
            depth -= 1
        yield i, ch, quote, depth
        if quote == "'":
            if ch == "'":
                quote = None
        elif ch == "\\" and i + 1 < n:
            i += 1
            yield i, line[i], "\\", depth      # an escaped character is never an operator
        elif quote == '"':
            if ch == '"':
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == "`":
            pass
        elif ch == "$" and line.startswith("$(", i):
            depth += 1
            i += 1
            yield i, line[i], quote, depth
        i += 1


def split_top(line, separators):
    """Split at unquoted top-level separators (a list of strings like ';' '&&'). Returns
    [(separator_before, text)]. Comments (# at the start of a word) end the line."""
    chunks, buf, sep, i, n = [], [], None, 0, len(line)
    skip_to, comment = -1, False
    for i, ch, quote, depth in scan(line):
        if i <= skip_to:
            continue
        if comment:                       # a # comment runs to the end of its line
            if ch != "\n":
                continue
            comment = False
        if quote is None and depth == 0:
            if ch == "#" and (not buf or buf[-1] in " \t\n"):
                comment = True
                continue
            op = next((o for o in separators if line.startswith(o, i)), None)
            if op:
                chunks.append((sep, "".join(buf)))
                sep, buf, skip_to = op, [], i + len(op) - 1
                continue
        buf.append(ch)
    chunks.append((sep, "".join(buf)))
    return chunks


def split_lists(line):
    """Split a line at unquoted ; && || into [(connector, text)].

    Bash expands variables ($?, $TOKEN ...) right before each command runs, so each
    part is tokenized only when its turn comes.
    """
    return split_top(line, [";", "&&", "||"])
