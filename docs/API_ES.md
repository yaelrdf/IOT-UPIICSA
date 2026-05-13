# Documentación de API REST

## Base URL

```
http://localhost:5000
```

## Autenticación

Actualmente sin autenticación (se recomienda añadir en producción).

## Formato de Respuesta

Todas las respuestas están en JSON.

## Códigos de Estado HTTP

| Código | Significado |
|--------|------------|
| 200 | Éxito |
| 400 | Solicitud inválida |
| 404 | Recurso no encontrado |
| 500 | Error del servidor |

---

## Endpoints

### GET /api/stats

Obtiene estadísticas generales del sistema.

**Ejemplo:**
```bash
curl http://localhost:5000/api/stats
```

**Respuesta:**
```json
{
  "total_devices": 12,
  "blocked_devices": 2,
  "events_today": 45,
  "critical_today": 3,
  "unacknowledged": 7,
  "intel_ips": 50000,
  "intel_domains": 25000,
  "database_size_mb": 15.3
}
```

---

### GET /api/devices

Obtiene lista de todos los dispositivos detectados.

**Parámetros:**
- `limit` (opcional): Número máximo de resultados (default: 100)
- `offset` (opcional): Desplazamiento para paginación (default: 0)

**Ejemplo:**
```bash
curl "http://localhost:5000/api/devices?limit=20"
```

**Respuesta:**
```json
{
  "success": true,
  "devices": [
    {
      "ip": "192.168.1.5",
      "mac": "AA:BB:CC:DD:EE:FF",
      "vendor": "Apple Inc.",
      "hostname": "iphone-usuario",
      "first_seen": "2026-05-12T10:30:00",
      "last_seen": "2026-05-12T23:36:40",
      "is_blocked": false,
      "events_today": 3,
      "total_events": 45
    },
    {
      "ip": "192.168.1.10",
      "mac": "11:22:33:44:55:66",
      "vendor": "Amazon.com Inc.",
      "hostname": "alexa-casa",
      "first_seen": "2026-04-15T08:00:00",
      "last_seen": "2026-05-12T23:35:00",
      "is_blocked": true,
      "events_today": 0,
      "total_events": 12
    }
  ],
  "total": 12
}
```

---

### POST /api/devices/{ip}/block

Bloquea un dispositivo (lo coloca en la lista de bloqueo).

**Parámetros de Ruta:**
- `ip`: Dirección IP del dispositivo a bloquear

**Ejemplo:**
```bash
curl -X POST http://localhost:5000/api/devices/192.168.1.5/block
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Dispositivo 192.168.1.5 bloqueado exitosamente",
  "device": {
    "ip": "192.168.1.5",
    "is_blocked": true
  }
}
```

---

### POST /api/devices/{ip}/unblock

Desbloquea un dispositivo (lo quita de la lista de bloqueo).

**Parámetros de Ruta:**
- `ip`: Dirección IP del dispositivo a desbloquear

**Ejemplo:**
```bash
curl -X POST http://localhost:5000/api/devices/192.168.1.10/unblock
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Dispositivo 192.168.1.10 desbloqueado exitosamente",
  "device": {
    "ip": "192.168.1.10",
    "is_blocked": false
  }
}
```

---

### GET /api/events

Obtiene registro de eventos de seguridad.

**Parámetros:**
- `limit` (opcional): Número máximo de resultados (default: 100, máximo: 500)
- `offset` (opcional): Desplazamiento para paginación (default: 0)
- `severity` (opcional): Filtrar por severidad (critical, high, medium, low)
- `device_ip` (opcional): Filtrar por IP de dispositivo
- `type` (opcional): Filtrar por tipo de evento
- `acknowledged` (opcional): Filtrar por estado (true/false)

**Ejemplo con Filtros:**
```bash
curl "http://localhost:5000/api/events?severity=critical&limit=50&acknowledged=false"
```

**Respuesta:**
```json
{
  "success": true,
  "events": [
    {
      "id": 1,
      "timestamp": "2026-05-12T23:30:45",
      "type": "BLACKLIST_IP",
      "severity": "CRITICAL",
      "device_ip": "192.168.1.5",
      "description": "Conexión a IP maliciosa 10.0.0.99",
      "acknowledged": false
    },
    {
      "id": 2,
      "timestamp": "2026-05-12T23:25:10",
      "type": "BEACONING",
      "severity": "HIGH",
      "device_ip": "192.168.1.7",
      "description": "Actividad de beacon detectada a 10.0.0.50:8080",
      "acknowledged": true
    }
  ],
  "total": 45
}
```

---

### POST /api/events/{id}/acknowledge

Marca un evento como reconocido (leído).

**Parámetros de Ruta:**
- `id`: ID del evento a reconocer

**Ejemplo:**
```bash
curl -X POST http://localhost:5000/api/events/1/acknowledge
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Evento 1 marcado como reconocido",
  "event": {
    "id": 1,
    "acknowledged": true,
    "acknowledged_at": "2026-05-12T23:40:00"
  }
}
```

---

### GET /api/connections

Obtiene las conexiones de red capturadas.

**Parámetros:**
- `limit` (opcional): Número máximo (default: 100, máximo: 1000)
- `offset` (opcional): Desplazamiento (default: 0)
- `source_ip` (opcional): Filtrar por IP origen
- `dest_ip` (opcional): Filtrar por IP destino
- `hours` (opcional): Últimas N horas (default: 24)

**Ejemplo:**
```bash
curl "http://localhost:5000/api/connections?source_ip=192.168.1.5&hours=1"
```

