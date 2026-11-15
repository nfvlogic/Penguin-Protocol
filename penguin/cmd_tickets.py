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
from .pip import say
from .manual import DESCRIPTION, EXAMPLES, EXIT_STATUS, HELP, MAN, SEE_ALSO
from .tickets import LEVELS, NUDGES, TOTAL
from .variants import levels_for

PRIO_COLOR = {"Critical": "1;31", "High": "33", "Normal": "36"}



def wrap_para(text, width):
    """Wrap a paragraph, but keep its own line breaks and indentation (a folder layout must stay a layout)."""
    rows = []
    for line in text.split("\n"):
        rows += textwrap.wrap(line, width, subsequent_indent=" " * (len(line) - len(line.lstrip())) if line[:1] == " " else "",
                              replace_whitespace=False, drop_whitespace=False) or [""]
    return rows

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
        self.checks_done = self.met_checks()
        self.card()
        self.coach()

    def complete(self):
        n, lv = self.level, self.ticket()
        if lv["module"] == "Vault":     # a boss: the big celebration
            self.out(say("vaultwin", [("1;33", f"VAULT {int(lv['ticket'][4:])} CRACKED"),
                                      ("1;32", f"✓ Objective secured: Operation {lv['op']} ({lv['ticket']})"),
                                      ("90", "Five missions, one job. You are getting good, partner.")], self.width()))
        else:
            self.out(say("win", [("1;32", f"✓ Objective secured: Operation {lv['op']} ({lv['ticket']})"),
                                 ("90", "Nice work, partner.")], self.width()))
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
            if lv["module"] == "Vault":     # after each vault, so a normal win stays clean (password shows it any time)
                self.out(c("1;36", f"Password for level {n + 1}: {code_for(n + 1)}")
                         + c("90", f"  (type  level {n + 1}  to start here later)"))
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
            goal = parts[self.part][1]
            if callable(goal) and goal(self):     # already done before it was asked for: tick it now
                self.next_part()

    def auto_check(self):
        lv = self.ticket()
        if lv["parts"]:
            if self.part < len(lv["parts"]):
                goal = lv["parts"][self.part][1]
                if callable(goal) and goal(self):
                    self.next_part()
        elif lv["checks"]:
            met = self.met_checks()
            if len(met) == len(lv["checks"]):
                self.complete()
                return
            if self.checks_done is not None:       # tell the player each time one more requirement is satisfied
                for k in sorted(met - self.checks_done):
                    self.out(c("1;32", f"✓ Requirement met ({len(met)}/{len(lv['checks'])}): ") + lv["checks"][k][0])
            self.checks_done = met

    # The first mission also coaches: one short nudge at a time, until the player has used the basic commands.
    COACH = [
        (lambda t: any(x.split()[0] == "ls" for x in t if x.split()), "First time? Type  ls  to see what is here."),
        (lambda t: any("cat" in x.split() and "welcome" in x for x in t), "Good. Now read the welcome file:  cat welcome.txt"),
        (lambda t: any(x.startswith("cd") and "atlas" in x for x in t), "It points to a folder. Go inside:  cd atlas"),
        (lambda t: any("README" in x for x in t), "Now read the project file there:  cat README.md"),
    ]

    def coach(self):
        if self.level != 1 or self.part or self.expert or not self.tips:
            return
        nxt = next((k for k, (done, _) in enumerate(self.COACH) if not done(self.typed)), len(self.COACH))
        if nxt == self.coach_last:
            return
        self.coach_last = nxt
        msg = self.COACH[nxt][1] if nxt < len(self.COACH) else "Found the port number? Send it:  submit NUMBER"
        rows = textwrap.wrap(msg, self.width() - 6)
        self.out("\n".join([c("1;33", "Pip: ") + c("36", rows[0])] + ["      " + c("36", r) for r in rows[1:]]))

    def met_checks(self):
        return {k for k, (_, f) in enumerate(self.ticket()["checks"] or []) if f(self)}

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
    def where_text(self, lv):
        """Where things are and where new files go: said on every card, so nobody has to guess."""
        names = sorted({rel.strip("/").split("/")[0] + ("/" if "/" in rel.strip("/") or rel.endswith("/") else "")
                        for rel in lv["files"]})
        shown = [n for n in names if not n.startswith(".")]
        hidden = len(shown) < len(names)
        text = "You start in ~ (your home folder, /home/analyst). Paths in this briefing start there."
        if shown:
            text += " In it: " + "  ".join(shown) + (" + hidden files." if hidden else ".")
        return text

    def requirements(self, lv, w):
        """The checklist of a mission that closes by itself, with the real paths."""
        rows = [c("1;33", " REQUIREMENTS (check shows them)")]
        for text, ok in self.progress():
            mark = c("32", "[x]") if ok else "[ ]"
            wrapped = textwrap.wrap(text, max(20, w - 8), break_long_words=False, break_on_hyphens=False)
            rows += ["   " + mark + " " + wrapped[0]] + ["       " + r for r in wrapped[1:]]
        return rows

    def result_tree(self, lv, w):
        """WHEN YOU ARE DONE: the end state drawn as a tree from ~, so it is clear WHERE everything goes."""
        if not lv.get("result"):
            return []
        notes = {p.rstrip("/"): note for p, note in lv["result"]}
        folders = {p.rstrip("/") for p, _ in lv["result"] if p.endswith("/")}
        paths = []                                    # in the order they are listed
        for p, _ in lv["result"]:
            parts = p.rstrip("/").split("/")
            for k in range(1, len(parts) + 1):
                if "/".join(parts[:k]) not in paths:
                    paths.append("/".join(parts[:k]))
                if k < len(parts):
                    folders.add("/".join(parts[:k]))
        have = {f.rstrip("/") for f in lv["files"]}
        def exists(p):
            return p in have or any(f.startswith(p + "/") for f in have)
        rows = [c("1;33", " WHEN YOU ARE DONE (your home folder):"), "   ~/"]
        def walk(parent, prefix):
            kids = [p for p in paths if "/" in p and p.rsplit("/", 1)[0] == parent] if parent else \
                   [p for p in paths if "/" not in p]
            for i, p in enumerate(kids):
                last = i == len(kids) - 1
                name = p.rsplit("/", 1)[-1] + ("/" if p in folders else "")
                note = notes.get(p) or ("(already there)" if exists(p) else "")
                if note and p not in notes:
                    note = c("90", note)
                elif note:
                    note = c("1;32", note) if note.startswith("NEW") else c("1;33", note)
                branch = "   " + prefix + ("└── " if last else "├── ")
                line = branch + name
                if note and vlen(line) + 2 + vlen(note) <= w:
                    rows.append(line + "  " + note)
                else:
                    rows.append(line)
                    if note:
                        pad = "   " + prefix + ("    " if last else "│   ") + "  "
                        plain = re.sub(r"\x1b\[[0-9;]*m", "", note)
                        col = "1;32" if plain.startswith("NEW") else ("90" if plain == "(already there)" else "1;33")
                        rows.extend(pad + c(col, t) for t in textwrap.wrap(plain, max(16, w - vlen(pad))))
                walk(p, prefix + ("    " if last else "│   "))
        walk("", "")
        return rows

    def card_lines(self, w, two):
        lv, n = self.ticket(), self.level
        boss = lv["module"] == "Vault"
        rule = c("33", "═" * w) if boss else c("90", "─" * w)
        left_title, right_title = f" {lv['ticket']}  Operation {lv['op']}", f"Threat: {lv['threat']} "
        if boss:
            left_title, right_title = f" ◆ VAULT {int(lv['ticket'][4:])} · {lv['op']}", f"BOSS  {n}/{TOTAL} "
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
            for para in lv["brief"] + [self.where_text(lv)]:
                body += [" " + t for t in wrap_para(para, w - 2)] + [""]
            if lv.get("result"):
                body += self.result_tree(lv, w) + [""]
            if lv["parts"]:
                body.append(c("1;33", " STEPS"))
                for k, (question, _) in enumerate(lv["parts"]):
                    mark = c("32", "[x]") if k < self.part else (c("1;97", "[>]") if k == self.part else "[ ]")
                    wrapped = textwrap.wrap(f"{k + 1}. {question}", w - 8)
                    body += [f" {mark} {wrapped[0]}"] + ["     " + t for t in wrapped[1:]]
                body.append("")
            if lv["checks"] and not lv["parts"]:
                body += self.requirements(lv, w) + [""]
            body += [c("1;33", " MISSION COMPLETE WHEN")] + [" " + t for t in textwrap.wrap(lv["done"], w - 2)]
            return lines + body + [rule]


        def build(lw, rw):
            left = [c("1;33", " BRIEFING")]
            for para in lv["brief"] + [self.where_text(lv)]:
                left += [" " + s for s in wrap_para(para, lw - 1)] + [""]
            if lv.get("result"):
                left += self.result_tree(lv, lw) + [""]
            if lv["parts"]:
                left.append(c("1;33", " STEPS"))
                for k, (question, _) in enumerate(lv["parts"]):
                    mark = c("32", "[x]") if k < self.part else (c("1;97", "[>]") if k == self.part else "[ ]")
                    wrapped = textwrap.wrap(f"{k + 1}. {question}", lw - 6)
                    left += [f" {mark} {wrapped[0]}"] + ["     " + s for s in wrapped[1:]]
                left.append("")
            if lv["checks"] and not lv["parts"]:
                left += self.requirements(lv, lw) + [""]
            left += [c("1;33", " MISSION COMPLETE WHEN")] + [" " + s for s in textwrap.wrap(lv["done"], lw - 1)]
            hint = self.finish_hint()
            if hint:
                left += [""] + [c("1;36", " " + s) for s in textwrap.wrap(hint, lw - 1)]
            right = [c("1;33", "TOOLKIT (examples use other files)")]
            for syntax, expl, example in lv["cmds"]:
                if syntax in ("submit ANSWER", "check"):  # always available: listed in the footer
                    continue
                right += [c("32", s) for s in textwrap.wrap(syntax, rw)]
                right += [c("90", "  " + s) for s in textwrap.wrap(expl, rw - 2)]
                if example:   # a sample of how it is typed (never the answer): on a phone too
                    right += [c("36", "  e.g. " + s if i == 0 else "       " + s)
                              for i, s in enumerate(textwrap.wrap(example, rw - 7, break_on_hyphens=False))]
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

    def finish_hint(self):
        """One line telling the player how this ticket gets closed (new players do not know about submit)."""
        lv = self.ticket()
        if lv["parts"]:
            goal = lv["parts"][min(self.part, len(lv["parts"]) - 1)][1]
            by_answer = not callable(goal)
        else:
            by_answer = not lv["checks"]
        if by_answer:
            return "Found the answer? Type:  submit ANSWER"
        return "" if "closes by itself" in lv["done"].lower() else "This one closes by itself. Type  check  to see what is missing."

    def card(self):
        w = self.width()
        if not self.expert:     # Pip opens the briefing with one line
            lv = self.ticket()
            self.out(say("vault" if lv["module"] == "Vault" else "think", [("33", lv["pip"][0])], w))
        lines = [""] + self.card_lines(w, w >= 70)
        footer = (" New Game+: only the problem is shown.   hint (one)  man  help"
                  if self.expert else
                  " Always available: ls cd pwd cat less tree man   Mission: task  check  hint  submit  password"
                  if w >= 70 else " Always: ls cd pwd cat less tree man   Also: task check hint submit")
        lines += [c("90", row) for row in ([" " + r for r in textwrap.wrap(footer.strip(), w - 2, subsequent_indent="  ")] if vlen(footer) > w else [footer])]
        lines += [""]
        self.out("\n".join(lines))

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
            self.out(say("fail", [("31", "Wrong answer, try again."), ("90", self.why_wrong(" ".join(args).strip(), accepted))],
                         self.width()))
            raise ShellError("")
        if lv["parts"]:
            self.next_part()
        else:
            self.complete()

    def why_wrong(self, given, accepted):
        """Pip's one-line reason for a wrong answer: the usual beginner slips, then a nudge towards hint."""
        g, goals = given.lower().strip("'\""), [str(a).lower() for a in accepted]
        if any(a in g and a != g for a in goals):
            return "Close! Send only the answer itself, nothing around it."
        if "/" in g and any(g.rstrip("/").split("/")[-1] == a for a in goals):
            return "Just the name, not the whole path."
        if self.ticket().get("wrong"):           # the hand-written trap of this mission
            return self.ticket()["wrong"]
        texts = " ".join(list(self.ticket()["files"]) + [v for v in self.ticket()["files"].values() if isinstance(v, str)]).lower()
        if len(g) >= 3 and re.search(r"(?<![\w.-])" + re.escape(g) + r"(?![\w-])", texts):
            return "That is in the files, but it is a decoy. Check which file is current."
        if g.isdigit() and all(a.isdigit() for a in goals):
            return "Not that number. Look again, or type hint."
        return "Stuck? Type hint."

    FIRSTS = [("pipe", lambda l: "|" in l.replace("||", ""), "First pipe! You chained two commands."),
              ("redirect", lambda l: re.search(r"(^|[^2&])>", l) is not None, "First redirect! You saved output to a file."),
              ("grep", lambda l: re.search(r"(^|[|;&]\s*)grep\b", l) is not None, "First grep! You searched without opening every file.")]

    def celebrate(self, line):
        """Pip hops the first time you use a big idea (once per game)."""
        if self.expert or not self.tips or os.environ.get("PENGUIN_FIRSTS") == "0":   # 0: the command tests want pure output
            return
        for key, used, msg in self.FIRSTS:
            if key not in self.firsts and used(line) and self.status == 0:
                self.firsts.add(key)
                self.out(say("win", [("1;32", msg)], self.width()))
                return

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
        more = [("90", "Type hint again for more.")] if self.hint_stage < 3 else []
        return say("hint", [("33", f"hint {self.hint_stage}/3"), text] + more, self.width())

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
        if not args:            # the whole briefing again
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
        self.out(say("sleep", [("90", "Pip is off the grid. Progress saved.")], self.width()))
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
