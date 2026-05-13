# Architecture & Design

## System Overview

The IoT Network Security Monitor follows a three-layer architecture:

```
┌─────────────────────────────────┐
│   Application Layer (Web UI)    │  Flask Dashboard, REST API
│   - Dashboard                   │  Device Management, Event Viewer
│   - API Endpoints               │  Real-time Status
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Processing Layer (Analysis)   │  Detection Engine, Database
│   - Analyzer                    │  Multiple Detection Rules
│   - Alerter                     │  Event Storage & Management
│   - Database                    │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Perception Layer (Sensing)    │  Network Discovery, Packet Capture
│   - Scanner                     │  ARP Spoofing, Traffic Analysis
│   - Packet Capture              │  Threat Intelligence
│   - ARP Spoofer                 │
│   - Threat Intel                │
└─────────────────────────────────┘
```

## Module Descriptions

### 1. Config (`config.py`)
**Purpose**: Load and parse YAML configuration

**Key Classes**:
- `NetworkConfig`: Network interface settings
- `ScanConfig`: Scan timing and target configuration
- `EmailConfig`: Email alert settings
- `ThresholdConfig`: Detection thresholds
- `Config`: Root configuration object

**Dataflow**: YAML → Config object → All other modules

### 2. Database (`database.py`)
**Purpose**: SQLite data persistence with thread-safe connections

**Tables**:
- `devices`: Connected devices and their metadata
- `events`: Detected anomalies and alerts
- `connections`: Network traffic metadata
- `threat_intel`: IP/domain blocklist cache
- `geo_cache`: Geolocation data cache

**Key Methods**:
- `upsert_device()`: Add/update device
- `add_event()`: Record detected event
- `add_connection()`: Store traffic metadata
- `get_events()`: Query events with filtering

**Thread Safety**: Uses thread-local connections (thread-safe for scheduler + Flask)

### 3. Scanner (`scanner.py`)
**Purpose**: Network device discovery and enumeration

**Key Methods**:
- `arp_scan()`: Broadcast ARP request, discover devices
- `resolve_hostname()`: Reverse DNS lookup
- `run_discovery()`: Periodic discovery task

**Detection**: 
- Sends ARP "Who has X.X.X.X?" broadcast
- Collects MAC addresses and vendor OUI
- Performs reverse-DNS lookup
- Triggers NEW_DEVICE event on first detection

**Frequency**: Configurable (default: every 5 minutes)

### 4. PacketCapture (`capture.py`)
**Purpose**: Sniff network traffic and extract metadata

**Key Methods**:
- `start()`: Begin sniffing in background thread
- `drain()`: Get captured packets and clear buffer
- `block_ip()`: Add IP to block list
- `sync_blocked_from_db()`: Load block list from database

**Metadata Extracted**:
- Source/destination IP
- Destination port
- Protocol (TCP/UDP/Other)
- Payload size
- Timestamp
- DNS queries (from UDP port 53)

**Important**: Never stores packet payload content (encrypted or otherwise)

**Modes**:
- **Passive**: Sniff only, log traffic
- **Active**: MITM with optional blocking (requires IP forwarding)

### 5. Analyzer (`analyzer.py`)
**Purpose**: Run detection rules against captured metadata

**Detection Rules**:

1. **IP Blacklist** (`_check_blacklist_ips`)
   - Check each destination IP against threat intel DB
   - Severity: CRITICAL
   
2. **Domain Blacklist** (`_check_blacklist_domains`)
   - Check DNS queries against threat intel DB
   - Severity: HIGH

3. **Beaconing** (`_check_beaconing`)
   - Identify regular outbound connections
   - Groups by (destination IP, port)
   - Calculates coefficient of variation (CV) of intervals
   - Alerts if CV < 0.20 (high regularity)
   - Severity: HIGH

4. **Geographic Anomaly** (`_check_geo_anomaly`)
   - Check destination country against alert list
   - Default alert countries: KP (North Korea), IR (Iran)
   - Severity: MEDIUM

5. **High Volume** (`_check_high_volume`)
   - Monitor total bytes sent per minute
   - Default threshold: 2 MB/min
   - Severity: MEDIUM

### 6. ThreatIntel (`threat_intel.py`)
**Purpose**: Manage threat intelligence data and geolocation

**Sources**:
- abuse.ch Feodo Tracker (C2 servers)
- URLhaus (Malware distribution)
- Emerging Threats (Botnet C2)
- Custom sources via config.yaml

**Key Methods**:
- `update_all()`: Download and cache all sources
- `check_ip()`: Look up IP in blacklist
- `check_domain()`: Look up domain in blacklist
- `geo_lookup()`: Geolocation via ip-api.com

**Caching**:
- IP/domain blacklists: Updated every 24 hours
- Geolocation: Cached for 24 hours
- Rate-limited: 45 requests/minute for ip-api.com

### 7. Alerter (`alerter.py`)
**Purpose**: Send notifications for high-severity events

**Methods**:
- `send_event_email()`: Send single-event alert
- `send_digest()`: Send batch alert

**Email Format**:
- HTML formatted with severity colors
- Includes event type, severity, device info, description
- Links to web dashboard for details

**Severity Threshold**: Configurable per severity level

### 8. ARPSpoofer (`spoofer.py`)
**Purpose**: MITM traffic capture via ARP poisoning

**Operation**:
1. Resolve gateway MAC via ARP
2. Enable IP forwarding: `echo 1 > /proc/sys/net/ipv4/ip_forward`
3. Continuously send forged ARP replies:
   - To target: "I am the gateway"
   - To gateway: "I am the target"
