# LinuxIP - Linux practice shell 

Windows: double-click `LinuxIP.bat` (or run `py -3 linux_13.4.py`).
macOS/Linux: double-click `LinuxIP.command` (or run `python3 linux_13.4.py`). If macOS blocks it, right-click > Open once. Python 3.9+, standard library only.
Everything is simulated in memory; the only real file written is `linuxip_save.json`.

## Where things are
| File | What it contains |
|---|---|
| `linux_13.4.py` | Entry point (starts the shell) |
| `linuxip/shell.py` | Runs command lines: pipes, redirects, `&&` `||` `;`, globs, exit codes, main loop |
| `linuxip/parser.py` | Quotes, `$VARIABLES`, `$?`, `~`, globs, operators (like bash) |
| `linuxip/vfs.py` | The simulated file system |
| `linuxip/cmd_files.py` | pwd cd ls tree cat less echo mkdir rmdir touch cp mv rm chmod find du df |
| `linuxip/cmd_text.py` | grep sort uniq cut head tail wc |
| `linuxip/cmd_network.py` | ip hostname ping curl (+ the Horizon API), whoami id date uname which type sudo |
| `linuxip/cmd_sys.py` | sed awk tr tee diff xargs ps kill ss systemctl journalctl ssh tar stat file |
| `linuxip/awk.py` | the small awk interpreter |
| `linuxip/clearance.py` | clearance codes: `unlock CODE` jumps to a ticket on any computer |
| `linuxip/cmd_dev.py` | export env python3 source pip flask git |
| `linuxip/cmd_tickets.py` | Ticket cards, submit/check/hint/tasks, save/load, help, man |
| `linuxip/manual.py` | `man` pages and `help` text |
| `linuxip/tickets.py` | **The 42 tickets** - edit here to change or add tickets |
| `linuxip/tickets_data.py` | Generated logs/CSVs, git and venv setups, first-level hints |
| `tests/test_linuxip.py` | Full walkthrough, real-Linux behaviour, and "no answers on the cards" checks |

## Run the tests (after every change)
    cd tests && python -m unittest -v

## Add a ticket
Add a `task(...)` entry in `linuxip/tickets.py` (copy an existing one). Card examples must use
OTHER files/folders/hosts than the ticket and never contain an answer - the tests check this.
Add a first-level hint in `NUDGES` (tickets_data.py) and the solution to `WALKTHROUGH` in the tests.
