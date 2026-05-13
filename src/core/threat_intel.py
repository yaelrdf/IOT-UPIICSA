"""
Threat intelligence — downloads and caches IP/domain blocklists,
and provides geo-lookup via ip-api.com (free, no key needed).
"""
import logging
import re
import time
import requests
from typing import Optional, Dict
from datetime import datetime

from src.constants import PRIVATE_RANGES

log = logging.getLogger(__name__)

# Simple rate limiting for ip-api.com (45 req/min free tier)
_geo_last_call = 0.0
_GEO_MIN_INTERVAL = 1.5    # seconds between calls


def _is_private(ip: str) -> bool:
    return any(ip.startswith(p) for p in PRIVATE_RANGES)


class ThreatIntel:
    def __init__(self, config, db):
        self.cfg = config
        self.db  = db

    # ── blocklist management ───────────────────────────────────────────────────

    def update_all(self) -> Dict[str, int]:
        """Download all configured intel sources. Returns {source: count}."""
        results = {}
        for src in self.cfg.threat_intel.sources:
            try:
                count = self._download_source(src)
                results[src.name] = count
            except Exception as e:
                log.error("Failed to update %s: %s", src.name, e)
                results[src.name] = -1
        # Record event
        total = sum(v for v in results.values() if v >= 0)
        self.db.add_event(
            "system", "intel_updated",
            f"Threat intel updated: {total} entries across {len(results)} sources",
            {"sources": results},
        )
        return results

    def _download_source(self, src) -> int:
        """Fetch a single source URL and upsert entries into DB."""
        log.info("Downloading threat intel: %s …", src.url)
        resp = requests.get(src.url, timeout=30)
        resp.raise_for_status()

        values = []
        for line in resp.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            # Hosts-file format: "0.0.0.0 domain.com"
            if src.type == "domain" and " " in line:
                parts = line.split()
                if len(parts) >= 2:
                    line = parts[1]
            # Strip any trailing path / port
            line = line.split("/")[0].split(":")[0].strip()
            if not line or line in ("0.0.0.0", "127.0.0.1", "localhost"):
                continue
            # Basic validation
            if src.type == "ip" and not _looks_like_ip(line):
                continue
            if src.type == "domain" and not _looks_like_domain(line):
                continue
            values.append(line)

        self.db.bulk_upsert_intel(src.name, src.type, values)
        log.info("  → %s: %d entries loaded", src.name, len(values))
        return len(values)

    # ── lookup helpers ────────────────────────────────────────────────────────

    def check_ip(self, ip: str) -> Optional[Dict]:
        return self.db.check_ip(ip)

    def check_domain(self, domain: str) -> Optional[Dict]:
        return self.db.check_domain(domain)

    # ── geo lookup ────────────────────────────────────────────────────────────

    def geo_lookup(self, ip: str) -> Optional[Dict]:
        """
        Return geolocation info for an IP.
        Results cached in DB for geo_cache_hours.
        """
        if _is_private(ip):
            return {"country": "Private", "country_code": "LAN", "isp": "Local network"}

        # Check DB cache first
        cached = self.db.get_geo(ip, self.cfg.thresholds.geo_cache_hours)
        if cached:
            return cached

        # Rate-limit API calls
        global _geo_last_call
        elapsed = time.time() - _geo_last_call
        if elapsed < _GEO_MIN_INTERVAL:
            time.sleep(_GEO_MIN_INTERVAL - elapsed)
        _geo_last_call = time.time()

        try:
            url  = self.cfg.threat_intel.geo_api_url.format(ip=ip)
            resp = requests.get(url, timeout=5)
            data = resp.json()
            if data.get("status") == "fail":
                return None
            result = {
                "country":      data.get("country", ""),
                "country_code": data.get("countryCode", ""),
                "isp":          data.get("isp", ""),
                "org":          data.get("org", ""),
            }
            self.db.save_geo(ip, **result)
            return result
        except Exception as e:
            log.debug("Geo lookup failed for %s: %s", ip, e)
            return None


# ── helpers ───────────────────────────────────────────────────────────────────

_IP_RE     = re.compile(r"^\d{1,3}(\.\d{1,3}){3}(/\d{1,2})?$")
_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$")


def _looks_like_ip(s: str) -> bool:
    return bool(_IP_RE.match(s))


def _looks_like_domain(s: str) -> bool:
    return bool(_DOMAIN_RE.match(s))
