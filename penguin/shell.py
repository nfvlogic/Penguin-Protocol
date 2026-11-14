"""The shell itself: runs command lines like bash and drives the main loop."""
import os
import random
import re
import shutil
import sys
import time

from .pip import say
from .cmd_dev import DevCommands
from .cmd_shell import ShellCommands
from .compound import CompoundCommands, needs_more
from .cmd_files import FileCommands
from .cmd_network import NetworkCommands
from .cmd_text import TextCommands
from .cmd_sys import SysCommands, default_procs
from .cmd_tickets import TicketCommands
from .core import HOME, HOST, MY_IP, NOW, TTY, USER, VERSION, ShellError, c, plain
from .manual import MAN
from .parser import parse, scan, split_lists, tokenize
from .tickets import TOTAL
from .variants import levels_for
from .vfs import FS

ALIASES = {"ll": ["ls", "-alF"], "la": ["ls", "-A"], "l": ["ls", "-CF"],
           "levels": ["tasks"], "logout": ["exit"], "pip3": ["pip"]}
# Commands that exist on a real system but are not part of MAN (handled with a real message).
EXTRA = {"apt", "apt-get", "printenv", "whatis", "nano", "vim", "vi", "code"}
WINDOWS = {"cls": "clear", "ipconfig": "ip addr", "del": "rm", "copy": "cp", "move": "mv",
           "ren": "mv", "md": "mkdir -p", "findstr": "grep", "tasklist": "ps", "rd": "rm -r",
           "systeminfo": "uname -a", "where": "which"}
BUILTINS = {"cd", "export", "unset", "source", "history", "type", "exit", "help", "echo", "pwd", "printf", "alias",
            "unalias", "read", "let", "test", "[", "[[", "break", "continue", "umask", "pushd", "popd", "dirs"}


