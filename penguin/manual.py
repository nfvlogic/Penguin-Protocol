"""Text for help and man pages (kept short, in the style of real man pages).

Examples here use generic names on purpose: they never show a ticket's solution.
"""

# Commands that exist only in this practice shell (not on real Linux)
PRACTICE = {"submit", "check", "hint", "task", "tasks", "reset", "save", "tips", "help", "clearance", "password", "unlock", "level", "newgame", "mode"}

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
    "printf": ("format and print text (a builtin)", "printf FORMAT [ARGUMENT]...",
               ["%s text  %d number  %f decimal  %x hex   \\n newline  \\t tab", "the format is reused until every argument is used"]),
    "alias": ("make a short name for a command", "alias [NAME='COMMAND ARGS']", ["alias ll='ls -l'   then   ll works as ls -l", "alias alone lists them"]),
    "unalias": ("remove an alias", "unalias NAME", []),
    "seq": ("print a sequence of numbers", "seq [FIRST [STEP]] LAST", ["seq 5 = 1 2 3 4 5   seq 2 2 10 = 2 4 6 8 10"]),
    "nl": ("number the lines of a file", "nl [-b a] [FILE]", ["-b a  number empty lines too"]),
    "rev": ("reverse every line character by character", "rev [FILE]", []),
    "ln": ("make links between files", "ln -s TARGET LINKNAME",
           ["-s  symbolic link: LINKNAME points to TARGET (ls -l shows LINKNAME -> TARGET)", "-f  replace an existing link",
            "-n  if LINKNAME is a link to a folder, replace the link itself (without -n the new link is made inside that folder)"]),
    "readlink": ("print where a symbolic link points", "readlink [-f] LINK", ["-f  the full real path"]),
    "top": ("show the busiest processes (here: one snapshot)", "top [-b -n 1]", ["%CPU and %MEM columns show who uses the machine"]),
    "pushd": ("go to a folder and remember the one you left", "pushd DIR", ["popd goes back, dirs shows the stack"]),
    "popd": ("go back to the folder remembered by pushd", "popd", []),
    "dirs": ("show the pushd/popd folder stack", "dirs", []),
    "tac": ("print a file backwards, last line first", "tac [FILE]", []),
    "date": ("show the date and time", "date [+FORMAT] [-u]", ["+%F  2026-11-12   +%H:%M  hours:minutes   +%s  seconds since 1970", "-u  in UTC"]),
    "umask": ("show the default permission mask", "umask", []),
    "chown": ("change the owner of a file (needs root)", "chown OWNER[:GROUP] FILE...", []),
    "chgrp": ("change the group of a file (needs root)", "chgrp GROUP FILE...", []),
    "test": ("check conditions: files, text, numbers (same as [ ])", "test EXPRESSION   or   [ EXPRESSION ]",
             ["-f FILE file exists   -d DIR folder exists   -e exists   -s not empty   -r -w -x permissions",
              "-z TEXT empty   -n TEXT not empty   A = B equal text   A != B different text",
              "N -eq M equal   -ne  -lt  -gt  -le  -ge   (numbers)   ! NOT   -a AND   -o OR",
              "exit status 0 = true, 1 = false: use it with if and while"]),
    "[": ("check conditions: same as test, the last argument must be ]", "[ EXPRESSION ]", ["see man test"]),
    "[[": ("check conditions (bash): like [ with patterns: [[ $x == a* ]]", "[[ EXPRESSION ]]", ["see man test"]),
    "read": ("read a line from the keyboard into a variable", "read [-p PROMPT] NAME", []),
    "let": ("do arithmetic on variables", "let NAME=EXPRESSION", ["let n=n+1   same as   n=$((n+1))"]),
    "break": ("leave a for/while loop", "break", []),
    "continue": ("jump to the next round of a loop", "continue", []),
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
    "task": ("[practice] show the whole briefing of the current mission again", "task | task N", []),
    "tasks": ("[practice] list all tickets and their status", "tasks", []),
    "password": ("[practice] show the password of the current level (to continue on another computer)", "password", []),
    "clearance": ("[practice] same as password", "clearance", []),
    "unlock": ("[practice] jump to the level a password belongs to (works on any computer)",
               "unlock CODE", []),
    "level": ("[practice] go to a level; levels you have not reached need their password", "level N",
              ["the password is shown on the ticket card, and printed when you finish the level before", "level alone shows where you are"]),
    "mode": ("[practice] show whether you play guided or New Game+", "mode", []),
    "newgame": ("[practice] start over with new answers; newgame + starts New Game+", "newgame | newgame +",
                ["newgame  progress reset, every answer changes", "newgame +  New Game+, unlocked when you beat the game: new answers, "
                 "no command lists, no tips, one hint per ticket", "the New Game+ password is printed when you finish; it unlocks it on any computer"]),
    "reset": ("[practice] rebuild the files of the current ticket", "reset", []),
    "save": ("[practice] save your progress", "save", []),
    "tips": ("[practice] turn the learning tips under errors on or off", "tips on | tips off", []),
}


