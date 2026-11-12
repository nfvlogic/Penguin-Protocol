"""Generated files and setup functions used by the tickets (log files, CSVs, git history...)."""
import random

from .core import HOME, parse_requirements

REQUIREMENTS = """Flask==3.0.3
PyMySQL==1.1.1
SQLAlchemy==2.0.36
alembic==1.14.0
python-dotenv==1.0.1"""

DEPLOY_SH = """#!/bin/bash
# Pre-deploy check for Horizon
echo "== Horizon pre-deploy check =="
echo "Checking database..."
ping -c 2 horizon-db-02
echo "Checking API..."
ping -c 2 horizon-api
echo "Pre-deploy check finished: OK\""""


# ---------------------------------------------------------------- generated files
def gen_app_log():
    out = []
    for i in range(1, 161):
        t = f"08:{i // 3:02d}:{(i * 7) % 60:02d}"
        ms = 20 + (i * 13) % 300
        if i in (30, 77, 140):
            out.append(f"{t} ERROR GET /test/crash 500 {ms}ms (synthetic monitoring test)")
        elif i in (55, 101, 118):
            out.append(f"{t} ERROR POST /requests/new 500 {ms}ms KeyError: 'launch_date'")
        elif i % 17 == 0:
            out.append(f"{t} WARN GET /projects/unknown 404 {ms}ms")
        else:
            out.append(f"{t} INFO GET {['/projects', '/requests', '/gates', '/api/health'][i % 4]} 200 {ms}ms")
    return "\n".join(out)


def gen_deploy_log():
    lines = ["00:00 deployed version=v1.7.0 (previous release)"]
    lines += [f"{i * 6 // 60:02d}:{i * 6 % 60:02d} INFO health check ok" for i in range(1, 239)]
    return "\n".join(lines + ["23:59 deployed version=v1.8.3"])


def gen_test_report():
    names = ["gate_approval", "requestor_role", "launch_date", "sso_login", "project_list",
             "trademark_bu", "scope_length", "date_format", "permissions", "audit_log"]
    status = ["FAILED"] * 6 + ["XFAILED"] * 3 + ["PASSED"] * 31
    random.Random(4).shuffle(status)
    lines = ["============ test session starts ============", "collected 40 items", ""]
    lines += [f"tests/test_{names[i % 10]}.py::test_case_{i + 1:02d} {st}" for i, st in enumerate(status)]
    return "\n".join(lines + ["", "====== summary hidden: count the results yourself ======"])


def gen_migrations():
    names = ["initial_schema", "add_projects", "add_users", "add_roles", "add_gates"]
    rows = [f"{i:04d} {names[i % 5]}_{i}" for i in range(1, 42)] + ["0038 add_trademark_bu_field"]
    random.Random(8).shuffle(rows)
    return "\n".join(rows)


def gen_access():
    rows = ([("/api/health", 200)] * 20 + [("/api/projects", 200)] * 9 + [("/api/requests", 500)] * 8 +
            [("/api/projects", 500)] * 3 + [("/api/gates", 500)] * 5 + [("/login", 302)] * 6)
    random.Random(11).shuffle(rows)
    return "\n".join(f"10.20.30.{5 + i % 7} GET {p} {s} {12 + i % 40}ms" for i, (p, s) in enumerate(rows))


def gen_incident(server, errors):
    log = []
    for i in range(40):
        if i % 4 == 1 and sum("ERROR" in x for x in log) < errors:
            log.append(f"10:{i:02d} ERROR query timeout after 30s")
        elif i % 9 == 0:
            log.append(f"10:{i:02d} WARN slow query (8s)")
        else:
            log.append(f"10:{i:02d} INFO query ok")
    return {
        f"incident/2026/11/10/{server}.log": "10:00 ERROR replica lag\n10:05 ERROR replica lag\n10:09 INFO recovered",
        f"incident/2026/11/11/{server}.log": "10:00 INFO query ok\n10:20 ERROR connection reset",
        "incident/2026/11/12/horizon-db-01.log": "10:00 INFO query ok\n10:01 ERROR connection reset",
        f"incident/2026/11/12/{server}.log": "\n".join(log),
        "incident/2026/11/12/horizon-tst.log": "10:00 INFO 200 /\n10:01 ERROR 500 /requests/new",
        "incident/README.txt": "Server logs, one folder per day: incident/<year>/<month>/<day>/<server>.log",
    }