class Shell(ShellCommands, CompoundCommands, FileCommands, TextCommands, SysCommands, NetworkCommands, DevCommands,
            TicketCommands):
    def __init__(self):
        self.fs = FS()
        self.cwd = self.oldpwd = HOME
        self.level, self.best, self.part, self.finished = 1, 1, 0, False
        env_seed = os.environ.get("PENGUIN_SEED")           # a fixed seed (tests); otherwise every new game is different
        self.seed = int(env_seed) if env_seed is not None else random.randrange(1, 10 ** 9)
        self.levels = levels_for(self.seed)
        self.expert = False                                  # New Game+: cards without the command list, no tips
        self.plus_unlocked = False                           # becomes True when the game has been beaten
        self.running, self.status, self.tips = True, 0, True
        self.typed = []
        self.firsts = set()        # big ideas Pip has already celebrated this game
        self.pipe_out = False      # True when stdout goes into a pipe or a file
        self.err_target = None     # list collecting errors when 2> is used
        self._failed, self._status = False, None
        self.reset_ticket_state()

    def reset_ticket_state(self):
        """State that every ticket starts fresh with."""
        self.env = {"HOME": HOME, "USER": USER, "SHELL": "/bin/bash", "LANG": "en_US.UTF-8",
                    "PATH": "/usr/local/bin:/usr/bin:/bin", "PWD": HOME, "HOSTNAME": HOST}
        self.procs, self.svc, self.listen, self.remote = default_procs(), {}, {}, {}
        self.pipeline_cmds, self.capture_stack, self.aliases = [], [], dict(ALIASES)
        self.heredoc, self.dirstack = None, []
        self.hostname, self.sessions, self.merging = HOST, [], False
        self.venv, self.installed, self.flask_ran, self.flask_port = None, {}, False, None
        self.repo, self.mark, self.hint_stage, self.ran = None, {}, 0, set()
        self.coach_last = -1                                 # first-mission coaching: which nudge was shown last
        self.checks_done = None                              # which "closes by itself" requirements are already met

    # ------------------------------------------------------------ output
    def out(self, text):
        """Standard output: printed, or collected while a $(...) is being captured."""
        if self.capture_stack:
            self.capture_stack[-1].append(plain(text))
        else:
            print(text, flush=True)

    def show_error(self, msg, tip=None):
        """Error messages go to the screen even inside $(...), like stderr does."""
        if self.merging and self.capture_stack:     # 2>&1 around a script: errors stay in order with its output
            if msg:
                self.out(msg)
            return
        if msg:  # `false` fails silently, like real Linux
            print(c("31", msg), flush=True)
        if tip and self.tips:
            print(c("90", "  tip: " + tip), flush=True)

    def warn(self, msg, tip=None):
        """A non-fatal error: print it (or send it to 2>), keep the command running."""
        self._failed = True
        if self.err_target is not None:
            self.err_target.append(msg)
        else:
            self.show_error(msg, tip)

    def tip(self, text):
        """A learning tip that is not part of the command output."""
        if self.tips and not self.pipe_out and not self.capture_stack:
            print(c("90", "  tip: " + text), flush=True)

    def short_cwd(self):
        if self.cwd == HOME or self.cwd.startswith(HOME + "/"):
            return "~" + self.cwd[len(HOME):]
        return self.cwd

    def prompt(self):
        venv = f"({self.venv.rsplit('/', 1)[-1]}) " if self.venv else ""
        return venv + c("1;32", f"{USER}@{self.hostname}") + ":" + c("1;34", self.short_cwd()) + "$ "

    def width(self):
        return min(shutil.get_terminal_size((100, 30)).columns - 1, 110) if TTY else 100

    # ------------------------------------------------------------ helpers for commands
    def path(self, arg, follow=True):
        """Absolute path of a typed name. Symbolic links are followed unless follow=False
        (rm, mv, ln and readlink work on the link itself)."""
        p = self.fs.norm(arg, self.cwd)
        return self.fs.follow(p) if follow and self.fs.links else p

    def writable(self, p):
        return p == HOME or p.startswith(HOME + "/") or p.startswith("/tmp/") or p == "/dev/null"

    def access(self, p, bit):
        """May the current user r(4) w(2) or x(1) this path? Your own files use the owner bits,
        files of root (everything outside your home and /tmp) use the 'others' bits."""
        mode = self.fs.mode(self.fs.follow(p))
        mine = self.writable(p) or p == HOME
        return bool((mode >> 6 if mine else mode) & bit)

    def read_keyboard(self, cmd="cat"):
        """A command with no file and no pipe reads what you type, until Ctrl+D (like real Linux)."""
        if self.tips and TTY:
            print(c("90", f"  tip: {cmd} is waiting for you to type. Press Ctrl+D on an empty line to finish (Ctrl+C cancels)"),
                  flush=True)
        lines = []
        while True:
            try:
                lines.append(input())
            except EOFError:
                break
        return "\n".join(lines)

    def read_heredoc(self, line):
        """cat <<EOF ... EOF : read the lines up to the delimiter. Returns (text, expand_variables)."""
        m = re.search(r"<<(-?)\s*(['\"]?)([A-Za-z_]\w*)\2", line)
        if not m:
            return None
        strip_tabs, quoted, delim = bool(m.group(1)), bool(m.group(2)), m.group(3)
        body = []
        while True:
            try:
                more = input("> " if TTY else "")
            except (EOFError, KeyboardInterrupt):
                print(f"bash: warning: here-document delimited by end-of-file (wanted `{delim}')")
                break
            if not TTY:
                print("> " + more)
            if (more.lstrip("\t") if strip_tabs else more) == delim:
                break
            body.append(more.lstrip("\t") if strip_tabs else more)
        return "\n".join(body), not quoted

    def heredoc_text(self):
        text, expand = self.heredoc or ("", False)
        if expand:
            from .parser import tokenize
            safe = '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
            toks = tokenize(safe, self.env, self.status, self)
            return toks[0][1] if toks else ""
        return text

    def can_write(self, p):
        """May the owner write p? (a file with no w bit is read-only, like after chmod 444)"""
        return self.writable(p) and (not self.fs.exists(p) or self.access(p, 2))

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
        if not self.access(p, 4):
            raise ShellError(f"{cmd}: {name}: Permission denied", 1,
                             tip="you have no read (r) permission: see ls -l and man chmod"
                             if self.writable(p) else "this file belongs to root: normal users cannot read it (sudo is not available here)")
        return self.fs.d[p]

    def gather(self, files, stdin, cmd, example, msg="{cmd}: {name}: No such file or directory"):
        """Text from files (missing ones are reported, the rest continue) or from stdin."""
        if not files:
            return stdin if stdin is not None else self.read_keyboard(cmd)
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
            self.celebrate(line)
            self.auto_check()
            self.coach()
        if self.running:
            self.save()

    def run_simple(self, line):
        """Run one command line (no loops): check the syntax of the whole line first (like bash),
        then run each part, expanding variables and $(...) just before it runs."""
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
                lists = parse(tokenize(text, self.env, self.status, self))
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
        if not self.can_write(p):
            raise ShellError(f"bash: {target}: Permission denied", 1,
                             tip="the file is read-only: see ls -l and man chmod" if self.writable(p) else None)
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
            redirs = []
            for op, target in cmd["redirs"]:      # &> FILE means  > FILE 2>&1
                redirs += [(">" if op == "&>" else ">>", target), ("2>&1", None)] if op in ("&>", "&>>") else [(op, target)]
            outer_err, outer_merging = self.err_target, self.merging
            merge = any(op == "2>&1" for op, _ in redirs)
            to_stderr = any(op in ("1>&2", ">&2") for op, _ in redirs)
            outs = [r for r in redirs if r[0] in (">", ">>")]
            errs = [r for r in redirs if r[0] in ("2>", "2>>")]
            self.pipe_out = not last or bool(outs) or bool(self.capture_stack) or merge
            own_err = [] if (errs or (merge and not self.capture_stack_will_exist(cmd))) else None
            self.err_target = own_err if own_err is not None else outer_err
            self.merging = merge or (outer_merging and not errs)
            self._failed, self._status = False, None
            stdin, result, out_path, err_path = (data if idx else None), "", None, None
            try:
                for op, target in redirs:
                    if op == "<":
                        stdin = self.read_text(target, "bash")
                    elif op == "<<":
                        stdin = self.heredoc_text()
                    elif op in (">", ">>"):
                        out_path = self.open_redirect(op, target)
                    elif op in ("2>", "2>>"):
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
            if merge and own_err:              # 2>&1: the error messages join the normal output
                result = "\n".join(own_err + ([result] if result else []))
            elif err_path:
                self.append_file(err_path, "\n".join(own_err))
            self.err_target, self.merging = outer_err, outer_merging
            if to_stderr and result:           # >&2: the output goes where error messages go
                print(c("31", result) if not self.capture_stack else result, flush=True)
                result = ""
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

    def capture_stack_will_exist(self, cmd):
        """True when the command is a script: its output is collected, so merged errors are written in order."""
        name = cmd["argv"][0][0] if cmd["argv"] else ""
        return "/" in name and not name.startswith("/usr/bin/")

    def dispatch(self, argv, stdin):
        if not argv:
            return ""
        if self.sessions and self.sessions[-1].get("canned"):       # inside an ssh session: server-specific answers
            canned = self.sessions[-1]["canned"]
            if " ".join(argv) in canned:
                return canned[" ".join(argv)]
        name, args = argv[0], argv[1:]
        if re.fullmatch(r"[A-Za-z_]\w*=.*", name):  # NAME=value
            k, _, v = name.partition("=")
            self.env[k] = v
            return self.dispatch(args, stdin) if args else ""
        if name in self.aliases and self.aliases[name]:
            name, args = self.aliases[name][0], self.aliases[name][1:] + args
        if name == ".":
            name = "source"
        if "/" in name:
            base = self.fs.follow(self.path(name, follow=False))
            if base.startswith("/usr/bin/") and self.fs.base(base) in MAN:   # /usr/bin/ls works like ls
                return self.dispatch([self.fs.base(base)] + args, stdin)
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
        keys = ["0", "#", "@", "*"] + [str(k) for k in range(1, 10)]
        saved = {k: self.env.get(k) for k in keys}
        self.env.update({"0": name, "#": str(len(args)), "@": " ".join(args), "*": " ".join(args)})
        for k, a in enumerate(args[:9], 1):
            self.env[str(k)] = a
        for k in range(len(args) + 1, 10):
            self.env.pop(str(k), None)
        captured = []
        piped = self.pipe_out
        if piped:  # output goes to a pipe or a file: collect it instead of printing
            self.capture_stack.append(captured)
        try:
            self.run_line(self.fs.d[p])
        finally:
            if piped:
                self.capture_stack.pop()
            self.pipe_out = piped
            for k, v in saved.items():
                if v is None:
                    self.env.pop(k, None)
                else:
                    self.env[k] = v
        self.ran.add(p)
        return "\n".join(captured)

    # ------------------------------------------------------------ tab completion
    def completions(self, buffer, text):
        """Candidates for Tab: command names in the first position, otherwise files and folders."""
        before = buffer[:len(buffer) - len(text)]
        stripped = before.rstrip()
        first = not stripped or stripped.endswith((";", "|", "&&", "||", "(", "then", "do", "else"))
        if first and "/" not in text:
            names = set(MAN) | EXTRA | set(self.aliases) | BUILTINS | {"if", "for", "while", "until"}
            names -= {"levels", "logout", "pip3"}
            return sorted(n for n in names if n.startswith(text))
        folder, _, base = text.rpartition("/")
        shown_dir = folder + "/" if "/" in text else ""
        base_dir = self.path(folder or "/") if "/" in text else self.cwd
        if not self.fs.isdir(base_dir):
            return []
        out = []
        for name, is_dir in self.fs.children(base_dir):
            if name.startswith(base) and (base.startswith(".") or not name.startswith(".")):
                out.append(shown_dir + name + ("/" if is_dir else ""))
        return out

    def setup_completion(self):
        try:
            import readline
        except ImportError:
            return  # Windows has no readline: Tab simply does not complete there
        matches = []

        def completer(text, state):
            if state == 0:
                matches[:] = self.completions(readline.get_line_buffer(), text)
            return (matches[state] + ("" if matches[state].endswith("/") else " ")) if state < len(matches) else None
        readline.set_completer_delims(" \t\n;|&<>=")
        readline.set_completer(completer)
        if "libedit" in (readline.__doc__ or ""):   # macOS
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

    # ------------------------------------------------------------ main loop
    def banner(self):
        if TTY:
            sys.stdout.write("\x1b[3J\x1b[2J\x1b[H")  # clear screen and scrollback
        if self.width() < 70:      # a phone: skip the system-information block so the first mission is on screen
            self.out(f"Welcome to Penguin Protocol {VERSION} (Atlas dev box, simulated)")
            self.out("")
            self.out(c("1;33", "  UPLINK OPEN") + c("33", "  Cover: contractor 'analyst', badge 4821. You are inside Atlas."))
            self.out(c("33", "  Stay quiet. Leave no trace. Control is listening."))
            self.out(c("90", "  help = all commands   man <cmd> = manual   hint = help with the mission"))
            self.out(self.pip_hello())
            return
        self.out(f"Welcome to Penguin Protocol {VERSION} (GNU/Linux 6.8.0-corp x86_64) - Atlas dev box (simulated)")
        self.out("")
        self.out(f"  System information as of {NOW}")
        self.out("")
        self.out("  System load:  0.08               Users logged in:       1")
        self.out(f"  Usage of /:   41.2% of 62.67GB   IPv4 address for eth0: {MY_IP}")
        self.out(f"  Memory usage: 23%                Open files:            {TOTAL} targets")
        self.out("")
        self.out(c("90", "  Authorized use only. Practice environment: nothing here touches your real files."))
        self.out(c("90", "  help = all commands   man <cmd> = manual   hint = help with the mission"))
        self.out("")
        self.out("Last login: Wed Nov 11 17:42:13 2026 from 10.20.30.5")
        self.out("")
        self.out(c("1;33", "  UPLINK OPEN") + c("33", "  Cover: contractor 'analyst', badge 4821. You are inside Atlas."))
        self.out(c("33", "  Stay quiet. Leave no trace. Control is listening."))
        self.out(self.pip_hello())

    def pip_hello(self):
        """Pip waves hello under the uplink message."""
        return say("wave", [("33", "Agent Pip, reporting in."), ("90", "I'll be in your ear the whole way.")], self.width())

    def start(self):
        """Everything before the first prompt: banner, load the save, show the first ticket."""
        self._buf, self._here = None, None      # unfinished multi-line command / open here-document
        self.banner()
        if getattr(self, "fresh", False):
            pass                                            # --new: ignore the saved game
        elif self.load():
            self.out(c("32", "Welcome back! Progress loaded"))
        if getattr(self, "start_expert", False):
            if self.plus_unlocked:                  # --plus: a fresh New Game+
                self.seed = random.randrange(1, 10 ** 9) if "PENGUIN_SEED" not in os.environ else self.seed
                self.levels = levels_for(self.seed)
                self.best, self.finished, self.level, self.part = 1, False, 1, 0
                self.expert, self.tips = True, False
            else:
                self.out(c("33", f"New Game+ is locked: finish all {TOTAL} tickets first (or use  newgame +  with its password)."))
        self.start_level(self.level, self.part)
        if self.part:
            self.out(c("1;97", f"-> Continuing at step {self.part + 1}"))
        self.save()
        return self.prompt()

    def feed(self, line):
        """Handle ONE typed line and return the next prompt: the normal prompt, or '> ' while a quote,
        loop, pipe, backslash or here-document is still open. The terminal and the web page both use this."""
        if getattr(self, "_here", None) is not None:       # inside  cat <<EOF  ...  EOF
            h = self._here
            text = line.lstrip("\t") if h["strip"] else line
            if text == h["delim"]:
                self._here = None
                self.heredoc = ("\n".join(h["body"]), not h["quoted"])
                self.execute(h["line"])
                return self.prompt()
            h["body"].append(text)
            return "> "
        if getattr(self, "_buf", None) is not None:        # continuation of an unfinished command
            line = self._buf[:-1] + line if self._buf.endswith("\\") else self._buf + "\n" + line
            self._buf = None
        elif "!!" in line and self.typed:  # history expansion: !! = the previous command
            line = line.replace("!!", self.typed[-1])
            print(line)
        if needs_more(line):         # unfinished quote, loop or pipe: bash shows the > prompt
            self._buf = line
            return "> "
        m = re.search(r"<<(-?)\s*(['\"]?)([A-Za-z_]\w*)\2", line) if "<<" in line else None
        if m:
            self._here = {"strip": bool(m.group(1)), "quoted": bool(m.group(2)), "delim": m.group(3),
                          "body": [], "line": line}
            return "> "
        self.heredoc = None
        self.execute(line)
        return self.prompt()

    def interrupt(self):
        """Ctrl+C: cancel the line being typed (and any unfinished command), like bash."""
        print("^C")
        self._buf = self._here = None
        self.status = 130
        return self.prompt()

    def eof(self):
        """Ctrl+D. Returns the next prompt, or None when the shell logs out."""
        if getattr(self, "_here", None) is not None:
            h = self._here
            print(f"bash: warning: here-document delimited by end-of-file (wanted `{h['delim']}')")
            self._here = None
            self.heredoc = ("\n".join(h["body"]), not h["quoted"])
            self.execute(h["line"])
            return self.prompt()
        if getattr(self, "_buf", None) is not None:
            quote = [q for _, _, q, _ in scan(self._buf + " ")][-1]
            if quote in ("'", '"'):
                self.show_error(f"bash: unexpected EOF while looking for matching `{quote}'")
            self.show_error("bash: syntax error: unexpected end of file")
            self._buf = None
            self.running = False
            return None
        if self.sessions:
            print()
            print(self.leave_session())
            return self.prompt()
        print()
        self.running = False
        return None

    def run(self):
        if TTY:
            self.setup_completion()
        prompt = self.start()
        while self.running:
            if TTY:
                sys.stdout.write(f"\x1b]0;{USER}@{self.hostname}: {self.short_cwd()}\x07")
            try:
                line = input(prompt if TTY else "")
            except KeyboardInterrupt:  # Ctrl+C cancels the line, like bash
                prompt = self.interrupt()
                continue
            except EOFError:           # Ctrl+D (Ctrl+Z Enter on Windows) logs out
                if TTY and not self.sessions and self._buf is None and self._here is None:
                    try:
                        time.sleep(0.1)  # on Windows Ctrl+C can arrive as EOF first
                    except KeyboardInterrupt:
                        print("^C")
                        continue
                prompt = self.eof()
                continue
            if not TTY:
                print(prompt + line)
            prompt = self.feed(line)
        self.save(session_open=False)
        print("logout")