# The options of the most used commands (override the short entries above)
MAN.update({
    "ls": ("list directory contents", "ls [-a] [-A] [-l] [-h] [-1] [-d] [-R] [-t] [-S] [-r] [-F] [FILE]...",
           ["-a  do not hide entries starting with .   -A  same, without . and ..", "-l  long listing: permissions, links, owner, size, date",
            "-h  sizes like 1.2K (with -l)   -1  one entry per line", "-d  list the folder itself, not what is inside",
            "-R  recursive: every folder below too", "-t  newest first   -S  biggest first   -r  reverse the order",
            "-F  add / to folders and * to programs", "in -l, the first letter is d (folder), - (file) or l (link: name -> target)"]),
    "cat": ("concatenate files and print on the standard output", "cat [-n] [-A] [FILE]...",
            ["-n  number all output lines", "-A  show hidden characters: $ end of line, ^M Windows line ending, ^I tab",
             "with no file, cat reads what you type until Ctrl+D"]),
    "head": ("output the first part of files", "head [-n N] [-c N] [-q] [-v] [FILE]...",
             ["-n N  the first N lines (default 10); -n -N = all but the last N", "-c N  the first N bytes",
              "-q / -v  never / always print the file name header"]),
    "tail": ("output the last part of files", "tail [-n N] [-c N] [-f] [FILE]...",
             ["-n N  the last N lines (default 10); -n +N = from line N to the end", "-c N  the last N bytes",
              "-f  keep waiting for new lines (here: shows the end and stops)"]),
    "wc": ("print newline, word, and byte counts", "wc [-l] [-w] [-c] [-m] [FILE]...",
           ["-l  lines", "-w  words", "-c  bytes", "-m  characters"]),
    "echo": ("display a line of text", "echo [-n] [-e] [STRING]...",
             ["-n  no trailing newline", "-e  understand \\n (newline), \\t (tab), \\\\ (backslash)",
              "tip: echo text > file writes, >> appends"]),
    "touch": ("create an empty file (or update its time)", "touch [-c] FILE...", ["-c  do not create files that do not exist"]),
    "cp": ("copy files and directories", "cp [-r] [-i] [-v] SOURCE... DEST",
           ["-r  copy directories recursively", "DEST can be a new name or a folder", "a link is followed: the copy is of the target"]),
    "chmod": ("change file mode bits", "chmod MODE FILE...",
              ["numbers: 3 digits for owner, group, others; r=4 w=2 x=1 added up (755 = rwxr-xr-x, 644 = rw-r--r--, 600 = rw-------)",
               "letters: who (u g o a) + or - or = what (r w x):  u+x   g-w   o-rwx   a=r   u+x,g-w",
               "check the result with ls -l or stat"]),
    "find": ("search for files in a directory hierarchy", "find [DIR...] [TESTS] [ACTION]",
             ["-name P / -iname P  file name matches P (quote wildcards: \"*.txt\"); -path P the whole path",
              "-type f|d|l  files, folders, links     -empty  empty files or folders     -perm 644  exact permissions",
              "-size +1k  bigger than 1 KiB (-1k smaller; c bytes, k, M, G)     -mtime -1  changed less than 1 day ago",
              "-maxdepth N / -mindepth N  how deep to look     ! TEST  NOT     TEST -o TEST  OR     \\( ... \\)  grouping",
              "-exec CMD {} \\;  run CMD for every match ({} = the file); with + all matches at once",
              "-delete  remove the matches     -print  print them (the default)"]),
    "grep": ("print lines that match patterns", "grep [OPTIONS] PATTERN [FILE]...",
             ["-i  ignore case (grep is case-sensitive by default!)", "-v  invert: lines that do NOT match",
              "-c  print only a count of matching lines", "-n  prefix each line with its line number",
              "-r  read all files under each directory     --include=GLOB / --exclude=GLOB  only / not these file names",
              "-l / -L  only names of files with / without a match", "-w  whole words only     -x  whole lines only",
              "-E  extended regex (a|b, +, ?)     -F  plain text     -o  only the matching part",
              "-e P  a pattern (repeat -e for several)     -m N  stop after N matches     -s  hide file errors",
              "-A N / -B N / -C N  also show N lines after / before / around each match", "-h / -H  hide / show file names"]),
    "sort": ("sort lines of text files", "sort [-n] [-h] [-r] [-u] [-f] [-t SEP -k N] [FILE]...",
             ["-n  compare as numbers   -h  as sizes (1K 2M)", "-r  reverse   -u  unique lines only   -f  ignore case",
              "-t SEP -k N  sort by field N"]),
    "curl": ("transfer a URL (call web servers and APIs)", "curl [-i] [-I] [-s] [-f] [-H HEADER] [-o FILE] [-w FORMAT] URL",
             ["-i  include the HTTP status line and headers   -I  only the headers (HEAD request)",
              "-H  send a header, e.g. -H \"Accept: application/json\"", "-o FILE  write the body to FILE   -s  silent",
              "-f  fail with an error (exit 22) on HTTP errors   -v  show the request and response headers",
              "-w FORMAT  print info after the transfer: %{http_code} %{size_download} %{time_total}"]),
    "uname": ("print system information", "uname [-a] [-s] [-n] [-r] [-m]",
              ["-a  everything   -s  kernel name   -n  host name   -r  kernel release   -m  machine"]),
    "id": ("print user and group ids", "id [-u] [-g] [-n]", ["-u  just the user id   -g  group id   -n  names instead of numbers"]),
})

