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

from penguin.cmd_dev import ghash  # noqa: E402
from penguin.manual import DESCRIPTION, EXAMPLES, EXIT_STATUS, HELP, MAN, SEE_ALSO  # noqa: E402
from penguin.tickets import LEVELS, TOTAL  # noqa: E402
from penguin.variants import levels_for  # noqa: E402

ALL_LEVELS = [lv for seed in range(0, 7) for lv in levels_for(seed)]   # the rules must hold for every seed
from penguin.tickets_data import NUDGES  # noqa: E402

from penguin.tickets_data import COSTS_PRD, COSTS_TOP, DU_UPLOADS, EXPORT_OPEN, TRAFFIC_404, TRAFFIC_SUM  # noqa: E402

WALKTHROUGH = f"""
cat welcome.txt
cd atlas
cat README.md
submit 5050
tree atlas
cat atlas/config/tst.py
submit atlas-db-02
cd atlas
ls -a
cat .flaskenv
cat .env
submit atlas_dev
cd atlas/app/features
mkdir -p launch_date/templates
touch launch_date/__init__.py launch_date/routes.py
check
echo Launch date field > launch_date/README.md
cp atlas/config/*.py backup/
mv atlas/migrations/draft.py atlas/migrations/0040_add_trademark_bu.py
tree vault
ls -a vault/drawer
cat vault/drawer/.keycard
mkdir -p loot/plans
cp vault/shelf/plans.txt loot/plans/
mv loot/plans/plans.txt loot/plans/floor-2.txt
submit AMBER-17
check
check
echo atlas/*.pyc
rm atlas/*.pyc
check
rm -r atlas/__pycache__
echo __pycache__/ > atlas/.gitignore
echo "*.pyc" >> atlas/.gitignore
echo .env >> atlas/.gitignore
echo "- Added launch date field (ATL-104)" >> atlas/CHANGELOG.md
find atlas -name "*gate*"
cat atlas/app/workflow/gate_rules.py
submit g2-310
grep -r TODO atlas/app
grep -r release-blocker atlas/app
submit approvals.py
grep error app.log
grep 500 app.log | grep -v synthetic
submit /requests/new
grep -r ALERT signals | grep -v drill
find signals -name "*.bak"
rm signals/relay-01.log.bak signals/relay-04.log.bak signals/archive/relay-02.log.bak
submit relay-07.log
submit kestrel-4
check
wc -l deploy.log
tail -n 1 deploy.log
submit v1.8.3
grep -c FAILED test_report.txt
grep -cw FAILED test_report.txt
submit 6
grep -rl SECRET_KEY atlas/app --include="*.py" | wc -l
submit 3
cut -d " " -f 1 migrations_list.txt | sort | uniq -d
submit 0038
grep " 500 " access.log | cut -d " " -f 3 | sort | uniq -c | sort -n -r | head -n 1
submit /api/requests
grep -cw DENIED transfers.log
grep -w DENIED transfers.log | cut -d " " -f 2 | sort | uniq -c | sort -n -r | head -n 1
tail -n 1 transfers.log
submit 8
submit acct-42
submit 17:55
check
./deploy.sh
cat deploy.sh
chmod +x deploy.sh
./deploy.sh > deploy_check.log
file tickets_export.csv
cat -A tickets_export.csv
grep -c ',open$' tickets_export.csv
tr -d '\\r' < tickets_export.csv > clean.csv
grep -c ',open$' clean.csv
submit {EXPORT_OPEN}
diff atlas/config/tst.py atlas/config/prd.py
submit CACHE_TTL
submit 30
cp atlas/config/tst.py atlas/config/tst.py.bak
sed 's/atlas-db-02/atlas-db-new/g' atlas/config/tst.py
sed -i 's/atlas-db-02/atlas-db-new/g' atlas/config/tst.py
diff atlas/config/tst.py.bak atlas/config/tst.py
awk '{{print $4}}' traffic.log | sort | uniq -c
submit 3
awk '$4 == 404' traffic.log | wc -l
grep -c 404 traffic.log
submit {TRAFFIC_404}
awk '$4 == 404 {{print $1}}' traffic.log | sort | uniq -c | sort -n -r
submit 10.20.30.66
awk '$1 == "10.20.30.66" {{s += $5}} END {{print s}}' traffic.log
submit {TRAFFIC_SUM}
cat -A roster.csv
tr -d '\r' < roster.csv > clean.csv
grep -c ',active$' clean.csv
sed -i 's/lisbon/oslo/g' clean.csv
submit 5
check
awk -F, '$2 == "prd" {{s += $3}} END {{print s}}' costs.csv
submit {COSTS_PRD}
awk -F, '{{t[$1] += $3}} END {{for (k in t) print k, t[k]}}' costs.csv | sort -k2 -n -r
submit {COSTS_TOP}
find build -name "*.tmp"
find build -name "*.tmp" | xargs echo
find build -name "*.tmp" | xargs rm
grep atlas /etc/hosts
ping -c 3 atlas-db-02
ping -c 3 atlas-db-03
submit 10.20.30.12
grep -v RESOLVED alerts.log
grep 10.20.30.13 /etc/hosts
submit atlas-db-03
ssh analyst@atlas-prd "df -h"
ssh analyst@atlas-prd "df -h" > prd_disk.txt
submit /var/log
ssh analyst@atlas-prd "ls -l /var/log/atlas | sort -k5 -n -r | head -n 1"
submit debug.log
ping -c 1 atlas-api
ping -c 1 atlas-db-02
ping -c 1 atlas-pre
ping -c 1 gateway
awk -F, '$1 == "guest-laptop-07" {{s += $3}} END {{print s}}' exfil.csv
find drop -name "*.tmp" | xargs rm
submit atlas-pre
submit 520
check
curl http://atlas-api/token
whoami
curl "http://atlas-api/token?user=analyst"
submit atl-4821
curl http://atlas-api/api/projects/NPI-042
TOKEN=atl-4821
curl -H "Authorization: Bearer $TOKEN" http://atlas-api/api/projects/NPI-042
submit Gate 2
curl http://atlas-api/api/users > users.json
grep -c admin users.json
grep -c '"admin"' users.json
submit 3
find incident -name "atlas-db-02*"
grep -c ERROR incident/2026/11/12/atlas-db-02.log
submit 7
pip install -r atlas/requirements.txt
cd atlas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask run --port 5050
curl http://atlas-api/token
curl "http://atlas-api/token?user=analyst"
curl http://atlas-api/api/users > agents.json
grep -c '"approver"' agents.json
submit atl-4821
submit 3
check
cd atlas
source .venv/bin/activate
flask run
export DB_HOST=localhost
export DB_NAME=atlas_dev
flask run
cd atlas
git status
submit feature/requestor-role
submit app/routes.py
git log --oneline
submit {ghash('Add trademark BU dropdown')}
cd atlas
git checkout -b feature/launch-date
echo "add_column('request', 'launch_date')" > migrations/0042_add_launch_date.py
git add migrations/0042_add_launch_date.py
git commit -m "ATL-146 Add launch date column"
cd atlas
git diff
submit compass-db-01
git restore config/tst.py
git diff --staged
submit requests
ps aux | sort -k3 -n -r | head -n 3
submit 4127
kill 4127
ps aux | grep report_worker
kill -9 4127
cd atlas
git status
git branch
git diff
ps aux | grep exfil
kill 5150
submit feature/night-shift
submit app/auth.py
check
ls -la atlas
stat atlas/.env
chmod 600 atlas/.env
chmod 750 atlas/scripts/deploy.sh
chmod 644 atlas/config/prd.py
systemctl --user status atlas-api
journalctl --user -u atlas-api -n 5
submit /home/analyst/atlas/api.conf
ls -l atlas/api.conf
chmod 640 atlas/api.conf
systemctl --user restart atlas-api
tar -czf backups/config-backup.tar.gz atlas/config
tar -tzf backups/config-backup.tar.gz | grep -c 'py$'
submit 3
tar -xzf backups/config-backup.tar.gz -C restore atlas/config/tst.py
cd atlas
source .venv/bin/activate
flask run --port 5050
ss -tlnp
submit 4388
kill 4388
flask run --port 5050
du -s data/* | sort -n -r | head -n 3
submit uploads
submit {DU_UPLOADS}
du -s cargo/* | sort -n -r | head -n 1
systemctl --user status vault-door
journalctl --user -u vault-door -n 5
chmod 640 vault.conf
systemctl --user restart vault-door
tar -czf out/cargo.tar.gz cargo/crates
submit crates
check
cat /etc/passwd | tail -n 2
grep -c 'bash$' /etc/passwd
submit 2
grep mysql /etc/passwd | cut -d: -f3
submit 114
echo 'for h in $(cat hosts.txt); do ping -c 1 $h > /dev/null 2>&1 && echo "$h up" || echo "$h down"; done' > check_hosts.sh
chmod +x check_hosts.sh
./check_hosts.sh > report.txt
find logs -name "*.log" -size +1k
tar -czf logs-archive.tar.gz $(find logs -name "*.log" -size +1k)
find logs -name "*.log" -size +1k -delete
readlink current
submit v1.8.2
ln -sf releases/v1.9.0 current
ls -l releases/v1.8.2
ln -sfn releases/v1.9.0 current
cat nightly.sh
./nightly.sh
./nightly.sh > nightly.log 2>&1
./nightly.sh 2> nightly.err > /dev/null
grep -c 'nologin$' /etc/passwd
readlink front
ln -sfn releases/v2.0.0 front
cat sweep.sh
./sweep.sh 2> sweep.err > /dev/null
submit 3
check
grep -r request_form atlas/app/templates
submit request_new.html
ls atlas/migrations
submit 0042
echo "add_column('request', 'launch_date')" > atlas/migrations/0042_add_launch_date.py
grep Failed auth.log | cut -d " " -f 9 | sort | uniq -c | sort -n -r
submit svc_atlas
grep Accepted auth.log
submit 10.20.30.66
grep 10.20.30.66 /etc/hosts
submit guest-laptop-07
ping -c 2 atlas-pre
submit atlas-pre
grep -r "primary = atlas-pre" lb
submit requests.conf
grep atlas-tst /etc/hosts
submit 10.20.30.31
grep -c workflow sprint.csv
grep -c ",workflow," sprint.csv
submit 11
cut -d "," -f 3 sprint.csv | sort -n -r | head -n 1
submit 21
grep ",workflow," sprint.csv > workflow.csv
curl -H "Authorization: Bearer atl-4821" http://atlas-api/api/incidents | grep critical | grep open
submit INC-9003
grep ERROR incident/2026/11/12/atlas-db-03.log | head -n 1
submit 03:12
echo "incident: INC-9003" > postmortem.txt
echo "host: atlas-db-03" >> postmortem.txt
echo "first error: 03:12" >> postmortem.txt
grep -r MASTERKEY core | grep -v bak
chmod 600 core/room-c/master.key
tar -czf exit.tar.gz core
echo "key: omega-7" > report.txt
echo "status: secured" >> report.txt
submit omega-7
check
tasks
"""


