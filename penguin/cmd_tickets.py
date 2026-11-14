"""Ticket system and practice commands: cards, submit, check, hint, tasks, save/load, help, man."""
import getpass
import json
import os
import random
import re
import sys
import textwrap

from .clearance import code_for, is_plus_code, level_from_code, plus_code
from .core import HOME, LEGACY_SAVE, SAVE_FILE, TTY, ShellError, c, vlen
from .manual import DESCRIPTION, EXAMPLES, EXIT_STATUS, HELP, MAN, SEE_ALSO
from .tickets import LEVELS, NUDGES, TOTAL
from .variants import levels_for

PRIO_COLOR = {"Critical": "1;31", "High": "33", "Normal": "36"}


class TicketCommands:
    # ---------------------------------------------------------- ticket lifecycle
    def ticket(self):
        return self.levels[self.level - 1]

    def start_level(self, n, part=0):
        self.level, self.cwd, self.oldpwd, self.part = n, HOME, HOME, part
        self.fs.reset()
        self.reset_ticket_state()
        lv = self.ticket()
        for rel, text in lv["files"].items():
            path = HOME + "/" + rel.rstrip("/")
            if rel.endswith("/"):
                self.fs.mkdirs(path)
            else:
                self.fs.mkdirs(self.fs.parent(path))
                self.fs.write(path, text)
        if lv["setup"]:
            lv["setup"](self)
        self.card()

    def complete(self):
        n, lv = self.level, self.ticket()
        self.out(c("1;32", f"✓ Objective secured: Operation {lv['op']} ({lv['ticket']})"))
        if n == TOTAL:
            self.best, self.finished = TOTAL, True
            self.plus_unlocked = True
            self.out(c("1;32", f"Mission complete: all {TOTAL} objectives secured. You were never here. "
                               "Next step: do the same on a real Ubuntu (wsl --install)."))
            if self.expert:
                self.out(c("1;36", "New Game+ complete. You can do this for real now."))
            else:
                self.out(c("1;36", "New Game+ unlocked: type  newgame +  for a new game with new answers, no command lists, "
                                   "no tips and one hint per ticket.") + c("90", f"\n  Password to unlock it on another computer: {plus_code()}"))
        else:
            self.best = max(self.best, n + 1)
            self.out(c("1;36", f"Password for level {n + 1}: {code_for(n + 1)}")
                     + c("90", f"  (keep it: type  level {n + 1}  on any computer and enter it to start here)"))
            self.start_level(n + 1)
        self.save()

    def next_part(self):
        parts = self.ticket()["parts"]
        self.out(c("1;32", f"✓ Step {self.part + 1}/{len(parts)} done"))
        self.part += 1
        self.hint_stage = 0
        if self.part >= len(parts):
            self.complete()
        else:
            self.out(c("1;97", f"-> Step {self.part + 1}/{len(parts)}: ") + parts[self.part][0])
            self.save()

    def auto_check(self):
        lv = self.ticket()
        if lv["parts"]:
            if self.part < len(lv["parts"]):
                goal = lv["parts"][self.part][1]
                if callable(goal) and goal(self):
                    self.next_part()
        elif lv["checks"] and all(f(self) for _, f in lv["checks"]):
            self.complete()

    def progress(self):
        lv = self.ticket()
        if lv["parts"]:
            return [(f"Step {k + 1}: {q}", k < self.part) for k, (q, _) in enumerate(lv["parts"])]
        if lv["checks"]:
            return [(label, bool(f(self))) for label, f in lv["checks"]]
        return [("Answer submitted", False)]

    # ---------------------------------------------------------- saving
    def save(self, session_open=True):
        state = {"seed": self.seed, "expert": self.expert, "plus": self.plus_unlocked, "ticket": self.ticket()["ticket"], "best_ticket": LEVELS[self.best - 1]["ticket"],
                 "level": self.level, "best": self.best, "finished": self.finished, "part": self.part,
                 "tips": self.tips, "open": session_open}
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f)
        except OSError as e:
            self.show_error(f"warning: could not save progress ({e})")

    def load(self):
        try:
            path = SAVE_FILE if os.path.exists(SAVE_FILE) or "PENGUIN_SAVE" in os.environ or not os.path.exists(LEGACY_SAVE) else LEGACY_SAVE
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if "PENGUIN_SEED" not in os.environ and "seed" in data:   # the saved game keeps its own answers
                self.seed = int(data["seed"])
                self.levels = levels_for(self.seed)
            ids = [lv["ticket"] for lv in LEVELS]
            best = ids.index(data["best_ticket"]) + 1 if data.get("best_ticket") in ids else int(data.get("best", 1))
            level = ids.index(data["ticket"]) + 1 if data.get("ticket") in ids else int(data.get("level", 1))
            self.best = min(max(best, 1), TOTAL)
            self.level = min(max(level, 1), self.best)
            self.finished = bool(data.get("finished", False))
            self.tips = bool(data.get("tips", True))
            self.expert = bool(data.get("expert", False))
            self.plus_unlocked = bool(data.get("plus", False)) or self.finished
            parts = self.ticket()["parts"] or []
            self.part = min(max(int(data.get("part", 0)), 0), max(len(parts) - 1, 0))
            return True
        except (OSError, ValueError, TypeError, AttributeError, KeyError):
            return False

    # ---------------------------------------------------------- the ticket card
    def card_lines(self, w, two):
        lv, n = self.ticket(), self.level
        rule = c("90", "─" * w)
        left_title, right_title = f" {lv['ticket']}  Operation {lv['op']}", f"Threat: {lv['threat']} "
        gap = w - len(left_title) - len(right_title)
        if gap >= 1:
            head = [c("1;97", left_title) + " " * gap + c(PRIO_COLOR.get(lv["prio"], "37"), right_title)]
        else:    # narrow screen (a phone): the title wraps and the priority gets its own line
            head = [c("1;97", " " + t) for t in textwrap.wrap(left_title.strip(), w - 1)] + \
                   [c(PRIO_COLOR.get(lv["prio"], "37"), " " + right_title.strip())]
        parts = [f"Handler: {lv['handler']}", f"Phase: {lv['phase']}", f"File {n} of {TOTAL}",
                 f"Password: {code_for(n)}"] + (["NEW GAME+"] if self.expert else [])
        rows, cur = [], ""
        for part in parts:  # wrap between fields, never inside one
            if cur and len(cur) + len(part) + 4 > w:
                rows.append(cur)
                cur = ""
            cur += ("   " if cur else " ") + part
        rows.append(cur)
        lines = [rule] + head + [c("90", r) for r in rows] + [rule]
        if self.expert:   # the briefing and nothing else
            body = [c("1;33", " BRIEFING")]
            for para in lv["brief"]:
                body += [" " + t for t in textwrap.wrap(para, w - 2)] + [""]
            if lv["parts"]:
                body.append(c("1;33", " STEPS"))
                for k, (question, _) in enumerate(lv["parts"]):
                    mark = c("32", "[x]") if k < self.part else (c("1;97", "[>]") if k == self.part else "[ ]")
                    wrapped = textwrap.wrap(f"{k + 1}. {question}", w - 8)
                    body += [f" {mark} {wrapped[0]}"] + ["     " + t for t in wrapped[1:]]
                body.append("")
            body += [c("1;33", " MISSION COMPLETE WHEN")] + [" " + t for t in textwrap.wrap(lv["done"], w - 2)]
            return lines + body + [rule]

        def build(lw, rw):
            left = [c("1;33", " BRIEFING")]
            for para in lv["brief"]:
                left += [" " + s for s in textwrap.wrap(para, lw - 1)] + [""]
            if lv["parts"]:
                left.append(c("1;33", " STEPS"))
                for k, (question, _) in enumerate(lv["parts"]):
                    mark = c("32", "[x]") if k < self.part else (c("1;97", "[>]") if k == self.part else "[ ]")
                    wrapped = textwrap.wrap(f"{k + 1}. {question}", lw - 6)
                    left += [f" {mark} {wrapped[0]}"] + ["     " + s for s in wrapped[1:]]
                left.append("")
            left += [c("1;33", " MISSION COMPLETE WHEN")] + [" " + s for s in textwrap.wrap(lv["done"], lw - 1)]
            right = [c("1;33", "TOOLKIT (examples: other files)")]
            for syntax, expl, example in lv["cmds"]:
                if syntax in ("submit ANSWER", "check"):  # always available: listed in the footer
                    continue
                right += [c("32", s) for s in textwrap.wrap(syntax, rw)]
                right += [c("90", "  " + s) for s in textwrap.wrap(f"{expl} (e.g. {example})", rw - 2)]
            return left, right
        if two:  # pick the column split that makes the card shortest
            best = None
            for lw in range(w // 3, w - 37):
                left, right = build(lw, w - lw - 3)
                if best is None or max(len(left), len(right)) < best[0]:
                    best = (max(len(left), len(right)), lw, left, right)
            _, lw, left, right = best
            for i in range(max(len(left), len(right))):
                l = left[i] if i < len(left) else ""
                r = right[i] if i < len(right) else ""
                lines.append(l + " " * (lw - vlen(l)) + c("90", " │ ") + r)
        else:
            left, right = build(w - 1, w - 1)
            lines += left + [""] + [" " + r for r in right]
        return lines + [rule]

    def card(self):
        w = self.width()
        lines = [""] + self.card_lines(w, w >= 70)
        footer = (" New Game+: only the problem is shown.   hint (one)  man  help"
                  if self.expert else
                  " Always available: ls cd pwd cat less tree man   Mission: task  check  hint  submit  password")
        lines += [c("90", row) for row in ([" " + r for r in textwrap.wrap(footer.strip(), w - 2, subsequent_indent="  ")] if vlen(footer) > w else [footer])]
        lines += [""]
        self.out("\n".join(lines))

    def summary(self):
        lv, w = self.ticket(), self.width()
        out = [c("1;97", f"{lv['ticket']}  Operation {lv['op']}") + c("90", f"   (threat: {lv['threat']}, file {self.level} of {TOTAL})")]
        if lv["parts"]:
            for k, (q, _) in enumerate(lv["parts"]):
                mark = "[x]" if k < self.part else ("[>]" if k == self.part else "[ ]")
                wrapped = textwrap.wrap(f"{mark} {q}", w - 2)
                out += ["  " + wrapped[0]] + ["      " + x for x in wrapped[1:]]
        else:
            out += ["  " + x for x in textwrap.wrap("Goal: " + lv["done"], w - 2)]
        rows, cur = [], "  Commands: "
        for syntax, _, _ in lv["cmds"]:  # never split one command over two lines
            if len(cur) + len(syntax) + 3 > w and cur.strip() != "Commands:":
                rows.append(cur.rstrip())
                cur = " " * 12
            cur += syntax + "   "
        out += [c("32", r) for r in rows + [cur.rstrip()]]
        out.append(c("90", "  Full briefing: task full    Hint: hint"))
        return "\n".join(out)

    # ---------------------------------------------------------- practice commands
    def cmd_submit(self, args, stdin):
        lv = self.ticket()
        if lv["parts"] and self.part >= len(lv["parts"]):
            raise ShellError("submit: this ticket is already resolved (type tasks)")
        if lv["parts"]:
            goal = lv["parts"][self.part][1]
            if callable(goal):
                raise ShellError(f"submit: step {self.part + 1} has no answer to submit. It completes by itself.",
                                 tip="type check to see what is still missing")
        elif lv["checks"]:
            raise ShellError("submit: this ticket has no answer to submit. It completes by itself.",
                             tip="type check to see what is still missing")
        else:
            goal = lv["answer"]
        if not args:
            raise ShellError("submit: missing answer", tip="type submit followed by what you found")
        accepted = goal if isinstance(goal, tuple) else (goal,)
        if " ".join(args).strip().lower() not in [a.lower() for a in accepted]:
            raise ShellError("Wrong answer, try again.", tip="type hint if you are stuck")
        if lv["parts"]:
            self.next_part()
        else:
            self.complete()

    def cmd_check(self, args, stdin):
        lv = self.ticket()
        if not lv["checks"] and not lv["parts"]:
            return "check: this ticket needs an answer. Find it, then: submit ANSWER"
        rows = []
        for k, (label, ok) in enumerate(self.progress()):
            current = lv["parts"] and k == self.part
            rows.append(f"[{'x' if ok else ('>' if current else ' ')}] {label}")
        return "\n".join(rows)

    def cmd_hint(self, args, stdin):
        """3 levels: a direction, then the commands to use, then the full solution."""
        lv = self.ticket()
        self.hint_stage = min(self.hint_stage + 1, 1 if self.expert else 3)
        if self.hint_stage == 1:
            text = NUDGES.get(lv["ticket"], "Read the ticket again: the commands on the card are all you need.")
        elif self.hint_stage == 2:
            found = []
            for tok in re.findall(r"(?:git|pip) [a-z-]+|python3 -m venv|\./[\w.]+|[a-z]+", lv["hint"]):
                if (tok in MAN or tok.split()[0] in ("git", "pip", "python3") or tok.startswith("./")) and tok not in found:
                    found.append(tok)
            text = "use these commands: " + ", ".join(found)
        else:
            text = "solution: " + lv["hint"]
        if self.expert:
            return c("33", "hint 1/1: ") + text + c("90", "  (New Game+: one hint per ticket - use man and help)")
        more = "  (type hint again for more)" if self.hint_stage < 3 else ""
        return c("33", f"hint {self.hint_stage}/3: ") + text + c("90", more)

    def cmd_tasks(self, args, stdin):
        rows, module = [], None
        for i, lv in enumerate(self.levels, 1):
            if lv["module"] != module:
                module = lv["module"]
                rows.append(c("1;33", f"PHASE: {lv['phase'].upper()}"))
            done = i < self.best or (i == TOTAL and self.finished)
            status = c("32", "done") if done else ("open" if i <= self.best else c("90", "locked"))
            rows.append(f"{'>' if i == self.level else ' '} {i:>2}  {lv['ticket']:<9}{lv['op']:<28}{status}")
        return "\n".join(rows)

    def cmd_task(self, args, stdin):
        if not args:
            return self.summary()
        if args[0] in ("full", "card"):
            self.card()
            return ""
        if not args[0].isdigit() or not 1 <= int(args[0]) <= TOTAL:
            raise ShellError(f"task: which number (1-{TOTAL})?", tip="example: task 1")
        n = int(args[0])
        if n > self.best:
            raise ShellError(f"task {n} is locked. Finish ticket {self.best} first", tip="type tasks to see the list")
        self.start_level(n)
        self.save()

    def cmd_password(self, args, stdin):
        return f"Password for level {self.level}: {code_for(self.level)}   (on another computer: level {self.level}, then type it)"

    cmd_clearance = cmd_password            # the old name still works

    def cmd_unlock(self, args, stdin):
        if not args:
            raise ShellError("unlock: missing password", tip="example: unlock PP-21-XXXX-XXXX")
        n = level_from_code(args[0], TOTAL)
        if n is None:
            raise ShellError("unlock: invalid password", tip="codes look like PP-21-XXXX-XXXX")
        self.best = max(self.best, n)
        self.start_level(n)
        self.save()

    def cmd_mode(self, args, stdin):
        """Shows the mode. New Game+ is a whole new run, started with newgame +, not a switch."""
        if args:
            raise ShellError("mode: the mode cannot be switched during a game", 1,
                             tip="start a new run with  newgame  (guided) or  newgame +  (New Game+, after you beat the game)")
        if self.expert:
            return "mode: New Game+ (only the problem is shown, no tips, one hint per ticket)"
        return ("mode: guided (commands and tips are shown)\n" +
                ("New Game+ is unlocked: type  newgame +" if self.plus_unlocked
                 else f"New Game+ unlocks when you finish all {TOTAL} tickets."))

    def cmd_level(self, args, stdin):
        """level N : go to level N. A level you have not reached yet needs its password (the code printed on that ticket)."""
        if not args:
            return (f"You are on level {self.level} of {TOTAL} (you have reached level {self.best}).\n"
                    "Type  level N  to go to level N. A level you have not reached needs its password.")
        if not args[0].isdigit() or not 1 <= int(args[0]) <= TOTAL:
            raise ShellError(f"level: which number (1-{TOTAL})?", tip="example: level 10")
        n = int(args[0])
        if n > self.best:
            prompt = f"Password for level {n}: "
            try:
                typed = getpass.getpass(prompt) if TTY else input(prompt)
            except EOFError:
                typed = ""
            if level_from_code(typed.strip(), TOTAL) != n:
                raise ShellError("level: wrong password", 1,
                                 tip=f"the password of level {n} is the password shown on that ticket's card")
            self.best = n
            self.out(c("32", f"Password accepted. Starting at level {n}."))
        self.start_level(n)
        self.save()

    def cmd_newgame(self, args, stdin):
        """newgame : start over with new answers. newgame + : New Game+ (unlocked when you beat the game)."""
        plus = bool(args) and args[0].lower() in ("+", "plus", "ng+", "expert")
        if args and not plus:
            raise ShellError(f"newgame: unknown option '{args[0]}'", 1, tip="newgame   or   newgame +")
        if plus and not self.plus_unlocked:
            try:
                typed = (getpass.getpass if TTY else input)("New Game+ is locked. Finish the game, or type its password: ")
            except EOFError:
                typed = ""
            if not is_plus_code(typed):
                raise ShellError("newgame: New Game+ is still locked", 1,
                                 tip=f"it unlocks when you finish all {TOTAL} tickets; the password is printed then")
            self.plus_unlocked = True
        what = ("Start New Game+? Progress is reset, every answer changes, commands and tips are hidden and you get one hint "
                "per ticket. (y/N) " if plus else "Start a new game? Your progress is reset and every answer changes. (y/N) ")
        try:
            answer = input(what)
        except EOFError:
            answer = ""
        if answer.strip().lower() not in ("y", "yes"):
            return "Nothing changed."
        self.seed = random.randrange(1, 10 ** 9)
        self.levels = levels_for(self.seed)
        self.best, self.finished = 1, False
        self.expert, self.tips = plus, not plus
        self.start_level(1)
        self.save()

    def cmd_reset(self, args, stdin):
        self.start_level(self.level)
        return "Ticket files rebuilt."

    def cmd_save(self, args, stdin):
        self.save()
        return "Progress saved."

    def cmd_tips(self, args, stdin):
        if args[:1] in (["on"], ["off"]):
            self.tips = args[0] == "on"
        return f"tips are {'on' if self.tips else 'off'} (tips are the grey lines under errors)"

    def cmd_exit(self, args, stdin):
        if self.sessions:                  # leaving an ssh session, not the practice shell
            return self.leave_session()
        self.save()
        self.running = False

    def cmd_history(self, args, stdin):
        return "\n".join(f"{i:>5}  {cmd}" for i, cmd in enumerate(self.typed, 1))

    def cmd_clear(self, args, stdin):
        if TTY:
            sys.stdout.write("\x1b[2J\x1b[3J\x1b[H")

    def cmd_help(self, args, stdin):
        return HELP

    def man_page(self, name, short=False):
        desc, synopsis, options = MAN[name]
        if short:
            return f"Usage: {synopsis}\n{desc}" + ("".join("\n  " + o for o in options))
        title = f"{name.upper()}(1)"
        lines = [c("1", title) + " " * max(1, 60 - 2 * len(title)) + "User Commands" + " " * 8 + c("1", title), "",
                 c("1", "NAME"), f"       {name} - {desc}", "", c("1", "SYNOPSIS"), f"       {synopsis}"]
        if name in DESCRIPTION:
            lines += ["", c("1", "DESCRIPTION")] + ["       " + l for l in textwrap.wrap(DESCRIPTION[name], 70)]
        if options:
            lines += ["", c("1", "OPTIONS")] + [f"       {o}" for o in options]
        if name in EXAMPLES:
            lines += ["", c("1", "EXAMPLES")]
            for command, what in EXAMPLES[name]:
                lines += [f"       {c('32', command)}", f"              {what}"]
        if name in EXIT_STATUS:
            lines += ["", c("1", "EXIT STATUS")] + ["       " + l for l in textwrap.wrap(EXIT_STATUS[name], 70)]
        if name in SEE_ALSO:
            lines += ["", c("1", "SEE ALSO"), f"       {SEE_ALSO[name]}"]
        return "\n".join(lines)

    def cmd_man(self, args, stdin):
        if not args:
            raise ShellError("What manual page do you want?\nFor example, try 'man man'.", 1, tip="example: man grep")
        name = args[0]
        if name not in MAN:
            raise ShellError(f"No manual entry for {name}", 16, tip="type help to see the commands")
        return self.man_page(name)

    def cmd_whatis(self, args, stdin):
        return "\n".join(f"{a} (1) - {MAN[a][0]}" if a in MAN else f"{a}: nothing appropriate." for a in args)