def gen_auth_log():
    events = ([("Failed", "svc_horizon", "10.20.30.66")] * 14 + [("Failed", "root", "10.20.30.66")] * 6 +
              [("Failed", "root", "10.20.30.41")] * 3 + [("Failed", "analyst", "10.20.30.47")] * 2 +
              [("Failed", "admin", "10.20.30.41")] * 4)
    random.Random(21).shuffle(events)
    events.insert(10, ("Accepted", "analyst", "10.20.30.47"))
    events.append(("Accepted", "svc_horizon", "10.20.30.66"))
    return "\n".join(f"Nov 12 01:{i * 2 // 60:02d}:{i * 2 % 60:02d} linuxip sshd[{2400 + i}]: {k} password for {u} from {ip}"
                     for i, (k, u, ip) in enumerate(events))


def gen_sprint():
    rng = random.Random(9)
    comps = ["workflow"] * 11 + ["workflow-ui"] * 6 + ["sso"] * 9 + ["requests"] * 10 + ["reports"] * 8
    rng.shuffle(comps)
    rows = ["ticket,component,points"]
    for i, comp in enumerate(comps):
        rows.append(f"HZN-{1200 + i},{comp},{21 if i == 23 else rng.choice([1, 2, 3, 5, 8, 13])}")
    return "\n".join(rows)


WORKFLOW_LINES = [l for l in gen_sprint().splitlines() if ",workflow," in l]


# ---------------------------------------------------------------- setup functions (git, venv)
def wf(g, rel, text):
    path = HOME + "/" + rel
    g.fs.mkdirs(g.fs.parent(path))
    g.fs.write(path, text)


def setup_702(g):
    venv = HOME + "/horizon/.venv"
    wf(g, "horizon/.venv/bin/activate", "# This file must be used with \"source bin/activate\"")
    wf(g, "horizon/.venv/pyvenv.cfg", "home = /usr/bin\nversion = 3.12.3")
    g.fs.mkdirs(venv + "/lib/python3.12/site-packages")
    g.installed[venv] = parse_requirements(REQUIREMENTS)


def setup_703(g):
    g.git_init(HOME + "/horizon")
    wf(g, "horizon/README.md", "# POPMAPS\nInternal stage-gate app.")
    wf(g, "horizon/app/routes.py", "def projects():\n    return list_projects()")
    wf(g, "horizon/app/models.py", "class Project: ...\nclass Request: ...")
    g.git_commit_all("Initial Horizon import")
    wf(g, "horizon/app/roles.py", 'ROLES = ["admin", "approver", "viewer", "requestor"]')
    g.git_commit_all("Add requestor role")
    wf(g, "horizon/app/forms.py", "trademark_bu = SelectField('Trademark BU')")
    g.git_commit_all("Add trademark BU dropdown")
    wf(g, "horizon/README.md", "# Horizon\nInternal stage-gate app (formerly POPMAPS).")
    g.git_commit_all("Rename POPMAPS to Horizon")
    g.git_switch("feature/requestor-role", create=True)
    wf(g, "horizon/app/gates.py", "def submit_gate_01(request, user):\n    check_role(user, 'requestor')")
    g.git_commit_all("Requestor can submit Gate 01")
    wf(g, "horizon/app/routes.py", "def projects():\n    return list_projects()\n\n"
                                  "def my_requests():\n    return list_requests(owner=current_user)")
    wf(g, "horizon/notes_meeting.txt", "Ask the tech lead about Gate 02 rules")


def setup_704(g):
    g.git_init(HOME + "/horizon")
    wf(g, "horizon/README.md", "# Horizon\nInternal stage-gate app.")
    wf(g, "horizon/app/routes.py", "def requests_new(): ...")
    for n, name in ((38, "add_requestor_role"), (39, "add_scope"), (40, "add_trademark_bu"), (41, "add_bu_dropdown")):
        wf(g, f"horizon/migrations/00{n}_{name}.py", f"# migration {n}")
    g.git_commit_all("Initial Horizon import")
    wf(g, "horizon/requirements.txt", REQUIREMENTS)
    g.git_commit_all("Pin requirements")
    g.mark["main_len"] = len(g.repo["branches"]["main"])


def setup_705(g):
    g.git_init(HOME + "/horizon")
    wf(g, "horizon/config/tst.py", 'DB_HOST = "horizon-db-02"\nDB_NAME = "horizon_tst"')
    wf(g, "horizon/app/sso.py", "# SSO placeholder")
    wf(g, "horizon/requirements.txt", REQUIREMENTS)
    g.git_commit_all("Initial Horizon import")
    g.git_switch("feature/sso", create=True)
    wf(g, "horizon/app/sso.py", "def saml_login():\n    return redirect(idp_url())")
    g.git_commit_all("Add SAML login")
    wf(g, "horizon/requirements.txt", REQUIREMENTS + "\nrequests==2.32.3")
    g.git_add(["requirements.txt"])
    wf(g, "horizon/config/tst.py", 'DB_HOST = "popmaps-db-01"\nDB_NAME = "horizon_tst"')