HELP = """FILES      pwd  cd [dir|..|-|~]  ls [-a -l -h -R -t -S]  tree  cat  less  head/tail -n N -c N  wc -l
           mkdir [-p]  rmdir  touch  cp [-r]  mv  rm [-r -f]  chmod MODE  ./script.sh  du -sh  df -h
SEARCH     find DIR -name "PATTERN" -type f|d -size -mtime -exec ... \\;   grep [-i -v -c -n -r -l -w -E -A -B -C] PATTERN [FILE]
           sort [-n -r -u]  uniq [-c -d -u]  cut -d SEP -f N
NETWORK    ip addr  hostname -I  ping -c N HOST  curl [-i -H HEADER] URL
TEXT       sed 's/OLD/NEW/g' FILE  awk '{print $1}' FILE  tr -d '\\r'  tee FILE  diff A B  xargs CMD
SERVERS    ps aux  pgrep  kill [-9] PID  ss -tlnp  systemctl --user status|restart X  journalctl -u X
           ssh user@host CMD  tar -czf|-tzf|-xzf  stat  file  uptime  free -h
SYSTEM     whoami  id  date  uname -a  which CMD  type CMD  history  clear  sudo
DEV        git status | log --oneline | diff [--staged] | branch | checkout -b NAME | switch NAME
               add FILE | commit -m "msg" | restore FILE
           python3 -m venv DIR   source DIR/bin/activate   deactivate
           pip install -r FILE   pip list   flask run [--port N]
           export NAME=value   env   echo $NAME   unset NAME
SCRIPTING  for f in *.log; do echo $f; done     if [ -f x ]; then echo yes; else echo no; fi
           while [ $n -lt 3 ]; do n=$((n+1)); done    echo $(date +%F)   echo {a,b}.txt   $((2+3))
           alias  seq  printf  read  test  [ ]  !! (repeat the last command)   cat <<EOF ... EOF   (Tab completes)
SHELL      a | b     output of a becomes input of b        cmd > file   save output (>> appends)
           a && b    run b only if a worked                cmd < file   read input from file
           a || b    run b only if a failed                cmd 2> file  save error messages   cmd 2>&1  errors join the output
           a ; b     run both                              echo $?      exit status of last command
           "quotes" keep spaces and stop * from expanding  # comment
TICKETS    task  tasks  task N  level N  unlock CODE  password  newgame [+]  mode  hint  check  submit ANSWER  reset  save  tips on|off  exit
MORE       man CMD explains a command and its options. Arrow up repeats commands. Scroll up for history.
NOTE       Like real Linux, everything is case-sensitive: File.txt and file.txt are different files."""


