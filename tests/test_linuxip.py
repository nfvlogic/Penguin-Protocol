"""Tests for Penguin Protocol. Run from the project folder:   cd tests && python -m unittest -v

Uses only the standard library. The game runs in a subprocess with piped input, so
output is plain text (no colours). A temporary save file is used, your progress is safe.
"""
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from linuxip.cmd_dev import ghash  # noqa: E402
from linuxip.manual import HELP, MAN  # noqa: E402
from linuxip.tickets import LEVELS, TOTAL  # noqa: E402
from linuxip.tickets_data import NUDGES  # noqa: E402

from linuxip.tickets_data import COSTS_PRD, COSTS_TOP, EXPORT_OPEN, TRAFFIC_404, TRAFFIC_SUM  # noqa: E402

WALKTHROUGH = f"""
cat welcome.txt
cd horizon
cat README.md
submit 5050
tree horizon
cat horizon/config/tst.py
submit horizon-db-02
cd horizon
ls -a
cat .flaskenv
cat .env
submit horizon_dev
cd horizon/app/features
mkdir -p launch_date/templates
touch launch_date/__init__.py launch_date/routes.py
check
echo Launch date field > launch_date/README.md
cp horizon/config/*.py backup/
mv horizon/migrations/draft.py horizon/migrations/0040_add_trademark_bu.py
echo horizon/*.pyc
rm horizon/*.pyc
check
rm -r horizon/__pycache__
echo __pycache__/ > horizon/.gitignore
echo "*.pyc" >> horizon/.gitignore
echo .env >> horizon/.gitignore
echo "- Added launch date field (HZN-104)" >> horizon/CHANGELOG.md
find horizon -name "*gate*"
cat horizon/app/workflow/gate_rules.py
submit g2-310
grep -r TODO horizon/app
grep -r release-blocker horizon/app
submit approvals.py
grep error app.log
grep 500 app.log | grep -v synthetic
submit /requests/new
wc -l deploy.log
tail -n 1 deploy.log
submit v1.8.3
grep -c FAILED test_report.txt
grep -cw FAILED test_report.txt
submit 6
grep -rl SECRET_KEY horizon/app --include="*.py" | wc -l
submit 3
cut -d " " -f 1 migrations_list.txt | sort | uniq -d
submit 0038
grep " 500 " access.log | cut -d " " -f 3 | sort | uniq -c | sort -n -r | head -n 1
submit /api/requests
./deploy.sh
cat deploy.sh
chmod +x deploy.sh
./deploy.sh > deploy_check.log
file tickets_export.csv
cat -A tickets_export.csv
grep -c ',open$' tickets_export.csv
tr -d '\r' < tickets_export.csv > clean.csv
grep -c ',open$' clean.csv
submit {EXPORT_OPEN}
diff horizon/config/tst.py horizon/config/prd.py
submit CACHE_TTL
submit 30
cp horizon/config/tst.py horizon/config/tst.py.bak
sed 's/horizon-db-02/horizon-db-new/g' horizon/config/tst.py
sed -i 's/horizon-db-02/horizon-db-new/g' horizon/config/tst.py
diff horizon/config/tst.py.bak horizon/config/tst.py
awk '$4 == 404' traffic.log | wc -l
grep -c 404 traffic.log
submit {TRAFFIC_404}
awk '$4 == 404 {{print $1}}' traffic.log | sort | uniq -c | sort -n -r
submit 10.20.30.66
awk '$1 == "10.20.30.66" {{s += $5}} END {{print s}}' traffic.log
submit {TRAFFIC_SUM}
awk -F, '$2 == "prd" {{s += $3}} END {{print s}}' costs.csv
submit {COSTS_PRD}
awk -F, '{{t[$1] += $3}} END {{for (k in t) print k, t[k]}}' costs.csv | sort -k2 -n -r
submit {COSTS_TOP}
grep horizon /etc/hosts
ping -c 3 horizon-db-02
ping -c 3 horizon-db-03
submit 10.20.30.12
grep -v RESOLVED alerts.log
grep 10.20.30.13 /etc/hosts
submit horizon-db-03
ssh analyst@horizon-prd "df -h"
ssh analyst@horizon-prd "df -h" > prd_disk.txt
submit /var/log
ssh analyst@horizon-prd "ls -l /var/log/horizon | sort -k5 -n -r | head -n 1"
submit debug.log
curl http://horizon-api/token
whoami
curl "http://horizon-api/token?user=analyst"
submit hzn-4821
curl http://horizon-api/api/projects/NPI-042
TOKEN=hzn-4821
curl -H "Authorization: Bearer $TOKEN" http://horizon-api/api/projects/NPI-042
submit Gate 2
curl http://horizon-api/api/users > users.json
grep -c admin users.json
grep -c '"admin"' users.json
submit 3
find incident -name "horizon-db-02*"
grep -c ERROR incident/2026/11/12/horizon-db-02.log
submit 7
pip install -r horizon/requirements.txt
cd horizon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask run --port 5050
cd horizon
source .venv/bin/activate
flask run
export DB_HOST=localhost
export DB_NAME=horizon_dev
flask run
cd horizon
git status
submit feature/requestor-role
submit app/routes.py
git log --oneline
submit {ghash('Add trademark BU dropdown')}
cd horizon
git checkout -b feature/launch-date
echo "add_column('request', 'launch_date')" > migrations/0042_add_launch_date.py
git add migrations/0042_add_launch_date.py
git commit -m "HZN-621 Add launch date column"
cd horizon
git diff
submit popmaps-db-01
git restore config/tst.py
git diff --staged
submit requests
ps aux | sort -k3 -n -r | head -n 3
submit 4127
kill 4127
ps aux | grep report_worker
kill -9 4127
ls -la horizon
stat horizon/.env
chmod 600 horizon/.env
chmod 750 horizon/scripts/deploy.sh
chmod 644 horizon/config/prd.py
systemctl --user status horizon-api
journalctl --user -u horizon-api -n 5
submit /home/analyst/horizon/api.conf
ls -l horizon/api.conf
chmod 640 horizon/api.conf
systemctl --user restart horizon-api
tar -czf backups/config-backup.tar.gz horizon/config
tar -tzf backups/config-backup.tar.gz | grep -c 'py$'
submit 3
tar -xzf backups/config-backup.tar.gz -C restore horizon/config/tst.py
cd horizon
source .venv/bin/activate
flask run --port 5050
ss -tlnp
submit 4388
kill 4388
flask run --port 5050
grep -r request_form horizon/app/templates
submit request_new.html
ls horizon/migrations
submit 0042
echo "add_column('request', 'launch_date')" > horizon/migrations/0042_add_launch_date.py
grep Failed auth.log | cut -d " " -f 9 | sort | uniq -c | sort -n -r
submit svc_horizon
grep Accepted auth.log
submit 10.20.30.66
grep 10.20.30.66 /etc/hosts
submit guest-laptop-07
ping -c 2 horizon-pre
submit horizon-pre
grep -r "primary = horizon-pre" lb
submit requests.conf
grep horizon-tst /etc/hosts
submit 10.20.30.31
grep -c workflow sprint.csv
grep -c ",workflow," sprint.csv
submit 11
cut -d "," -f 3 sprint.csv | sort -n -r | head -n 1
submit 21
grep ",workflow," sprint.csv > workflow.csv
curl -H "Authorization: Bearer hzn-4821" http://horizon-api/api/incidents | grep critical | grep open
submit INC-9003
grep ERROR incident/2026/11/12/horizon-db-03.log | head -n 1
submit 03:12
echo "incident: INC-9003" > postmortem.txt
echo "host: horizon-db-03" >> postmortem.txt
echo "first error: 03:12" >> postmortem.txt
tasks
"""


