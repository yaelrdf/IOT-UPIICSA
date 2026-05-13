# Development Guide

## Setting Up Development Environment

### Prerequisites
- Python 3.7+
- Git
- pip (Python package manager)
- Virtual environment tool (venv)

### Clone and Setup

```bash
git clone <repository-url>
cd IOT-UPIICSA

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install dev dependencies
pip install pytest black flake8
```

## Project Structure

```
IOT-UPIICSA/
├── *.py              # Core modules
├── monitor.py        # Main entry point
├── app.py            # Orchestrator & scheduler
├── web.py            # Flask web server
├── config.yaml       # Configuration file
├── requirements.txt  # Dependencies
│
├── templates/        # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── devices.html
│   ├── events.html
│   └── threat_intel.html
│
├── data/             # Runtime data (git-ignored)
│   ├── monitor.db    # SQLite database
│   └── monitor.log   # Application log
│
├── tests/            # Unit tests (future)
├── docs/             # Documentation
│   ├── README.md
│   ├── ARCHITECTURE.md
│   └── DEVELOPMENT.md
│
└── setup.sh          # Installation script
```

## Code Style

We follow PEP 8 with these conventions:

### Formatting
```python
# Use type hints where helpful
def check_ip(self, ip: str) -> Optional[Dict]:
    """Docstring with parameters and return type."""
    pass

# Import order: stdlib, third-party, local
import logging
import json
from typing import List, Dict

import requests
from scapy.all import ARP

from database import Database
```

### Naming
- Classes: `PascalCase` (e.g., `PacketCapture`)
- Methods/functions: `snake_case` (e.g., `run_discovery`)
- Constants: `UPPER_CASE` (e.g., `PRIVATE_RANGES`)
- Private: Prefix with `_` (e.g., `_extract_metadata`)

### Comments
```python
# Clear comment for complex logic
if cv <= max_cv:  # Coefficient of variation indicates beaconing
    # Detect beaconing pattern
    pass
```

### Max Line Length
- 88 characters for most code
- 100 characters acceptable for strings/URLs
- Break long lines at logical points

## Running the Application

### Development Mode

```bash
# Test with demo data
sudo python3 monitor.py -d

# With specific config
sudo python3 monitor.py -c config.test.yaml

# Without web server (scheduler only)
sudo python3 monitor.py --no-web
```

### Testing

```bash
# Run syntax check
python3 -m py_compile *.py

# Run pylint (if installed)
pylint *.py --disable=all --enable=E

# Run unit tests (when available)
python3 -m pytest tests/
```

## Database Schema

### devices
```sql
CREATE TABLE devices (
    id          INTEGER PRIMARY KEY,
    ip          TEXT UNIQUE NOT NULL,
    mac         TEXT,
    vendor      TEXT,
    hostname    TEXT,
    is_blocked  INTEGER DEFAULT 0,
    notes       TEXT,
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL
);
```

### events
```sql
CREATE TABLE events (
    id          INTEGER PRIMARY KEY,
    device_id   INTEGER,
    device_ip   TEXT,
    event_type  TEXT NOT NULL,
    severity    TEXT NOT NULL,
    description TEXT,
    details     TEXT,  -- JSON
    acknowledged INTEGER DEFAULT 0,
    timestamp   TEXT NOT NULL
);
```

### connections
```sql
CREATE TABLE connections (
    id          INTEGER PRIMARY KEY,
    device_id   INTEGER,
    src_ip      TEXT,
    dst_ip      TEXT,
    dst_port    INTEGER,
    protocol    TEXT,
    bytes       INTEGER DEFAULT 0,
    country     TEXT,
    country_code TEXT,
    isp         TEXT,
    dns_query   TEXT,
    timestamp   TEXT NOT NULL
);
```

## Adding a New Detection Rule

### Step 1: Define Event Type
Edit `constants.py`:
```python
class EventType:
    MY_NEW_RULE = "my_new_rule"
    
    LABELS = {
        MY_NEW_RULE: "My New Rule Detection",
    }

EVENT_SEVERITY = {
    EventType.MY_NEW_RULE: Severity.HIGH,
}
```

### Step 2: Implement Detection Logic
Edit `analyzer.py`:
```python
def _check_my_rule(self, src_ip, device_id, packets) -> list:
    """Check for my new detection rule."""
    events = []
    
    # Your detection logic here
    for pkt in packets:
        if suspicious_condition(pkt):
            desc = f"Suspicious: {pkt['dst_ip']}"
            eid = self.db.add_event(
                src_ip, EventType.MY_NEW_RULE, desc,
                {"dst_ip": pkt["dst_ip"]},
                device_id=device_id,
            )
            events.append({"id": eid, "type": EventType.MY_NEW_RULE})
    
    return events
```

