import time
import requests
from typing import Dict, List, Optional
from collections import deque
from config import Config
from cache_manager import CacheManager

class RateLimiter:
    """Token bucket rate limiter"""
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def can_proceed(self) -> bool:
        """Check if request is allowed"""
        now = time.time()
        
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        return len(self.requests) < self.max_requests
    
    def wait_time(self) -> float:
        """Calculate wait time until next request allowed"""
        if self.can_proceed():
            return 0
        
        now = time.time()
        oldest = self.requests[0]
        return max(0, (oldest + self.time_window) - now)
    
    def add_request(self):
        """Record a new request"""
        self.requests.append(time.time())


class GeoLocator:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.rate_limiter = RateLimiter(Config.GEOIP_RATE_LIMIT)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ThreatCanvas/2.0'})
    
    def geolocate_ip(self, ip: str) -> Optional[Dict]:
        """Geolocate single IP with caching"""
        cached = self.cache.get(ip)
        if cached:
            return cached
        
        wait = self.rate_limiter.wait_time()
        if wait > 0:
            print(f"⏳ Rate limit reached, waiting {wait:.1f}s...")
            time.sleep(wait)
        
        try:
            if not self.rate_limiter.can_proceed():
                print(f"⚠️  Rate limit exceeded for {ip}, skipping")
                return self._default_geo(ip)
            
            self.rate_limiter.add_request()
            
            response = self.session.get(
                f"{Config.GEOIP_API_URL}{ip}",
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                geo_data = {
                    'lat': data.get('lat', 0),
                    'lon': data.get('lon', 0),
                    'city': data.get('city', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'countryCode': data.get('countryCode', 'XX'),
                    'org': data.get('org', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'as': data.get('as', 'Unknown')
                }
                
                self.cache.set(ip, geo_data)
                return geo_data
            else:
                print(f"⚠️  GeoIP failed for {ip}: {data.get('message', 'Unknown error')}")
                return self._default_geo(ip)
        
        except requests.RequestException as e:
            print(f"❌ Network error for {ip}: {e}")
            return self._default_geo(ip)
        except Exception as e:
            print(f"❌ Unexpected error for {ip}: {e}")
            return self._default_geo(ip)
    
    def geolocate_batch(self, ips: List[str]) -> Dict[str, Dict]:
        """Geolocate multiple IPs efficiently"""
        results = {}
        uncached_ips = []
        
        for ip in ips:
            cached = self.cache.get(ip)
            if cached:
                results[ip] = cached
            else:
                uncached_ips.append(ip)
        
        print(f"📍 Geolocating {len(uncached_ips)} IPs (using cache for {len(results)})")
        
        for ip in uncached_ips:
            geo = self.geolocate_ip(ip)
            if geo:
                results[ip] = geo
        
        return results
    
    def _default_geo(self, ip: str) -> Dict:
        """Return default geolocation for failed lookups"""
        return {
            'lat': 0,
            'lon': 0,
            'city': 'Unknown',
            'country': 'Unknown',
            'countryCode': 'XX',
            'org': 'Unknown',
            'isp': 'Unknown',
            'as': 'Unknown'
        }
