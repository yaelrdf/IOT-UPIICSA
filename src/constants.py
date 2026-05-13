"""
Shared constants for event types, severity levels, and their mappings.
"""


class EventType:
    NEW_DEVICE      = "new_device"
    BLACKLIST_IP    = "blacklist_ip"
    BLACKLIST_DOMAIN= "blacklist_domain"
    BEACONING       = "beaconing"
    GEO_ANOMALY     = "geo_anomaly"
    HIGH_VOLUME     = "high_volume"
    PORT_SCAN       = "port_scan"
    DEVICE_BLOCKED  = "device_blocked"
    DEVICE_UNBLOCKED= "device_unblocked"
    INTEL_UPDATED   = "intel_updated"

    LABELS = {
        NEW_DEVICE:       "New device",
        BLACKLIST_IP:     "Known-bad IP",
        BLACKLIST_DOMAIN: "Known-bad domain",
        BEACONING:        "Beaconing detected",
        GEO_ANOMALY:      "Geo anomaly",
        HIGH_VOLUME:      "High data volume",
        PORT_SCAN:        "Port scan detected",
        DEVICE_BLOCKED:   "Device blocked",
        DEVICE_UNBLOCKED: "Device unblocked",
        INTEL_UPDATED:    "Threat intel updated",
    }


class Severity:
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"

    WEIGHTS = {LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4}

    # Bootstrap color class for each severity
    BS_COLOR = {
        LOW:      "info",
        MEDIUM:   "warning",
        HIGH:     "orange",
        CRITICAL: "danger",
    }


# Default severity per event type
EVENT_SEVERITY = {
    EventType.NEW_DEVICE:       Severity.LOW,
    EventType.BLACKLIST_IP:     Severity.CRITICAL,
    EventType.BLACKLIST_DOMAIN: Severity.HIGH,
    EventType.BEACONING:        Severity.HIGH,
    EventType.GEO_ANOMALY:      Severity.MEDIUM,
    EventType.HIGH_VOLUME:      Severity.MEDIUM,
    EventType.PORT_SCAN:        Severity.HIGH,
    EventType.DEVICE_BLOCKED:   Severity.LOW,
    EventType.DEVICE_UNBLOCKED: Severity.LOW,
    EventType.INTEL_UPDATED:    Severity.LOW,
}

# Private IP ranges (we skip geo lookups for these)
PRIVATE_RANGES = [
    "10.", "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.", "192.168.", "127.", "169.254.",
]
