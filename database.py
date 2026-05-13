"""
Database layer — all SQLite interactions live here.
Uses thread-local connections so the scheduler and Flask can share the DB safely.
"""
import sqlite3
import threading
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from constants import EventType, Severity, EVENT_SEVERITY

log = logging.getLogger(__name__)

_local = threading.local()


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    # ── connection management ──────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        """Return this thread's SQLite connection, creating it if needed."""
        if not hasattr(_local, "conn"):
            _local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            _local.conn.row_factory = sqlite3.Row
            _local.conn.execute("PRAGMA journal_mode=WAL")
            _local.conn.execute("PRAGMA foreign_keys=ON")
        return _local.conn

    def init_schema(self):
        """Create all tables on first run."""
        conn = self._conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS devices (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ip          TEXT NOT NULL UNIQUE,
                mac         TEXT,
                vendor      TEXT,
                hostname    TEXT,
                is_blocked  INTEGER DEFAULT 0,
                notes       TEXT,
                first_seen  TEXT NOT NULL,
                last_seen   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id    INTEGER REFERENCES devices(id),
                device_ip    TEXT,
                event_type   TEXT NOT NULL,
                severity     TEXT NOT NULL,
                description  TEXT,
                details      TEXT,          -- JSON blob
                acknowledged INTEGER DEFAULT 0,
                timestamp    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS connections (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id   INTEGER REFERENCES devices(id),
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

            CREATE TABLE IF NOT EXISTS threat_intel (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                source       TEXT NOT NULL,
                type         TEXT NOT NULL,   -- 'ip' or 'domain'
                value        TEXT NOT NULL,
                description  TEXT,
                last_updated TEXT NOT NULL,
                UNIQUE(source, value)
            );

            CREATE TABLE IF NOT EXISTS geo_cache (
                ip           TEXT PRIMARY KEY,
                country      TEXT,
                country_code TEXT,
                isp          TEXT,
                org          TEXT,
                cached_at    TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_ts      ON events(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_events_severity ON events(severity);
            CREATE INDEX IF NOT EXISTS idx_conn_device    ON connections(device_id);
            CREATE INDEX IF NOT EXISTS idx_conn_ts        ON connections(timestamp);
            CREATE INDEX IF NOT EXISTS idx_intel_value    ON threat_intel(value);
        """)
        conn.commit()
        log.info("Database schema ready at %s", self.db_path)

    # ── devices ───────────────────────────────────────────────────────────────

    def upsert_device(self, ip: str, mac: str = None, vendor: str = None,
                      hostname: str = None) -> Dict:
        conn = self._conn()
        now = datetime.utcnow().isoformat()
        row = conn.execute("SELECT * FROM devices WHERE ip=?", (ip,)).fetchone()
        if row:
            conn.execute(
                "UPDATE devices SET mac=COALESCE(?,mac), vendor=COALESCE(?,vendor),"
                " hostname=COALESCE(?,hostname), last_seen=? WHERE ip=?",
                (mac, vendor, hostname, now, ip)
            )
            conn.commit()
            return dict(conn.execute("SELECT * FROM devices WHERE ip=?", (ip,)).fetchone())
        else:
            conn.execute(
                "INSERT INTO devices(ip,mac,vendor,hostname,first_seen,last_seen)"
                " VALUES(?,?,?,?,?,?)",
                (ip, mac, vendor, hostname, now, now)
            )
            conn.commit()
            return dict(conn.execute("SELECT * FROM devices WHERE ip=?", (ip,)).fetchone())

    def get_device(self, ip: str = None, device_id: int = None) -> Optional[Dict]:
        conn = self._conn()
        if ip:
            row = conn.execute("SELECT * FROM devices WHERE ip=?", (ip,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()
        return dict(row) if row else None

    def get_all_devices(self) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT d.*, "
            " (SELECT COUNT(*) FROM events e WHERE e.device_id=d.id AND date(e.timestamp)=date('now')) AS events_today,"
            " (SELECT COUNT(*) FROM events e WHERE e.device_id=d.id) AS total_events"
            " FROM devices d ORDER BY d.last_seen DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def set_device_blocked(self, device_id: int, blocked: bool):
        conn = self._conn()
        conn.execute("UPDATE devices SET is_blocked=? WHERE id=?", (int(blocked), device_id))
        conn.commit()

    # ── events ────────────────────────────────────────────────────────────────

    def add_event(self, device_ip: str, event_type: str, description: str,
                  details: dict = None, device_id: int = None,
                  severity: str = None) -> int:
        conn = self._conn()
        if severity is None:
            severity = EVENT_SEVERITY.get(event_type, Severity.LOW)
        now = datetime.utcnow().isoformat()
        cur = conn.execute(
            "INSERT INTO events(device_id,device_ip,event_type,severity,description,details,timestamp)"
            " VALUES(?,?,?,?,?,?,?)",
            (device_id, device_ip, event_type, severity,
             description, json.dumps(details or {}), now)
        )
        conn.commit()
        return cur.lastrowid

    def get_events(self, limit: int = 100, severity: str = None,
                   device_id: int = None, acknowledged: bool = None) -> List[Dict]:
        conn = self._conn()
        q = "SELECT * FROM events WHERE 1=1"
        params = []
        if severity:
            q += " AND severity=?"; params.append(severity)
        if device_id:
            q += " AND device_id=?"; params.append(device_id)
        if acknowledged is not None:
            q += " AND acknowledged=?"; params.append(int(acknowledged))
        q += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in conn.execute(q, params).fetchall()]

    def acknowledge_event(self, event_id: int):
        conn = self._conn()
        conn.execute("UPDATE events SET acknowledged=1 WHERE id=?", (event_id,))
        conn.commit()

    def count_events_today(self) -> int:
        conn = self._conn()
        row = conn.execute(
            "SELECT COUNT(*) FROM events WHERE date(timestamp)=date('now')"
        ).fetchone()
        return row[0]

    def count_unacknowledged(self) -> int:
        conn = self._conn()
        return conn.execute(
            "SELECT COUNT(*) FROM events WHERE acknowledged=0"
        ).fetchone()[0]

    # ── connections ───────────────────────────────────────────────────────────

    def add_connection(self, device_id: int, src_ip: str, dst_ip: str,
                       dst_port: int = None, protocol: str = None,
                       bytes_: int = 0, country: str = None,
                       country_code: str = None, isp: str = None,
                       dns_query: str = None):
        conn = self._conn()
        conn.execute(
            "INSERT INTO connections"
            "(device_id,src_ip,dst_ip,dst_port,protocol,bytes,country,country_code,isp,dns_query,timestamp)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (device_id, src_ip, dst_ip, dst_port, protocol, bytes_,
             country, country_code, isp, dns_query,
             datetime.utcnow().isoformat())
        )
        conn.commit()

    def get_connections(self, device_id: int = None,
                        minutes: int = 30, limit: int = 200) -> List[Dict]:
        conn = self._conn()
        since = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
        if device_id:
            rows = conn.execute(
                "SELECT * FROM connections WHERE device_id=? AND timestamp>=?"
                " ORDER BY timestamp DESC LIMIT ?",
                (device_id, since, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM connections WHERE timestamp>=?"
                " ORDER BY timestamp DESC LIMIT ?",
                (since, limit)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_connection_volume(self, device_id: int, minutes: int = 1) -> int:
        """Return total bytes for a device in the last N minutes."""
        conn = self._conn()
        since = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
        row = conn.execute(
            "SELECT COALESCE(SUM(bytes),0) FROM connections"
            " WHERE device_id=? AND timestamp>=?",
            (device_id, since)
        ).fetchone()
        return row[0]

    # ── threat intel ──────────────────────────────────────────────────────────

    def bulk_upsert_intel(self, source: str, type_: str, values: List[str]):
        """Insert/replace a batch of threat intel entries."""
        conn = self._conn()
        now = datetime.utcnow().isoformat()
        conn.executemany(
            "INSERT OR REPLACE INTO threat_intel(source,type,value,last_updated)"
            " VALUES(?,?,?,?)",
            [(source, type_, v, now) for v in values if v]
        )
        conn.commit()

    def check_ip(self, ip: str) -> Optional[Dict]:
        conn = self._conn()
        row = conn.execute(
            "SELECT * FROM threat_intel WHERE type='ip' AND value=? LIMIT 1", (ip,)
        ).fetchone()
        return dict(row) if row else None

    def check_domain(self, domain: str) -> Optional[Dict]:
        conn = self._conn()
        domain = domain.rstrip(".")
        row = conn.execute(
            "SELECT * FROM threat_intel WHERE type='domain' AND value=? LIMIT 1",
            (domain,)
        ).fetchone()
        return dict(row) if row else None

    def count_intel_entries(self) -> Dict[str, int]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT type, COUNT(*) as cnt FROM threat_intel GROUP BY type"
        ).fetchall()
        return {r["type"]: r["cnt"] for r in rows}

    def get_intel_sources(self) -> List[Dict]:
        conn = self._conn()
        rows = conn.execute(
            "SELECT source, type, COUNT(*) as cnt, MAX(last_updated) as updated"
            " FROM threat_intel GROUP BY source, type"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── geo cache ─────────────────────────────────────────────────────────────

    def get_geo(self, ip: str, max_age_hours: int = 24) -> Optional[Dict]:
        conn = self._conn()
        since = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()
        row = conn.execute(
            "SELECT * FROM geo_cache WHERE ip=? AND cached_at>=?", (ip, since)
        ).fetchone()
        return dict(row) if row else None

    def save_geo(self, ip: str, country: str, country_code: str,
                 isp: str = "", org: str = ""):
        conn = self._conn()
        conn.execute(
            "INSERT OR REPLACE INTO geo_cache(ip,country,country_code,isp,org,cached_at)"
            " VALUES(?,?,?,?,?,?)",
            (ip, country, country_code, isp, org, datetime.utcnow().isoformat())
        )
        conn.commit()

    # ── dashboard stats ───────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        conn = self._conn()
        total_devices = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
        blocked_devices = conn.execute(
            "SELECT COUNT(*) FROM devices WHERE is_blocked=1"
        ).fetchone()[0]
        events_today = self.count_events_today()
        unacked = self.count_unacknowledged()
        critical_today = conn.execute(
            "SELECT COUNT(*) FROM events WHERE severity='critical' AND date(timestamp)=date('now')"
        ).fetchone()[0]
        intel = self.count_intel_entries()
        return {
            "total_devices": total_devices,
            "blocked_devices": blocked_devices,
            "events_today": events_today,
            "unacknowledged": unacked,
            "critical_today": critical_today,
            "intel_ips": intel.get("ip", 0),
            "intel_domains": intel.get("domain", 0),
        }

    def seed_demo_data(self):
        """Insert realistic-looking demo data for UI testing."""
        import random, time
        log.info("Seeding demo data…")
        devices = [
            ("192.168.1.101", "aa:bb:cc:dd:ee:01", "Samsung Electronics", "smart-tv"),
            ("192.168.1.102", "aa:bb:cc:dd:ee:02", "Amazon Technologies", "echo-dot"),
            ("192.168.1.103", "aa:bb:cc:dd:ee:03", "Espressif Inc.", "esp32-sensor"),
            ("192.168.1.104", "aa:bb:cc:dd:ee:04", "Apple Inc.", "iphone"),
            ("192.168.1.105", "aa:bb:cc:dd:ee:05", "Unknown", "unknown-device"),
        ]
        ids = {}
        for ip, mac, vendor, host in devices:
            d = self.upsert_device(ip, mac, vendor, host)
            ids[ip] = d["id"]

        events = [
            ("192.168.1.101", EventType.BEACONING, "Regular outbound connections every 60s",
             {"dst_ip": "45.12.33.99", "interval_avg": 60.1, "cv": 0.04}),
            ("192.168.1.103", EventType.BLACKLIST_IP, "Connection to known C2 server",
             {"dst_ip": "91.108.56.77", "source": "feodo_tracker"}),
            ("192.168.1.105", EventType.NEW_DEVICE, "New device joined the network",
             {"mac": "aa:bb:cc:dd:ee:05"}),
            ("192.168.1.102", EventType.GEO_ANOMALY, "Connection to KP (North Korea)",
             {"dst_ip": "175.45.176.0", "country": "North Korea", "country_code": "KP"}),
            ("192.168.1.101", EventType.HIGH_VOLUME, "Unusual outbound volume: 8 MB/min",
             {"bytes_per_min": 8388608}),
        ]
        for ip, etype, desc, det in events:
            self.add_event(ip, etype, desc, det, device_id=ids.get(ip))

        log.info("Demo data seeded: %d devices, %d events", len(devices), len(events))
