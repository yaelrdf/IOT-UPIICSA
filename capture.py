"""
Packet capture — sniffs the network interface and extracts metadata.
Stores per-packet metadata in the DB (never payload content).
In active mode, forwards non-blocked packets when we're acting as MITM.
"""
import logging
import time
import threading
from typing import List, Dict, Any, Set
from datetime import datetime

from constants import PRIVATE_RANGES

log = logging.getLogger(__name__)


def _is_private(ip: str) -> bool:
    return any(ip.startswith(p) for p in PRIVATE_RANGES)


def _extract_metadata(pkt) -> Dict[str, Any]:
    """Pull metadata fields from a Scapy packet. Returns None if not IP."""
    try:
        from scapy.all import IP, TCP, UDP, DNS, DNSQR
        if IP not in pkt:
            return None
        meta = {
            "src_ip":    pkt[IP].src,
            "dst_ip":    pkt[IP].dst,
            "protocol":  "OTHER",
            "dst_port":  None,
            "bytes":     len(pkt),
            "dns_query": None,
            "timestamp": time.time(),
        }
        if TCP in pkt:
            meta["protocol"] = "TCP"
            meta["dst_port"] = pkt[TCP].dport
        elif UDP in pkt:
            meta["protocol"] = "UDP"
            meta["dst_port"] = pkt[UDP].dport
            # Capture DNS queries for domain blacklist checking
            if DNS in pkt and pkt[DNS].qr == 0 and DNSQR in pkt:
                meta["dns_query"] = pkt[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".")
        return meta
    except Exception:
        return None


class PacketCapture:
    """
    Manages a Scapy sniff session in a background thread.
    Fills a thread-safe list with packet metadata dicts.
    """

    def __init__(self, config, db):
        self.cfg        = config
        self.db         = db
        self._packets   = []
        self._lock      = threading.Lock()
        self._thread    = None
        self._stop_evt  = threading.Event()
        self._blocked: Set[str] = set()   # IPs we should drop traffic to

    # ── public API ────────────────────────────────────────────────────────────

    def start(self, duration: int = None):
        """Start sniffing in a background thread for `duration` seconds."""
        if duration is None:
            duration = self.cfg.scan.capture_duration_sec
        self._stop_evt.clear()
        with self._lock:
            self._packets.clear()
        self._thread = threading.Thread(
            target=self._sniff_loop, args=(duration,),
            daemon=True, name="packet-capture"
        )
        self._thread.start()
        log.info("Capture started on %s (duration=%ds, mode=%s)",
                 self.cfg.network.interface, duration, self.cfg.network.mode)

    def stop(self):
        """Signal the sniff thread to stop."""
        self._stop_evt.set()

    def wait(self):
        """Block until capture is done."""
        if self._thread:
            self._thread.join()

    def drain(self) -> List[Dict]:
        """Return captured packets and clear the buffer."""
        with self._lock:
            pkts = list(self._packets)
            self._packets.clear()
        return pkts

    def block_ip(self, ip: str):
        self._blocked.add(ip)
        log.info("Blocking traffic to %s", ip)

    def unblock_ip(self, ip: str):
        self._blocked.discard(ip)
        log.info("Unblocked traffic to %s", ip)

    def sync_blocked_from_db(self):
        """Pull the current block list from DB (call after block/unblock via UI)."""
        devices = self.db.get_all_devices()
        blocked_ips = {d["ip"] for d in devices if d.get("is_blocked")}
        self._blocked = blocked_ips

    # ── internal ──────────────────────────────────────────────────────────────

    def _sniff_loop(self, duration: int):
        try:
            from scapy.all import sniff
            sniff(
                iface=self.cfg.network.interface,
                prn=self._handle_packet,
                store=False,
                timeout=duration,
                promisc=True,
                stop_filter=lambda _: self._stop_evt.is_set(),
            )
        except PermissionError:
            log.error("Packet capture failed: permission denied — run as root")
        except Exception as exc:
            log.error("Packet capture error: %s", exc)
        finally:
            log.info("Capture finished (%d packets collected)", len(self._packets))

    def _handle_packet(self, pkt):
        meta = _extract_metadata(pkt)
        if not meta:
            return

        # In active (MITM) mode, check if we should drop or forward the packet
        if self.cfg.network.mode == "active":
            if meta["dst_ip"] in self._blocked:
                log.debug("DROPPED packet to blocked IP %s", meta["dst_ip"])
                return  # Drop — don't forward, don't record
            self._forward_packet(pkt)

        with self._lock:
            self._packets.append(meta)

    def _forward_packet(self, pkt):
        """Forward a packet (kernel IP forward handles this, but we need
        to send it explicitly when using Scapy's promisc sniff bypass)."""
        try:
            from scapy.all import IP, send
            if IP in pkt:
                fwd = pkt.copy()
                fwd[IP].ttl -= 1
                if fwd[IP].ttl <= 0:
                    return
                del fwd[IP].chksum
                send(fwd, iface=self.cfg.network.interface, verbose=False)
        except Exception as e:
            log.debug("Forward error: %s", e)


def save_packets_to_db(db, packets: List[Dict], geo_lookup_fn=None):
    """
    Persist a batch of packet metadata to the connections table.
    Resolves device IDs from IPs and optionally fetches geo data.
    """
    for meta in packets:
        src_ip = meta.get("src_ip")
        dst_ip = meta.get("dst_ip")
        if not src_ip or not dst_ip:
            continue

        # Only record connections FROM known devices (not just any passing traffic)
        device = db.get_device(ip=src_ip)
        if not device:
            continue

        geo_info = {}
        if geo_lookup_fn and not _is_private(dst_ip):
            geo_info = geo_lookup_fn(dst_ip) or {}

        db.add_connection(
            device_id    = device["id"],
            src_ip       = src_ip,
            dst_ip       = dst_ip,
            dst_port     = meta.get("dst_port"),
            protocol     = meta.get("protocol"),
            bytes_       = meta.get("bytes", 0),
            country      = geo_info.get("country"),
            country_code = geo_info.get("country_code"),
            isp          = geo_info.get("isp"),
            dns_query    = meta.get("dns_query"),
        )
