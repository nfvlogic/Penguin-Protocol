"""Developer tools: environment variables, python/venv, pip, flask and git."""
import difflib
import hashlib
import re

from .core import ShellError, c, parse_requirements


def ghash(msg):
    """Deterministic short commit hash (same message -> same hash)."""
    return hashlib.sha1(msg.encode("utf-8")).hexdigest()[:7]


class DevCommands:
    def cmd_true(self, args, stdin):
        return ""

    def cmd_false(self, args, stdin):
        raise ShellError("", 1)

    # ---------------------------------------------------------- environment variables
    def cmd_export(self, args, stdin):
        if not args or args == ["-p"]:
            return "\n".join(f'declare -x {k}="{v}"' for k, v in sorted(self.env.items()))
        for a in args:
            k, eq, v = a.partition("=")
            if not re.fullmatch(r"[A-Za-z_]\w*", k):
                self.warn(f"bash: export: `{a}': not a valid identifier",
                          "no spaces around =, e.g. export LOG_LEVEL=debug")
            elif eq:
                self.env[k] = v
            else:
                self.env.setdefault(k, "")

    def cmd_unset(self, args, stdin):
        for a in args:
            self.env.pop(a, None)

    def cmd_env(self, args, stdin):
        return "\n".join(f"{k}={v}" for k, v in sorted(self.env.items()))

    def cmd_printenv(self, args, stdin):
        if not args:
            return self.cmd_env(args, stdin)
        if args[0] not in self.env:
            self._status = 1
            return ""
        return self.env[args[0]]

    # ---------------------------------------------------------- python / venv / pip / flask
    def cmd_python3(self, args, stdin):
        if not args:
            raise ShellError("python3: the interactive >>> prompt is not available in this practice shell", 1,
                             tip="try python3 --version (see man python3)")
        if args[0] in ("--version", "-V"):
            return "Python 3.12.3"
        if args[0] == "-m" and len(args) > 1:
            mod, rest = args[1], args[2:]
            if mod == "venv":
                if not rest:
                    raise ShellError("usage: venv [-h] [--clear] ENV_DIR [ENV_DIR ...]\n"
                                     "venv: error: the following arguments are required: ENV_DIR", 2,
                                     tip="venv needs the name of the folder to create")
                root = self.path(rest[0])
                if not self.writable(root):
                    raise ShellError(f"Error: [Errno 13] Permission denied: '{rest[0]}'", 1)
                self.fs.mkdirs(root + "/lib/python3.12/site-packages")
                self.fs.mkdirs(root + "/bin")
                self.fs.write(root + "/bin/activate", "# This file must be used with \"source bin/activate\"")
                self.fs.write(root + "/pyvenv.cfg", "home = /usr/bin\nversion = 3.12.3")
                self.installed.setdefault(root, {})
                return ""
            if mod == "pip":
                return self.cmd_pip(rest, stdin)
            if mod == "flask":
                return self.cmd_flask(rest, stdin)
            raise ShellError(f"/usr/bin/python3: No module named {mod}", 1)
        if self.fs.isfile(self.path(args[0])):
            return ""  # scripts are not executed in this simulation
        raise ShellError(f"python3: can't open file '{self.path(args[0])}': [Errno 2] No such file or directory", 2)

    def cmd_python(self, args, stdin):
        if not self.venv:
            raise ShellError("Command 'python' not found, did you mean:\n"
                             "  command 'python3' from deb python3\n"
                             "  command 'python' from deb python-is-python3", 127,
                             tip="on Ubuntu the command is python3 (inside an active venv, python works too)")
        return self.cmd_python3(args, stdin)

    def cmd_source(self, args, stdin):
        if not args:
            raise ShellError("bash: source: filename argument required\nsource: usage: source filename [arguments]",
                             2, tip="source needs a file, e.g. a venv's bin/activate")
        p = self.path(args[0])
        if not self.fs.isfile(p):
            raise ShellError(f"bash: {args[0]}: No such file or directory", 1,
                             tip="check the path with ls -a (did you create the venv first?)")
        if p.endswith("/bin/activate"):
            self.venv = p[: -len("/bin/activate")]
            self.env["VIRTUAL_ENV"] = self.venv
            self.env["PATH"] = self.venv + "/bin:" + self.env.get("PATH", "")
            self.installed.setdefault(self.venv, {})
            return ""
        for line in self.fs.d[p].splitlines():
            if line.strip() and not line.strip().startswith("#"):
                self.run_line(line)

    def cmd_deactivate(self, args, stdin):
        if not self.venv:
            raise ShellError("deactivate: command not found", 127, tip="no virtual env is active")
        self.env["PATH"] = self.env.get("PATH", "").replace(self.venv + "/bin:", "")
        self.venv = None
        self.env.pop("VIRTUAL_ENV", None)

    def cmd_pip(self, args, stdin):
        if not self.venv:
            raise ShellError("error: externally-managed-environment\n\n"
                             "× This environment is externally managed\n"
                             "╰─> To install Python packages system-wide, try apt install\n"
                             "    python3-xyz, where xyz is the package you are trying to\n"
                             "    install.\n\n"
                             "    If you wish to install a non-Debian-packaged Python package,\n"
                             "    create a virtual environment using python3 -m venv path/to/venv.", 1,
                             tip="pip only works inside an active virtual env (see man python3 and man source)")
        pkgs = self.installed.setdefault(self.venv, {})
        if not args:
            return "\nUsage:\n  pip <command> [options]\n\nCommands:\n  install  list  freeze"
        sub, rest = args[0], args[1:]
        if sub == "install":
            new = {}
            if rest[:1] == ["-r"]:
                if len(rest) < 2:
                    raise ShellError("ERROR: -r option requires 1 argument.", 2)
                p = self.path(rest[1])
                if not self.fs.isfile(p):
                    raise ShellError(f"ERROR: Could not open requirements file: [Errno 2] No such file or directory: "
                                     f"'{rest[1]}'", 1, tip="run it from the folder that contains that file")
                new = parse_requirements(self.fs.d[p])
            else:
                for r in rest:
                    new.update(parse_requirements(r))
            if not new:
                raise ShellError("ERROR: You must give at least one requirement to install (see \"pip help install\")", 1)
            lines = [f"Collecting {n}" + (f"=={v}" if v != "latest" else "") for n, v in new.items()]
            lines.append("Installing collected packages: " + ", ".join(new))
            pkgs.update(new)
            return "\n".join(lines + ["Successfully installed " + " ".join(f"{n}-{v}" for n, v in new.items())])
        if sub == "freeze":
            return "\n".join(f"{n}=={v}" for n, v in sorted(pkgs.items()))
        if sub == "list":
            rows = ["Package          Version", "---------------- -------", "pip              24.0"]
            return "\n".join(rows + [f"{n:<16} {v}" for n, v in sorted(pkgs.items())])
        raise ShellError(f'ERROR: unknown command "{sub}"', 1, tip="this shell supports pip install, list and freeze")

    def cmd_flask(self, args, stdin):
        if not self.venv or "flask" not in self.installed.get(self.venv, {}):
            raise ShellError("flask: command not found", 127,
                             tip="Flask is installed inside a virtual env: activate it and install the requirements")
        if not args or args[0] == "--version":
            return "Python 3.12.3\nFlask 3.0.3\nWerkzeug 3.0.4"
        if args[0] != "run":
            raise ShellError(f"Usage: flask [OPTIONS] COMMAND [ARGS]...\nError: No such command '{args[0]}'.", 2)
        if not (self.fs.isfile(self.cwd + "/wsgi.py") or self.fs.isfile(self.cwd + "/app.py") or "FLASK_APP" in self.env):
            raise ShellError("Error: Could not locate a Flask application. Use the 'flask --app' option, 'FLASK_APP' "
                             "environment variable, or a 'wsgi.py' or 'app.py' file in the current directory.", 2,
                             tip="run it from the project folder (the one with wsgi.py)")
        cfg = {}
        if "python-dotenv" in self.installed[self.venv]:  # real Flask loads .flaskenv and .env automatically
            for name in (".flaskenv", ".env"):
                for line in self.fs.d.get(self.cwd + "/" + name, "").splitlines():
                    k, eq, v = line.partition("=")
                    if eq and not k.strip().startswith("#"):
                        cfg[k.strip()] = v.strip()
        cfg.update(self.env)
        head = " * Serving Flask app 'wsgi'\n * Debug mode: off\nTraceback (most recent call last):\n"
        for var in ("DB_HOST", "DB_NAME"):
            if not cfg.get(var):
                raise ShellError(head + '  File "/home/analyst/horizon/app/__init__.py", line 12, in create_app\n'
                                 f"    raise RuntimeError(\"{var} is not set\")\nRuntimeError: {var} is not set", 1,
                                 tip="environment variables are set with export NAME=value")
        if cfg["DB_HOST"] not in ("localhost", "127.0.0.1"):
            raise ShellError(head + f"sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (2003, "
                             f"\"Can't connect to MySQL server on '{cfg['DB_HOST']}'\")", 1,
                             tip="for local development the database runs on this machine")
        if cfg["DB_NAME"] != "horizon_dev":
            raise ShellError(head + "sqlalchemy.exc.OperationalError: (pymysql.err.OperationalError) (1049, "
                             f"\"Unknown database '{cfg['DB_NAME']}'\")", 1)
        port, i, rest = self.env.get("FLASK_RUN_PORT", "5000"), 0, args[1:]
        while i < len(rest):
            a = rest[i]
            if a in ("--port", "-p", "--host", "-h") and i + 1 < len(rest):
                if a in ("--port", "-p"):
                    port = rest[i + 1]
                i += 2
                continue
            if a.startswith("--port="):
                port = a.split("=", 1)[1]
            elif a not in ("--debug", "--reload", "--no-reload"):
                raise ShellError(f"Usage: flask run [OPTIONS]\nTry 'flask run --help' for help.\n\n"
                                 f"Error: No such option: {a}", 2, tip="see man flask")
            i += 1
        if not str(port).isdigit():
            raise ShellError(f"Error: Invalid value for '--port' / '-p': '{port}' is not a valid integer.", 2)
        pid = self.listen.get(int(port))
        if pid in self.procs:
            raise ShellError(" * Serving Flask app 'wsgi'\n * Debug mode: off\nAddress already in use\n"
                             f"Port {port} is in use by another program. Either identify and stop that program, "
                             "or start the server with a different port.", 1,
                             tip="find out who uses the port: ss -tlnp")
        self.flask_ran, self.flask_port = True, str(port)
        self.tip("a real server keeps running until Ctrl+C; here it stops at once so you can keep typing")
        return (" * Serving Flask app 'wsgi'\n * Debug mode: off\n"
                "WARNING: This is a development server. Do not use it in a production deployment.\n"
                f" * Running on http://127.0.0.1:{port}\nPress CTRL+C to quit")

    # ---------------------------------------------------------- git: internal model
    def git_init(self, root):
        self.repo = {"root": root, "branch": "main", "branches": {"main": []}, "index": {}}
        self.fs.mkdirs(root + "/.git")

    def git_head(self):
        commits = self.repo["branches"][self.repo["branch"]]
        return commits[-1] if commits else {"tree": {}, "msg": "", "hash": ""}

    def git_working(self):
        root, out = self.repo["root"] + "/", {}
        for k, v in self.fs.d.items():
            if k.startswith(root) and not k.endswith("/"):
                rel = k[len(root):]
                parts = rel.split("/")
                if parts[0] in (".git", ".venv") or "__pycache__" in parts:
                    continue
                out[rel] = v
        return out

    def git_staged(self):
        tree = dict(self.git_head()["tree"])
        for rel, v in self.repo["index"].items():
            if v is None:
                tree.pop(rel, None)
            else:
                tree[rel] = v
        return tree

    def git_clean(self):
        return self.git_staged() == self.git_head()["tree"] == self.git_working()

    def git_add(self, rels):
        work, staged = self.git_working(), self.git_staged()
        for rel in rels:
            matched = [r for r in set(work) | set(staged)
                       if rel in (".", "") or r == rel or r.startswith(rel.rstrip("/") + "/")]
            if not matched:
                raise ShellError(f"fatal: pathspec '{rel}' did not match any files", 128,
                                 tip="check the path with git status (paths are relative to where you are)")
            for r in matched:
                self.repo["index"][r] = work.get(r)

    def git_commit(self, msg):
        tree = self.git_staged()
        if tree == self.git_head()["tree"]:
            untracked = set(self.git_working()) - set(tree)
            changed = self.git_working() != tree
            text = (f"On branch {self.repo['branch']}\n" +
                    ("nothing added to commit but untracked files present (use \"git add\" to track)" if untracked else
                     "no changes added to commit (use \"git add\" and/or \"git commit -a\")" if changed else
                     "nothing to commit, working tree clean"))
            raise ShellError(text, 1, tip="changes must be staged with git add before a commit")
        h = ghash(msg)
        known = {cm["hash"] for b in self.repo["branches"].values() for cm in b}
        while h in known:
            h = ghash(msg + h)
        self.repo["branches"][self.repo["branch"]].append({"hash": h, "msg": msg, "tree": tree})
        self.repo["index"] = {}
        return h

    def git_commit_all(self, msg):
        self.git_add(["."])
        self.git_commit(msg)

    def git_switch(self, name, create=False):
        branches = self.repo["branches"]
        if create:
            if name in branches:
                raise ShellError(f"fatal: a branch named '{name}' already exists", 128,
                                 tip="to move to an existing branch use git switch NAME")
            branches[name] = list(branches[self.repo["branch"]])
            self.repo["branch"] = name
            return
        old = self.git_head()["tree"]
        new = branches[name][-1]["tree"] if branches[name] else {}
        if old != new:
            work = self.git_working()
            dirty = sorted(r for r in set(old) | set(self.git_staged())
                           if self.git_staged().get(r) != old.get(r) or work.get(r) != old.get(r))
            dirty = [r for r in dirty if old.get(r) != new.get(r)]
            if dirty:
                raise ShellError("error: Your local changes to the following files would be overwritten by checkout:\n" +
                                 "\n".join("\t" + r for r in dirty) +
                                 "\nPlease commit your changes or stash them before you switch branches.\nAborting",
                                 1, tip="commit the changes first, or undo them (see man git)")
            for rel in old:
                if rel not in new:
                    self.fs.d.pop(self.repo["root"] + "/" + rel, None)
            for rel, v in new.items():
                p = self.repo["root"] + "/" + rel
                self.fs.mkdirs(self.fs.parent(p))
                self.fs.write(p, v)
        self.repo["branch"] = name

    def git_rel(self, arg):
        p, root = self.path(arg), self.repo["root"]
        if p == root:
            return "."
        if not p.startswith(root + "/"):
            raise ShellError(f"fatal: {arg}: '{arg}' is outside repository at '{root}'", 128)
        return p[len(root) + 1:]

    def git_diff_text(self, a, b, only=None):
        out = []
        for rel in sorted(set(a) | set(b)):
            if (only and only != "." and rel != only and not rel.startswith(only.rstrip("/") + "/")) or a.get(rel) == b.get(rel):
                continue
            out += [c("1", f"diff --git a/{rel} b/{rel}"), c("1", "index 3f2a1b9..8c4d2e7 100644")]
            old, new = (a.get(rel) or "").splitlines(), (b.get(rel) or "").splitlines()
            for line in difflib.unified_diff(old, new, f"a/{rel}", f"b/{rel}", lineterm="", n=3):
                color = "1" if line[:3] in ("---", "+++") else {"+": "32", "-": "31", "@": "36"}.get(line[:1], "")
                out.append(c(color, line) if color else line)
        return "\n".join(out)

    # ---------------------------------------------------------- git: commands
    def cmd_git(self, args, stdin):
        if not args:
            return ("usage: git [--version] [--help] <command> [<args>]\n\n"
                    "   status  log  diff  branch  checkout  switch  add  commit  restore  init")
        sub, rest = args[0], args[1:]
        if sub == "--version":
            return "git version 2.43.0"
        if sub in ("push", "pull", "fetch"):
            raise ShellError("fatal: No configured push destination." if sub == "push" else
                             "fatal: 'origin' does not appear to be a git repository", 128,
                             tip="this practice repo has no remote; at work it goes to Azure DevOps")
        if sub == "init":
            if self.repo and (self.cwd + "/").startswith(self.repo["root"] + "/"):
                return f"Reinitialized existing Git repository in {self.repo['root']}/.git/"
            self.git_init(self.cwd)
            return f"Initialized empty Git repository in {self.cwd}/.git/"
        known = ("status", "log", "diff", "branch", "checkout", "switch", "add", "commit", "restore", "show")
        if sub not in known:
            raise ShellError(f"git: '{sub}' is not a git command. See 'git --help'.", 1,
                             tip="supported here: " + " ".join(known))
        if not self.repo or not (self.cwd + "/").startswith(self.repo["root"] + "/"):
            raise ShellError("fatal: not a git repository (or any of the parent directories): .git", 128,
                             tip="git only works inside a repository: go into the project folder first")
        return getattr(self, "git_cmd_" + sub)(rest)

    def git_cmd_status(self, rest):
        r = self.repo
        head, staged, work = self.git_head()["tree"], self.git_staged(), self.git_working()

        def kind(a, b, rel):
            return "new file" if rel not in a else ("deleted" if rel not in b else "modified")
        st = [f"\t{kind(head, staged, x) + ':':<12}{x}" for x in sorted(set(head) | set(staged)) if head.get(x) != staged.get(x)]
        un = [f"\t{kind(staged, work, x) + ':':<12}{x}" for x in sorted(staged) if staged.get(x) != work.get(x)]
        ut = [f"\t{x}" for x in sorted(set(work) - set(staged))]
        if "-s" in rest or "--short" in rest:
            return "\n".join([c("32", "A" if x.strip().startswith("new") else "M") + "  " + x.split(":", 1)[1].strip() for x in st] +
                             [" " + c("31", "M") + " " + x.split(":", 1)[1].strip() for x in un] +
                             [c("31", "??") + " " + x.strip() for x in ut])
        lines = [f"On branch {r['branch']}"]
        if st:
            lines += ["Changes to be committed:", '  (use "git restore --staged <file>..." to unstage)']
            lines += [c("32", x) for x in st] + [""]
        if un:
            lines += ["Changes not staged for commit:", '  (use "git add <file>..." to update what will be committed)',
                      '  (use "git restore <file>..." to discard changes in working directory)']
            lines += [c("31", x) for x in un] + [""]
        if ut:
            lines += ["Untracked files:", '  (use "git add <file>..." to include in what will be committed)']
            lines += [c("31", x) for x in ut] + [""]
        if not (st or un or ut):
            lines.append("nothing to commit, working tree clean")
        elif not st:
            lines.append('no changes added to commit (use "git add" and/or "git commit -a")' if un else
                         'nothing added to commit but untracked files present (use "git add" to track)')
        return "\n".join(lines).rstrip()

    def git_cmd_log(self, rest):
        o, _ = self.opts([a for a in rest if a not in ("--oneline", "--graph", "--all")], "git log", "", with_value="n")
        n = str(o.get("n", "999"))
        commits = list(reversed(self.repo["branches"][self.repo["branch"]]))[: int(n) if n.isdigit() else 999]
        if not commits:
            raise ShellError(f"fatal: your current branch '{self.repo['branch']}' does not have any commits yet", 128)
        if "--oneline" in rest:
            return "\n".join(c("33", cm["hash"]) + (c("36", f" (HEAD -> {self.repo['branch']})") if k == 0 else "") +
                             " " + cm["msg"] for k, cm in enumerate(commits))
        return "\n\n".join(c("33", f"commit {cm['hash']}{'d41c9e07b2' * 3}"[:47]) + "\nAuthor: Horizon Dev <dev@corp.local>\n"
                           "Date:   Thu Nov 12 09:00:00 2026 +0100\n\n    " + cm["msg"] for cm in commits)

    def git_cmd_branch(self, rest):
        names = [a for a in rest if not a.startswith("-")]
        if names:
            if names[0] in self.repo["branches"]:
                raise ShellError(f"fatal: a branch named '{names[0]}' already exists", 128)
            self.repo["branches"][names[0]] = list(self.repo["branches"][self.repo["branch"]])
            return ""
        return "\n".join(c("32", f"* {b}") if b == self.repo["branch"] else f"  {b}" for b in sorted(self.repo["branches"]))

    def git_cmd_checkout(self, rest):
        if not rest:
            raise ShellError("fatal: you must specify path(s) to restore", 128, tip="see man git")
        if rest[0] == "-b":
            if len(rest) < 2:
                raise ShellError("error: switch `b' requires a value", 129, tip="-b needs the name of the new branch")
            self.git_switch(rest[1], create=True)
            return f"Switched to a new branch '{rest[1]}'"
        if rest[0] in self.repo["branches"]:
            self.git_switch(rest[0])
            return f"Switched to branch '{rest[0]}'"
        files = [a for a in rest if a != "--"]
        if all(self.git_rel(f) in self.git_staged() for f in files):
            return self.git_cmd_restore(files)
        raise ShellError(f"error: pathspec '{rest[0]}' did not match any file(s) known to git", 1,
                         tip="to create a new branch use checkout -b")

    def git_cmd_switch(self, rest):
        if not rest:
            raise ShellError("fatal: missing branch or commit argument", 128, tip="see git branch for the names")
        if rest[0] in ("-c", "--create"):
            if len(rest) < 2:
                raise ShellError("error: switch `c' requires a value", 129)
            self.git_switch(rest[1], create=True)
            return f"Switched to a new branch '{rest[1]}'"
        if rest[0] not in self.repo["branches"]:
            raise ShellError(f"fatal: invalid reference: {rest[0]}", 128, tip="to create a branch use switch -c")
        self.git_switch(rest[0])
        return f"Switched to branch '{rest[0]}'"

    def git_cmd_add(self, rest):
        paths = [a for a in rest if not a.startswith("-")]
        if "-A" in rest or "--all" in rest:
            paths = paths or ["."]
        if not paths:
            raise ShellError("Nothing specified, nothing added.\nhint: Maybe you wanted to say 'git add .'?", 0,
                             tip="git add needs the file(s) to stage")
        self.git_add([self.git_rel(p) for p in paths])
        return ""

    def git_cmd_commit(self, rest):
        msg = None
        for k, a in enumerate(rest):
            if a in ("-m", "-am") and k + 1 < len(rest):
                msg = rest[k + 1]
            if a in ("-a", "-am"):
                self.git_add([x for x in self.git_staged()])
        if msg is None:
            raise ShellError("Aborting commit due to empty commit message.", 1,
                             tip='without -m git opens an editor; give the message with -m "..."')
        h = self.git_commit(msg)
        return f"[{self.repo['branch']} {h}] {msg}"

    def git_cmd_diff(self, rest):
        files = [self.git_rel(a) for a in rest if not a.startswith("-")]
        only = files[0] if files else None
        if "--staged" in rest or "--cached" in rest:
            return self.git_diff_text(self.git_head()["tree"], self.git_staged(), only)
        staged, work = self.git_staged(), self.git_working()
        return self.git_diff_text(staged, {k: v for k, v in work.items() if k in staged}, only)

    def git_cmd_restore(self, rest):
        paths = [a for a in rest if not a.startswith("-")]
        if not paths:
            raise ShellError("fatal: you must specify path(s) to restore", 128, tip="restore needs the file(s) to undo")
        for p in paths:
            rel = self.git_rel(p)
            if "--staged" in rest:
                self.repo["index"].pop(rel, None)
                continue
            staged = self.git_staged()
            if rel not in staged:
                raise ShellError(f"error: pathspec '{p}' did not match any file(s) known to git", 1)
            full = self.repo["root"] + "/" + rel
            self.fs.mkdirs(self.fs.parent(full))
            self.fs.write(full, staged[rel])
        return ""

    def git_cmd_show(self, rest):
        head = self.git_head()
        if not head["hash"]:
            raise ShellError("fatal: your current branch does not have any commits yet", 128)
        commits = self.repo["branches"][self.repo["branch"]]
        prev = commits[-2]["tree"] if len(commits) > 1 else {}
        return (c("33", f"commit {head['hash']}") + "\nAuthor: Horizon Dev <dev@corp.local>\n\n    " + head["msg"] +
                "\n\n" + self.git_diff_text(prev, head["tree"]))
