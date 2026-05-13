# IoT Network Security Monitor

A low-cost, Raspberry Pi-based network security monitoring system for detecting malicious and anomalous behavior on home IoT networks.

## Overview

This project implements a comprehensive security monitoring solution specifically designed for IoT devices on home networks. It combines multiple detection techniques to identify suspicious behavior without requiring modifications to the network infrastructure or access to encrypted traffic.

### Key Features

- **Device Discovery**: Automatically detects all devices on the network via ARP scanning
- **Packet Capture & Metadata Analysis**: Intercepts and analyzes network metadata (never payload content)
- **Blacklist Integration**: Checks connections against known malicious IP/domain lists from:
  - abuse.ch (Feodo Tracker, URLhaus)
  - Emerging Threats
  - Custom sources
- **Beaconing Detection**: Identifies regular outbound connections typical of botnet command & control
- **Geographic Anomaly Detection**: Flags connections to suspicious countries
- **High Volume Detection**: Alerts when devices send unusual amounts of data
- **Email Alerts**: Sends real-time notifications for high-severity events
- **Web Dashboard**: Interactive dashboard for monitoring, device management, and event review
- **Active Mode (Optional)**: ARP spoofing-based MITM to block traffic from compromised devices

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Raspberry Pi Zero 2 W                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Network Interface (Wi-Fi)                 │  │
│  │          (802.11 b/g/n - Promiscuous Mode)          │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Perception Layer (Network Sensing)          │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ • Scanner: ARP discovery + vendor lookup       │  │  │
│  │  │ • Capturer: Packet sniffing + metadata extract │  │  │
│  │  │ • Spoofer: ARP poisoning (active mode)         │  │  │
│  │  │ • Threat Intel: IP/domain blacklist manager    │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Processing Layer (Analysis & Decision)      │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ • Analyzer: Runs 5 detection rules in parallel │  │  │
│  │  │   - Blacklist (IP & Domain)                   │  │  │
│  │  │   - Beaconing pattern detection               │  │  │
│  │  │   - Geographic anomalies                      │  │  │
│  │  │   - High volume detection                     │  │  │
│  │  │ • Database: Event & connection storage        │  │  │
│  │  │ • Alerter: Email notifications                │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Application Layer (User Interaction)         │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ • Web Dashboard (Flask)                        │  │  │
│  │  │ • REST API                                     │  │  │
│  │  │ • Event Log Viewer                             │  │  │
│  │  │ • Device Management & Blocking                 │  │  │
│  │  │ • Threat Intelligence Status                   │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │     Persistent Storage (SQLite Database)            │  │
│  │  • Devices & Metadata                              │  │
│  │  • Events & Alerts                                 │  │
│  │  • Network Connections                             │  │
│  │  • Threat Intelligence Cache                       │  │
│  │  • Geolocation Cache                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Hardware Requirements

- **Raspberry Pi Zero 2 W** (recommended) or any Raspberry Pi with Wi-Fi
- **Wireless adapter** (if not built-in; Zero 2 W has built-in 802.11ac)
- **Power supply**: 5V 2.5A minimum
- **SD card**: 32GB (Class 10 recommended)

### Software Requirements

- Python 3.7+
- Raspbian OS (or Ubuntu Server for Raspberry Pi)
- Root/sudo access for packet capture and ARP spoofing

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd IOT-UPIICSA
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your network**
   ```bash
   # First, find your network interface and gateway:
   ip route | grep default
   ip a
   
   # Edit config.yaml with your network details:
   nano config.yaml
   ```

   Key configuration items:
   ```yaml
   network:
     interface: "wlan0"          # Your Wi-Fi adapter
     gateway_ip: "192.168.1.1"   # Your router IP
     subnet: "192.168.1.0/24"    # Your subnet
   
   email:
     enabled: true
     sender_email: "your-email@gmail.com"
     sender_password: "your_app_password"  # Google App Password
     recipient_email: "your-email@gmail.com"
   ```

4. **Run the monitor** (requires sudo)
   ```bash
   sudo python3 monitor.py
   ```

   Options:
   ```bash
   sudo python3 monitor.py -d          # Run with demo data
   sudo python3 monitor.py --no-web    # Monitoring only (no web UI)
   ```

5. **Access the dashboard**
   - Open browser: `http://your-pi-ip:5000`
   - View events, devices, and alerts
   - Manage blocked devices

## Configuration

### Network Settings

