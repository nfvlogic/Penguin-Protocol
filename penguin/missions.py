"""The story layer: every ticket is an operation. You are an undercover operative inside Atlas.

Only the presentation lives here (codename, handler, phase, threat level and the first paragraph of the
briefing). The answers, files and checks stay in tickets.py. Keep every literal value (ports, hosts, file
names, numbers) of the original text: the answer variants in variants.py replace them by seed.
"""

PHASE = {"Onboarding": "Infiltration", "Code search": "Reconnaissance", "Pipes": "Surveillance",
         "Text tools": "Forensics", "Environments": "Lateral movement", "API": "The back channel",
         "Git & Python": "Deep cover", "Servers": "Inside the walls", "Scripting": "Tradecraft",
         "Feature work": "The final operation", "Vault": "The Vault"}

HANDLER = {"Tech lead": "Control", "Platform team": "Quartermaster", "Product owner": "The Broker",
           "QA team": "Field tester", "Security team": "Counter-intel", "Monitoring": "Watchtower",
           "Code review bot": "The Auditor", "Code review": "The Auditor", "CI pipeline": "Autopilot",
           "Release manager": "The Courier", "Change board": "The Committee", "Integration team": "Contact",
           "Finance": "The Paymaster", "Scrum master": "The Dispatcher", "Pip": "Pip"}

THREAT = {"Normal": "Low", "High": "Elevated", "Critical": "Critical", "Boss": "Boss"}

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

# ticket -> what Pip tells you on the card: (the secret mission in one line, what to do in one line).
# Short on purpose; the full briefing is one command away (task full). Never put an answer here.
PIP = {
    "ATL-101": ("Your badge got you in. Prove your cover holds.", "Find the port Atlas uses on your machine."),
    "ATL-102": ("The test floor moves to a new database soon.", "Find which DB_HOST the TST environment uses."),
    "ATL-103": ("Atlas crashes on start-up. Someone left a trap.", "Find the right DB_NAME in the project's hidden settings."),
    "ATL-104": ("A new feature is your excuse to make folders.", "Build the empty launch_date module."),
    "ATL-105": ("Before you leave a trace, copy the evidence.", "Back up the configs and rename the migration."),
    "ATL-106": ("The Auditor spotted clutter in your work.", "Delete the .pyc files and the __pycache__ folder."),
    "ATL-107": ("Good agents leave no fingerprints.", "Create the .gitignore the briefing describes."),
    "ATL-108": ("Someone changed the gate rules and hid it.", "Find which rules version really runs."),
    "ATL-109": ("A developer left a secret note in the code.", "Find the file with the release blocker."),
    "ATL-110": ("Testers hit an error page. Decoys everywhere.", "Find the real failing endpoint in app.log."),
    "ATL-111": ("Nobody will say what runs on TST.", "Find the deployed version in deploy.log."),
    "ATL-112": ("CI is red and the team panics.", "Count the tests that really failed."),
    "ATL-113": ("One secret key unlocks every session.", "Count the app files that use SECRET_KEY."),
    "ATL-114": ("Two migrations wear the same identity.", "Find the duplicated revision number."),
    "ATL-115": ("Watchtower is flashing red.", "Find the endpoint with the most 500 errors."),
    "ATL-116": ("The Committee wants proof before tonight.", "Read deploy.sh, run it, save its output."),
    "ATL-117": ("A Windows file hides invisible ink.", "Clean the CSV, then count the open tickets."),
    "ATL-118": ("TST and PRD should differ in only 3 places.", "Find the setting someone slipped in."),
    "ATL-119": ("Move the target without anyone noticing.", "Point TST to the new database server."),
    "ATL-120": ("A stranger is probing the network.", "Follow the 404s back to one IP address."),
    "ATL-121": ("Follow the money.", "Add up what Atlas costs in the cloud."),
    "ATL-122": ("Time to sweep the safe house.", "Delete every .tmp file below ~/build, nothing else."),
    "ATL-123": ("The primary database went dark.", "Find the replica that still answers."),
    "ATL-124": ("A silent alarm went off.", "Find the name of the server that is still down."),
    "ATL-125": ("A server stopped writing logs.", "Ask it questions over ssh, one at a time."),
    "ATL-126": ("Every secret handshake starts with a token.", "Get a token from the API."),
    "ATL-127": ("The channel is guarded.", "Ask the API which stage the project is in."),
    "ATL-128": ("Who holds the keys to the kingdom?", "Count the real admins in the user list."),
    "ATL-129": ("Someone drained Atlas from the inside today.", "Count today's ERROR lines on the suspect server."),
    "ATL-130": ("Your old hideout is gone.", "Build a fresh virtual environment and start the app."),
    "ATL-131": ("No files, no paper trail.", "Set the environment variables so Atlas starts."),
    "ATL-132": ("A colleague vanished mid-operation.", "Find out where the repository stands."),
    "ATL-133": ("Never commit straight to main.", "Work on a new branch and add the migration."),
    "ATL-134": ("Something slipped into your branch.", "Review your changes and undo the loose thread."),
    "ATL-135": ("A rogue process is eating your CPU.", "Find it and stop it."),
    "ATL-136": ("The vault doors are open.", "Give the 3 files the right permissions."),
    "ATL-137": ("The engine will not turn over.", "Read what the service says, fix it, restart it."),
    "ATL-138": ("Every operative needs an escape plan.", "Back up the config, check it, practice a restore."),
    "ATL-139": ("Someone is squatting in your port.", "Find who holds it, stop it, start Atlas."),
    "ATL-140": ("Something is swallowing the disk.", "Find the folder that really uses the most space."),
    "ATL-141": ("Counter-intel wants the guest list.", "Find which accounts can really log in."),
    "ATL-142": ("Watchtower wants a roll call.", "Write a script that checks every server."),
    "ATL-143": ("Old logs say too much.", "Archive the big logs, then delete them."),
    "ATL-144": ("The Courier needs a quiet switch.", "Point current to a new release."),
    "ATL-145": ("The nightly script is far too noisy.", "Split its output and its errors into two files."),
    "ATL-146": ("A blind spot in the database.", "Find the next migration number and add the column."),
    "ATL-147": ("You are not the only intruder.", "Find who was targeted and where the attacker came from."),
    "ATL-148": ("The PRE environment went dark.", "Find the dead server and check its fallback."),
    "ATL-149": ("Your cover needs sprint numbers.", "Count the workflow tickets and save them."),
    "ATL-150": ("Final operation.", "Find the open critical incident and write the post-mortem."),
}


