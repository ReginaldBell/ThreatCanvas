# ThreatCanvas 🌍  
**Developer:** Reginald Bell  
**GitHub:** [@ReginaldBell](https://github.com/ReginaldBell)

> Real-time SSH attack visualization tool — parses system logs, geolocates IPs, and maps cyber activity live using Flask and Leaflet.js.

---

## 🚀 Overview  
**ThreatCanvas** is a lightweight cybersecurity visualization project that demonstrates log analysis, geolocation, and live attack mapping.  
It parses authentication logs (like `/var/log/auth.log`), identifies login attempts, and displays attacker IPs on an interactive world map.

---

## 🧠 Features  
✅ Parses SSH logs to extract IPs  
✅ Geolocates attacker IPs via `ip-api.com`  
✅ Displays interactive map with Leaflet.js  
✅ Real-time updates via Flask backend  
✅ Simple JSON API for automation and integration  

---

## 🛠️ Tech Stack  
- **Python 3** — Flask, Requests  
- **JavaScript** — Leaflet.js, Fetch API  
- **HTML/CSS** — clean static UI  
- **Ngrok** — public link tunneling  
- **Linux / Kali** — development environment  

---

## ⚙️ Installation  
Clone the project and set up the environment:

```bash
git clone https://github.com/ReginaldBell/ThreatCanvas.git
cd ThreatCanvas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py