```yaml
network:
  interface: "wlan0"          # Interface to monitor
  mode: "passive"             # or "active" (MITM mode)
  gateway_ip: "192.168.1.1"   # Router IP
  subnet: "192.168.1.0/24"    # Network subnet
```

**Modes:**
- **Passive**: Monitor only (recommended for testing)
- **Active**: MITM with traffic blocking capability (requires root, IP forwarding)

### Scan Settings

```yaml
scan:
  discovery_interval_sec: 300      # How often to scan for devices
  capture_duration_sec: 60         # Seconds to capture per session
  capture_interval_sec: 600        # How often to capture traffic
  targets: "all"                   # or ["192.168.1.10", "192.168.1.20"]
```

### Alert Thresholds

```yaml
thresholds:
  beaconing_min_connections: 8      # Minimum connections to flag
  beaconing_max_cv: 0.20            # Max coefficient of variation (regularity)
  volume_alert_kb_per_min: 2048     # 2 MB/min threshold
  geo_alert_countries:              # Country codes to alert on
    - "KP"                          # North Korea
    - "IR"                          # Iran
```

### Email Configuration

To enable email alerts on Gmail:

1. Enable 2-factor authentication on your Google account
2. Create an App Password: https://myaccount.google.com/apppasswords
3. Set in config:
   ```yaml
   email:
     enabled: true
     sender_email: "your-email@gmail.com"
     sender_password: "16-character-app-password"  # NOT your Gmail password
   ```

## Usage

### Web Dashboard

- **Dashboard**: Real-time system status and recent alerts
- **Devices**: View all detected devices, history, and block/unblock
- **Events**: Full event log with filtering and search
- **Threat Intel**: Status of blocklists and data sources
- **API**: RESTful API for programmatic access

### Detection Methods

#### 1. Blacklist Matching
Checks all outbound IPs and DNS queries against known-bad lists from abuse.ch and Emerging Threats.

**Severity**: CRITICAL (IP), HIGH (Domain)

#### 2. Beaconing Detection
Identifies regular outbound connections that match botnet command & control patterns.

Algorithm:
- Groups packets by (destination IP, port)
- Calculates inter-connection intervals
- Computes coefficient of variation (CV)
- Flags if CV < 0.20 (high regularity)

**Severity**: HIGH

#### 3. Geographic Anomalies
Detects connections to countries on the alert list (default: KP, IR).

**Severity**: MEDIUM

#### 4. High Volume Detection
Alerts when a device sends more than the configured threshold per minute.

**Severity**: MEDIUM

#### 5. New Device
Alerts when a new device joins the network.

**Severity**: LOW

### REST API

**Get System Stats**
```bash
curl http://localhost:5000/api/stats
```

**List All Devices**
```bash
curl http://localhost:5000/api/devices
```

**Get Events**
```bash
curl "http://localhost:5000/api/events?severity=high"
curl "http://localhost:5000/api/events?device_id=1"
```

**Block a Device**
```bash
curl -X POST http://localhost:5000/api/devices/1/block
```

**Acknowledge an Event**
```bash
curl -X POST http://localhost:5000/api/events/42/acknowledge
```

## Project Structure

```
IOT-UPIICSA/
├── monitor.py           # Main entry point
├── app.py              # Orchestrator & scheduler
├── web.py              # Flask web server & API
├── config.py           # Configuration loader
├── config.yaml         # Configuration file (EDIT THIS)
├── constants.py        # Event types & severity mappings
├── database.py         # SQLite database layer
├── scanner.py          # Network discovery
├── capture.py          # Packet sniffing
├── analyzer.py         # Detection engine
├── threat_intel.py     # Blocklist & geo-lookup
├── alerter.py          # Email notifications
├── spoofer.py          # ARP spoofing (MITM)
├── templates/          # HTML templates
│   ├── dashboard.html
│   ├── devices.html
│   ├── events.html
│   └── threat_intel.html
├── requirements.txt    # Python dependencies
└── Readme.md          # This file
```

## Modules

### Scanner (`scanner.py`)
Discovers devices using ARP scanning and reverse-DNS lookup.

### PacketCapture (`capture.py`)
Sniffs the network interface and extracts metadata. Optionally forwards packets in MITM mode.

### Analyzer (`analyzer.py`)
Runs detection rules against captured metadata:
1. IP Blacklist Check
2. Domain Blacklist Check
3. Geographic Anomaly Detection
4. Beaconing Pattern Detection
5. High Volume Detection

### ThreatIntel (`threat_intel.py`)
Manages blocklists and geolocation data:
- Downloads IP/domain blocklists from multiple sources
- Caches results in SQLite
- Provides geo-lookup via ip-api.com

