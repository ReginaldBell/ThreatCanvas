import threading
import subprocess
import re
from datetime import datetime
from typing import Optional, Tuple

def start_ssh_stream(socketio, use_journalctl=True, journal_units=("sshd", "sshd-session"), tail_file=None):
    """
    Start background thread to stream SSH events in real-time
    
    Args:
        socketio: Flask-SocketIO instance
        use_journalctl: Use systemd journal (True) or tail file (False)
        journal_units: Tuple of systemd units to monitor
        tail_file: Path to log file if not using journalctl
    """
    
    def stream_worker():
        print("🔴 Starting real-time SSH stream...")
        
        if use_journalctl:
            _stream_from_journalctl(socketio, journal_units)
        elif tail_file:
            _stream_from_file(socketio, tail_file)
        else:
            print("❌ No stream source configured")
    
    thread = threading.Thread(target=stream_worker, daemon=True)
    thread.start()
    print("✅ SSH stream thread started")


def _stream_from_journalctl(socketio, units):
    """Stream from systemd journal"""
    
    # Build command for multiple units
    unit_args = []
    for unit in units:
        unit_args.extend(['-u', unit])
    
    cmd = ['journalctl', '-f', '-n', '0'] + unit_args
    
    print(f"📡 Monitoring systemd units: {', '.join(units)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                event = _parse_ssh_line(line.strip())
                if event:
                    print(f"🔵 New SSH event: {event['ip']} - {event['type']}")
                    socketio.emit('new_ssh_event', event)
        
    except PermissionError:
        print("❌ Permission denied: Run as root or add user to systemd-journal group")
    except FileNotFoundError:
        print("❌ journalctl not found: Install systemd or use file mode")
    except Exception as e:
        print(f"❌ Stream error: {e}")


def _stream_from_file(socketio, filepath):
    """Stream from log file using tail -f"""
    
    print(f"📡 Monitoring file: {filepath}")
    
    try:
        process = subprocess.Popen(
            ['tail', '-f', '-n', '0', filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            if line:
                event = _parse_ssh_line(line.strip())
                if event:
                    print(f"🔵 New SSH event: {event['ip']} - {event['type']}")
                    socketio.emit('new_ssh_event', event)
        
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
    except Exception as e:
        print(f"❌ Stream error: {e}")


def _parse_ssh_line(line: str) -> Optional[dict]:
    """
    Parse SSH log line and extract event details
    
    Returns dict with: ip, type, timestamp, username, port
    """
    
    patterns = {
        'failed_login': re.compile(
            r'Failed password for (?:invalid user )?(\w+) from ([\d.]+) port (\d+)'
        ),
        'accepted_login': re.compile(
            r'Accepted password for (\w+) from ([\d.]+) port (\d+)'
        ),
        'invalid_user': re.compile(
            r'Invalid user (\w+) from ([\d.]+) port (\d+)'
        ),
        'break_in_attempt': re.compile(
            r'POSSIBLE BREAK-IN ATTEMPT.*from ([\d.]+)'
        ),
        'connection_closed': re.compile(
            r'Connection closed by ([\d.]+) port (\d+)'
        ),
        'disconnected': re.compile(
            r'Disconnected from (?:invalid user )?(?:\w+ )?(?:authenticating user )?(?:\w+ )?([\d.]+) port (\d+)'
        )
    }
    
    for event_type, pattern in patterns.items():
        match = pattern.search(line)
        if match:
            groups = match.groups()
            
            # Extract IP (always present)
            if event_type == 'break_in_attempt':
                ip = groups[0]
                username = 'unknown'
                port = 'unknown'
            else:
                # Most patterns: (username, ip, port)
                if len(groups) >= 2:
                    username = groups[0] if len(groups) >= 3 else 'unknown'
                    ip = groups[1] if len(groups) >= 3 else groups[0]
                    port = groups[2] if len(groups) >= 3 else groups[1] if len(groups) >= 2 else 'unknown'
                else:
                    ip = groups[0]
                    username = 'unknown'
                    port = 'unknown'
            
            return {
                'ip': ip,
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'port': port,
                'raw_line': line
            }
    
    return None
