import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from config import Config

class LogParser:
    def __init__(self):
        self.log_path = self._get_log_path()
        
        self.patterns = {
            'failed_login': re.compile(
                r'(\w+\s+\d+\s+\d+:\d+:\d+).*sshd.*Failed password for .* from ([\d.]+)'
            ),
            'accepted_login': re.compile(
                r'(\w+\s+\d+\s+\d+:\d+:\d+).*sshd.*Accepted password for .* from ([\d.]+)'
            ),
            'invalid_user': re.compile(
                r'(\w+\s+\d+\s+\d+:\d+:\d+).*sshd.*Invalid user .* from ([\d.]+)'
            ),
            'break_in_attempt': re.compile(
                r'(\w+\s+\d+\s+\d+:\d+:\d+).*sshd.*POSSIBLE BREAK-IN ATTEMPT from ([\d.]+)'
            )
        }
    
    def _get_log_path(self) -> Path:
        """Determine which log file to use"""
        auth_log = Path(Config.AUTH_LOG_PATH)
        fallback = Path(Config.FALLBACK_LOG_PATH)
        
        if auth_log.exists():
            return auth_log
        elif fallback.exists():
            print(f"⚠️  Using fallback log: {fallback}")
            return fallback
        else:
            raise FileNotFoundError("No auth.log or sample log file found")
    
    def parse_logs(self, since: Optional[str] = None, event_types: Optional[List[str]] = None, 
                   search_ip: Optional[str] = None, limit: int = Config.DEFAULT_LIMIT) -> List[Dict]:
        """Parse auth.log with filtering"""
        cutoff_time = self._parse_time_filter(since) if since else None
        event_types = event_types or list(self.patterns.keys())
        
        incidents = []
        
        try:
            with open(self.log_path, 'r', errors='ignore') as f:
                for line in f:
                    if search_ip and search_ip not in line:
                        continue
                    
                    for event_type, pattern in self.patterns.items():
                        if event_type not in event_types:
                            continue
                        
                        match = pattern.search(line)
                        if match:
                            timestamp_str, ip = match.groups()
                            timestamp = self._parse_timestamp(timestamp_str)
                            
                            if cutoff_time and timestamp < cutoff_time:
                                continue
                            
                            incidents.append({
                                'ip': ip,
                                'timestamp': timestamp.isoformat(),
                                'type': event_type,
                                'raw_line': line.strip()
                            })
                            
                            if len(incidents) >= limit:
                                return incidents
                            break
        
        except FileNotFoundError:
            print(f"❌ Log file not found: {self.log_path}")
            return []
        except Exception as e:
            print(f"❌ Error parsing logs: {e}")
            return []
        
        return incidents
    
    def aggregate_by_ip(self, incidents: List[Dict]) -> List[Dict]:
        """Aggregate incidents by IP address"""
        ip_map = defaultdict(lambda: {
            'count': 0,
            'types': set(),
            'timestamps': [],
            'last_seen': None
        })
        
        for incident in incidents:
            ip = incident['ip']
            timestamp = incident['timestamp']
            event_type = incident['type']
            
            ip_map[ip]['count'] += 1
            ip_map[ip]['types'].add(event_type)
            ip_map[ip]['timestamps'].append(timestamp)
            
            if not ip_map[ip]['last_seen'] or timestamp > ip_map[ip]['last_seen']:
                ip_map[ip]['last_seen'] = timestamp
        
        aggregated = []
        for ip, data in ip_map.items():
            aggregated.append({
                'ip': ip,
                'count': data['count'],
                'types': sorted(list(data['types'])),
                'last_seen': data['last_seen'],
                'samples': sorted(data['timestamps'], reverse=True)[:5]
            })
        
        aggregated.sort(key=lambda x: x['count'], reverse=True)
        return aggregated
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse syslog timestamp"""
        try:
            current_year = datetime.now().year
            dt = datetime.strptime(f"{current_year} {timestamp_str}", "%Y %b %d %H:%M:%S")
            return dt
        except ValueError:
            return datetime.now()
    
    def _parse_time_filter(self, since: str) -> Optional[datetime]:
        """Convert time filter to datetime cutoff"""
        now = datetime.now()
        
        if since == '1h':
            return now - timedelta(hours=1)
        elif since == '24h':
            return now - timedelta(hours=24)
        elif since == '7d':
            return now - timedelta(days=7)
        elif since == '30d':
            return now - timedelta(days=30)
        else:
            return None
    
    def get_stats(self) -> Dict:
        """Get overall statistics"""
        incidents = self.parse_logs(limit=Config.MAX_INCIDENTS)
        aggregated = self.aggregate_by_ip(incidents)
        
        event_type_counts = defaultdict(int)
        
        for incident in incidents:
            event_type_counts[incident['type']] += 1
        
        return {
            'total_incidents': len(incidents),
            'unique_ips': len(aggregated),
            'event_types': dict(event_type_counts),
            'log_file': str(self.log_path)
        }
