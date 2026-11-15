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
# Short on purpose: the briefing card under it has everything. Never put an answer here.
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


# What Pip tells you to do on the card: a few plain sentences (where to look, what must exist or be handed in at the end).
# Never a command, never an answer.
TODO = {
    "ATL-101": "Start with the welcome file in your home folder: it points to the project documentation. In it, find the port the app uses when you run it locally, and submit that number.",
    "ATL-102": "Open the project and look at the config of each environment. Find the DB_HOST the TST environment uses today (not the old COMPASS one) and submit it.",
    "ATL-103": "Go into the project folder and look at ALL its files, including the hidden ones. Find the settings file that holds the right DB_NAME and submit only that name.",
    "ATL-104": "Go to ~/atlas/app/features and create the empty launch_date module there: the folders and files the tree on the card shows, with the one line of text in README.md. The mission closes by itself when it all exists.",
    "ATL-105": "Put a copy of the 3 config files into the backup folder, and give the draft migration its proper new name (same folder, same content). The mission closes by itself when both are done.",
    "ATL-106": "Remove the compiled .pyc files and the __pycache__ folder from the project, and nothing else. The mission closes by itself when they are gone.",
    "ATL-107": "Create a .gitignore file in the project with exactly the 3 lines from the briefing, in that order. Then add the new line at the END of CHANGELOG.md without erasing what is there.",
    "ATL-108": "Several files in the project have 'gate' in their name, but only one is the rules file really in use. Find it, read its rules version and submit it.",
    "ATL-109": "A developer left a TODO(release-blocker) note somewhere in the application code (not in the docs). Find the file that contains it and submit the file name only.",
    "ATL-110": "Read app.log and find the request that really fails with HTTP 500. Ignore the lines marked as monitoring tests, and submit the path of the endpoint.",
    "ATL-111": "deploy.log lists every deployment, the newest at the bottom. Find the version that is deployed on TST now and submit it.",
    "ATL-112": "Look at test_report.txt and count only the tests that really FAILED. Tests marked XFAILED are known issues and do not count. Submit the number.",
    "ATL-113": "Count how many Python files in the application code use SECRET_KEY. Files that are not Python code (templates, docs, settings) do not count. Submit the number.",
    "ATL-114": "Look at migrations_list.txt and find the revision number that two migrations share. Submit that number.",
    "ATL-115": "Read access.log and find the endpoint that answers with HTTP 500 most often. The health check is busy, but that is not what you are after. Submit its path.",
    "ATL-116": "Read deploy.sh first so you know what it does, then run it and save everything it prints in deploy_check.log. The mission closes by itself.",
    "ATL-117": "Make a clean copy of the export called clean.csv without the hidden Windows character at the end of each line. Then count the tickets whose status is open and submit the number.",
    "ATL-118": "Compare the TST and PRD config files. Besides host, name and DEBUG, one more setting differs. Find its name and the value PRD uses for it.",
    "ATL-119": "In the TST config the old database server appears in two lines. Make both point to the new server, change nothing else, and keep the original as tst.py.bak. Do not touch the PRD config.",
    "ATL-120": "traffic.log has the requests of today. Work out how many different status codes there are, how many requests got 404, which IP made most of them, and how much time that IP used in total.",
    "ATL-121": "costs.csv has the monthly cost per service and environment. Add up the cost of the prd environment, then find the most expensive service over all environments.",
    "ATL-122": "Delete every file that ends in .tmp anywhere below the build folder. All other files must stay, even ones with tmp in their name. The mission closes by itself.",
    "ATL-123": "PRD points to a database that stopped answering. Check which of the two replicas answers, look up its IP address in /etc/hosts and submit that address.",
    "ATL-124": "alerts.log has today's alerts and most are resolved. Find the one that is not, turn its IP into a server name using /etc/hosts, and submit the name.",
    "ATL-125": "You cannot log in to atlas-prd, but you can ask it single questions. Find which disk is full, save that proof in prd_disk.txt, then find the biggest file in the Atlas log folder.",
    "ATL-126": "Ask the token endpoint of the API for an access token. Read what the server answers: it tells you what it needs from you. Submit the token.",
    "ATL-127": "Ask the API about project NPI-042. The endpoint is protected: read what the server asks for, give it, then read the stage and submit it.",
    "ATL-128": "Save the user list from the API as users.json, then count the users that really are admins. A pending admin request is not an admin yet. Submit the number.",
    "ATL-129": "Find today's log of the suspect server in the incident folder (one folder per day) and count the ERROR lines in it. Logs of other days do not count.",
    "ATL-130": "Create a virtual environment called .venv in the project, install the requirements into it, and start the app on the port the README names. The mission closes by itself.",
    "ATL-131": "Atlas does not start because its environment variables are missing. Find out which ones, set them with the values for local development, and start the app. The mission closes by itself.",
    "ATL-132": "Inside the project, find out the state of the repository: which branch you are on, which file has uncommitted changes, and the short hash of one commit.",
    "ATL-133": "Do not work on main. Create the new branch from the briefing, add the migration file with its one line, and commit it with the message the briefing asks for. The mission closes by itself.",
    "ATL-134": "Review what changed in the project before the pull request. One config file got an accidental change: find it, undo it, and find out which package is staged for requirements.txt.",
    "ATL-135": "Find the process that uses the most CPU and submit its PID. Then stop it, and check that it is really gone.",
    "ATL-136": "Three files have the wrong permissions: .env, scripts/deploy.sh and config/prd.py. Give each the permissions the briefing describes. The mission closes by itself.",
    "ATL-137": "The atlas-api service is in a failed state. Find out which file it cannot read and submit its full path, then fix the cause and start the service again.",
    "ATL-138": "Put the config folder into a compressed archive in the backups folder, find out how many .py files it holds, and practice restoring one single file into the restore folder.",
    "ATL-139": "The port Atlas needs is taken. Find which process holds it and submit its PID, then stop that process and start Atlas on the same port.",
    "ATL-140": "Under the data folder there are four folders. Find which one uses the most disk space and how many KB it uses. The one with the most files is not necessarily the biggest.",
    "ATL-141": "Look at /etc/passwd: the last field of every line is the login shell. Count the accounts with a real shell like bash, and find the user id of the mysql account.",
    "ATL-142": "Write a script check_hosts.sh in your home folder (next to hosts.txt) that prints one line per name in hosts.txt: the name and up or down. Make it runnable, run it, and save its output in report.txt.",
    "ATL-143": "Put every log in the logs folder that is bigger than 1 KiB into one compressed archive, then delete those logs. Smaller logs stay. The mission closes by itself.",
    "ATL-144": "The folder current is a link to one release. Find out which release it points to now, then make it point to the release the briefing names.",
    "ATL-145": "Read the nightly script, then run it twice: once saving everything it prints (messages and errors, in order) in nightly.log, once saving only the errors in nightly.err.",
    "ATL-146": "Find which template renders the request form and the next free migration number. Then create the migration that adds the launch_date column, as described in the briefing.",
    "ATL-147": "auth.log shows failed logins. Find which account was targeted most, the IP it later logged in from, and which machine in /etc/hosts has that IP.",
    "ATL-148": "Find which Atlas server is down, which load balancer config uses it as primary, and whether that site's fallback answers. Submit the fallback's IP address.",
    "ATL-149": "sprint.csv lists the tickets of the sprint. Count the tickets of the workflow component, find the biggest story-point value, and save only the workflow lines in workflow.csv.",
    "ATL-150": "Ask the incidents endpoint of the API for the incident that is critical and still open. Find the first ERROR of today in its server's log, and write postmortem.txt as the briefing says.",
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


# The story line of each briefing: one or two short sentences. The facts live in the paragraphs that follow (TASK below).
STORY = {
    "ATL-101": "Control wants proof that your cover holds: run Atlas on your own machine.",
    "ATL-102": "TST is about to move to a new database server. Where does it point today?",
    "ATL-103": "Atlas dies on start-up with: Unknown database 'compass_dev'. An old environment file is the trap.",
    "ATL-104": "Your cover story: build the Launch date feature. Start with the empty module.",
    "ATL-105": "Keep a copy of the evidence before you leave any trace.",
    "ATL-106": "Your pull request contains compiled files. Wipe the scene.",
    "ATL-107": "Good agents leave no fingerprints. Make sure it never happens again.",
    "ATL-108": "Gate approvals do not behave as documented. Which rules are really running?",
    "ATL-109": "Release v1.9 goes out on Friday. A developer left a TODO(release-blocker) somewhere in the code.",
    "ATL-110": "Testers get an error page when they create a new request on TST.",
    "ATL-111": "Which Atlas version is on TST right now? deploy.log has 240 lines, the newest at the bottom; the first line is the previous release.",
    "ATL-112": "The CI pipeline is red. How many tests really failed?",
    "ATL-113": "Counter-intel wants to rotate the SECRET_KEY. Who touches it?",
    "ATL-114": "Alembic refuses to upgrade: two migrations share one revision number.",
    "ATL-115": "Watchtower is flashing red. Which endpoint is failing?",
    "ATL-116": "The Committee wants a pre-deploy check before tonight's deployment of v1.9.",
    "ATL-117": "Invisible ink: a Windows export hides a character in every line.",
    "ATL-118": "A bug only happens on PRD. Did somebody slip in a change?",
    "ATL-119": "Move the target without anyone noticing: TST moves to the new database server atlas-db-new.",
    "ATL-120": "You are not alone in the network: a stranger is probing for missing pages.",
    "ATL-121": "Follow the money: what does Atlas cost in the cloud?",
    "ATL-122": "Time to sweep the safe house.",
    "ATL-123": "The primary database just went dark. Switch Atlas to a replica that is alive.",
    "ATL-124": "Watchtower triggered a silent alarm.",
    "ATL-125": "Atlas on atlas-prd stopped writing logs.",
    "ATL-126": "Power BI wants to read Atlas data through its REST API. Every handshake starts with a token.",
    "ATL-127": "The Broker needs the status of project NPI-042, but the channel is guarded.",
    "ATL-128": "Before go-live: how many users hold the keys to the kingdom?",
    "ATL-129": "Atlas was very slow today. Control suspects atlas-db-02.",
    "ATL-130": "Your laptop was reinstalled. Build a new safe house.",
    "ATL-131": "No files, no paper trail: on the servers, settings come from environment variables.",
    "ATL-132": "A colleague vanished mid-operation. Where does the repository stand?",
    "ATL-133": "Team rule: never commit straight to main. Work from the shadows.",
    "ATL-134": "Your SSO branch is almost ready. Review it before you push.",
    "ATL-135": "Your dev box is crawling: a rogue process is eating the CPU.",
    "ATL-136": "Counter-intel found the vault doors open: files with the wrong permissions.",
    "ATL-137": "The atlas-api service will not turn over.",
    "ATL-138": "Every operative needs an escape plan: back up the configuration.",
    "ATL-139": "Somebody is squatting in your safe house: the port is already taken.",
    "ATL-140": "The data disk is almost full: something is swallowing everything.",
    "ATL-141": "Access review: who on this server can actually log in? Every account is one line of /etc/passwd: name:x:uid:gid:comment:home:shell.",
    "ATL-142": "Watchtower wants a roll call of a list of servers.",
    "ATL-143": "Old logs say too much. Make them disappear into an archive.",
    "ATL-144": "The Courier needs a quiet switch of the live release.",
    "ATL-145": "nightly.sh mails the team far too much noise.",
    "ATL-146": "The request form must save a desired launch date, but /requests/new crashes with KeyError: 'launch_date'.",
    "ATL-147": "You are not the only one trying to get in: many failed logins overnight.",
    "ATL-148": "The PRE environment went dark, and nobody can test v1.9. The configs in ~/lb/sites say for each part of Atlas which server is 'primary' and which is 'fallback'.",
    "ATL-149": "Sprint review in one hour. Keep your cover airtight.",
    "ATL-150": "Final operation: write the post-mortem.",
}


# What has to be done, short and without telling HOW (the commands are on the card, `hint` helps when stuck).
# Replaces the paragraphs after the story. Keep literal values (hosts, ports, file names): variants.py swaps them by seed.
TASK = {
    "ATL-101": ["Start with welcome.txt in your home folder: it points to the project docs. Find the port the app uses locally."],
    "ATL-102": ["Project: ~/atlas. Each environment has its own config file. There is also an old COMPASS config folder: the "
                "README says whether it is still valid."],
    "ATL-103": ["Project: ~/atlas. Some of its files are hidden (the one in your home folder is the OLD one). One hidden file "
                "points to the one that holds the settings: in it find DB_NAME=... and submit only the value after the = sign."],
    "ATL-104": ["~/atlas/app/features already exists and is empty. Build the launch_date module inside it, exactly as "
                "the tree below shows. Do not create atlas, app or features again."],
    "ATL-108": ["Project: ~/atlas. Several files have 'gate' in their name: code, an old copy, a test and a template. Only the "
                "one in app/workflow (not in old/) is active."],
    "ATL-105": ["When you are done: ~/backup holds a copy of each of the 3 files in ~/atlas/config (the originals stay), "
                "and ~/atlas/migrations/draft.py has the new name 0040_add_trademark_bu.py (same folder, same content)."],
    "ATL-106": ["Remove from ~/atlas every compiled file ending in .pyc (only those directly in that folder) and the whole "
                "folder atlas/__pycache__. Nothing else may disappear."],
    "ATL-107": ["Create atlas/.gitignore with exactly these 3 lines, in this order: __pycache__/  then  *.pyc  then  .env",
                "Add this as the new LAST line of atlas/CHANGELOG.md; the lines already there must stay: - Added launch date field (ATL-104)"],
    "ATL-110": ["app.log has 160 lines from this morning. Find the real endpoint that fails with HTTP 500. Fake crashes sent by "
                "monitoring are marked as tests and do not count."],
    "ATL-112": ["test_report.txt lists 40 tests. XFAILED means expected to fail (a known issue) and does not count. Count only the tests that really FAILED."],
    "ATL-113": ["Count the .py files in atlas/app that mention SECRET_KEY. Templates, docs and settings files do not count."],
    "ATL-114": ["migrations_list.txt has one migration per line: <number> <name>. Find the revision number that is used twice."],
    "ATL-115": ["access.log has today's API traffic. Line format: <ip> <method> <path> <status> <time>. Find the endpoint with the most HTTP 500 answers. "
                "The busiest endpoint overall is the health check: that is not what we are after."],
    "ATL-116": ["Run the pre-deploy script deploy.sh and keep its output in a file called deploy_check.log (in your home folder, next to deploy.sh). "
                "Check what the script does before you run it."],
    "ATL-117": ["tickets_export.csv comes from a Windows laptop: an invisible extra character, a carriage return (\\r), ends every line, which is why "
                "searching for open gives 0. Make clean.csv in your home folder: the same lines without that character. Then give the number "
                "of tickets whose status (last column) is open."],
    "ATL-118": ["Compare atlas/config/tst.py and atlas/config/prd.py. They should differ in only 3 settings: the database host, the database name and DEBUG. Find out "
                "which other setting differs and what value PRD has for it."],
    "ATL-119": ["In atlas/config/tst.py the old server atlas-db-02 appears in TWO lines (host and URL). Both must point to the "
                "new server atlas-db-new, and nothing else may change. Keep the original as tst.py.bak in the same folder. "
                "Do not touch prd.py."],
    "ATL-120": ["traffic.log has today's API requests: <ip> <method> <path> <status> <time>. A stranger is probing for pages "
                "that do not exist (status 404). Careful: some paths contain 404 too; only the status counts."],
    "ATL-121": ["costs.csv has one line per service and environment: service,environment,eur (the first line is a header)."],
    "ATL-122": ["Delete every file ending in .tmp anywhere below ~/build. All other files must stay, even ones with tmp in "
                "their name."],
    "ATL-123": ["PRD points to atlas-db-01, which stopped answering. Two replicas exist: atlas-db-02 and atlas-db-03. Server "
                "names and their IPs are in /etc/hosts. Find out which replica answers and submit its IP address."],
    "ATL-124": ["alerts.log has today's alerts; most are resolved. One host is still down and its alert only shows an IP. "
                "Submit the name of that server."],
    "ATL-125": ["You do not log in to atlas-prd; as the user analyst you can only send it one command at a time. "
                "On Linux, logs live in /var."],
    "ATL-126": ["Get an API access token from the token endpoint: http://atlas-api/token. The server tells you what it needs: "
                "read its replies."],
    "ATL-127": ["The projects endpoint is protected. Read what the server asks for and find the stage of project NPI-042."],
    "ATL-128": ["Save the list from http://atlas-api/api/users (one JSON user per line) as users.json in your home folder, then count the real "
                "admins. A pending 'admin-request' is not an admin yet."],
    "ATL-129": ["Today is 2026-11-12. Count the ERROR lines in today's log of atlas-db-02. Logs are in ~/incident, one folder "
                "per day; other days do not count."],
    "ATL-130": ["Build the dev environment: a virtual environment in ~/atlas/.venv, the requirements (listed in "
                "~/atlas/requirements.txt) installed into it, and Atlas running on the port from the README."],
    "ATL-131": ["Atlas refuses to start because its environment variables are not set. The venv in ~/atlas/.venv is ready. "
                "Set what is missing (the values for local development are in ~/atlas/.env.example) and get Atlas running."],
    "ATL-132": ["Find out the state of the repository in ~/atlas and answer the three steps."],
    "ATL-133": ["Never commit straight to main. In ~/atlas create a branch called feature/launch-date and add the file "
                "migrations/0042_add_launch_date.py containing one line: add_column('request', 'launch_date')",
                "Commit it with a message that starts with the ticket number ATL-146. Made a mistake on main? Type reset to "
                "start this ticket again."],
    "ATL-134": ["Review the pending changes in ~/atlas before the pull request. An accidental change slipped into a config "
                "file, and a package is waiting to be added to requirements.txt."],
    "ATL-135": ["Find the process that uses the most CPU and make it stop for good."],
    "ATL-136": ["Fix the permissions of three files in ~/atlas: .env: the owner can read and write, nobody else can do "
                "anything. scripts/deploy.sh: the owner can do everything, the group can read and run it, others nothing. "
                "config/prd.py: everybody can read it, only the owner can write."],
    "ATL-137": ["atlas-api is a service of your own user and it is in a failed state. Find out why, fix the cause and get it "
                "running (active) again."],
    "ATL-138": ["Back up the folder atlas/config into a compressed archive ~/backups/config-backup.tar.gz. Then answer how "
                "many .py files it holds, and restore only atlas/config/tst.py into ~/restore (the folder exists)."],
    "ATL-139": ["Atlas must run on port 5050 (the front end expects it) but the port is taken. Find who holds it, remove the "
                "blocker and start Atlas on that port. The venv in ~/atlas/.venv is ready and configured."],
    "ATL-140": ["Under ~/data there are four folders. Find which one really uses the most disk space (not necessarily the one "
                "with most files) and how much it uses, in KB."],
    "ATL-142": ["Write a script check_hosts.sh that prints, for every name in hosts.txt, NAME up or NAME down (one line per "
                "server, same order). Up means the server answers a ping. Run it and save its output in report.txt, also in your home folder."],
    "ATL-143": ["Every .log file in ~/logs bigger than 1 KiB must end up in one compressed archive, ~/logs-archive.tar.gz, and "
                "no longer be in ~/logs. Smaller logs stay. The archive holds only the big logs."],
    "ATL-144": ["~/current is a symbolic link to one release in ~/releases. Find out which release it serves now, "
                "then make it serve v1.9.0."],
    "ATL-145": ["Read nightly.sh, then run it twice. First time: everything it prints, normal messages and errors, in order, "
                "goes into nightly.log. Second time: only the error messages go into nightly.err. Both files go in your home folder, next to nightly.sh."],
    "ATL-146": ["The column does not exist yet. The form templates are somewhere in ~/atlas/app/templates and the migrations are in "
                "~/atlas/migrations. Find the template of the form and the next free migration number, then create the new "
                "migration file in ~/atlas/migrations: its name is <NUMBER>_add_launch_date.py and it holds exactly one line: "
                "add_column('request', 'launch_date')"],
    "ATL-150": ["The incidents endpoint http://atlas-api/api/incidents lists all Atlas incidents (it needs your token). Find the "
                "critical incident that is still open, then find in its server's log when the first ERROR happened today. Server "
                "logs are in ~/incident/<year>/<month>/<day>/<server>.log and today is 2026-11-12. Write postmortem.txt in your "
                "home folder, as the steps below say."],
    "ATL-149": ["sprint.csv has every ticket of the sprint: ticket,component,points. Answer the questions and create "
                "workflow.csv (in your home folder, next to sprint.csv) with only the lines of the workflow component ('workflow-ui' is a different component)."],
}


# ticket -> what your home folder must look like when you are done: (path from ~, note). The card draws it as a tree
# from ~, marks folders that already exist, so nobody has to guess WHERE to create things. Never put an answer here.
RESULT = {
    "ATL-104": [("atlas/app/features/launch_date/", "NEW folder"),
                ("atlas/app/features/launch_date/__init__.py", "NEW empty file"),
                ("atlas/app/features/launch_date/routes.py", "NEW empty file"),
                ("atlas/app/features/launch_date/templates/", "NEW empty folder"),
                ("atlas/app/features/launch_date/README.md", "NEW file, text: Launch date field")],
    "ATL-105": [("atlas/config/", "keep the 3 files here"),
                ("atlas/migrations/draft.py", "GONE: renamed (mv) to the name below"),
                ("atlas/migrations/0040_add_trademark_bu.py", "NEW name of draft.py, same content"),
                ("backup/dev.py", "NEW copy of atlas/config/dev.py"),
                ("backup/prd.py", "NEW copy of atlas/config/prd.py"),
                ("backup/tst.py", "NEW copy of atlas/config/tst.py")],
    "VLT-01": [("loot/", "NEW folder"), ("loot/plans/", "NEW folder"),
               ("loot/plans/floor-2.txt", "NEW: a copy of plans.txt (find it in ~/vault), renamed")],
    "ATL-106": [("atlas/*.pyc", "DELETE every .pyc file directly in atlas"),
                ("atlas/__pycache__/", "DELETE this whole folder")],
    "ATL-107": [("atlas/.gitignore", "NEW file, 3 lines: __pycache__/  *.pyc  .env"),
                ("atlas/CHANGELOG.md", "CHANGED: one new line at the end")],
    "VLT-02": [("signals/", "every *.bak file inside, in any subfolder: DELETE")],
    "ATL-116": [("deploy.sh", "CHANGED: made executable, then run"),
                ("deploy_check.log", "NEW: what deploy.sh printed")],
    "ATL-117": [("tickets_export.csv", "stays as it is"),
                ("clean.csv", "NEW: the same lines without the \\r")],
    "VLT-04": [("roster.csv", "stays as it is"),
               ("clean.csv", "NEW: roster.csv without the \\r, lisbon changed to oslo")],
    "ATL-119": [("atlas/config/prd.py", "do not touch"),
                ("atlas/config/tst.py", "CHANGED: atlas-db-02 becomes atlas-db-new (2 lines)"),
                ("atlas/config/tst.py.bak", "NEW: copy of tst.py BEFORE the change")],
    "ATL-122": [("build/", "every *.tmp file inside, in any subfolder: DELETE")],
    "ATL-125": [("prd_disk.txt", "NEW: the df -h output of atlas-prd")],
    "ATL-128": [("users.json", "NEW: the user list from the API")],
    "ATL-130": [("atlas/.venv/", "NEW virtual environment")],
    "VLT-06": [("agents.json", "NEW: the user list from the API")],
    "ATL-133": [("atlas/migrations/0042_add_launch_date.py", "NEW, on branch feature/launch-date, committed")],
    "ATL-136": [("atlas/.env", "CHANGED permissions: 600"),
                ("atlas/config/prd.py", "CHANGED permissions: 644"),
                ("atlas/scripts/deploy.sh", "CHANGED permissions: 750")],
    "ATL-138": [("backups/config-backup.tar.gz", "NEW archive of atlas/config"),
                ("restore/atlas/config/tst.py", "NEW: only this file, taken out of the archive")],
    "ATL-142": [("hosts.txt", "the servers to check"),
                ("check_hosts.sh", "NEW script, executable"),
                ("report.txt", "NEW: what check_hosts.sh printed")],
    "ATL-143": [("logs/", "the .log files bigger than 1 KiB: DELETE (small ones stay)"),
                ("logs-archive.tar.gz", "NEW archive with only the big logs")],
    "ATL-144": [("current", "CHANGED: link pointing to releases/v1.9.0")],
    "ATL-145": [("nightly.log", "NEW: everything, messages and errors, in order"),
                ("nightly.err", "NEW: only the error messages")],
    "VLT-08": [("out/cargo.tar.gz", "NEW archive of the biggest folder in ~/cargo")],
    "VLT-09": [("front", "CHANGED: link pointing to releases/v2.0.0"),
               ("sweep.err", "NEW: only the error of sweep.sh")],
    "ATL-146": [("atlas/migrations/<NUMBER>_add_launch_date.py", "NEW, one line")],
    "ATL-149": [("workflow.csv", "NEW: only the workflow lines of sprint.csv")],
    "ATL-150": [("postmortem.txt", "NEW, exactly 3 lines")],
    "VLT-10": [("exit.tar.gz", "NEW archive of the whole ~/core folder"),
               ("report.txt", "NEW, exactly 2 lines")],
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
        if lv["ticket"] in TODO:
            lv["pip"][1] = TODO[lv["ticket"]]
        lv["wrong"] = WRONG.get(lv["ticket"], "")
        lv["result"] = list(RESULT.get(lv["ticket"], []))
        first = STORY.get(lv["ticket"], first)
        lv["brief"] = [first] + list(TASK.get(lv["ticket"]) or lv["brief"][1:])
        lv["phase"] = PHASE.get(lv["module"], lv["module"])
        lv["handler"] = HANDLER.get(lv["from"], lv["from"])
        lv["threat"] = THREAT.get(lv["prio"], lv["prio"])
