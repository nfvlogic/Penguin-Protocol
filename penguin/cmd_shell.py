"""Shell builtins and small utilities: echo printf alias unalias seq nl rev tac date umask chown chgrp."""
import calendar
import re
import shlex
from datetime import datetime

from .core import HOME, HOST, NOW, USER, ShellError

NOW_DT = datetime(2026, 11, 12, 9, 0, 1)
EPOCH = calendar.timegm((2026, 11, 12, 8, 0, 1))   # 09:00:01 CET = 08:00:01 UTC


def escapes(text, stop_at_c=False):
    """Process backslash escapes like echo -e / printf: \\n \\t \\\\ \\r \\a \\b \\e \\0NNN \\xHH."""
    out, i = [], 0
    simple = {"n": "\n", "t": "\t", "\\": "\\", "r": "\r", "a": "\a", "b": "\b", "e": "\x1b", "f": "\f", "v": "\v", '"': '"', "'": "'"}
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt == "c" and stop_at_c:
                return "".join(out), True
            m = re.match(r"0([0-7]{1,3})|x([0-9a-fA-F]{1,2})", text[i + 1:])
            if m:
                out.append(chr(int(m.group(1), 8) if m.group(1) is not None else int(m.group(2), 16)))
                i += 1 + m.end()
                continue
            out.append(simple.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out), False


def printf_format(fmt, args):
    """printf: the format is reused until every argument is used, like the real one."""
    spec = re.compile(r"%([-+ 0#]*)(\d+|\*)?(?:\.(\d+))?([sdiouxXcbeEfgG%])")
    fmt = escapes(fmt)[0] if "%%" not in fmt else fmt   # keep %% safe, escapes first otherwise
    fmt = escapes(fmt)[0] if "%%" in fmt and "\\" in fmt else fmt
    pieces, used_any = [], False
    args = list(args)
    while True:
        taken = 0

        def repl(m):
            nonlocal taken
            flags, width, prec, conv = m.group(1), m.group(2) or "", m.group(3), m.group(4)
            if conv == "%":
                return "%"
            arg = args.pop(0) if args else ""
            taken += 1
            if conv == "b":
                arg = escapes(arg)[0]
                conv = "s"
            if conv == "c":
                return (arg[:1]).rjust(int(width or 0))
            if conv in "di":
                try:
                    n = int(arg or 0, 0)
                except ValueError:
                    n = 0
                return ("%" + flags + width + "d") % n
            if conv in "ouxX":
                try:
                    n = int(arg or 0, 0)
                except ValueError:
                    n = 0
                return ("%" + flags + width + conv) % n
            if conv in "eEfgG":
                try:
                    f = float(arg or 0)
                except ValueError:
                    f = 0.0
                return ("%" + flags + width + (("." + prec) if prec is not None else "") + conv) % f
            return ("%" + flags + width + (("." + prec) if prec is not None else "") + "s") % arg
        pieces.append(spec.sub(repl, fmt))
        used_any = used_any or taken > 0
        if not args or taken == 0:
            break
    return "".join(pieces)


