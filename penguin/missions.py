"""The story layer: every ticket is an operation. You are an undercover operative inside Atlas.

Only the presentation lives here (codename, handler, phase, threat level and the first paragraph of the
briefing). The answers, files and checks stay in tickets.py. Keep every literal value (ports, hosts, file
names, numbers) of the original text: the answer variants in variants.py replace them by seed.
"""

PHASE = {"Onboarding": "Infiltration", "Code search": "Reconnaissance", "Pipes": "Surveillance",
         "Text tools": "Forensics", "Environments": "Lateral movement", "API": "The back channel",
         "Git & Python": "Deep cover", "Servers": "Inside the walls", "Scripting": "Tradecraft",
         "Feature work": "The final operation"}

HANDLER = {"Tech lead": "Control", "Platform team": "Quartermaster", "Product owner": "The Broker",
           "QA team": "Field tester", "Security team": "Counter-intel", "Monitoring": "Watchtower",
           "Code review bot": "The Auditor", "Code review": "The Auditor", "CI pipeline": "Autopilot",
           "Release manager": "The Courier", "Change board": "The Committee", "Integration team": "Contact",
           "Finance": "The Paymaster", "Scrum master": "The Dispatcher"}

THREAT = {"Normal": "Low", "High": "Elevated", "Critical": "Critical"}

