"""
Analyzer — the brain of the system.
Takes captured packet metadata and runs all detection rules:
  1. Known-bad IP (blacklist)
  2. Known-bad domain (blacklist)
  3. Beaconing detection
  4. Geographic anomaly
  5. High data volume
"""
import logging
import statistics
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any

from src.constants import EventType, Severity, PRIVATE_RANGES

log = logging.getLogger(__name__)


def _is_private(ip: str) -> bool:
    return any(ip.startswith(p) for p in PRIVATE_RANGES)


class Analyzer:
    def __init__(self, config, db, threat_intel):
        self.cfg    = config
        self.db     = db
        self.intel  = threat_intel

    # ── main entry point ──────────────────────────────────────────────────────

    def analyze(self, packets: List[Dict]) -> List[Dict]:
        """
        Run all detection rules against a batch of packet metadata.
        Returns a list of event dicts that were created.
        """
        events_created = []

        # Group packets by source device IP for per-device analysis
        by_src: Dict[str, List[Dict]] = defaultdict(list)
        for pkt in packets:
            by_src[pkt["src_ip"]].append(pkt)

        for src_ip, pkt_list in by_src.items():
            device = self.db.get_device(ip=src_ip)
            if not device:
                continue   # Only analyze known devices
            did = device["id"]

            events_created += self._check_blacklist_ips(src_ip, did, pkt_list)
            events_created += self._check_blacklist_domains(src_ip, did, pkt_list)
            events_created += self._check_geo_anomaly(src_ip, did, pkt_list)
            events_created += self._check_beaconing(src_ip, did, pkt_list)
            events_created += self._check_high_volume(src_ip, did)

        return events_created

    # ── detection rules ───────────────────────────────────────────────────────

    def _check_blacklist_ips(self, src_ip, device_id, packets) -> list:
        """Flag connections to IPs on known blocklists."""
        events = []
        seen = set()
        for pkt in packets:
            dst = pkt["dst_ip"]
            if dst in seen or _is_private(dst):
                continue
            seen.add(dst)
            hit = self.intel.check_ip(dst)
            if hit:
                desc = (f"Connection to known malicious IP {dst} "
                        f"(source: {hit['source']})")
                eid = self.db.add_event(
                    src_ip, EventType.BLACKLIST_IP, desc,
                    {"dst_ip": dst, "source": hit["source"],
                     "last_updated": hit["last_updated"]},
                    device_id=device_id,
                )
                events.append({"id": eid, "type": EventType.BLACKLIST_IP,
                               "device_ip": src_ip, "dst_ip": dst})
                log.warning("BLACKLIST IP: %s → %s (%s)", src_ip, dst, hit["source"])
        return events

    def _check_blacklist_domains(self, src_ip, device_id, packets) -> list:
        """Flag DNS queries for blacklisted domains."""
        events = []
        seen = set()
        for pkt in packets:
            domain = pkt.get("dns_query")
            if not domain or domain in seen:
                continue
            seen.add(domain)
            hit = self.intel.check_domain(domain)
            if hit:
                desc = f"DNS query to known-bad domain: {domain} (source: {hit['source']})"
                eid = self.db.add_event(
                    src_ip, EventType.BLACKLIST_DOMAIN, desc,
                    {"domain": domain, "source": hit["source"]},
                    device_id=device_id,
                )
                events.append({"id": eid, "type": EventType.BLACKLIST_DOMAIN,
                               "device_ip": src_ip, "domain": domain})
                log.warning("BLACKLIST DOMAIN: %s → %s", src_ip, domain)
        return events

    def _check_geo_anomaly(self, src_ip, device_id, packets) -> list:
        """Flag connections to alert-listed countries."""
        events = []
        seen = set()
        alert_codes = set(self.cfg.thresholds.geo_alert_countries)
        for pkt in packets:
            dst = pkt["dst_ip"]
            if dst in seen or _is_private(dst):
                continue
            seen.add(dst)
            geo = self.intel.geo_lookup(dst)
            if not geo:
                continue
            cc = geo.get("country_code", "")
            if cc in alert_codes:
                desc = (f"Connection to {geo.get('country','?')} ({cc}): "
                        f"{src_ip} → {dst}")
                eid = self.db.add_event(
                    src_ip, EventType.GEO_ANOMALY, desc,
                    {"dst_ip": dst, "country": geo.get("country"),
                     "country_code": cc, "isp": geo.get("isp")},
                    device_id=device_id,
                )
                events.append({"id": eid, "type": EventType.GEO_ANOMALY,
                               "device_ip": src_ip, "country_code": cc})
                log.warning("GEO ANOMALY: %s → %s (%s)", src_ip, dst, cc)
        return events

    def _check_beaconing(self, src_ip, device_id, packets) -> list:
        """
        Detect regular, repeating outbound connections — a botnet heartbeat pattern.
        Groups packets by (dst_ip, dst_port) and checks the coefficient of variation
        of the inter-connection intervals. Low CV = highly regular = suspicious.
        """
        events = []
        min_conns = self.cfg.thresholds.beaconing_min_connections
        max_cv    = self.cfg.thresholds.beaconing_max_cv

        # Group by destination
        groups: Dict[tuple, List[float]] = defaultdict(list)
        for pkt in packets:
            if not _is_private(pkt["dst_ip"]):
                key = (pkt["dst_ip"], pkt.get("dst_port"))
                groups[key].append(pkt["timestamp"])

        for (dst_ip, dst_port), timestamps in groups.items():
            if len(timestamps) < min_conns:
                continue
            timestamps.sort()
            intervals = [timestamps[i+1] - timestamps[i]
                         for i in range(len(timestamps) - 1)]
            if not intervals or statistics.mean(intervals) == 0:
                continue
            cv = statistics.stdev(intervals) / statistics.mean(intervals)
            if cv <= max_cv:
                avg_interval = statistics.mean(intervals)
                desc = (f"Beaconing detected: {src_ip} → {dst_ip}:{dst_port} "
                        f"every ~{avg_interval:.1f}s (CV={cv:.3f})")
                eid = self.db.add_event(
                    src_ip, EventType.BEACONING, desc,
                    {"dst_ip": dst_ip, "dst_port": dst_port,
                     "connection_count": len(timestamps),
                     "avg_interval_sec": round(avg_interval, 2),
                     "coefficient_of_variation": round(cv, 4)},
                    device_id=device_id,
                )
                events.append({"id": eid, "type": EventType.BEACONING,
                               "device_ip": src_ip})
                log.warning("BEACONING: %s → %s:%s every %.1fs (CV=%.3f)",
                            src_ip, dst_ip, dst_port, avg_interval, cv)
        return events

    def _check_high_volume(self, src_ip, device_id) -> list:
        """Alert when a device sends an unusual amount of data in the last minute."""
        events = []
        threshold_kb = self.cfg.thresholds.volume_alert_kb_per_min
        bytes_last_min = self.db.get_connection_volume(device_id, minutes=1)
        kb = bytes_last_min / 1024
        if kb >= threshold_kb:
            desc = (f"High outbound volume from {src_ip}: "
                    f"{kb:.0f} KB in the last minute (threshold: {threshold_kb} KB)")
            eid = self.db.add_event(
                src_ip, EventType.HIGH_VOLUME, desc,
                {"kb_per_min": round(kb, 1), "threshold_kb": threshold_kb},
                device_id=device_id,
            )
            events.append({"id": eid, "type": EventType.HIGH_VOLUME,
                           "device_ip": src_ip})
            log.warning("HIGH VOLUME: %s → %.0f KB/min", src_ip, kb)
        return events