### Step 3: Call from analyze()
```python
def analyze(self, packets: List[Dict]) -> List[Dict]:
    events_created = []
    # ... existing checks ...
    events_created += self._check_my_rule(src_ip, did, pkt_list)
    return events_created
```

## Adding a Custom API Endpoint

Edit `web.py`:
```python
@app.route("/api/custom/<int:device_id>")
def api_custom_endpoint(device_id):
    """Get custom data for a device."""
    device = db.get_device(device_id=device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404
    
    # Get custom data
    custom_data = {...}
    
    return jsonify(custom_data)
```

## Debugging

### Check Logs
```bash
# Tail log file
tail -f data/monitor.log

# Search for specific event
grep BLACKLIST data/monitor.log

# Show last 100 events
tail -100 data/monitor.log
```

### Database Inspection
```bash
sqlite3 data/monitor.db

# List all tables
.tables

# Show devices
SELECT ip, vendor, is_blocked FROM devices;

# Show recent events
SELECT timestamp, device_ip, event_type, severity FROM events ORDER BY timestamp DESC LIMIT 10;

# Exit
.quit
```

### Test API Endpoints
```bash
# Get stats
curl http://localhost:5000/api/stats | jq .

# List devices
curl http://localhost:5000/api/devices | jq .

# Get events
curl "http://localhost:5000/api/events?severity=high" | jq .

# Health check
curl http://localhost:5000/api/health | jq .
```

## Performance Optimization

### Reducing CPU Usage
1. Increase `capture_interval_sec` in config.yaml
2. Decrease `capture_duration_sec`
3. Reduce number of `targets` to monitor
4. Increase `discovery_interval_sec`

### Reducing Memory Usage
1. Lower `limit` in database queries
2. Archive old events periodically
3. Clear geo cache: `DELETE FROM geo_cache;`

### Improving Database Performance
1. Rebuild indices: `REINDEX;`
2. Optimize: `VACUUM;`
3. Check fragmentation: `PRAGMA freelist_count;`

## Contributing

### Before Submitting Code
1. Follow code style guidelines
2. Test on actual hardware
3. Add comments for complex logic
4. Update documentation if needed
5. Test with demo data: `sudo python3 monitor.py -d`

### Common Development Tasks

**Add new config option:**
1. Add field to appropriate `@dataclass` in `config.py`
2. Update `load_config()` function
3. Update `config.yaml` template
4. Update `QUICKSTART.md`

**Add new threat intel source:**
1. Add to `config.yaml` sources list
2. Source must be text file (one entry per line)
3. Support formats: IP addresses, domains, hosts file

**Fix a bug:**
1. Create test case that reproduces bug
2. Fix the code
3. Verify test passes
4. Test on actual hardware if possible

## Testing Checklist

Before release:
- [ ] Syntax check: `python3 -m py_compile *.py`
- [ ] Demo mode: `sudo python3 monitor.py -d`
- [ ] Web dashboard loads without errors
- [ ] All API endpoints return valid JSON
- [ ] Device discovery works
- [ ] Events are created and stored
- [ ] Email alerts work (if enabled)
- [ ] Device blocking/unblocking works
- [ ] Log file is created and written to
- [ ] No crashes on Ctrl+C

## Troubleshooting Development

### Module Not Found
```python
# Add to Python path
import sys
sys.path.insert(0, '/home/user/IOT-UPIICSA')

# Or run from correct directory
cd /home/user/IOT-UPIICSA
python3 monitor.py
```

### Database Locked
```bash
# Database WAL file issue
rm data/monitor.db-wal data/monitor.db-shm
```

### Permission Denied
```bash
# Must run as sudo for packet capture
sudo python3 monitor.py
```

### Port Already in Use
```bash
# Change port in config.yaml
web:
  port: 5001
```

## Performance Benchmarks

Target metrics (Raspberry Pi Zero 2 W):
- Device discovery: <5 seconds for 20 devices
- Packet capture: <100 MB/min memory peak
- Analysis: <1 second for 1000 packets
- Email send: <5 seconds per alert
- Web dashboard load: <1 second

## Future Development Ideas

1. **Machine Learning**: Detect anomalies statistically
2. **DNS Sinkhole**: Redirect malicious domains locally
3. **Port Scanning**: Detect port scans from/to devices
4. **Protocol Analysis**: Identify suspicious protocol usage
5. **Automation**: Auto-block based on threat level
6. **Mobile UI**: Responsive dashboard for phones
7. **Multi-device**: Centralized monitoring across network
8. **Notifications**: Slack, Discord, webhook integrations
9. **Reports**: Scheduled PDF reports
10. **Dashboard**: Historical graphs and trends

## Questions?

- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Review [README.md](README.md) for user-facing documentation
- Check source code comments for implementation details

Happy developing! 🚀
