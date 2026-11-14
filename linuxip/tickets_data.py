"""Generated files and setup functions used by the tickets (log files, CSVs, git history...)."""
import random

from .core import HOME, parse_requirements

REQUIREMENTS = """Flask==3.0.3
PyMySQL==1.1.1
SQLAlchemy==2.0.36
alembic==1.14.0
python-dotenv==1.0.1"""

DEPLOY_SH = """#!/bin/bash
# Pre-deploy check for Atlas
echo "== Atlas pre-deploy check =="
echo "Checking database..."
ping -c 2 atlas-db-02
echo "Checking API..."
ping -c 2 atlas-api
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
        "incident/2026/11/12/atlas-db-01.log": "10:00 INFO query ok\n10:01 ERROR connection reset",
        f"incident/2026/11/12/{server}.log": "\n".join(log),
        "incident/2026/11/12/atlas-tst.log": "10:00 INFO 200 /\n10:01 ERROR 500 /requests/new",
        "incident/README.txt": "Server logs, one folder per day: incident/<year>/<month>/<day>/<server>.log",
    }


def gen_auth_log():
    events = ([("Failed", "svc_atlas", "10.20.30.66")] * 14 + [("Failed", "root", "10.20.30.66")] * 6 +
              [("Failed", "root", "10.20.30.41")] * 3 + [("Failed", "analyst", "10.20.30.47")] * 2 +
              [("Failed", "admin", "10.20.30.41")] * 4)
    random.Random(21).shuffle(events)
    events.insert(10, ("Accepted", "analyst", "10.20.30.47"))
    events.append(("Accepted", "svc_atlas", "10.20.30.66"))
    return "\n".join(f"Nov 12 01:{i * 2 // 60:02d}:{i * 2 % 60:02d} linuxip sshd[{2400 + i}]: {k} password for {u} from {ip}"
                     for i, (k, u, ip) in enumerate(events))


def gen_sprint():
    rng = random.Random(9)
    comps = ["workflow"] * 11 + ["workflow-ui"] * 6 + ["sso"] * 9 + ["requests"] * 10 + ["reports"] * 8
    rng.shuffle(comps)
    rows = ["ticket,component,points"]
    for i, comp in enumerate(comps):
        rows.append(f"ATL-{1200 + i},{comp},{21 if i == 23 else rng.choice([1, 2, 3, 5, 8, 13])}")
    return "\n".join(rows)


WORKFLOW_LINES = [l for l in gen_sprint().splitlines() if ",workflow," in l]


# ---------------------------------------------------------------- setup functions (git, venv)
def wf(g, rel, text):
    path = HOME + "/" + rel
    g.fs.mkdirs(g.fs.parent(path))
    g.fs.write(path, text)


def setup_702(g):
    venv = HOME + "/atlas/.venv"
    wf(g, "atlas/.venv/bin/activate", "# This file must be used with \"source bin/activate\"")
    wf(g, "atlas/.venv/pyvenv.cfg", "home = /usr/bin\nversion = 3.12.3")
    g.fs.mkdirs(venv + "/lib/python3.12/site-packages")
    g.installed[venv] = parse_requirements(REQUIREMENTS)


def setup_703(g):
    g.git_init(HOME + "/atlas")
    wf(g, "atlas/README.md", "# COMPASS\nInternal stage-gate app.")
    wf(g, "atlas/app/routes.py", "def projects():\n    return list_projects()")
    wf(g, "atlas/app/models.py", "class Project: ...\nclass Request: ...")
    g.git_commit_all("Initial Atlas import")
    wf(g, "atlas/app/roles.py", 'ROLES = ["admin", "approver", "viewer", "requestor"]')
    g.git_commit_all("Add requestor role")
    wf(g, "atlas/app/forms.py", "trademark_bu = SelectField('Trademark BU')")
    g.git_commit_all("Add trademark BU dropdown")
    wf(g, "atlas/README.md", "# Atlas\nInternal stage-gate app (formerly COMPASS).")
    g.git_commit_all("Rename COMPASS to Atlas")
    g.git_switch("feature/requestor-role", create=True)
    wf(g, "atlas/app/gates.py", "def submit_gate_01(request, user):\n    check_role(user, 'requestor')")
    g.git_commit_all("Requestor can submit Gate 01")
    wf(g, "atlas/app/routes.py", "def projects():\n    return list_projects()\n\n"
                                  "def my_requests():\n    return list_requests(owner=current_user)")
    wf(g, "atlas/notes_meeting.txt", "Ask the tech lead about Gate 02 rules")


def setup_704(g):
    g.git_init(HOME + "/atlas")
    wf(g, "atlas/README.md", "# Atlas\nInternal stage-gate app.")
    wf(g, "atlas/app/routes.py", "def requests_new(): ...")
    for n, name in ((38, "add_requestor_role"), (39, "add_scope"), (40, "add_trademark_bu"), (41, "add_bu_dropdown")):
        wf(g, f"atlas/migrations/00{n}_{name}.py", f"# migration {n}")
    g.git_commit_all("Initial Atlas import")
    wf(g, "atlas/requirements.txt", REQUIREMENTS)
    g.git_commit_all("Pin requirements")
    g.mark["main_len"] = len(g.repo["branches"]["main"])


def setup_705(g):
    g.git_init(HOME + "/atlas")
    wf(g, "atlas/config/tst.py", 'DB_HOST = "atlas-db-02"\nDB_NAME = "atlas_tst"')
    wf(g, "atlas/app/sso.py", "# SSO placeholder")
    wf(g, "atlas/requirements.txt", REQUIREMENTS)
    g.git_commit_all("Initial Atlas import")
    g.git_switch("feature/sso", create=True)
    wf(g, "atlas/app/sso.py", "def saml_login():\n    return redirect(idp_url())")
    g.git_commit_all("Add SAML login")
    wf(g, "atlas/requirements.txt", REQUIREMENTS + "\nrequests==2.32.3")
    g.git_add(["requirements.txt"])
    wf(g, "atlas/config/tst.py", 'DB_HOST = "compass-db-01"\nDB_NAME = "atlas_tst"')


# ---------------------------------------------------------------- first-level hints (no commands, no answers)
NUDGES = {
    "ATL-101": "The welcome file tells you where to look next.",
    "ATL-102": "Each environment has its own config file. Ignore the legacy folder.",
    "ATL-103": "Hidden files start with a dot. Look inside the project folder for them.",
    "ATL-104": "Go to the features folder first. One mkdir option creates a folder and its subfolder at once.",
    "ATL-106": "Four separate jobs: copy, rename, delete files by pattern, delete a folder.",
    "ATL-107": "One redirect creates/overwrites a file, the other adds at the end. Quote text with *.",
    "ATL-108": "Search by file name in all subfolders, then open the one that is not in old/.",
    "ATL-109": "Search inside every file of the application code for the marker text.",
    "ATL-110": "Show the lines with the error status code, then hide the monitoring tests.",
    "ATL-111": "The newest entry is the last line of the file.",
    "ATL-112": "Count the FAILED lines, but make sure XFAILED is not counted.",
    "ATL-114": "Take only the number column, sort it, and show what repeats.",
    "ATL-115": "Keep only the error lines first, then count by path.",
    "ATL-116": "Read the script, make it executable, run it and save its output.",
    "ATL-122": "Find the replicas in /etc/hosts and test each one.",
    "ATL-123": "Hide the resolved alerts, then look up the remaining IP.",
    "ATL-125": "Call the token URL and read what the error asks for.",
    "ATL-126": "Call the endpoint without a token first: the error says which header to add.",
    "ATL-127": "Save the API output to a file, then count exact role matches.",
    "ATL-128": "Find today's log of that server, then count the ERROR lines.",
    "ATL-129": "Work inside the project folder, in this order: create the venv, activate it, install, run.",
    "ATL-130": "flask run tells you which variable is missing. .env.example shows the values.",
    "ATL-131": "Go into the project folder. One git command answers the first two steps.",
    "ATL-132": "Create the branch BEFORE you write and commit the file.",
    "ATL-133": "Compare what is staged with what is not staged.",
    "ATL-143": "Search the templates for the form; list the migrations to see the last number.",
    "ATL-144": "Filter the failed lines, take the user field and rank them. Then look at the successful one.",
    "ATL-145": "Test every Atlas server, then search the load balancer configs for the one that is down.",
    "ATL-146": "Include the commas in your search so workflow-ui does not match.",
    "ATL-147": "Use the token on the incidents API and keep lines with both critical and open.",
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

TST_CONFIG = 'DB_HOST = "atlas-db-02"\nDB_URL = "mysql+pymysql://atlas@atlas-db-02/atlas_tst"\nDB_NAME = "atlas_tst"\nDEBUG = True'
TST_CONFIG_NEW = TST_CONFIG.replace("atlas-db-02", "atlas-db-new")


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
-rw-r--r-- 1 atlas atlas      48211 Nov 12 09:00 app.log
-rw-r--r-- 1 atlas atlas 8429356811 Nov 12 09:00 debug.log
-rw-r--r-- 1 atlas atlas      91234 Nov 11 23:59 app.log.1"""


