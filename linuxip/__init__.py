"""Penguin Protocol - a Linux practice shell for the Atlas team (simulated, safe to experiment in).

Modules:
  core.py          constants, colours, ShellError
  vfs.py           the simulated file system
  parser.py        quotes, variables, globs, | > >> < 2> ; && ||
  shell.py         runs command lines, main loop
  cmd_files.py     pwd cd ls tree cat less echo mkdir rmdir touch cp mv rm chmod find du df
  cmd_text.py      grep sort uniq cut head tail wc
  cmd_network.py   ip hostname ping curl (+ the Atlas API), whoami id date uname which type sudo
  cmd_dev.py       export env python3 source pip flask git
  cmd_tickets.py   ticket cards, submit check hint tasks, save/load, help, man
  manual.py        man pages and help text
  tickets.py       the 50 tickets (edit here to add tickets)
  tickets_data.py  generated log files, CSVs and git/venv setups for the tickets
"""
