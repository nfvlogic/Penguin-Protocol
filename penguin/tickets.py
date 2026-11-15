"""The 50 Atlas tickets (the story around them is in missions.py). Edit this file to change or add tickets.

Each ticket has either an `answer` (submit it), `checks` (completes by itself) or
`parts` (several steps; a step goal is an answer string/tuple or a check function).

RULE FOR CARDS: examples ("e.g. ...") must use OTHER files, folders and hosts than the
ticket, and must never contain an answer. tests/test_penguin.py checks this automatically.
"""
from .cmd_dev import ghash
from .cmd_sys import tar_members
from .core import API, HOME, TOKEN
from .tickets_data import (DU_FILES, DU_UPLOADS, BIG_LOGS, HOST_REPORT, LOG_BIG, LOG_SMALL, NIGHTLY, NIGHTLY_ERROR, setup_nightly, setup_release,  # noqa: F401
                           COSTS, COSTS_PRD, COSTS_TOP, DEPLOY_SH, EXPORT_ROWS, EXPORT_OPEN, EXPORT_TEXT,  # noqa: F401
                           NUDGES, REQUIREMENTS, TRAFFIC, TRAFFIC_404, TRAFFIC_SUM, TST_CONFIG, TST_CONFIG_NEW,
                           WORKFLOW_LINES, gen_access, gen_app_log, gen_auth_log, gen_deploy_log, gen_incident,
                           gen_migrations, gen_sprint, gen_test_report, readable_conf, setup_417, setup_702,
                           setup_703, setup_704, setup_705, setup_801, setup_802, setup_803, setup_805)


# ---------------------------------------------------------------- check helpers
def home_file(rel):
    return lambda g: g.fs.isfile(HOME + "/" + rel)


def home_dir(rel):
    return lambda g: g.fs.isdir(HOME + "/" + rel)


def gone(rel):
    return lambda g: not g.fs.exists(HOME + "/" + rel)


def content(rel, expected):
    return lambda g: [l.rstrip() for l in g.fs.d.get(HOME + "/" + rel, "").strip().split("\n")] == expected


def no_ext(ext, folder=""):
    return lambda g: not any(n.endswith(ext) for n, _ in g.fs.children((HOME + "/" + folder).rstrip("/")))


def task(module, ticket, name, prio, frm, brief, done, cmds, files=None, answer=None,
         checks=None, hint="", parts=None, setup=None):
    return {"module": module, "ticket": ticket, "name": name, "prio": prio, "from": frm, "brief": brief,
            "done": done, "cmds": cmds, "files": files or {}, "answer": answer, "checks": checks,
            "hint": hint, "parts": parts, "setup": setup}


# Commands used on many cards: (syntax, explanation, example with OTHER names)
LS = ("ls [FOLDER]", "list the files in a folder", "ls reports")
CAT = ("cat FILE", "show what is inside a file", "cat notes.md")
CD = ("cd FOLDER", "go into a folder; cd .. goes up, cd ~ goes home", "cd projects")
TREE = ("tree FOLDER", "show all folders and files below a folder", "tree projects")
SUBMIT = ("submit ANSWER", "send what you found to close the ticket", "submit abc-123")
CHECK = ("check", "see which requirements are done", "check")
PING = ("ping -c N HOST", "send N packets: replies = online, no reply = down", "ping -c 3 gateway")

