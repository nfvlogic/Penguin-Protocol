<h1 align="center">Penguin Protocol</h1>

<p align="center"><b>Learn Linux by doing the job.</b><br>
A realistic terminal simulator with 50 hands-on tickets, from your first <code>ls</code> to a live incident.</p>

<p align="center">
  <img alt="Python 3.9+" src="https://img.shields.io/badge/python-3.9%2B-blue">
  <img alt="Dependencies: none" src="https://img.shields.io/badge/dependencies-none-brightgreen">
  <img alt="Platforms" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey">
  <img alt="Tickets: 50" src="https://img.shields.io/badge/tickets-50-orange">
</p>

---

## Overview

Penguin Protocol puts you in the seat of a new engineer on a team. Tickets arrive from the tech lead, QA,
security and monitoring, and each one is a situation you would meet at work: an error hidden in a log, a full
disk, a service that will not start, a file that anyone can read.

You solve them with real commands. The shell is a faithful simulation of bash on Ubuntu, so options, exit
codes and error messages match what you will see on a real server.

> Everything runs in memory. Nothing touches your real files, so you can break things freely.

## Demo

<p align="center">
  <img src="docs/demo.svg" alt="Animated demo: solving the first ticket in Penguin Protocol" width="700">
</p>

The first ticket, solved. Every new game has its own answers, so yours will differ.

<details>
<summary>Plain-text version</summary>

```text
──────────────────────────────────────────────────────────────────────────
 ATL-101  Run Atlas locally                              Priority: Normal
 From: Tech lead   Module: Onboarding   Ticket 1 of 50
 Password: PP-01-WYYR-3VU5
──────────────────────────────────────────────────────────────────────────
 DESCRIPTION                       │ COMMANDS (examples: other files)
 Welcome to the Atlas team! Atlas  │ ls [FOLDER]
 is our internal stage-gate app    │   list the files in a folder (e.g. ls
 (Flask + MySQL). Before you pick  │   reports)
 up feature work, you need to run  │ cat FILE
 it on your machine.               │   show what is inside a file (e.g.
                                   │   cat notes.md)
 Start with the welcome file in    │ cd FOLDER
 your home folder: it tells you    │   go into a folder; cd .. goes up, cd
 where the project documentation   │   ~ goes home (e.g. cd projects)
 is. Find the port the app uses    │
 when you run it locally.          │
                                   │
 RESOLVED WHEN                     │
 You submit the local port number. │
──────────────────────────────────────────────────────────────────────────
 Always available: ls cd pwd cat less tree man   Ticket: task  check
   hint  submit  password

analyst@penguin:~$ cat welcome.txt
Welcome to the Atlas team!
The code is in ~/atlas. Start with README.md there.
analyst@penguin:~$ cd atlas
analyst@penguin:~/atlas$ cat README.md
# Atlas
Internal stage-gate app (Flask + MySQL). Formerly COMPASS.

Run locally:
  flask run --port 5050

More setup help: docs/setup.md
analyst@penguin:~/atlas$ submit 5050
✓ Ticket ATL-101 resolved: Run Atlas locally
Password for level 2: PP-02-HZT3-6T2X  (keep it: type  level 2  on any computer and enter it to start here)
```

</details>

## Features

- **Realistic shell.** Pipes, redirects (`>`, `2>&1`, here-documents), variables, `$(...)`, arithmetic, brace
  expansion, `for` / `while` / `if`, aliases, history and Tab completion.
- **60+ commands**, including `grep`, `find`, `sed`, `awk`, `tar`, `ssh`, `systemctl`, `journalctl`, `ps`,
  `kill`, `curl`, `chmod`, `ln` and `git`.
- **Real permissions and errors.** Ownership, `chmod` modes and "Permission denied" behave as on Linux.
- **Guided learning.** Every ticket lists the commands you need, three levels of hints, and a built-in manual
  (`man`).
- **Portable progress.** Every level has a password, so you can continue on any computer.

## Quick start

| System | Start |
|---|---|
| Windows | Double-click `PenguinProtocol.bat` |
| macOS / Linux | Double-click `PenguinProtocol.command` (first time: right-click, Open) |
| Any terminal | `python3 penguin.py` (Windows: `py -3 penguin.py`) |

Requires Python 3.9 or newer. No packages to install.

## How to play

Each ticket shows what is wrong, what counts as done, and the commands you will need.

```text
tasks           list all tickets and your progress      hint          get help (3 levels)
task            show the current ticket again           check         see which requirements are met
submit ANSWER   send your answer                        man COMMAND   read a manual page
reset           rebuild the files of the ticket         help          list every command
level N         go to level N (password needed)         newgame       start over with new answers
newgame +       New Game+ (after you beat the game)     mode          show guided or New Game+
```

Finishing a ticket unlocks the next one. Every new game has its own answers, saved with your progress.

**Continue anywhere.** Each ticket card shows the **password** of its level. On any computer, type `level 10`
and enter the password of level 10 to start there. Levels you have already reached need no password, and
`password` shows the current one again. `newgame` starts over with new answers.

## New Game+

Once you beat all 50 tickets, **New Game+** unlocks: type `newgame +` for a new run with new answers where cards
show only the problem, there are no tips under errors, and you get one hint per ticket. It is meant to feel like
doing the job for real, with just `man` and your memory. The password to unlock it on another computer is
printed when you finish the game.

## Command line

```text
python3 penguin.py              continue your game (or start a new one)
python3 penguin.py --new        start a new game with new answers
python3 penguin.py --plus       start New Game+ (needs a beaten game, see below)
python3 penguin.py --seed 42    use answer set 42 (the same number gives the same answers)
python3 penguin.py --version    show the version        --help   show all options
```

The built-in manual (`man grep`, `man find`, ...) has a description, options, examples, exit status and related
commands, like a real manual page.

## Curriculum

| Module | Tickets | Focus |
|---|:-:|---|
| Onboarding | 7 | Navigating, files and folders, globs, hidden files, redirects |
| Code search | 6 | `find`, `grep` and its options, `head`, `tail`, `wc` |
| Pipes | 3 | `cut`, `sort`, `uniq`, chaining commands, running scripts |
| Text tools | 6 | `tr`, `diff`, `sed`, `awk`, `xargs`, Windows line endings |
| Environments | 3 | Networking, `ping`, `ssh`, `/etc/hosts`, disk space |
| API | 4 | `curl`, headers, tokens, shell variables |
| Git & Python | 5 | Virtual environments, `git`, environment variables |
| Servers | 7 | Processes, permissions, services, logs, archives, accounts |
| Scripting | 4 | Loops, redirection, `find` with `tar`, symbolic links |
| Feature work | 5 | Multi-step cases that combine everything |

## Testing

```bash
cd tests && python -m unittest -v
```

The suite runs a full walkthrough of every ticket and checks the shell against real Linux behaviour.

## Contributing

Add a `task(...)` entry in `penguin/tickets.py`. Card examples must use other files, folders and hosts than
the ticket and must never contain an answer; the tests check this. Add a first-level hint in `NUDGES`
(`penguin/tickets_data.py`) and the solution to `WALKTHROUGH` in the tests.
