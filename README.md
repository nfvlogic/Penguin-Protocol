<p align="center">
  <img src="docs/icon.png" alt="Penguin Protocol icon: a penguin detective with a magnifying glass" width="150">
</p>

<h1 align="center">Penguin Protocol</h1>

<p align="center"><b>Learn Linux by going undercover.</b><br>
A realistic terminal simulator with 50 covert missions and 10 vaults, from your first <code>ls</code> to a live incident.</p>

<p align="center"><a href="https://nfvlogic.github.io/Penguin-Protocol/"><b>Play in your browser</b></a></p>

<p align="center">
  <img src="docs/pip.svg" alt="Pip, the pixel penguin in a detective hat, waving hello and thinking" width="360"><br>
  <sub>Meet Pip, your partner inside Atlas.</sub>
</p>

<p align="center">
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-f5a031?labelColor=1a1a1a">
  <img alt="Dependencies: none" src="https://img.shields.io/badge/dependencies-none-f5a031?labelColor=1a1a1a">
  <img alt="Platforms" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20Web-f5a031?labelColor=1a1a1a">
  <img alt="Missions: 60" src="https://img.shields.io/badge/missions-60-f5a031?labelColor=1a1a1a">
  <a href="https://github.com/nfvlogic/Penguin-Protocol/actions/workflows/tests.yml"><img alt="Tests" src="https://github.com/nfvlogic/Penguin-Protocol/actions/workflows/tests.yml/badge.svg"></a>
</p>

---

## Overview

You are an operative with an engineer's badge, planted inside a company called Atlas. Your handlers (Control,
the Quartermaster, Counter-intel, Watchtower) send you briefings, and every mission is a situation you would
meet at work: an error hidden in a log, a full disk, a service that will not start, a file that anyone can read.
Stay quiet, find the evidence, leave no trace.

You solve them with real commands. The shell is a faithful simulation of bash on Ubuntu, so options, exit
codes and error messages match what you will see on a real server.

You are not alone: **Pip**, a tiny pixel penguin in an orange deerstalker, is your partner in the field. He tells
you each mission in two lines, explains what went wrong when an answer is off, and celebrates your firsts. Every
five missions he leads you into a **vault**: a boss mission that combines everything you just learned.

> Everything runs in memory. Nothing touches your real files, so you can break things freely.

## Demo

<p align="center">
  <img src="docs/demo.svg" alt="Animated demo: solving the first mission in Penguin Protocol" width="700">
</p>

The first mission, solved. Every new game has its own answers, so yours will differ.

<details>
<summary>Plain-text version</summary>

```text
──────────────────────────────────────────────────────────────────────────
 ATL-101  Operation Front Door                                       1/60

 ▄█▀█▀█▄   Your badge got you in. Prove your cover holds.
 ▀█▀▀▀█▀   Find the port Atlas uses on your machine.

 GOAL  Submit the local port number.
 TOOLS
   ls [FOLDER]  list the files in a folder (e.g. ls reports)
   cat FILE     show what is inside a file (e.g. cat notes.md)
   cd FOLDER    go into a folder; cd .. goes up, cd ~ goes home (e.g. cd
                projects)
 Found it? submit ANSWER    Stuck? hint    Briefing: task full
──────────────────────────────────────────────────────────────────────────

Pip: First time? Type  ls  to see what is here.
analyst@penguin:~$ cat welcome.txt
Welcome to the Atlas team!
The code is in ~/atlas. Start with README.md there.
analyst@penguin:~$ submit 8080

 ▄█▀█▀█▄   Wrong answer, try again.
 ▀█▀▀▀█▀   Old notes lie. The project README says how the app runs today.

analyst@penguin:~$ cd atlas
analyst@penguin:~/atlas$ cat README.md
# Atlas
Internal stage-gate app (Flask + MySQL). Formerly COMPASS.

Run locally:
  flask run --port 5050

More setup help: docs/setup.md
analyst@penguin:~/atlas$ submit 5050

 ▄█▀█▀█▄   ✓ Objective secured: Operation Front Door (ATL-101)
 ▀█▀▀▀█▀   Nice work, partner.
```

</details>

## Features

- **Realistic shell.** Pipes, redirects (`>`, `2>&1`, here-documents), variables, `$(...)`, arithmetic, brace
  expansion, `for` / `while` / `if`, aliases, history and Tab completion.
- **60+ commands**, including `grep`, `find`, `sed`, `awk`, `tar`, `ssh`, `systemctl`, `journalctl`, `ps`,
  `kill`, `curl`, `chmod`, `ln` and `git`.
- **Real permissions and errors.** Ownership, `chmod` modes and "Permission denied" behave as on Linux.
- **Missions with a story.** Fifty briefings with codenames, handlers and phases, from your first day inside to
  the final operation, plus ten vaults.
- **Pip, your partner.** A tiny animated pixel penguin who tells each mission in two lines, names the trap when an
  answer is wrong, hops when you use your first pipe, redirect or `grep`, and dozes while the game loads.
- **Vaults.** After every five missions comes a boss mission with its own look: gold card, Pip walking in with a
  golden key, and a bigger celebration when you crack it.
