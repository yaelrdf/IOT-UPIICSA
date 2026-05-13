"""
Alerter — sends email notifications for high-severity events.
Uses standard smtplib so no extra dependencies needed.
"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict

log = logging.getLogger(__name__)

# Severity badge colors for HTML email
_SEV_COLOR = {
    "low":      "#0dcaf0",
    "medium":   "#ffc107",
    "high":     "#fd7e14",
    "critical": "#dc3545",
}


class Alerter:
    def __init__(self, config, db):
        self.cfg = config
        self.db  = db

    def should_alert(self, severity: str) -> bool:
        return (self.cfg.email.enabled and
                severity in self.cfg.email.alert_on_severity)

    def send_event_email(self, event: Dict, device: Dict = None):
        """Send a single-event alert email."""
        if not self.cfg.email.enabled:
            return
        subject = f"[IoT Monitor] {event['severity'].upper()}: {event['event_type']}"
        body    = self._build_event_html(event, device)
        self._send(subject, body)

    def send_digest(self, events: List[Dict]):
        """Send a digest of multiple events (used for batched alerts)."""
        if not self.cfg.email.enabled or not events:
            return
        subject = f"[IoT Monitor] {len(events)} alert(s) — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        body    = self._build_digest_html(events)
        self._send(subject, body)

    # ── private ───────────────────────────────────────────────────────────────

    def _send(self, subject: str, html_body: str):
        cfg = self.cfg.email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = cfg.sender_email
        msg["To"]      = cfg.recipient_email
        msg.attach(MIMEText(html_body, "html"))

        try:
            if cfg.use_ssl:
                ctx = ssl.create_default_context()
                with smtplib.SMTP_SSL(cfg.smtp_server, cfg.smtp_port, context=ctx) as s:
                    s.login(cfg.sender_email, cfg.sender_password)
                    s.send_message(msg)
            else:
                with smtplib.SMTP(cfg.smtp_server, cfg.smtp_port) as s:
                    s.starttls()
                    s.login(cfg.sender_email, cfg.sender_password)
                    s.send_message(msg)
            log.info("Alert email sent: %s", subject)
        except Exception as e:
            log.error("Email send failed: %s", e)

    def _build_event_html(self, event: Dict, device: Dict = None) -> str:
        sev   = event.get("severity", "low")
        color = _SEV_COLOR.get(sev, "#6c757d")
        dev_info = ""
        if device:
            dev_info = f"<p><b>Device:</b> {device.get('ip')} ({device.get('vendor','?')})</p>"
        return f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;max-width:600px">
        <div style="background:{color};color:#fff;padding:12px 20px;border-radius:6px 6px 0 0">
            <h2 style="margin:0">⚠️ IoT Monitor Alert</h2>
        </div>
        <div style="border:1px solid #ddd;border-top:0;padding:20px;border-radius:0 0 6px 6px">
            <p><b>Type:</b>
              <span style="background:{color};color:#fff;padding:2px 8px;border-radius:3px">
                {event.get('event_type','?').replace('_',' ').title()}
              </span>
            </p>
            <p><b>Severity:</b> {sev.upper()}</p>
            {dev_info}
            <p><b>Description:</b> {event.get('description','')}</p>
            <p><b>Time:</b> {event.get('timestamp','')}</p>
            <hr>
            <p style="font-size:12px;color:#888">
                IoT Network Security Monitor · Dashboard at http://localhost:5000
            </p>
        </div>
        </body></html>"""

    def _build_digest_html(self, events: List[Dict]) -> str:
        rows = ""
        for ev in events:
            sev   = ev.get("severity", "low")
            color = _SEV_COLOR.get(sev, "#6c757d")
            rows += f"""
            <tr>
              <td style="padding:8px;border-bottom:1px solid #eee">
                <span style="background:{color};color:#fff;padding:2px 6px;border-radius:3px;font-size:12px">
                  {sev.upper()}
                </span>
              </td>
              <td style="padding:8px;border-bottom:1px solid #eee">{ev.get('device_ip','?')}</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{ev.get('event_type','').replace('_',' ').title()}</td>
              <td style="padding:8px;border-bottom:1px solid #eee;font-size:12px">{ev.get('description','')[:100]}</td>
            </tr>"""
        return f"""
        <html><body style="font-family:Arial,sans-serif;color:#333;max-width:700px">
        <div style="background:#1a1a2e;color:#fff;padding:12px 20px;border-radius:6px 6px 0 0">
            <h2 style="margin:0">🛡️ IoT Monitor Digest — {len(events)} Alert(s)</h2>
        </div>
        <div style="border:1px solid #ddd;border-top:0;padding:20px;border-radius:0 0 6px 6px">
            <table width="100%" style="border-collapse:collapse">
              <thead>
                <tr style="background:#f8f9fa">
                  <th style="padding:8px;text-align:left">Severity</th>
                  <th style="padding:8px;text-align:left">Device</th>
                  <th style="padding:8px;text-align:left">Type</th>
                  <th style="padding:8px;text-align:left">Description</th>
                </tr>
              </thead>
              <tbody>{rows}</tbody>
            </table>
            <p style="font-size:12px;color:#888;margin-top:16px">
                View full details at http://localhost:5000
            </p>
        </div>
        </body></html>"""
