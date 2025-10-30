import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict

class CacheManager:
    def __init__(self, cache_file: Path, expiry_days: int = 30):
        self.cache_file = cache_file
        self.expiry_seconds = expiry_days * 86400
        self._cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("⚠️  Cache file corrupted, creating new cache")
            return {}
    
    def _save_cache(self):
        """Persist cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except IOError as e:
            print(f"❌ Failed to save cache: {e}")
    
    def get(self, ip: str) -> Optional[Dict]:
        """Retrieve cached IP data if not expired"""
        if ip not in self._cache:
            return None
        
        entry = self._cache[ip]
        cached_time = entry.get('cached_at', 0)
        
        if time.time() - cached_time > self.expiry_seconds:
            del self._cache[ip]
            return None
        
        return entry.get('data')
    
    def set(self, ip: str, data: Dict):
        """Cache IP geolocation data"""
        self._cache[ip] = {
            'data': data,
            'cached_at': time.time()
        }
        self._save_cache()
    
    def set_batch(self, ip_data_dict: Dict[str, Dict]):
        """Cache multiple IPs at once"""
        current_time = time.time()
        for ip, data in ip_data_dict.items():
            self._cache[ip] = {
                'data': data,
                'cached_at': current_time
            }
        self._save_cache()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired = [
            ip for ip, entry in self._cache.items()
            if current_time - entry.get('cached_at', 0) > self.expiry_seconds
        ]
        
        for ip in expired:
            del self._cache[ip]
        
        if expired:
            self._save_cache()
            print(f"🧹 Cleaned up {len(expired)} expired cache entries")
    
    def stats(self) -> Dict:
        """Return cache statistics"""
        return {
            'total_entries': len(self._cache),
            'cache_file': str(self.cache_file),
            'size_bytes': self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }
