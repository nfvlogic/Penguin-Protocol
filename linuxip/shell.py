"""The shell itself: runs command lines like bash and drives the main loop."""
import os
import re
import shutil
import sys
import time

from .cmd_dev import DevCommands
from .cmd_files import FileCommands
from .cmd_network import NetworkCommands
from .cmd_text import TextCommands
from .cmd_sys import SysCommands, default_procs
from .cmd_tickets import TicketCommands
from .core import HOME, HOST, MY_IP, NOW, TTY, USER, ShellError, c, plain
from .manual import MAN
from .parser import parse, split_lists, tokenize
from .tickets import TOTAL
from .vfs import FS

ALIASES = {"ll": ["ls", "-alF"], "la": ["ls", "-A"], "l": ["ls", "-CF"],
           "levels": ["tasks"], "level": ["task"], "logout": ["exit"], "pip3": ["pip"]}
# Commands that exist on a real system but are not part of MAN (handled with a real message).
EXTRA = {"apt", "apt-get", "printenv", "whatis", "nano", "vim", "vi", "code"}
WINDOWS = {"cls": "clear", "ipconfig": "ip addr", "del": "rm", "copy": "cp", "move": "mv",
           "ren": "mv", "md": "mkdir -p", "findstr": "grep", "tasklist": "ps", "rd": "rm -r",
           "systeminfo": "uname -a", "where": "which"}
BUILTINS = {"cd", "export", "unset", "source", "history", "type", "exit", "help", "echo", "pwd"}