- **Short, clear cards.** One goal line (or a checklist), every tool with its meaning and an example, and tools you
  have not seen before marked **new**. The full briefing is one command away (`task full`).
- **Guided learning.** Three levels of hints and a built-in manual (`man`).
- **Runs anywhere.** Terminal on Windows, macOS and Linux, or in the browser as an installable app.
- **Portable progress.** Every level has a password, so you can continue on any computer.

## Quick start

| System | Start |
|---|---|
| Windows | Double-click `PenguinProtocol.bat` |
| macOS / Linux | Double-click `PenguinProtocol.command` (first time: right-click, Open) |
| Any terminal | `python3 penguin.py` (Windows: `py -3 penguin.py`) |

Requires Python 3.10 or newer. No packages to install.

## Play in the browser

**Play now: https://nfvlogic.github.io/Penguin-Protocol/**

The same game runs in a web page (the real Python code, through Pyodide) and installs like an app. On an iPhone
open the page in Safari, then Share, Add to Home Screen. It works offline after the first load and keeps your
progress on the device.

On a phone held upright the page shows its own on-screen keyboard, with a row of terminal keys (Tab, Ctrl+C,
Ctrl+D, `|`, `>`, `<`, `~`, `/`, `-`, `$`, quotes and history arrows) above it. The Kbd key switches between that
keyboard, the phone's own keyboard and none. On a computer, or with the phone on its side, the normal keyboard is
used. Tapping the output hides the keyboard; tapping the prompt brings it back.

To build and try it locally:

```bash
python3 tools/build_web.py
python3 -m http.server -d site
```

Pushing to `main` publishes it with GitHub Pages (`.github/workflows/pages.yml`).

## How to play

Each mission card shows Pip's two-line briefing, the goal (or a checklist that ticks itself), and the tools you
will need, with an example for each. `task full` shows the full briefing. Answer missions end with `submit`;
missions marked "closes by itself" finish as soon as everything on the checklist is true (`check` shows it).

```text
tasks           list all missions and your progress     hint          get help (3 levels)
task            show the current mission again          check         see which requirements are met
submit ANSWER   send your answer                        man COMMAND   read a manual page
reset           rebuild the files of the mission        help          list every command
level N         go to level N (password needed)         newgame       start over with new answers
newgame +       New Game+ (after you beat the game)     mode          show guided or New Game+
```

Finishing a mission unlocks the next one. Every new game has its own answers, saved with your progress.

**Continue anywhere.** After each vault the game prints the **password** of the next level. On any computer,
type `level 10` and enter the password of level 10 to start there. Levels you have already reached need no password, and
`password` shows the current one again. `newgame` starts over with new answers.

## New Game+

Once you beat all 60 missions, **New Game+** unlocks: type `newgame +` for a new run with new answers where cards
show only the briefing, there are no tips under errors, and you get one hint per mission. It is meant to feel like
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

| Phase | Missions | Focus |
|---|:-:|---|
| Infiltration | 7 | Navigating, files and folders, globs, hidden files, redirects |
| Reconnaissance | 6 | `find`, `grep` and its options, `head`, `tail`, `wc` |
| Surveillance | 3 | `cut`, `sort`, `uniq`, chaining commands, running scripts |
| Forensics | 6 | `tr`, `diff`, `sed`, `awk`, `xargs`, Windows line endings |
| Lateral movement | 3 | Networking, `ping`, `ssh`, `/etc/hosts`, disk space |
| The back channel | 4 | `curl`, headers, tokens, shell variables |
| Deep cover | 5 | Virtual environments, `git`, environment variables |
| Inside the walls | 7 | Processes, permissions, services, logs, archives, accounts |
| Tradecraft | 4 | Loops, redirection, `find` with `tar`, symbolic links |
| The final operation | 5 | Multi-step cases that combine everything |
| The Vault | 10 | One boss after every 5 missions, combining exactly what those 5 taught |

## Testing

```bash
cd tests && python -m unittest -v
```

`python3 tools/make_demo.py` rebuilds the animated demo and `python3 tools/make_pip.py` the picture of Pip, both
from the game itself.

The suite runs a full walkthrough of every mission and checks the shell against real Linux behaviour.
`tests/test_web.py` checks that the web page, its script and the game agree with each other (it needs no browser).

## Contributing

Add a `task(...)` entry in `penguin/tickets.py`, and in `penguin/missions.py` its codename and first paragraph
(`OPS`), Pip's two lines (`PIP`) and the trap Pip names after a wrong answer (`WRONG`). Vaults live in
`penguin/vaults.py`.
Card examples must use other files, folders and hosts than the mission and must never contain an answer; the tests check this. Add a first-level hint in `NUDGES`
(`penguin/tickets_data.py`) and the solution to `WALKTHROUGH` in the tests.

## License

Copyright (c) 2026 nfvlogic. All rights reserved.

You are welcome to view the code and run the game for your own learning. For anything else, such as copying,
sharing, changing, teaching with it or using it in a company, please ask first by opening an issue. See
[LICENSE](LICENSE).
