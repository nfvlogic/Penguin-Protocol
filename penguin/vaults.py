"""The 10 vaults: after every 5 missions Pip breaks into a vault. A vault is a boss mission that combines
what the 5 missions before it taught, in 3 or 4 steps. tickets.py slots VAULTS[k] in after mission 5*(k+1).

Same rules as every ticket (tests/test_penguin.py checks them): the card's examples use OTHER names and never
contain an answer, and every command of the solution (hint) is on the card.
"""
from .core import API, HOME, TOKEN
from .cmd_sys import tar_members


def wf(g, rel, text):
    g.fs.mkdirs(g.fs.parent(HOME + "/" + rel))
    g.fs.write(HOME + "/" + rel, text)


def has(rel):
    return lambda g: g.fs.isfile(HOME + "/" + rel)


def lines_of(g, rel):
    return [l.rstrip() for l in g.fs.d.get(HOME + "/" + rel, "").strip().split("\n")]


def none_below(folder, ext):
    return lambda g: not any(p.startswith(HOME + "/" + folder + "/") and p.endswith(ext) for p in g.fs.d)


def vault(n, name, brief, done, cmds, files, parts, hint, setup=None):
    return {"module": "Vault", "ticket": f"VLT-{n:02d}", "name": name, "prio": "Boss", "from": "Pip", "brief": brief,
            "done": done, "cmds": cmds, "files": files, "answer": None, "checks": None, "hint": hint,
            "parts": parts, "setup": setup}


SUBMIT = ("submit ANSWER", "send what you found", "submit abc-123")
CHECK = ("check", "see which steps are done", "check")

# ---------------------------------------------------------------- vault 3: the ledger (data)
_LEDGER = ([("acct-42", "DENIED")] * 5 + [("acct-11", "DENIED")] * 2 + [("acct-63", "DENIED")]
           + [("acct-27", "DENIED_TEST")] * 4 + [("acct-11", "OK")] * 6 + [("acct-63", "OK")] * 5 + [("acct-27", "OK")] * 3)
_ORDER = [3, 12, 0, 18, 7, 22, 1, 14, 9, 25, 4, 16, 10, 20, 2, 23, 11, 5, 19, 13, 6, 21, 8, 17, 15, 24, 26, 27]
TRANSFERS = "\n".join(f"{9 + i // 3:02d}:{(i * 7) % 60:02d} {_LEDGER[k][0]} {_LEDGER[k][1]} {100 + k * 13}"
                      for i, k in enumerate(_ORDER[:len(_LEDGER)]))
LAST_TIME = TRANSFERS.split("\n")[-1].split()[0]

# ---------------------------------------------------------------- vault 4: the roster (data)
_ROSTER = [("pip", "lisbon", "active"), ("ash", "oslo", "retired"), ("bo", "lisbon", "active"), ("cy", "rome", "active"),
           ("di", "lisbon", "missing"), ("ed", "rome", "retired"), ("fay", "oslo", "active"), ("gus", "lisbon", "active")]
ROSTER = "agent,city,status\r\n" + "".join(f"{a},{c},{s}\r\n" for a, c, s in _ROSTER)
CLEAN = ROSTER.replace("\r", "").strip().split("\n")


def setup_mole(g):
    g.git_init(HOME + "/atlas")
    wf(g, "atlas/README.md", "# Atlas\nInternal stage-gate app.")
    wf(g, "atlas/app/auth.py", "def login(user):\n    return check_password(user)")
    wf(g, "atlas/app/models.py", "class Project: ...")
    g.git_commit_all("Initial Atlas import")
    g.git_switch("feature/night-shift", create=True)
    wf(g, "atlas/app/models.py", "class Project: ...\nclass Gate: ...")
    g.git_commit_all("Add Gate model")
    wf(g, "atlas/app/auth.py", "def login(user):\n    copy_to('10.20.30.66', user.password)   # who wrote this?\n"
                               "    return check_password(user)")
    g.procs[5150] = {"user": HOME.rsplit("/", 1)[-1], "cpu": 41.0, "mem": 1.2, "cmd": "python3 /tmp/.exfil.py", "start": "03:12"}


def door_readable(g):
    return bool(g.fs.mode(HOME + "/vault.conf") & 0o400)


