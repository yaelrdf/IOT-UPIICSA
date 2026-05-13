# REST API Documentation

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently no authentication required (intended for local-only use). For production, implement:
- JWT tokens
- OAuth 2.0
- API keys

## Response Format

All endpoints return JSON. Errors follow this format:

```json
{
  "error": "Error description"
}
```

## Endpoints

### System Health

#### GET `/api/health`
**Description**: Health check and system status

**Response**:
```json
{
  "status": "ok",
  "timestamp": "2026-05-12T14:30:45.123456",
  "stats": {
    "total_devices": 5,
    "blocked_devices": 1,
    "events_today": 12,
    "unacknowledged": 3,
    "critical_today": 1,
    "intel_ips": 45000,
    "intel_domains": 12000
  }
}
```

**Status Codes**:
- `200`: System is healthy
- `500`: System error

---

### Statistics

#### GET `/api/stats`
**Description**: Get current system statistics

**Response**:
```json
{
  "total_devices": 5,
  "blocked_devices": 1,
  "events_today": 12,
  "unacknowledged": 3,
  "critical_today": 1,
  "intel_ips": 45000,
  "intel_domains": 12000
}
```

---

### Devices

#### GET `/api/devices`
**Description**: Get all connected devices

**Query Parameters**:
- None

**Response**:
```json
[
  {
    "id": 1,
    "ip": "192.168.1.101",
    "mac": "aa:bb:cc:dd:ee:01",
    "vendor": "Samsung Electronics",
    "hostname": "smart-tv",
    "is_blocked": 0,
    "notes": "Living room TV",
    "first_seen": "2026-05-10T10:30:00",
    "last_seen": "2026-05-12T14:30:00",
    "events_today": 2,
    "total_events": 5
  }
]
```

---

#### GET `/api/devices/<device_id>`
**Description**: Get detailed information for a specific device

**Parameters**:
- `device_id` (integer, path): Device ID

**Response**:
```json
{
  "device": {
    "id": 1,
    "ip": "192.168.1.101",
    "mac": "aa:bb:cc:dd:ee:01",
    "vendor": "Samsung Electronics",
    "hostname": "smart-tv",
    "is_blocked": 0,
    "notes": "Living room TV",
    "first_seen": "2026-05-10T10:30:00",
    "last_seen": "2026-05-12T14:30:00"
  },
  "events": [
    {
      "id": 42,
      "event_type": "blacklist_ip",
      "severity": "high",
      "description": "Connection to known malicious IP",
      "timestamp": "2026-05-12T12:15:00"
    }
  ],
  "connections": [
    {
      "id": 123,
      "src_ip": "192.168.1.101",
      "dst_ip": "8.8.8.8",
      "dst_port": 53,
      "protocol": "UDP",
      "bytes": 512,
      "country": "United States",
      "country_code": "US",
      "isp": "Google",
      "dns_query": "example.com",
      "timestamp": "2026-05-12T14:25:00"
    }
  ]
}
```

---

#### POST `/api/devices/<device_id>/block`
**Description**: Block all traffic from a device

**Parameters**:
- `device_id` (integer, path): Device ID

**Response**:
```json
{
  "ok": true,
  "message": "Device 192.168.1.101 blocked"
}
```

**Status Codes**:
- `200`: Successfully blocked
- `404`: Device not found
- `400`: Error blocking device

---

#### POST `/api/devices/<device_id>/unblock`
**Description**: Unblock a previously blocked device

**Parameters**:
- `device_id` (integer, path): Device ID

**Response**:
```json
{
  "ok": true,
  "message": "Device 192.168.1.101 unblocked"
}
```

**Status Codes**:
- `200`: Successfully unblocked
- `404`: Device not found
- `400`: Error unblocking device

---

#### POST `/api/devices/<device_id>/note`
**Description**: Set or update notes for a device

**Parameters**:
- `device_id` (integer, path): Device ID

**Body**:
```json
{
  "note": "My device description"
}
```

**Response**:
```json
{
  "ok": true
}
```

---

### Events

#### GET `/api/events`
**Description**: Get security events with optional filtering

**Query Parameters**:
- `severity` (string): Filter by severity (`critical`, `high`, `medium`, `low`)
- `device_id` (integer): Filter by device ID
- `acknowledged` (boolean): Filter by acknowledgment status

**Examples**:
```
GET /api/events?severity=critical
GET /api/events?device_id=1
GET /api/events?acknowledged=false
```

