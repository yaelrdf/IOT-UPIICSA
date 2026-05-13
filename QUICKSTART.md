# Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Raspberry Pi (Zero 2 W recommended) or any Linux machine
- Python 3.7+
- Root/sudo access

### Installation

1. **Clone or download the project**
   ```bash
   cd ~/projects
   git clone <repository-url> IOT-UPIICSA
   cd IOT-UPIICSA
   ```

2. **Run setup script**
   ```bash
   sudo bash setup.sh
   ```

3. **Configure your network**
   ```bash
   nano config.yaml
   ```
   
   Key settings to update:
   - `network.interface`: Your Wi-Fi adapter (e.g., `wlan0`)
   - `network.gateway_ip`: Your router IP (run `ip route | grep default`)
   - `network.subnet`: Your network range (e.g., `192.168.1.0/24`)
   - `email.sender_email` and `email.sender_password`: (optional, for alerts)

4. **Test with demo data**
   ```bash
   sudo python3 monitor.py -d
   ```
   
   Open browser: `http://localhost:5000`

5. **Run as systemd service (optional)**
   ```bash
   sudo systemctl start iot-monitor
   sudo systemctl enable iot-monitor
   ```

## Manual Testing

Run without background service:
```bash
sudo python3 monitor.py
```

Run in passive mode (monitoring only, no blocking):
```bash
# Edit config.yaml and set:
# network:
#   mode: "passive"
sudo python3 monitor.py
```

Run without web server (terminal only):
```bash
sudo python3 monitor.py --no-web
```

## Accessing the Dashboard

After starting:
- Local: `http://localhost:5000`
- Remote: `http://<your-pi-ip>:5000`

Default features available:
- 📊 Dashboard with live stats
- 📱 Device list and management
- ⚠️ Security events log
- 🔍 Threat intelligence status
- 🔗 REST API

## Stopping the Service

```bash
# If running as service
sudo systemctl stop iot-monitor

# If running interactively
Press Ctrl+C
```

## Checking Logs

```bash
# If running as service
sudo journalctl -u iot-monitor -f

# Or check log file
tail -f data/monitor.log
```

## Common Issues

### No devices discovered
- Check interface name: `ip a`
- Verify gateway IP: `ip route | grep default`
- Try passive mode first: set `mode: "passive"` in config.yaml

### Permission denied
- Make sure you're using `sudo`: `sudo python3 monitor.py`
- Required for packet capture and ARP spoofing

### Email not sending
- Enable 2FA on Gmail
- Create App Password: https://myaccount.google.com/apppasswords
- Use the 16-character app password (not your regular password)

## Next Steps

1. Review the full [README.md](README.md) for detailed documentation
2. Customize threat alert thresholds in `config.yaml`
3. Add custom threat intelligence sources
4. Set up email notifications
5. Configure firewall rules if needed

## Performance Tips

- Increase `capture_interval_sec` to capture less frequently (reduces CPU)
- Reduce `capture_duration_sec` if CPU usage is high
- In passive mode, CPU usage is minimal (~5%)

## Get Help

1. Check the logs: `tail -f data/monitor.log`
2. Test API: `curl http://localhost:5000/api/health`
3. Try demo mode: `sudo python3 monitor.py -d`
4. Review detailed documentation in [README.md](README.md)

---

**That's it!** Your IoT monitor is now running. 🎉