4. Traffic routes through our interface
5. On stop: Restore original ARP mappings

**Requirements**:
- Root privileges
- IP forwarding enabled
- Target must be in same subnet

### 9. Web Dashboard (`web.py`)
**Purpose**: Flask web server and REST API

**Routes**:
- `/`: Dashboard with stats
- `/devices`: Device list
- `/events`: Event log
- `/threat-intel`: Intelligence status
- `/api/*`: REST endpoints

**Features**:
- Real-time statistics
- Event filtering and searching
- Device blocking/unblocking
- Event acknowledgment
- Responsive Bootstrap UI

## Data Flow

### Network Discovery → Storage
```
Scanner.run_discovery()
    ↓
ARP scan discovers devices
    ↓
Vendor lookup via OUI
    ↓
Reverse DNS lookup
    ↓
Database.upsert_device()
    ↓
NEW_DEVICE event if first seen
```

### Traffic Capture → Analysis → Alerts
```
PacketCapture.start()
    ↓ (sniffer thread)
Extract metadata per packet
    ↓
Store in memory buffer
    ↓
PacketCapture.drain()
    ↓
save_packets_to_db()
    ↓
Analyzer.analyze(packets)
    ↓ (5 detection rules in parallel)
Generate events
    ↓
Alerter.send_event_email() if high severity
    ↓
Database stores all events
    ↓
Web UI displays in real-time
```

### Threat Intelligence Update
```
Scheduler triggers update_all()
    ↓
ThreatIntel downloads each source
    ↓
Parse IP/domain lists
    ↓
Database.bulk_upsert_intel()
    ↓
Cache in SQLite
    ↓
Immediately available for lookups
```

## Scheduling

The application uses APScheduler for background tasks:

**Task**: Device Discovery
- Frequency: Every 5 minutes (configurable)
- Function: `task_discover_devices()`
- Output: Populates devices table, triggers NEW_DEVICE events

**Task**: Traffic Capture
- Frequency: Every 10 minutes (configurable)
- Function: `task_capture_traffic()`
- Duration: 60 seconds per capture (configurable)
- Output: Populates connections table, generates events

**Task**: Threat Intel Update
- Frequency: Every 24 hours (configurable)
- Function: `task_update_threat_intel()`
- Output: Updates threat_intel and intel events tables

**Task**: Cleanup
- Frequency: Every hour
- Function: `task_cleanup()`
- Purpose: Maintenance tasks (future expansion)

## Security Considerations

### Metadata vs. Payload
- ✅ Captures: Source/dest IP, ports, protocols, sizes, timestamps
- ❌ Never captures: Encrypted content, passwords, keystrokes
- ✅ Privacy-preserving: No user data extraction

### Authentication
- Currently: No web authentication (local-only recommended)
- Future: Add OAuth/JWT for multi-user environments

### Encryption
- Database: Not encrypted (consider with production data)
- Connections: HTTP by default (use HTTPS reverse proxy)
- Email: SMTP SSL (configurable)

### Root Access
- Required for: Packet capture, ARP spoofing
- Risk: Only run on trusted systems
- Mitigation: Firewall restrict web dashboard, VPN access

## Performance Characteristics

### CPU Usage
- **Passive mode**: 5-15% (RPi Zero 2 W)
- **Active mode (MITM)**: 15-25% with blocking
- Scales with: Packet capture frequency, number of devices, number of rules

### Memory Usage
- **Base**: ~100-150 MB
- **With capture**: ~150-200 MB
- **Peak**: <300 MB

### Disk Usage
- **Database**: ~1-10 MB baseline
- **Logs**: ~50 KB per day
- **Growth**: ~10-50 MB per month

### Network Overhead
- **Intel updates**: <5 MB per update (daily)
- **API calls**: Negligible
- **Geo-lookups**: Rate-limited, ~100 bytes each

## Extensibility

### Adding New Detection Rules

1. Create method in `Analyzer` class:
```python
def _check_custom_rule(self, src_ip, device_id, packets) -> list:
    events = []
    # Detection logic
    return events
```

2. Call from `analyze()` method:
```python
events_created += self._check_custom_rule(src_ip, did, pkt_list)
```

3. Define event type in `constants.py`

### Adding Custom API Endpoints

```python
@app.route("/api/custom")
def api_custom():
    return jsonify({...})
```

### Adding Threat Intel Sources

Edit `config.yaml`:
```yaml
threat_intel:
  sources:
    - name: "custom_source"
      type: "ip"
      url: "https://..."
```

## Known Limitations

1. **Encrypted Content**: Cannot detect threats in encrypted traffic
2. **Subnet-bound**: Must be on same network to monitor
3. **No Defense**: Blocks traffic but doesn't prevent sophisticated attacks
4. **Rule-based**: No machine learning (prevents false positives but less adaptive)
5. **Single instance**: No distributed monitoring or failover
6. **Geolocation**: Depends on free ip-api.com (rate-limited, cached)

## Future Improvements

- [ ] Machine learning for anomaly detection
- [ ] HTTPS/TLS support with proper certificates
- [ ] Multi-user authentication and roles
- [ ] Database encryption at rest
- [ ] Distributed monitoring with multiple nodes
- [ ] DNS sinkholing capability
- [ ] Port scanning detection
- [ ] Network topology visualization
- [ ] Mobile app for alerts
- [ ] Integration with SIEM systems

---

For questions about the architecture, see [README.md](README.md) or review the source code comments.