# ---------------------------------------------------------------- first-level hints (no commands, no answers)
NUDGES = {
    "HZN-101": "The welcome file tells you where to look next.",
    "HZN-102": "Each environment has its own config file. Ignore the legacy folder.",
    "HZN-103": "Hidden files start with a dot. Look inside the project folder for them.",
    "HZN-104": "Go to the features folder first. One mkdir option creates a folder and its subfolder at once.",
    "HZN-105": "Four separate jobs: copy, rename, delete files by pattern, delete a folder.",
    "HZN-106": "One redirect creates/overwrites a file, the other adds at the end. Quote text with *.",
    "HZN-207": "Search by file name in all subfolders, then open the one that is not in old/.",
    "HZN-208": "Search inside every file of the application code for the marker text.",
    "HZN-209": "Show the lines with the error status code, then hide the monitoring tests.",
    "HZN-210": "The newest entry is the last line of the file.",
    "HZN-211": "Count the FAILED lines, but make sure XFAILED is not counted.",
    "HZN-312": "Take only the number column, sort it, and show what repeats.",
    "HZN-313": "Keep only the error lines first, then count by path.",
    "HZN-314": "Read the script, make it executable, run it and save its output.",
    "HZN-415": "Find the replicas in /etc/hosts and test each one.",
    "HZN-416": "Hide the resolved alerts, then look up the remaining IP.",
    "HZN-517": "Call the token URL and read what the error asks for.",
    "HZN-518": "Call the endpoint without a token first: the error says which header to add.",
    "HZN-519": "Save the API output to a file, then count exact role matches.",
    "HZN-520": "Find today's log of that server, then count the ERROR lines.",
    "HZN-701": "Work inside the project folder, in this order: create the venv, activate it, install, run.",
    "HZN-702": "flask run tells you which variable is missing. .env.example shows the values.",
    "HZN-703": "Go into the project folder. One git command answers the first two steps.",
    "HZN-704": "Create the branch BEFORE you write and commit the file.",
    "HZN-705": "Compare what is staged with what is not staged.",
    "HZN-621": "Search the templates for the form; list the migrations to see the last number.",
    "HZN-622": "Filter the failed lines, take the user field and rank them. Then look at the successful one.",
    "HZN-623": "Test every Horizon server, then search the load balancer configs for the one that is down.",
    "HZN-624": "Include the commas in your search so workflow-ui does not match.",
    "HZN-625": "Use the token on the incidents API and keep lines with both critical and open.",
}


# ---------------------------------------------------------------- data for the text-tools and server tickets
def gen_export():
    """A ticket export from Windows: every line ends with \\r\\n."""
    rng = random.Random(3)
    owners = ["ana", "bruno", "carla", "dev", "elena"]
    rows = ["id,owner,status"]
    for i in range(30):
        rows.append(f"{2100 + i},{rng.choice(owners)},{rng.choice(['open', 'closed', 'closed', 'review'])}")
    return rows


EXPORT_ROWS = gen_export()
EXPORT_OPEN = str(sum(r.endswith(",open") for r in EXPORT_ROWS))
EXPORT_TEXT = "\r\n".join(EXPORT_ROWS)

TST_CONFIG = 'DB_HOST = "horizon-db-02"\nDB_URL = "mysql+pymysql://horizon@horizon-db-02/horizon_tst"\nDB_NAME = "horizon_tst"\nDEBUG = True'
TST_CONFIG_NEW = TST_CONFIG.replace("horizon-db-02", "horizon-db-new")


def gen_traffic():
    rng = random.Random(21)
    rows = ([("10.20.30.66", "/api/projects/NPI-999", 404)] * 7 + [("10.20.30.41", "/api/gates/77", 404)] * 3 +
            [("10.20.30.12", "/api/users/5", 404)] * 2 + [("10.20.30.66", "/api/health", 200)] * 2 +
            [(f"10.20.30.{5 + i % 6}", "/api/projects/404", 200) for i in range(3)] +
            [(f"10.20.30.{5 + i % 7}", "/api/health", 200) for i in range(22)] +
            [(f"10.20.30.{5 + i % 4}", "/api/requests", 500) for i in range(4)])
    rng.shuffle(rows)
    return [f"{ip} GET {path} {status} {10 + (i * 7) % 83}ms" for i, (ip, path, status) in enumerate(rows)]