class Shell(FileCommands, TextCommands, SysCommands, NetworkCommands, DevCommands, TicketCommands):
    def __init__(self):
        self.fs = FS()
        self.cwd = self.oldpwd = HOME
        self.level, self.best, self.part, self.finished = 1, 1, 0, False
        self.running, self.status, self.tips = True, 0, True
        self.typed = []
        self.pipe_out = False      # True when stdout goes into a pipe or a file
        self.err_target = None     # list collecting errors when 2> is used
        self._failed, self._status = False, None
        self.reset_ticket_state()

    def reset_ticket_state(self):
        """State that every ticket starts fresh with."""
        self.env = {"HOME": HOME, "USER": USER, "SHELL": "/bin/bash", "LANG": "en_US.UTF-8",
                    "PATH": "/usr/local/bin:/usr/bin:/bin", "PWD": HOME, "HOSTNAME": HOST}
        self.procs, self.svc, self.listen, self.remote = default_procs(), {}, {}, {}
        self.pipeline_cmds = []
        self.venv, self.installed, self.flask_ran, self.flask_port = None, {}, False, None
        self.repo, self.mark, self.hint_stage, self.ran = None, {}, 0, set()

    # ------------------------------------------------------------ output
    def out(self, text):
        print(text, flush=True)

    def show_error(self, msg, tip=None):
        if msg:  # `false` fails silently, like real Linux
            self.out(c("31", msg))
        if tip and self.tips:
            self.out(c("90", "  tip: " + tip))

    def warn(self, msg, tip=None):
        """A non-fatal error: print it (or send it to 2>), keep the command running."""
        self._failed = True
        if self.err_target is not None:
            self.err_target.append(msg)
        else:
            self.show_error(msg, tip)

    def tip(self, text):
        """A learning tip that is not part of the command output."""
        if self.tips and not self.pipe_out:
            self.out(c("90", "  tip: " + text))

    def short_cwd(self):
        if self.cwd == HOME or self.cwd.startswith(HOME + "/"):
            return "~" + self.cwd[len(HOME):]
        return self.cwd

    def prompt(self):
        venv = f"({self.venv.rsplit('/', 1)[-1]}) " if self.venv else ""
        return venv + c("1;32", f"{USER}@{HOST}") + ":" + c("1;34", self.short_cwd()) + "$ "

    def width(self):
        return min(shutil.get_terminal_size((100, 30)).columns - 1, 110) if TTY else 100

    # ------------------------------------------------------------ helpers for commands
    def path(self, arg):
        return self.fs.norm(arg, self.cwd)

    def writable(self, p):
        return p == HOME or p.startswith(HOME + "/") or p.startswith("/tmp/") or p == "/dev/null"

    def suggest(self, arg):
        """If 'arg' exists with a different upper/lower case, return that spelling."""
        p = self.path(arg)
        folder, name = self.fs.parent(p), self.fs.base(p)
        if not self.fs.isdir(folder):
            return None
        for n, _ in self.fs.children(folder):
            if n.lower() == name.lower() and n != name:
                return arg[: len(arg) - len(name)] + n
        return None

    def missing_tip(self, arg, cmd):
        alt = self.suggest(arg)
        if alt:
            return f"Linux is case-sensitive: did you mean {cmd} {alt}?"
        return "check the name with ls (and tree for subfolders)"

    def opts(self, args, cmd, flags, with_value="", longs=()):
        """Parse short options like -la, -n 5, -n5. Returns ({flag: value}, positional)."""
        found, pos, i = {}, [], 0
        while i < len(args):
            a = args[i]
            if a == "--":
                pos += args[i + 1:]
                break
            if a.startswith("--"):
                if a in longs:
                    found[a] = True
                else:
                    raise ShellError(f"{cmd}: unrecognized option '{a}'\nTry '{cmd} --help' for more information.",
                                     2, tip=f"man {cmd} lists the options")
            elif a.startswith("-") and len(a) > 1:
                if a[1:].isdigit() and "n" in with_value:
                    found["n"] = a[1:]
                    i += 1
                    continue
                j = 1
                while j < len(a):
                    ch = a[j]
                    if ch in with_value:
                        if j + 1 < len(a):
                            found[ch] = a[j + 1:]
                        elif i + 1 < len(args):
                            found[ch] = args[i + 1]
                            i += 1
                        else:
                            raise ShellError(f"{cmd}: option requires an argument -- '{ch}'\n"
                                             f"Try '{cmd} --help' for more information.", 2,
                                             tip=f"man {cmd} shows how to use it")
                        break
                    if ch not in flags:
                        raise ShellError(f"{cmd}: invalid option -- '{ch}'\nTry '{cmd} --help' for more information.",
                                         2, tip=f"man {cmd} lists the options")
                    found[ch] = True
                    j += 1
            else:
                pos.append(a)
            i += 1
        return found, pos

    def read_text(self, name, cmd, msg="{cmd}: {name}: No such file or directory"):
        """Read a file or raise the real error. Used by cat, grep, sort ..."""
        if name == "-":
            return ""
        p = self.path(name)
        if self.fs.isdir(p):
            raise ShellError(f"{cmd}: {name}: Is a directory", 1, tip=f"{name} is a folder: use ls or cd on it")
        if not self.fs.isfile(p):
            raise ShellError(msg.format(cmd=cmd, name=name), 1, tip=self.missing_tip(name, cmd))
        if not self.fs.mode(p) & 0o400:
            raise ShellError(f"{cmd}: {name}: Permission denied", 1,
                             tip="the owner has no read (r) permission: see ls -l and man chmod")
        return self.fs.d[p]

    def gather(self, files, stdin, cmd, example, msg="{cmd}: {name}: No such file or directory"):
        """Text from files (missing ones are reported, the rest continue) or from stdin."""
        if not files:
            if stdin is None:
                raise ShellError(f"{cmd}: reading from the keyboard is not supported in this practice shell",
                                 1, tip=f"give a file or use a pipe, e.g. {example}")
            return stdin
        parts = []
        for f in files:
            try:
                parts.append(self.read_text(f, cmd, msg))
            except ShellError as e:
                self.warn(str(e), e.tip)
        return "\n".join(parts)

    # ------------------------------------------------------------ running a line
    def execute(self, line):
        line = line.strip()
        if not line:
            return
        self.typed.append(line)
        before = (self.level, self.part)
        self.run_line(line)
        if (self.level, self.part) == before:
            self.auto_check()
        if self.running:
            self.save()

    def run_line(self, line):
        """Run one command line: check the syntax of the whole line first (like bash),
        then run each part, expanding variables just before it runs."""
        try:
            parse(tokenize(line, self.env, self.status))
        except ShellError as e:
            self.show_error(str(e), e.tip)
            self.status = e.status
            return
        for connector, text in split_lists(line):
            if not text.strip():
                continue
            if (connector == "&&" and self.status != 0) or (connector == "||" and self.status == 0):
                continue
            try:
                lists = parse(tokenize(text, self.env, self.status))
            except ShellError as e:
                self.show_error(str(e), e.tip)
                self.status = e.status
                continue
            for _, pipeline in lists:
                self.status = self.run_pipeline(pipeline)
            if not self.running:
                break

    def expand(self, argv):
        """Glob expansion like bash: unquoted * ? [..] become matching names (if any)."""
        out = []
        for text, can_glob in argv:
            if can_glob and any(ch in text for ch in "*?["):
                out += self.fs.glob(text, self.cwd) or [text]
            else:
                out.append(text)
        return out

    def open_redirect(self, op, target):
        """Check (and for > truncate) a redirect target before the command runs."""
        p = self.path(target)
        if p == "/dev/null":
            return p
        if self.fs.isdir(p):
            raise ShellError(f"bash: {target}: Is a directory", 1)
        if not self.fs.isdir(self.fs.parent(p)):
            raise ShellError(f"bash: {target}: No such file or directory", 1,
                             tip="the folder for that file does not exist yet (see man mkdir)")
        if not self.writable(p):
            raise ShellError(f"bash: {target}: Permission denied", 1)
        if op in (">", "2>") or not self.fs.isfile(p):
            self.fs.write(p, "")
        return p

    def append_file(self, p, text):
        if p == "/dev/null" or text == "":
            return
        old = self.fs.d.get(p, "")
        self.fs.write(p, old + "\n" + text if old else text)

    def run_pipeline(self, pipeline):
        data, status = None, 0
        self.pipeline_cmds = [" ".join(a for a, _ in cmd["argv"]) for cmd in pipeline if cmd["argv"]]  # for ps
        for idx, cmd in enumerate(pipeline):
            last = idx == len(pipeline) - 1
            outs = [r for r in cmd["redirs"] if r[0] in (">", ">>")]
            errs = [r for r in cmd["redirs"] if r[0] in ("2>", "2>>")]
            self.pipe_out = not last or bool(outs)
            self.err_target = [] if errs else None
            self._failed, self._status = False, None
            stdin, result, out_path, err_path = (data if idx else None), "", None, None
            try:
                for op, target in cmd["redirs"]:
                    if op == "<":
                        stdin = self.read_text(target, "bash")
                    elif op in (">", ">>"):
                        out_path = self.open_redirect(op, target)
                    else:
                        err_path = self.open_redirect(op, target)
                result = self.dispatch(self.expand(cmd["argv"]), stdin) or ""
                status = self._status if self._status is not None else (1 if self._failed else 0)
            except ShellError as e:
                if self.err_target is not None:
                    self.err_target.append(str(e))
                else:
                    self.show_error(str(e), e.tip)
                status = e.status
            except Exception as e:  # crash safety: the shell must never die
                self.show_error(f"bash: internal error: {e}")
                status = 1
            if err_path:
                self.append_file(err_path, "\n".join(self.err_target))
            self.err_target = None
            if self.pipe_out:
                result = plain(result)
            if out_path:
                self.append_file(out_path, result)
                result = ""
            data = result
        self.pipe_out = False
        if data:
            self.out(data)
        return status

    def dispatch(self, argv, stdin):
        if not argv:
            return ""
        name, args = argv[0], argv[1:]
        if re.fullmatch(r"[A-Za-z_]\w*=.*", name):  # NAME=value
            k, _, v = name.partition("=")
            self.env[k] = v
            return self.dispatch(args, stdin) if args else ""
        if name in ALIASES:
            name, args = ALIASES[name][0], ALIASES[name][1:] + args
        if name == ".":
            name = "source"
        if "/" in name:
            return self.run_script(name, args)
        if args[:1] == ["--help"] and name in MAN:
            return self.man_page(name, short=True)
        fn = getattr(self, "cmd_" + name.replace("-", "_"), None) if (name in MAN or name in EXTRA) else None
        if fn is None:
            raise self.not_found(name)
        return fn(args, stdin)

    def not_found(self, name):
        low = name.lower()
        if name.startswith("cd.."):
            return ShellError(f"{name}: command not found", 127, tip="add a space: cd ..")
        if low in WINDOWS:
            return ShellError(f"{name}: command not found", 127,
                              tip=f"{name} is a Windows command. In Linux use: {WINDOWS[low]}")
        if low == "netstat":
            return ShellError("Command 'netstat' not found, but can be installed with:\n\nsudo apt install net-tools",
                              127, tip="modern Linux uses: ss -tlnp")
        if low == "ifconfig":
            return ShellError("Command 'ifconfig' not found, but can be installed with:\n\nsudo apt install net-tools",
                              127, tip="modern Linux uses: ip addr")
        if low != name and (low in MAN or low in ALIASES):
            return ShellError(f"{name}: command not found", 127,
                              tip=f"Linux is case-sensitive: commands are lowercase, try {low}")
        if self.fs.isfile(self.path(name)):
            return ShellError(f"{name}: command not found", 127,
                              tip="to run a script that is in this folder, put ./ in front of its name")
        return ShellError(f"{name}: command not found", 127, tip="type help to see the available commands")

    def run_script(self, name, args):
        p = self.path(name)
        if self.fs.isdir(p):
            raise ShellError(f"bash: {name}: Is a directory", 126)
        if not self.fs.isfile(p):
            raise ShellError(f"bash: {name}: No such file or directory", 127, tip="check the name with ls")
        if p not in self.fs.x:
            raise ShellError(f"bash: {name}: Permission denied", 126,
                             tip="the file has no execute (x) permission yet - see man chmod")
        captured, real_out, piped = [], self.out, self.pipe_out
        if piped:  # output goes to a pipe or a file: collect it instead of printing
            self.out = captured.append
        try:
            for line in self.fs.d[p].splitlines():
                if line.strip() and not line.strip().startswith("#"):
                    self.run_line(line)
        finally:
            self.out, self.pipe_out = real_out, piped
        self.ran.add(p)
        return "\n".join(captured)

    # ------------------------------------------------------------ main loop
    def banner(self):
        if TTY:
            sys.stdout.write("\x1b[3J\x1b[2J\x1b[H")  # clear screen and scrollback
        self.out("Welcome to LinuxIP 6.1 (GNU/Linux 6.8.0-corp x86_64) - Horizon dev box (simulated)")
        self.out("")
        self.out(f"  System information as of {NOW}")
        self.out("")
        self.out("  System load:  0.08               Users logged in:       1")
        self.out(f"  Usage of /:   41.2% of 62.67GB   IPv4 address for eth0: {MY_IP}")
        self.out(f"  Memory usage: 23%                Backlog:               {TOTAL} tickets")
        self.out("")
        self.out(c("90", "  Authorized use only. Practice environment: nothing here touches your real files."))
        self.out(c("90", "  help = all commands   man <cmd> = manual   hint = help with the ticket"))
        self.out("")
        self.out("Last login: Wed Nov 11 17:42:13 2026 from 10.20.30.5")

    def run(self):
        self.banner()
        if self.load():
            self.out(c("32", "Welcome back! Progress loaded"))
        self.start_level(self.level, self.part)
        if self.part:
            self.out(c("1;97", f"-> Continuing at step {self.part + 1}"))
        self.save()
        while self.running:
            if TTY:
                sys.stdout.write(f"\x1b]0;{USER}@{HOST}: {self.short_cwd()}\x07")
            try:
                line = input(self.prompt() if TTY else "")
            except KeyboardInterrupt:  # Ctrl+C cancels the line, like bash
                print("^C")
                self.status = 130
                continue
            except EOFError:           # Ctrl+D (Ctrl+Z Enter on Windows) logs out
                if TTY:
                    try:
                        time.sleep(0.1)  # on Windows Ctrl+C can arrive as EOF first
                    except KeyboardInterrupt:
                        print("^C")
                        continue
                print()
                break
            if not TTY:
                print(self.prompt() + line)
            self.execute(line)
        self.save(session_open=False)
        print("logout")


def main():
    if os.name == "nt":
        os.system("")  # enables ANSI colours in the Windows console
    else:
        try:
            import readline  # noqa: F401  (arrow-up history on Linux/macOS)
        except ImportError:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    shell = Shell()
    try:
        shell.run()
    except KeyboardInterrupt:
        shell.save(session_open=False)
        print("\nlogout")