def setup_417(g):
    g.remote = {"atlas-prd": {"df -h": DF_PRD, "ls -l /var/log/atlas": LOGDIR_PRD},
                "atlas-tst": {"df -h": DF_OK}}


def setup_801(g):
    g.procs.update({
        4010: {"user": HOME.rsplit("/", 1)[-1], "cpu": 1.2, "mem": 2.3, "cmd": "/usr/bin/python3 -m flask run --port 5050", "start": "08:57"},
        4127: {"user": HOME.rsplit("/", 1)[-1], "cpu": 97.3, "mem": 4.1, "cmd": "/usr/bin/python3 scripts/report_worker.py",
               "start": "07:12", "stubborn": True},
        4200: {"user": HOME.rsplit("/", 1)[-1], "cpu": 2.1, "mem": 3.0, "cmd": "node webpack --watch", "start": "08:41"},
        640: {"user": "mysql", "cpu": 3.4, "mem": 9.8, "cmd": "/usr/sbin/mysqld", "start": "Nov01"},
    })


def setup_802(g):
    g.fs.set_mode(HOME + "/atlas/.env", 0o666)
    g.fs.set_mode(HOME + "/atlas/scripts/deploy.sh", 0o644)
    g.fs.set_mode(HOME + "/atlas/config/prd.py", 0o666)