LEVELS = [
    # ------------------------------------------------------------ ONBOARDING
    task("Onboarding", "ATL-101", "Run Atlas locally", "Normal", "Tech lead",
         ["Welcome to the Atlas team! Atlas is our internal stage-gate app (Flask + MySQL). "
          "Before you pick up feature work, you need to run it on your machine.",
          "Start with the welcome file in your home folder: it tells you where the project "
          "documentation is. Find the port the app uses when you run it locally."],
         "You submit the local port number.",
         [LS, CAT, CD, SUBMIT],
         {"welcome.txt": "Welcome to the Atlas team!\nThe code is in ~/atlas. Start with README.md there.",
          "notes.txt": "Old note: COMPASS used port 8080. Not valid any more.",
          "atlas/README.md": "# Atlas\nInternal stage-gate app (Flask + MySQL). Formerly COMPASS.\n\n"
                               "Run locally:\n  flask run --port 5050\n\nMore setup help: docs/setup.md",
          "atlas/docs/setup.md": "1. Create a virtual env\n2. Install requirements\n3. Run (see README)"},
         answer="5050", hint="cat welcome.txt ; cd atlas ; cat README.md"),
    task("Onboarding", "ATL-102", "Which database does TST use?", "Normal", "Platform team",
         ["We are moving TST to a new database server and need to confirm what the code is "
          "configured to use today.",
          "Each environment has its own config file in the project. There is also an old "
          "config folder left over from COMPASS: the README says if it is still valid."],
         "You submit the DB_HOST used by the TST environment.",
         [TREE, CD, ("cd ..", "go up one folder", "cd .."), ("pwd", "show the folder you are in", "pwd"), CAT, SUBMIT],
         {"atlas/README.md": "# Atlas\nConfig per environment lives in config/ (dev.py, tst.py, prd.py).\n"
                               "config/legacy/ is the old COMPASS setup - do not use.",
          "atlas/config/dev.py": 'DB_HOST = "localhost"\nDB_NAME = "atlas_dev"',
          "atlas/config/tst.py": 'DB_HOST = "atlas-db-02"\nDB_NAME = "atlas_tst"',
          "atlas/config/prd.py": 'DB_HOST = "atlas-db-03"\nDB_NAME = "atlas"',
          "atlas/config/legacy/tst.py": 'DB_HOST = "compass-db-01"  # deprecated'},
         answer="atlas-db-02", hint="tree atlas ; cat atlas/config/tst.py"),
    task("Onboarding", "ATL-103", "App fails to start", "High", "Tech lead",
         ["Your local Atlas crashes on start-up with: Unknown database 'compass_dev'. "
          "Somebody started it with an old environment file.",
          "Flask loads settings from hidden files (names that start with a dot) in the project "
          "folder. Find the file that holds the database settings and the correct database "
          "name. The hidden file in your home folder is the OLD one.",
          "How: go into the project folder ~/atlas and list ALL its files with ls -a (a plain ls hides "
          "names that start with a dot). One hidden file points to the other one that holds the settings. "
          "Open it with cat and read the line DB_NAME=...  The answer is only the value after the = sign."],
         "You submit the correct DB_NAME: only the value after the = sign (from the project's settings file, not the old one in your home folder).",
         [("ls -a [FOLDER]", "list ALL files, hidden ones (.name) too", "ls -a reports"), CD, CAT,
          ("cd ~", "go back to your home folder", "cd ~"), SUBMIT],
         {"atlas/.flaskenv": "FLASK_APP=wsgi.py\n# DB settings and secrets are loaded from .env in this folder",
          "atlas/start.log": "09:00 starting Atlas\n09:00 ERROR (1049) Unknown database 'compass_dev'",
          "atlas/.env": "DB_HOST=localhost\nDB_NAME=atlas_dev\nDB_USER=atlas\nSECRET_KEY=change-me",
          "atlas/wsgi.py": "from app import create_app\napp = create_app()",
          ".env.old": "DB_NAME=compass_dev   # old app name, do not use"},
         answer="atlas_dev", hint="cd atlas ; ls -a ; cat .flaskenv ; cat .env"),
    task("Onboarding", "ATL-104", "Scaffold the Launch date feature", "Normal", "Product owner",
         ["New feature: requestors must enter a desired launch date. Create the empty feature "
          "module so the team can start coding.",
          "Inside ~/atlas/app/features create: a folder launch_date with an empty __init__.py, "
          "an empty routes.py, a subfolder templates, and README.md containing exactly: "
          "Launch date field",
          "Note: plain mkdir only creates one level, and fails if the parent does not exist."],
         "The structure exists. Closes by itself (type check).",
         [CD, ("mkdir -p A/B", "make a folder and any missing parent folders", "mkdir -p reports/2026/q4"),
          ("touch FILE...", "create one or more empty files", "touch a.txt b.txt"),
          ("echo TEXT > FILE", "write text into a file", "echo hello > note.txt"), TREE, CHECK],
         {"atlas/app/__init__.py": "", "atlas/app/features/": ""},
         checks=[("launch_date/__init__.py exists", home_file("atlas/app/features/launch_date/__init__.py")),
                 ("launch_date/routes.py exists", home_file("atlas/app/features/launch_date/routes.py")),
                 ("launch_date/templates/ exists", home_dir("atlas/app/features/launch_date/templates")),
                 ("README.md says: Launch date field",
                  content("atlas/app/features/launch_date/README.md", ["Launch date field"]))],
         hint="cd atlas/app/features ; mkdir -p launch_date/templates ; touch launch_date/__init__.py "
              "launch_date/routes.py ; echo Launch date field > launch_date/README.md"),
    task("Onboarding", "ATL-105", "Back up the configs", "Normal", "Tech lead",
         ["Your pull request was blocked, and before it is cleaned up there are two preparations: keep a "
          "copy of the config files, and give a migration a proper name.",
          "Copy the 3 files in atlas/config into the folder ~/backup (it already exists). Then rename "
          "atlas/migrations/draft.py to 0040_add_trademark_bu.py. Linux has no rename command: moving "
          "a file to a new name is renaming it."],
         "Both requirements are met. Closes by itself (type check).",
         [LS, ("cp FILE... FOLDER", "copy one or more files into a folder", "cp a.txt b.txt archive/"),
          ("mv OLD NEW", "rename (or move) a file", "mv old.txt new.txt"), CHECK],
         {"atlas/config/dev.py": "DEBUG = True", "atlas/config/tst.py": "DEBUG = False",
          "atlas/config/prd.py": "DEBUG = False",
          "atlas/migrations/0039_add_scope.py": "add_column('request', 'scope')",
          "atlas/migrations/draft.py": "add_column('request', 'trademark_bu')", "backup/": ""},
         checks=[("3 config files are in ~/backup",
                  lambda g: all(g.fs.isfile(f"{HOME}/backup/{e}.py") for e in ("dev", "tst", "prd"))),
                 ("migration renamed to 0040_add_trademark_bu.py",
                  lambda g: g.fs.isfile(HOME + "/atlas/migrations/0040_add_trademark_bu.py")
                  and not g.fs.exists(HOME + "/atlas/migrations/draft.py"))],
         hint="cp atlas/config/dev.py atlas/config/tst.py atlas/config/prd.py backup/ ; "
              "mv atlas/migrations/draft.py atlas/migrations/0040_add_trademark_bu.py"),
    task("Onboarding", "ATL-106", "Clean the repo before the PR", "High", "Code review bot",
         ["The pull request is still blocked: it contains compiled files. Delete every .pyc file directly "
          "in ~/atlas, and delete the folder atlas/__pycache__.",
          "The shell expands * before the command runs: a pattern like reports/*.txt becomes "
          "the list of every matching file. Preview it with echo before you delete."],
         "No .pyc files are left and __pycache__ is gone. Closes by itself (type check).",
         [("echo PATTERN", "preview what a * pattern expands to", "echo reports/*.tmp"),
          ("rm PATTERN", "delete every file that matches a pattern", "rm reports/*.tmp"),
          ("rm -r FOLDER", "delete a folder and everything in it", "rm -r old_reports"), CHECK],
         {"atlas/app.pyc": "x", "atlas/utils.pyc": "x", "atlas/wsgi.pyc": "x", "atlas/wsgi.py": "app = create_app()",
          "atlas/__pycache__/app.cpython-312.pyc": "x"},
         checks=[("no .pyc files left in ~/atlas", no_ext(".pyc", "atlas")),
                 ("atlas/__pycache__ deleted", gone("atlas/__pycache__"))],
         hint="rm atlas/*.pyc ; rm -r atlas/__pycache__"),
    task("Onboarding", "ATL-107", ".gitignore and changelog", "Normal", "Tech lead",
         ["So this never happens again, create atlas/.gitignore with these 3 lines in order: "
          "__pycache__/  then  *.pyc  then  .env",
          "And add one line at the END of atlas/CHANGELOG.md (do not erase it): "
          "- Added launch date field (ATL-104)",
          "Put text with * or spaces in quotes, so the shell passes it unchanged."],
         "Both files are correct. Closes by itself (type check).",
         [("echo TEXT > FILE", "write a file (overwrites it!)", "echo first > list.txt"),
          ("echo TEXT >> FILE", "add a line at the end of a file", 'echo "second line" >> list.txt'),
          CAT, CHECK],
         {"atlas/CHANGELOG.md": "# Changelog\n- Renamed COMPASS to Atlas\n- Added requestor role"},
         checks=[(".gitignore has the 3 lines", content("atlas/.gitignore", ["__pycache__/", "*.pyc", ".env"])),
                 ("CHANGELOG.md kept its lines and has the new one at the end",
                  content("atlas/CHANGELOG.md", ["# Changelog", "- Renamed COMPASS to Atlas",
                                                   "- Added requestor role", "- Added launch date field (ATL-104)"]))],
         hint='echo __pycache__/ > atlas/.gitignore ; echo "*.pyc" >> atlas/.gitignore ; '
              'echo .env >> atlas/.gitignore ; echo "- Added launch date field (ATL-104)" >> atlas/CHANGELOG.md'),
    # ------------------------------------------------------------ CODE SEARCH
    task("Code search", "ATL-108", "Which gate rules are active?", "Normal", "QA team",
         ["QA reports that Gate approvals behave differently than documented. They need to know "
          "which version of the gate rules is running.",
          "Several files in the project have 'gate' in their name: code, an old copy, a test and "
          "a template. Only the one in app/workflow (not in old/) is active."],
         "You submit the RULES_VERSION of the active rules file.",
         [('find FOLDER -name "PATTERN"', "search names in all subfolders; quote the * pattern",
           'find projects -name "*.md"'),
          ("cat PATH", "read a file by its path", "cat projects/app/main.py"), SUBMIT],
         {"atlas/app/workflow/gate_rules.py": 'RULES_VERSION = "g2-310"\n\ndef approve_gate(project, gate):\n    ...',
          "atlas/app/workflow/old/gate_rules_v1.py": 'RULES_VERSION = "g1-100"  # replaced in October',
          "atlas/tests/test_gate_rules.py": "from app.workflow.gate_rules import approve_gate",
          "atlas/app/templates/gate.html": "<h1>Gate approval</h1>",
          "atlas/app/routes.py": "from .workflow import gate_rules"},
         answer="g2-310", hint='find atlas -name "*gate*" ; cat atlas/app/workflow/gate_rules.py'),
    task("Code search", "ATL-109", "Release blocker hunt", "High", "Release manager",
         ["Release v1.9 is on Friday. Developers mark blocking issues in the code with "
          "TODO(release-blocker). Find it without opening every file.",
          "Search only the application code (atlas/app). The docs also mention the marker "
          "as an example: that one does not count."],
         "You submit the FILE NAME (e.g. main.py) that contains the release blocker.",
         [("grep -r WORD FOLDER", "search every file in a folder", "grep -r FIXME projects"),
          ("grep -n WORD FILE", "show line numbers", "grep -n import main.py"), SUBMIT],
         {"atlas/app/routes.py": "def projects():\n    # TODO: add pagination\n    return []",
          "atlas/app/approvals.py": "def approve(request, user):\n"
                                      "    # TODO(release-blocker): Gate 01 approval skips the requestor check\n    return True",
          "atlas/app/models.py": "class Project:\n    # TODO: rename compass_id column\n    pass",
          "atlas/app/sso.py": "# TODO: remove password fallback after SSO go-live",
          "atlas/docs/contributing.md": "Mark blockers like this: TODO(release-blocker): <text>"},
         answer=("approvals.py", "atlas/app/approvals.py"), hint="grep -r release-blocker atlas/app"),
    task("Code search", "ATL-110", "500 errors on TST", "Critical", "QA team",
         ["Testers get an error page when they create a new request on TST. app.log has 160 "
          "lines from this morning. Monitoring also sends fake crashes every hour: those are "
          "marked as tests and are not real.",
          "Find the real endpoint that fails with HTTP 500. Remember: grep is case-sensitive, "
          "so 'error' does NOT match 'ERROR'."],
         "You submit the path of the failing endpoint (starts with /).",
         [("grep WORD FILE", "show lines containing a word (case-sensitive)", "grep WARN server.log"),
          ("grep -i WORD FILE", "same, ignoring upper/lower case", "grep -i warn server.log"),
          ("grep -v WORD", "hide lines containing a word", "grep -v DEBUG server.log"),
          ("a | b", "pipe: the output of a goes into b", "grep WARN server.log | grep -v disk"), SUBMIT],
         {"app.log": gen_app_log()}, answer="/requests/new", hint="grep 500 app.log | grep -v synthetic"),
    task("Code search", "ATL-111", "What is deployed on TST?", "Normal", "Product owner",
         ["The product owner asks which Atlas version is on TST right now. deploy.log has 240 "
          "lines with the newest entry at the bottom. The first line is the previous release."],
         "You submit the deployed version (e.g. v0.0.0).",
         [("wc -l FILE", "count the lines of a file", "wc -l server.log"),
          ("head -n N FILE", "show the first N lines", "head -n 3 server.log"),
          ("tail -n N FILE", "show the last N lines", "tail -n 3 server.log"), SUBMIT],
         {"deploy.log": gen_deploy_log()}, answer="v1.8.3", hint="tail -n 1 deploy.log"),
    task("Code search", "ATL-112", "Failing unit tests", "High", "CI pipeline",
         ["The CI pipeline is red. test_report.txt lists 40 tests. How many really failed?",
          "Careful: XFAILED means 'expected to fail' (a known issue) and does not count. grep "
          "matches text anywhere in a line, so FAILED is also found inside XFAILED."],
         "You submit the number of failed tests.",
         [("head -n N FILE", "look at the format", "head -n 6 results.txt"),
          ("grep -c TEXT FILE", "count matching lines", "grep -c OK results.txt"),
          ("grep -w WORD FILE", "match WORD only as a whole word, not inside a longer word",
           "grep -w cat animals.txt"), SUBMIT],
         {"test_report.txt": gen_test_report()}, answer="6",
         hint="grep -c FAILED also counts XFAILED. Use grep -cw FAILED test_report.txt"),
    task("Code search", "ATL-113", "Who reads the secret key?", "High", "Security team",
         ["Security wants to rotate the SECRET_KEY before go-live. First they need to know how many "
          "Python source files in the application code (atlas/app) use it.",
          "The word also appears in templates, docs and settings files: those do not count. Only "
          "list the files, do not print every matching line."],
         "You submit the number of .py files in atlas/app that mention SECRET_KEY.",
         [("grep -rl WORD FOLDER", "list only the NAMES of the files that contain a word", "grep -rl TODO projects"),
          ('grep -r WORD FOLDER --include="PATTERN"', "search only files whose name matches the pattern",
           'grep -r TODO projects --include="*.js"'),
          ("a | wc -l", "count the lines a command prints", "grep -rl TODO projects | wc -l"), SUBMIT],
         {"atlas/app/__init__.py": 'app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]',
          "atlas/app/auth.py": 'token = sign(current_app.config["SECRET_KEY"], user)',
          "atlas/app/sso.py": "# SSO uses its own keys; falls back to SECRET_KEY in dev\nkey = get_secret(\"SECRET_KEY\")",
          "atlas/app/routes.py": "def projects():\n    return list_projects()",
          "atlas/app/templates/admin.html": "<p>Rotate SECRET_KEY every 90 days</p>",
          "atlas/tests/test_auth.py": 'SECRET_KEY = "test"',
          "atlas/docs/security.md": "The SECRET_KEY must never be committed.",
          "atlas/.env": "SECRET_KEY=change-me"},
         answer="3", hint='grep -rl SECRET_KEY atlas/app --include="*.py" | wc -l'),
    # ------------------------------------------------------------ PIPES
    task("Pipes", "ATL-114", "Migration conflict", "High", "CI pipeline",
         ["Alembic refuses to upgrade: two developers created a migration with the same "
          "revision number. migrations_list.txt has one migration per line: <number> <name>.",
          "Find the duplicated revision number. Note: uniq only compares neighbour lines."],
         "You submit the duplicated revision number.",
         [('cut -d " " -f N FILE', "take one column (field N) of each line", 'cut -d " " -f 2 names.txt'),
          ("sort", "sort lines so equal lines end up together", "sort names.txt"),
          ("uniq -d", "show only lines that are repeated", "... | uniq -d"),
          ("a | b | c", "chain commands with pipes", "cat names.txt | sort | uniq -c"), SUBMIT],
         {"migrations_list.txt": gen_migrations()}, answer="0038",
         hint='cut -d " " -f 1 migrations_list.txt | sort | uniq -d'),
    task("Pipes", "ATL-115", "Which endpoint is broken?", "Critical", "Monitoring",
         ["access.log has today's API traffic. Find the endpoint with the most HTTP 500 errors. "
          "The busiest endpoint is the health check: that is normal, do not just count all lines.",
          "Line format: <ip> <method> <path> <status> <time>   (the path is field 3)"],
         "You submit the path of the endpoint with the most 500 errors.",
         [('grep " TEXT " FILE', "keep lines containing a text (spaces included)", 'grep " 404 " web.log'),
          ('cut -d " " -f N', "take one field of each line", '... | cut -d " " -f 1'),
          ("sort | uniq -c", "count how often each line appears", "... | sort | uniq -c"),
          ("sort -n -r", "sort by number, biggest first", "... | sort -n -r"),
          ("head -n N", "keep only the first N lines", "... | head -n 5"), SUBMIT],
         {"access.log": gen_access()}, answer="/api/requests",
         hint='grep " 500 " access.log | cut -d " " -f 3 | sort | uniq -c | sort -n -r | head -n 1'),
    task("Pipes", "ATL-116", "Pre-deploy check", "Normal", "Change board",
         ["Before tonight's deployment of v1.9, run the pre-deploy script deploy.sh and attach "
          "its output to the change request. Read it first: never run a script you have not "
          "looked at.",
          "Save its output in a file called deploy_check.log."],
         "deploy.sh is executable, ran, and deploy_check.log has its result. Closes by itself.",
         [("ls -l", "details: an x in -rwxr-xr-x means executable", "ls -l reports"),
          ("cat FILE", "see what a script will do", "cat backup.sh"),
          ("chmod +x FILE", "make a file executable", "chmod +x backup.sh"),
          ("./FILE > LOG", "run a script in this folder and save its output", "./backup.sh > backup.log"),
          ("./FILE | tee LOG", "same, but you also SEE the output on the screen", "./backup.sh | tee backup.log"), CHECK],
         {"deploy.sh": DEPLOY_SH},
         checks=[("deploy.sh is executable", lambda g: HOME + "/deploy.sh" in g.fs.x),
                 ("deploy.sh has run", lambda g: HOME + "/deploy.sh" in g.ran),
                 ("deploy_check.log contains the script's final OK line",
                  lambda g: "finished: OK" in g.fs.d.get(HOME + "/deploy_check.log", ""))],
         hint="cat deploy.sh ; chmod +x deploy.sh ; ./deploy.sh > deploy_check.log"),
    # ------------------------------------------------------------ TEXT TOOLS
    task("Text tools", "ATL-117", "Export from Windows", "Normal", "Scrum master",
         ["The scrum master exported tickets_export.csv from a Windows laptop. Counting the open tickets "
          "with grep gives 0, although the file clearly has some. Windows ends every line with a hidden "
          "extra character (a carriage return).",
          "Make a clean copy called clean.csv without that character, then count the tickets whose "
          "status (the last column) is open."],
         "clean.csv exists without the hidden characters and you submit the number of open tickets.",
         [("file FILE", "what kind of file it is (CRLF = Windows line endings)", "file report.txt"),
          ("cat -A FILE", "show hidden characters: ^M is the Windows character, $ marks the end of a line", "cat -A report.txt"),
          ("tr -d 'CHARS' < FILE > NEW", "copy a file, deleting characters (\\r = carriage return)", "tr -d ';' < in.txt > out.txt"),
          ("grep -c 'TEXT$' FILE", "count lines that END with the text", "grep -c 'red$' data.csv"), SUBMIT, CHECK],
         {"tickets_export.csv": EXPORT_TEXT},
         parts=[("Create clean.csv: the same lines, without the Windows characters (completes by itself)",
                 lambda g: g.fs.d.get(HOME + "/clean.csv", "\r").split("\n") == EXPORT_ROWS),
                ("How many tickets have the status open?", EXPORT_OPEN)],
         hint="tr -d '\\r' < tickets_export.csv > clean.csv ; grep -c ',open$' clean.csv"),
    task("Text tools", "ATL-118", "TST is not like PRD", "High", "QA team",
         ["A bug only happens on PRD. Ops says the TST and PRD settings should differ in just 3 places: "
          "the database host, the database name and DEBUG. Check if that is true.",
          "Compare the two config files line by line. Lines starting with < are from the first file, "
          "lines starting with > from the second."],
         "Both questions answered.",
         [("diff FILE1 FILE2", "show the lines that differ (< first file, > second file)", "diff old.conf new.conf"),
          ("diff -u FILE1 FILE2", "same in the format git uses (- removed, + added)", "diff -u old.conf new.conf"),
          CAT, SUBMIT],
         {"atlas/config/tst.py": 'DB_HOST = "atlas-db-02"\nDB_NAME = "atlas_tst"\nDEBUG = True\nPOOL_SIZE = 5\nCACHE_TTL = 300\nSESSION_MINUTES = 30',
          "atlas/config/prd.py": 'DB_HOST = "atlas-db-03"\nDB_NAME = "atlas"\nDEBUG = False\nPOOL_SIZE = 5\nCACHE_TTL = 30\nSESSION_MINUTES = 30'},
         parts=[("Besides host, name and DEBUG, which setting is different? (its name)", "CACHE_TTL"),
                ("What value does PRD use for that setting?", "30")],
         hint="diff atlas/config/tst.py atlas/config/prd.py"),
    task("Text tools", "ATL-119", "Move TST to the new database", "High", "Platform team",
         ["TST moves to the new database server atlas-db-new. In atlas/config/tst.py the old server "
          "atlas-db-02 appears in TWO lines (host and URL): both must change, nothing else.",
          "Never edit by hand what a command can do for you, and always keep a backup first: copy the "
          "file to tst.py.bak in the same folder, then change the original. Do not touch prd.py."],
         "tst.py points to the new server everywhere, tst.py.bak keeps the original. Closes by itself (type check).",
         [("cp FILE FILE.bak", "make a backup copy next to the file", "cp app.conf app.conf.bak"),
          ("sed 's/OLD/NEW/g' FILE", "PREVIEW: print the file with every OLD replaced by NEW (file unchanged)",
           "sed 's/red/blue/g' colors.txt"),
          ("sed -i 's/OLD/NEW/g' FILE", "really change the file (-i = in place)", "sed -i 's/red/blue/g' colors.txt"),
          ("diff FILE1 FILE2", "check what changed", "diff a.txt b.txt"), CAT, CHECK],
         {"atlas/config/tst.py": TST_CONFIG,
          "atlas/config/prd.py": 'DB_HOST = "atlas-db-03"\nDB_URL = "mysql+pymysql://atlas@atlas-db-03/atlas"\nDB_NAME = "atlas"'},
         checks=[("tst.py.bak is a copy of the original", lambda g: g.fs.d.get(HOME + "/atlas/config/tst.py.bak") == TST_CONFIG),
                 ("tst.py uses atlas-db-new in both lines and nothing else changed",
                  lambda g: g.fs.d.get(HOME + "/atlas/config/tst.py") == TST_CONFIG_NEW),
                 ("prd.py was not touched", lambda g: "atlas-db-03/atlas\"" in g.fs.d.get(HOME + "/atlas/config/prd.py", ""))],
         hint="cp atlas/config/tst.py atlas/config/tst.py.bak ; sed -i 's/atlas-db-02/atlas-db-new/g' "
              "atlas/config/tst.py ; diff atlas/config/tst.py.bak atlas/config/tst.py"),
    task("Text tools", "ATL-120", "Who keeps asking for missing pages?", "High", "Security team",
         ["traffic.log has today's API requests: <ip> <method> <path> <status> <time>. Someone is probing "
          "for pages that do not exist (HTTP 404). The path itself can contain 404 too: a plain grep would "
          "count the wrong lines.",
          "awk works with columns: $1 is the first column, $4 the fourth. It can test a column and add up numbers."],
         "All 4 steps are answered.",
         [("awk '$N == VALUE' FILE", "print only the lines where column N equals VALUE", "awk '$2 == \"GET\"' web.log"),
          ("awk '{print $N}' FILE", "print column N of every line", "awk '{print $3}' web.log"),
          ("awk '$N == V {s += $M} END {print s}' FILE", "add up column M for the matching lines, print the total at the end",
           "awk '$1 == \"10.0.0.9\" {s += $2} END {print s}' sales.log"),
          ("a | sort | uniq -c | sort -n -r", "count and rank", "... | sort | uniq -c | sort -n -r"),
          ("wc -l", "count lines", "awk '$1 > 5' nums.txt | wc -l"), SUBMIT],
         {"traffic.log": "\n".join(TRAFFIC)},
         parts=[("Warm-up: print only the status column ($4). How many DIFFERENT status codes are there?", "3"),
                ("How many requests got the status 404?", TRAFFIC_404),
                ("Which IP address made most of those 404 requests?", "10.20.30.66"),
                ("What is the total time in ms of ALL requests of that IP? (the time column ends in ms: awk reads the number)", TRAFFIC_SUM)],
         hint="awk '{print $4}' traffic.log | sort | uniq -c ; awk '$4 == 404' traffic.log | wc -l ; awk '$4 == 404 {print $1}' traffic.log | sort | uniq -c | sort -n -r ; "
              "awk '$1 == \"10.20.30.66\" {s += $5} END {print s}' traffic.log"),
    task("Text tools", "ATL-121", "Cloud costs per environment", "Normal", "Finance",
         ["Finance asks what Atlas costs in the cloud. costs.csv has one line per service and environment: "
          "service,environment,eur (the first line is a header).",
          "Use awk with -F, (the comma separates the columns). With an array you can add up one total per "
          "name: totals[$1] += $3."],
         "Both questions answered.",
         [("awk -F, '{print $N}' FILE", "-F, makes the comma the column separator", "awk -F, '{print $2}' data.csv"),
          ("awk -F, '$N == \"V\" {s += $M} END {print s}' FILE", "total of column M where column N is V",
           "awk -F, '$1 == \"b\" {s += $2} END {print s}' x.csv"),
          ("awk -F, '{t[$N] += $M} END {for (k in t) print k, t[k]}' FILE", "one total per different value of column N",
           "awk -F, '{t[$3] += $1} END {for (k in t) print k, t[k]}' x.csv"),
          ("sort -k2 -n -r", "sort by the 2nd column, biggest number first", "... | sort -k2 -n -r"), SUBMIT],
         {"costs.csv": "\n".join(COSTS)},
         parts=[("What is the total monthly cost (EUR) of the prd environment?", COSTS_PRD),
                ("Which service is the most expensive over all environments? (its name)", COSTS_TOP)],
         hint="awk -F, '$2 == \"prd\" {s += $3} END {print s}' costs.csv ; "
              "awk -F, '{t[$1] += $3} END {for (k in t) print k, t[k]}' costs.csv | sort -k2 -n -r"),
    task("Text tools", "ATL-122", "Clean the build leftovers", "Normal", "Tech lead",
         ["The build folder is full of temporary files. Delete every file ending in .tmp anywhere below ~/build, "
          "and nothing else: other files, even ones with tmp in their name, must stay.",
          "find lists the files; xargs turns that list into the arguments of another command. Preview with "
          "echo before you delete anything."],
         "No .tmp file is left below ~/build and all other files are untouched. Closes by itself (type check).",
         [('find FOLDER -name "PATTERN"', "list files by name in all subfolders", 'find src -name "*.bak"'),
          ("... | xargs echo", "PREVIEW: show what xargs would run (-n 1 = one file per line)", 'find src -name "*.bak" | xargs -n 1 echo'),
          ("... | xargs CMD", "run CMD with the listed files as arguments", 'find src -name "*.bak" | xargs ls -l'),
          ("rm FILE...", "delete files", "rm old1.log old2.log"), CHECK],
         {"build/a.tmp": "x", "build/obj/b.tmp": "x", "build/obj/deep/c.tmp": "x", "build/keep.txt": "keep",
          "build/obj/main.o": "obj", "build/notes.tmp.keep": "keep", "build/Makefile": "all:"},
         checks=[("no .tmp file is left below ~/build",
                  lambda g: not any(k.endswith(".tmp") for k in g.fs.d if k.startswith(HOME + "/build/"))),
                 ("the other files are untouched",
                  lambda g: all(g.fs.isfile(f"{HOME}/build/{f}") for f in ("keep.txt", "obj/main.o", "notes.tmp.keep", "Makefile")))],
         hint='find build -name "*.tmp" | xargs echo ; find build -name "*.tmp" | xargs rm'),
    # ------------------------------------------------------------ ENVIRONMENTS
    task("Environments", "ATL-123", "PRD database failover", "Critical", "Platform team",
         ["PRD points to atlas-db-01, which stopped answering. There are two replicas: "
          "atlas-db-02 and atlas-db-03. We must switch Atlas to the one that is alive.",
          "Server names and their IPs are in /etc/hosts. Real ping never stops by itself: "
          "send a fixed number of packets."],
         "You submit the IP address of the database replica that answers.",
         [("ip addr", "show the IP addresses of this computer", "ip addr"),
          ("cat /etc/hosts", "all server names and their IPs", "cat /etc/hosts"),
          ("grep TEXT FILE", "show matching lines", "grep gateway /etc/hosts"), PING, SUBMIT],
         answer="10.20.30.12", hint="ping -c 3 atlas-db-02 ; ping -c 3 atlas-db-03 ; grep atlas-db /etc/hosts"),
    task("Environments", "ATL-124", "Monitoring alerts", "High", "Monitoring",
         ["alerts.log has today's Atlas alerts. Most were resolved automatically. One host is "
          "still down and the alert only shows its IP.",
          "Find the unresolved alert, turn the IP into a server name, and confirm it is down."],
         "You submit the NAME of the server that is down.",
         [CAT, ("grep -v WORD FILE", "hide lines containing a word", "grep -v INFO server.log"),
          ("grep IP /etc/hosts", "find the name of an IP", "grep 127.0.0.1 /etc/hosts"), PING, SUBMIT],
         {"alerts.log": "08:10 host 10.20.30.31 high memory RESOLVED 08:12\n"
                        "08:55 host 10.20.30.12 high cpu RESOLVED 09:01\n"
                        "09:42 host 10.20.30.13 not responding (3 checks failed)\n"
                        "09:50 host 10.20.30.33 slow disk RESOLVED 09:58"},
         answer="atlas-db-03", hint="grep -v RESOLVED alerts.log ; grep 10.20.30.13 /etc/hosts"),
    task("Environments", "ATL-125", "PRD disk is full", "Critical", "Monitoring",
         ["Monitoring says Atlas on atlas-prd stopped writing logs. You do not log in to servers to look "
          "around: you ask them one question at a time with ssh.",
          "Run  ssh analyst@atlas-prd COMMAND  to run COMMAND on that server (put the command in quotes if "
          "it has spaces). Find the full disk, save the proof, then find the biggest file in the folder atlas inside the server's log directory (on Linux, logs live in /var)."],
         "All 3 steps are done.",
         [("ssh USER@HOST \"COMMAND\"", "run one command on another server and show its output", 'ssh analyst@gateway "uptime"'),
          ("df -h", "disk space per disk: look at Use% and Mounted on", "df -h"),
          ("ls -l FOLDER", "file sizes are in column 5", "ls -l /srv/data"),
          ("sort -k5 -n -r | head -n 1", "biggest number in column 5 first, keep one", "... | sort -k5 -n -r | head -n 1"),
          ("ssh USER@HOST \"CMD\" > FILE", "save the server's answer in a local file", 'ssh analyst@gateway "date" > when.txt'),
          SUBMIT, CHECK],
         parts=[("Which mount point of atlas-prd is at 100%?", "/var/log"),
                ("Save the df -h output of atlas-prd in ~/prd_disk.txt (completes by itself)",
                 lambda g: "/var/log" in g.fs.d.get(HOME + "/prd_disk.txt", "") and "Filesystem" in g.fs.d.get(HOME + "/prd_disk.txt", "")),
                ("Which file in the Atlas log folder of that server is the biggest? (file name)", "debug.log")],
         hint='ssh analyst@atlas-prd "df -h" ; ssh analyst@atlas-prd "df -h" > prd_disk.txt ; '
              'ssh analyst@atlas-prd "ls -l /var/log/atlas | sort -k5 -n -r | head -n 1"',
         setup=setup_417),
    # ------------------------------------------------------------ API
    task("API", "ATL-126", "API access token", "Normal", "Integration team",
         ["The Power BI team wants to read Atlas data through its REST API. First you need a "
          f"token from the token endpoint: {API}/token",
          "Like real curl, the output is only the response body. Read the error messages and "
          "adjust your request."],
         "You submit the token.",
         [("curl URL", "send a web request and show the answer", f"curl {API}/status"),
          ("curl -i URL", "also show the HTTP status (200, 400, 403...)", f"curl -i {API}/status"),
          ("URL?key=value", "send data in the URL (a query); quote the URL", f'curl "{API}/search?q=gate"'),
          ("whoami", "print your user name", "whoami"), SUBMIT],
         answer=TOKEN, hint=f'curl {API}/token ; whoami ; curl "{API}/token?user=analyst"'),
    task("API", "ATL-127", "Project stage from the API", "Normal", "Product owner",
         [f"Check through the API in which stage project NPI-042 is: {API}/api/projects/NPI-042",
          "The projects endpoint is protected: it needs your token in a header. The error "
          "message tells you the exact header format. Tip: keep the token in a shell variable."],
         "You submit the stage (e.g. Gate 9).",
         [("curl URL", "call the endpoint and read the error", f"curl {API}/status"),
          ("NAME=value", "store a value in a shell variable", "CITY=Barcelona"),
          ("echo $NAME", "use the value of a variable", "echo $CITY"),
          ('curl -H "HEADER" URL', "send a header with the request", f'curl -H "Accept: text/plain" {API}/status'),
          SUBMIT],
         answer="Gate 2", hint=f'curl -H "Authorization: Bearer {TOKEN}" {API}/api/projects/NPI-042'),
    task("API", "ATL-128", "Role audit before go-live", "High", "Security team",
         [f"Before go-live, security wants to know how many Atlas users are admins. {API}/api/users "
          "returns one JSON user per line. Save it to users.json first (auditors want the file).",
          "Careful: a pending 'admin-request' is not an admin yet."],
         "You submit the number of real admins.",
         [("curl URL > FILE", "save the answer into a file", f"curl {API}/status > status.json"),
          CAT, ("grep -c TEXT FILE", "count matching lines", "grep -c up status.json"),
          ("grep -c '\"TEXT\"' FILE", "include the quotes to match one exact JSON value",
           "grep -c '\"up\"' status.json"), SUBMIT],
         answer="3", hint=f"curl {API}/api/users > users.json ; grep -c '\"admin\"' users.json"),
    task("API", "ATL-129", "Slow database incident", "Critical", "Tech lead",
         ["Users say Atlas was very slow TODAY (2026-11-12). The DBA suspects atlas-db-02. "
          "We need the number of ERROR lines in today's log of that server.",
          "Logs are in ~/incident, one folder per day. The same server has logs on other days "
          "too: use only today's."],
         "You submit the number of ERROR lines in today's log of that server.",
         [('find FOLDER -name "PATTERN"', "find files by name; * is a wildcard", 'find projects -name "*.log"'),
          TREE, ("grep -c WORD FILE", "count matching lines", "grep -c WARN server.log"),
          ("grep WORD FILE | wc -l", "the same, with a pipe", "grep WARN server.log | wc -l"), SUBMIT],
         gen_incident("atlas-db-02", 7), answer="7",
         hint='find incident -name "atlas-db-02*" ; grep -c ERROR incident/2026/11/12/atlas-db-02.log'),
    # ------------------------------------------------------------ GIT & PYTHON
    task("Git & Python", "ATL-130", "Set up the dev environment", "High", "Tech lead",
         ["Your laptop was reinstalled. Get Atlas running again the standard way: a virtual "
          "environment in a folder called .venv inside ~/atlas, the requirements installed "
          "into it, and the app started on the port from the README.",
          "On Ubuntu the command is python3 (python only exists inside a venv). pip refuses to "
          "install system-wide. Folders that start with a dot are hidden from plain ls."],
         "All 4 requirements are met. Closes by itself (type check).",
         [CD, ("python3 -m venv FOLDER", "create a virtual environment in FOLDER", "python3 -m venv myenv"),
          ("source FOLDER/bin/activate", "use that venv in this shell; the prompt shows its name",
           "source myenv/bin/activate"),
          ("pip install -r FILE", "install every package listed in a file", "pip install -r deps.txt"),
          ("pip list", "show the packages installed in the venv", "pip list"),
          ("flask run --port N", "start the app on a port", "flask run --port 8000"), CHECK],
         {"atlas/README.md": "# Atlas\nLocal setup: create a venv, install requirements.txt, "
                               "then: flask run --port 5050",
          "atlas/requirements.txt": REQUIREMENTS, "atlas/wsgi.py": "from app import create_app\napp = create_app()",
          "atlas/.env": "DB_HOST=localhost\nDB_NAME=atlas_dev", "atlas/app/__init__.py": "def create_app(): ..."},
         checks=[(".venv created in ~/atlas", home_dir("atlas/.venv")),
                 ("the venv is active", lambda g: g.venv == HOME + "/atlas/.venv"),
                 ("requirements installed in the venv", lambda g: "flask" in g.installed.get(HOME + "/atlas/.venv", {})),
                 ("Atlas started with flask run", lambda g: g.flask_ran)],
         hint="cd atlas ; python3 -m venv .venv ; source .venv/bin/activate ; "
              "pip install -r requirements.txt ; flask run --port 5050"),
    task("Git & Python", "ATL-131", "Missing environment variables", "High", "Platform team",
         ["On the servers there is no .env file: settings come from environment variables "
          "(Azure App Service works the same way). We copied that setup to your machine: the "
          "venv in ~/atlas/.venv is ready, but Atlas refuses to start.",
          "Activate the venv, run flask, read the error, then set what is missing as environment "
          "variables. .env.example shows the values for local development. No spaces around =."],
         "The variables are set and flask run works. Closes by itself (type check).",
         [CD, ("source FOLDER/bin/activate", "activate an existing venv", "source myenv/bin/activate"),
          ("flask run", "start the app and read the error", "flask run"), CAT,
          ("export NAME=value", "set an environment variable", "export LOG_LEVEL=debug"),
          ("echo $NAME", "show the value of a variable", "echo $LOG_LEVEL"),
          ("env", "list all environment variables", "env | grep LOG"), CHECK],
         {"atlas/requirements.txt": REQUIREMENTS, "atlas/wsgi.py": "from app import create_app\napp = create_app()",
          "atlas/.env.example": "# copy these into your environment\nDB_HOST=<server>\nDB_NAME=<database>\n"
                                  "# local development: DB_HOST=localhost  DB_NAME=atlas_dev",
          "atlas/app/__init__.py": "def create_app(): ..."},
         checks=[("DB_HOST is set correctly", lambda g: g.env.get("DB_HOST") == "localhost"),
                 ("DB_NAME is set correctly", lambda g: g.env.get("DB_NAME") == "atlas_dev"),
                 ("Atlas started with flask run", lambda g: g.flask_ran)],
         hint="cd atlas ; source .venv/bin/activate ; flask run ; cat .env.example ; export DB_HOST=localhost ; "
              "export DB_NAME=atlas_dev ; flask run",
         setup=setup_702),
    task("Git & Python", "ATL-132", "What is in my working copy?", "Normal", "Tech lead",
         ["You are taking over a colleague's work on Atlas. Before touching anything, find "
          "out where the repository stands.",
          "Every answer comes from git, run inside ~/atlas. git only works inside the project folder."],
         "All 3 steps are answered.",
         [CD, ("git status", "branch, changed files and untracked files", "git status"),
          ("git branch", "list branches; * marks the current one", "git branch"),
          ("git diff", "show changes that are not committed yet", "git diff"),
          ("git log --oneline", "short list of commits: hash + message", "git log --oneline"), SUBMIT],
         parts=[("Which branch is checked out?", "feature/requestor-role"),
                ("Which tracked file has changes that are not committed? (its path)", ("app/routes.py", "routes.py")),
                ("What is the short hash of the commit 'Add trademark BU dropdown'?", ghash("Add trademark BU dropdown"))],
         hint="cd atlas ; git status ; git log --oneline", setup=setup_703),
    task("Git & Python", "ATL-133", "Branch, fix and commit", "High", "Tech lead",
         ["Team rule: never commit straight to main. Create the branch feature/launch-date, add "
          "the migration migrations/0042_add_launch_date.py with one line: "
          "add_column('request', 'launch_date')",
          "Commit it with a message that starts with the ticket number ATL-146. "
          "Made a mistake on main? Type reset to start this ticket again."],
         "All requirements are met. Closes by itself (type check).",
         [CD, ("git checkout -b NAME", "create a new branch and switch to it", "git checkout -b fix/typo"),
          ('echo "TEXT" > FILE', "write a file; double quotes keep ( ) and ' safe", "echo \"print('hi')\" > hello.py"),
          ("git status", "see what changed", "git status"),
          ("git add FILE", "stage a file for the next commit", "git add hello.py"),
          ('git commit -m "MSG"', "save the staged changes as a commit", 'git commit -m "ATL-000 Fix typo"'),
          ("git log --oneline", "check your commit", "git log --oneline"), CHECK],
         checks=[("on the new feature branch", lambda g: g.repo and g.repo["branch"] == "feature/launch-date"),
                 ("last commit adds the migration with the right line",
                  lambda g: g.repo and g.git_head().get("tree", {}).get("migrations/0042_add_launch_date.py", "").strip()
                  == "add_column('request', 'launch_date')"),
                 ("commit message starts with ATL-146", lambda g: g.repo and g.git_head().get("msg", "").startswith("ATL-146")),
                 ("main was not touched", lambda g: g.repo and len(g.repo["branches"]["main"]) == g.mark.get("main_len")),
                 ("nothing left uncommitted", lambda g: g.repo and g.git_clean())],
         hint="cd atlas ; git checkout -b feature/launch-date ; echo \"add_column('request', 'launch_date')\" > "
              "migrations/0042_add_launch_date.py ; git add migrations/0042_add_launch_date.py ; "
              "git commit -m \"ATL-146 Add launch date column\"",
         setup=setup_704),
    task("Git & Python", "ATL-134", "Review before the pull request", "High", "Code review",
         ["Your SSO branch is almost ready for a pull request. Always review your changes "
          "before you push: something slipped in that should not be there.",
          "git has two kinds of changes: not staged yet, and staged (what WILL go into the next commit)."],
         "All 3 steps are done.",
         [CD, ("git status", "see staged and unstaged changes", "git status"),
          ("git diff", "show unstaged changes (- old line, + new line)", "git diff"),
          ("git restore FILE", "throw away the uncommitted changes in a file", "git restore notes.md"),
          ("git diff --staged", "show what is staged for the next commit", "git diff --staged"), SUBMIT, CHECK],
         parts=[("An accidental change slipped into a config file. Which DB_HOST value was put in?", "compass-db-01"),
                ("Undo it: restore that file to the committed version (completes by itself)",
                 lambda g: g.repo and g.git_working().get("config/tst.py") == g.git_head()["tree"].get("config/tst.py")),
                ("Which package is staged to be added to requirements.txt? (name only)", ("requests", "requests==2.32.3"))],
         hint="cd atlas ; git diff ; git restore config/tst.py ; git diff --staged", setup=setup_705),
    # ------------------------------------------------------------ SERVERS
    task("Servers", "ATL-135", "Runaway process", "Critical", "Platform team",
         ["Your dev box is crawling. Something is eating the CPU. Find the process that uses the most CPU "
          "and stop it.",
          "Every process has a number (PID). kill sends it a polite request to stop; some processes ignore "
          "polite requests: check with ps whether it is really gone, and use the stronger signal if not."],
         "You found the PID and the process is gone. Closes by itself after the answer.",
         [("ps -ef", "list all processes (ps aux also shows %CPU and %MEM)", "ps -ef | head -n 5"),
          ("sort -k3 -n -r", "sort by the 3rd column (the %CPU in ps aux), biggest first", "... | sort -k3 -n -r | head -n 3"),
          ("kill PID", "ask a process to stop (polite)", "kill 9999"),
          ("kill -9 PID", "force a process to stop: it cannot refuse", "kill -9 9999"), SUBMIT, CHECK],
         parts=[("Which process uses the most CPU? Submit its PID", "4127"),
                ("Stop it (completes by itself when it no longer shows in ps)", lambda g: 4127 not in g.procs)],
         hint="ps aux | sort -k3 -n -r | head -n 3 ; kill 4127 ; kill -9 4127", setup=setup_801),
    task("Servers", "ATL-136", "Secrets everyone can read", "High", "Security team",
         ["The audit found files with the wrong permissions. In ls -l the first column shows them: three "
          "letters for the owner (u), three for the group (g), three for everybody else (o).",
          "Numbers: r=4, w=2, x=1, added per group. 640 = rw- r-- --- . Fix three things: atlas/.env only "
          "readable and writable by its owner; atlas/scripts/deploy.sh runnable by owner and group but "
          "not by others (owner all, group read+execute); atlas/config/prd.py readable by everybody but "
          "writable only by the owner."],
         "All 3 files have the right permissions. Closes by itself (type check).",
         [("ls -la FOLDER", "long listing with permissions, including hidden files", "ls -la reports"),
          ("stat FILE", "shows the permissions as a number too, e.g. (0644/-rw-r--r--)", "stat report.txt"),
          ("chmod NNN FILE", "set permissions with 3 digits: owner, group, others", "chmod 640 report.txt"),
          ("chmod u+x FILE", "or change one thing: u/g/o + or - r/w/x", "chmod g-w report.txt"), CHECK],
         {"atlas/.env": "DB_HOST=localhost\nSECRET_KEY=change-me",
          "atlas/scripts/deploy.sh": "#!/bin/bash\necho deploying",
          "atlas/config/prd.py": 'DB_HOST = "atlas-db-03"'},
         checks=[(".env is 600 (only the owner can read and write)", lambda g: g.fs.mode(HOME + "/atlas/.env") == 0o600),
                 ("deploy.sh is 750 (owner all, group read+execute, others nothing)",
                  lambda g: g.fs.mode(HOME + "/atlas/scripts/deploy.sh") == 0o750),
                 ("prd.py is 644 (everybody reads, only the owner writes)",
                  lambda g: g.fs.mode(HOME + "/atlas/config/prd.py") == 0o644)],
         hint="ls -la atlas ; chmod 600 atlas/.env ; chmod 750 atlas/scripts/deploy.sh ; chmod 644 atlas/config/prd.py",
         setup=setup_802),
    task("Servers", "ATL-137", "The API service will not start", "Critical", "Tech lead",
         ["atlas-api is a service of your own user (a systemd user service) and it is in a failed state. "
          "Never guess: read what the service says about itself, then fix the cause.",
          "Services of your own user need --user in front of the action. After fixing the cause, start it "
          "again and check that it is active."],
         "The cause is found and the service is active again.",
         [("systemctl --user status NAME", "state of a service and its last log lines", "systemctl --user status myapp"),
          ("journalctl --user -u NAME -n N", "the last N log lines of a service", "journalctl --user -u myapp -n 20"),
          ("ls -l FILE", "check the permissions of a file (see also chmod)", "ls -l notes.txt"),
          ("chmod NNN FILE", "change permissions", "chmod 600 notes.txt"),
          ("systemctl --user restart NAME", "start the service again", "systemctl --user restart myapp"), SUBMIT, CHECK],
         {"atlas/api.conf": "port = 5050\ndb = atlas_dev"},
         parts=[("Which file can the service not read? (its full path)",
                 ("/home/analyst/atlas/api.conf", "~/atlas/api.conf", "atlas/api.conf")),
                ("Fix the cause and restart the service so it is active (completes by itself)",
                 lambda g: g.svc.get("atlas-api", {}).get("state") == "active")],
         hint="systemctl --user status atlas-api ; journalctl --user -u atlas-api -n 5 ; "
              "chmod 640 atlas/api.conf ; systemctl --user restart atlas-api",
         setup=setup_803),
    task("Servers", "ATL-138", "Backup before the release", "High", "Release manager",
         ["Before the release, back up the configuration. Put the folder atlas/config into a compressed "
          "archive called config-backup.tar.gz inside ~/backups. Then check what is in it, and finally "
          "practice a restore.",
          "tar letters: c create, x extract, t list, z gzip, f file name (the name comes right after f). "
          "To extract into another folder use -C FOLDER (it must exist)."],
         "All 3 steps are done.",
         [("tar -czf ARCHIVE FOLDER", "create a compressed archive", "tar -czf site.tar.gz reports"),
          ("tar -tzf ARCHIVE", "list what is inside (nothing is extracted)", "tar -tzf site.tar.gz"),
          ("tar -xzf ARCHIVE -C DIR [MEMBER]", "extract into DIR; add a path to take only that file",
           "tar -xzf site.tar.gz -C /tmp reports/jan.txt"),
          ("a | grep -c TEXT", "count matching lines", "tar -tzf site.tar.gz | grep -c 'txt$'"),
          ("ls -R FOLDER", "list a folder and everything below it", "ls -R reports"), SUBMIT, CHECK],
         {"atlas/config/dev.py": "DEBUG = True", "atlas/config/tst.py": "DEBUG = False",
          "atlas/config/prd.py": "DEBUG = False", "atlas/README.md": "# Atlas", "backups/": "", "restore/": ""},
         parts=[("Create ~/backups/config-backup.tar.gz with the folder atlas/config (completes by itself)",
                 lambda g: "atlas/config/prd.py" in tar_members(g.fs, HOME + "/backups/config-backup.tar.gz")),
                ("How many .py files are inside the archive?", "3"),
                ("Restore ONLY atlas/config/tst.py into ~/restore (completes by itself)",
                 lambda g: g.fs.isfile(HOME + "/restore/atlas/config/tst.py")
                 and not g.fs.exists(HOME + "/restore/atlas/config/prd.py"))],
         hint="tar -czf backups/config-backup.tar.gz atlas/config ; tar -tzf backups/config-backup.tar.gz | grep -c 'py$' ; "
              "tar -xzf backups/config-backup.tar.gz -C restore atlas/config/tst.py"),
    task("Servers", "ATL-139", "Port 5050 is already in use", "High", "Tech lead",
         ["You start Atlas on port 5050 and it refuses: the port is already taken. Your venv in "
          "~/atlas/.venv is ready and the environment is configured.",
          "Find out which process listens on that port, stop it, and start Atlas on 5050 again. Do not "
          "just pick another port: the front end expects 5050."],
         "Atlas runs on port 5050.",
         [CD, ("source FOLDER/bin/activate", "activate a venv", "source myenv/bin/activate"),
          ("flask run --port N", "start the app and read the error", "flask run --port 8000"),
          ("ss -tlnp", "who listens on which port: TCP, listening, numbers, with the process (PID)", "ss -tlnp | grep 22"),
          ("kill PID", "stop a process", "kill 9999"), SUBMIT, CHECK],
         {"atlas/wsgi.py": "from app import create_app\napp = create_app()", "atlas/requirements.txt": REQUIREMENTS,
          "atlas/app/__init__.py": "def create_app(): ..."},
         parts=[("Start Atlas on port 5050 and read the error. Which PID listens on 5050?", "4388"),
                ("Stop that process and start Atlas on port 5050 (completes by itself)",
                 lambda g: g.flask_port == "5050" and 4388 not in g.procs)],
         hint="cd atlas ; source .venv/bin/activate ; flask run --port 5050 ; ss -tlnp ; kill 4388 ; flask run --port 5050",
         setup=setup_805),
    task("Servers", "ATL-140", "Who ate the disk?", "High", "Platform team",
         ["The data disk is almost full. Under ~/data there are four folders. Find out which one really uses "
          "the most space. The folder with the most files is not necessarily the biggest one.",
          "du shows disk usage: -s gives one total per argument. Without -h the numbers are in KB."],
         "Both steps answered.",
         [("du -sh FOLDER...", "one human-readable total for each folder", "du -sh logs/*"),
          ("du -s FOLDER...", "totals in KB, good for sorting", "du -s logs/*"),
          ("sort -n -r | head -n 1", "biggest number first, keep one", "... | sort -n -r | head -n 1"),
          ("ls FOLDER | wc -l", "how many files a folder has", "ls logs/old | wc -l"), SUBMIT],
         DU_FILES,
         parts=[("Which folder under ~/data uses the most disk space? (its name)", "uploads"),
                ("How many KB does that folder use? (the number du -s prints)", DU_UPLOADS)],
         hint="du -s data/* | sort -n -r | head -n 1"),
    task("Servers", "ATL-141", "Who can log in here?", "Normal", "Security team",
         ["For the access review, security asks which accounts on this server can actually log in. Every account "
          "is one line of /etc/passwd with 7 fields separated by colons: name:x:uid:gid:comment:home:shell.",
          "An account can log in when its shell is a real shell like bash. Service accounts have nologin or "
          "false there."],
         "Both questions answered.",
         [("cat /etc/passwd", "one account per line", "cat /etc/group"),
          ("grep -c 'TEXT$' FILE", "count lines that END with a text", "grep -c 'sh$' /etc/shells"),
          ("cut -d: -f N FILE", "the colon separates the fields: take field N", "cut -d: -f1 /etc/group"),
          ("a | b", "pipe: the output of a goes into b", "grep root /etc/group | cut -d: -f3"), SUBMIT],
         parts=[("How many accounts have bash as their login shell?", "2"),
                ("Which user id (uid, field 3) does the account mysql have?", "114")],
         hint="grep -c 'bash$' /etc/passwd ; grep mysql /etc/passwd | cut -d: -f3"),
    # ------------------------------------------------------------ SCRIPTING
    task("Scripting", "ATL-142", "Which servers answer?", "High", "Monitoring",
         ["The on-call engineer wants a small script that checks a list of servers. hosts.txt has one server "
          "name per line.",
          "Write check_hosts.sh: for every name in hosts.txt it prints  NAME up  or  NAME down  (one line per "
          "server, same order). A successful ping means up. Run the script and save its output in report.txt."],
         "check_hosts.sh is executable and has run, and report.txt has one line per server. Closes by itself.",
         [("for NAME in LIST; do ...; done", "repeat commands for every item of a list", "for f in a.txt b.txt; do wc -l $f; done"),
          ("$(cat FILE)", "use the lines of a file as the list", "for n in $(cat names.txt); do echo $n; done"),
          ("A && B || C", "run B if A worked, otherwise C", "ls x && echo found || echo missing"),
          ("CMD > /dev/null 2>&1", "throw away all output of CMD: only its exit status is left", "ping -c 1 gateway > /dev/null 2>&1"),
          ("echo 'TEXT' > FILE", "write a script from the command line (single quotes keep $ as it is)", "echo 'echo hi' > hello.sh"),
          ("chmod +x FILE", "make it executable", "chmod +x hello.sh"),
          ("./FILE > LOG", "run a script in this folder and save its output", "./backup.sh > backup.log"), CHECK],
         {"hosts.txt": "atlas-api\natlas-tst\natlas-pre\natlas-prd\natlas-db-01\natlas-db-02"},
         checks=[("check_hosts.sh is executable", lambda g: HOME + "/check_hosts.sh" in g.fs.x),
                 ("check_hosts.sh has run", lambda g: HOME + "/check_hosts.sh" in g.ran),
                 ("report.txt has one up/down line per server, in order",
                  lambda g: g.fs.d.get(HOME + "/report.txt", "").split("\n") == HOST_REPORT)],
         hint="echo 'for h in $(cat hosts.txt); do ping -c 1 $h > /dev/null 2>&1 && echo \"$h up\" || echo \"$h down\"; done' "
              "> check_hosts.sh ; chmod +x check_hosts.sh ; ./check_hosts.sh > report.txt"),
    task("Scripting", "ATL-143", "Archive the big logs", "Normal", "Platform team",
         ["The log folder keeps growing. Every .log file in ~/logs that is bigger than 1 KiB must go into one "
          "compressed archive, ~/logs-archive.tar.gz, and then be deleted. Smaller logs stay where they are.",
          "Never delete what you have not listed: see which files find selects first. $(command) pastes the "
          "output of a command into another command."],
         "The archive holds exactly the big logs, and they are gone from ~/logs. Closes by itself (type check).",
         [('find FOLDER -name "PATTERN" -size +1k', "only files bigger than 1 KiB (k, M, G; -1k = smaller)",
           'find data -name "*.csv" -size +5k'),
          ("tar -czf ARCHIVE $(find ...)", "archive what find lists: $( ) pastes its output", "tar -czf old.tar.gz $(find data -name \"*.csv\")"),
          ("tar -tzf ARCHIVE", "list what is inside an archive", "tar -tzf old.tar.gz"),
          ("find ... -delete", "delete what find selects (check with find alone first!)", 'find data -name "*.tmp" -delete'), CHECK],
         {**{f"logs/app-{i}.log": (LOG_BIG if i % 2 else LOG_SMALL) for i in range(1, 7)}},
         checks=[("the archive holds exactly the three big logs",
                  lambda g: sorted(tar_members(g.fs, HOME + "/logs-archive.tar.gz")) == BIG_LOGS),
                 ("the big logs are deleted", lambda g: not any(g.fs.exists(f"{HOME}/{f}") for f in BIG_LOGS)),
                 ("the small logs are still there",
                  lambda g: all(g.fs.isfile(f"{HOME}/logs/app-{i}.log") for i in (2, 4, 6)))],
         hint='tar -czf logs-archive.tar.gz $(find logs -name "*.log" -size +1k) ; find logs -name "*.log" -size +1k -delete'),
    task("Scripting", "ATL-144", "Switch the current release", "High", "Release manager",
         ["The web server always serves the folder  current , which is a symbolic link to one release in "
          "~/releases. Find out which release it serves now, then switch it to v1.9.0.",
          "Careful: if the link points to a folder, a plain  ln -sf  creates the new link INSIDE that folder. "
          "One option tells ln to replace the link itself: read man ln."],
         "Both steps are done.",
         [("readlink LINK", "where a symbolic link points", "readlink live"),
          ("ls -l", "links show as  name -> target", "ls -l /srv"),
          ("ln -s TARGET LINK", "make a symbolic link", "ln -s /srv/app/blue live"),
          ("ln -sfn TARGET LINK", "replace an existing link, even one that points to a folder", "ln -sfn /srv/app/green live"),
          SUBMIT, CHECK],
         {"releases/v1.8.2/app.txt": "version 1.8.2", "releases/v1.8.3/app.txt": "version 1.8.3",
          "releases/v1.9.0/app.txt": "version 1.9.0"},
         parts=[("Which release does current serve now? (the folder name)", "v1.8.2"),
                ("Switch current to the release v1.9.0 (completes by itself)",
                 lambda g: g.fs.follow(HOME + "/current") == HOME + "/releases/v1.9.0")],
         hint="readlink current ; ln -sfn releases/v1.9.0 current", setup=setup_release),
    task("Scripting", "ATL-145", "Silence the nightly job", "Normal", "Platform team",
         ["nightly.sh runs every night and mails the team its whole output, errors included. Read the script, "
          "then run it twice: once with ALL its output (normal messages and errors, in order) in nightly.log, "
          "once with only the error messages in nightly.err.",
          "Two output streams leave a program: normal output (1) and error messages (2). > catches the first, "
          "2> the second, and 2>&1 sends the errors to the same place as the normal output."],
         "nightly.log has everything in order and nightly.err only the error. Closes by itself (type check).",
         [CAT, ("./FILE > LOG 2>&1", "normal output and errors, in order, into one file", "./sync.sh > sync.log 2>&1"),
          ("./FILE 2> LOG", "only the error messages into a file (normal output stays on screen)", "./sync.sh 2> sync.err"),
          ("CMD > /dev/null", "throw the normal output away", "./sync.sh 2> sync.err > /dev/null"), CHECK],
         {"nightly.sh": NIGHTLY},
         checks=[("nightly.log has the output and the error, in order",
                  lambda g: g.fs.d.get(HOME + "/nightly.log", "").split("\n") ==
                  ["backup started", NIGHTLY_ERROR, "backup finished"]),
                 ("nightly.err has only the error message",
                  lambda g: g.fs.d.get(HOME + "/nightly.err", "").split("\n") == [NIGHTLY_ERROR])],
         hint="cat nightly.sh ; ./nightly.sh > nightly.log 2>&1 ; ./nightly.sh 2> nightly.err > /dev/null", setup=setup_nightly),
    # ------------------------------------------------------------ FEATURE WORK (multi-step)
    task("Feature work", "ATL-146", "Add the launch date column", "High", "Product owner",
         ["The request form must save a desired launch date. The column does not exist yet: "
          "that is why /requests/new crashes with KeyError: 'launch_date'.",
          "Find the template of the form, find the next free migration number, and write the "
          "migration that adds the column."],
         "All 3 steps are done.",
         [("grep -r WORD FOLDER", "find which file contains a word", "grep -r FIXME projects"),
          ("ls FOLDER", "list a folder", "ls projects"),
          ('echo "TEXT" > FILE', "write a file; double quotes keep ( ) and ' safe", "echo \"print('hi')\" > hello.py"),
          ("cat FILE", "check what you wrote", "cat hello.py"), SUBMIT, CHECK],
         {"atlas/app/templates/request_new.html": "{% extends 'base.html' %}\n{{ request_form }}",
          "atlas/app/templates/request_list.html": "{% extends 'base.html' %}\n{{ table }}",
          "atlas/app/templates/base.html": "<html>{% block content %}{% endblock %}</html>",
          "atlas/migrations/0038_add_requestor_role.py": "add_column('user', 'role')",
          "atlas/migrations/0039_add_scope.py": "add_column('request', 'scope')",
          "atlas/migrations/0040_add_trademark_bu.py": "add_column('request', 'trademark_bu')",
          "atlas/migrations/0041_add_bu_dropdown.py": "add_column('request', 'bu')"},
         parts=[("Which template renders the request form? (file name)",
                 ("request_new.html", "atlas/app/templates/request_new.html")),
                ("What is the next free migration number? (4 digits)", "0042"),
                ("Create the migration <NUMBER>_add_launch_date.py in atlas/migrations with exactly "
                 "one line: add_column('request', 'launch_date')   (completes by itself)",
                 lambda g: content("atlas/migrations/0042_add_launch_date.py",
                                   ["add_column('request', 'launch_date')"])(g))],
         hint="grep -r request_form atlas/app/templates ; ls atlas/migrations ; "
              "echo \"add_column('request', 'launch_date')\" > atlas/migrations/0042_add_launch_date.py"),
    task("Feature work", "ATL-147", "Brute force on the service account", "Critical", "Security team",
         ["Before SSO goes live, Atlas still allows password login on its server. Overnight, "
          "auth.log recorded many failed logins. Who was targeted, did the attacker get in, "
          "and from which machine?",
          "Counting by spaces, the user name is field 9 and the IP address is field 11."],
         "All 3 steps are answered.",
         [("head -n N FILE", "look at the format", "head -n 5 server.log"),
          ("grep WORD FILE", "keep only one kind of line (case-sensitive)", "grep WARN server.log"),
          ('cut -d " " -f N', "take one field of each line", '... | cut -d " " -f 2'),
          ("sort | uniq -c | sort -n -r", "count and rank, most frequent first", "... | sort | uniq -c | sort -n -r"),
          ("grep IP /etc/hosts", "find the machine name of an IP", "grep 127.0.0.1 /etc/hosts"), SUBMIT],
         {"auth.log": gen_auth_log()},
         parts=[("Which account received the most failed logins?", "svc_atlas"),
                ("That account then logged in successfully. From which IP?", "10.20.30.66"),
                ("Which machine is that IP? (its name in /etc/hosts)", "guest-laptop-07")],
         hint='grep Failed auth.log | cut -d " " -f 9 | sort | uniq -c | sort -n -r ; '
              'grep Accepted auth.log ; grep 10.20.30.66 /etc/hosts'),
    task("Feature work", "ATL-148", "Atlas PRE is down", "Critical", "QA team",
         ["Nobody can test the v1.9 release: the PRE environment does not respond. The load "
          "balancer configs in ~/lb/sites say for each part of Atlas which server is "
          "'primary' and which is 'fallback'.",
          "Find the server that is down, which site uses it as primary, and whether its "
          "fallback can take over. A server can be primary in one file and fallback in another."],
         "All 3 steps are answered.",
         [("grep TEXT FILE", "list matching lines, e.g. servers in /etc/hosts", "grep gateway /etc/hosts"), PING,
          ("grep -r TEXT FOLDER", "search all files in a folder", "grep -r timeout projects"),
          ("cat FILE", "read one config", "cat projects/site.conf"), SUBMIT],
         {"lb/lb.conf": "include sites/*.conf;",
          "lb/sites/requests.conf": "site = requests.atlas.local\nprimary = atlas-pre\nfallback = atlas-tst",
          "lb/sites/reports.conf": "site = reports.atlas.local\nprimary = atlas-tst\nfallback = atlas-pre",
          "lb/sites/admin.conf": "site = admin.atlas.local\nprimary = atlas-prd\nfallback = atlas-tst"},
         parts=[("Which Atlas server is down? (its name)", "atlas-pre"),
                ("Which config file uses it as PRIMARY? (file name)", ("requests.conf", "lb/sites/requests.conf")),
                ("Is that site's fallback online? Submit the fallback's IP address", "10.20.30.31")],
         hint='grep atlas /etc/hosts ; ping -c 3 atlas-pre ; grep -r "primary = atlas-pre" lb ; '
              'cat lb/sites/requests.conf ; ping -c 3 atlas-tst'),
    task("Feature work", "ATL-149", "Sprint review numbers", "High", "Scrum master",
         ["Sprint review in one hour. sprint.csv has every ticket of the sprint: ticket,component,points.",
          "Answer the questions, then give the scrum master a file workflow.csv with only the "
          "workflow tickets. Careful: 'workflow-ui' is a different component."],
         "Both questions answered and workflow.csv created.",
         [("head -n N FILE", "look at the format", "head -n 5 data.csv"),
          ("grep -c TEXT FILE", "count; include the commas to match one exact column value", 'grep -c ",red," data.csv'),
          ('cut -d "," -f N FILE', "take one CSV column", 'cut -d "," -f 2 data.csv'),
          ("sort -n -r | head -n 1", "biggest number first, keep one", "... | sort -n -r | head -n 1"),
          ("grep TEXT FILE > NEW", "save matching lines in a new file", 'grep ",red," data.csv > red.csv'),
          SUBMIT, CHECK],
         {"sprint.csv": gen_sprint()},
         parts=[("How many tickets belong to the workflow component?", "11"),
                ("What is the biggest story-point value of a single ticket?", "21"),
                ("Create workflow.csv with only the workflow lines (completes by itself)",
                 lambda g: content("workflow.csv", WORKFLOW_LINES)(g))],
         hint='grep -c ",workflow," sprint.csv ; cut -d "," -f 3 sprint.csv | sort -n -r | head -n 1 ; '
              'grep ",workflow," sprint.csv > workflow.csv'),
    task("Feature work", "ATL-150", "Release post-mortem", "Critical", "Tech lead",
         [f"Final case. The incidents endpoint {API}/api/incidents lists all Atlas incidents (it "
          "needs your token). Find the critical incident that is still open, find in its "
          "server's log when the first ERROR happened today, and write the post-mortem file.",
          "Server logs: ~/incident/<year>/<month>/<day>/<server>.log. Today is 2026-11-12."],
         "All 3 steps done: two answers and postmortem.txt.",
         [('curl -H "HEADER" URL', "call a protected API (the header format is in the 401 error)",
           f'curl -H "Accept: text/plain" {API}/status'),
          ("... | grep a | grep b", "keep lines that contain BOTH words", "... | grep WARN | grep disk"),
          ('find FOLDER -name "PATTERN"', "find a file by name", 'find projects -name "*.log"'),
          ("grep WORD FILE | head -n 1", "the first matching line", "grep WARN server.log | head -n 1"),
          ("echo TEXT >> FILE", "add a line to a file", 'echo "line two" >> notes.md'),
          SUBMIT, CHECK],
         {"incident/README.txt": "One folder per day: incident/<year>/<month>/<day>/<server>.log",
          "incident/2026/11/11/atlas-db-03.log": "01:00 INFO ok\n01:30 ERROR replica lag\n01:40 INFO ok",
          "incident/2026/11/12/atlas-db-02.log": "00:10 INFO ok\n02:55 ERROR connection reset\n03:00 INFO ok",
          "incident/2026/11/12/atlas-db-03.log": "\n".join(
              ["02:00 INFO backup started", "02:30 WARN disk usage 91%", "02:58 WARN disk usage 98%",
               "03:12 ERROR disk full on /var - writes rejected", "03:13 ERROR query failed",
               "03:15 ERROR replica stopped", "03:40 INFO on-call paged"])},
         parts=[("Which incident is critical AND still open? (its ID)", "INC-9003"),
                ("At what time (HH:MM) was the first ERROR today on that incident's server?", "03:12"),
                ("Write postmortem.txt with exactly 3 lines:  incident: <ID>  /  host: <server>  /  "
                 "first error: <HH:MM>   (completes by itself)",
                 lambda g: content("postmortem.txt", ["incident: INC-9003", "host: atlas-db-03",
                                                      "first error: 03:12"])(g))],
         hint=f'curl -H "Authorization: Bearer {TOKEN}" {API}/api/incidents | grep critical | grep open ; '
              'grep ERROR incident/2026/11/12/atlas-db-03.log | head -n 1 ; '
              'echo "incident: INC-9003" > postmortem.txt ; echo "host: atlas-db-03" >> postmortem.txt ; '
              'echo "first error: 03:12" >> postmortem.txt'),
]
from .vaults import VAULTS, NUDGES as _VAULT_NUDGES  # noqa: E402
from .missions import apply as _tell_story  # noqa: E402

# after every 5 missions, Pip breaks into a vault: a boss mission that combines those 5 (vaults.py)
LEVELS = [lv for k in range(0, len(LEVELS), 5) for lv in LEVELS[k:k + 5] + [VAULTS[k // 5]]]
NUDGES.update(_VAULT_NUDGES)
_tell_story(LEVELS)
TOTAL = len(LEVELS)