TRAFFIC = gen_traffic()
TRAFFIC_404 = str(sum(l.split()[3] == "404" for l in TRAFFIC))
TRAFFIC_SUM = str(sum(int(l.split()[4][:-2]) for l in TRAFFIC if l.startswith("10.20.30.66 ")))


def gen_costs():
    rng = random.Random(5)
    rows = ["service,environment,eur"]
    for svc in ("compute", "database", "storage", "network", "monitoring"):
        for env in ("dev", "tst", "prd"):
            rows.append(f"{svc},{env},{rng.randrange(40, 900, 10) * (3 if svc == 'database' else 1)}")
    return rows


COSTS = gen_costs()
_prd = sum(int(r.split(",")[2]) for r in COSTS[1:] if r.split(",")[1] == "prd")
_by_service = {}
for _r in COSTS[1:]:
    _s, _, _v = _r.split(",")
    _by_service[_s] = _by_service.get(_s, 0) + int(_v)
COSTS_PRD = str(_prd)
COSTS_TOP = max(_by_service, key=_by_service.get)

DF_PRD = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        63G   31G   30G  51% /
/dev/sdb1        20G   20G     0 100% /var/log
tmpfs           3.9G     0  3.9G   0% /dev/shm"""
DF_OK = """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        63G   22G   38G  37% /
/dev/sdb1        20G  3.1G   16G  17% /var/log
tmpfs           3.9G     0  3.9G   0% /dev/shm"""
LOGDIR_PRD = """total 8231228
-rw-r--r-- 1 horizon horizon      48211 Nov 12 09:00 app.log
-rw-r--r-- 1 horizon horizon 8429356811 Nov 12 09:00 debug.log
-rw-r--r-- 1 horizon horizon      91234 Nov 11 23:59 app.log.1"""


def setup_417(g):
    g.remote = {"horizon-prd": {"df -h": DF_PRD, "ls -l /var/log/horizon": LOGDIR_PRD},
                "horizon-tst": {"df -h": DF_OK}}


def setup_801(g):
    g.procs.update({
        4010: {"user": HOME.rsplit("/", 1)[-1], "cpu": 1.2, "mem": 2.3, "cmd": "/usr/bin/python3 -m flask run --port 5050", "start": "08:57"},
        4127: {"user": HOME.rsplit("/", 1)[-1], "cpu": 97.3, "mem": 4.1, "cmd": "/usr/bin/python3 scripts/report_worker.py",
               "start": "07:12", "stubborn": True},
        4200: {"user": HOME.rsplit("/", 1)[-1], "cpu": 2.1, "mem": 3.0, "cmd": "node webpack --watch", "start": "08:41"},
        640: {"user": "mysql", "cpu": 3.4, "mem": 9.8, "cmd": "/usr/sbin/mysqld", "start": "Nov01"},
    })


def setup_802(g):
    g.fs.set_mode(HOME + "/horizon/.env", 0o666)
    g.fs.set_mode(HOME + "/horizon/scripts/deploy.sh", 0o644)
    g.fs.set_mode(HOME + "/horizon/config/prd.py", 0o666)


def readable_conf(g):
    return bool(g.fs.mode(HOME + "/horizon/api.conf") & 0o400)


def setup_803(g):
    path = HOME + "/horizon/api.conf"
    g.fs.set_mode(path, 0o200)
    denied = f"ERROR cannot read {path}: Permission denied"
    g.svc["horizon-api"] = {
        "desc": "Horizon API (Flask)", "state": "failed", "pid": 4410,
        "exec": HOME + "/horizon/.venv/bin/flask run --port 5050",
        "journal": [("08:58:40", "Started Horizon API (Flask)."), ("08:58:41", denied),
                    ("08:58:41", "horizon-api.service: Main process exited, code=exited, status=1/FAILURE"),
                    ("08:58:41", "horizon-api.service: Failed with result 'exit-code'.")],
        "start": lambda gg: [] if readable_conf(gg) else [denied, "horizon-api.service: Failed with result 'exit-code'."]}


def setup_805(g):
    setup_702(g)
    g.env.update({"DB_HOST": "localhost", "DB_NAME": "horizon_dev"})
    g.procs[4388] = {"user": HOME.rsplit("/", 1)[-1], "cpu": 0.1, "mem": 0.6, "cmd": "python3 -m http.server 5050", "start": "08:20"}
    g.listen[5050] = 4388