def readable_conf(g):
    return bool(g.fs.mode(HOME + "/atlas/api.conf") & 0o400)


def setup_803(g):
    path = HOME + "/atlas/api.conf"
    g.fs.set_mode(path, 0o200)
    denied = f"ERROR cannot read {path}: Permission denied"
    g.svc["atlas-api"] = {
        "desc": "Atlas API (Flask)", "state": "failed", "pid": 4410,
        "exec": HOME + "/atlas/.venv/bin/flask run --port 5050",
        "journal": [("08:58:40", "Started Atlas API (Flask)."), ("08:58:41", denied),
                    ("08:58:41", "atlas-api.service: Main process exited, code=exited, status=1/FAILURE"),
                    ("08:58:41", "atlas-api.service: Failed with result 'exit-code'.")],
        "start": lambda gg: [] if readable_conf(gg) else [denied, "atlas-api.service: Failed with result 'exit-code'."]}


def setup_805(g):
    setup_702(g)
    g.env.update({"DB_HOST": "localhost", "DB_NAME": "atlas_dev"})
    g.procs[4388] = {"user": HOME.rsplit("/", 1)[-1], "cpu": 0.1, "mem": 0.6, "cmd": "python3 -m http.server 5050", "start": "08:20"}
    g.listen[5050] = 4388


NUDGES.update({
    "ATL-139": "A for loop can walk through the names. ping succeeds or fails: use && and || to print up or down.",
    "ATL-140": "List with find first. Archive with tar, pasting find's answer in with $( ). Delete only after the archive exists.",
    "ATL-141": "readlink shows the target. To replace a link that points to a folder you need an extra ln option.",
    "ATL-142": "Two streams: output and errors. One redirect each, or send the errors to the same place as the output.",
    "ATL-105": "Two jobs: copy the three files into the backup folder, then move the migration to its new name.",
    "ATL-113": "One grep option lists only file names. Another limits the search to files with a certain name pattern.",
    "ATL-117": "Look at the file with a command that shows hidden characters. One command can delete a given character.",
    "ATL-118": "There is a command that compares two files line by line. Lines with < and > are the differences.",
    "ATL-119": "Backup first. Then sed can replace text inside a file: look at its option for changing the file itself.",
    "ATL-120": "awk can test one column and print another. For the total, add the column up and print it at the END.",
    "ATL-121": "Tell awk the columns are separated by commas. A total per name needs an array.",
    "ATL-124": "You can run one command on another server through ssh. Ask it about its disks first.",
    "ATL-134": "List all processes with their CPU use, then sort by that column. Stopping a process needs its number.",
    "ATL-135": "The long listing shows permissions. Three digits set them for owner, group and everybody else.",
    "ATL-136": "Ask the service how it is doing, then read its log. The cause is written there.",
    "ATL-137": "One tar command creates the archive, another lists it, a third extracts into a folder.",
    "ATL-138": "Activate the venv inside the project folder, start it and read the error. Then find which process listens on that port.",
})


HOST_REPORT = ["atlas-api up", "atlas-tst up", "atlas-pre down", "atlas-prd up", "atlas-db-01 down", "atlas-db-02 up"]
LOG_BIG = "\n".join(f"2026-11-12 08:{i:02d}:00 INFO request handled" for i in range(60))
LOG_SMALL = "2026-11-12 08:00:00 INFO ok"
BIG_LOGS = ["logs/app-1.log", "logs/app-3.log", "logs/app-5.log"]
NIGHTLY = '#!/bin/bash\necho "backup started"\nls /nonexistent\necho "backup finished"'
NIGHTLY_ERROR = "ls: cannot access '/nonexistent': No such file or directory"


def setup_release(g):
    g.fs.links[HOME + "/current"] = "releases/v1.8.2"


def setup_nightly(g):
    g.fs.set_mode(HOME + "/nightly.sh", 0o755)