def run(commands, state=None):
    """Run the game with piped input. Returns (output, save-file data)."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    if state is None:
        os.remove(path)
    else:
        with open(path, "w") as f:
            json.dump(state, f)
    env = dict(os.environ, LINUXIP_SAVE=path)
    proc = subprocess.run([sys.executable, os.path.join(ROOT, "linux_13.4.py")], input=commands,
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=120)
    data = None
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        os.remove(path)
    return proc.stdout + proc.stderr, data


def answer(out, command):
    """The output lines printed right after `command` was typed at the prompt."""
    lines = out.splitlines()
    for i, line in enumerate(lines):
        if "@linuxip:" in line and line.endswith("$ " + command):
            res = []
            for nxt in lines[i + 1:]:
                if "@linuxip:" in nxt and "$ " in nxt:
                    break
                res.append(nxt)
            return "\n".join(res)
    raise AssertionError(f"command not found in transcript: {command}")


class Short(unittest.TestCase):
    def assertIn(self, member, container, msg=None):  # keep failure messages short
        if member not in container:
            self.fail(msg or f"not found: {member!r}")


class Walkthrough(Short):
    @classmethod
    def setUpClass(cls):
        cls.out, cls.save = run(WALKTHROUGH)

    def test_all_tickets_resolved(self):
        self.assertEqual(self.out.count("resolved:"), TOTAL, self.out[-2000:])
        self.assertIn("Backlog empty", self.out)

    def test_no_crash(self):
        self.assertNotIn("internal error", self.out)
        self.assertNotIn("Wrong answer", self.out)

    def test_save_file(self):
        self.assertEqual(self.save["ticket"], LEVELS[-1]["ticket"])
        self.assertTrue(self.save["finished"])

    def test_traps_give_the_wrong_number_first(self):
        self.assertEqual(answer(self.out, "grep -c FAILED test_report.txt"), "9")
        self.assertEqual(answer(self.out, "grep -cw FAILED test_report.txt"), "6")
        self.assertEqual(answer(self.out, "grep -c admin users.json"), "4")
        self.assertEqual(answer(self.out, "grep -c workflow sprint.csv"), "17")

    def test_grep_is_case_sensitive(self):
        self.assertEqual(answer(self.out, "grep error app.log"), "")

    def test_real_messages(self):
        self.assertIn("bash: ./deploy.sh: Permission denied", self.out)
        self.assertIn("error: externally-managed-environment", self.out)
        self.assertIn("RuntimeError: DB_HOST is not set", self.out)
        self.assertIn("3 packets transmitted, 3 received, 0% packet loss", self.out)
        self.assertIn("100% packet loss", self.out)
        self.assertIn('{"error":"missing user. Use /token?user=<your user name>"}', self.out)
        self.assertIn("Running on http://127.0.0.1:5050", self.out)

    def test_glob_expansion(self):
        self.assertEqual(answer(self.out, "echo horizon/*.pyc"),
                         "horizon/app.pyc horizon/utils.pyc horizon/wsgi.pyc")


class RealLinux(Short):
    """Behaviour that must match a real bash on Ubuntu."""

    @classmethod
    def setUpClass(cls):
        cls.out, _ = run("\n".join([
            "cd..", "dir", "Ls", "ipconfig", "rm -r /", "cat horizon", "cd welcome.txt", "cat Welcome.txt",
            'echo "hello', "ls |", "| sort", "task 9", "submit wrong-000", "mkdir", "mkdir a/b",
            "grep zzz welcome.txt; echo $?", "cat nope && echo yes || echo no", "X=5; echo $X",
            "echo '$HOME'", 'echo "$HOME"', "ls *.zzz", "find . -name *.txt", "rm /etc/hosts",
            "python --version", "sudo ls", "cp", "cd /nope", "ls -z", "echo hi > /etc/x", "history",
        ]) + "\n")

    def test_errors(self):
        o = self.out
        for text in ["cd..: command not found", "Ls: command not found", "ipconfig: command not found",
                     "rm: it is dangerous to operate recursively on '/'", "cat: horizon: Is a directory",
                     "bash: cd: welcome.txt: Not a directory", "cat: Welcome.txt: No such file or directory",
                     "did you mean cat welcome.txt", "unexpected EOF while looking for matching",
                     "bash: syntax error: unexpected end of file", "syntax error near unexpected token `|'",
                     "task 9 is locked", "Wrong answer, try again.", "mkdir: missing operand",
                     "mkdir: cannot create directory 'a/b': No such file or directory",
                     "ls: cannot access '*.zzz': No such file or directory", "find: paths must precede expression",
                     "rm: cannot remove '/etc/hosts': Permission denied", "Command 'python' not found",
                     "is not in the sudoers file", "cp: missing file operand",
                     "bash: cd: /nope: No such file or directory", "ls: invalid option -- 'z'",
                     "bash: /etc/x: Permission denied"]:
            self.assertIn(text, o)

    def test_exit_status_and_variables(self):
        self.assertEqual(answer(self.out, "grep zzz welcome.txt; echo $?"), "1")
        self.assertTrue(answer(self.out, "cat nope && echo yes || echo no").endswith("no"))
        self.assertEqual(answer(self.out, "X=5; echo $X"), "5")
        self.assertEqual(answer(self.out, "echo '$HOME'"), "$HOME")
        self.assertEqual(answer(self.out, 'echo "$HOME"'), "/home/analyst")

    def test_dir_works_like_ls(self):
        self.assertIn("welcome.txt", answer(self.out, "dir"))


class SaveAndResume(Short):
    def test_resume_mid_step(self):
        out, data = run("check\n", state={"ticket": "HZN-621", "best_ticket": "HZN-621", "part": 1})
        self.assertIn("Welcome back! Progress loaded", out)
        self.assertIn("Continuing at step 2", out)
        self.assertIn("[x] Step 1", out)
        self.assertEqual(data["ticket"], "HZN-621")

    def test_old_numbered_save(self):
        out, _ = run("tasks\n", state={"level": 3, "best": 5})
        self.assertIn(">  3  HZN-103", out)

    def test_every_ticket_starts(self):
        cmds = "".join(f"task {n}\ntask\nhint\nhint\nhint\ncheck\nls -a\n" for n in range(1, TOTAL + 1))
        out, _ = run(cmds, state={"ticket": LEVELS[0]["ticket"], "best_ticket": LEVELS[-1]["ticket"]})
        for lv in LEVELS:
            self.assertIn(lv["ticket"], out)
        self.assertEqual(out.count("hint 3/3"), TOTAL)
        self.assertNotIn("internal error", out)


# ---------------------------------------------------------------- the cards must not give the solution away
ALWAYS = {"ls", "cd", "pwd", "cat", "less", "tree", "man", "check", "hint", "submit", "task", "then"}
VALUE_OPTS = {"-d", "-f", "-n", "-c", "-k", "-t", "-m", "-H"}


def answers(lv):
    """All answers of a ticket that are specific enough to be recognised in a text."""
    raw = [lv["answer"]] if lv["answer"] else []
    raw += [goal for _, goal in (lv["parts"] or []) if not callable(goal)]
    out = []
    for a in raw:
        out += list(a) if isinstance(a, tuple) else [a]
    return [a for a in out if len(a) >= 3]   # 1-2 digit numbers appear naturally (head -n 5 ...)


GENERIC = {"ps aux", "ss -tlnp", "df -h"}   # standard invocations: not a ticket-specific solution


def specific_parts(command):
    """Pipeline parts of a solution command that contain real arguments (file, host, value...)."""
    parts = []
    for part in command.split("|"):
        try:
            toks = shlex.split(part)
        except ValueError:
            continue
        if not toks:
            continue
        start = 2 if toks[0] in ("git", "pip", "flask") else 1
        args, skip = [], False
        for t in toks[start:]:
            if skip:
                skip = False
            elif t.startswith("-"):
                skip = t in VALUE_OPTS
            else:
                args.append(t)
        if args and " ".join(toks) not in GENERIC:
            parts.append(" ".join(toks))
    return parts


class Cards(Short):
    def test_every_card_lists_the_commands_of_its_solution(self):
        for lv in LEVELS:
            card = " ".join(s + " " + e for s, _, e in lv["cmds"])
            for cmd in re.findall(r"(?:^|[;|]\s*)([a-z0-9]+|\./)", lv["hint"]):
                self.assertTrue(cmd in ALWAYS or cmd in card, f"{lv['ticket']}: '{cmd}' missing from the card")

    def test_examples_never_show_the_solution(self):
        for lv in LEVELS:
            solution = [p for seg in lv["hint"].split(";") for p in specific_parts(seg)]
            names = {part for rel in lv["files"] for part in rel.rstrip("/").split("/") if len(part) >= 4}
            for syntax, expl, example in lv["cmds"]:
                ex = " ".join(example.split())
                for part in specific_parts(ex.replace("...", "")):
                    self.assertNotIn(part, solution, f"{lv['ticket']}: example '{example}' is the solution")
                for tok in re.split(r"[\s/\"'|>]+", ex):
                    self.assertNotIn(tok, names, f"{lv['ticket']}: example '{example}' uses the ticket file '{tok}'")
                for a in answers(lv):
                    self.assertFalse(a.lower() in (syntax + " " + expl + " " + example).lower(),
                                     f"{lv['ticket']}: card line '{syntax}' contains the answer '{a}'")

    def test_texts_never_contain_answers(self):
        for lv in LEVELS:
            texts = lv["brief"] + [lv["done"], lv["name"], NUDGES.get(lv["ticket"], "")]
            texts += [q for q, _ in (lv["parts"] or [])]
            for a in answers(lv):
                for t in texts:
                    self.assertFalse(a.lower() in t.lower(), f"{lv['ticket']}: text contains the answer '{a}': {t[:60]}")

    def test_help_and_man_never_contain_answers(self):
        everything = (HELP + " " + " ".join(d + " " + s + " " + " ".join(o) for d, s, o in MAN.values())).lower()
        for lv in LEVELS:
            for a in answers(lv):
                if not a.isdigit():
                    self.assertFalse(a.lower() in everything, f"help/man contains the answer '{a}' of {lv['ticket']}")
            for part in [p for seg in lv["hint"].split(";") for p in specific_parts(seg)]:
                self.assertFalse(part.lower() in everything, f"help/man contains the solution '{part}'")


if __name__ == "__main__":
    unittest.main(verbosity=2)