# ticket -> what Pip says after a wrong answer: the trap most beginners fall into on that mission. Never an answer.
WRONG = {
    "ATL-101": "Old notes lie. The project README says how the app runs today.",
    "ATL-102": "The legacy folder is the old COMPASS setup. Use the TST file in config.",
    "ATL-103": "The hidden file in your home folder is the OLD one. Look inside the project folder.",
    "ATL-108": "Files in old/ are leftovers. Open the rules file that is actually used.",
    "ATL-109": "Send the file name only, like main.py.",
    "ATL-110": "Lines marked synthetic are monitoring tests, not real errors. Hide them.",
    "ATL-111": "The newest entry is the LAST line of deploy.log, not the first.",
    "ATL-112": "XFAILED is not FAILED. Count whole words only.",
    "ATL-113": "Count files, not lines: one grep option prints only file names.",
    "ATL-114": "Look for a revision number that appears twice in the first column.",
    "ATL-115": "Only status 500 counts. The health check is just busy, not broken.",
    "ATL-117": "The Windows character hides the line ends. Clean the file first, then count.",
    "ATL-118": "Let diff compare the two files: the lines with < and > are the differences.",
    "ATL-120": "A path can contain 404 too. Test the status column only (column 4).",
    "ATL-121": "Use the eur column (3rd). For the first question, only prd lines count.",
    "ATL-123": "Ping both replicas: only one of them answers.",
    "ATL-124": "Most alerts were RESOLVED. Hide those, then look the IP up in /etc/hosts.",
    "ATL-125": "Ask atlas-prd itself through ssh. Your own disks do not count.",
    "ATL-126": "The token endpoint wants your user name in the URL.",
    "ATL-127": "Send your token in the Authorization header, then read the stage.",
    "ATL-128": "admin-request is not admin. Count the exact role, quotes included.",
    "ATL-129": "Only today's log of that one server counts.",
    "ATL-132": "git status and git log answer these. The short hash is in git log --oneline.",
    "ATL-134": "git diff shows the slipped-in change. git diff --staged shows what is staged.",
    "ATL-135": "Sort ps aux by the %CPU column, biggest first. The top line is the culprit.",
    "ATL-137": "journalctl prints the error with the full path of the file.",
    "ATL-138": "List the archive with tar -tzf and count only the lines ending in py.",
    "ATL-139": "ss -tlnp shows which PID listens on the port.",
    "ATL-140": "The folder with the most files is not always the biggest. du -s measures space.",
    "ATL-141": "The shell is the last field. Count lines that END in bash.",
    "ATL-144": "readlink shows where current points right now.",
    "ATL-146": "The next migration number is one more than the highest in the folder.",
    "ATL-147": "Count the Failed lines per account. The Accepted line shows the IP.",
    "ATL-148": "Ping the servers first. The lb configs say which one is primary.",
    "ATL-149": "Match the component column exactly, with the commas around it.",
    "ATL-150": "Critical AND open: both words must be on the same line.",
    "VLT-01": "The real key card is the hidden file, not the expired one.",
    "VLT-02": "Drills say (drill). The real alert does not.",
    "VLT-03": "DENIED_TEST lines are drills. Count DENIED as a whole word only.",
    "VLT-04": "Count in clean.csv: the hidden characters break counting in the original.",
    "VLT-05": "Ping each name on the list. For the total, add up the kb column for one host only.",
    "VLT-06": "Count the exact role with quotes, so similar words do not count.",
    "VLT-07": "git status shows both the branch and the changed file.",
    "VLT-08": "du -s measures space. The most files is not the most space.",
    "VLT-09": "Count lines that END in nologin.",
    "VLT-10": "The .bak files are decoys. Hide them from the search.",
}


def apply(levels):
    """Add the story to every ticket (called once, from tickets.py)."""
    from .vaults import OPS as VOPS, PIP as VPIP
    OPS.update(VOPS)
    PIP.update(VPIP)
    for lv in levels:
        op, first = OPS[lv["ticket"]]
        lv["op"] = op
        lv["pip"] = list(PIP[lv["ticket"]])
        lv["wrong"] = WRONG.get(lv["ticket"], "")
        lv["brief"] = [first] + list(lv["brief"][1:])
        lv["phase"] = PHASE.get(lv["module"], lv["module"])
        lv["handler"] = HANDLER.get(lv["from"], lv["from"])
        lv["threat"] = THREAT.get(lv["prio"], lv["prio"])
