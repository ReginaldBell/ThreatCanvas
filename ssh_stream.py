import os, re, subprocess, threading, contextlib

SSH_RE   = re.compile(r'.*sshd(?:\[\d+\])?:\s*(?P<event>Failed|Accepted|Invalid user|Disconnected|authentication failure).*', re.I)
IP_RE    = re.compile(r'\bfrom\s+(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\b')
USER_RE  = re.compile(r'for(?:\s+invalid user)?\s+(?P<user>[\w.\-]+)')

def _parse(line: str):
    if not SSH_RE.search(line):
        return None
    parts = line.split()
    ts = " ".join(parts[:3]) if len(parts) >= 3 else None
    status = ("failed" if "Failed" in line else
              "accepted" if "Accepted" in line else
              "invalid" if "Invalid user" in line else
              "other")
    ip   = IP_RE.search(line).group("ip") if IP_RE.search(line) else None
    user = USER_RE.search(line).group("user") if USER_RE.search(line) else None
    return {"timestamp": ts, "user": user, "ip": ip, "status": status, "raw": line.rstrip()}

def start_ssh_stream(socketio, use_journalctl: bool = True, journal_unit: str = "ssh", tail_file: str = "/var/log/auth.log"):
    """
    Call ONCE from your existing app.py AFTER 'socketio = SocketIO(app, ...)'.
    Streams real sshd logs and emits 'ssh_event' dicts via Flask-SocketIO.
    """
    def _worker():
        cmd = (["journalctl","-u",journal_unit,"-f","-o","short","--no-pager"] if use_journalctl
               else ["tail","-F",tail_file])
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    continue
                evt = _parse(line)
                if evt:
                    try:
                        socketio.emit("ssh_event", evt)
                        print("[ssh_event]", evt)
                    except Exception:
                        pass
        finally:
            with contextlib.suppress(Exception):
                proc.terminate()

    threading.Thread(target=_worker, daemon=True).start()