**Respuesta:**
```json
{
  "success": true,
  "connections": [
    {
      "src_ip": "192.168.1.5",
      "dest_ip": "8.8.8.8",
      "dest_port": 53,
      "protocol": "UDP",
      "timestamp": "2026-05-12T23:35:00"
    },
    {
      "src_ip": "192.168.1.5",
      "dest_ip": "142.250.80.46",
      "dest_port": 443,
      "protocol": "TCP",
      "timestamp": "2026-05-12T23:36:00"
    }
  ],
  "total": 45
}
```

---

### GET /api/intel/sources

Obtiene estado de las fuentes de inteligencia de amenazas.

**Ejemplo:**
```bash
curl http://localhost:5000/api/intel/sources
```

**Respuesta:**
```json
{
  "success": true,
  "sources": [
    {
      "name": "abuse.ch Feodo",
      "type": "ips",
      "url": "https://feodotracker.abuse.ch",
      "enabled": true,
      "ips_count": 5432,
      "domains_count": 0,
      "last_update": "2026-05-12T00:00:00",
      "status": "active"
    },
    {
      "name": "URLhaus Malware IPs",
      "type": "ips",
      "url": "https://urlhaus.abuse.ch",
      "enabled": true,
      "ips_count": 8921,
      "domains_count": 0,
      "last_update": "2026-05-12T00:00:00",
      "status": "active"
    },
    {
      "name": "URLhaus Domains",
      "type": "domains",
      "url": "https://urlhaus.abuse.ch",
      "enabled": true,
      "ips_count": 0,
      "domains_count": 12543,
      "last_update": "2026-05-12T00:00:00",
      "status": "active"
    }
  ],
  "total_ips": 35689,
  "total_domains": 12543
}
```

---

### POST /api/intel/refresh

Actualiza todas las fuentes de inteligencia de amenazas.

**Nota:** Esto puede tomar varios minutos. Se ejecuta asincrónico.

**Ejemplo:**
```bash
curl -X POST http://localhost:5000/api/intel/refresh
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Actualización de inteligencia iniciada",
  "status": "updating",
  "sources_queued": 5
}
```

---

### GET /api/health

Verifica el estado general del sistema.

**Ejemplo:**
```bash
curl http://localhost:5000/api/health
```

**Respuesta:**
```json
{
  "success": true,
  "status": "healthy",
  "components": {
    "database": "ok",
    "scheduler": "ok",
    "threat_intel": "ok",
    "packet_capture": "ok"
  },
  "uptime_seconds": 3600
}
```

---

## Códigos de Tipo de Evento

| Código | Descripción | Severidad |
|--------|------------|-----------|
| NEW_DEVICE | Dispositivo nuevo detectado | 🟢 Baja |
| BLACKLIST_IP | Conexión a IP en lista negra | 🔴 Crítica |
| BLACKLIST_DOMAIN | Conexión a dominio en lista negra | 🔴 Crítica |
| BEACONING | Actividad de beacon detectada | 🟠 Alta |
| GEO_ANOMALY | Conexión a ubicación anómala | 🟡 Media |
| HIGH_VOLUME | Alto volumen de datos detectado | 🟡 Media |

---

## Códigos de Severidad

| Código | Color | Valor |
|--------|-------|-------|
| CRITICAL | 🔴 Rojo | 4 |
| HIGH | 🟠 Naranja | 3 |
| MEDIUM | 🟡 Amarillo | 2 |
| LOW | 🟢 Verde | 1 |

---

## Ejemplo de Cliente Python

```python
import requests
import json

BASE_URL = "http://localhost:5000"

# Obtener estadísticas
response = requests.get(f"{BASE_URL}/api/stats")
stats = response.json()
print(f"Dispositivos: {stats['total_devices']}")
print(f"Eventos críticos hoy: {stats['critical_today']}")

# Obtener dispositivos
response = requests.get(f"{BASE_URL}/api/devices")
devices = response.json()['devices']
for device in devices:
    print(f"{device['ip']} - {device['vendor']}")

# Bloquear un dispositivo
response = requests.post(f"{BASE_URL}/api/devices/192.168.1.5/block")
result = response.json()
print(f"Bloqueado: {result['success']}")

# Obtener eventos críticos
response = requests.get(
    f"{BASE_URL}/api/events",
    params={"severity": "critical", "limit": 10}
)
events = response.json()['events']
for event in events:
    print(f"{event['timestamp']} - {event['description']}")
```

---

## Ejemplo de Cliente CURL Avanzado

```bash
#!/bin/bash

BASE_URL="http://localhost:5000"

# Obtener todos los dispositivos
echo "=== Dispositivos ==="
curl -s "${BASE_URL}/api/devices" | jq '.devices[] | {ip, vendor, is_blocked}'

# Obtener eventos críticos de hoy
echo -e "\n=== Eventos Críticos ==="
curl -s "${BASE_URL}/api/events?severity=critical" | jq '.events[] | {timestamp, description}'

# Bloquear dispositivo
echo -e "\n=== Bloqueando dispositivo ==="
curl -X POST "${BASE_URL}/api/devices/192.168.1.5/block" | jq .

# Ver fuentes de amenazas
echo -e "\n=== Fuentes de Inteligencia ==="
curl -s "${BASE_URL}/api/intel/sources" | jq '.sources[] | {name, ips_count, last_update}'
```

---

## Límites y Rate Limiting

- Máximo 1000 resultados por solicitud
- Sin rate limiting por IP en desarrollo
- Se recomienda implementar en producción

---

## Cambios Planeados

- [ ] Autenticación JWT
- [ ] Rate limiting
- [ ] Paginación mejorada
- [ ] Webhooks
- [ ] GraphQL API

---

**Última actualización:** Mayo 12, 2026  
**Versión API:** 1.0
