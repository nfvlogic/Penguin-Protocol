"""Network and system commands: ip hostname ping curl whoami id date uname which type sudo."""
import json
import re
from urllib.parse import parse_qs, urlsplit

from .core import HOST, MY_IP, NOW, ONLINE, TOKEN, USER, ShellError, c
from .manual import MAN, PRACTICE

PROJECTS = [{"id": "NPI-041", "name": "Carton redesign", "stage": "Gate 1", "status": "approved"},
            {"id": "NPI-042", "name": "New leaflet layout", "stage": "Gate 2", "status": "in review"},
            {"id": "NPI-043", "name": "Label update", "stage": "Request", "status": "draft"}]
INCIDENTS = [("INC-9001", "atlas-tst", "low", "closed"), ("INC-9002", "atlas-db-02", "critical", "closed"),
             ("INC-9003", "atlas-db-03", "critical", "open"), ("INC-9004", "atlas-prd", "medium", "open"),
             ("INC-9005", "atlas-db-01", "low", "open")]
USERS = [("ana", "admin"), ("ben", "viewer"), ("carla", "approver"), ("dan", "admin"),
         ("eva", "requestor"), ("felix", "viewer"), ("gina", "approver"), ("hugo", "admin"),
         ("iris", "requestor"), ("joan", "approver"), ("kai", "viewer"), ("lena", "admin-request")]


def compact(obj):
    return json.dumps(obj, separators=(",", ":"))


