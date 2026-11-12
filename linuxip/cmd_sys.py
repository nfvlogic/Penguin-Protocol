"""System and text-processing commands: sed awk tr tee diff xargs | ps pgrep kill ss | systemctl journalctl ssh |
tar | stat file uptime free sleep basename dirname."""
import difflib
import json
import re
import shlex

from .awk import run_awk
from .cmd_files import perm_string
from .cmd_text import bre_to_re
from .core import HOME, HOST, MY_IP, NOW, USER, ShellError

ARCHIVE_MAGIC = "\x1f\x8bTAR"
SHELL_PID, PS_PID = 1021, 5001


def default_procs():
    """The background processes every box has. Tickets add their own."""
    return {
        1: {"user": "root", "cpu": 0.0, "mem": 0.1, "cmd": "/sbin/init", "start": "Nov01"},
        612: {"user": "root", "cpu": 0.0, "mem": 0.2, "cmd": "/usr/sbin/sshd -D", "start": "Nov01"},
        655: {"user": "root", "cpu": 0.0, "mem": 0.1, "cmd": "/usr/sbin/cron -f", "start": "Nov01"},
        SHELL_PID: {"user": USER, "cpu": 0.0, "mem": 0.1, "cmd": "-bash", "start": "08:55", "tty": "pts/0"},
    }


def sed_regex(text, ere, ignore_case):
    try:
        return re.compile(text if ere else bre_to_re(text), re.I if ignore_case else 0)
    except re.error:
        raise ShellError("sed: -e expression #1, char 0: Invalid preceding regular expression", 1)


def parse_sed(script, ere):
    """'s/a/b/g;3d' -> list of commands. Supports s p d q with addresses N, N,M, $, /re/."""
    cmds, i, n = [], 0, len(script)

    def fail(msg):
        raise ShellError(f"sed: -e expression #1, char {i}: {msg}", 1,
                         tip="example: sed 's/old/new/' file    (s = substitute, g = every match)")

    def read_until(delim):
        nonlocal i
        out = []
        while i < n and script[i] != delim:
            if script[i] == "\\" and i + 1 < n:
                out.append(script[i + 1] if script[i + 1] == delim else script[i:i + 2])
                i += 2
            else:
                out.append(script[i])
                i += 1
        if i >= n:
            fail(f"unterminated `{'s' if delim else ''}' command")
        i += 1
        return "".join(out)

    def addr():
        nonlocal i
        if i < n and script[i].isdigit():
            j = i
            while i < n and script[i].isdigit():
                i += 1
            return ("n", int(script[j:i]))
        if i < n and script[i] == "$":
            i += 1
            return ("last", None)
        if i < n and script[i] == "/":
            i += 1
            return ("re", sed_regex(read_until("/"), ere, False))
        return None
    while i < n:
        while i < n and script[i] in " \t;\n":
            i += 1
        if i >= n:
            break
        a1 = addr()
        a2 = None
        if a1 and i < n and script[i] == ",":
            i += 1
            a2 = addr()
        neg = False
        while i < n and script[i] in " !":
            neg = neg or script[i] == "!"
            i += 1
        if i >= n:
            fail("missing command")
        ch = script[i]
        i += 1
        if ch == "s":
            delim = script[i] if i < n else fail("unterminated `s' command")
            i += 1
            pat, repl = read_until(delim), read_until(delim)
            flags = ""
            while i < n and script[i] not in ";}\n ":
                flags += script[i]
                i += 1
            rx = sed_regex(pat, ere, "I" in flags or "i" in flags)
            cmds.append((a1, a2, neg, "s", (rx, repl, "g" in flags, "p" in flags)))
        elif ch in "pdq":
            cmds.append((a1, a2, neg, ch, None))
        else:
            fail(f"unknown command: `{ch}'")
    return cmds


def sed_replacement(repl, m):
    out, i = [], 0
    while i < len(repl):
        ch = repl[i]
        if ch == "\\" and i + 1 < len(repl):
            nxt = repl[i + 1]
            out.append(m.group(int(nxt)) or "" if nxt.isdigit() else {"n": "\n", "t": "\t"}.get(nxt, nxt))
            i += 2
        elif ch == "&":
            out.append(m.group(0))
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def run_sed(cmds, text, quiet):
    lines = text.split("\n") if text else []
    out, active = [], {}
    total = len(lines)
    for no, line in enumerate(lines, 1):
        deleted, stop = False, False
        for k, (a1, a2, neg, cmd, arg) in enumerate(cmds):
            def hit(a):
                return (a[0] == "n" and no == a[1]) or (a[0] == "last" and no == total) or \
                       (a[0] == "re" and bool(a[1].search(line)))
            if a1 is None:
                sel = True
            elif a2 is None:
                sel = hit(a1)
            elif active.get(k):
                sel = True
                if (a2[0] == "n" and no >= a2[1]) or (a2[0] != "n" and hit(a2)):
                    active[k] = False
            elif hit(a1):
                sel = True
                active[k] = not (a2[0] == "n" and a2[1] <= no)
            else:
                sel = False
            if sel == neg:
                continue
            if cmd == "s":
                rx, repl, glob, printit = arg
                new, count = rx.subn(lambda m: sed_replacement(repl, m), line, 0 if glob else 1)
                line = new
                if count and printit:
                    out.append(line)
            elif cmd == "p":
                out.append(line)
            elif cmd == "d":
                deleted = True
                break
            elif cmd == "q":
                stop = True
        if not deleted and not quiet:
            out.append(line)
        if stop:
            break
    return "\n".join(out)


