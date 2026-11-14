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

## Features

- **Realistic shell.** Pipes, redirects (`>`, `2>&1`, here-documents), variables, `$(...)`, arithmetic, brace
  expansion, `for` / `while` / `if`, aliases, history and Tab completion.
- **60+ commands**, including `grep`, `find`, `sed`, `awk`, `tar`, `ssh`, `systemctl`, `journalctl`, `ps`,
  `kill`, `curl`, `chmod`, `ln` and `git`.
- **Real permissions and errors.** Ownership, `chmod` modes and "Permission denied" behave as on Linux.
- **Guided learning.** Every ticket lists the commands you need, three levels of hints, and a built-in manual
  (`man`).
- **Portable progress.** A clearance code on each ticket lets you continue on any computer.

## Quick start

| System | Start |
|---|---|
| Windows | Double-click `PenguinProtocol.bat` |
| macOS / Linux | Double-click `PenguinProtocol.command` (first time: right-click, Open) |
| Any terminal | `python3 linux_13.4.py` (Windows: `py -3 linux_13.4.py`) |

Requires Python 3.9 or newer. No packages to install.

## How to play

Each ticket shows what is wrong, what counts as done, and the commands you will need.

```text
tasks           list all tickets and your progress      hint          get help (3 levels)
task            show the current ticket again           check         see which requirements are met
submit ANSWER   send your answer                        man COMMAND   read a manual page
reset           rebuild the files of the ticket         help          list every command
```

Finishing a ticket unlocks the next one. Each card shows a **clearance code**: type `unlock CODE` on any
computer to jump back to that ticket, and `clearance` to show the code again.

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

Add a `task(...)` entry in `linuxip/tickets.py`. Card examples must use other files, folders and hosts than
the ticket and must never contain an answer; the tests check this. Add a first-level hint in `NUDGES`
(`tickets_data.py`) and the solution to `WALKTHROUGH` in the tests.
