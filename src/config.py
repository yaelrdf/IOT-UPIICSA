"""
Configuration loader — reads config.yaml and exposes a typed Config object.
"""
import os
import yaml
from dataclasses import dataclass, field
from typing import List, Union


# ── sub-configs ────────────────────────────────────────────────────────────────

@dataclass
class NetworkConfig:
    interface: str = "eth0"
    mode: str = "passive"          # "passive" or "active"
    gateway_ip: str = "192.168.1.1"
    subnet: str = "192.168.1.0/24"

@dataclass
class ScanConfig:
    discovery_interval_sec: int = 300
    capture_duration_sec: int = 60
    capture_interval_sec: int = 600
    targets: Union[str, List[str]] = "all"

@dataclass
class EmailConfig:
    enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 465
    use_ssl: bool = True
    sender_email: str = ""
    sender_password: str = ""
    recipient_email: str = ""
    alert_on_severity: List[str] = field(default_factory=lambda: ["high", "critical"])

@dataclass
class ThresholdConfig:
    beaconing_min_connections: int = 8
    beaconing_max_cv: float = 0.20
    beaconing_window_min: int = 30
    volume_alert_kb_per_min: int = 2048
    geo_alert_countries: List[str] = field(default_factory=lambda: ["KP", "IR"])
    geo_cache_hours: int = 24
    new_device_alert: bool = True

@dataclass
class WebConfig:
    host: str = "0.0.0.0"
    port: int = 5000
    secret_key: str = "change_me"
    debug: bool = False

@dataclass
class DatabaseConfig:
    path: str = "data/monitor.db"

@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "data/monitor.log"
    max_bytes: int = 10_485_760
    backup_count: int = 3

@dataclass
class ThreatIntelSource:
    name: str = ""
    url: str = ""
    type: str = "ip"   # "ip" or "domain"

@dataclass
class ThreatIntelConfig:
    auto_update: bool = True
    update_interval_sec: int = 86400
    geo_api_url: str = "http://ip-api.com/json/{ip}?fields=countryCode,country,isp,org"
    sources: List[ThreatIntelSource] = field(default_factory=list)


# ── root config ────────────────────────────────────────────────────────────────

@dataclass
class Config:
    network: NetworkConfig = field(default_factory=NetworkConfig)
    scan: ScanConfig = field(default_factory=ScanConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    web: WebConfig = field(default_factory=WebConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    threat_intel: ThreatIntelConfig = field(default_factory=ThreatIntelConfig)


def load_config(path: str = "config.yaml") -> Config:
    """Load YAML config file and return a Config dataclass instance."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}

    cfg = Config()

    n = raw.get("network", {})
    cfg.network = NetworkConfig(
        interface=n.get("interface", cfg.network.interface),
        mode=n.get("mode", cfg.network.mode),
        gateway_ip=n.get("gateway_ip", cfg.network.gateway_ip),
        subnet=n.get("subnet", cfg.network.subnet),
    )

    s = raw.get("scan", {})
    cfg.scan = ScanConfig(
        discovery_interval_sec=s.get("discovery_interval_sec", cfg.scan.discovery_interval_sec),
        capture_duration_sec=s.get("capture_duration_sec", cfg.scan.capture_duration_sec),
        capture_interval_sec=s.get("capture_interval_sec", cfg.scan.capture_interval_sec),
        targets=s.get("targets", cfg.scan.targets),
    )

    e = raw.get("email", {})
    cfg.email = EmailConfig(
        enabled=e.get("enabled", False),
        smtp_server=e.get("smtp_server", cfg.email.smtp_server),
        smtp_port=e.get("smtp_port", cfg.email.smtp_port),
        use_ssl=e.get("use_ssl", cfg.email.use_ssl),
        sender_email=e.get("sender_email", ""),
        sender_password=e.get("sender_password", ""),
        recipient_email=e.get("recipient_email", ""),
        alert_on_severity=e.get("alert_on_severity", cfg.email.alert_on_severity),
    )

    t = raw.get("thresholds", {})
    cfg.thresholds = ThresholdConfig(
        beaconing_min_connections=t.get("beaconing_min_connections", 8),
        beaconing_max_cv=t.get("beaconing_max_cv", 0.20),
        beaconing_window_min=t.get("beaconing_window_min", 30),
        volume_alert_kb_per_min=t.get("volume_alert_kb_per_min", 2048),
        geo_alert_countries=t.get("geo_alert_countries", ["KP", "IR"]),
        geo_cache_hours=t.get("geo_cache_hours", 24),
        new_device_alert=t.get("new_device_alert", True),
    )

    w = raw.get("web", {})
    cfg.web = WebConfig(
        host=w.get("host", "0.0.0.0"),
        port=w.get("port", 5000),
        secret_key=w.get("secret_key", "change_me"),
        debug=w.get("debug", False),
    )

    d = raw.get("database", {})
    cfg.database = DatabaseConfig(path=d.get("path", "data/monitor.db"))

    l = raw.get("logging", {})
    cfg.logging = LoggingConfig(
        level=l.get("level", "INFO"),
        file=l.get("file", "data/monitor.log"),
        max_bytes=l.get("max_bytes", 10_485_760),
        backup_count=l.get("backup_count", 3),
    )

    ti = raw.get("threat_intel", {})
    sources = [
        ThreatIntelSource(name=s["name"], url=s["url"], type=s.get("type", "ip"))
        for s in ti.get("sources", [])
    ]
    cfg.threat_intel = ThreatIntelConfig(
        auto_update=ti.get("auto_update", True),
        update_interval_sec=ti.get("update_interval_sec", 86400),
        geo_api_url=ti.get("geo_api_url", cfg.threat_intel.geo_api_url),
        sources=sources,
    )

    # Make sure the data directory exists
    os.makedirs(os.path.dirname(cfg.database.path), exist_ok=True)

    return cfg