# ticket -> (operation codename, first paragraph of the briefing)
OPS = {
    "ATL-101": ("Front Door", "You are in. Your contractor badge got you through the front door of Atlas, an internal stage-gate "
                "app (Flask + MySQL), and Control wants proof that your cover holds. Nobody questions an engineer who runs "
                "the app on their own machine, so make it run."),
    "ATL-102": ("Quiet Ledger", "Word from the Quartermaster: the TST environment is about to move to a new database server, "
                "and nobody has written down what it points to today. Whoever knows where TST really keeps its data holds "
                "the keys to the test floor."),
    "ATL-103": ("Wrong Key", "Your first crash, and it is no accident: Atlas dies on start-up with: Unknown database "
                "'compass_dev'. Somebody started it with an old environment file left behind like a trap for the careless."),
    "ATL-104": ("Trojan Folder", "The Broker hands you a cover story: requestors must enter a desired launch date. Building "
                "that feature gives you every reason to create your own folders inside the project without raising "
                "eyebrows. Create the empty feature module."),
    "ATL-105": ("Paper Trail", "Control: before you leave any trace, keep a copy of the evidence. Your pull request was blocked, "
               "and before it is cleaned up there are two preparations: keep a copy of the config files, and give a "
               "migration a proper name."),
    "ATL-106": ("Clean Hands", "The Auditor flagged your pull request: it contains compiled files, the kind of clutter that gets "
                "noticed. Wipe the scene. Delete every .pyc file directly in ~/atlas, and delete the folder atlas/__pycache__."),
    "ATL-107": ("Blank Page", "Good agents leave no fingerprints. So this never happens again, create atlas/.gitignore with "
                "these 3 lines in order: __pycache__/  then  *.pyc  then  .env"),
    "ATL-108": ("Fine Print", "The field testers say Gate approvals do not behave the way the documents promise. Somebody "
                "changed the rules and left the old copies lying around to hide it. Find out which version of the gate "
                "rules is really running."),
    "ATL-109": ("Dead Drop", "Release v1.9 goes out on Friday. Somewhere in the code a developer left a message for the team: "
                "TODO(release-blocker). Find the dead drop without opening every file."),
    "ATL-110": ("Red Herring", "Testers get an error page when they create a new request on TST. app.log has 160 lines from "
                "this morning. Monitoring also sends fake crashes every hour: those are marked as tests and are not real. "
                "Decoys everywhere, so do not chase them."),
    "ATL-111": ("Last Seen", "The Broker wants to know which Atlas version is on TST right now, and nobody will say. deploy.log "
                "has 240 lines with the newest entry at the bottom. The first line is the previous release."),
    "ATL-112": ("Cold Case", "The CI pipeline is red and the team is panicking. test_report.txt lists 40 tests. How many really "
                "failed? Cut through the noise."),
    "ATL-113": ("Skeleton Key", "Counter-intel wants to rotate the SECRET_KEY before go-live, the one secret that unlocks every "
                "session. First they need to know who touches it: how many Python source files in the application code "
                "(atlas/app) use it."),
    "ATL-114": ("Double Agent", "Alembic refuses to upgrade: two developers created a migration with the same revision number, "
                "two agents wearing one identity. migrations_list.txt has one migration per line: <number> <name>."),
    "ATL-115": ("Hot Wire", "Watchtower is flashing red. access.log has today's API traffic. Find the endpoint with the most "
                "HTTP 500 errors. The busiest endpoint is the health check: that is normal, do not just count all lines."),
    "ATL-116": ("Dry Run", "The Committee demands a pre-deploy check before tonight's deployment of v1.9: run the pre-deploy "
                "script deploy.sh and attach its output to the change request. Read it first: never run a script you "
                "have not looked at."),
    "ATL-117": ("Hidden Ink", "The Dispatcher exported tickets_export.csv from a Windows laptop. Counting the open tickets with "
                "grep gives 0, although the file clearly has some. Windows ends every line with a hidden extra character "
                "(a carriage return): invisible ink."),
    "ATL-118": ("Mirror Image", "A bug only happens on PRD. The field tester says the TST and PRD settings should differ in just 3 "
                "places: the database host, the database name and DEBUG. Somebody may have slipped in a change. Check if "
                "that is true."),
    "ATL-119": ("Quiet Swap", "Move the target without anyone noticing. TST moves to the new database server atlas-db-new. In "
                "atlas/config/tst.py the old server atlas-db-02 appears in TWO lines (host and URL): both must change, "
                "nothing else."),
    "ATL-120": ("Night Watcher", "You are not alone in the network. traffic.log has today's API requests: <ip> <method> <path> "
                "<status> <time>. A stranger is probing for pages that do not exist (HTTP 404). The path itself can "
                "contain 404 too: a plain grep would count the wrong lines."),
    "ATL-121": ("Money Trail", "Follow the money. The Paymaster asks what Atlas costs in the cloud. costs.csv has one line per "
                "service and environment: service,environment,eur (the first line is a header)."),
    "ATL-122": ("Sweep", "Time to sweep the safe house. The build folder is full of temporary files. Delete every file ending in "
                ".tmp anywhere below ~/build, and nothing else: other files, even ones with tmp in their name, must stay."),
    "ATL-123": ("Lifeboat", "The primary just went dark: PRD points to atlas-db-01, which stopped answering. There are two "
                "replicas: atlas-db-02 and atlas-db-03. We must switch Atlas to the one that is alive."),
    "ATL-124": ("Silent Alarm", "Watchtower triggered a silent alarm. alerts.log has today's Atlas alerts. Most were resolved "
                "automatically. One host is still down and the alert only shows its IP."),
    "ATL-125": ("Dark Server", "Atlas on atlas-prd stopped writing logs. You do not log in to servers to look around: you ask them "
                "one question at a time with ssh, like passing a message through a locked door."),
    "ATL-126": ("Handshake", "Your contact on the integration team wants Power BI to read Atlas data through its REST API. Every "
                "secret handshake starts the same way: you first need a token from the token endpoint: http://atlas-api/token"),
    "ATL-127": ("Inside Man", "The Broker needs the status of project NPI-042, but the channel is guarded. Check through the API "
                "in which stage it is: http://atlas-api/api/projects/NPI-042"),
    "ATL-128": ("Keys to the Kingdom", "Before go-live, Counter-intel wants to know how many Atlas users hold the keys to the "
                "kingdom: the admins. http://atlas-api/api/users returns one JSON user per line. Save it to users.json "
                "first (auditors want the file)."),
    "ATL-129": ("Slow Burn", "Users say Atlas was very slow TODAY (2026-11-12): somebody is draining it from the inside. Control "
                "suspects atlas-db-02. We need the number of ERROR lines in today's log of that server."),
    "ATL-130": ("Safe House", "Your laptop was reinstalled and the old hideout is gone. Build a new safe house the standard way: a "
                "virtual environment in a folder called .venv inside ~/atlas, the requirements installed into it, and the "
                "app started on the port from the README."),
    "ATL-131": ("Ghost Variables", "No files, no paper trail. On the servers there is no .env file: settings come from "
                "environment variables (Azure App Service works the same way). We copied that setup to your machine: the "
                "venv in ~/atlas/.venv is ready, but Atlas refuses to start."),
    "ATL-132": ("Dead Letter", "You are taking over the work of a colleague who vanished mid-operation. Before touching anything, "
                "find out where the repository stands."),
    "ATL-133": ("Shadow Branch", "Team rule: never commit straight to main. Work from the shadows: create the branch "
                "feature/launch-date, add the migration migrations/0042_add_launch_date.py with one line: "
                "add_column('request', 'launch_date')"),
    "ATL-134": ("Loose Thread", "Your SSO branch is almost ready for a pull request. Always review your changes before you push: "
                "something slipped in that should not be there, a loose thread that could unravel your cover."),
    "ATL-135": ("Rogue Process", "Your dev box is crawling. Something is eating the CPU, a rogue process that was not there "
                "yesterday. Find the process that uses the most CPU and stop it."),
    "ATL-136": ("Open Vault", "Counter-intel found the vault doors open: files with the wrong permissions. In ls -l the first "
                "column shows them: three letters for the owner (u), three for the group (g), three for everybody else (o)."),
    "ATL-137": ("Cold Engine", "atlas-api is a service of your own user (a systemd user service) and it is in a failed state: the "
                "engine will not turn over. Never guess: read what the service says about itself, then fix the cause."),
    "ATL-138": ("Escape Plan", "Every operative needs an escape plan. Before the release, back up the configuration. Put the "
                "folder atlas/config into a compressed archive called config-backup.tar.gz inside ~/backups. Then check "
                "what is in it, and finally practice a restore."),
    "ATL-139": ("Occupied", "You start Atlas on port 5050 and it refuses: the port is already taken, as if somebody were squatting "
                "in your safe house. Your venv in ~/atlas/.venv is ready and the environment is configured."),
    "ATL-140": ("Black Hole", "The data disk is almost full: something is swallowing everything. Under ~/data there are four "
                "folders. Find out which one really uses the most space. The folder with the most files is not "
                "necessarily the biggest one."),
    "ATL-141": ("Guest List", "For the access review, Counter-intel asks who is on the guest list: which accounts on this server "
                "can actually log in. Every account is one line of /etc/passwd with 7 fields separated by colons: "
                "name:x:uid:gid:comment:home:shell."),
    "ATL-142": ("Roll Call", "Watchtower wants a roll call: a small script that checks a list of servers. hosts.txt has one "
                "server name per line."),
    "ATL-143": ("Smoke and Mirrors", "The log folder keeps growing, and old logs say too much. Every .log file in ~/logs that is "
                "bigger than 1 KiB must go into one compressed archive, ~/logs-archive.tar.gz, and then be deleted. "
                "Smaller logs stay where they are."),
    "ATL-144": ("Sleight of Hand", "The web server always serves the folder  current , which is a symbolic link to one release in "
                "~/releases. The Courier needs a quiet switch: find out which release it serves now, then switch it to "
                "v1.9.0."),
    "ATL-145": ("Muffled", "nightly.sh runs every night and mails the team its whole output, errors included: far too noisy "
                "for an operative. Read the script, then run it twice: once with ALL its output (normal messages and "
                "errors, in order) in nightly.log, once with only the error messages in nightly.err."),
    "ATL-146": ("Blind Spot", "The request form must save a desired launch date. The column does not exist yet: that is why "
                "/requests/new crashes with KeyError: 'launch_date'. A blind spot in the database."),
    "ATL-147": ("Second Intruder", "You are not the only one trying to get in. Before SSO goes live, Atlas still allows password "
                "login on its server. Overnight, auth.log recorded many failed logins. Who was targeted, did the attacker "
                "get in, and from which machine?"),
    "ATL-148": ("Blackout", "Nobody can test the v1.9 release: the PRE environment went dark. The load balancer configs in "
                "~/lb/sites say for each part of Atlas which server is 'primary' and which is 'fallback'."),
    "ATL-149": ("Cover Story", "Sprint review in one hour, and the Dispatcher needs numbers to keep your cover airtight. "
                "sprint.csv has every ticket of the sprint: ticket,component,points."),
    "ATL-150": ("Endgame", "Final operation. The incidents endpoint http://atlas-api/api/incidents lists all Atlas incidents (it "
                "needs your token). Find the critical incident that is still open, find in its server's log when the first "
                "ERROR happened today, and write the post-mortem file."),
}


def apply(levels):
    """Add the story to every ticket (called once, from tickets.py)."""
    for lv in levels:
        op, first = OPS[lv["ticket"]]
        lv["op"] = op
        lv["brief"] = [first] + list(lv["brief"][1:])
        lv["phase"] = PHASE.get(lv["module"], lv["module"])
        lv["handler"] = HANDLER.get(lv["from"], lv["from"])
        lv["threat"] = THREAT.get(lv["prio"], lv["prio"])