### Alerter (`alerter.py`)
Sends email notifications for high-severity events with HTML formatting.

### ARPSpoofer (`spoofer.py`)
Poisons ARP caches to intercept traffic (active mode only):
- Tells devices we're the gateway
- Tells gateway we're each device
- Enables traffic filtering and blocking

### Database (`database.py`)
SQLite persistent storage with thread-safe connections:
- Devices
- Events
- Network connections
- Threat intelligence cache
- Geolocation cache

## Performance

**Minimal Resource Usage:**
- **CPU**: ~5-15% average (Raspberry Pi Zero 2 W)
- **RAM**: ~150-200 MB running (512 MB available)
- **Disk**: ~10-50 MB per month of logs
- **Bandwidth**: <100 KB/min for blocklist updates

**Scalability:**
- Supports monitoring up to 50+ devices per Raspberry Pi
- Handles 500+ packet captures per minute
- Database auto-indexes for performance

## Troubleshooting

### "Permission denied" for packet capture
```bash
# Make sure you're running with sudo
sudo python3 monitor.py
```

### No devices discovered
- Check your network interface: `ip a`
- Verify gateway IP: `ip route | grep default`
- Verify subnet in config.yaml
- Try passive mode first

### Email not sending
- Enable 2FA on Gmail account
- Create App Password (not your regular password)
- Check SMTP settings in config.yaml
- Review logs: `tail data/monitor.log`

### High CPU usage
- Reduce `capture_duration_sec` in config.yaml
- Increase `capture_interval_sec` to capture less frequently
- Reduce number of `targets` to monitor

### Database locked
- Stop the monitor
- Check for stale processes: `ps aux | grep python`
- Remove lock file: `rm data/monitor.db-wal`
- Restart the monitor

## Security Considerations

1. **Root Access**: This tool requires root. Only run on trusted systems.
2. **HTTPS**: Add reverse proxy (nginx/Apache) for HTTPS on web dashboard.
3. **Authentication**: Implement basic auth or OAuth for production.
4. **Network**: Run on isolated network segment if possible.
5. **Firewall**: Restrict access to web dashboard (default port 5000).
6. **Logging**: Logs contain IP addresses and hostnames (privacy consideration).

## Privacy & Ethics

- **Metadata Only**: We never capture or store packet payloads
- **Local Processing**: All analysis happens locally (no cloud upload)
- **Consensual**: Only deploy in networks you own/manage
- **Transparent**: Inform household members about monitoring
- **Legitimate Purpose**: Monitor IoT security, not surveillance

## Limitations

- Cannot detect encrypted threats (TLS/SSL content)
- Requires monitoring interface on same network
- Cannot detect attacks on the monitor itself
- Blocklists may have false positives
- No machine learning (rule-based only)
- Passive mode doesn't block traffic (view-only)

## Future Enhancements

- [ ] Machine learning for anomaly detection
- [ ] HTTPS support with self-signed certificates
- [ ] Multi-user authentication & role-based access
- [ ] Historical graph generation
- [ ] Mobile app
- [ ] Slack/Discord integration
- [ ] Automated threat response (auto-blocking)
- [ ] DNS sinkhole capability
- [ ] Port scanning detection
- [ ] Network topology visualization

## Contributing

Contributions welcome! Areas for improvement:
- Additional threat intel sources
- Performance optimizations
- Web UI improvements
- Additional detection methods
- Better documentation

## License

See LICENSE file.

## References

### Technical Papers
- Feodo Tracker (abuse.ch) - C2 detection
- URLhaus - Malware distribution network detection
- Emerging Threats - Open source IDS rules
- IP-API - Geolocation data

### Tools & Libraries
- **Scapy** - Packet manipulation
- **Flask** - Web framework
- **APScheduler** - Task scheduling
- **SQLite** - Database
- **PyYAML** - Configuration

## Authors

- Yael Saldaña Flores
- Emanuel Giovani Luna Ramos

**Course**: Internet of Things (IoT)  
**Institution**: UPIICSA (Unidad Profesional Interdisciplinaria de Ingeniería y Ciencias Sociales y Administrativas)  
**Semester**: 2026-2

## Support

For issues, questions, or suggestions:
1. Check the Troubleshooting section
2. Review logs: `tail -f data/monitor.log`
3. Run with demo data: `sudo python3 monitor.py -d`
4. Test API endpoints: `curl http://localhost:5000/api/health`

---

**Last Updated**: May 2026  
**Status**: Production Ready