def run(commands, state=None, seed=0):
    """Run the game with piped input. Returns (output, save-file data)."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    if state is None:
        os.remove(path)
    else:
        with open(path, "w") as f:
            json.dump(state, f)
    env = dict(os.environ, PENGUIN_SAVE=path, PENGUIN_FIRSTS=os.environ.get("PENGUIN_FIRSTS", "0"))
    if seed is None:
        env.pop("PENGUIN_SEED", None)
    else:
        env["PENGUIN_SEED"] = str(seed)
    proc = subprocess.run([sys.executable, os.path.join(ROOT, "penguin.py")], input=commands,
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
        if "@penguin:" in line and line.endswith("$ " + command):
            res = []
            for nxt in lines[i + 1:]:
                if "@penguin:" in nxt and "$ " in nxt:
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
        self.assertEqual(self.out.count("secured:"), TOTAL, self.out[-2000:])
        self.assertIn("Mission complete", self.out)

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
        self.assertEqual(answer(self.out, "echo atlas/*.pyc"),
                         "atlas/app.pyc atlas/utils.pyc atlas/wsgi.pyc")


class RealLinux(Short):
    """Behaviour that must match a real bash on Ubuntu."""

    @classmethod
    def setUpClass(cls):
        cls.out, _ = run("\n".join([
            "cd..", "dir", "Ls", "ipconfig", "rm -r /", "cat atlas", "cd welcome.txt", "cat Welcome.txt",
            "| sort", "task 9", "submit wrong-000", "mkdir", "mkdir a/b",
            "grep zzz welcome.txt; echo $?", "cat nope && echo yes || echo no", "X=5; echo $X",
            "echo '$HOME'", 'echo "$HOME"', "ls *.zzz", "find . -name *.txt", "rm /etc/hosts",
            "python --version", "sudo ls", "cp", "cd /nope", "ls -z", "echo hi > /etc/x", "history",
        ]) + "\n")

    def test_errors(self):
        o = self.out
        for text in ["cd..: command not found", "Ls: command not found", "ipconfig: command not found",
                     "rm: it is dangerous to operate recursively on '/'", "cat: atlas: Is a directory",
                     "bash: cd: welcome.txt: Not a directory", "cat: Welcome.txt: No such file or directory",
                     "did you mean cat welcome.txt", "syntax error near unexpected token `|'",
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


class Scripting(Short):
    """Loops, tests, substitutions and expansions must behave like bash."""

    @classmethod
    def setUpClass(cls):
        cls.out, _ = run("\n".join([
            "echo $(pwd)", 'echo "n: $(ls | wc -l)"', "echo $((2+3*4)) $((7/2)) $((-7/2)) $((7%3))",
            "echo {a,b,c}.txt f{1..3}", "echo {01..03}", 'echo "{a,b}"',
            "for f in a b c; do echo $f; done", "mkdir d && touch d/x.md d/y.md",
            "for f in d/*.md; do echo found $f; done", "if [ -f d/x.md ]; then echo yes; fi",
            "if test -d nope; then echo dir; else echo nodir; fi",
            "x=5; while [ $x -gt 3 ]; do echo $x; x=$((x-1)); done", "[ -f nope ] || echo missing",
            "[ 5 -gt abc ]", "if [ -f x; then echo oops; fi", 'echo -e "a\\tb"', 'printf "%s-%s\\n" a b c d',
            "date +%F", "for i in $(seq 1 3); do echo n=$i; done",
            "for i in 1 2 3", "do", "  if [ $i -eq 2 ]; then continue; fi", "  echo i=$i", "done",
            "V='a b'; echo $V | wc -w", 'echo "$V" | wc -w', "echo [$EMPTY]x", "unset V; echo ${V:-fallback}",
            'echo "unclosed', "still open", 'closed"', "done_marker=1", "echo $done_marker",
            "echo `echo back`", "n=0; until [ $n -ge 2 ]; do n=$((n+1)); done; echo $n",
            "for i in 1 2 3; do if [ $i -eq 2 ]; then break; fi; echo b$i; done", "fi", "alias ll='ls -l'",
        ]) + "\n")

    def test_expansions(self):
        o = self.out
        self.assertEqual(answer(o, "echo $(pwd)"), "/home/analyst")
        self.assertEqual(answer(o, 'echo "n: $(ls | wc -l)"'), "n: 3")
        self.assertEqual(answer(o, "echo $((2+3*4)) $((7/2)) $((-7/2)) $((7%3))"), "14 3 -3 1")
        self.assertEqual(answer(o, "echo {a,b,c}.txt f{1..3}"), "a.txt b.txt c.txt f1 f2 f3")
        self.assertEqual(answer(o, "echo {01..03}"), "01 02 03")
        self.assertEqual(answer(o, 'echo "{a,b}"'), "{a,b}")
        self.assertEqual(answer(o, "echo `echo back`"), "back")

    def test_word_splitting_and_quotes(self):
        o = self.out
        self.assertEqual(answer(o, "V='a b'; echo $V | wc -w"), "2")
        self.assertEqual(answer(o, 'echo "$V" | wc -w'), "2")
        self.assertEqual(answer(o, "echo [$EMPTY]x"), "[]x")
        self.assertEqual(answer(o, "unset V; echo ${V:-fallback}"), "fallback")

    def test_loops_and_tests(self):
        o = self.out
        self.assertEqual(answer(o, "for f in a b c; do echo $f; done"), "a\nb\nc")
        self.assertEqual(answer(o, "for f in d/*.md; do echo found $f; done"), "found d/x.md\nfound d/y.md")
        self.assertEqual(answer(o, "if [ -f d/x.md ]; then echo yes; fi"), "yes")
        self.assertEqual(answer(o, "if test -d nope; then echo dir; else echo nodir; fi"), "nodir")
        self.assertEqual(answer(o, "x=5; while [ $x -gt 3 ]; do echo $x; x=$((x-1)); done"), "5\n4")
        self.assertEqual(answer(o, "[ -f nope ] || echo missing"), "missing")
        self.assertEqual(answer(o, "n=0; until [ $n -ge 2 ]; do n=$((n+1)); done; echo $n"), "2")
        self.assertEqual(answer(o, "for i in 1 2 3; do if [ $i -eq 2 ]; then break; fi; echo b$i; done"), "b1")
        self.assertEqual(answer(o, "for i in $(seq 1 3); do echo n=$i; done"), "n=1\nn=2\nn=3")

    def test_multi_line_input_shows_the_continuation_prompt(self):
        o = self.out
        self.assertIn("> do", o)
        self.assertIn("i=1\ni=3", o)
        self.assertIn("> still open", o)
        self.assertEqual(answer(o, "echo $done_marker"), "1")

    def test_builtin_messages(self):
        o = self.out
        self.assertIn("bash: [: abc: integer expression expected", o)
        self.assertIn("bash: [: missing `]'", o)
        self.assertIn("bash: syntax error near unexpected token `fi'", o)
        self.assertEqual(answer(o, 'echo -e "a\\tb"'), "a\tb")
        self.assertEqual(answer(o, 'printf "%s-%s\\n" a b c d'), "a-b\nc-d")
        self.assertEqual(answer(o, "date +%F"), "2026-11-12")

    def test_end_of_input_inside_a_quote(self):
        out, _ = run('echo "hello\n')
        self.assertIn("bash: unexpected EOF while looking for matching `\"'", out)
        self.assertIn("bash: syntax error: unexpected end of file", out)


class RealCommands(Short):
    """Options and behaviour of the common commands, checked against what GNU/Linux prints."""

    @classmethod
    def setUpClass(cls):
        cls.cmds = [
            "mkdir -p t/sub && printf 'one\\ntwo\\nthree\\nfour\\n' > t/a.txt && echo hi > t/sub/b.log && touch t/empty.txt",
            "grep -n -C1 three t/a.txt", "grep -A1 one t/a.txt", "grep -e one -e four t/a.txt", "grep -c o t/a.txt",
            "grep -m1 o t/a.txt", "grep -x two t/a.txt", "grep -o -E '[a-z]{3}' t/a.txt | head -n 2",
            "grep -rn hi t --include='*.log'", "grep -v o t/a.txt",
            "find t -type f", "find t -name '*.txt' -o -name '*.log'", "find t ! -name '*.txt' -type f",
            "find t -empty", "find t -maxdepth 1 -type d", "find t -name '*.log' -exec cat {} \\;",
            "find t -size +0 -type f", "find t -mtime +1", "find t -name 'x' -exec echo {} +",
            "tail -n 2 t/a.txt", "tail -n +3 t/a.txt", "head -n -3 t/a.txt", "head -c 4 t/a.txt",
            "ln -s t/a.txt link", "ls -l link", "cat link", "readlink -f link", "rm link; ls link",
            "chmod 444 t/a.txt", "echo x > t/a.txt", "ls -l t/a.txt", "chmod 600 t/a.txt && ls -l t/a.txt",
            "chmod u+x,g-r t/a.txt && ls -l t/a.txt", "chmod 000 t/sub; cd t/sub", "ls t/sub", "chmod 755 t/sub",
            "printf '1K\\n2M\\n500\\n' | sort -h", "printf 'a b c\\n' | awk '{print $2}'",
            "printf 'x 1\\ny 2\\nz 3\\n' | awk '$2 > 1 {s += $2} END {print s}'",
            "printf 'a,b\\nc,d\\n' | awk -F, '{print $2}'", "echo hello | sed 's/l/L/g'", "printf 'a\\nb\\nc\\n' | sed -n '2p'",
            "printf 'a\\nb\\n' | sed '1d'", "printf 'a\\nb\\n' | sed '$d'", "echo abc | tr a-c A-C", "echo 'a  b' | tr -s ' '",
            "printf 'a\\nb\\n' | tac", "echo hello | rev", "seq 3", "seq 2 2 8", "date +%Y/%m/%d", "date +%H:%M",
            "uname -sr", "id -un", "cat <<EOT", "x $USER", "EOT", "pushd t >/dev/null; pwd; popd >/dev/null; pwd",
        ]
        cls.out, _ = run("\n".join(cls.cmds) + "\n")

    def a(self, command):
        return answer(self.out, command)

    def test_grep(self):
        self.assertEqual(self.a("grep -n -C1 three t/a.txt"), "2-two\n3:three\n4-four")
        self.assertEqual(self.a("grep -A1 one t/a.txt"), "one\ntwo")
        self.assertEqual(self.a("grep -e one -e four t/a.txt"), "one\nfour")
        self.assertEqual(self.a("grep -c o t/a.txt"), "3")
        self.assertEqual(self.a("grep -m1 o t/a.txt"), "one")
        self.assertEqual(self.a("grep -x two t/a.txt"), "two")
        self.assertEqual(self.a("grep -o -E '[a-z]{3}' t/a.txt | head -n 2"), "one\ntwo")
        self.assertEqual(self.a("grep -rn hi t --include='*.log'"), "t/sub/b.log:1:hi")
        self.assertEqual(self.a("grep -v o t/a.txt"), "three")

    def test_find(self):
        self.assertEqual(self.a("find t -type f"), "t/a.txt\nt/empty.txt\nt/sub/b.log")
        self.assertEqual(self.a("find t ! -name '*.txt' -type f"), "t/sub/b.log")
        self.assertEqual(self.a("find t -empty"), "t/empty.txt")
        self.assertEqual(self.a("find t -maxdepth 1 -type d"), "t\nt/sub")
        self.assertEqual(self.a("find t -name '*.log' -exec cat {} \\;"), "hi")
        self.assertEqual(self.a("find t -size +0 -type f"), "t/a.txt\nt/sub/b.log")
        self.assertEqual(self.a("find t -mtime +1"), "")
        self.assertEqual(self.a("find t -name 'x' -exec echo {} +"), "")

    def test_head_tail(self):
        self.assertEqual(self.a("tail -n 2 t/a.txt"), "three\nfour")
        self.assertEqual(self.a("tail -n +3 t/a.txt"), "three\nfour")
        self.assertEqual(self.a("head -n -3 t/a.txt"), "one")
        self.assertEqual(self.a("head -c 4 t/a.txt"), "one\n")

    def test_symlinks(self):
        self.assertIn("lrwxrwxrwx 1 analyst analyst", self.a("ls -l link"))
        self.assertIn("link -> t/a.txt", self.a("ls -l link"))
        self.assertEqual(self.a("cat link"), "one\ntwo\nthree\nfour")
        self.assertEqual(self.a("readlink -f link"), "/home/analyst/t/a.txt")
        self.assertIn("ls: cannot access 'link'", self.a("rm link; ls link"))

    def test_permissions(self):
        self.assertIn("bash: t/a.txt: Permission denied", self.a("echo x > t/a.txt"))
        self.assertTrue(self.a("ls -l t/a.txt").startswith("-r--r--r-- 1 analyst analyst"))
        self.assertIn("-rw-------", self.a("chmod 600 t/a.txt && ls -l t/a.txt"))
        self.assertIn("-rwx------", self.a("chmod u+x,g-r t/a.txt && ls -l t/a.txt"))
        self.assertIn("bash: cd: t/sub: Permission denied", self.a("chmod 000 t/sub; cd t/sub"))
        self.assertIn("ls: cannot open directory 't/sub': Permission denied", self.a("ls t/sub"))

    def test_text_tools(self):
        self.assertEqual(self.a("printf '1K\\n2M\\n500\\n' | sort -h"), "500\n1K\n2M")
        self.assertEqual(self.a("printf 'a b c\\n' | awk '{print $2}'"), "b")
        self.assertEqual(self.a("printf 'x 1\\ny 2\\nz 3\\n' | awk '$2 > 1 {s += $2} END {print s}'"), "5")
        self.assertEqual(self.a("printf 'a,b\\nc,d\\n' | awk -F, '{print $2}'"), "b\nd")
        self.assertEqual(self.a("echo hello | sed 's/l/L/g'"), "heLLo")
        self.assertEqual(self.a("printf 'a\\nb\\nc\\n' | sed -n '2p'"), "b")
        self.assertEqual(self.a("printf 'a\\nb\\n' | sed '$d'"), "a")
        self.assertEqual(self.a("echo abc | tr a-c A-C"), "ABC")
        self.assertEqual(self.a("echo 'a  b' | tr -s ' '"), "a b")
        self.assertEqual(self.a("printf 'a\\nb\\n' | tac"), "b\na")
        self.assertEqual(self.a("seq 2 2 8"), "2\n4\n6\n8")

    def test_small_commands(self):
        self.assertEqual(self.a("date +%Y/%m/%d"), "2026/11/12")
        self.assertEqual(self.a("date +%H:%M"), "09:00")
        self.assertEqual(self.a("uname -sr"), "Linux 6.8.0-corp")
        self.assertEqual(self.a("id -un"), "analyst")

    def test_heredoc_and_pushd(self):
        self.assertIn("x analyst", self.out)
        self.assertIn("/home/analyst/t\n/home/analyst", self.out)


class Completion(unittest.TestCase):
    def test_tab_completion(self):
        os.environ.setdefault("PENGUIN_SAVE", os.path.join(tempfile.gettempdir(), "penguin_completion_test.json"))
        from penguin.shell import Shell
        s = Shell()
        s.start_level(1)
        self.assertEqual(s.completions("gre", "gre"), ["grep"])
        self.assertIn("sed", s.completions("se", "se"))
        self.assertEqual(s.completions("ls at", "at"), ["atlas/"])
        self.assertEqual(s.completions("cat atlas/READ", "atlas/READ"), ["atlas/README.md"])
        self.assertEqual(s.completions("cat atlas/", "atlas/"), ["atlas/docs/", "atlas/README.md"])
        self.assertEqual(s.completions("echo hi | sor", "sor"), ["sort"])
        self.assertEqual(s.completions("cat w", "w"), ["welcome.txt"])


class SystemAndNetwork(Short):
    """The machine around you: system files, redirection of error messages, curl, ssh sessions."""

    @classmethod
    def setUpClass(cls):
        cls.out, _ = run("\n".join([
            "cat /etc/passwd | tail -n 1", "cat /etc/shadow", "ls /root", "cat /var/log/syslog", "ls /bin | head -n 1",
            "/usr/bin/echo via-path", "cat /etc/os-release | head -n 1", "touch -c nothere; ls nothere",
            "ls -d */", "mkdir dd; ls -d */", "ls nope; echo $?", "ls nope 2>&1 | wc -l", "ls nope > o.txt 2>&1; cat o.txt",
            "ls nope &> both.txt; cat both.txt", "echo oops >&2", "curl -I http://atlas-api/status | head -n 1",
            'curl -s -o /dev/null -w "%{http_code}\\n" http://atlas-api/status', "curl -f http://atlas-api/nope; echo $?",
            "ssh analyst@gateway", "hostname", "pwd", "ls -a", "exit", "hostname", "ssh nowhere uptime; echo $?",
            "ssh atlas-db-01; echo $?", "top | head -n 2", "ps aux | grep -c ps",
        ]) + "\n")

    def a(self, command):
        return answer(self.out, command)

    def test_system_files(self):
        self.assertEqual(self.a("cat /etc/passwd | tail -n 1"), "analyst:x:1000:1000:analyst,,,:/home/analyst:/bin/bash")
        self.assertIn("cat: /etc/shadow: Permission denied", self.a("cat /etc/shadow"))
        self.assertIn("ls: cannot open directory '/root': Permission denied", self.a("ls /root"))
        self.assertIn("cat: /var/log/syslog: Permission denied", self.a("cat /var/log/syslog"))
        self.assertEqual(self.a("/usr/bin/echo via-path"), "via-path")
        self.assertEqual(self.a("cat /etc/os-release | head -n 1"), 'PRETTY_NAME="Ubuntu 24.04.1 LTS"')

    def test_globs_and_touch(self):
        self.assertEqual(self.a("touch -c nothere; ls nothere").splitlines()[0],
                         "ls: cannot access 'nothere': No such file or directory")
        self.assertEqual(self.a("mkdir dd; ls -d */"), "atlas/  dd/")

    def test_exit_status_and_error_streams(self):
        self.assertTrue(self.a("ls nope; echo $?").endswith("2"))
        self.assertEqual(self.a("ls nope 2>&1 | wc -l"), "1")
        self.assertEqual(self.a("ls nope > o.txt 2>&1; cat o.txt"), "ls: cannot access 'nope': No such file or directory")
        self.assertEqual(self.a("ls nope &> both.txt; cat both.txt"), "ls: cannot access 'nope': No such file or directory")
        self.assertEqual(self.a("echo oops >&2"), "oops")

    def test_curl(self):
        self.assertEqual(self.a("curl -I http://atlas-api/status | head -n 1"), "HTTP/1.1 200 OK")
        self.assertEqual(self.a('curl -s -o /dev/null -w "%{http_code}\\n" http://atlas-api/status'), "200")
        self.assertIn("curl: (22) The requested URL returned error: 404", self.a("curl -f http://atlas-api/nope; echo $?"))

    def test_ssh_login_session(self):
        o = self.out
        self.assertIn("analyst@gateway:~$ hostname", o)
        self.assertIn("analyst@gateway:~$ hostname\ngateway", o)
        self.assertIn("Connection to gateway closed.", o)
        self.assertIn("ssh: Could not resolve hostname nowhere", o)
        self.assertIn("ssh: connect to host atlas-db-01 port 22: Connection timed out", o)

    def test_top_and_ps(self):
        self.assertTrue(self.a("top | head -n 2").startswith("top - 09:00:01 up 12 days"))
        self.assertEqual(self.a("ps aux | grep -c ps").splitlines()[0], "2")


class SshTicket(Short):
    def test_server_answers_inside_a_session(self):
        from penguin.tickets import LEVELS
        tid = next(lv["ticket"] for lv in LEVELS if lv["name"] == "PRD disk is full")
        out, _ = run("ssh analyst@atlas-prd\ndf -h\nls -l /var/log/atlas\nexit\n", state={"ticket": tid, "best_ticket": tid})
        self.assertIn("/dev/sdb1        20G   20G     0 100% /var/log", out)
        self.assertIn("8429356811 Nov 12 09:00 debug.log", out)
        self.assertIn("Connection to atlas-prd closed.", out)


class Randomised(Short):
    """Every new game has other answers; a saved game keeps its own. The commands must really print them."""

    @staticmethod
    def play(seed, name, commands):
        levels = levels_for(seed)
        lv = next(l for l in levels if l["name"] == name)
        out, _ = run(commands + "true\n", state={"ticket": lv["ticket"], "best_ticket": lv["ticket"]}, seed=seed)
        return lv, out

    def test_answers_change_with_the_seed(self):
        varied = {}
        for seed in range(0, 7):
            for lv in levels_for(seed):
                if lv["answer"]:
                    varied.setdefault(lv["name"], set()).add(str(lv["answer"]))
        for name in ("Run Atlas locally", "Failing unit tests", "Migration conflict", "What is deployed on TST?",
                     "Slow database incident", "Which gate rules are active?"):
            self.assertGreater(len(varied[name]), 2, f"{name} has the same answer in every game")

    def test_commands_print_the_new_answers(self):
        for seed in (1, 2, 3):
            lv, out = self.play(seed, "Failing unit tests", "grep -cw FAILED test_report.txt\n")
            self.assertEqual(answer(out, "grep -cw FAILED test_report.txt"), lv["answer"])
            lv, out = self.play(seed, "Migration conflict", 'cut -d " " -f 1 migrations_list.txt | sort | uniq -d\n')
            self.assertEqual(answer(out, 'cut -d " " -f 1 migrations_list.txt | sort | uniq -d'), lv["answer"])
            lv, out = self.play(seed, "What is deployed on TST?", "tail -n 1 deploy.log\n")
            self.assertIn(lv["answer"], answer(out, "tail -n 1 deploy.log"))
            lv, out = self.play(seed, "Slow database incident", "grep -c ERROR incident/2026/11/12/atlas-db-02.log\n")
            self.assertEqual(answer(out, "grep -c ERROR incident/2026/11/12/atlas-db-02.log"), lv["answer"])
            lv, out = self.play(seed, "Who reads the secret key?", 'grep -rl SECRET_KEY atlas/app --include="*.py" | wc -l\n')
            self.assertEqual(answer(out, 'grep -rl SECRET_KEY atlas/app --include="*.py" | wc -l'), lv["answer"])
            lv, out = self.play(seed, "Which endpoint is broken?",
                                'grep " 500 " access.log | cut -d " " -f 3 | sort | uniq -c | sort -n -r | head -n 1\n')
            self.assertIn(lv["answer"], answer(out, 'grep " 500 " access.log | cut -d " " -f 3 | sort | uniq -c | sort -n -r | head -n 1'))

    def test_awk_and_du_answers(self):
        lv, out = self.play(2, "Who keeps asking for missing pages?", "awk '$4 == 404' traffic.log | wc -l\n")
        self.assertEqual(answer(out, "awk '$4 == 404' traffic.log | wc -l"), lv["parts"][1][1])
        top = lv["parts"][2][1]
        lv, out = self.play(2, "Who keeps asking for missing pages?", f"awk '$1 == \"{top}\" {{s += $5}} END {{print s}}' traffic.log\n")
        self.assertEqual(answer(out, f"awk '$1 == \"{top}\" {{s += $5}} END {{print s}}' traffic.log"), lv["parts"][3][1])
        lv, out = self.play(3, "Who ate the disk?", "du -s data/* | sort -n -r | head -n 1\n")
        size, folder = answer(out, "du -s data/* | sort -n -r | head -n 1").split("\t")
        self.assertEqual((folder, size), ("data/" + lv["parts"][0][1], lv["parts"][1][1]))

    def test_a_saved_game_keeps_its_answers(self):
        out, data = run("hint\n", seed=7)
        self.assertEqual(data["seed"], 7)
        out2, data2 = run("tasks\n", state=data, seed=None)          # no fixed seed: the saved one is used
        self.assertEqual(data2["seed"], 7)
        _, a = run("check\n", seed=None)
        _, b = run("check\n", seed=None)
        self.assertNotEqual(a["seed"], b["seed"])                       # two new games differ

    def test_pip_celebrates_each_first_once_and_explains_wrong_answers(self):
        os.environ["PENGUIN_FIRSTS"] = "1"
        try:
            out, _ = run("cat welcome.txt | grep atlas\nls | head -n 1\nls > x.txt\nsubmit 8080\nsubmit 1234\n")
        finally:
            del os.environ["PENGUIN_FIRSTS"]
        self.assertEqual(out.count("First pipe!"), 1)
        self.assertIn("First redirect!", out)
        self.assertIn("Old notes lie", out)                       # mission 1's own hand-written trap (8080 is in notes.txt)

    def test_a_vault_follows_every_five_missions(self):
        self.assertEqual([k + 1 for k, lv in enumerate(LEVELS) if lv["ticket"].startswith("VLT")], list(range(6, TOTAL + 1, 6)))
        lv = LEVELS[5]
        cmds = "\n".join(lv["hint"].split(" ; ")) + "\nsubmit AMBER-17\ncheck\n"
        out, data = run(cmds, state={"ticket": "VLT-01", "best_ticket": "VLT-01"})
        self.assertIn("VAULT 1 · Archive", out)
        self.assertIn("BOSS", out)
        self.assertIn("VAULT 1 CRACKED", out)
        self.assertIn("Password for level 7", out)              # passwords come after each vault
        self.assertEqual(data["ticket"], "ATL-106")

    def test_level_command_asks_for_a_password(self):
        from penguin.clearance import code_for
        out, data = run("level 10\nwrong-password\nlevel 10\n%s\n" % code_for(10))
        self.assertIn("Password for level 10: ", out)
        self.assertIn("level: wrong password", out)
        self.assertIn("Password accepted. Starting at level 10.", out)
        self.assertEqual(data["level"], 10)
        self.assertEqual(data["best"], 10)
        out, data = run("level 3\n", state={"ticket": "ATL-105", "best_ticket": "ATL-105"})   # reached already: no password
        self.assertNotIn("Password for level", out)
        self.assertEqual(data["level"], 3)
        out, _ = run("level 99\nlevel x\nlevel\n")
        self.assertIn(f"level: which number (1-{TOTAL})?", out)
        self.assertIn(f"You are on level 1 of {TOTAL}", out)


class ModesAndManuals(Short):
    LAST = {"ticket": LEVELS[-1]["ticket"], "best_ticket": LEVELS[-1]["ticket"]}

    def test_new_game_plus_is_locked_until_you_beat_the_game(self):
        from penguin.clearance import plus_code
        out, data = run("newgame +\nwrong\nmode\n")
        self.assertIn("New Game+ is locked. Finish the game, or type its password: ", out)
        self.assertIn("newgame: New Game+ is still locked", out)
        self.assertIn(f"New Game+ unlocks when you finish all {TOTAL} tickets.", out)
        self.assertFalse(data["expert"])
        out, data = run("newgame +\n%s\ny\nmode\n" % plus_code())          # the password unlocks it on any computer
        self.assertIn("mode: New Game+", out)
        self.assertTrue(data["expert"] and data["plus"])

    def test_finishing_the_game_unlocks_new_game_plus(self):
        from penguin.clearance import plus_code
        out, data = run("submit 0\n", state=dict(self.LAST, plus=False))
        lv = LEVELS[-1]
        out, data = run("check\n", state=dict(self.LAST))
        self.assertFalse(data["plus"])
        # beat the last ticket (the last vault): its solution, then its answers
        cmds = "\n".join(lv["hint"].split(" ; ")) + "\nsubmit omega-7\ncheck\n"
        out, data = run(cmds, state=dict(self.LAST))
        self.assertIn("Mission complete", out)
        self.assertIn("New Game+ unlocked: type  newgame +", out)
        self.assertIn(plus_code(), out)
        self.assertTrue(data["plus"] and data["finished"])

    def test_new_game_plus_hides_commands_tips_and_most_hints(self):
        out, data = run("ls nope\nhint\nhint\n", state=dict(self.LAST, plus=True, expert=True, tips=False))
        card = out.split("Welcome back", 1)[1].split("analyst@penguin")[0]
        self.assertIn("BRIEFING", card)
        self.assertNotIn("TOOLKIT", card)
        self.assertIn("NEW GAME+", card)
        self.assertNotIn("tip: check the name", out)
        self.assertEqual(out.count("hint 1/1:"), 2)                       # asking again never gives more
        self.assertNotIn("hint 2/3", out)

    def test_new_game_plus_survives_a_restart_and_a_normal_new_game_leaves_it(self):
        out, data = run("tasks\n", state=dict(self.LAST, plus=True, expert=True, tips=False))
        self.assertTrue(data["expert"])
        out, data = run("newgame\ny\n", state=data)
        self.assertFalse(data["expert"])
        self.assertTrue(data["plus"])                                      # unlocked for good
        self.assertIn("GOAL", out.split("Start a new game?")[1])               # back to the normal card

    def test_mode_cannot_be_switched(self):
        out, _ = run("mode expert\nmode\n")
        self.assertIn("mode: the mode cannot be switched during a game", out)
        self.assertIn("mode: guided", out)

    def test_man_pages_have_sections_and_examples(self):
        out, _ = run("man grep\nman find\nman nosuchthing\n")
        for section in ("NAME", "SYNOPSIS", "DESCRIPTION", "OPTIONS", "EXAMPLES", "EXIT STATUS", "SEE ALSO"):
            self.assertIn(section, out.split("man find")[0])
        self.assertIn("grep -i warn server.log", out)
        self.assertIn("No manual entry for nosuchthing", out)

    def test_every_common_command_has_examples(self):
        for name in ("ls", "grep", "find", "sed", "awk", "chmod", "tar", "ssh", "curl", "kill", "ps"):
            self.assertIn(name, EXAMPLES)
            self.assertIn(name, DESCRIPTION)


class CommandLine(Short):
    def cli(self, *args, stdin=""):
        env = dict(os.environ, PENGUIN_SAVE=os.path.join(tempfile.gettempdir(), "penguin_cli_test.json"))
        env.pop("PENGUIN_SEED", None)
        return subprocess.run([sys.executable, os.path.join(ROOT, "penguin.py"), *args], input=stdin, capture_output=True,
                              text=True, encoding="utf-8", env=env, timeout=60)

    def test_version_and_help(self):
        self.assertEqual(self.cli("--version").stdout.strip(), "Penguin Protocol 6.1")
        out = self.cli("--help")
        self.assertEqual(out.returncode, 0)
        self.assertIn("Usage: penguin.py [OPTIONS]", out.stdout)
        self.assertIn("--plus", out.stdout)

    def test_bad_options_fail_cleanly(self):
        out = self.cli("--bogus")
        self.assertEqual(out.returncode, 2)
        self.assertIn("penguin: unknown option '--bogus'", out.stderr)
        self.assertEqual(self.cli("--seed", "x").returncode, 2)

    def test_plus_flag_needs_a_beaten_game(self):
        locked = self.cli("--plus", "--seed", "4", "--save", os.path.join(tempfile.gettempdir(), "penguin_cli_new.json"),
                          stdin="exit\n").stdout
        self.assertIn("New Game+ is locked", locked)
        self.assertNotIn("NEW GAME+", locked)

    def test_new_flag_ignores_the_saved_game(self):
        again = self.cli("--new", "--seed", "4", stdin="exit\n").stdout
        self.assertNotIn("Welcome back", again)


class SaveAndResume(Short):
    def test_resume_mid_step(self):
        out, data = run("check\n", state={"ticket": "ATL-146", "best_ticket": "ATL-146", "part": 1})
        self.assertIn("Welcome back! Progress loaded", out)
        self.assertIn("Continuing at step 2", out)
        self.assertIn("[x] Step 1", out)
        self.assertEqual(data["ticket"], "ATL-146")

    def test_old_numbered_save(self):
        out, _ = run("tasks\n", state={"level": 3, "best": 5})
        self.assertIn(">  3  ATL-103", out)

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
    def test_pip_never_gives_the_answer_away(self):
        for seed in (0, 7, 42):
            for lv in levels_for(seed):
                goals = [lv["answer"]] if lv["answer"] else [g for _, g in (lv["parts"] or []) if not callable(g)]
                for goal in goals:
                    for a in (goal if isinstance(goal, tuple) else (goal,)):
                        if len(str(a)) >= 3:
                            for line in lv["pip"] + [lv["wrong"]]:
                                self.assertNotIn(str(a).lower(), line.lower(), f"{lv['ticket']}: Pip says the answer '{a}'")

    def test_every_card_lists_the_commands_of_its_solution(self):
        for lv in ALL_LEVELS:
            card = " ".join(s + " " + e for s, _, e in lv["cmds"])
            for cmd in re.findall(r"(?:^|[;|]\s*)([a-z0-9]+|\./)", lv["hint"]):
                self.assertTrue(cmd in ALWAYS or cmd in card, f"{lv['ticket']}: '{cmd}' missing from the card")

    def test_examples_never_show_the_solution(self):
        for lv in ALL_LEVELS:
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
        for lv in ALL_LEVELS:
            texts = lv["brief"] + [lv["done"], lv["name"], NUDGES.get(lv["ticket"], "")]
            texts += [q for q, _ in (lv["parts"] or [])]
            for a in answers(lv):
                for t in texts:
                    self.assertFalse(a.lower() in t.lower(), f"{lv['ticket']}: text contains the answer '{a}': {t[:60]}")

    def test_help_and_man_never_contain_answers(self):
        extra = " ".join(DESCRIPTION.values()) + " " + " ".join(f"{c} {w}" for ex in EXAMPLES.values() for c, w in ex)
        extra += " " + " ".join(EXIT_STATUS.values()) + " " + " ".join(SEE_ALSO.values())
        everything = (HELP + " " + extra + " " + " ".join(d + " " + s + " " + " ".join(o) for d, s, o in MAN.values())).lower()
        for lv in ALL_LEVELS:
            for a in answers(lv):
                if not a.isdigit():
                    self.assertFalse(a.lower() in everything, f"help/man contains the answer '{a}' of {lv['ticket']}")
            for part in [p for seg in lv["hint"].split(";") for p in specific_parts(seg)]:
                self.assertFalse(part.lower() in everything, f"help/man contains the solution '{part}'")



class FeedTests(unittest.TestCase):
    """Shell.feed() handles one typed line and returns the next prompt (used by the web page)."""

    def setUp(self):
        os.environ["PENGUIN_SAVE"] = os.path.join(tempfile.mkdtemp(), "save.json")
        os.environ["PENGUIN_SEED"] = "1"
        from penguin.shell import Shell
        self.sh = Shell()
        self.sh.start()

    def test_continuation_and_heredoc(self):
        sh = self.sh
        self.assertEqual(sh.feed("for i in 1 2; do"), "> ")
        self.assertEqual(sh.feed("echo $i"), "> ")
        self.assertTrue(sh.feed("done").startswith("analyst@"))
        self.assertEqual(sh.feed("cat <<EOF > /tmp/h.txt"), "> ")
        self.assertEqual(sh.feed("hello"), "> ")
        self.assertTrue(sh.feed("EOF").startswith("analyst@"))
        self.assertEqual(sh.fs.d["/tmp/h.txt"].strip(), "hello")

    def test_interrupt_and_logout(self):
        sh = self.sh
        sh.feed("echo 'open")
        self.assertTrue(sh.interrupt().startswith("analyst@"))
        self.assertIsNone(sh.eof())
        self.assertFalse(sh.running)


if __name__ == "__main__":
    unittest.main(verbosity=2)
