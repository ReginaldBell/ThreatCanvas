import re
from datetime import datetime

FAILED_RE = re.compile(r'(?P<ts>\w{3}\s+\d+\s[\d:]+).*Failed password.*from (?P<ip>\d+\.\d+\.\d+\.\d+)')
ACCEPT_RE = re.compile(r'(?P<ts>\w{3}\s+\d+\s[\d:]+).*Accepted password.*from (?P<ip>\d+\.\d+\.\d+\.\d+)')

def parse_authlog(path="data/sample_auth.log", year=None):
    events = []
    with open(path, "r", errors="ignore") as f:
        for line in f:
            m = FAILED_RE.search(line) or ACCEPT_RE.search(line)
            if not m:
                continue
            ts_raw, ip = m.group("ts"), m.group("ip")
            y = year or datetime.utcnow().year
            ts = datetime.strptime(f"{y} {ts_raw}", "%Y %b %d %H:%M:%S")
            evt_type = "failed_login" if "Failed password" in line else "login_success"
            events.append({"timestamp": ts.isoformat(), "ip": ip, "type": evt_type})
    return events

def aggregate(events, last_n=500):
    recent = sorted(events, key=lambda e: e["timestamp"], reverse=True)[:last_n]
    rollup = {}
    for e in recent:
        r = rollup.setdefault(e["ip"], {"ip": e["ip"], "count": 0, "types": set(), "last_seen": e["timestamp"]})
        r["count"] += 1
        r["types"].add(e["type"])
        if e["timestamp"] > r["last_seen"]:
            r["last_seen"] = e["timestamp"]
    for v in rollup.values():
        v["types"] = sorted(v["types"])
    return list(rollup.values())