class NetworkCommands:
    def resolve(self, name):
        if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", name):
            return name
        for line in self.fs.d.get("/etc/hosts", "").splitlines():
            parts = line.split()
            if len(parts) >= 2 and not parts[0].startswith("#") and name in parts[1:]:
                return parts[0]
        return None

    def cmd_ip(self, args, stdin):
        args = [a for a in args if not a.startswith("-")]
        obj = args[0] if args else ""
        if obj in ("a", "addr", "address"):
            return ("1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000\n"
                    "    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00\n"
                    f"    inet {c('35', '127.0.0.1')}/8 scope host lo\n"
                    "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000\n"
                    "    link/ether 00:15:5d:3a:7c:21 brd ff:ff:ff:ff:ff:ff\n"
                    f"    inet {c('35', MY_IP)}/24 brd 10.20.30.255 scope global eth0")
        if obj in ("r", "route"):
            return (f"default via 10.20.30.1 dev eth0 proto dhcp src {MY_IP} metric 100\n"
                    f"10.20.30.0/24 dev eth0 proto kernel scope link src {MY_IP}")
        if not obj:
            raise ShellError("Usage: ip [ OPTIONS ] OBJECT { COMMAND | help }\n"
                             "where  OBJECT := { address | route | link | ... }", 255, tip="try: ip addr")
        raise ShellError(f'Object "{obj}" is unknown, try "ip help".', 1, tip="try: ip addr or ip route")

    def cmd_hostname(self, args, stdin):
        return MY_IP + " " if "-I" in args else self.hostname

    def cmd_ping(self, args, stdin):
        o, hosts = self.opts(args, "ping", "q4", with_value="cWi")
        if not hosts:
            raise ShellError("ping: usage error: Destination address required", 1, tip="example: ping -c 3 gateway")
        name = hosts[0]
        ip = self.resolve(name)
        if not ip:
            raise ShellError(f"ping: {name}: Name or service not known", 2,
                             tip="the names this computer knows are listed in /etc/hosts")
        count = int(o["c"]) if str(o.get("c", "")).isdigit() else 4
        label = f"{name} ({ip})" if name != ip else ip
        lines = [f"PING {name} ({ip}) 56(84) bytes of data."]
        if ip in ONLINE:
            times = [0.398 + (k * 7 % 5) / 100 for k in range(count)]
            lines += [f"64 bytes from {label}: icmp_seq={k + 1} ttl=64 time={t:.3f} ms" for k, t in enumerate(times)]
            lines += ["", f"--- {name} ping statistics ---",
                      f"{count} packets transmitted, {count} received, 0% packet loss, time {count * 1001 - 1000}ms",
                      f"rtt min/avg/max/mdev = {min(times):.3f}/{sum(times) / count:.3f}/{max(times):.3f}/0.015 ms"]
        else:
            lines += [f"From {MY_IP} icmp_seq={k + 1} Destination Host Unreachable" for k in range(count)]
            lines += ["", f"--- {name} ping statistics ---",
                      f"{count} packets transmitted, 0 received, +{count} errors, 100% packet loss, time {count * 1015}ms"]
            self._status = 1
        if "c" not in o:
            self.tip("real ping keeps going until you press Ctrl+C; -c N stops after N packets")
        return "\n".join(lines)

    def cmd_curl(self, args, stdin):
        headers, flags, urls, out_file, i, write_out = {}, set(), [], None, 0, None
        while i < len(args):
            a = args[i]
            if a in ("-H", "--header", "-X", "--request", "-d", "--data", "-o", "--output", "-w", "--write-out", "-u", "--user",
                     "-A", "--user-agent", "-m", "--max-time", "--connect-timeout", "-e", "--referer", "--data-raw"):
                if i + 1 >= len(args):
                    raise ShellError(f"curl: option {a}: requires parameter", 2)
                if a in ("-H", "--header"):
                    k, _, v = args[i + 1].partition(":")
                    headers[k.strip().lower()] = v.strip()
                elif a in ("-o", "--output"):
                    out_file = args[i + 1]
                elif a in ("-w", "--write-out"):
                    write_out = args[i + 1]
                i += 2
                continue
            if a.startswith("-") and len(a) > 1:
                flags.update(a[1:] if not a.startswith("--") else [a])
            else:
                urls.append(a)
            i += 1
        if not urls:
            raise ShellError("curl: no URL specified!\ncurl: try 'curl --help' for more information", 2,
                             tip="example: curl http://atlas-api/status")
        url = urls[0] if "://" in urls[0] else "http://" + urls[0]
        parts = urlsplit(url)
        host = parts.hostname or ""
        ip = self.resolve(host)
        if not ip:
            raise ShellError(f"curl: (6) Could not resolve host: {host}", 6,
                             tip="this machine only knows the hosts in /etc/hosts")
        port = 443 if parts.scheme == "https" else 80
        if ip != "10.20.30.20" or port == 443:
            raise ShellError(f"curl: (7) Failed to connect to {host} port {port} after 3 ms: Couldn't connect to server",
                             7, tip="the internal API is plain http (not https)" if ip == "10.20.30.20"
                             else "only atlas-api runs a web server in this network")
        status, body = self.api(parts.path.rstrip("/"), parse_qs(parts.query), headers)
        text = body if isinstance(body, str) else compact(body)
        code = status.split()[0]
        if ("f" in flags or "--fail" in flags) and int(code) >= 400:
            raise ShellError(f"curl: (22) The requested URL returned error: {code}", 22)
        size = len(text) + 1
        if out_file:
            p = self.open_redirect(">", out_file)
            self.append_file(p, text)
            text = ""
        head = f"HTTP/1.1 {status}\nServer: nginx/1.24.0\nContent-Type: application/json\nContent-Length: {size}\nConnection: keep-alive\n"
        if "I" in flags:                       # HEAD request: only the headers
            text = c("32" if code.startswith("2") else "33", head.split("\n")[0]) + "\n" + "\n".join(head.split("\n")[1:])
        elif "i" in flags:
            text = (c("32" if code.startswith("2") else "33", head.split("\n")[0]) + "\n" +
                    "\n".join(head.split("\n")[1:]) + "\n" + text)
        if "v" in flags:
            verbose = [f"*   Trying {ip}:80...", f"* Connected to {host} ({ip}) port 80", f"> GET {parts.path or '/'} HTTP/1.1",
                       f"> Host: {host}", "> User-Agent: curl/8.5.0", "> Accept: */*", ">"] + \
                      ["< " + l for l in head.split("\n") if l] + ["<"]
            if not self.pipe_out:
                for line in verbose:
                    print(c("90", line), flush=True)
        if write_out:
            fmt = (write_out.replace("%{http_code}", code).replace("%{size_download}", str(0 if out_file else size))
                   .replace("%{time_total}", "0.004112").replace("%{url_effective}", url).replace("\\n", "\n"))
            text = (text + "\n" if text else "") + fmt.rstrip("\n") if not out_file or out_file != "/dev/null" else fmt.rstrip("\n")
        return text

    def api(self, path, query, headers):
        """The simulated Atlas REST API. Returns (status line, body)."""
        authed = headers.get("authorization", "") == f"Bearer {TOKEN}"
        no_auth = ("401 Unauthorized", {"error": 'missing or invalid token. Send header "Authorization: Bearer <token>"'})
        if path == "/status":
            return "200 OK", {"service": "atlas-api", "status": "up", "version": "1.8.3"}
        if path == "/token":
            user = query.get("user", [""])[0]
            if not user:
                return "400 Bad Request", {"error": "missing user. Use /token?user=<your user name>"}
            if user != USER:
                return "403 Forbidden", {"error": "not your user. Run whoami"}
            return "200 OK", {"user": USER, "token": TOKEN}
        if path.startswith("/api/projects"):
            if not authed:
                return no_auth
            pid = path[len("/api/projects"):].strip("/")
            if not pid:
                return "200 OK", "\n".join(compact(p) for p in PROJECTS)
            found = [p for p in PROJECTS if p["id"] == pid]
            return ("200 OK", found[0]) if found else ("404 Not Found", {"error": f"project {pid} not found"})
        if path == "/api/incidents":
            if not authed:
                return no_auth
            return "200 OK", "\n".join(compact({"id": i, "host": h, "severity": s, "status": st})
                                       for i, h, s, st in INCIDENTS)
        if path == "/api/users":
            return "200 OK", "\n".join(compact({"id": k + 1, "name": n, "role": r}) for k, (n, r) in enumerate(USERS))
        return "404 Not Found", {"error": "not found"}

    # ---------------------------------------------------------- system
    def cmd_whoami(self, args, stdin):
        return USER

    def cmd_id(self, args, stdin):
        return f"uid=1000({USER}) gid=1000({USER}) groups=1000({USER}),100(users)"

    def cmd_date(self, args, stdin):
        return NOW

    def cmd_uname(self, args, stdin):
        if "-a" in args:
            return f"Linux {HOST} 6.8.0-corp #1 SMP PREEMPT_DYNAMIC Thu Oct 30 10:12:44 UTC 2026 x86_64 GNU/Linux"
        return "Linux"

    def cmd_which(self, args, stdin):
        out = []
        for a in args:
            if a in MAN and a not in PRACTICE and a not in ("cd", "export", "unset", "source", "history", "type", "exit", "alias",
                                                              "unalias", "read", "let", "break", "continue", "umask", "pushd",
                                                              "popd", "dirs", "[[", "help"):
                if a in ("pip", "flask") and not self.venv:
                    self._status = 1
                    continue
                out.append(f"{self.venv}/bin/{a}" if self.venv and a in ("python", "pip", "flask") else f"/usr/bin/{a}")
            else:
                self._status = 1
        return "\n".join(out)

    def cmd_type(self, args, stdin):
        from .shell import ALIASES, BUILTINS
        out = []
        for a in args:
            if a in ALIASES and a not in ("levels", "level", "logout", "pip3"):
                out.append(f"{a} is aliased to `{' '.join(ALIASES[a])}'")
            elif a in BUILTINS:
                out.append(f"{a} is a shell builtin")
            elif a in MAN and a not in PRACTICE:
                out.append(f"{a} is /usr/bin/{a}")
            elif a in PRACTICE:
                out.append(f"{a} is a practice-shell command (it does not exist on real Linux)")
            else:
                self.warn(f"bash: type: {a}: not found")
        return "\n".join(out)

    def cmd_sudo(self, args, stdin):
        raise ShellError(f"[sudo] password for {USER}: \n{USER} is not in the sudoers file.  This incident will be reported.",
                         1, tip="no ticket needs admin rights (and in real life sudo asks for your password)")

    def cmd_apt(self, args, stdin):
        raise ShellError("E: Could not open lock file /var/lib/dpkg/lock-frontend - open (13: Permission denied)\n"
                         "E: Unable to acquire the dpkg frontend lock (/var/lib/dpkg/lock-frontend), are you root?",
                         100, tip="installing system packages needs sudo; for Python packages use a venv and pip")

    cmd_apt_get = cmd_apt

    def cmd_nano(self, args, stdin):
        raise ShellError("nano: text editors are not available in this practice shell", 1,
                         tip='write files with echo "text" > file and add lines with >>')

    cmd_vim = cmd_vi = cmd_code = cmd_nano
