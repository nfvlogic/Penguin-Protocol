"""Text for help and man pages (kept short, in the style of real man pages).

Examples here use generic names on purpose: they never show a ticket's solution.
"""

# name: (description, synopsis, [options])
MAN = {
    "sed": ("stream editor: change or print lines of text", "sed [-n] [-i] [-E] 's/OLD/NEW/[g]' [FILE]...",
            ["s/OLD/NEW/   replace the first OLD of each line (add g for every OLD)", "-n  print only what a p command selects",
             "-i  change the file itself instead of printing", "-E  extended regular expressions",
             "3d, 2,4d, /text/d   delete a line, a range, or lines that match", "3p, 2,4p   print a line or a range (use with -n)"]),
    "awk": ("pattern scanning: work with the columns (fields) of each line", "awk [-F SEP] [-v VAR=VALUE] 'PROGRAM' [FILE]...",
            ["$1, $2 ... the fields of a line; $0 is the whole line; NF = number of fields; NR = line number",
             "-F SEP  field separator (default: spaces)", "'CONDITION {ACTION}'  run ACTION on lines where CONDITION is true",
             "BEGIN {...} runs before the first line, END {...} after the last", "print, printf, +=, ++, arrays: count[$1]++"]),
    "tr": ("translate or delete characters (reads standard input only)", "tr [-d] [-s] SET1 [SET2]",
           ["-d  delete the characters in SET1", "-s  squeeze repeated characters into one", "ranges: a-z   classes: [:upper:] [:digit:]"]),
    "tee": ("read from input and write to a file AND to the screen", "tee [-a] FILE...", ["-a  append instead of overwrite"]),
    "diff": ("compare two files line by line", "diff [-u] [-q] FILE1 FILE2",
             ["< lines only in FILE1,  > lines only in FILE2", "3c3 = line 3 changed, 5a6 = added, 7d6 = deleted",
              "-u  unified format (like git diff)", "-q  only say whether they differ", "exit status 0 = same, 1 = different"]),
    "xargs": ("build and run commands from standard input", "xargs [-n N] [-I {}] COMMAND [ARG]...",
              ["-n N  use at most N items per command", "-I {}  run once per line, replacing {} with the line"]),
    "basename": ("strip the folder from a path", "basename PATH [SUFFIX]", []),
    "dirname": ("strip the file name from a path", "dirname PATH", []),
    "sleep": ("wait for a number of seconds", "sleep N", []),
    "ps": ("show running processes", "ps | ps aux | ps -ef",
           ["aux  every process: user, PID, %CPU, %MEM, command", "-ef  every process with its parent (PPID)",
            "tip: ps aux | grep NAME finds one program (grep shows up too)"]),
    "pgrep": ("find process IDs by name", "pgrep [-f] [-l] PATTERN", ["-l  show the name too", "-f  match the whole command line"]),
    "kill": ("send a signal to a process (by PID)", "kill [-9] PID...",
             ["kill PID  polite request to stop (SIGTERM, 15)", "kill -9 PID  force it to stop (SIGKILL): the process cannot refuse",
              "you can only signal your own processes"]),
    "ss": ("show network sockets (replaces netstat)", "ss -tlnp",
           ["-t  TCP   -l  listening only   -n  numbers, no names   -p  show the process (PID)"]),
    "systemctl": ("control services", "systemctl [--user] status|start|stop|restart|is-active NAME",
                  ["--user  services of your own user (no root needed)", "status shows the state and the last log lines"]),
    "journalctl": ("read the system logs of services", "journalctl [--user] -u NAME [-n N] [-p err]",
                   ["-u NAME  one service", "-n N  the last N lines", "-p err  only errors"]),
    "ssh": ("run commands on another server", "ssh [user@]HOST [COMMAND]",
            ["ssh analyst@gateway uptime  runs uptime there and shows the answer", "needs the server to be online (see ping)"]),
    "tar": ("make and open archives", "tar -czf ARCHIVE.tar.gz FILE... | tar -tzf ARCHIVE | tar -xzf ARCHIVE [-C DIR] [FILE]",
            ["c create   x extract   t list   z gzip   f archive name (always last in the letters)   v verbose",
             "-C DIR  extract into that folder (it must exist)"]),
    "stat": ("show details of a file: size, permissions as a number, owner", "stat FILE...", []),
    "file": ("tell what kind of file something is", "file FILE...", ["shows things like Windows line endings (CRLF)"]),
    "uptime": ("how long the machine has been running and its load", "uptime", []),
    "free": ("show memory usage", "free [-h]", ["-h  human readable (Gi, Mi)"]),
    "true": ("do nothing, successfully (exit status 0)", "true", []),
    "false": ("do nothing, unsuccessfully (exit status 1)", "false", []),
    "pwd": ("print name of current/working directory", "pwd", []),
    "cd": ("change the working directory (bash builtin)", "cd [DIR]",
           ["cd        go to your home folder (~)", "cd ..     go up one folder", "cd -      go back to the previous folder"]),
    "ls": ("list directory contents", "ls [-a] [-l] [-h] [-1] [FILE]...",
           ["-a  do not hide entries starting with .", "-l  long listing: permissions, owner, size, date",
            "-h  sizes like 1.2K (with -l)", "-1  one entry per line"]),
    "ll": ("alias for ls -alF (as on Ubuntu)", "ll [FILE]...", []),
    "dir": ("list directory contents (same as ls; ls is what everybody uses)", "dir [FILE]...", []),
    "tree": ("list contents of directories in a tree-like format", "tree [-a] [DIR]", ["-a  include hidden files"]),
    "cat": ("concatenate files and print on the standard output", "cat [-n] [FILE]...", ["-n  number all output lines"]),
    "less": ("view a file (here: prints it; in real Linux press q to quit)", "less FILE", []),
    "more": ("view a file (here: prints it)", "more FILE", []),
    "head": ("output the first part of files", "head [-n N] [FILE]...", ["-n N  print the first N lines (default 10)"]),
    "tail": ("output the last part of files", "tail [-n N] [FILE]...", ["-n N  print the last N lines (default 10)"]),
    "wc": ("print newline, word, and byte counts", "wc [-l] [-w] [-c] [FILE]...",
           ["-l  lines", "-w  words", "-c  bytes"]),
    "echo": ("display a line of text", "echo [-n] [STRING]...",
             ["-n  do not output the trailing newline", "tip: echo text > file writes, >> appends"]),
    "mkdir": ("make directories", "mkdir [-p] DIRECTORY...", ["-p  no error if existing, make parent directories as needed"]),
    "rmdir": ("remove empty directories", "rmdir DIRECTORY...", []),
    "touch": ("create an empty file (or update its time)", "touch FILE...", []),
    "cp": ("copy files and directories", "cp [-r] SOURCE... DEST", ["-r  copy directories recursively"]),
    "mv": ("move (rename) files", "mv SOURCE... DEST", []),
    "rm": ("remove files or directories", "rm [-r] [-f] FILE...",
           ["-r  remove directories and their contents recursively", "-f  ignore nonexistent files, never prompt"]),
    "chmod": ("change file mode bits", "chmod MODE FILE...", ["+x   make executable", "-x   remove execute permission",
                                                              "755  rwxr-xr-x    644  rw-r--r--"]),
    "find": ("search for files in a directory hierarchy", "find [DIR] [-name PATTERN] [-iname PATTERN] [-type f|d]",
             ["-name P   file name matches P (quote wildcards: \"*.txt\")", "-iname P  same, ignoring case",
              "-type f   only files     -type d  only directories"]),
    "grep": ("print lines that match patterns", "grep [OPTIONS] PATTERN [FILE]...",
             ["-i  ignore case (grep is case-sensitive by default!)", "-v  invert: lines that do NOT match",
              "-c  print only a count of matching lines", "-n  prefix each line with its line number",
              "-r  read all files under each directory", "-l  print only names of files with a match",
              "-w  match whole words only", "-E  extended regex (a|b, +, ?)", "-F  pattern is plain text, not a regex"]),
    "sort": ("sort lines of text files", "sort [-n] [-r] [-u] [-t SEP -k N] [FILE]...",
             ["-n  compare as numbers", "-r  reverse", "-u  unique lines only", "-t SEP -k N  sort by field N"]),
    "uniq": ("report or omit repeated lines (input must be sorted!)", "uniq [-c] [-d] [-u] [FILE]",
             ["-c  prefix lines by the number of occurrences", "-d  only print duplicate lines",
              "-u  only print unique lines"]),
    "cut": ("remove sections from each line of files", "cut -d DELIM -f LIST [FILE]...",
            ["-d DELIM  use DELIM instead of TAB", "-f LIST   select these fields, e.g. -f 1 or -f 1,3"]),
    "du": ("estimate file space usage", "du [-s] [-h] [FILE]...", ["-s  total only", "-h  human readable"]),
    "df": ("report file system disk space usage", "df [-h]", ["-h  human readable"]),
    "ip": ("show routing, network devices, interfaces", "ip addr | ip route", []),
    "hostname": ("show the system's host name", "hostname [-I]", ["-I  show the IP addresses"]),
    "ping": ("send ICMP ECHO_REQUEST to network hosts", "ping [-c COUNT] HOST",
             ["-c N  stop after N packets (real ping runs until Ctrl+C)"]),
    "curl": ("transfer a URL (call web servers and APIs)", "curl [-i] [-s] [-H HEADER] [-o FILE] URL",
             ["-i  include the HTTP status line in the output", "-H  send a header, e.g. -H \"Accept: application/json\"",
              "-o FILE  write the body to FILE", "-s  silent"]),
    "whoami": ("print effective user name", "whoami", []),
    "id": ("print user and group ids", "id", []),
    "date": ("print the system date and time", "date", []),
    "uname": ("print system information", "uname [-a]", []),
    "which": ("locate a command", "which COMMAND", []),
    "type": ("describe a command (bash builtin)", "type NAME", []),
    "sudo": ("execute a command as another user", "sudo COMMAND", []),
    "history": ("show the commands you typed", "history", []),
    "clear": ("clear the terminal screen", "clear", []),
    "export": ("set an environment variable", "export NAME=value", []),
    "unset": ("remove a variable", "unset NAME", []),
    "env": ("print the environment variables", "env", []),
    "source": ("run commands from a file in this shell", "source FILE   (or: . FILE)",
               ["source DIR/bin/activate  turns a Python virtual env on"]),
    "deactivate": ("turn the active Python virtual env off", "deactivate", []),
    "python": ("Python interpreter (only inside a venv on Ubuntu)", "python [--version] [-m MODULE]", []),
    "python3": ("Python interpreter", "python3 [--version] [-m MODULE]", ["-m venv DIR  create a virtual env in DIR"]),
    "pip": ("Python package installer (needs an active venv)", "pip install -r FILE | pip list | pip freeze", []),
    "flask": ("Flask command line", "flask run [--port N]", []),
    "git": ("the stupid content tracker", "git <command> [args]",
            ["status            what changed", "log --oneline     list of commits", "diff [--staged]   show changes",
             "branch            list branches", "checkout -b NAME  create a branch and switch to it",
             "switch NAME       switch branch", "add FILE          stage a file", "commit -m \"msg\"   save staged changes",
             "restore FILE      undo uncommitted changes in a file"]),
    "man": ("an interface to the system reference manuals", "man COMMAND", []),
    "help": ("list the commands of this practice shell", "help", []),
    "exit": ("leave the shell (progress is saved)", "exit", []),
    # practice-shell commands (not part of real Linux)
    "submit": ("[practice] send the answer of the current ticket", "submit ANSWER", []),
    "check": ("[practice] show the requirements of the current ticket", "check", []),
    "hint": ("[practice] get a hint (type it again for more)", "hint", []),
    "task": ("[practice] reminder of the current ticket", "task | task full | task N", []),
    "tasks": ("[practice] list all tickets and their status", "tasks", []),
    "clearance": ("[practice] show the clearance code of the current ticket", "clearance", []),
    "unlock": ("[practice] jump to the ticket a clearance code belongs to (works on any computer)",
               "unlock CODE", []),
    "reset": ("[practice] rebuild the files of the current ticket", "reset", []),
    "save": ("[practice] save your progress", "save", []),
    "tips": ("[practice] turn the learning tips under errors on or off", "tips on | tips off", []),
}

