# server.py (Python 3.13-friendly, no eventlet)
import os
import re
import subprocess
from threading import Thread
from flask import Flask, render_template
from flask_socketio import SocketIO

# ---- Config (env overrides) -----------------------------------------------
USE_JOURNALCTL = os.getenv("USE_JOURNALCTL", "1") not in ("0", "false", "False")
JOURNAL_UNIT   = os.getenv("JOURNAL_UNIT", "ssh")          # sometimes "sshd"
TAIL_FILE      = os.getenv("TAIL_FILE", "/var/log/auth.log")
HOST           = os.getenv("HOST", "0.0.0.0")
PORT           = int(os.getenv("PORT", "5000"))

# ---- App -------------------------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---- Parsers ---------------------------------------------------------------
SSH_RE   = re.compile(r'.*sshd(?:\[\d+\])?:\s*(?P<event>Failed|Accepted|Disconnected|Invalid user|authentication failure).*', re.IGNORECASE)
IP_RE    = re.compile(r'\bfrom\s+(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\b')
USER_RE  = re.compile(r'for(?:\s+invalid user)?\s+(?P<user>[\w.\-]+)')
TS_FUNC  = lambda s: " ".join(s.split()[:3]) if len(s.split()) >= 3 else None

def parse_line(line: str):
    m = SSH_RE.search(line)
    if not m:
        return None
    data = {
        "raw": line.rstrip(),
        "event": m.group("event"),
        "timestamp": TS_FUNC(line),
    }
    ip = IP_RE.search(line)
    if ip:
        data["ip"] = ip.group("ip")
    u = USER_RE.search(line)
    if u:
        data["user"] = u.group("user")
    return data

# ---- Log streamer ----------------------------------------------------------
def stream_logs():
    """
    Streams ssh logs using journalctl -f (preferred) or tail -F auth.log.
    Emits parsed events to connected Socket.IO clients on 'ssh_event'.
    """
    if USE_JOURNALCTL:
        cmd = ["journalctl", "-u", JOURNAL_UNIT, "-f", "-o", "short", "--no-pager"]
    else:
        cmd = ["tail", "-F", TAIL_FILE]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        for raw in iter(proc.stdout.readline, ""):
            if not raw:
                continue
            parsed = parse_line(raw)
            if parsed:
                socketio.emit("ssh_event", parsed)
    finally:
        with contextlib.suppress(Exception):
            proc.terminate()

# ---- Routes ----------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect")
def on_connect():
    socketio.emit("status", {"msg": "connected"})

# ---- Main ------------------------------------------------------------------
if __name__ == "__main__":
    # start background reader
    t = Thread(target=stream_logs, daemon=True)
    t.start()
    # run (Werkzeug ok for dev; set allow_unsafe_werkzeug for Python 3.13)
    socketio.run(app, host=HOST, port=PORT, allow_unsafe_werkzeug=True)


# --- START: ssh_stream integration (auto) ---
try:
    if "socketio" in globals():
        from ssh_stream import start_ssh_stream
        # If your unit is "sshd" on your system, change journal_unit="sshd"
        start_ssh_stream(socketio, use_journalctl=True, journal_unit="sshd")
    else:
        pass
except Exception as _e:
    print("ssh_stream not started:", _e)
# --- END: ssh_stream integration ---