# ---------------------------------------------------------------- longer manual pages (DESCRIPTION, EXAMPLES, EXIT STATUS, SEE ALSO)
DESCRIPTION = {
    "ls": "Lists the files and folders inside the given folders (the current one by default). Names are sorted alphabetically, "
          "ignoring case. Names that start with a dot are hidden unless you ask for them with -a or -A. With -l, every file gets "
          "one line: type and permissions, number of links, owner, group, size, date and name.",
    "cd": "Changes the folder your shell is working in. It is built into the shell, because a separate program could not "
          "change the folder of the shell that started it. Without an argument it goes to your home folder.",
    "pwd": "Prints the full path of the folder you are in.",
    "cat": "Prints files one after the other on the screen. Because it simply copies its input to its output, it is also used "
           "to join files, and (with a redirect) to create small files: type the text, then press Ctrl+D.",
    "head": "Prints the first part of each file: the first 10 lines by default. With several files it writes a header with each name.",
    "tail": "Prints the last part of each file: the last 10 lines by default. It is the quick way to look at the newest entries "
            "of a log, where new lines are added at the end.",
    "wc": "Counts the lines, words and bytes of its input. With one option it prints just that number, which makes it handy at "
          "the end of a pipe to count what the earlier commands found.",
    "cp": "Copies files. With several sources the last argument must be a folder. Copying a folder needs -r. If the destination "
          "file exists it is overwritten without asking.",
    "mv": "Moves files and folders, and renames them: moving a file to a new name in the same folder is how you rename it. "
          "An existing destination is replaced without asking.",
    "rm": "Removes files. There is no trash can: what rm deletes is gone. A folder needs -r. Check the names first, for example "
          "by running the same pattern with echo or ls before you delete.",
    "mkdir": "Creates folders. A plain mkdir creates one level and fails if the parent does not exist; -p creates every missing "
             "parent and is not an error when the folder already exists.",
    "touch": "Creates an empty file, or updates the modification time of an existing one.",
    "chmod": "Changes who may read (r), write (w) or execute (x) a file. Permissions are given separately to the owner (u), the "
             "group (g) and everybody else (o). Numbers add r=4, w=2, x=1 for each of the three: 640 means owner rw-, group r--, "
             "others none. For a folder, x means that you may enter it.",
    "find": "Walks down a folder tree and prints the paths that match all the tests you give. Tests are combined with AND "
            "unless you write -o. By default it prints each match (-print); -exec runs a command on each one instead. "
            "Always quote patterns such as '*.txt' so the shell does not expand them first.",
    "grep": "Prints the lines that match a pattern. The pattern is a basic regular expression unless you use -E (extended) or "
            "-F (plain text). Matching is case-sensitive by default. Together with a pipe it is the main tool for finding "
            "things in logs and command output.",
    "sort": "Sorts lines. By default the order is alphabetical, so 10 comes before 9: use -n for numbers and -h for sizes "
            "such as 2K and 3M. uniq needs sorted input, so sort usually comes before it.",
    "uniq": "Collapses repeated neighbouring lines. Only lines that are next to each other are compared, so sort the input "
            "first. With -c every line is prefixed by how many times it occurred.",
    "cut": "Cuts columns out of each line, either by character position (-c) or by a separator (-d) and field numbers (-f).",
    "sed": "A stream editor: it reads text line by line, applies the commands you give it, and prints the result. The most used "
           "command is s/OLD/NEW/, which substitutes text. With -i it changes the file itself instead of printing.",
    "awk": "A small programming language for text made of columns. Each line is split into fields $1, $2 ... and the program "
           "is a list of CONDITION {ACTION} rules. With variables you can add numbers, and with arrays you can count by name.",
    "tr": "Translates or deletes single characters. It only reads standard input, so give it a file with < or a pipe.",
    "tee": "Copies its input to the screen and to one or more files at the same time, like a T-junction in a pipe.",
    "diff": "Compares two files line by line and prints how to turn the first into the second. Lines marked < only exist in "
            "the first file, lines marked > only in the second.",
    "xargs": "Reads items from its input and runs a command with those items as arguments. It is the bridge between commands "
             "that print names (like find) and commands that expect names (like rm).",
    "tar": "Packs many files into one archive and unpacks them again. Combined with z it also compresses (.tar.gz). Pick one "
           "action letter: c to create, t to list, x to extract. The letter f must be followed by the archive name.",
    "ln": "Makes links. A symbolic link (-s) is a small file that points to another path, shown by ls -l as name -> target. "
          "Reading or writing the link reaches the target; removing the link leaves the target alone.",
    "ps": "Shows the processes that are running. Every process has a number (PID), an owner and a command line.",
    "kill": "Sends a signal to a process, identified by its PID. The default signal (TERM) asks it politely to stop and can be "
            "ignored. KILL (-9) cannot be ignored: the system removes the process at once, without letting it clean up.",
    "ssh": "Opens a secure connection to another machine. With a command it runs that command there and shows the result; "
           "without one you get a login shell on that machine, and exit brings you back.",
    "curl": "Sends a request to a URL and prints the answer. It is the standard tool to try web servers and APIs from a terminal.",
    "ping": "Sends small test packets to a host and tells you whether it answers and how fast. On Linux it never stops by itself: "
            "use -c to send a fixed number.",
    "df": "Shows how full each mounted disk is. The Use% column tells you which disk is about to run out of space.",
    "du": "Estimates how much disk space files and folders use. With -s you get one total per argument, which you can sort.",
    "date": "Prints the date and time, or formats them with a + format such as +%F for 2026-11-12.",
    "echo": "Prints its arguments. It is used to show variables, to write short files with a redirect, and to preview what a "
            "wildcard will expand to.",
    "printf": "Prints text with a format, like the C function. Unlike echo, it does not add a newline: write \\n yourself.",
    "test": "Checks a condition and sets the exit status: 0 for true, 1 for false. [ ... ] is the same command; the last "
            "argument must be ]. It is meant for if and while.",
    "top": "Shows the busiest processes, ordered by CPU use, with an overview of CPU and memory above them.",
    "ss": "Shows network sockets. With -tlnp you see which program listens on which TCP port.",
    "systemctl": "Controls services managed by systemd: show their state, start, stop or restart them. Services of your own "
                 "user need --user.",
    "journalctl": "Reads the logs that systemd collects from services. Use -u to pick one service and -n to limit the lines.",
    "pushd": "Like cd, but remembers the folder you left on a stack. popd returns to it and dirs shows the stack.",
}