**Response**:
```json
[
  {
    "id": 42,
    "device_id": 1,
    "device_ip": "192.168.1.101",
    "event_type": "blacklist_ip",
    "severity": "high",
    "description": "Connection to known malicious IP 91.108.56.77",
    "details": {
      "dst_ip": "91.108.56.77",
      "source": "feodo_tracker",
      "last_updated": "2026-05-12T00:00:00"
    },
    "acknowledged": 0,
    "timestamp": "2026-05-12T12:15:00"
  }
]
```

---

#### POST `/api/events/<event_id>/acknowledge`
**Description**: Mark an event as acknowledged

**Parameters**:
- `event_id` (integer, path): Event ID

**Response**:
```json
{
  "ok": true
}
```

**Status Codes**:
- `200`: Successfully acknowledged
- `400`: Error acknowledging event

---

### Connections

#### GET `/api/connections`
**Description**: Get network connections with optional filtering

**Query Parameters**:
- `device_id` (integer): Filter by device ID
- `minutes` (integer): Time window in minutes (default: 30)
- `limit` (integer): Maximum results (default: 200)

**Examples**:
```
GET /api/connections?device_id=1
GET /api/connections?minutes=60&limit=100
```

**Response**:
```json
[
  {
    "id": 123,
    "device_id": 1,
    "src_ip": "192.168.1.101",
    "dst_ip": "8.8.8.8",
    "dst_port": 53,
    "protocol": "UDP",
    "bytes": 512,
    "country": "United States",
    "country_code": "US",
    "isp": "Google",
    "dns_query": "example.com",
    "timestamp": "2026-05-12T14:25:00"
  }
]
```

---

### Threat Intelligence

#### GET `/api/intel/sources`
**Description**: Get threat intelligence source information

**Response**:
```json
{
  "sources": [
    {
      "source": "feodo_tracker",
      "type": "ip",
      "cnt": 45000,
      "updated": "2026-05-12T00:00:00"
    },
    {
      "source": "urlhaus_domains",
      "type": "domain",
      "cnt": 12000,
      "updated": "2026-05-12T00:00:00"
    }
  ],
  "counts": {
    "ip": 45000,
    "domain": 12000
  }
}
```

---

## Error Handling

### Common Errors

**404 Not Found**:
```json
{
  "error": "Not found"
}
```

**500 Internal Server Error**:
```json
{
  "error": "Internal server error"
}
```

### Status Codes

| Code | Meaning |
|------|---------|
| 200  | OK - Request successful |
| 400  | Bad Request - Invalid parameters |
| 404  | Not Found - Resource doesn't exist |
| 500  | Internal Server Error - Server error |

---

## Examples

### Get all events from today
```bash
curl "http://localhost:5000/api/events" \
  -H "Accept: application/json" | jq '.'
```

### Block a device
```bash
curl -X POST "http://localhost:5000/api/devices/1/block" \
  -H "Content-Type: application/json"
```

### Get high-severity events
```bash
curl "http://localhost:5000/api/events?severity=high" \
  -H "Accept: application/json" | jq '.[] | {device_ip, event_type, description}'
```

### Get events for specific device
```bash
curl "http://localhost:5000/api/events?device_id=1" \
  -H "Accept: application/json" | jq '.[] | {timestamp, event_type, severity}'
```

### Acknowledge an event
```bash
curl -X POST "http://localhost:5000/api/events/42/acknowledge" \
  -H "Content-Type: application/json"
```

### Get system health
```bash
curl "http://localhost:5000/api/health" \
  -H "Accept: application/json" | jq '.stats'
```

---

## Rate Limiting

Currently no rate limiting implemented. For production:
- Implement Flask-Limiter
- Limit: 100 requests/minute per IP
- Burst: 10 requests/second

---

## Webhooks (Future)

Planned for future releases:
- Event webhooks
- Custom callbacks on detection
- Integration with external systems

---

## Changelog

### Version 1.0.0
- Initial API release
- All core endpoints implemented
- Event filtering and device management
- Threat intelligence status

---

## Support

For API issues or questions:
1. Check [README.md](README.md) for configuration
2. Review [DEVELOPMENT.md](DEVELOPMENT.md) for debugging
3. Check logs: `tail -f data/monitor.log`

---

**Last Updated**: May 2026  
**API Version**: 1.0.0
