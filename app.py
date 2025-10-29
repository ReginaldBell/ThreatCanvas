from flask import Flask, jsonify, send_from_directory
from parser import parse_authlog, aggregate
from geolocate import geolocate

app = Flask(__name__, static_folder="static")
DATA_PATH = "data/sample_auth.log"

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/incidents")
def incidents():
    events = parse_authlog(DATA_PATH)
    rolled = aggregate(events)
    payload = []
    for r in rolled:
        geo = geolocate(r["ip"])
        if geo["lat"] and geo["lon"]:
            payload.append({
                "ip": r["ip"],
                "count": r["count"],
                "types": r["types"],
                "last_seen": r["last_seen"],
                "lat": geo["lat"], "lon": geo["lon"],
                "city": geo["city"], "country": geo["country"],
                "org": geo["org"],
            })
    payload.sort(key=lambda x: x["count"], reverse=True)
    return jsonify(payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