HELP = """FILES      pwd  cd [dir|..|-|~]  ls [-a -l -h]  tree  cat  less  head/tail -n N  wc -l
           mkdir [-p]  rmdir  touch  cp [-r]  mv  rm [-r -f]  chmod MODE  ./script.sh  du -sh  df -h
SEARCH     find DIR -name "PATTERN" [-type f|d]   grep [-i -v -c -n -r -l -w -E] PATTERN [FILE]
           sort [-n -r -u]  uniq [-c -d -u]  cut -d SEP -f N
NETWORK    ip addr  hostname -I  ping -c N HOST  curl [-i -H HEADER] URL
TEXT       sed 's/OLD/NEW/g' FILE  awk '{print $1}' FILE  tr -d '\r'  tee FILE  diff A B  xargs CMD
SERVERS    ps aux  pgrep  kill [-9] PID  ss -tlnp  systemctl --user status|restart X  journalctl -u X
           ssh user@host CMD  tar -czf|-tzf|-xzf  stat  file  uptime  free -h
SYSTEM     whoami  id  date  uname -a  which CMD  type CMD  history  clear  sudo
DEV        git status | log --oneline | diff [--staged] | branch | checkout -b NAME | switch NAME
               add FILE | commit -m "msg" | restore FILE
           python3 -m venv DIR   source DIR/bin/activate   deactivate
           pip install -r FILE   pip list   flask run [--port N]
           export NAME=value   env   echo $NAME   unset NAME
SHELL      a | b     output of a becomes input of b        cmd > file   save output (>> appends)
           a && b    run b only if a worked                cmd < file   read input from file
           a || b    run b only if a failed                cmd 2> file  save error messages
           a ; b     run both                              echo $?      exit status of last command
           "quotes" keep spaces and stop * from expanding  # comment
TICKETS    task  task full  tasks  task N  unlock CODE  clearance  hint  check  submit ANSWER  reset  save  tips on|off  exit
MORE       man CMD explains a command and its options. Arrow up repeats commands. Scroll up for history.
NOTE       Like real Linux, everything is case-sensitive: File.txt and file.txt are different files."""
