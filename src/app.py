"""
Main application orchestrator — coordinates all system components.
Manages the scheduler, database, packet capture, analysis, alerting, and web UI.

Run as: sudo python app.py (requires root for packet capture and ARP spoofing)
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

# Local imports
from src.config import load_config
from src.database import Database
from src.core import Scanner, PacketCapture, save_packets_to_db, Analyzer, ThreatIntel, Alerter, ARPSpoofer
from src.constants import EventType


# ── global state ───────────────────────────────────────────────────────────

cfg = None
db = None
scanner = None
packet_capture = None
analyzer = None
threat_intel = None
alerter = None
arp_spoofer = None
scheduler = None

log = logging.getLogger(__name__)


# ── setup ──────────────────────────────────────────────────────────────────

def init_logging():
    """Configure logging to file and console."""
    global cfg
    os.makedirs(os.path.dirname(cfg.logging.file), exist_ok=True)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, cfg.logging.level))
    console_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console.setFormatter(console_fmt)

    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        cfg.logging.file,
        maxBytes=cfg.logging.max_bytes,
        backupCount=cfg.logging.backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
    )
    file_handler.setFormatter(file_fmt)

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(file_handler)

    log.info("Logging initialized (file: %s)", cfg.logging.file)


def init_app():
    """Initialize all components."""
    global cfg, db, scanner, packet_capture, analyzer, threat_intel, alerter, arp_spoofer
    global scheduler

    log.info("=" * 70)
    log.info("IoT Network Security Monitor — Initialization")
    log.info("=" * 70)

    # Database
    db.init_schema()
    log.info("Database ready: %s", cfg.database.path)

    # Components
    scanner = Scanner(cfg, db)
    packet_capture = PacketCapture(cfg, db)
    threat_intel = ThreatIntel(cfg, db)
    analyzer = Analyzer(cfg, db, threat_intel)
    alerter = Alerter(cfg, db)

    # ARP Spoofer (only in active mode)
    if cfg.network.mode == "active":
        arp_spoofer = ARPSpoofer(cfg.network.interface, cfg.network.gateway_ip)

    # Scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()
    log.info("Scheduler started")

    log.info("All components initialized")


# ── scheduled tasks ───────────────────────────────────────────────────────

def task_discover_devices():
    """Periodic network discovery task."""
    try:
        log.info("→ Starting device discovery…")
        devices = scanner.run_discovery()
        log.info("  Found %d device(s)", len(devices))

        if cfg.network.mode == "active" and arp_spoofer:
            target_ips = scanner.get_target_ips()
            arp_spoofer.set_targets(target_ips)
            log.info("  Updated ARP spoof targets: %d device(s)", len(target_ips))
    except Exception as e:
        log.error("Device discovery failed: %s", e)


def task_capture_traffic():
    """Periodic traffic capture and analysis task."""
    try:
        log.info("→ Starting traffic capture session…")
        targets = scanner.get_target_ips()
        if not targets:
            log.info("  No targets to capture — skipping")
            return

        # Start capture
        packet_capture.start(duration=cfg.scan.capture_duration_sec)
        packet_capture.wait()
        packets = packet_capture.drain()
        log.info("  Captured %d packet(s)", len(packets))

        # Save to database
        save_packets_to_db(db, packets, threat_intel.geo_lookup)
        log.info("  Saved to database")

        # Analyze
        events = analyzer.analyze(packets)
        log.info("  Analysis complete: %d event(s) detected", len(events))

        # Alert on high-severity events
        for event in events:
            if alerter.should_alert(event.get("severity", "low")):
                e_dict = db.get_events(limit=1)[0] if events else {}
                device = db.get_device(ip=e_dict.get("device_ip")) if e_dict else None
                alerter.send_event_email(e_dict, device)
                log.info("  Alert sent for %s", event.get("type"))

    except Exception as e:
        log.error("Traffic capture task failed: %s", e)


def task_update_threat_intel():
    """Periodic threat intelligence update task."""
    try:
        log.info("→ Updating threat intelligence…")
        results = threat_intel.update_all()
        for source, count in results.items():
            status = f"{count} entries" if count >= 0 else "FAILED"
            log.info("  %s: %s", source, status)
    except Exception as e:
        log.error("Threat intel update failed: %s", e)


def task_cleanup():
    """Periodic cleanup task (purge old data, etc.)."""
    try:
        log.info("→ Running cleanup tasks…")
        # Could implement old data purge here
        log.info("  Cleanup complete")
    except Exception as e:
        log.error("Cleanup failed: %s", e)


# ── shutdown ───────────────────────────────────────────────────────────────

def shutdown():
    """Gracefully shut down all components."""
    global scheduler, packet_capture, arp_spoofer

    log.info("=" * 70)
    log.info("Shutting down…")
    log.info("=" * 70)

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        log.info("Scheduler stopped")

    if packet_capture:
        packet_capture.stop()
        log.info("Packet capture stopped")

    if arp_spoofer:
        arp_spoofer.stop()
        log.info("ARP spoofer stopped")

    log.info("System shutdown complete")


# ── main ───────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    global cfg, db

    # Load config
    cfg = load_config("config.yaml")
    db = Database(cfg.database.path)

    # Setup logging
    init_logging()
    log.info("Configuration loaded from config.yaml")

    # Init components
    init_app()

    # Schedule tasks
    log.info("Scheduling tasks…")
    scheduler.add_job(
        task_discover_devices,
        "interval",
        seconds=cfg.scan.discovery_interval_sec,
        id="discover_devices",
        name="Device Discovery"
    )
    scheduler.add_job(
        task_capture_traffic,
        "interval",
        seconds=cfg.scan.capture_interval_sec,
        id="capture_traffic",
        name="Traffic Capture & Analysis"
    )
    if cfg.threat_intel.auto_update:
        scheduler.add_job(
            task_update_threat_intel,
            "interval",
            seconds=cfg.threat_intel.update_interval_sec,
            id="update_intel",
            name="Threat Intel Update"
        )
    scheduler.add_job(
        task_cleanup,
        "interval",
        seconds=3600,  # Once per hour
        id="cleanup",
        name="Cleanup"
    )

    log.info("Scheduled jobs:")
    for job in scheduler.get_jobs():
        log.info("  - %s (%s)", job.name, job.trigger)

    # Start with an initial discovery
    log.info("Running initial device discovery…")
    task_discover_devices()

    log.info("=" * 70)
    log.info("System ready. Press Ctrl+C to stop.")
    log.info("Web dashboard: http://localhost:%d", cfg.web.port)
    log.info("=" * 70)

    # Keep the main thread alive
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Received interrupt signal")
        shutdown()
        sys.exit(0)
    except Exception as e:
        log.error("Unexpected error: %s", e)
        shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