EXAMPLES = {
    "ls": [("ls -l /etc", "details of the files in /etc"), ("ls -la ~", "everything in your home folder, hidden files too"),
           ("ls -lh", "sizes like 4.0K and 1.2M"), ("ls -lt", "newest first"), ("ls -R src", "src and everything below it")],
    "cd": [("cd /usr/share", "go to an absolute path"), ("cd ..", "one folder up"), ("cd -", "back to the previous folder"),
           ("cd", "home")],
    "cat": [("cat notes.txt", "show a file"), ("cat a.txt b.txt > both.txt", "join two files"),
            ("cat -n notes.txt", "with line numbers"), ("cat -A data.csv", "show hidden characters")],
    "head": [("head -n 3 server.log", "the first 3 lines"), ("head -c 100 notes.txt", "the first 100 bytes"),
             ("head -n -2 notes.txt", "everything except the last 2 lines")],
    "tail": [("tail -n 20 server.log", "the last 20 lines"), ("tail -n +2 data.csv", "everything from line 2 (skip a header)"),
             ("tail -f server.log", "follow the file as it grows (Ctrl+C to stop)")],
    "wc": [("wc -l notes.txt", "number of lines"), ("ls | wc -l", "how many files are here"), ("wc -w essay.txt", "number of words")],
    "cp": [("cp notes.txt notes.bak", "make a backup copy"), ("cp *.txt archive/", "copy many files into a folder"),
           ("cp -r project project2", "copy a whole folder")],
    "mv": [("mv draft.txt final.txt", "rename a file"), ("mv *.log old/", "move files into a folder")],
    "rm": [("rm notes.bak", "delete a file"), ("rm -r old_project", "delete a folder and everything in it"),
           ("echo *.tmp", "preview what rm *.tmp would delete")],
    "mkdir": [("mkdir work", "one folder"), ("mkdir -p work/2026/q4", "the whole path at once")],
    "touch": [("touch todo.txt", "create an empty file"), ("touch -c maybe.txt", "only update it if it exists")],
    "chmod": [("chmod 600 secret.txt", "only the owner can read and write"), ("chmod 755 run.sh", "everybody can run it, only the owner changes it"),
              ("chmod u+x run.sh", "add execute for the owner"), ("chmod g-w shared.txt", "remove write for the group"),
              ("chmod o-rwx private.txt", "others get nothing")],
    "find": [("find . -name '*.log'", "every .log file below here"), ("find /etc -type d", "only folders"),
             ("find . -size +1M", "files bigger than 1 MiB"), ("find . -name '*.bak' -exec rm {} \\;", "delete matches (look first without -exec!)"),
             ("find . -maxdepth 1 -type f", "files in this folder only")],
    "grep": [("grep error server.log", "lines containing error"), ("grep -i warn server.log", "ignore case"),
             ("grep -rn TODO src", "search a folder, with line numbers"), ("grep -v '^#' conf.txt", "lines that are not comments"),
             ("grep -c ok results.txt", "how many lines match"), ("grep -C2 fail server.log", "2 lines of context around each match")],
    "sort": [("sort names.txt", "alphabetical"), ("sort -n numbers.txt", "numeric"), ("sort -t, -k2 -n data.csv", "by the 2nd comma-separated column"),
             ("du -sh * | sort -h", "folders by size")],
    "uniq": [("sort names.txt | uniq", "remove duplicates"), ("sort names.txt | uniq -c | sort -rn", "count and rank")],
    "cut": [("cut -d: -f1 /etc/passwd", "the first colon-separated field"), ("cut -c1-8 notes.txt", "the first 8 characters of each line")],
    "sed": [("sed 's/cat/dog/' pets.txt", "replace the first cat of each line"), ("sed 's/cat/dog/g' pets.txt", "replace every cat"),
            ("sed -n '5,8p' notes.txt", "print only lines 5 to 8"), ("sed '/^#/d' conf.txt", "delete comment lines"),
            ("sed -i 's/8080/9090/' app.conf", "change the file in place")],
    "awk": [("awk '{print $2}' data.txt", "the second column"), ("awk -F: '{print $1}' /etc/passwd", "colon as separator"),
            ("awk '$3 > 10' data.txt", "lines whose third column is above 10"),
            ("awk '{s += $2} END {print s}' data.txt", "add up a column"),
            ("awk '{n[$1]++} END {for (k in n) print k, n[k]}' data.txt", "count by first column")],
    "tr": [("tr a-z A-Z < notes.txt", "to upper case"), ("tr -d ' ' < notes.txt", "delete the spaces"),
           ("tr -s ' ' < notes.txt", "squeeze repeated spaces")],
    "tee": [("ls | tee list.txt", "show the list and save it"), ("date | tee -a log.txt", "append instead of overwrite")],
    "diff": [("diff old.txt new.txt", "what changed"), ("diff -u old.txt new.txt", "in the format git uses")],
    "xargs": [("find . -name '*.bak' | xargs ls -l", "details of every file find lists"), ("ls *.txt | xargs wc -l", "count lines of every file"),
              ("echo a b c | xargs -n 1 echo", "one item per command")],
    "tar": [("tar -czf site.tar.gz site", "create a compressed archive"), ("tar -tzf site.tar.gz", "list what is inside"),
            ("tar -xzf site.tar.gz -C /tmp", "extract into /tmp"), ("tar -xzf site.tar.gz site/index.html", "extract one file")],
    "ln": [("ln -s /srv/app/v2 live", "live now points to v2"), ("ln -sfn /srv/app/v3 live", "move the link to v3"),
           ("readlink live", "where does it point?")],
    "ps": [("ps aux", "every process"), ("ps aux | grep nginx", "find one program"), ("ps -ef", "with the parent process (PPID)")],
    "kill": [("kill 4242", "ask process 4242 to stop"), ("kill -9 4242", "force it"), ("pgrep -l nginx", "find the PID by name first")],
    "ssh": [("ssh deploy@web01", "log in to web01"), ("ssh deploy@web01 'df -h'", "run one command there"),
            ("ssh web01 'ls /etc | wc -l'", "pipes inside the quotes run on the server")],
    "curl": [("curl http://api.local/status", "GET a URL"), ("curl -i http://api.local/status", "with the response headers"),
             ("curl -H 'Authorization: Bearer abc' http://api.local/me", "send a header"),
             ("curl -s -o /dev/null -w '%{http_code}\\n' http://api.local", "only the status code")],
    "ping": [("ping -c 3 gateway", "three packets, then stop"), ("ping -c 1 10.0.0.1", "one packet to an IP")],
    "df": [("df -h", "human-readable sizes")],
    "du": [("du -sh .", "total size of this folder"), ("du -s * | sort -n", "each item, smallest first")],
    "date": [("date +%F", "2026-11-12"), ("date +%H:%M", "hours and minutes"), ("date -u", "in UTC")],
    "echo": [("echo $HOME", "show a variable"), ("echo hello > hi.txt", "write a file"), ("echo more >> hi.txt", "append a line")],
    "printf": [("printf '%s has %d files\\n' docs 12", "format text and numbers"), ("printf '%05.1f\\n' 3.14159", "00003.1")],
    "test": [("[ -f notes.txt ] && echo found", "does the file exist?"), ("[ \"$a\" = \"$b\" ]", "are two texts equal?"),
             ("[ $n -gt 5 ]", "number comparison"), ("[ -d src ] || mkdir src", "create it if missing")],
    "top": [("top | head -n 12", "the top of the table")],
    "ss": [("ss -tlnp", "listening TCP ports and their programs"), ("ss -tlnp | grep 22", "who listens on port 22")],
    "systemctl": [("systemctl --user status myapp", "state and last log lines"), ("systemctl --user restart myapp", "restart it")],
    "journalctl": [("journalctl --user -u myapp -n 30", "the last 30 lines of one service"), ("journalctl -p err", "errors only")],
}