USAGE = """Penguin Protocol - learn Linux with realistic tickets.

Usage: penguin.py [OPTIONS]

Options:
  --new          start a new game (new answers); your old save is replaced when you play
  --plus         start New Game+ (only after you beat the game): new answers, no command lists, no tips
  --seed N       use answer set N (the same N always gives the same answers)
  --save FILE    use another save file
  --version      show the version
  -h, --help     show this help

Inside the game: help, man COMMAND, hint, check, submit ANSWER, tasks, level N, newgame."""


def parse_args(argv):
    """Handle the command line options. Returns a dict of what to do."""
    opts, i = {"new": False, "expert": False}, 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            print(USAGE)
            sys.exit(0)
        elif a == "--version":
            print(f"Penguin Protocol {VERSION}")
            sys.exit(0)
        elif a == "--new":
            opts["new"] = True
        elif a in ("--plus", "--expert"):
            opts["expert"] = True
        elif a in ("--seed", "--save") and i + 1 < len(argv):
            if a == "--seed":
                if not argv[i + 1].lstrip("-").isdigit():
                    print(f"penguin: --seed needs a number, not '{argv[i + 1]}'", file=sys.stderr)
                    sys.exit(2)
                os.environ["PENGUIN_SEED"] = argv[i + 1]
            else:
                os.environ["PENGUIN_SAVE"] = argv[i + 1]
            i += 1
        else:
            print(f"penguin: unknown option '{a}'\nTry 'penguin.py --help' for more information.", file=sys.stderr)
            sys.exit(2)
        i += 1
    return opts


def main(argv=None):
    opts = parse_args(sys.argv[1:] if argv is None else argv)
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
    shell.fresh, shell.start_expert = opts["new"], opts["expert"]
    try:
        shell.run()
    except KeyboardInterrupt:
        shell.save(session_open=False)
        print("\nlogout")
