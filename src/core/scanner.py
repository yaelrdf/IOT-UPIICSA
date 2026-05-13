"""
Network scanner — ARP-based device discovery with vendor lookup.
Falls back gracefully if Scapy isn't available or we don't have raw socket access.
"""
import logging
import socket
from typing import List, Tuple, Optional

log = logging.getLogger(__name__)


def _get_vendor(mac: str) -> str:
    """Attempt vendor lookup via Scapy's manufacturer DB."""
    try:
        from scapy.all import conf
        vendor = conf.manufdb._get_manuf(mac)
        return vendor or "Unknown"
    except Exception:
        return "Unknown"


def arp_scan(interface: str, subnet: str) -> List[Tuple[str, str, str]]:
    """
    Broadcast ARP scan and return list of (ip, mac, vendor) tuples.
    Requires root / CAP_NET_RAW.
    """
    try:
        from scapy.all import ARP, Ether, srp
        log.info("ARP scanning %s on %s …", subnet, interface)
        arp   = ARP(pdst=subnet)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        result, _ = srp(ether / arp, iface=interface, timeout=3, verbose=False)
        found = []
        for _, rcv in result:
            ip  = rcv.psrc
            mac = rcv.hwsrc
            vendor = _get_vendor(mac)
            found.append((ip, mac, vendor))
        log.info("ARP scan found %d device(s)", len(found))
        return found
    except PermissionError:
        log.error("ARP scan failed: permission denied — run as root")
        return []
    except Exception as exc:
        log.error("ARP scan error: %s", exc)
        return []


def resolve_hostname(ip: str) -> Optional[str]:
    """Reverse-DNS lookup with short timeout."""
    try:
        socket.setdefaulttimeout(1)
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


class Scanner:
    """
    Wraps arp_scan and device upsert so the scheduler can call it easily.
    """
    def __init__(self, config, db):
        self.cfg = config
        self.db  = db

    def run_discovery(self) -> List[dict]:
        """
        Scan the network, upsert all found devices, return list of device dicts.
        Fires a NEW_DEVICE event for any device seen for the first time.
        """
        from constants import EventType
        results = arp_scan(self.cfg.network.interface, self.cfg.network.subnet)
        devices = []
        for ip, mac, vendor in results:
            existing = self.db.get_device(ip=ip)
            hostname = resolve_hostname(ip)
            device   = self.db.upsert_device(ip, mac, vendor, hostname)
            devices.append(device)

            if not existing and self.cfg.thresholds.new_device_alert:
                self.db.add_event(
                    ip, EventType.NEW_DEVICE,
                    f"New device joined the network: {vendor} ({mac})",
                    {"mac": mac, "vendor": vendor, "hostname": hostname},
                    device_id=device["id"],
                )
                log.info("New device: %s (%s / %s)", ip, mac, vendor)

        return devices

    def get_target_ips(self) -> List[str]:
        """
        Return IPs to target based on config.
        'all' → all discovered devices; otherwise use the explicit list.
        """
        if self.cfg.scan.targets == "all":
            return [d["ip"] for d in self.db.get_all_devices()]
        return list(self.cfg.scan.targets)
