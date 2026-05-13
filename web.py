"""
Flask web application — provides REST API and HTML dashboard for the IoT monitor.
"""
import logging
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import load_config
from database import Database
from constants import EventType, Severity
from threat_intel import ThreatIntel

log = logging.getLogger(__name__)

app = Flask(__name__)
cfg = None
db = None
threat_intel = None


# ── initialization ────────────────────────────────────────────────────────

def init_web_app(config, database, intel=None):
    """Initialize Flask app with external config and database."""
    global cfg, db, threat_intel
    cfg = config
    db = database
    threat_intel = intel

    app.config["SECRET_KEY"] = cfg.web.secret_key
    app.config["JSON_SORT_KEYS"] = False
    log.info("Flask app initialized")


# ── authentication ─────────────────────────────────────────────────────────

def login_required(f):
    """Simple login decorator (optional auth)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, no auth. Could implement with session tokens if needed.
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def index():
    """Home dashboard."""
    stats = db.get_stats()
    devices = db.get_all_devices()
    recent_events = db.get_events(limit=10)
    unacked_count = db.count_unacknowledged()

    # Calculate summary
    critical_count = sum(1 for e in recent_events if e["severity"] == "critical")
    high_count = sum(1 for e in recent_events if e["severity"] == "high")

    return render_template(
        "dashboard_es.html",  # Spanish template
        stats=stats,
        devices=devices,
        recent_events=recent_events,
        unacked_count=unacked_count,
        critical_count=critical_count,
        high_count=high_count,
    )


@app.route("/devices")
@login_required
def devices_page():
    """Devices list page."""
    devices = db.get_all_devices()
    return render_template("devices_es.html", devices=devices)  # Spanish template


@app.route("/events")
@login_required
def events_page():
    """Events log page."""
    severity_filter = request.args.get("severity")
    device_filter = request.args.get("device")
    acked_filter = request.args.get("acked")  # "true", "false", or None

    query_kwargs = {"limit": 500}
    if severity_filter and severity_filter != "all":
        query_kwargs["severity"] = severity_filter
    if device_filter and device_filter != "all":
        try:
            query_kwargs["device_id"] = int(device_filter)
        except:
            pass
    if acked_filter == "false":
        query_kwargs["acknowledged"] = False
    elif acked_filter == "true":
        query_kwargs["acknowledged"] = True

    events = db.get_events(**query_kwargs)

    # Get list of devices for filter dropdown
    devices = db.get_all_devices()

    return render_template(
        "events_es.html",  # Spanish template
        events=events,
        devices=devices,
        severity_filter=severity_filter or "all",
        device_filter=device_filter or "all",
        acked_filter=acked_filter or "all",
    )


@app.route("/threat-intel")
@login_required
def threat_intel_page():
    """Threat intelligence status page."""
    intel_sources = db.get_intel_sources()
    intel_counts = db.count_intel_entries()
    
    # Create stats dictionary for template
    intel_stats = {
        "total_ips": intel_counts.get("total_ips", 0),
        "total_domains": intel_counts.get("total_domains", 0),
        "active_sources": len(intel_sources) if intel_sources else 0,
        "last_update": "Hace menos de 24 horas"  # Default
    }
    
    return render_template(
        "threat_intel_es.html",  # Spanish template
        sources=intel_sources,
        counts=intel_counts,
        intel_stats=intel_stats,
        intel_config={"active_sources": intel_stats["active_sources"]}
    )


# ── API endpoints ──────────────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    """Get current system statistics."""
    return jsonify(db.get_stats())


@app.route("/api/devices")
def api_devices():
    """Get all devices."""
    devices = db.get_all_devices()
    return jsonify(devices)


@app.route("/api/devices/<int:device_id>")
def api_device_detail(device_id):
    """Get device details including recent events and connections."""
    device = db.get_device(device_id=device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404

    events = db.get_events(device_id=device_id, limit=50)
    connections = db.get_connections(device_id=device_id, minutes=60, limit=100)

    return jsonify({
        "device": device,
        "events": events,
        "connections": connections,
    })


@app.route("/api/events")
def api_events():
    """Get events with optional filtering."""
    severity = request.args.get("severity")
    device_id = request.args.get("device_id")
    acknowledged = request.args.get("acknowledged")

    kwargs = {"limit": 500}
    if severity:
        kwargs["severity"] = severity
    if device_id:
        try:
            kwargs["device_id"] = int(device_id)
        except:
            pass
    if acknowledged is not None:
        kwargs["acknowledged"] = acknowledged.lower() == "true"

    events = db.get_events(**kwargs)
    return jsonify(events)


@app.route("/api/events/<int:event_id>/acknowledge", methods=["POST"])
def api_acknowledge_event(event_id):
    """Acknowledge an event."""
    try:
        db.acknowledge_event(event_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/devices/<int:device_id>/block", methods=["POST"])
def api_block_device(device_id):
    """Block a device."""
    try:
        device = db.get_device(device_id=device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404

        db.set_device_blocked(device_id, True)

        # Also add blocking event
        db.add_event(
            device["ip"],
            EventType.DEVICE_BLOCKED,
            f"Device blocked: {device['ip']} ({device.get('vendor','?')})",
            {"reason": "manual"},
            device_id=device_id,
        )

        return jsonify({"ok": True, "message": f"Device {device['ip']} blocked"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/devices/<int:device_id>/unblock", methods=["POST"])
def api_unblock_device(device_id):
    """Unblock a device."""
    try:
        device = db.get_device(device_id=device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404

        db.set_device_blocked(device_id, False)

        # Add unblocking event
        db.add_event(
            device["ip"],
            EventType.DEVICE_UNBLOCKED,
            f"Device unblocked: {device['ip']} ({device.get('vendor','?')})",
            {"reason": "manual"},
            device_id=device_id,
        )

        return jsonify({"ok": True, "message": f"Device {device['ip']} unblocked"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/devices/<int:device_id>/note", methods=["POST"])
def api_set_device_note(device_id):
    """Set a note on a device."""
    try:
        data = request.get_json() or {}
        note = data.get("note", "")

        conn = db._conn()
        conn.execute("UPDATE devices SET notes=? WHERE id=?", (note, device_id))
        conn.commit()

        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/connections")
def api_connections():
    """Get recent connections with optional filtering."""
    device_id = request.args.get("device_id")
    minutes = int(request.args.get("minutes", 30))
    limit = int(request.args.get("limit", 200))

    kwargs = {"minutes": minutes, "limit": limit}
    if device_id:
        try:
            kwargs["device_id"] = int(device_id)
        except:
            pass

    connections = db.get_connections(**kwargs)
    return jsonify(connections)


@app.route("/api/intel/sources")
def api_intel_sources():
    """Get threat intel source information."""
    sources = db.get_intel_sources()
    counts = db.count_intel_entries()
    return jsonify({"sources": sources, "counts": counts})


@app.route("/api/intel/refresh", methods=["POST"])
def api_intel_refresh():
    """Refresh threat intelligence from all sources."""
    try:
        # Try to use module-level threat_intel first, then fall back to app module
        intel = threat_intel
        if intel is None:
            try:
                import app as app_module
                intel = app_module.threat_intel
            except ImportError:
                pass
        
        if intel is None:
            return jsonify({
                "success": False,
                "error": "Módulo de inteligencia de amenazas no inicializado"
            }), 500
        
        intel.update_all()
        return jsonify({
            "success": True,
            "message": "Actualización iniciada - Fuentes de inteligencia actualizadas"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/health")
def api_health():
    """Health check endpoint."""
    try:
        stats = db.get_stats()
        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── error handlers ─────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    log.error("Internal server error: %s", error)
    return jsonify({"error": "Internal server error"}), 500


# ── template filters ──────────────────────────────────────────────────────

@app.template_filter("timeago")
def timeago_filter(iso_string):
    """Convert ISO datetime string to "X minutes ago" format."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        now = datetime.utcnow()
        delta = now - dt.replace(tzinfo=None)

        if delta.total_seconds() < 60:
            return "just now"
        elif delta.total_seconds() < 3600:
            mins = int(delta.total_seconds() / 60)
            return f"{mins}m ago"
        elif delta.total_seconds() < 86400:
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = int(delta.total_seconds() / 86400)
            return f"{days}d ago"
    except:
        return iso_string


@app.template_filter("severity_badge")
def severity_badge(severity):
    """Return Bootstrap class for severity level."""
    from constants import Severity
    color_map = {
        Severity.CRITICAL: "danger",
        Severity.HIGH: "warning",
        Severity.MEDIUM: "info",
        Severity.LOW: "secondary",
    }
    return color_map.get(severity, "secondary")


if __name__ == "__main__":
    # For testing only; normally run via the main app
    cfg = load_config("config.yaml")
    db = Database(cfg.database.path)
    init_web_app(cfg, db)
    app.run(host=cfg.web.host, port=cfg.web.port, debug=cfg.web.debug)