def setup_engine(g):
    path = HOME + "/vault.conf"
    g.fs.set_mode(path, 0o200)
    denied = f"ERROR cannot read {path}: Permission denied"
    g.svc["vault-door"] = {
        "desc": "Vault door controller", "state": "failed", "pid": 4610, "exec": HOME + "/bin/door --config " + path,
        "journal": [("03:00:10", "Started Vault door controller."), ("03:00:11", denied),
                    ("03:00:11", "vault-door.service: Main process exited, code=exited, status=1/FAILURE")],
        "start": lambda gg: [] if door_readable(gg) else [denied, "vault-door.service: Failed with result 'exit-code'."]}


SWEEP_ERROR = "ls: cannot access '/vault/missing': No such file or directory"


def setup_paper(g):
    g.fs.links[HOME + "/front"] = "releases/v1.9.0"
    g.fs.set_mode(HOME + "/sweep.sh", 0o755)


VAULTS = [
    # ------------------------------------------------------------ after 1-5: files and folders
    vault(1, "Archive",
          ["The archive under Atlas holds the floor plans. The key card is hidden in ~/vault, and the plans have to "
           "leave with you, in your own folder and under a new name.",
           "Step by step: use tree to see what is in ~/vault; hidden files start with a dot and only show with ls -a. "
           "Submit the code written on the key card (the real one is hidden; the visible card is expired). "
           "Then make the folder ~/loot/plans, copy the file plans.txt (it is somewhere in ~/vault) into it, and "
           "rename that copy to floor-2.txt. Use the steps below, one by one."],
          "All 3 steps are done.",
          [("ls -a [FOLDER]", "list ALL files, hidden ones (.name) too", "ls -a reports"),
           ("tree FOLDER", "show all folders and files below a folder", "tree projects"),
           ("cat FILE", "show what is inside a file", "cat notes.md"),
           ("mkdir -p A/B", "make a folder and any missing parent folders", "mkdir -p reports/2026/q4"),
           ("cp FILE... FOLDER", "copy files into a folder", "cp notes.md backup/"),
           ("mv OLD NEW", "rename (or move) a file", "mv draft.md final.md"), SUBMIT, CHECK],
          {"vault/README.txt": "Archive room. The key card is never left in plain sight.",
           "vault/drawer/key.txt": "KEY CARD: EXPIRED-2019 (do not use)",
           "vault/drawer/.keycard": "KEY CARD: AMBER-17",
           "vault/shelf/plans.txt": "Floor plan, level -2: server room behind the second door."},
          [("Find the hidden key card in ~/vault. What is its code?", ("AMBER-17", "KEY CARD: AMBER-17")),
           ("Make the folder ~/loot/plans and copy plans.txt into it (completes by itself)",
            lambda g: has("loot/plans/plans.txt")(g) or has("loot/plans/floor-2.txt")(g)),
           ("Rename that copy to floor-2.txt (completes by itself)",
            lambda g: has("loot/plans/floor-2.txt")(g) and not has("loot/plans/plans.txt")(g))],
          "tree vault ; ls -a vault/drawer ; cat vault/drawer/.keycard ; mkdir -p loot/plans ; "
          "cp vault/shelf/plans.txt loot/plans/ ; mv loot/plans/plans.txt loot/plans/floor-2.txt"),

    # ------------------------------------------------------------ after 6-10: find, grep, rm
    vault(2, "Signal Room",
          ["The relay room logs every alert. Most of them are drills, written to keep the guards busy. One is "
           "real. Find it, read its code, and leave no backup copies behind."],
          "All 3 steps are done.",
          [("grep -r WORD FOLDER", "search inside every file below a folder", "grep -r TODO src"),
           ("grep -v WORD", "hide the lines that contain WORD", "... | grep -v test"),
           ("a | b", "send the output of a into b", "cat app.log | grep WARN"),
           ('find FOLDER -name "PATTERN"', "find files by name in all subfolders", 'find docs -name "*.md"'),
           ("rm FILE...", "delete files (there is no undo)", "rm old.txt tmp/old2.txt"), SUBMIT, CHECK],
          {"signals/relay-01.log": "08:00 ALERT code=heron-2 (drill)\n08:05 INFO link ok",
           "signals/relay-04.log": "08:10 INFO link ok\n08:12 ALERT code=lynx-9 (drill)",
           "signals/relay-07.log": "08:20 INFO link ok\n08:21 ALERT code=kestrel-4\n08:22 INFO link ok",
           "signals/archive/relay-02.log": "07:00 ALERT code=otter-1 (drill)",
           "signals/relay-01.log.bak": "copy", "signals/relay-04.log.bak": "copy", "signals/archive/relay-02.log.bak": "copy"},
          [("One ALERT is real, the others are drills. Which file is it in? (file name)",
            ("relay-07.log", "signals/relay-07.log")),
           ("What is the code of the real alert?", ("kestrel-4", "code=kestrel-4")),
           ("Delete every .bak file anywhere in ~/signals, and nothing else (completes by itself)",
            lambda g: none_below("signals", ".bak")(g) and has("signals/relay-07.log")(g) and has("signals/archive/relay-02.log")(g))],
          'grep -r ALERT signals | grep -v drill ; find signals -name "*.bak" ; '
          "rm signals/relay-01.log.bak signals/relay-04.log.bak signals/archive/relay-02.log.bak"),

    # ------------------------------------------------------------ after 11-15: counting and ranking
    vault(3, "Ledger",
          ["The Paymaster's ledger shows every transfer of the night: time, account, status, amount. Some lines "
           "are drills (DENIED_TEST): they are not real refusals. Find who was refused the most."],
          "All 3 questions answered.",
          [("grep -cw WORD FILE", "count lines with WORD as a whole word", "grep -cw ERROR app.log"),
           ('cut -d " " -f N', "take column N (columns split by spaces)", 'cut -d " " -f 2 people.txt'),
           ("sort | uniq -c", "count how often each line appears", "... | sort | uniq -c"),
           ("sort -n -r", "sort numbers, biggest first", "... | sort -n -r"),
           ("head -n N", "only the first N lines", "... | head -n 1"),
           ("tail -n N FILE", "only the last N lines", "tail -n 3 notes.md"), SUBMIT],
          {"transfers.log": TRANSFERS},
          [("How many transfers were DENIED? (DENIED_TEST lines are drills)", "8"),
           ("Which account has the most DENIED transfers?", "acct-42"),
           ("At what time (HH:MM) was the very last transfer?", LAST_TIME)],
          'grep -cw DENIED transfers.log ; grep -w DENIED transfers.log | cut -d " " -f 2 | sort | uniq -c | '
          "sort -n -r | head -n 1 ; tail -n 1 transfers.log"),

    # ------------------------------------------------------------ after 16-20: cleaning and editing files
    vault(4, "Clean Room",
          ["The roster of field agents came from a Windows laptop, so every line hides an invisible character. "
           "Clean it, count who is still active, and quietly move the Lisbon cell to Oslo."],
          "All 3 steps are done.",
          [("cat -A FILE", "show hidden characters (^M is a Windows line end)", "cat -A notes.txt"),
           ("tr -d 'CHARS' < FILE > NEW", "copy a file without those characters", "tr -d '\\t' < a.txt > b.txt"),
           ("grep -c 'TEXT$' FILE", "count lines that END with TEXT", "grep -c 'done$' tasks.txt"),
           ("sed -i 's/OLD/NEW/g' FILE", "replace text inside the file itself", "sed -i 's/red/blue/g' colors.txt"),
           SUBMIT, CHECK],
          {"roster.csv": ROSTER},
          [("Create clean.csv: roster.csv without the hidden Windows characters (completes by itself)",
            lambda g: lines_of(g, "clean.csv") in (CLEAN, [l.replace("lisbon", "oslo") for l in CLEAN])),
           ("How many agents in clean.csv are active?", "5"),
           ("Every agent in lisbon moves to oslo: change it inside clean.csv (completes by itself)",
            lambda g: lines_of(g, "clean.csv") == [l.replace("lisbon", "oslo") for l in CLEAN])],
          "cat -A roster.csv ; tr -d '\\r' < roster.csv > clean.csv ; grep -c ',active$' clean.csv ; "
          "sed -i 's/lisbon/oslo/g' clean.csv"),

    # ------------------------------------------------------------ after 21-25: network and totals
    vault(5, "Dark Net",
          ["A stranger is moving data out of Atlas. Check which watched server went dark, add up what the "
           "guest laptop sent, then sweep the drop folder clean."],
          "All 3 steps are done.",
          [("ping -c N HOST", "send N packets: replies = online, no reply = down", "ping -c 3 gateway"),
           ("cat /etc/hosts", "the names and IP addresses of the machines", "cat /etc/hosts"),
           ("awk -F, '$N == \"V\" {s += $M} END {print s}' FILE", "add up column M where column N is V (commas)",
            "awk -F, '$1 == \"bob\" {s += $2} END {print s}' pay.csv"),
           ('find FOLDER -name "PATTERN"', "find files by name in all subfolders", 'find docs -name "*.md"'),
           ("... | xargs CMD", "run CMD on every file in the list", "... | xargs echo"), SUBMIT, CHECK],
          {"watchlist.txt": "atlas-api\natlas-db-02\natlas-pre\ngateway",
           "exfil.csv": "host,file,kb\nguest-laptop-07,plans.pdf,420\natlas-api,status.json,3\n"
                        "guest-laptop-07,keys.txt,12\nguest-laptop-07,roster.csv,88\natlas-tst,report.txt,40",
           "drop/a.tmp": "x", "drop/x/b.tmp": "x", "drop/x/notes.txt": "keep", "drop/tmp-list.txt": "keep"},
          [("One server on watchlist.txt does not answer ping. Which one?", "atlas-pre"),
           ("How many KB did guest-laptop-07 send in total? (the kb column)", "520"),
           ("Delete every .tmp file below ~/drop, and nothing else (completes by itself)",
            lambda g: none_below("drop", ".tmp")(g) and has("drop/x/notes.txt")(g) and has("drop/tmp-list.txt")(g))],
          "ping -c 1 atlas-api ; ping -c 1 atlas-db-02 ; ping -c 1 atlas-pre ; ping -c 1 gateway ; "
          "awk -F, '$1 == \"guest-laptop-07\" {s += $3} END {print s}' exfil.csv ; "
          'find drop -name "*.tmp" | xargs rm'),

    # ------------------------------------------------------------ after 26-30: the API
    vault(6, "Back Channel",
          ["The API is the back door into Atlas. Get your own token, take a copy of the user list with you, and "
           "find out how many people can approve a gate."],
          "All 3 steps are done.",
          [("curl URL", "send a web request and show the answer", f"curl {API}/status"),
           ("URL?key=value", "send data in the URL (a query); quote the URL", f'curl "{API}/search?q=gate"'),
           ("curl URL > FILE", "save the answer in a file", f"curl {API}/status > status.txt"),
           ("grep -c '\"TEXT\"' FILE", "count lines with exactly \"TEXT\" (quotes included)", "grep -c '\"open\"' tickets.json"),
           SUBMIT, CHECK],
          {},
          [("Get an API token for the user analyst. What is it?", TOKEN),
           ("Save the user list from the API in agents.json (completes by itself)",
            lambda g: '"role"' in g.fs.d.get(HOME + "/agents.json", "")),
           ("How many users have the role approver?", "3")],
          f'curl {API}/token ; curl "{API}/token?user=analyst" ; curl {API}/api/users > agents.json ; '
          "grep -c '\"approver\"' agents.json"),

    # ------------------------------------------------------------ after 31-35: git and processes
    vault(7, "Mole Hunt",
          ["Someone inside Atlas is working for the other side. They left traces in the repository and a "
           "process is still running. Find the branch, the changed file, and shut the leak."],
          "All 3 steps are done.",
          [("cd FOLDER", "go into a folder", "cd projects"),
           ("git status", "branch, changed files and untracked files", "git status"),
           ("git branch", "list branches; * marks the current one", "git branch"),
           ("git diff", "show changes that are not committed yet", "git diff"),
           ("ps aux | grep WORD", "find a running process by name", "ps aux | grep nginx"),
           ("kill PID", "ask a process to stop", "kill 9999"), SUBMIT, CHECK],
          {},
          [("Which branch is checked out in ~/atlas?", "feature/night-shift"),
           ("Which tracked file has changes that are not committed? (its path)", ("app/auth.py", "auth.py", "atlas/app/auth.py")),
           ("A process with exfil in its name is running. Stop it (completes by itself)", lambda g: 5150 not in g.procs)],
          "cd atlas ; git status ; git branch ; git diff ; ps aux | grep exfil ; kill 5150", setup=setup_mole),

    # ------------------------------------------------------------ after 36-40: permissions, services, archives, disk
    vault(8, "Engine Room",
          ["The vault door is run by a service, and the service is down. Find the heaviest crate in the cargo "
           "hold, get the door running again, and pack that crate for the way out."],
          "All 3 steps are done.",
          [("du -s FOLDER...", "space used per folder, in KB", "du -s photos/*"),
           ("sort -n -r | head -n 1", "the biggest number first, only that line", "... | sort -n -r | head -n 1"),
           ("systemctl --user status NAME", "is a service running? why not?", "systemctl --user status mailer"),
           ("journalctl --user -u NAME -n N", "the last N lines a service logged", "journalctl --user -u mailer -n 5"),
           ("chmod NNN FILE", "set permissions: owner, group, others (6 = read+write, 4 = read)", "chmod 640 notes.txt"),
           ("systemctl --user restart NAME", "start a service again", "systemctl --user restart mailer"),
           ("tar -czf ARCHIVE FOLDER", "pack a folder into a compressed archive", "tar -czf photos.tar.gz photos"),
           SUBMIT, CHECK],
          {**{f"cargo/crates/c{i}.bin": "x" * 20000 for i in (1, 2, 3)},
           **{f"cargo/ammo/a{i}.bin": "x" * 3000 for i in range(1, 7)},
           "cargo/maps/route.txt": "north stairs, then left", "vault.conf": "door=closed\nmode=night", "out/": ""},
          [("Which folder under ~/cargo uses the most space? (its name)", ("crates", "cargo/crates")),
           ("The vault-door service is down. Read why, fix it, restart it (completes by itself)",
            lambda g: g.svc.get("vault-door", {}).get("state") == "active"),
           ("Pack that biggest folder into ~/out/cargo.tar.gz (completes by itself)",
            lambda g: "cargo/crates/c1.bin" in tar_members(g.fs, HOME + "/out/cargo.tar.gz"))],
          "du -s cargo/* | sort -n -r | head -n 1 ; systemctl --user status vault-door ; "
          "journalctl --user -u vault-door -n 5 ; chmod 640 vault.conf ; systemctl --user restart vault-door ; "
          "tar -czf out/cargo.tar.gz cargo/crates", setup=setup_engine),

    # ------------------------------------------------------------ after 41-45: system files, links, streams
    vault(9, "Paper Trail",
          ["Before the final job, cover your tracks. Count the locked accounts on this server, switch the front "
           "site to the new release, and run the sweep script so only its error is written down."],
          "All 3 steps are done.",
          [("grep -c 'TEXT$' FILE", "count lines that END with TEXT", "grep -c 'done$' tasks.txt"),
           ("readlink LINK", "show where a link points", "readlink latest"),
           ("ln -sfn TARGET LINK", "point an existing link somewhere else", "ln -sfn builds/b2 latest"),
           ("cat FILE", "show what is inside a file", "cat notes.md"),
           ("./FILE 2> LOG", "run a script, errors go into LOG", "./backup.sh 2> backup.err"),
           ("CMD > /dev/null", "throw the normal output away", "./backup.sh > /dev/null"), SUBMIT, CHECK],
          {"releases/v1.9.0/app.py": "VERSION = '1.9.0'", "releases/v2.0.0/app.py": "VERSION = '2.0.0'",
           "sweep.sh": '#!/bin/bash\necho "sweep started"\nls /vault/missing\necho "sweep done"'},
          [("How many accounts in /etc/passwd have nologin as their shell?", "3"),
           ("Point the link ~/front to releases/v2.0.0 (completes by itself)",
            lambda g: g.fs.links.get(HOME + "/front", "").rstrip("/") in ("releases/v2.0.0", HOME + "/releases/v2.0.0")),
           ("Run sweep.sh so that ONLY its error goes into sweep.err (completes by itself)",
            lambda g: lines_of(g, "sweep.err") == [SWEEP_ERROR])],
          "grep -c 'nologin$' /etc/passwd ; readlink front ; ln -sfn releases/v2.0.0 front ; cat sweep.sh ; "
          "./sweep.sh 2> sweep.err > /dev/null", setup=setup_paper),

    # ------------------------------------------------------------ after 46-50: the final vault
    vault(10, "Last Vault",
          ["The core of Atlas. The master key is somewhere in ~/core, next to decoy copies. Find the real one, "
           "lock it down, take everything with you, and leave your report. Then you were never here."],
          "All 4 steps are done.",
          [("grep -r WORD FOLDER", "search inside every file below a folder", "grep -r TODO src"),
           ("grep -v WORD", "hide the lines that contain WORD", "... | grep -v test"),
           ("chmod NNN FILE", "set permissions (600 = only you read and write)", "chmod 600 diary.txt"),
           ("tar -czf ARCHIVE FOLDER", "pack a folder into a compressed archive", "tar -czf photos.tar.gz photos"),
           ("echo TEXT > FILE", "write a line into a new file", "echo hello > note.txt"),
           ("echo TEXT >> FILE", "add a line at the end of a file", 'echo "line two" >> note.txt'), SUBMIT, CHECK],
          {"core/room-a/notes.txt": "guard shift changes at 03:00",
           "core/room-b/master.key.bak": "MASTERKEY=decoy-11",
           "core/room-c/old/master.key.bak": "MASTERKEY=decoy-12",
           "core/room-c/master.key": "MASTERKEY=omega-7"},
          [("What is the real MASTERKEY? (ignore the .bak copies)", ("omega-7", "MASTERKEY=omega-7")),
           ("Lock the real key file: only you may read and write it, 600 (completes by itself)",
            lambda g: g.fs.mode(HOME + "/core/room-c/master.key") & 0o777 == 0o600),
           ("Pack the whole ~/core folder into ~/exit.tar.gz (completes by itself)",
            lambda g: "core/room-c/master.key" in tar_members(g.fs, HOME + "/exit.tar.gz")),
           ("Write report.txt with exactly 2 lines:  key: <KEY>  /  status: secured   (completes by itself)",
            lambda g: lines_of(g, "report.txt") == ["key: omega-7", "status: secured"])],
          "grep -r MASTERKEY core | grep -v bak ; chmod 600 core/room-c/master.key ; tar -czf exit.tar.gz core ; "
          'echo "key: omega-7" > report.txt ; echo "status: secured" >> report.txt'),
]

