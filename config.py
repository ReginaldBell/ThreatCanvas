import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Settings
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Log File Paths
    AUTH_LOG_PATH = os.getenv('AUTH_LOG_PATH', '/var/log/auth.log')
    FALLBACK_LOG_PATH = os.getenv('FALLBACK_LOG_PATH', './sample_auth.log')
    
    # Cache Settings
    CACHE_DIR = Path(os.getenv('CACHE_DIR', './cache'))
    IP_CACHE_FILE = CACHE_DIR / 'ip_cache.json'
    CACHE_EXPIRY_DAYS = int(os.getenv('CACHE_EXPIRY_DAYS', 30))
    
    # GeoIP Settings
    GEOIP_API_URL = os.getenv('GEOIP_API_URL', 'http://ip-api.com/json/')
    GEOIP_RATE_LIMIT = int(os.getenv('GEOIP_RATE_LIMIT', 45))
    GEOIP_BATCH_SIZE = int(os.getenv('GEOIP_BATCH_SIZE', 100))
    
    # API Settings
    MAX_INCIDENTS = int(os.getenv('MAX_INCIDENTS', 5000))
    DEFAULT_LIMIT = int(os.getenv('DEFAULT_LIMIT', 1000))
    
    @classmethod
    def init_app(cls):
        """Initialize application directories"""
        cls.CACHE_DIR.mkdir(exist_ok=True)
        
        if not Path(cls.AUTH_LOG_PATH).exists() and not Path(cls.FALLBACK_LOG_PATH).exists():
            print(f"⚠️  No log file found. Creating sample at {cls.FALLBACK_LOG_PATH}")
            cls._create_sample_log()
    
    @classmethod
    def _create_sample_log(cls):
        """Create a sample auth.log for testing"""
        sample = """Oct 28 10:15:23 kali sshd[1234]: Failed password for invalid user admin from 192.168.1.100 port 54321 ssh2
Oct 28 10:16:45 kali sshd[1235]: Failed password for root from 45.155.204.23 port 12345 ssh2
Oct 28 10:17:12 kali sshd[1236]: Accepted password for user from 203.0.113.42 port 22334 ssh2
Oct 28 10:18:33 kali sshd[1237]: Failed password for invalid user test from 198.51.100.77 port 44556 ssh2
Oct 28 10:19:01 kali sshd[1238]: Failed password for root from 45.155.204.23 port 12346 ssh2
Oct 28 10:20:15 kali sshd[1239]: Invalid user hacker from 203.0.113.50 port 55123 ssh2
Oct 28 10:21:30 kali sshd[1240]: Failed password for root from 198.51.100.88 port 33445 ssh2
Oct 28 10:22:45 kali sshd[1241]: POSSIBLE BREAK-IN ATTEMPT from 45.155.204.23 port 12347 ssh2"""
        
        with open(cls.FALLBACK_LOG_PATH, 'w') as f:
            f.write(sample)
