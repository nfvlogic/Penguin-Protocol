"""The 30 Horizon tickets. Edit this file to change or add tickets.

Each ticket has either an `answer` (submit it), `checks` (completes by itself) or
`parts` (several steps; a step goal is an answer string/tuple or a check function).

RULE FOR CARDS: examples ("e.g. ...") must use OTHER files, folders and hosts than the
ticket, and must never contain an answer. tests/test_linuxip.py checks this automatically.
"""
from .cmd_dev import ghash
from .cmd_sys import tar_members
from .core import API, HOME, TOKEN
from .tickets_data import (COSTS, COSTS_PRD, COSTS_TOP, DEPLOY_SH, EXPORT_ROWS, EXPORT_OPEN, EXPORT_TEXT,  # noqa: F401
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
    task("Onboarding", "HZN-101", "Run Horizon locally", "Normal", "Tech lead",
         ["Welcome to the Horizon team! Horizon is our internal stage-gate app (Flask + MySQL). "
          "Before you pick up feature work, you need to run it on your machine.",
          "Start with the welcome file in your home folder: it tells you where the project "
          "documentation is. Find the port the app uses when you run it locally."],
         "You submit the local port number.",
         [LS, CAT, CD, SUBMIT],
         {"welcome.txt": "Welcome to the Horizon team!\nThe code is in ~/horizon. Start with README.md there.",
          "notes.txt": "Old note: POPMAPS used port 8080. Not valid any more.",
          "horizon/README.md": "# Horizon\nInternal stage-gate app (Flask + MySQL). Formerly POPMAPS.\n\n"
                               "Run locally:\n  flask run --port 5050\n\nMore setup help: docs/setup.md",
          "horizon/docs/setup.md": "1. Create a virtual env\n2. Install requirements\n3. Run (see README)"},
         answer="5050", hint="cat welcome.txt ; cd horizon ; cat README.md"),
    task("Onboarding", "HZN-102", "Which database does TST use?", "Normal", "Platform team",
         ["We are moving TST to a new database server and need to confirm what the code is "
          "configured to use today.",
          "Each environment has its own config file in the project. There is also an old "
          "config folder left over from POPMAPS: the README says if it is still valid."],
         "You submit the DB_HOST used by the TST environment.",
         [TREE, CD, ("cd ..", "go up one folder", "cd .."), ("pwd", "show the folder you are in", "pwd"), CAT, SUBMIT],
         {"horizon/README.md": "# Horizon\nConfig per environment lives in config/ (dev.py, tst.py, prd.py).\n"
                               "config/legacy/ is the old POPMAPS setup - do not use.",
          "horizon/config/dev.py": 'DB_HOST = "localhost"\nDB_NAME = "horizon_dev"',
          "horizon/config/tst.py": 'DB_HOST = "horizon-db-02"\nDB_NAME = "horizon_tst"',
          "horizon/config/prd.py": 'DB_HOST = "horizon-db-03"\nDB_NAME = "horizon"',
          "horizon/config/legacy/tst.py": 'DB_HOST = "popmaps-db-01"  # deprecated'},
         answer="horizon-db-02", hint="tree horizon ; cat horizon/config/tst.py"),
    task("Onboarding", "HZN-103", "App fails to start", "High", "Tech lead",
         ["Your local Horizon crashes on start-up with: Unknown database 'popmaps_dev'. "
          "Somebody started it with an old environment file.",
          "Flask loads settings from hidden files (names that start with a dot) in the project "
          "folder. Find the file that holds the database settings and the correct database "
          "name. The hidden file in your home folder is the OLD one."],
         "You submit the correct DB_NAME from the project's settings file.",
         [("ls -a [FOLDER]", "list ALL files, hidden ones (.name) too", "ls -a reports"), CD, CAT,
          ("cd ~", "go back to your home folder", "cd ~"), SUBMIT],
         {"horizon/.flaskenv": "FLASK_APP=wsgi.py\n# DB settings and secrets are loaded from .env in this folder",
          "horizon/start.log": "09:00 starting Horizon\n09:00 ERROR (1049) Unknown database 'popmaps_dev'",
          "horizon/.env": "DB_HOST=localhost\nDB_NAME=horizon_dev\nDB_USER=horizon\nSECRET_KEY=change-me",
          "horizon/wsgi.py": "from app import create_app\napp = create_app()",
          ".env.old": "DB_NAME=popmaps_dev   # old app name, do not use"},
         answer="horizon_dev", hint="cd horizon ; ls -a ; cat .flaskenv ; cat .env"),
    task("Onboarding", "HZN-104", "Scaffold the Launch date feature", "Normal", "Product owner",
         ["New feature: requestors must enter a desired launch date. Create the empty feature "
          "module so the team can start coding.",
          "Inside ~/horizon/app/features create: a folder launch_date with an empty __init__.py, "
          "an empty routes.py, a subfolder templates, and README.md containing exactly: "
          "Launch date field",
          "Note: plain mkdir only creates one level, and fails if the parent does not exist."],
         "The structure exists. Closes by itself (type check).",
         [CD, ("mkdir -p A/B", "make a folder and any missing parent folders", "mkdir -p reports/2026/q4"),
          ("touch FILE...", "create one or more empty files", "touch a.txt b.txt"),
          ("echo TEXT > FILE", "write text into a file", "echo hello > note.txt"), TREE, CHECK],
         {"horizon/app/__init__.py": "", "horizon/app/features/": ""},
         checks=[("launch_date/__init__.py exists", home_file("horizon/app/features/launch_date/__init__.py")),
                 ("launch_date/routes.py exists", home_file("horizon/app/features/launch_date/routes.py")),
                 ("launch_date/templates/ exists", home_dir("horizon/app/features/launch_date/templates")),
                 ("README.md says: Launch date field",
                  content("horizon/app/features/launch_date/README.md", ["Launch date field"]))],
         hint="cd horizon/app/features ; mkdir -p launch_date/templates ; touch launch_date/__init__.py "
              "launch_date/routes.py ; echo Launch date field > launch_date/README.md"),
    task("Onboarding", "HZN-105", "Clean the repo before the PR", "High", "Code review bot",
         ["Your pull request was blocked: it contains compiled files and a badly named migration.",
          "1) back up the 3 config files (horizon/config, *.py) into ~/backup. 2) rename "
          "horizon/migrations/draft.py to 0040_add_trademark_bu.py. 3) delete every .pyc file "
          "directly in ~/horizon. 4) delete the folder horizon/__pycache__.",
          "The shell expands * before the command runs: a pattern like reports/*.txt becomes "
          "the list of every matching file."],
         "All 4 requirements are met. Closes by itself (type check).",
         [("cp FILES... FOLDER", "copy files; * matches many names", "cp reports/*.txt archive/"),
          ("mv OLD NEW", "rename (or move) a file", "mv old.txt new.txt"),
          ("rm PATTERN", "delete every file that matches a pattern", "rm reports/*.tmp"),
          ("rm -r FOLDER", "delete a folder and everything in it", "rm -r old_reports"),
          ("echo PATTERN", "preview what a * pattern expands to", "echo reports/*.tmp"), CHECK],
         {"horizon/config/dev.py": "DEBUG = True", "horizon/config/tst.py": "DEBUG = False",
          "horizon/config/prd.py": "DEBUG = False", "horizon/app.pyc": "x", "horizon/utils.pyc": "x",
          "horizon/wsgi.pyc": "x", "horizon/wsgi.py": "app = create_app()",
          "horizon/__pycache__/app.cpython-312.pyc": "x",
          "horizon/migrations/0039_add_scope.py": "add_column('request', 'scope')",
          "horizon/migrations/draft.py": "add_column('request', 'trademark_bu')", "backup/": ""},
         checks=[("3 config files are in ~/backup",
                  lambda g: all(g.fs.isfile(f"{HOME}/backup/{e}.py") for e in ("dev", "tst", "prd"))),
                 ("migration renamed to 0040_add_trademark_bu.py",
                  lambda g: g.fs.isfile(HOME + "/horizon/migrations/0040_add_trademark_bu.py")
                  and not g.fs.exists(HOME + "/horizon/migrations/draft.py")),
                 ("no .pyc files left in ~/horizon", no_ext(".pyc", "horizon")),
                 ("horizon/__pycache__ deleted", gone("horizon/__pycache__"))],
         hint="cp horizon/config/*.py backup/ ; mv horizon/migrations/draft.py "
              "horizon/migrations/0040_add_trademark_bu.py ; rm horizon/*.pyc ; rm -r horizon/__pycache__"),
    task("Onboarding", "HZN-106", ".gitignore and changelog", "Normal", "Tech lead",
         ["So this never happens again, create horizon/.gitignore with these 3 lines in order: "
          "__pycache__/  then  *.pyc  then  .env",
          "And add one line at the END of horizon/CHANGELOG.md (do not erase it): "
          "- Added launch date field (HZN-104)",
          "Put text with * or spaces in quotes, so the shell passes it unchanged."],
         "Both files are correct. Closes by itself (type check).",
         [("echo TEXT > FILE", "write a file (overwrites it!)", "echo first > list.txt"),
          ("echo TEXT >> FILE", "add a line at the end of a file", 'echo "second line" >> list.txt'),
          CAT, CHECK],
         {"horizon/CHANGELOG.md": "# Changelog\n- Renamed POPMAPS to Horizon\n- Added requestor role"},
         checks=[(".gitignore has the 3 lines", content("horizon/.gitignore", ["__pycache__/", "*.pyc", ".env"])),
                 ("CHANGELOG.md kept its lines and has the new one at the end",
                  content("horizon/CHANGELOG.md", ["# Changelog", "- Renamed POPMAPS to Horizon",
                                                   "- Added requestor role", "- Added launch date field (HZN-104)"]))],
         hint='echo __pycache__/ > horizon/.gitignore ; echo "*.pyc" >> horizon/.gitignore ; '
              'echo .env >> horizon/.gitignore ; echo "- Added launch date field (HZN-104)" >> horizon/CHANGELOG.md'),
    # ------------------------------------------------------------ CODE SEARCH
    task("Code search", "HZN-207", "Which gate rules are active?", "Normal", "QA team",
         ["QA reports that Gate approvals behave differently than documented. They need to know "
          "which version of the gate rules is running.",
          "Several files in the project have 'gate' in their name: code, an old copy, a test and "
          "a template. Only the one in app/workflow (not in old/) is active."],
         "You submit the RULES_VERSION of the active rules file.",
         [('find FOLDER -name "PATTERN"', "search names in all subfolders; quote the * pattern",
           'find projects -name "*.md"'),
          ("cat PATH", "read a file by its path", "cat projects/app/main.py"), SUBMIT],
         {"horizon/app/workflow/gate_rules.py": 'RULES_VERSION = "g2-310"\n\ndef approve_gate(project, gate):\n    ...',
          "horizon/app/workflow/old/gate_rules_v1.py": 'RULES_VERSION = "g1-100"  # replaced in October',
          "horizon/tests/test_gate_rules.py": "from app.workflow.gate_rules import approve_gate",
          "horizon/app/templates/gate.html": "<h1>Gate approval</h1>",
          "horizon/app/routes.py": "from .workflow import gate_rules"},
         answer="g2-310", hint='find horizon -name "*gate*" ; cat horizon/app/workflow/gate_rules.py'),
    task("Code search", "HZN-208", "Release blocker hunt", "High", "Release manager",
         ["Release v1.9 is on Friday. Developers mark blocking issues in the code with "
          "TODO(release-blocker). Find it without opening every file.",
          "Search only the application code (horizon/app). The docs also mention the marker "
          "as an example: that one does not count."],
         "You submit the FILE NAME (e.g. main.py) that contains the release blocker.",
         [("grep -r WORD FOLDER", "search every file in a folder", "grep -r FIXME projects"),
          ("grep -n WORD FILE", "show line numbers", "grep -n import main.py"), SUBMIT],
         {"horizon/app/routes.py": "def projects():\n    # TODO: add pagination\n    return []",
          "horizon/app/approvals.py": "def approve(request, user):\n"
                                      "    # TODO(release-blocker): Gate 01 approval skips the requestor check\n    return True",
          "horizon/app/models.py": "class Project:\n    # TODO: rename popmaps_id column\n    pass",
          "horizon/app/sso.py": "# TODO: remove password fallback after SSO go-live",
          "horizon/docs/contributing.md": "Mark blockers like this: TODO(release-blocker): <text>"},
         answer=("approvals.py", "horizon/app/approvals.py"), hint="grep -r release-blocker horizon/app"),
    task("Code search", "HZN-209", "500 errors on TST", "Critical", "QA team",
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
    task("Code search", "HZN-210", "What is deployed on TST?", "Normal", "Product owner",
         ["The product owner asks which Horizon version is on TST right now. deploy.log has 240 "
          "lines with the newest entry at the bottom. The first line is the previous release."],
         "You submit the deployed version (e.g. v0.0.0).",
         [("wc -l FILE", "count the lines of a file", "wc -l server.log"),
          ("head -n N FILE", "show the first N lines", "head -n 3 server.log"),
          ("tail -n N FILE", "show the last N lines", "tail -n 3 server.log"), SUBMIT],
         {"deploy.log": gen_deploy_log()}, answer="v1.8.3", hint="tail -n 1 deploy.log"),
    task("Code search", "HZN-211", "Failing unit tests", "High", "CI pipeline",
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
    task("Code search", "HZN-212", "Who reads the secret key?", "High", "Security team",
         ["Security wants to rotate the SECRET_KEY before go-live. First they need to know how many "
          "Python source files in the application code (horizon/app) use it.",
          "The word also appears in templates, docs and settings files: those do not count. Only "
          "list the files, do not print every matching line."],
         "You submit the number of .py files in horizon/app that mention SECRET_KEY.",
         [("grep -rl WORD FOLDER", "list only the NAMES of the files that contain a word", "grep -rl TODO projects"),
          ('grep -r WORD FOLDER --include="PATTERN"', "search only files whose name matches the pattern",
           'grep -r TODO projects --include="*.js"'),
          ("a | wc -l", "count the lines a command prints", "grep -rl TODO projects | wc -l"), SUBMIT],
         {"horizon/app/__init__.py": 'app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]',
          "horizon/app/auth.py": 'token = sign(current_app.config["SECRET_KEY"], user)',
          "horizon/app/sso.py": "# SSO uses its own keys; falls back to SECRET_KEY in dev\nkey = get_secret(\"SECRET_KEY\")",
          "horizon/app/routes.py": "def projects():\n    return list_projects()",
          "horizon/app/templates/admin.html": "<p>Rotate SECRET_KEY every 90 days</p>",
          "horizon/tests/test_auth.py": 'SECRET_KEY = "test"',
          "horizon/docs/security.md": "The SECRET_KEY must never be committed.",
          "horizon/.env": "SECRET_KEY=change-me"},
         answer="3", hint='grep -rl SECRET_KEY horizon/app --include="*.py" | wc -l'),
    # ------------------------------------------------------------ PIPES
    task("Pipes", "HZN-312", "Migration conflict", "High", "CI pipeline",
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
    task("Pipes", "HZN-313", "Which endpoint is broken?", "Critical", "Monitoring",
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
    task("Pipes", "HZN-314", "Pre-deploy check", "Normal", "Change board",
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
    task("Text tools", "HZN-315", "Export from Windows", "Normal", "Scrum master",
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
    task("Text tools", "HZN-316", "TST is not like PRD", "High", "QA team",
         ["A bug only happens on PRD. Ops says the TST and PRD settings should differ in just 3 places: "
          "the database host, the database name and DEBUG. Check if that is true.",
          "Compare the two config files line by line. Lines starting with < are from the first file, "
          "lines starting with > from the second."],
         "Both questions answered.",
         [("diff FILE1 FILE2", "show the lines that differ (< first file, > second file)", "diff old.conf new.conf"),
          ("diff -u FILE1 FILE2", "same in the format git uses (- removed, + added)", "diff -u old.conf new.conf"),
          CAT, SUBMIT],
         {"horizon/config/tst.py": 'DB_HOST = "horizon-db-02"\nDB_NAME = "horizon_tst"\nDEBUG = True\nPOOL_SIZE = 5\nCACHE_TTL = 300\nSESSION_MINUTES = 30',
          "horizon/config/prd.py": 'DB_HOST = "horizon-db-03"\nDB_NAME = "horizon"\nDEBUG = False\nPOOL_SIZE = 5\nCACHE_TTL = 30\nSESSION_MINUTES = 30'},
         parts=[("Besides host, name and DEBUG, which setting is different? (its name)", "CACHE_TTL"),
                ("What value does PRD use for that setting?", "30")],
         hint="diff horizon/config/tst.py horizon/config/prd.py"),
    task("Text tools", "HZN-317", "Move TST to the new database", "High", "Platform team",
         ["TST moves to the new database server horizon-db-new. In horizon/config/tst.py the old server "
          "horizon-db-02 appears in TWO lines (host and URL): both must change, nothing else.",
          "Never edit by hand what a command can do for you, and always keep a backup first: copy the "
          "file to tst.py.bak in the same folder, then change the original. Do not touch prd.py."],
         "tst.py points to the new server everywhere, tst.py.bak keeps the original. Closes by itself (type check).",
         [("cp FILE FILE.bak", "make a backup copy next to the file", "cp app.conf app.conf.bak"),
          ("sed 's/OLD/NEW/g' FILE", "PREVIEW: print the file with every OLD replaced by NEW (file unchanged)",
           "sed 's/red/blue/g' colors.txt"),
          ("sed -i 's/OLD/NEW/g' FILE", "really change the file (-i = in place)", "sed -i 's/red/blue/g' colors.txt"),
          ("diff FILE1 FILE2", "check what changed", "diff a.txt b.txt"), CAT, CHECK],
         {"horizon/config/tst.py": TST_CONFIG,
          "horizon/config/prd.py": 'DB_HOST = "horizon-db-03"\nDB_URL = "mysql+pymysql://horizon@horizon-db-03/horizon"\nDB_NAME = "horizon"'},
         checks=[("tst.py.bak is a copy of the original", lambda g: g.fs.d.get(HOME + "/horizon/config/tst.py.bak") == TST_CONFIG),
                 ("tst.py uses horizon-db-new in both lines and nothing else changed",
                  lambda g: g.fs.d.get(HOME + "/horizon/config/tst.py") == TST_CONFIG_NEW),
                 ("prd.py was not touched", lambda g: "horizon-db-03/horizon\"" in g.fs.d.get(HOME + "/horizon/config/prd.py", ""))],
         hint="cp horizon/config/tst.py horizon/config/tst.py.bak ; sed -i 's/horizon-db-02/horizon-db-new/g' "
              "horizon/config/tst.py ; diff horizon/config/tst.py.bak horizon/config/tst.py"),
    task("Text tools", "HZN-318", "Who keeps asking for missing pages?", "High", "Security team",
         ["traffic.log has today's API requests: <ip> <method> <path> <status> <time>. Someone is probing "
          "for pages that do not exist (HTTP 404). The path itself can contain 404 too: a plain grep would "
          "count the wrong lines.",
          "awk works with columns: $1 is the first column, $4 the fourth. It can test a column and add up numbers."],
         "All 3 steps are answered.",
         [("awk '$N == VALUE' FILE", "print only the lines where column N equals VALUE", "awk '$2 == \"GET\"' web.log"),
          ("awk '{print $N}' FILE", "print column N of every line", "awk '{print $3}' web.log"),
          ("awk '$N == V {s += $M} END {print s}' FILE", "add up column M for the matching lines, print the total at the end",
           "awk '$1 == \"10.0.0.9\" {s += $2} END {print s}' sales.log"),
          ("a | sort | uniq -c | sort -n -r", "count and rank", "... | sort | uniq -c | sort -n -r"),
          ("wc -l", "count lines", "awk '$1 > 5' nums.txt | wc -l"), SUBMIT],
         {"traffic.log": "\n".join(TRAFFIC)},
         parts=[("How many requests got the status 404?", TRAFFIC_404),
                ("Which IP address made most of those 404 requests?", "10.20.30.66"),
                ("What is the total time in ms of ALL requests of that IP? (the time column ends in ms: awk reads the number)", TRAFFIC_SUM)],
         hint="awk '$4 == 404' traffic.log | wc -l ; awk '$4 == 404 {print $1}' traffic.log | sort | uniq -c | sort -n -r ; "
              "awk '$1 == \"10.20.30.66\" {s += $5} END {print s}' traffic.log"),
    task("Text tools", "HZN-319", "Cloud costs per environment", "Normal", "Finance",
         ["Finance asks what Horizon costs in the cloud. costs.csv has one line per service and environment: "
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
    # ------------------------------------------------------------ ENVIRONMENTS
    task("Environments", "HZN-415", "PRD database failover", "Critical", "Platform team",
         ["PRD points to horizon-db-01, which stopped answering. There are two replicas: "
          "horizon-db-02 and horizon-db-03. We must switch Horizon to the one that is alive.",
          "Server names and their IPs are in /etc/hosts. Real ping never stops by itself: "
          "send a fixed number of packets."],
         "You submit the IP address of the database replica that answers.",
         [("ip addr", "show the IP addresses of this computer", "ip addr"),
          ("cat /etc/hosts", "all server names and their IPs", "cat /etc/hosts"),
          ("grep TEXT FILE", "show matching lines", "grep gateway /etc/hosts"), PING, SUBMIT],
         answer="10.20.30.12", hint="ping -c 3 horizon-db-02 ; ping -c 3 horizon-db-03 ; grep horizon-db /etc/hosts"),
    task("Environments", "HZN-416", "Monitoring alerts", "High", "Monitoring",
         ["alerts.log has today's Horizon alerts. Most were resolved automatically. One host is "
          "still down and the alert only shows its IP.",
          "Find the unresolved alert, turn the IP into a server name, and confirm it is down."],
         "You submit the NAME of the server that is down.",
         [CAT, ("grep -v WORD FILE", "hide lines containing a word", "grep -v INFO server.log"),
          ("grep IP /etc/hosts", "find the name of an IP", "grep 127.0.0.1 /etc/hosts"), PING, SUBMIT],
         {"alerts.log": "08:10 host 10.20.30.31 high memory RESOLVED 08:12\n"
                        "08:55 host 10.20.30.12 high cpu RESOLVED 09:01\n"
                        "09:42 host 10.20.30.13 not responding (3 checks failed)\n"
                        "09:50 host 10.20.30.33 slow disk RESOLVED 09:58"},
         answer="horizon-db-03", hint="grep -v RESOLVED alerts.log ; grep 10.20.30.13 /etc/hosts"),
    task("Environments", "HZN-417", "PRD disk is full", "Critical", "Monitoring",
         ["Monitoring says Horizon on horizon-prd stopped writing logs. You do not log in to servers to look "
          "around: you ask them one question at a time with ssh.",
          "Run  ssh analyst@horizon-prd COMMAND  to run COMMAND on that server (put the command in quotes if "
          "it has spaces). Find the full disk, save the proof, then find the biggest file in the folder horizon inside the server's log directory (on Linux, logs live in /var)."],
         "All 3 steps are done.",
         [("ssh USER@HOST \"COMMAND\"", "run one command on another server and show its output", 'ssh analyst@gateway "uptime"'),
          ("df -h", "disk space per disk: look at Use% and Mounted on", "df -h"),
          ("ls -l FOLDER", "file sizes are in column 5", "ls -l /srv/data"),
          ("sort -k5 -n -r | head -n 1", "biggest number in column 5 first, keep one", "... | sort -k5 -n -r | head -n 1"),
          ("ssh USER@HOST \"CMD\" > FILE", "save the server's answer in a local file", 'ssh analyst@gateway "date" > when.txt'),
          SUBMIT, CHECK],
         parts=[("Which mount point of horizon-prd is at 100%?", "/var/log"),
                ("Save the df -h output of horizon-prd in ~/prd_disk.txt (completes by itself)",
                 lambda g: "/var/log" in g.fs.d.get(HOME + "/prd_disk.txt", "") and "Filesystem" in g.fs.d.get(HOME + "/prd_disk.txt", "")),
                ("Which file in the Horizon log folder of that server is the biggest? (file name)", "debug.log")],
         hint='ssh analyst@horizon-prd "df -h" ; ssh analyst@horizon-prd "df -h" > prd_disk.txt ; '
              'ssh analyst@horizon-prd "ls -l /var/log/horizon | sort -k5 -n -r | head -n 1"',
         setup=setup_417),
    # ------------------------------------------------------------ API
    task("API", "HZN-517", "API access token", "Normal", "Integration team",
         ["The Power BI team wants to read Horizon data through its REST API. First you need a "
          f"token from the token endpoint: {API}/token",
          "Like real curl, the output is only the response body. Read the error messages and "
          "adjust your request."],
         "You submit the token.",
         [("curl URL", "send a web request and show the answer", f"curl {API}/status"),
          ("curl -i URL", "also show the HTTP status (200, 400, 403...)", f"curl -i {API}/status"),
          ("URL?key=value", "send data in the URL (a query); quote the URL", f'curl "{API}/search?q=gate"'),
          ("whoami", "print your user name", "whoami"), SUBMIT],
         answer=TOKEN, hint=f'curl {API}/token ; whoami ; curl "{API}/token?user=analyst"'),
    task("API", "HZN-518", "Project stage from the API", "Normal", "Product owner",
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
    task("API", "HZN-519", "Role audit before go-live", "High", "Security team",
         [f"Before go-live, security wants to know how many Horizon users are admins. {API}/api/users "
          "returns one JSON user per line. Save it to users.json first (auditors want the file).",
          "Careful: a pending 'admin-request' is not an admin yet."],
         "You submit the number of real admins.",
         [("curl URL > FILE", "save the answer into a file", f"curl {API}/status > status.json"),
          CAT, ("grep -c TEXT FILE", "count matching lines", "grep -c up status.json"),
          ("grep -c '\"TEXT\"' FILE", "include the quotes to match one exact JSON value",
           "grep -c '\"up\"' status.json"), SUBMIT],
         answer="3", hint=f"curl {API}/api/users > users.json ; grep -c '\"admin\"' users.json"),
    task("API", "HZN-520", "Slow database incident", "Critical", "Tech lead",
         ["Users say Horizon was very slow TODAY (2026-11-12). The DBA suspects horizon-db-02. "
          "We need the number of ERROR lines in today's log of that server.",
          "Logs are in ~/incident, one folder per day. The same server has logs on other days "
          "too: use only today's."],
         "You submit the number of ERROR lines in today's log of that server.",
         [('find FOLDER -name "PATTERN"', "find files by name; * is a wildcard", 'find projects -name "*.log"'),
          TREE, ("grep -c WORD FILE", "count matching lines", "grep -c WARN server.log"),
          ("grep WORD FILE | wc -l", "the same, with a pipe", "grep WARN server.log | wc -l"), SUBMIT],
         gen_incident("horizon-db-02", 7), answer="7",
         hint='find incident -name "horizon-db-02*" ; grep -c ERROR incident/2026/11/12/horizon-db-02.log'),
    # ------------------------------------------------------------ GIT & PYTHON
    task("Git & Python", "HZN-701", "Set up the dev environment", "High", "Tech lead",
         ["Your laptop was reinstalled. Get Horizon running again the standard way: a virtual "
          "environment in a folder called .venv inside ~/horizon, the requirements installed "
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
         {"horizon/README.md": "# Horizon\nLocal setup: create a venv, install requirements.txt, "
                               "then: flask run --port 5050",
          "horizon/requirements.txt": REQUIREMENTS, "horizon/wsgi.py": "from app import create_app\napp = create_app()",
          "horizon/.env": "DB_HOST=localhost\nDB_NAME=horizon_dev", "horizon/app/__init__.py": "def create_app(): ..."},
         checks=[(".venv created in ~/horizon", home_dir("horizon/.venv")),
                 ("the venv is active", lambda g: g.venv == HOME + "/horizon/.venv"),
                 ("requirements installed in the venv", lambda g: "flask" in g.installed.get(HOME + "/horizon/.venv", {})),
                 ("Horizon started with flask run", lambda g: g.flask_ran)],
         hint="cd horizon ; python3 -m venv .venv ; source .venv/bin/activate ; "
              "pip install -r requirements.txt ; flask run --port 5050"),
    task("Git & Python", "HZN-702", "Missing environment variables", "High", "Platform team",
         ["On the servers there is no .env file: settings come from environment variables "
          "(Azure App Service works the same way). We copied that setup to your machine: the "
          "venv in ~/horizon/.venv is ready, but Horizon refuses to start.",
          "Activate the venv, run flask, read the error, then set what is missing as environment "
          "variables. .env.example shows the values for local development. No spaces around =."],
         "The variables are set and flask run works. Closes by itself (type check).",
         [CD, ("source FOLDER/bin/activate", "activate an existing venv", "source myenv/bin/activate"),
          ("flask run", "start the app and read the error", "flask run"), CAT,
          ("export NAME=value", "set an environment variable", "export LOG_LEVEL=debug"),
          ("echo $NAME", "show the value of a variable", "echo $LOG_LEVEL"),
          ("env", "list all environment variables", "env | grep LOG"), CHECK],
         {"horizon/requirements.txt": REQUIREMENTS, "horizon/wsgi.py": "from app import create_app\napp = create_app()",
          "horizon/.env.example": "# copy these into your environment\nDB_HOST=<server>\nDB_NAME=<database>\n"
                                  "# local development: DB_HOST=localhost  DB_NAME=horizon_dev",
          "horizon/app/__init__.py": "def create_app(): ..."},
         checks=[("DB_HOST is set correctly", lambda g: g.env.get("DB_HOST") == "localhost"),
                 ("DB_NAME is set correctly", lambda g: g.env.get("DB_NAME") == "horizon_dev"),
                 ("Horizon started with flask run", lambda g: g.flask_ran)],
         hint="cd horizon ; source .venv/bin/activate ; flask run ; cat .env.example ; export DB_HOST=localhost ; "
              "export DB_NAME=horizon_dev ; flask run",
         setup=setup_702),
    task("Git & Python", "HZN-703", "What is in my working copy?", "Normal", "Tech lead",
         ["You are taking over a colleague's work on Horizon. Before touching anything, find "
          "out where the repository stands.",
          "Every answer comes from git, run inside ~/horizon. git only works inside the project folder."],
         "All 3 steps are answered.",
         [CD, ("git status", "branch, changed files and untracked files", "git status"),
          ("git branch", "list branches; * marks the current one", "git branch"),
          ("git diff", "show changes that are not committed yet", "git diff"),
          ("git log --oneline", "short list of commits: hash + message", "git log --oneline"), SUBMIT],
         parts=[("Which branch is checked out?", "feature/requestor-role"),
                ("Which tracked file has changes that are not committed? (its path)", ("app/routes.py", "routes.py")),
                ("What is the short hash of the commit 'Add trademark BU dropdown'?", ghash("Add trademark BU dropdown"))],
         hint="cd horizon ; git status ; git log --oneline", setup=setup_703),
    task("Git & Python", "HZN-704", "Branch, fix and commit", "High", "Tech lead",
         ["Team rule: never commit straight to main. Create the branch feature/launch-date, add "
          "the migration migrations/0042_add_launch_date.py with one line: "
          "add_column('request', 'launch_date')",
          "Commit it with a message that starts with the ticket number HZN-621. "
          "Made a mistake on main? Type reset to start this ticket again."],
         "All requirements are met. Closes by itself (type check).",
         [CD, ("git checkout -b NAME", "create a new branch and switch to it", "git checkout -b fix/typo"),
          ('echo "TEXT" > FILE', "write a file; double quotes keep ( ) and ' safe", "echo \"print('hi')\" > hello.py"),
          ("git status", "see what changed", "git status"),
          ("git add FILE", "stage a file for the next commit", "git add hello.py"),
          ('git commit -m "MSG"', "save the staged changes as a commit", 'git commit -m "HZN-000 Fix typo"'),
          ("git log --oneline", "check your commit", "git log --oneline"), CHECK],
         checks=[("on the new feature branch", lambda g: g.repo and g.repo["branch"] == "feature/launch-date"),
                 ("last commit adds the migration with the right line",
                  lambda g: g.repo and g.git_head().get("tree", {}).get("migrations/0042_add_launch_date.py", "").strip()
                  == "add_column('request', 'launch_date')"),
                 ("commit message starts with HZN-621", lambda g: g.repo and g.git_head().get("msg", "").startswith("HZN-621")),
                 ("main was not touched", lambda g: g.repo and len(g.repo["branches"]["main"]) == g.mark.get("main_len")),
                 ("nothing left uncommitted", lambda g: g.repo and g.git_clean())],
         hint="cd horizon ; git checkout -b feature/launch-date ; echo \"add_column('request', 'launch_date')\" > "
              "migrations/0042_add_launch_date.py ; git add migrations/0042_add_launch_date.py ; "
              "git commit -m \"HZN-621 Add launch date column\"",
         setup=setup_704),
    task("Git & Python", "HZN-705", "Review before the pull request", "High", "Code review",
         ["Your SSO branch is almost ready for a pull request. Always review your changes "
          "before you push: something slipped in that should not be there.",
          "git has two kinds of changes: not staged yet, and staged (what WILL go into the next commit)."],
         "All 3 steps are done.",
         [CD, ("git status", "see staged and unstaged changes", "git status"),
          ("git diff", "show unstaged changes (- old line, + new line)", "git diff"),
          ("git restore FILE", "throw away the uncommitted changes in a file", "git restore notes.md"),
          ("git diff --staged", "show what is staged for the next commit", "git diff --staged"), SUBMIT, CHECK],
         parts=[("An accidental change slipped into a config file. Which DB_HOST value was put in?", "popmaps-db-01"),
                ("Undo it: restore that file to the committed version (completes by itself)",
                 lambda g: g.repo and g.git_working().get("config/tst.py") == g.git_head()["tree"].get("config/tst.py")),
                ("Which package is staged to be added to requirements.txt? (name only)", ("requests", "requests==2.32.3"))],
         hint="cd horizon ; git diff ; git restore config/tst.py ; git diff --staged", setup=setup_705),
    # ------------------------------------------------------------ SERVERS
    task("Servers", "HZN-801", "Runaway process", "Critical", "Platform team",
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
    task("Servers", "HZN-802", "Secrets everyone can read", "High", "Security team",
         ["The audit found files with the wrong permissions. In ls -l the first column shows them: three "
          "letters for the owner (u), three for the group (g), three for everybody else (o).",
          "Numbers: r=4, w=2, x=1, added per group. 640 = rw- r-- --- . Fix three things: horizon/.env only "
          "readable and writable by its owner; horizon/scripts/deploy.sh runnable by owner and group but "
          "not by others (owner all, group read+execute); horizon/config/prd.py readable by everybody but "
          "writable only by the owner."],
         "All 3 files have the right permissions. Closes by itself (type check).",
         [("ls -la FOLDER", "long listing with permissions, including hidden files", "ls -la reports"),
          ("stat FILE", "shows the permissions as a number too, e.g. (0644/-rw-r--r--)", "stat report.txt"),
          ("chmod NNN FILE", "set permissions with 3 digits: owner, group, others", "chmod 640 report.txt"),
          ("chmod u+x FILE", "or change one thing: u/g/o + or - r/w/x", "chmod g-w report.txt"), CHECK],
         {"horizon/.env": "DB_HOST=localhost\nSECRET_KEY=change-me",
          "horizon/scripts/deploy.sh": "#!/bin/bash\necho deploying",
          "horizon/config/prd.py": 'DB_HOST = "horizon-db-03"'},
         checks=[(".env is 600 (only the owner can read and write)", lambda g: g.fs.mode(HOME + "/horizon/.env") == 0o600),
                 ("deploy.sh is 750 (owner all, group read+execute, others nothing)",
                  lambda g: g.fs.mode(HOME + "/horizon/scripts/deploy.sh") == 0o750),
                 ("prd.py is 644 (everybody reads, only the owner writes)",
                  lambda g: g.fs.mode(HOME + "/horizon/config/prd.py") == 0o644)],
         hint="ls -la horizon ; chmod 600 horizon/.env ; chmod 750 horizon/scripts/deploy.sh ; chmod 644 horizon/config/prd.py",
         setup=setup_802),
    task("Servers", "HZN-803", "The API service will not start", "Critical", "Tech lead",
         ["horizon-api is a service of your own user (a systemd user service) and it is in a failed state. "
          "Never guess: read what the service says about itself, then fix the cause.",
          "Services of your own user need --user in front of the action. After fixing the cause, start it "
          "again and check that it is active."],
         "The cause is found and the service is active again.",
         [("systemctl --user status NAME", "state of a service and its last log lines", "systemctl --user status myapp"),
          ("journalctl --user -u NAME -n N", "the last N log lines of a service", "journalctl --user -u myapp -n 20"),
          ("ls -l FILE", "check the permissions of a file (see also chmod)", "ls -l notes.txt"),
          ("chmod NNN FILE", "change permissions", "chmod 600 notes.txt"),
          ("systemctl --user restart NAME", "start the service again", "systemctl --user restart myapp"), SUBMIT, CHECK],
         {"horizon/api.conf": "port = 5050\ndb = horizon_dev"},
         parts=[("Which file can the service not read? (its full path)",
                 ("/home/analyst/horizon/api.conf", "~/horizon/api.conf", "horizon/api.conf")),
                ("Fix the cause and restart the service so it is active (completes by itself)",
                 lambda g: g.svc.get("horizon-api", {}).get("state") == "active")],
         hint="systemctl --user status horizon-api ; journalctl --user -u horizon-api -n 5 ; "
              "chmod 640 horizon/api.conf ; systemctl --user restart horizon-api",
         setup=setup_803),
    task("Servers", "HZN-804", "Backup before the release", "High", "Release manager",
         ["Before the release, back up the configuration. Put the folder horizon/config into a compressed "
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
         {"horizon/config/dev.py": "DEBUG = True", "horizon/config/tst.py": "DEBUG = False",
          "horizon/config/prd.py": "DEBUG = False", "horizon/README.md": "# Horizon", "backups/": "", "restore/": ""},
         parts=[("Create ~/backups/config-backup.tar.gz with the folder horizon/config (completes by itself)",
                 lambda g: "horizon/config/prd.py" in tar_members(g.fs, HOME + "/backups/config-backup.tar.gz")),
                ("How many .py files are inside the archive?", "3"),
                ("Restore ONLY horizon/config/tst.py into ~/restore (completes by itself)",
                 lambda g: g.fs.isfile(HOME + "/restore/horizon/config/tst.py")
                 and not g.fs.exists(HOME + "/restore/horizon/config/prd.py"))],
         hint="tar -czf backups/config-backup.tar.gz horizon/config ; tar -tzf backups/config-backup.tar.gz | grep -c 'py$' ; "
              "tar -xzf backups/config-backup.tar.gz -C restore horizon/config/tst.py"),
    task("Servers", "HZN-805", "Port 5050 is already in use", "High", "Tech lead",
         ["You start Horizon on port 5050 and it refuses: the port is already taken. Your venv in "
          "~/horizon/.venv is ready and the environment is configured.",
          "Find out which process listens on that port, stop it, and start Horizon on 5050 again. Do not "
          "just pick another port: the front end expects 5050."],
         "Horizon runs on port 5050.",
         [CD, ("source FOLDER/bin/activate", "activate a venv", "source myenv/bin/activate"),
          ("flask run --port N", "start the app and read the error", "flask run --port 8000"),
          ("ss -tlnp", "who listens on which port: TCP, listening, numbers, with the process (PID)", "ss -tlnp | grep 22"),
          ("kill PID", "stop a process", "kill 9999"), SUBMIT, CHECK],
         {"horizon/wsgi.py": "from app import create_app\napp = create_app()", "horizon/requirements.txt": REQUIREMENTS,
          "horizon/app/__init__.py": "def create_app(): ..."},
         parts=[("Start Horizon on port 5050 and read the error. Which PID listens on 5050?", "4388"),
                ("Stop that process and start Horizon on port 5050 (completes by itself)",
                 lambda g: g.flask_port == "5050" and 4388 not in g.procs)],
         hint="cd horizon ; source .venv/bin/activate ; flask run --port 5050 ; ss -tlnp ; kill 4388 ; flask run --port 5050",
         setup=setup_805),
    # ------------------------------------------------------------ FEATURE WORK (multi-step)
    task("Feature work", "HZN-621", "Add the launch date column", "High", "Product owner",
         ["The request form must save a desired launch date. The column does not exist yet: "
          "that is why /requests/new crashes with KeyError: 'launch_date'.",
          "Find the template of the form, find the next free migration number, and write the "
          "migration that adds the column."],
         "All 3 steps are done.",
         [("grep -r WORD FOLDER", "find which file contains a word", "grep -r FIXME projects"),
          ("ls FOLDER", "list a folder", "ls projects"),
          ('echo "TEXT" > FILE', "write a file; double quotes keep ( ) and ' safe", "echo \"print('hi')\" > hello.py"),
          ("cat FILE", "check what you wrote", "cat hello.py"), SUBMIT, CHECK],
         {"horizon/app/templates/request_new.html": "{% extends 'base.html' %}\n{{ request_form }}",
          "horizon/app/templates/request_list.html": "{% extends 'base.html' %}\n{{ table }}",
          "horizon/app/templates/base.html": "<html>{% block content %}{% endblock %}</html>",
          "horizon/migrations/0038_add_requestor_role.py": "add_column('user', 'role')",
          "horizon/migrations/0039_add_scope.py": "add_column('request', 'scope')",
          "horizon/migrations/0040_add_trademark_bu.py": "add_column('request', 'trademark_bu')",
          "horizon/migrations/0041_add_bu_dropdown.py": "add_column('request', 'bu')"},
         parts=[("Which template renders the request form? (file name)",
                 ("request_new.html", "horizon/app/templates/request_new.html")),
                ("What is the next free migration number? (4 digits)", "0042"),
                ("Create the migration <NUMBER>_add_launch_date.py in horizon/migrations with exactly "
                 "one line: add_column('request', 'launch_date')   (completes by itself)",
                 lambda g: content("horizon/migrations/0042_add_launch_date.py",
                                   ["add_column('request', 'launch_date')"])(g))],
         hint="grep -r request_form horizon/app/templates ; ls horizon/migrations ; "
              "echo \"add_column('request', 'launch_date')\" > horizon/migrations/0042_add_launch_date.py"),
    task("Feature work", "HZN-622", "Brute force on the service account", "Critical", "Security team",
         ["Before SSO goes live, Horizon still allows password login on its server. Overnight, "
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
         parts=[("Which account received the most failed logins?", "svc_horizon"),
                ("That account then logged in successfully. From which IP?", "10.20.30.66"),
                ("Which machine is that IP? (its name in /etc/hosts)", "guest-laptop-07")],
         hint='grep Failed auth.log | cut -d " " -f 9 | sort | uniq -c | sort -n -r ; '
              'grep Accepted auth.log ; grep 10.20.30.66 /etc/hosts'),
    task("Feature work", "HZN-623", "Horizon PRE is down", "Critical", "QA team",
         ["Nobody can test the v1.9 release: the PRE environment does not respond. The load "
          "balancer configs in ~/lb/sites say for each part of Horizon which server is "
          "'primary' and which is 'fallback'.",
          "Find the server that is down, which site uses it as primary, and whether its "
          "fallback can take over. A server can be primary in one file and fallback in another."],
         "All 3 steps are answered.",
         [("grep TEXT FILE", "list matching lines, e.g. servers in /etc/hosts", "grep gateway /etc/hosts"), PING,
          ("grep -r TEXT FOLDER", "search all files in a folder", "grep -r timeout projects"),
          ("cat FILE", "read one config", "cat projects/site.conf"), SUBMIT],
         {"lb/lb.conf": "include sites/*.conf;",
          "lb/sites/requests.conf": "site = requests.horizon.local\nprimary = horizon-pre\nfallback = horizon-tst",
          "lb/sites/reports.conf": "site = reports.horizon.local\nprimary = horizon-tst\nfallback = horizon-pre",
          "lb/sites/admin.conf": "site = admin.horizon.local\nprimary = horizon-prd\nfallback = horizon-tst"},
         parts=[("Which Horizon server is down? (its name)", "horizon-pre"),
                ("Which config file uses it as PRIMARY? (file name)", ("requests.conf", "lb/sites/requests.conf")),
                ("Is that site's fallback online? Submit the fallback's IP address", "10.20.30.31")],
         hint='grep horizon /etc/hosts ; ping -c 3 horizon-pre ; grep -r "primary = horizon-pre" lb ; '
              'cat lb/sites/requests.conf ; ping -c 3 horizon-tst'),
    task("Feature work", "HZN-624", "Sprint review numbers", "High", "Scrum master",
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
    task("Feature work", "HZN-625", "Release post-mortem", "Critical", "Tech lead",
         [f"Final case. The incidents endpoint {API}/api/incidents lists all Horizon incidents (it "
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
          "incident/2026/11/11/horizon-db-03.log": "01:00 INFO ok\n01:30 ERROR replica lag\n01:40 INFO ok",
          "incident/2026/11/12/horizon-db-02.log": "00:10 INFO ok\n02:55 ERROR connection reset\n03:00 INFO ok",
          "incident/2026/11/12/horizon-db-03.log": "\n".join(
              ["02:00 INFO backup started", "02:30 WARN disk usage 91%", "02:58 WARN disk usage 98%",
               "03:12 ERROR disk full on /var - writes rejected", "03:13 ERROR query failed",
               "03:15 ERROR replica stopped", "03:40 INFO on-call paged"])},
         parts=[("Which incident is critical AND still open? (its ID)", "INC-9003"),
                ("At what time (HH:MM) was the first ERROR today on that incident's server?", "03:12"),
                ("Write postmortem.txt with exactly 3 lines:  incident: <ID>  /  host: <server>  /  "
                 "first error: <HH:MM>   (completes by itself)",
                 lambda g: content("postmortem.txt", ["incident: INC-9003", "host: horizon-db-03",
                                                      "first error: 03:12"])(g))],
         hint=f'curl -H "Authorization: Bearer {TOKEN}" {API}/api/incidents | grep critical | grep open ; '
              'grep ERROR incident/2026/11/12/horizon-db-03.log | head -n 1 ; '
              'echo "incident: INC-9003" > postmortem.txt ; then >> for the other 2 lines'),
]
TOTAL = len(LEVELS)