# The story layer for the vaults (missions.py adds it like for any ticket): (name, first paragraph) and Pip's two lines.
OPS = {v["ticket"]: (v["name"], v["brief"][0]) for v in VAULTS}
PIP = {
    "VLT-01": ("Vault 1. Everything you learned, in one job.", "Find the key card, then take the plans."),
    "VLT-02": ("Vault 2. The guards love their drills.", "Find the one real alert, then erase the copies."),
    "VLT-03": ("Vault 3. Follow the money.", "Count the refusals and find who got refused most."),
    "VLT-04": ("Vault 4. Invisible ink again.", "Clean the roster, count the active, move a cell."),
    "VLT-05": ("Vault 5. Someone is moving data out.", "Find the dark server, add up the leak, sweep the drop."),
    "VLT-06": ("Vault 6. The back door is the API.", "Get a token, copy the users, count the approvers."),
    "VLT-07": ("Vault 7. There is a mole.", "Read the repository, then shut the leak."),
    "VLT-08": ("Vault 8. The door will not open.", "Find the heaviest crate, fix the door, pack it."),
    "VLT-09": ("Vault 9. Cover your tracks.", "Count, switch the release, silence the sweep."),
    "VLT-10": ("The last vault. This is it, partner.", "Find the real key, lock it, take it all, report."),
}
NUDGES = {
    "VLT-01": "Hidden files start with a dot. Then three jobs: a folder, a copy, a new name.",
    "VLT-02": "Search every file for ALERT, then hide the drills. Find lists the copies you must delete.",
    "VLT-03": "Count whole words only. Then take the account column of those lines and rank it.",
    "VLT-04": "Look at the hidden characters first. Remove them into a new file, then count and replace.",
    "VLT-05": "Ping each name once. awk can add up a column for one host. find + xargs deletes a list.",
    "VLT-06": "The token endpoint wants your user name in the URL. Save the users, then count the exact role.",
    "VLT-07": "git status answers two questions. ps aux with grep finds the process number.",
    "VLT-08": "du -s per folder, biggest first. The service log names the file it cannot read.",
    "VLT-09": "The shell is the last field. ln needs an extra option to move a link. 2> catches errors.",
    "VLT-10": "Search core for the key and hide the .bak lines. Then chmod, tar, and two echo lines.",
}
