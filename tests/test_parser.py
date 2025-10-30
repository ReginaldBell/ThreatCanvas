import pytest
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from parser import LogParser

@pytest.fixture
def sample_log_file(tmp_path):
    log_content = """Oct 28 10:15:23 kali sshd[1234]: Failed password for invalid user admin from 192.168.1.100 port 54321 ssh2
Oct 28 10:16:45 kali sshd[1235]: Failed password for root from 45.155.204.23 port 12345 ssh2
Oct 28 10:17:12 kali sshd[1236]: Accepted password for user from 203.0.113.42 port 22334 ssh2
Oct 28 10:18:33 kali sshd[1237]: Failed password for invalid user test from 198.51.100.77 port 44556 ssh2
Oct 28 10:19:01 kali sshd[1238]: Failed password for root from 45.155.204.23 port 12346 ssh2
Oct 28 10:20:15 kali sshd[1239]: Invalid user hacker from 203.0.113.50 port 55123 ssh2
"""
    log_file = tmp_path / "test_auth.log"
    log_file.write_text(log_content)
    return log_file

def test_parse_failed_login(sample_log_file):
    parser = LogParser()
    parser.log_path = sample_log_file
    incidents = parser.parse_logs(event_types=['failed_login'])
    assert len(incidents) >= 3
    assert all(i['type'] == 'failed_login' for i in incidents)

def test_ip_aggregation(sample_log_file):
    parser = LogParser()
    parser.log_path = sample_log_file
    incidents = parser.parse_logs()
    aggregated = parser.aggregate_by_ip(incidents)
    repeated_ip = next((item for item in aggregated if item['ip'] == '45.155.204.23'), None)
    assert repeated_ip is not None
    assert repeated_ip['count'] == 2

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
