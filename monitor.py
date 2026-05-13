#!/usr/bin/env python3
"""
IoT Network Security Monitor — Main Entry Point

Usage:
    sudo python3 monitor.py       # Run with default config
    sudo python3 monitor.py -d    # Run with demo data
    sudo python3 monitor.py -c custom.yaml  # Run with custom config

Requires root/sudo for:
    - Packet capture (raw sockets)
    - ARP spoofing (active mode)
    - IP forwarding control
"""
import argparse
import logging
import logging.handlers
import os
import sys
import threading
import time
from pathlib import Path

# Ensure we're running Python 3.7+
if sys.version_info < (3, 7):
    print("Error: Python 3.7+ is required", file=sys.stderr)
    sys.exit(1)

# Ensure we're in the right directory
SCRIPT_DIR = Path(__file__).parent
os.chdir(SCRIPT_DIR)

# Now import our modules
from config import load_config
from database import Database
import app as app_module
from web import init_web_app, app as flask_app

log = logging.getLogger(__name__)


def check_requirements():
    """Check if all required Python packages are installed."""
    required = {
        'scapy': 'Scapy',
        'flask': 'Flask',
        'apscheduler': 'APScheduler',
        'requests': 'Requests',
        'yaml': 'PyYAML',
    }

    missing = []
    for module, name in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(name)

    if missing:
        print(f"Error: Missing required packages: {', '.join(missing)}", file=sys.stderr)
        print(f"Install with: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)


def check_permissions():
    """Check if we're running as root (required for packet capture)."""
    if os.geteuid() != 0:
        print("Warning: This script should be run as root for packet capture and ARP spoofing.", file=sys.stderr)
        print("         Many features will not work correctly without root privileges.", file=sys.stderr)
        response = input("Continue anyway? [y/N]: ").lower().strip()
        if response != 'y':
            sys.exit(1)


def setup_logging(cfg):
    """Setup the root logger."""
    os.makedirs(os.path.dirname(cfg.logging.file), exist_ok=True)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, cfg.logging.level))
    console_fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s",
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
        "[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s"
    )
    file_handler.setFormatter(file_fmt)

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(file_handler)


def run_app_scheduler(cfg, db):
    """Run the main app scheduler in a background thread."""
    app_module.cfg = cfg
    app_module.db = db
    app_module.init_app()

    # Schedule tasks
    log.info("Scheduling monitoring tasks…")
    app_module.scheduler.add_job(
        app_module.task_discover_devices,
        "interval",
        seconds=cfg.scan.discovery_interval_sec,
        id="discover_devices",
        name="Device Discovery"
    )
    app_module.scheduler.add_job(
        app_module.task_capture_traffic,
        "interval",
        seconds=cfg.scan.capture_interval_sec,
        id="capture_traffic",
        name="Traffic Capture & Analysis"
    )
    if cfg.threat_intel.auto_update:
        app_module.scheduler.add_job(
            app_module.task_update_threat_intel,
            "interval",
            seconds=cfg.threat_intel.update_interval_sec,
            id="update_intel",
            name="Threat Intel Update"
        )
    app_module.scheduler.add_job(
        app_module.task_cleanup,
        "interval",
        seconds=3600,  # Once per hour
        id="cleanup",
        name="Cleanup"
    )

    log.info("Scheduled jobs:")
    for job in app_module.scheduler.get_jobs():
        log.info("  - %s (%s)", job.name, job.trigger)

    # Run initial discovery
    log.info("Running initial device discovery…")
    app_module.task_discover_devices()

    log.info("Monitoring system is ready")


def run_flask_app(cfg):
    """Run the Flask web server."""
    log.info("Starting web server on http://%s:%d", cfg.web.host, cfg.web.port)
    try:
        flask_app.run(
            host=cfg.web.host,
            port=cfg.web.port,
            debug=False,  # Always disable debug in production
            use_reloader=False,  # Don't reload in threading context
        )
    except Exception as e:
        log.error("Flask server error: %s", e)
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="IoT Network Security Monitor",
        epilog="Run with sudo for full functionality"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to config file (default: config.yaml)"
    )
    parser.add_argument(
        "-d", "--demo",
        action="store_true",
        help="Load demo data for testing"
    )
    parser.add_argument(
        "--no-web",
        action="store_true",
        help="Run without web server (monitoring only)"
    )
    args = parser.parse_args()

    # Check requirements
    check_requirements()

    # Check permissions
    check_permissions()

    # Load configuration
    try:
        cfg = load_config(args.config)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Setup logging
    setup_logging(cfg)
    log = logging.getLogger(__name__)

    log.info("=" * 70)
    log.info("IoT Network Security Monitor — Starting")
    log.info("=" * 70)
    log.info("Config: %s", args.config)
    log.info("Network: %s on %s (%s mode)", cfg.network.subnet, cfg.network.interface, cfg.network.mode)
    log.info("Database: %s", cfg.database.path)

    # Initialize database
    db = Database(cfg.database.path)
    db.init_schema()

    if args.demo:
        log.info("Loading demo data…")
        db.seed_demo_data()

    # Initialize web app with config and db
    init_web_app(cfg, db)

    # Start app scheduler in background
    scheduler_thread = threading.Thread(
        target=run_app_scheduler,
        args=(cfg, db),
        daemon=False,
        name="AppScheduler"
    )
    scheduler_thread.start()

    # Give scheduler time to start
    time.sleep(2)

    if args.no_web:
        log.info("Web server disabled. Monitoring will continue in background.")
        log.info("To view events, enable the web server or check the logs.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Received interrupt signal, shutting down…")
            app_module.shutdown()
            sys.exit(0)
    else:
        # Start Flask web server (this blocks)
        try:
            log.info("=" * 70)
            log.info("Web dashboard: http://%s:%d", cfg.web.host, cfg.web.port)
            log.info("Press Ctrl+C to stop both services")
            log.info("=" * 70)
            run_flask_app(cfg)
        except KeyboardInterrupt:
            log.info("Received interrupt signal, shutting down…")
            app_module.shutdown()
            sys.exit(0)
        except Exception as e:
            log.error("Fatal error: %s", e)
            app_module.shutdown()
            sys.exit(1)


if __name__ == "__main__":
    main()
