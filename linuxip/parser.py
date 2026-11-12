"""Turn a command line into commands, like bash does.

Supports: 'single' and "double" quotes, backslash escapes, $VAR ${VAR} $?,
~ at the start of a word, globs (* ? [..]) only when NOT quoted, # comments,
and the operators  |  >  >>  <  2>  2>>  ;  &&  ||
"""
import re

from .core import HOME, ShellError

OPERATORS = ["2>>", "&&", "||", ">>", "2>", "|", ">", "<", ";", "&"]
REDIRECTS = {">", ">>", "<", "2>", "2>>"}


def tokenize(line, env, status):
    """Return a list of ('op', text) and ('word', text, can_glob) tokens."""
    tokens, i, n = [], 0, len(line)
    buf, has_word, glob = [], False, False

    def flush():
        nonlocal buf, has_word, glob
        if has_word:
            tokens.append(("word", "".join(buf), glob))
        buf, has_word, glob = [], False, False

    def variable(j):
        """Expand $NAME / ${NAME} / $? starting at line[j] == '$'."""
        m = re.match(r"\$(\?|\{(\w+)\}|(\w+))", line[j:])
        if not m:
            return "$", 1
        if m.group(1) == "?":
            return str(status), 2
        return env.get(m.group(2) or m.group(3), ""), m.end()

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
        elif ch == '"':
            i += 1
            has_word = True
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
                elif line[i] == "$":
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
        elif ch == "$":
            text, size = variable(i)
            buf.append(text)
            has_word, i = True, i + size
        elif ch == "~" and not has_word and (i + 1 == n or line[i + 1] in "/ \t;|&<>"):
            buf.append(HOME)
            has_word, i = True, i + 1
        else:
            op = next((o for o in OPERATORS if line.startswith(o, i)), None)
            if op and op.startswith("2") and has_word:
                op = None  # the 2 is part of a word, e.g. file2>x
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


def split_lists(line):
    """Split a line at unquoted ; && || into [(connector, text)].

    Bash expands variables ($?, $TOKEN ...) right before each command runs, so each
    part is tokenized only when its turn comes.
    """
    chunks, buf, connector, quote, i, n = [], [], None, None, 0, len(line)
    while i < n:
        ch = line[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            elif ch == "\\" and quote == '"' and i + 1 < n:
                buf.append(line[i + 1])
                i += 1
        elif ch in "'\"":
            quote = ch
            buf.append(ch)
        elif ch == "\\":
            buf.append(line[i:i + 2])
            i += 1
        elif ch == "#" and (not buf or buf[-1] in " \t"):
            break
        elif ch == ";" or line.startswith("&&", i) or line.startswith("||", i):
            op = ";" if ch == ";" else line[i:i + 2]
            chunks.append((connector, "".join(buf)))
            connector, buf = op, []
            i += len(op)
            continue
        else:
            buf.append(ch)
        i += 1
    chunks.append((connector, "".join(buf)))
    return chunks