EXIT_STATUS = {
    "grep": "0 if a line was selected, 1 if none was, 2 if an error occurred.",
    "diff": "0 if the files are the same, 1 if they differ, 2 if there was trouble.",
    "test": "0 if the condition is true, 1 if it is false, 2 if the expression is wrong.",
    "ls": "0 if everything went well, 1 for minor problems, 2 for serious trouble such as a missing argument.",
    "find": "0 if everything went well, a value above 0 if an error occurred.",
    "ping": "0 if replies came back, 1 if no reply, 2 on an error such as an unknown host.",
    "curl": "0 on success; 6 could not resolve the host, 7 could not connect, 22 the server answered with an HTTP error (with -f).",
    "ssh": "The exit status of the remote command, or 255 if the connection itself failed.",
    "kill": "0 if the signal was sent, 1 if it failed (no such process, or not yours).",
}

SEE_ALSO = {
    "ls": "tree, find, stat, chmod", "cd": "pwd, pushd", "cat": "head, tail, less, tee", "head": "tail, cat, wc", "tail": "head, cat, journalctl",
    "wc": "grep, sort, uniq", "cp": "mv, rm, tar", "mv": "cp, rm", "rm": "rmdir, find", "mkdir": "rmdir, touch", "touch": "mkdir, cat",
    "chmod": "ls, stat, chown", "find": "grep, xargs, ls", "grep": "sed, awk, find, cut", "sort": "uniq, cut, wc", "uniq": "sort, wc",
    "cut": "awk, sort, tr", "sed": "awk, tr, grep", "awk": "sed, cut, sort", "tr": "sed, cut", "tee": "cat, echo", "diff": "cat, sort, git",
    "xargs": "find, grep", "tar": "cp, ls", "ln": "ls, readlink", "ps": "kill, top, pgrep, ss", "kill": "ps, pgrep, top", "ssh": "curl, ping, tar",
    "curl": "ping, ssh", "ping": "ssh, curl, ip", "df": "du, ls", "du": "df, ls, sort", "date": "echo", "echo": "printf, cat", "printf": "echo",
    "test": "if, while, find", "top": "ps, kill, free", "ss": "ps, curl, ping", "systemctl": "journalctl, ps", "journalctl": "systemctl, tail, grep",
}
