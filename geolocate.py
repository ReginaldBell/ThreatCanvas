import json, os, time, requests

CACHE_PATH = "data/geo_cache.json"
API_URL = "http://ip-api.com/json/"  # free; cache results to respect limits

def _load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def _save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f)

def geolocate(ip):
    cache = _load_cache()
    if ip in cache:
        return cache[ip]
    try:
        r = requests.get(API_URL + ip, timeout=5)
        data = r.json()
        if data.get("status") == "success":
            result = {
                "lat": data.get("lat"),
                "lon": data.get("lon"),
                "city": data.get("city"),
                "country": data.get("country"),
                "org": data.get("org"),
            }
        else:
            result = {"lat": None, "lon": None, "city": None, "country": None, "org": None}
    except Exception:
        result = {"lat": None, "lon": None, "city": None, "country": None, "org": None}
    cache[ip] = result
    _save_cache(cache)
    time.sleep(0.2)
    return result