class ShellCommands:
    def cmd_echo(self, args, stdin):
        newline_off, interpret = False, False
        while args and re.fullmatch(r"-[neE]+", args[0]):
            newline_off = newline_off or "n" in args[0]
            if "e" in args[0]:
                interpret = True
            if "E" in args[0]:
                interpret = False
            args = args[1:]
        text = " ".join(args)
        return escapes(text, True)[0] if interpret else text

    def cmd_printf(self, args, stdin):
        if not args:
            raise ShellError("printf: usage: printf [-v var] format [arguments]", 2,
                             tip='example: printf "%s is %d\\n" age 30')
        out = printf_format(args[0], args[1:])
        return out[:-1] if out.endswith("\n") else out

    def cmd_alias(self, args, stdin):
        real = {k: v for k, v in self.aliases.items() if k not in ("levels", "logout", "pip3")}
        if not args:
            return "\n".join(f"alias {k}='{' '.join(v)}'" for k, v in sorted(real.items()))
        out = []
        for a in args:
            name, eq, value = a.partition("=")
            if eq:
                self.aliases[name] = shlex.split(value) if value else []
            elif name in real:
                out.append(f"alias {name}='{' '.join(real[name])}'")
            else:
                self.warn(f"bash: alias: {name}: not found")
        return "\n".join(out)

    def cmd_unalias(self, args, stdin):
        if not args:
            raise ShellError("unalias: usage: unalias [-a] name [name ...]", 2)
        for a in args:
            if a == "-a":
                self.aliases.clear()
            elif a in self.aliases:
                del self.aliases[a]
            else:
                self.warn(f"bash: unalias: {a}: not found")
        return ""

    def cmd_seq(self, args, stdin):
        nums = []
        for a in args:
            if not re.fullmatch(r"-?\d+", a):
                raise ShellError(f"seq: invalid floating point argument: '{a}'\nTry 'seq --help' for more information.", 1,
                                 tip="example: seq 1 5")
            nums.append(int(a))
        if not nums or len(nums) > 3:
            raise ShellError("seq: missing operand\nTry 'seq --help' for more information.", 1, tip="example: seq 1 5")
        first, step, last = (1, 1, nums[0]) if len(nums) == 1 else ((nums[0], 1, nums[1]) if len(nums) == 2 else tuple(nums))
        if step == 0:
            raise ShellError("seq: invalid Zero increment value: '0'", 1)
        return "\n".join(str(v) for v in range(first, last + (1 if step > 0 else -1), step))

    def cmd_nl(self, args, stdin):
        o, files = self.opts(args, "nl", "", with_value="b")
        text = self.gather(files, stdin, "nl", "cat file | nl")
        number_all = o.get("b") == "a"
        out, n = [], 0
        for line in text.split("\n"):
            if line == "" and not number_all:
                out.append(" " * 7)
            else:
                n += 1
                out.append(f"{n:>6}\t{line}")
        return "\n".join(out)

    def cmd_rev(self, args, stdin):
        return "\n".join(l[::-1] for l in self.gather(args, stdin, "rev", "echo hello | rev").split("\n"))

    def cmd_tac(self, args, stdin):
        lines = self.gather(args, stdin, "tac", "cat file | tac").split("\n")
        return "\n".join(reversed(lines))

    def cmd_date(self, args, stdin):
        utc = "-u" in args
        args = [a for a in args if a != "-u"]
        dt = datetime(2026, 11, 12, 8, 0, 1) if utc else NOW_DT
        if not args:
            return NOW.replace("CET", "UTC").replace("09:00:01", "08:00:01") if utc else NOW
        if args[0] in ("-I", "--iso-8601"):
            return "2026-11-12"
        if args[0].startswith("-"):
            raise ShellError(f"date: invalid option -- '{args[0].lstrip('-')[:1]}'\nTry 'date --help' for more information.", 1,
                             tip="example: date +%F  (2026-11-12)   date +%H:%M")
        if not args[0].startswith("+"):
            raise ShellError(f"date: invalid date '{args[0]}'", 1, tip="format the date with a plus: date +%Y-%m-%d")
        fmt = args[0][1:].replace("%s", str(EPOCH)).replace("%Z", "UTC" if utc else "CET").replace("%z", "+0000" if utc else "+0100")
        fmt = fmt.replace("%F", "%Y-%m-%d").replace("%T", "%H:%M:%S").replace("%D", "%m/%d/%y").replace("%R", "%H:%M")
        return dt.strftime(fmt)

    def cmd_pushd(self, args, stdin):
        target = args[0] if args else None
        if target is None:
            if not self.dirstack:
                raise ShellError("bash: pushd: no other directory", 1)
            target = self.dirstack[-1]
            self.dirstack[-1] = self.cwd
        else:
            self.dirstack.append(self.cwd)
        try:
            self.cmd_cd([target], None)
        except ShellError:
            if args:
                self.dirstack.pop()
            raise
        return self.cmd_dirs([], None)

    def cmd_popd(self, args, stdin):
        if not self.dirstack:
            raise ShellError("bash: popd: directory stack empty", 1)
        self.cmd_cd([self.dirstack.pop()], None)
        return self.cmd_dirs([], None)

    def cmd_dirs(self, args, stdin):
        return " ".join([self.short_cwd()] + [("~" + d[len(HOME):]) if d.startswith(HOME) else d for d in reversed(self.dirstack)])

    def cmd_top(self, args, stdin):
        rows = sorted(self.process_rows().items(), key=lambda kv: -kv[1]["cpu"])
        busy = sum(r["cpu"] for _, r in rows)
        out = ["top - 09:00:01 up 12 days,  3:41,  1 user,  load average: " + f"{busy / 100 + 0.08:.2f}, 0.03, 0.01",
               f"Tasks: {len(rows):>3} total,   {1 + (busy > 50)} running, {len(rows) - 1 - (busy > 50)} sleeping,   0 stopped,   0 zombie",
               f"%Cpu(s): {min(busy, 100):4.1f} us,  0.5 sy,  0.0 ni, {max(99.5 - busy, 0):4.1f} id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st",
               "MiB Mem :   7867.0 total,   4196.2 free,   1843.1 used,   1936.9 buff/cache",
               "MiB Swap:   2048.0 total,   2048.0 free,      0.0 used.   5740.8 avail Mem",
               "", "    PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND"]
        for pid, r in rows:
            out.append(f"{pid:>7} {r['user']:<9} 20   0 {int(r['mem'] * 90000 + 4000):>7} {int(r['mem'] * 12000 + 900):>6} "
                       f"{int(r['mem'] * 2000 + 400):>6} {'R' if r['cpu'] > 50 else 'S'} {r['cpu']:>5.1f} {r['mem']:>5.1f} "
                       f"{'312:41.07' if r['cpu'] > 50 else '  0:00.12'} {r['cmd'].split()[0].lstrip('-').rsplit('/', 1)[-1]}")
        self.tip("real top keeps refreshing until you press q: here you get one snapshot")
        return "\n".join(out)

    def cmd_uname(self, args, stdin):
        parts = {"s": "Linux", "n": self.hostname, "r": "6.8.0-corp", "v": "#1 SMP PREEMPT_DYNAMIC Thu Oct 30 10:12:44 UTC 2026",
                 "m": "x86_64", "o": "GNU/Linux", "p": "x86_64", "i": "x86_64"}
        flags = "".join(a.lstrip("-") for a in args if a.startswith("-") and not a.startswith("--"))
        if any(a == "--all" for a in args):
            flags += "a"
        if not flags:
            return "Linux"
        for ch in flags:
            if ch not in "asnrvmopi":
                raise ShellError(f"uname: invalid option -- '{ch}'\nTry 'uname --help' for more information.", 1)
        order = "snrvmo" if "a" in flags else [k for k in "snrvmopi" if k in flags]
        return " ".join(parts[k] for k in order)

    def cmd_id(self, args, stdin):
        flags = "".join(a.lstrip("-") for a in args if a.startswith("-"))
        names = "n" in flags
        if "u" in flags:
            return USER if names else "1000"
        if "g" in flags and "G" not in flags:
            return USER if names else "1000"
        if "G" in flags:
            return f"{USER} users" if names else "1000 100"
        return f"uid=1000({USER}) gid=1000({USER}) groups=1000({USER}),100(users)"

    def cmd_umask(self, args, stdin):
        return "0022"

    def cmd_chown(self, args, stdin, cmd="chown"):
        args = [a for a in args if a != "-R"]
        if len(args) < 2:
            raise ShellError(f"{cmd}: missing operand{' after ' + repr(args[0]) if args else ''}\n"
                             f"Try '{cmd} --help' for more information.", 1, tip=f"example: {cmd} analyst file.txt")
        owner = args[0].replace(":", " ").split()
        for n in args[1:]:
            p = self.path(n)
            if not self.fs.exists(p):
                self.warn(f"{cmd}: cannot access '{n}': No such file or directory", self.missing_tip(n, cmd))
            elif any(o != USER for o in owner) or not self.writable(p):
                self.warn(f"{cmd}: changing ownership of '{n}': Operation not permitted",
                          "only root can give files to somebody else (you are not in sudoers here)")
        return ""

    def cmd_chgrp(self, args, stdin):
        return self.cmd_chown(args, stdin, "chgrp")