def set_chars(spec):
    """tr character set: a-z ranges, [:upper:] classes and \\n \\r \\t escapes."""
    classes = {"[:upper:]": "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "[:lower:]": "abcdefghijklmnopqrstuvwxyz",
               "[:digit:]": "0123456789", "[:space:]": " \t\n\r", "[:alpha:]": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
               "[:alnum:]": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", "[:punct:]": "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"}
    out, i = [], 0
    while i < len(spec):
        for name, chars in classes.items():
            if spec.startswith(name, i):
                out += list(chars)
                i += len(name)
                break
        else:
            ch = spec[i]
            if ch == "\\" and i + 1 < len(spec):
                ch = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\"}.get(spec[i + 1], spec[i + 1])
                i += 1
            if i + 2 < len(spec) and spec[i + 1] == "-":
                last = spec[i + 2]
                out += [chr(k) for k in range(ord(ch), ord(last) + 1)]
                i += 3
            else:
                out.append(ch)
                i += 1
    return out


class SysCommands:
    # ---------------------------------------------------------- text processing
    def cmd_sed(self, args, stdin):
        scripts, files, quiet, ere, inplace, i = [], [], False, False, None, 0
        while i < len(args):
            a = args[i]
            if a in ("-e", "--expression") and i + 1 < len(args):
                scripts.append(args[i + 1])
                i += 1
            elif a.startswith("--expression="):
                scripts.append(a.split("=", 1)[1])
            elif a.startswith("-i"):
                inplace = a[2:]
            elif a in ("-n", "--quiet", "--silent"):
                quiet = True
            elif a in ("-E", "-r", "--regexp-extended"):
                ere = True
            elif a.startswith("-") and len(a) > 1 and set(a[1:]) <= set("nEri"):
                quiet, ere = quiet or "n" in a, ere or "E" in a or "r" in a
                if "i" in a:
                    inplace = ""
            elif a.startswith("-") and a != "-":
                raise ShellError(f"sed: invalid option -- '{a.lstrip('-')}'\nUsage: sed [OPTION]... {{script-only-if-no-other-script}} [input-file]...",
                                 1, tip="man sed lists the options")
            else:
                files.append(a)
            i += 1
        if not scripts:
            if not files:
                raise ShellError("Usage: sed [OPTION]... {script-only-if-no-other-script} [input-file]...", 1,
                                 tip="example: sed 's/old/new/' file")
            scripts.append(files.pop(0))
        cmds = parse_sed(";".join(scripts), ere)
        if inplace is None:
            return run_sed(cmds, self.gather(files, stdin, "sed", "sed 's/a/b/' file", msg="sed: can't read {name}: No such file or directory"), quiet)
        if not files:
            raise ShellError("sed: no input files", 1, tip="-i changes files in place: sed -i 's/old/new/' FILE")
        for f in files:
            p = self.path(f)
            if not self.fs.isfile(p):
                self.warn(f"sed: can't read {f}: No such file or directory", self.missing_tip(f, "sed"))
            elif not self.writable(p):
                self.warn(f"sed: couldn't open temporary file {self.fs.parent(p)}/sedX1y2Z3: Permission denied")
            else:
                if inplace:
                    self.fs.write(p + inplace, self.fs.d[p])
                self.fs.write(p, run_sed(cmds, self.fs.d[p], quiet))
        return ""

    def cmd_awk(self, args, stdin):
        fs, assigns, i = " ", {}, 0
        while i < len(args) and args[i].startswith("-") and args[i] != "-":
            a = args[i]
            if a.startswith("-F"):
                fs = a[2:] if len(a) > 2 else (args[i + 1] if i + 1 < len(args) else "")
                i += 1 if len(a) > 2 else 2
                fs = "\t" if fs == "t" else fs
            elif a == "-v" and i + 1 < len(args):
                k, _, v = args[i + 1].partition("=")
                assigns[k] = v
                i += 2
            else:
                raise ShellError(f"awk: unknown option {a} ignored", 2, tip="man awk shows what this awk understands")
        if i >= len(args):
            raise ShellError("usage: awk [-F fs][-v var=value] 'prog' [file ...]", 2, tip="example: awk '{print $1}' file")
        program, files = args[i], args[i + 1:]
        texts = [self.gather([f], stdin, "awk", "awk '{print $1}' file", msg="awk: fatal: cannot open file `{name}' for reading: No such file or directory")
                 for f in files] if files else [self.gather([], stdin, "awk", "cat file | awk '{print $1}'")]
        return run_awk(program, texts, fs, assigns)

    def cmd_tr(self, args, stdin):
        o, pos = self.opts(args, "tr", "dsc")
        if stdin is None:
            raise ShellError("tr: reading from the keyboard is not supported in this practice shell", 1,
                             tip="tr only reads input: use  tr ... < file  or  cat file | tr ...")
        if not pos or ("d" not in o and "s" not in o and len(pos) < 2):
            raise ShellError(f"tr: missing operand{' after ' + repr(pos[0]) if pos else ''}\nTry 'tr --help' for more information.", 1,
                             tip="example: tr a-z A-Z   or   tr -d ','")
        set1 = set_chars(pos[0])
        text = stdin
        if "c" in o:
            text = "".join(ch for ch in text if ch in set1 or ch == "\n") if "d" in o else text
        if "d" in o:
            return "".join(ch for ch in text if ch not in set1) if "c" not in o else text
        set2 = set_chars(pos[1]) if len(pos) > 1 else []
        if set2:
            set2 += [set2[-1]] * max(0, len(set1) - len(set2))
            table = {a: b for a, b in zip(set1, set2)}
            text = "".join(table.get(ch, ch) for ch in text)
        if "s" in o:
            squeeze = set(set2 or set1)
            text = "".join(ch for k, ch in enumerate(text) if not (k and ch == text[k - 1] and ch in squeeze))
        return text

    def cmd_tee(self, args, stdin):
        o, files = self.opts(args, "tee", "a")
        if stdin is None:
            raise ShellError("tee: reading from the keyboard is not supported in this practice shell", 1,
                             tip="use it in a pipe: ... | tee FILE")
        for f in files:
            p = self.path(f)
            if self.fs.isdir(p):
                self.warn(f"tee: {f}: Is a directory")
            elif not self.fs.isdir(self.fs.parent(p)):
                self.warn(f"tee: {f}: No such file or directory", "the folder does not exist yet (see man mkdir)")
            elif not self.writable(p):
                self.warn(f"tee: {f}: Permission denied")
            elif "a" in o and self.fs.isfile(p):
                self.append_file(p, stdin)
            else:
                self.fs.write(p, stdin)
        return stdin

    def cmd_diff(self, args, stdin):
        o, files = self.opts(args, "diff", "uq")
        if len(files) != 2:
            raise ShellError(f"diff: {'missing operand after ' + repr(files[-1]) if files else 'missing operand'}\n"
                             "diff: Try 'diff --help' for more information.", 2, tip="example: diff old.txt new.txt")
        texts = []
        for f in files:
            p = self.path(f)
            if self.fs.isdir(p):
                raise ShellError(f"diff: {f}: Is a directory (comparing folders is not supported here)", 2)
            if not self.fs.isfile(p):
                raise ShellError(f"diff: {f}: No such file or directory", 2, tip=self.missing_tip(f, "diff"))
            texts.append(self.read_text(f, "diff").split("\n") if self.fs.d[p] else [])
        a, b = texts
        if a == b:
            return ""
        self._status = 1
        if "q" in o:
            return f"Files {files[0]} and {files[1]} differ"
        if "u" in o:
            stamp = "2026-11-12 09:00:00.000000000 +0100"
            body = list(difflib.unified_diff(a, b, lineterm="", n=3))[2:]
            return "\n".join([f"--- {files[0]}\t{stamp}", f"+++ {files[1]}\t{stamp}"] + body)

        def rng(lo, hi):
            return str(lo) if lo == hi else f"{lo},{hi}"
        out = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            if tag == "replace":
                out += [f"{rng(i1 + 1, i2)}c{rng(j1 + 1, j2)}"] + ["< " + x for x in a[i1:i2]] + ["---"] + ["> " + x for x in b[j1:j2]]
            elif tag == "delete":
                out += [f"{rng(i1 + 1, i2)}d{j1}"] + ["< " + x for x in a[i1:i2]]
            else:
                out += [f"{i1}a{rng(j1 + 1, j2)}"] + ["> " + x for x in b[j1:j2]]
        return "\n".join(out)

    def cmd_xargs(self, args, stdin):
        n, repl, i = None, None, 0
        while i < len(args) and args[i].startswith("-"):
            if args[i] == "-n" and i + 1 < len(args):
                n, i = int(args[i + 1]), i + 2
            elif args[i].startswith("-I"):
                repl, i = (args[i][2:] or args[i + 1]), i + (1 if len(args[i]) > 2 else 2)
            else:
                raise ShellError(f"xargs: invalid option -- '{args[i].lstrip('-')}'", 1, tip="man xargs lists the options")
        cmd = args[i:] or ["echo"]
        if stdin is None:
            raise ShellError("xargs: reading from the keyboard is not supported in this practice shell", 1,
                             tip="use it in a pipe: find . -name '*.pyc' | xargs rm")
        items = stdin.splitlines() if repl else stdin.split()
        if not items:
            return ""
        if repl:
            groups = [[a.replace(repl, it) for a in cmd] for it in items]
        else:
            size = n or len(items)
            groups = [cmd + items[k:k + size] for k in range(0, len(items), size)]
        out = []
        for argv in groups:
            res = self.dispatch(argv, None)
            if res:
                out.append(res)
        return "\n".join(out)

    def cmd_basename(self, args, stdin):
        if not args:
            raise ShellError("basename: missing operand\nTry 'basename --help' for more information.", 1)
        name = args[0].rstrip("/").rsplit("/", 1)[-1] or "/"
        return name[:-len(args[1])] if len(args) > 1 and name.endswith(args[1]) and name != args[1] else name

    def cmd_dirname(self, args, stdin):
        if not args:
            raise ShellError("dirname: missing operand\nTry 'dirname --help' for more information.", 1)
        head = args[0].rstrip("/").rsplit("/", 1)
        return "." if len(head) == 1 else (head[0] or "/")

    def cmd_sleep(self, args, stdin):
        if not args:
            raise ShellError("sleep: missing operand\nTry 'sleep --help' for more information.", 1)
        if not re.fullmatch(r"\d+(\.\d+)?[smhd]?", args[0]):
            raise ShellError(f"sleep: invalid time interval '{args[0]}'\nTry 'sleep --help' for more information.", 1)
        return ""

    # ---------------------------------------------------------- processes and ports
    def process_rows(self):
        """All processes (ticket ones + the commands of the current pipeline, like a real ps)."""
        rows = dict(self.procs)
        rows[PS_PID] = {"user": USER, "cpu": 0.0, "mem": 0.0, "cmd": "ps", "start": "09:00", "tty": "pts/0"}
        for k, cmdline in enumerate(c for c in getattr(self, "pipeline_cmds", []) if c.split()[0] != "ps"):
            rows[PS_PID + 1 + k] = {"user": USER, "cpu": 0.0, "mem": 0.0, "cmd": cmdline, "start": "09:00", "tty": "pts/0"}
        return dict(sorted(rows.items()))

    def cmd_ps(self, args, stdin):
        flags = "".join(a.lstrip("-") for a in args if not a.startswith("--"))
        rows = self.process_rows()
        if not flags:
            mine = {p: r for p, r in rows.items() if r.get("tty")}
            return "    PID TTY          TIME CMD\n" + "\n".join(
                f"{p:>7} {r['tty']:<8} 00:00:00 {r['cmd'].lstrip('-').split()[0]}" for p, r in mine.items())
        if "e" in flags and "f" in flags:
            out = ["UID          PID    PPID  C STIME TTY          TIME CMD"]
            for p, r in rows.items():
                out.append(f"{r['user']:<8} {p:>7} {0 if p == 1 else 1:>7}  {int(r['cpu'])} {r['start']:>5} "
                           f"{r.get('tty', '?'):<8} 00:00:00 {r['cmd']}")
            return "\n".join(out)
        if "a" in flags and "u" in flags or "e" in flags:
            out = ["USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND"]
            for p, r in rows.items():
                out.append(f"{r['user']:<8} {p:>7} {r['cpu']:>4.1f} {r['mem']:>4.1f} {int(r['mem'] * 90000 + 4000):>7} "
                           f"{int(r['mem'] * 12000 + 900):>6} {r.get('tty', '?'):<8} {'R' if r['cpu'] > 50 else 'S':<4} "
                           f"{r['start']:>5} {'0:00' if r['cpu'] < 50 else '312:41':>6} {r['cmd']}")
            return "\n".join(out)
        raise ShellError("error: unsupported option (BSD syntax)\nUsage:\n ps [options]", 1,
                         tip="try ps aux (all processes with CPU and memory) or ps -ef")

    def cmd_pgrep(self, args, stdin):
        o, pos = self.opts(args, "pgrep", "fl")
        if not pos:
            raise ShellError("pgrep: no matching criteria specified\nTry `pgrep --help' for more information.", 2)
        rx = re.compile(pos[0])
        hits = [(p, r) for p, r in self.procs.items()
                if rx.search(r["cmd"] if "f" in o else r["cmd"].lstrip("-").split()[0].rsplit("/", 1)[-1])]
        self._status = 0 if hits else 1
        return "\n".join(f"{p} {r['cmd'].split()[0].rsplit('/', 1)[-1]}" if "l" in o else str(p) for p, r in hits)

    def cmd_kill(self, args, stdin):
        sig, pids, i = "TERM", [], 0
        while i < len(args):
            a = args[i]
            if a == "-s" and i + 1 < len(args):
                sig, i = args[i + 1].upper().removeprefix("SIG"), i + 2
                continue
            if a.startswith("-") and len(a) > 1 and not a[1:].isdigit() or (a.startswith("-") and a[1:].isdigit() and not pids):
                sig = {"9": "KILL", "15": "TERM", "1": "HUP", "2": "INT"}.get(a[1:], a[1:].upper().removeprefix("SIG"))
            else:
                pids.append(a)
            i += 1
        if not pids:
            raise ShellError("bash: kill: usage: kill [-s sigspec | -n signum | -sigspec] pid | jobspec ... or kill -l [sigspec]", 2,
                             tip="example: kill 1234   (or kill -9 1234 if it does not stop)")
        if sig not in ("TERM", "KILL", "HUP", "INT", "STOP", "CONT", "QUIT", "USR1", "USR2"):
            raise ShellError(f"bash: kill: {sig}: invalid signal specification", 1)
        for raw in pids:
            if not raw.isdigit():
                self.warn(f"bash: kill: {raw}: arguments must be process or job IDs")
                continue
            pid = int(raw)
            proc = self.procs.get(pid)
            if proc is None:
                self.warn(f"bash: kill: ({pid}) - No such process", "list the running processes with ps aux")
            elif proc["user"] != USER:
                self.warn(f"bash: kill: ({pid}) - Operation not permitted", f"that process belongs to {proc['user']}, not to you")
            elif pid == SHELL_PID:
                self.running = False
            elif sig in ("TERM", "HUP", "INT", "QUIT") and proc.get("stubborn"):
                self.tip("the process ignored that polite request (SIGTERM): there is a stronger signal, see man kill")
            elif sig in ("STOP", "CONT", "USR1", "USR2"):
                pass
            else:
                del self.procs[pid]
        return ""

    def cmd_ss(self, args, stdin):
        flags = "".join(a.lstrip("-") for a in args)
        if "l" not in flags and "a" not in flags:
            return "Netid State Recv-Q Send-Q Local Address:Port Peer Address:Port Process"
        procs = "p" in flags
        head = "Netid " if "u" in flags or "t" in flags and False else ""
        rows = [("sshd", 612, "0.0.0.0:22"), ("sshd", 612, "[::]:22")]
        rows += [(self.procs[pid]["cmd"].split()[0].rsplit("/", 1)[-1], pid, f"127.0.0.1:{port}")
                 for port, pid in sorted(self.listen.items()) if pid in self.procs]
        out = [f"{head}State  Recv-Q Send-Q Local Address:Port Peer Address:Port" + (" Process" if procs else "")]
        for name, pid, local in rows:
            out.append(f"{head}LISTEN 0      128    {local:>21}      0.0.0.0:*" + (f'    users:(("{name}",pid={pid},fd=3))' if procs else ""))
        return "\n".join(out)

    # ---------------------------------------------------------- services and logs
    def unit_name(self, name):
        return name[:-8] if name.endswith(".service") else name

    def cmd_systemctl(self, args, stdin):
        user = "--user" in args
        args = [a for a in args if not a.startswith("--")]
        if len(args) < 2:
            raise ShellError("systemctl: missing command and unit\nUsage: systemctl [--user] status|start|stop|restart|is-active UNIT", 1,
                             tip="example: systemctl --user status myapp")
        action, name = args[0], self.unit_name(args[1])
        units = self.svc if user else {k: v for k, v in self.svc.items() if v.get("system")}
        svc = units.get(name)
        if svc is None:
            raise ShellError(f"Unit {name}.service could not be found." if action == "status"
                             else f"Failed to {action} {name}.service: Unit {name}.service not found.", 4 if action == "status" else 5,
                             tip="services of your own user need the --user option: systemctl --user ..."
                             if not user and name in self.svc else "check the name of the service")
        if action == "status":
            return self.service_status(name, svc)
        if action == "is-active":
            self._status = 0 if svc["state"] == "active" else 3
            return svc["state"]
        if action in ("start", "restart", "stop"):
            if not user:
                raise ShellError(f"Failed to {action} {name}.service: Interactive authentication required.\n"
                                 f"See system logs and 'systemctl status {name}.service' for details.", 1,
                                 tip="system services need root. User services run with --user")
            if action == "stop":
                self.procs.pop(svc.get("pid"), None)
                svc["state"] = "inactive"
                return ""
            errors = svc["start"](self) if svc.get("start") else []
            svc["journal"] = svc.get("journal", [])
            if errors:
                svc["state"] = "failed"
                svc["journal"] += [("09:31:%02d" % (k + 10), m) for k, m in enumerate(errors)]
                raise ShellError(f'Job for {name}.service failed because the control process exited with error code.\n'
                                 f'See "systemctl --user status {name}.service" and "journalctl --user -xeu {name}.service" for details.', 1)
            pid = svc["pid"] = 7000 + len(svc["journal"])
            self.procs[pid] = {"user": USER, "cpu": 0.4, "mem": 1.2, "cmd": svc.get("exec", name), "start": "09:31"}
            svc["state"] = "active"
            svc["journal"].append(("09:31:20", f"Started {svc.get('desc', name)}."))
            return ""
        raise ShellError(f"Unknown command verb {action}.", 1, tip="try: status, start, stop, restart, is-active")

    def service_status(self, name, svc):
        state = svc["state"]
        dot = {"active": "●", "failed": "×", "inactive": "○"}[state]
        scope = "user" if not svc.get("system") else "system"
        path = f"{HOME}/.config/systemd/user/{name}.service" if scope == "user" else f"/lib/systemd/system/{name}.service"
        active = {"active": "active (running) since Thu 2026-11-12 09:31:20 CET; 12s ago",
                  "failed": "failed (Result: exit-code) since Thu 2026-11-12 08:58:41 CET; 33min ago",
                  "inactive": "inactive (dead)"}[state]
        lines = [f"{dot} {name}.service - {svc.get('desc', name)}",
                 f"     Loaded: loaded ({path}; enabled; preset: enabled)", f"     Active: {active}"]
        if svc.get("pid") and state == "active":
            lines.append(f"   Main PID: {svc['pid']} ({svc.get('exec', name).split()[0].rsplit('/', 1)[-1]})")
        if state == "failed":
            lines.append(f"    Process: {svc.get('pid', 4410)} ExecStart={svc.get('exec', name)} (code=exited, status=1/FAILURE)")
        lines.append("")
        lines += [f"Nov 12 {t} {HOST} {name}[{svc.get('pid', 4410)}]: {m}" for t, m in svc.get("journal", [])[-8:]]
        return "\n".join(lines)

    def cmd_journalctl(self, args, stdin):
        o_unit, count, prio, i = None, None, False, 0
        while i < len(args):
            a = args[i]
            if a in ("-u", "--unit") and i + 1 < len(args):
                o_unit, i = self.unit_name(args[i + 1]), i + 2
            elif a == "-n" and i + 1 < len(args):
                count, i = int(args[i + 1]) if args[i + 1].isdigit() else 10, i + 2
            elif a.startswith("-n") and a[2:].isdigit():
                count, i = int(a[2:]), i + 1
            elif a in ("-p", "--priority") and i + 1 < len(args):
                prio, i = True, i + 2
            elif a in ("--user", "--no-pager", "-x", "-e", "-xe", "-r"):
                i += 1
            elif a.startswith("-"):
                raise ShellError(f"journalctl: unrecognized option '{a}'", 1, tip="man journalctl lists the options")
            else:
                i += 1
        lines = []
        for name, svc in self.svc.items():
            if o_unit and name != o_unit:
                continue
            lines += [(t, f"Nov 12 {t} {HOST} {name}[{svc.get('pid', 4410)}]: {m}") for t, m in svc.get("journal", [])]
        if o_unit and o_unit not in self.svc:
            return "-- No entries --"
        if prio:
            lines = [l for l in lines if re.search(r"error|failed|denied", l[1], re.I)]
        lines.sort(key=lambda x: x[0])
        texts = [l for _, l in lines]
        if count is not None:
            texts = texts[-count:]
        return "\n".join(texts) if texts else "-- No entries --"

    # ---------------------------------------------------------- remote machines
    def cmd_ssh(self, args, stdin):
        o, pos = self.opts(args, "ssh", "q", with_value="pilo")
        if not pos:
            raise ShellError("usage: ssh [-p port] [user@]hostname [command]", 255, tip="example: ssh analyst@gateway uptime")
        target, command = pos[0], " ".join(pos[1:])
        user, _, host = target.rpartition("@")
        ip = self.resolve(host)
        if not ip:
            raise ShellError(f"ssh: Could not resolve hostname {host}: Name or service not known", 255,
                             tip="the server names this computer knows are in /etc/hosts")
        from .core import ONLINE
        if ip not in ONLINE:
            raise ShellError(f"ssh: connect to host {host} port 22: Connection timed out", 255,
                             tip="the host does not answer: is it down? (ping it)")
        if not command:
            raise ShellError("ssh: an interactive login is not available in this practice shell", 1,
                             tip=f"run one command on the server instead: ssh {user + '@' if user else ''}{host} COMMAND")
        first, *rest = [seg.strip() for seg in command.split(" | ")]
        table = {"hostname": host, "whoami": user or USER, "date": NOW,
                 "uptime": " 09:00:01 up 41 days,  3:12,  1 user,  load average: 0.21, 0.18, 0.15"}
        table.update((self.remote or {}).get(host, {}))
        if first not in table:
            raise ShellError(f"bash: line 1: {first.split()[0]}: command not found", 127)
        out = table[first]
        for seg in rest:
            out = self.dispatch(shlex.split(seg), out)
        return out

    # ---------------------------------------------------------- inspecting files and the machine
    def cmd_stat(self, args, stdin):
        if not args:
            raise ShellError("stat: missing operand\nTry 'stat --help' for more information.", 1)
        out = []
        for f in args:
            p = self.path(f)
            if not self.fs.exists(p):
                self.warn(f"stat: cannot statx '{f}': No such file or directory", self.missing_tip(f, "stat"))
                continue
            is_dir = self.fs.isdir(p)
            bits = self.fs.mode(p)
            size = 4096 if is_dir else len(self.fs.d.get(p, ""))
            kind = "directory" if is_dir else ("regular empty file" if not size else "regular file")
            stamp = "2026-11-12 09:00:00.000000000 +0100"
            out.append(f"  File: {f}\n  Size: {size:<10}\tBlocks: 8          IO Block: 4096   {kind}\n"
                       f"Device: 801h/2049d\tInode: 1048577     Links: {2 if is_dir else 1}\n"
                       f"Access: ({bits:04o}/{'d' if is_dir else '-'}{perm_string(bits)})  Uid: ( 1000/ {USER})   Gid: ( 1000/ {USER})\n"
                       f"Access: {stamp}\nModify: {stamp}\nChange: {stamp}\n Birth: -")
        return "\n".join(out)

    def cmd_file(self, args, stdin):
        if not args:
            raise ShellError("Usage: file [OPTION...] [FILE...]\nTry `file --help' for more information.", 1)
        out = []
        for f in args:
            p = self.path(f)
            if not self.fs.exists(p):
                out.append(f"{f}: cannot open `{f}' (No such file or directory)")
            elif self.fs.isdir(p):
                out.append(f"{f}: directory")
            else:
                text = self.fs.d[p]
                if text.startswith(ARCHIVE_MAGIC):
                    kind = "gzip compressed data, from Unix"
                elif not text:
                    kind = "empty"
                elif text.startswith("#!"):
                    interp = text.splitlines()[0]
                    kind = ("Bourne-Again shell script" if "bash" in interp else "POSIX shell script" if "sh" in interp
                            else "script") + ", ASCII text executable"
                else:
                    kind = "ASCII text"
                    if f.endswith(".json"):
                        kind = "JSON text data"
                    if "\r\n" in text:
                        kind += ", with CRLF line terminators"
                out.append(f"{f}: {kind}")
        return "\n".join(out)

    def cmd_uptime(self, args, stdin):
        return " 09:00:01 up 12 days,  3:41,  1 user,  load average: 0.08, 0.03, 0.01"

    def cmd_free(self, args, stdin):
        if "-h" in args:
            return ("               total        used        free      shared  buff/cache   available\n"
                    "Mem:           7.7Gi       1.8Gi       4.1Gi        32Mi       1.9Gi       5.6Gi\n"
                    "Swap:          2.0Gi          0B       2.0Gi")
        return ("               total        used        free      shared  buff/cache   available\n"
                "Mem:         8056240     1887312     4296904       32768     1984120     5878928\n"
                "Swap:        2097148           0     2097148")

    # ---------------------------------------------------------- archives
    def cmd_tar(self, args, stdin):
        mode, archive, dest, names, flags, i = None, None, None, [], "", 0
        if args and not args[0].startswith("-") and set(args[0]) <= set("cxtzjvfCp"):
            args = ["-" + args[0]] + args[1:]
        while i < len(args):
            a = args[i]
            if a.startswith("-") and not a.startswith("--") and len(a) > 1:
                for ch in a[1:]:
                    if ch in "cxt":
                        mode = ch
                    elif ch == "f":
                        i += 1
                        archive = args[i] if i < len(args) else None
                    elif ch == "C":
                        i += 1
                        dest = args[i] if i < len(args) else None
                    elif ch in "zjvp":
                        flags += ch
                    else:
                        raise ShellError(f"tar: invalid option -- '{ch}'\nTry 'tar --help' or 'tar --usage' for more information.", 64)
            elif a.startswith("--directory="):
                dest = a.split("=", 1)[1]
            else:
                names.append(a)
            i += 1
        if mode is None:
            raise ShellError("tar: You must specify one of the '-Acdtrux', '--delete' or '--test-label' options\n"
                             "Try 'tar --help' or 'tar --usage' for more information.", 2,
                             tip="c = create, x = extract, t = list;  example: tar -czf backup.tar.gz folder")
        if archive is None:
            raise ShellError("tar: Refusing to read archive contents from terminal (missing -f option)\n"
                             "tar: Error is not recoverable: exiting now", 2, tip="the archive name goes after -f: tar -tzf FILE")
        verbose = "v" in flags
        if mode == "c":
            return self.tar_create(archive, names, verbose)
        p = self.path(archive)
        if not self.fs.isfile(p):
            raise ShellError(f"tar: {archive}: Cannot open: No such file or directory\n"
                             "tar: Error is not recoverable: exiting now", 2, tip=self.missing_tip(archive, "tar -tzf"))
        text = self.fs.d[p]
        if not text.startswith(ARCHIVE_MAGIC):
            raise ShellError("\ngzip: stdin: not in gzip format\ntar: Child returned status 1\n"
                             "tar: Error is not recoverable: exiting now", 2, tip=f"{archive} is not a tar.gz archive")
        members = json.loads(text[len(ARCHIVE_MAGIC):])
        wanted = [m for m in members if not names or any(m[0].rstrip("/") == n.rstrip("/") or m[0].startswith(n.rstrip("/") + "/") for n in names)]
        for n in names:
            if not any(m[0].rstrip("/") == n.rstrip("/") or m[0].startswith(n.rstrip("/") + "/") for m in members):
                self.warn(f"tar: {n}: Not found in archive")
        if mode == "t":
            return "\n".join(m[0] for m in wanted)
        base = self.path(dest) if dest else self.cwd
        if dest and not self.fs.isdir(base):
            raise ShellError(f"tar: {dest}: Cannot open: No such file or directory\ntar: Error is not recoverable: exiting now", 2,
                             tip="the folder must exist first (mkdir)")
        if not self.writable(base + "/x"):
            raise ShellError("tar: .: Cannot open: Permission denied\ntar: Error is not recoverable: exiting now", 2)
        for name, is_dir, content in wanted:
            target = self.fs.join(base, name.rstrip("/"))
            if is_dir:
                self.fs.mkdirs(target)
            else:
                self.fs.mkdirs(self.fs.parent(target))
                self.fs.write(target, content)
        if self._failed:
            self._status = 2
            self.warn("tar: Exiting with failure status due to previous errors")
        return "\n".join(m[0] for m in wanted) if verbose else ""

    def tar_create(self, archive, names, verbose):
        if not names:
            raise ShellError("tar: Cowardly refusing to create an empty archive\nTry 'tar --help' or 'tar --usage' for more information.", 2,
                             tip="name the files or folders to put in: tar -czf backup.tar.gz folder")
        out_path = self.path(archive)
        if not self.writable(out_path) or not self.fs.isdir(self.fs.parent(out_path)):
            raise ShellError(f"tar: {archive}: Cannot open: " + ("Permission denied" if self.fs.isdir(self.fs.parent(out_path))
                             else "No such file or directory") + "\ntar: Error is not recoverable: exiting now", 2,
                             tip="the folder for the archive must exist (mkdir) and be one you can write to")
        members = []

        def add(rel, full):
            if full == out_path:
                return
            if self.fs.isdir(full):
                members.append([rel.rstrip("/") + "/", True, ""])
                for n, _ in self.fs.children(full):
                    add(rel.rstrip("/") + "/" + n, self.fs.join(full, n))
            else:
                members.append([rel, False, self.fs.d[full]])
        for n in names:
            full = self.path(n)
            if not self.fs.exists(full):
                self.warn(f"tar: {n}: Cannot stat: No such file or directory")
            else:
                if n.startswith("/"):
                    self.show_error("tar: Removing leading `/' from member names")
                add(n.lstrip("/"), full)
        self.fs.write(out_path, ARCHIVE_MAGIC + json.dumps(members))
        if self._failed:
            self._status = 2
            self.warn("tar: Exiting with failure status due to previous errors")
        return "\n".join(m[0] for m in members) if verbose else ""


def tar_members(fs, path):
    """Names inside an archive made by tar here (for ticket checks); [] if it is not one."""
    text = fs.d.get(path, "")
    return [m[0] for m in json.loads(text[len(ARCHIVE_MAGIC):])] if text.startswith(ARCHIVE_MAGIC) else []
