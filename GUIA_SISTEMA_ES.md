# Guía Completa del Sistema Monitor de Seguridad IoT

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [¿Cómo Funciona?](#cómo-funciona)
3. [Componentes del Sistema](#componentes-del-sistema)
4. [Arquitectura](#arquitectura)
5. [Tipos de Detección](#tipos-de-detección)
6. [Instalación y Configuración](#instalación-y-configuración)
7. [Interfaz Web](#interfaz-web)
8. [API REST](#api-rest)
9. [Mantenimiento y Troubleshooting](#mantenimiento-y-troubleshooting)

---

## Introducción

El **Monitor de Seguridad IoT** es un sistema de bajo costo basado en Raspberry Pi que detecta comportamiento malicioso y anómalo en redes IoT domésticas. 

### Características Principales

✅ **Descubrimiento Automático de Dispositivos** - Detecta todos los dispositivos en la red mediante escaneo ARP  
✅ **Análisis de Metadata de Paquetes** - Captura y analiza metadatos de red (nunca contenido de datos)  
✅ **Integración de Listas Negras** - Verifica conexiones contra listas de IPs y dominios maliciosos  
✅ **Detección de Beacon** - Identifica conexiones regulares típicas de botnets  
✅ **Detección de Anomalías Geográficas** - Alerta sobre conexiones a países sospechosos  
✅ **Detección de Alto Volumen** - Detecta cuando dispositivos envían cantidades inusuales de datos  
✅ **Alertas por Email** - Notificaciones en tiempo real para eventos de alta severidad  
✅ **Panel Web Interactivo** - Dashboard completo para monitoreo y gestión  
✅ **Modo Activo (Opcional)** - ARP spoofing para bloquear tráfico de dispositivos comprometidos  

---

## ¿Cómo Funciona?

### Flujo de Trabajo General

```
1. DETECCIÓN (Discovery)
   └─ Scanner detecta dispositivos en la red via ARP
   └─ Base de datos almacena información de cada dispositivo
   └─ Se genera evento NEW_DEVICE para dispositivos nuevos

2. CAPTURA (Capture)
   └─ Packet Capture intercepta paquetes en modo promiscuo
   └─ Se extraen metadatos: IPs origen/destino, puertos, protocolos
   └─ Se almacenan conexiones en la base de datos

3. ANÁLISIS (Analysis)
   └─ El Analyzer ejecuta 5 reglas de detección en paralelo:
   
   A) Verificación de Lista Negra de IPs
      └─ ¿Es la IP de destino conocida como maliciosa?
      └─ Se consulta la base de datos de inteligencia de amenazas
      
   B) Verificación de Lista Negra de Dominios
      └─ ¿Aparece una petición a un dominio malicioso?
      └─ Se analizan consultas DNS capturadas
      
   C) Detección de Beacon (Botnet C&C)
      └─ ¿El dispositivo intenta conectarse regularmente a la misma IP:puerto?
      └─ Algoritmo: Calcula variación de intervalo entre conexiones
      └─ Si CV < 0.20 = comportamiento de beacon
      
   D) Detección de Anomalía Geográfica
      └─ ¿El dispositivo se conecta a una ubicación inusual?
      └─ Se realiza geolocalización IP y se compara con patrón histórico
      
   E) Detección de Alto Volumen
      └─ ¿El dispositivo envía una cantidad anormal de datos?
      └─ Se calcula promedio y se alerta si supera threshold

4. ALERTAS (Alerting)
   └─ Los eventos de alta severidad generan alertas por email
   └─ Todos los eventos se almacenan en la base de datos
   └─ El dashboard muestra todos los eventos en tiempo real

5. ACCIÓN (Action)
   └─ El usuario puede bloquear un dispositivo mediante ARP spoofing
   └─ En modo activo, el Spoofer envena el caché ARP
   └─ El dispositivo malicioso pierde conexión a internet
```

### Proceso de Detección de Beacon (Ejemplo Detallado)

```
IP: 192.168.1.5  (Smart TV comprometido)
Destino: 10.0.0.50:8080 (C&C del botnet)

Conexión 1: 14:30:00
Conexión 2: 14:30:30 (intervalo: 30 segundos)
Conexión 3: 14:31:00 (intervalo: 30 segundos)
Conexión 4: 14:31:30 (intervalo: 30 segundos)
Conexión 5: 14:32:00 (intervalo: 30 segundos)

Análisis:
- Media de intervalos: 30 segundos
- Desviación estándar: ≈0 (muy consistente)
- Coeficiente de Variación = StdDev / Media = 0 / 30 = 0.0
- 0.0 < 0.20 = ¡COMPORTAMIENTO DE BEACON DETECTADO!
- Severidad: CRÍTICA
- Acción: Generar alerta, enviar email, almacenar en BD

VS. Comportamiento Normal:

IP: 192.168.1.10  (Usuario navegando)
Destino: múltiples IPs (google.com, youtube.com, etc)

Conexión 1: 14:30:00 a google.com
Conexión 2: 14:30:45 a youtube.com (intervalo: 45 segundos)
Conexión 3: 14:32:20 a facebook.com (intervalo: 95 segundos)
Conexión 4: 14:34:10 a reddit.com (intervalo: 110 segundos)

Análisis:
- Intervalos: [45, 95, 110] segundos
- Media: 83.33 segundos
- Desviación: muy alta
- Coeficiente de Variación = 0.45
- 0.45 > 0.20 = Comportamiento normal, sin alerta
```

---

## Componentes del Sistema

### 1. **Scanner** (scanner.py)
Responsable de descubrir dispositivos en la red.

**Funciones Clave:**
- `arp_scan()`: Ejecuta escaneo ARP para descubrir dispositivos
- `resolve_hostname()`: Intenta resolver nombre de host para cada IP
- `run_discovery()`: Ejecuta el proceso completo de descubrimiento

**Proceso:**
1. Envía peticiones ARP a todas las IPs en la subred
2. Recibe respuestas ARP con MAC address y datos del proveedor
3. Realiza búsqueda OUI (Organizationally Unique Identifier) para identificar fabricante
4. Almacena dispositivo en base de datos

**Evento Generado:** `NEW_DEVICE` si es la primera vez que ve el dispositivo

---

### 2. **Capture** (capture.py)
Captura paquetes de red en modo promiscuo.

**Funciones Clave:**
- `start()`: Inicia captura de paquetes en thread separado
- `_sniff_loop()`: Loop principal de captura
- `_handle_packet()`: Procesa cada paquete capturado
- `block_ip()`: Activa bloqueo de una IP mediante ARP spoofing

**Datos Extraídos:**
- IP origen y destino
- Puertos origen y destino
- Protocolo (TCP, UDP, ICMP)
- Consultas DNS (si aplica)
- Timestamp

**Base de Datos:**
- Tabla `connections`: almacena cada conexión única
- Nunca captura contenido de payload (solo metadatos)

---

### 3. **Analyzer** (analyzer.py)
Motor de detección que ejecuta todas las reglas.

**5 Reglas de Detección:**

#### A) Verificación de Lista Negra de IPs
```python
def _check_blacklist_ips(self, conn):
    # ¿Es la IP de destino maliciosa?
    threat = self.threat_intel.check_ip(dest_ip)
    if threat:
        self.db.add_event(
            type=EventType.BLACKLIST_IP,
            severity=Severity.CRITICAL,
            device_ip=src_ip,
            description=f"Conexión a IP maliciosa {dest_ip} ({threat})"
        )
```

#### B) Verificación de Lista Negra de Dominios
```python
def _check_blacklist_domains(self, conn):
    # ¿Es el dominio malicioso?
    if conn.dns_name:
        threat = self.threat_intel.check_domain(conn.dns_name)
        if threat:
            self.db.add_event(
                type=EventType.BLACKLIST_DOMAIN,
                severity=Severity.CRITICAL,
                device_ip=src_ip,
                description=f"Conexión a dominio malicioso {conn.dns_name}"
            )
```

#### C) Detección de Beacon
```python
def _check_beaconing(self, conn):
    # Agrupa conexiones por (dest_ip, port)
    # Calcula intervalos entre conexiones
    # Calcula Coeficiente de Variación
    # Si CV < 0.20 = comportamiento de beacon
    
    cv = stddev(intervals) / mean(intervals)
    if cv < 0.20:
        self.db.add_event(
            type=EventType.BEACONING,
            severity=Severity.HIGH,
            device_ip=src_ip,
            description=f"Actividad de beacon detectada a {dest_ip}:{port}"
        )
```

#### D) Detección de Anomalía Geográfica
```python
def _check_geo_anomaly(self, conn):
    # Realiza geolocalización del destino
    # Compara con ubicación histórica del dispositivo
    # Si la ubicación es muy diferente = anomalía
    
    location = self.threat_intel.geo_lookup(dest_ip)
    if location differs from historical pattern:
        self.db.add_event(
            type=EventType.GEO_ANOMALY,
            severity=Severity.MEDIUM,
            device_ip=src_ip,
            description=f"Conexión a ubicación inusual: {location}"
        )
```

#### E) Detección de Alto Volumen
```python
def _check_high_volume(self, device_ip):
    # Calcula bytes por hora
    # Compara con promedio histórico
    # Si supera 2x el promedio = alto volumen
    
    current_rate = calculate_bytes_per_hour(device_ip)
    avg_rate = get_historical_average(device_ip)
    if current_rate > 2 * avg_rate:
        self.db.add_event(
            type=EventType.HIGH_VOLUME,
            severity=Severity.MEDIUM,
            device_ip=device_ip,
            description=f"Alto volumen de datos: {current_rate} bytes/hora"
        )
```

---

### 4. **Threat Intel** (threat_intel.py)
Gestión de listas negras e inteligencia de amenazas.

**Fuentes Integradas:**
1. **abuse.ch Feodo Tracker** - Botnet C&C IPs
2. **URLhaus Malware IPs** - IPs distribuidoras de malware
3. **Botnet IPs** - Servidores de comando y control
4. **Emerging Threats** - Amenazas emergentes
5. **URLhaus Domains** - Dominios maliciosos

**Funciones Clave:**
- `update_all()`: Descarga listas de todas las fuentes
- `check_ip(ip)`: Verifica si una IP está en lista negra
- `check_domain(domain)`: Verifica si dominio está en lista negra
- `geo_lookup(ip)`: Obtiene ubicación geográfica (rate-limited a 45 req/min)

**Caching:**
- Las listas se almacenan en tabla `threat_intel` de la BD
- Las geolocalización se cachean en tabla `geo_cache`
- Las listas se actualizan cada 24 horas automáticamente

---

### 5. **Database** (database.py)
Almacenamiento persistente con SQLite3.

**Tablas:**

| Tabla | Propósito | Campos Clave |
|-------|-----------|--------------|
| `devices` | Todos los dispositivos detectados | ip, mac, vendor, hostname, first_seen, last_seen, is_blocked |
| `events` | Eventos de seguridad | id, timestamp, type, severity, device_ip, description, acknowledged |
| `connections` | Conexiones de red | src_ip, dest_ip, dest_port, protocol, timestamp |
| `threat_intel` | Cache de listas negras | ip/domain, threat_source, timestamp |
| `geo_cache` | Cache de geolocalización | ip, country, city, timestamp |

**Características:**
- Thread-safe con `threading.local()`
- Soporta scheduler y Flask simultáneamente
- Limpieza automática de datos antiguos

---

### 6. **Alerter** (alerter.py)
Sistema de alertas por email.

**Funciones Clave:**
- `send_event_email()`: Envía alerta de un evento crítico
- `send_digest()`: Envía resumen diario de eventos

**Configuración:**
```yaml
email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  from_address: your-email@gmail.com
  password: your-app-password
  recipients:
    - admin@example.com
```

**Formato:**
- HTML formateado con colores por severidad
- Incluye detalles del evento
- Resumen de últimas 24 horas en digest

---

### 7. **Spoofer** (spoofer.py)
ARP spoofing para bloqueo activo de dispositivos.

**Funciones Clave:**
- `start()`: Comienza el envenenamiento ARP
- `add_target(target_ip)`: Añade dispositivo a lista de bloqueo
- `remove_target(target_ip)`: Quita dispositivo de bloqueo
- `_restore_target()`: Restaura caché ARP cuando se detiene

**Cómo Funciona:**
1. El spoofer se posiciona como man-in-the-middle (MITM)
2. Envía paquetes ARP falsos diciendo que es el gateway
3. El dispositivo bloqueado intenta conectarse al "gateway" (el spoofer)
4. El spoofer rechaza las conexiones o las redirige
5. Cuando se detiene, se envía ARP de restauración

**Requisitos:**
- Necesita privilegios de root
- IP forwarding habilitado
- En la subred del gateway

---

### 8. **Web** (web.py)
Interfaz web Flask y REST API.

**Endpoints Principales:**

```
GET  /                          - Panel de control
GET  /devices                   - Lista de dispositivos
GET  /events                    - Registro de eventos
GET  /threat_intel              - Estado de inteligencia de amenazas

POST /api/devices/{ip}/block    - Bloquear dispositivo
POST /api/devices/{ip}/unblock  - Desbloquear dispositivo
POST /api/events/{id}/acknowledge - Reconocer evento

GET  /api/stats                 - Estadísticas del sistema
GET  /api/devices               - JSON de dispositivos
GET  /api/events                - JSON de eventos
GET  /api/connections           - Conexiones de red
GET  /api/intel/sources         - Estado de fuentes de intel
```

**Autenticación:**
- Las versiones en producción deberían añadir autenticación
- Actualmente acceso abierto (en desarrollo)

---

### 9. **Monitor** (monitor.py)
Punto de entrada principal que coordina todo.

**Responsabilidades:**
- Carga configuración desde `config.yaml`
- Inicializa base de datos
- Crea scheduler de tareas en background
- Inicia servidor web Flask
- Maneja señales de interrupción (Ctrl+C)

**Modos de Ejecución:**
```bash
python3 monitor.py              # Modo normal
python3 monitor.py -d           # Modo demo (con datos de ejemplo)
python3 monitor.py -c custom.yaml # Configuración personalizada
```

---

## Arquitectura

### Diagrama en 3 Capas

```
┌─────────────────────────────────────────────────────────────┐
│              CAPA DE APLICACIÓN (Web & API)                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Flask Web Server                                    │   │
│  │ • Dashboard Interactivo                             │   │
│  │ • REST API (10+ endpoints)                          │   │
│  │ • Gestión de Dispositivos                           │   │
│  │ • Visualización de Eventos                          │   │
│  │ • Estado de Inteligencia de Amenazas                │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│         CAPA DE PROCESAMIENTO (Análisis & Decisiones)       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Scheduler (APScheduler)                             │   │
│  │ • Task: Descubrimiento de dispositivos (5 min)      │   │
│  │ • Task: Captura de tráfico (10 min)                 │   │
│  │ • Task: Actualización de intel (24 horas)           │   │
│  │ • Task: Limpieza de datos (1 hora)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Analyzer Engine                                      │   │
│  │ • 5 Reglas de detección en paralelo                 │   │
│  │ • Genera eventos de seguridad                        │   │
│  │ • Alertas por email para eventos críticos           │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│        CAPA DE PERCEPCIÓN (Captura de Red)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Packet Capture (Scapy)                              │   │
│  │ • Sniffing en modo promiscuo                        │   │
│  │ • Extracción de metadatos                           │   │
│  │ • Captura DNS                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ARP Scanner                                          │   │
│  │ • Descubrimiento de dispositivos                    │   │
│  │ • Búsqueda de fabricante (OUI)                      │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ARP Spoofer                                          │   │
│  │ • Envenenamiento ARP (MITM)                         │   │
│  │ • Bloqueo de dispositivos                           │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│         ALMACENAMIENTO PERSISTENTE (SQLite3)                │
│  • Dispositivos, Eventos, Conexiones                        │
│  • Cache de Inteligencia de Amenazas                        │
│  • Cache de Geolocalización                                 │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
Interface de Red
     ↓
Packet Capture → Metadatos → Base de Datos (connections)
     ↓                              ↓
Analyzer ← ← ← ← ← ← ← ← ← ← ← ← 
     ↓
5 Reglas de Detección
     ↓
Eventos Generados → Base de Datos (events)
     ↓
¿Severidad CRÍTICA? → Sí → Alerter → Email
     ↓
Dashboard Web Actualizado (en tiempo real)
     ↓
Usuario revisa y toma acciones (bloquear, reconocer)
```

---

## Tipos de Detección

### 1. Verificación de Lista Negra de IPs
**Severidad:** 🔴 CRÍTICA  
**Cómo funciona:** Compara IP de destino contra lista de IPs maliciosas conocidas  
**Fuentes:** abuse.ch Feodo, URLhaus, Emerging Threats  
**Ejemplo:** `192.168.1.5 → 10.0.0.99:80` donde 10.0.0.99 es conocido botnet C&C  

### 2. Verificación de Lista Negra de Dominios
**Severidad:** 🔴 CRÍTICA  
**Cómo funciona:** Analiza consultas DNS, compara dominio contra lista negra  
**Fuentes:** URLhaus, Emerging Threats  
**Ejemplo:** `192.168.1.5 → malware-distribution.ru` (dominio en lista negra)  

### 3. Detección de Beacon
**Severidad:** 🟠 ALTA  
**Cómo funciona:** Identifica patrones regulares de conexión (botnet C&C check-in)  
**Algoritmo:** Coeficiente de Variación de intervalos < 0.20  
**Ejemplo:** Smart TV se conecta a `10.0.0.50:8080` cada 30 segundos (CV=0.0)  

### 4. Detección de Anomalía Geográfica
**Severidad:** 🟡 MEDIA  
**Cómo funciona:** Realiza geolocalización de IP, compara con patrón histórico  
**Algoritmo:** Si ubicación varía significativamente de conexiones anteriores  
**Ejemplo:** `192.168.1.10 → IP en China` (usuario normalmente en México)  

### 5. Detección de Alto Volumen
**Severidad:** 🟡 MEDIA  
**Cómo funciona:** Monitorea bytes enviados/recibidos, alerta si supera promedio  
**Umbral:** 2x el promedio histórico  
**Ejemplo:** Dispositivo normalmente envía 10MB/hora, ahora envía 50MB/hora  

---

## Instalación y Configuración

### 1. Crear Entorno Virtual

```bash
cd /home/yaeladmin/git/IOT-UPIICSA
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Paquetes necesarios:**
- `scapy>=2.5.0` - Captura y análisis de paquetes
- `flask>=3.0.0` - Servidor web
- `apscheduler>=3.10.0` - Scheduler de tareas
- `requests>=2.31.0` - Descargar fuentes de intel
- `pyyaml>=6.0.0` - Parsear configuración
- `python-nmap>=0.7.1` - Escaneo de red

### 3. Configurar config.yaml

```yaml
network:
  interface: eth0           # Interfaz de red a monitorear
  mode: passive             # passive o active (MITM)
  gateway: 192.168.1.1      # IP del gateway
  subnet: 192.168.1.0/24    # Subred a monitorear

scan:
  discovery_interval_sec: 300      # Descubrimiento cada 5 min
  capture_interval_sec: 600        # Captura cada 10 min
  max_connections_db: 100000       # Límite de conexiones en BD

email:
  smtp_server: smtp.gmail.com      # Servidor SMTP
  smtp_port: 587                   # Puerto SMTP
  from_address: tu-email@gmail.com # Email remitente
  password: tu-app-password        # Contraseña de app
  recipients:
    - admin@ejemplo.com            # Destinatarios

thresholds:
  high_volume_multiplier: 2.0      # Múltiplo para alto volumen
  beaconing_cv_threshold: 0.20     # CV para detectar beacon
  geo_anomaly_distance_km: 1000    # Distancia para anomalía

threat_intel:
  auto_update: true
  update_interval_hours: 24
  sources:
    - name: abuse.ch Feodo
      type: ips
      url: https://abuse.ch/api
    - name: URLhaus Malware IPs
      type: ips
      url: https://urlhaus.abuse.ch/api

web:
  host: 0.0.0.0
  port: 5000
  debug: false
```

### 4. Ejecutar el Sistema

```bash
# Modo demostración (con datos de ejemplo)
echo "y" | python3 monitor.py -d

# Modo producción (requiere root para captura activa)
sudo python3 monitor.py
```

### 5. Acceder al Dashboard

```
http://localhost:5000
```

---

## Interfaz Web

### Panel de Control
- **Estadísticas en Tiempo Real:** Dispositivos, eventos, alertas críticas
- **Alertas Destacadas:** Eventos críticos y de alta severidad
- **Eventos Recientes:** Últimos 20 eventos con detalles
- **Dispositivos Conectados:** Lista rápida con contador de eventos

### Página de Dispositivos
- **Tabla Completa:** Todos los dispositivos detectados
- **Información:** IP, MAC, Fabricante, Hostname, Fecha visto
- **Controles:** Bloquear/Desbloquear, Ver eventos del dispositivo
- **Eventos:** Número de eventos hoy y total

### Página de Eventos
- **Filtros Avanzados:** Por severidad, dispositivo, tipo, estado
- **Tabla de Eventos:** Todos los eventos con detalles
- **Acciones:** Reconocer eventos
- **Colores:** Código de severidad (rojo=crítica, naranja=alta, etc)

### Página de Inteligencia de Amenazas
- **Estadísticas:** Total IPs, dominios, fuentes activas
- **Tabla de Fuentes:** Estado de cada fuente de datos
- **Última Actualización:** Cuándo se descargaron las listas
- **Control Manual:** Botón para actualizar inteligencia

---

## API REST

### Autenticación
Actualmente sin autenticación (se recomienda añadir en producción con JWT)

### Endpoints

#### GET /api/stats
Obtiene estadísticas del sistema

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
  "intel_ips": 50000
}
```

#### GET /api/devices
Lista todos los dispositivos

```bash
curl http://localhost:5000/api/devices
```

#### POST /api/devices/{ip}/block
Bloquea un dispositivo

```bash
curl -X POST http://localhost:5000/api/devices/192.168.1.5/block
```

#### POST /api/devices/{ip}/unblock
Desbloquea un dispositivo

```bash
curl -X POST http://localhost:5000/api/devices/192.168.1.5/unblock
```

#### GET /api/events
Obtiene eventos (con filtros opcionales)

```bash
curl "http://localhost:5000/api/events?severity=critical&limit=50"
```

#### POST /api/events/{id}/acknowledge
Marca un evento como reconocido

```bash
curl -X POST http://localhost:5000/api/events/123/acknowledge
```

#### GET /api/connections
Obtiene conexiones de red

```bash
curl http://localhost:5000/api/connections
```

#### GET /api/intel/sources
Estado de fuentes de inteligencia

```bash
curl http://localhost:5000/api/intel/sources
```

#### POST /api/intel/refresh
Actualiza todas las fuentes de inteligencia

```bash
curl -X POST http://localhost:5000/api/intel/refresh
```

---

## Mantenimiento y Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'yaml'"

**Solución:**
```bash
source venv/bin/activate
pip install pyyaml
```

### Problema: "Interface 'eth0' not found"

**Solución:** Verifica el nombre correcto de tu interfaz de red:
```bash
ip link show
# o
ifconfig
```

Actualiza `config.yaml` con el nombre correcto (ej: `wlan0`, `enp0s3`)

### Problema: "Permission denied" en packet capture

**Solución:** Necesita root. Las siguientes opciones:

```bash
# Opción 1: Ejecutar con sudo
sudo python3 monitor.py

# Opción 2: Dar permisos a Scapy sin root (no recomendado)
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
```

### Problema: Database locked

**Solución:** La base de datos está siendo usada. Cierra otras instancias:
```bash
pkill -f "python3 monitor.py"
sleep 2
python3 monitor.py -d
```

### Problema: No se envían emails

**Verificar:**
1. ¿Está config.yaml configurado correctamente?
2. ¿Es una contraseña de app (no la contraseña regular) si usas Gmail?
3. ¿Está habilitado "Acceso a aplicaciones menos seguras" en Gmail?

**Gmail App Password:**
1. Ve a https://myaccount.google.com/security
2. Activa "2-Step Verification"
3. En "App passwords", crea una contraseña para "Mail" y "Linux"
4. Usa esa contraseña en `config.yaml`

### Diagnóstico General

**Ver logs en tiempo real:**
```bash
tail -f logs/monitor.log
```

**Ver estado de base de datos:**
```bash
sqlite3 data/monitor.db ".tables"
sqlite3 data/monitor.db "SELECT COUNT(*) FROM events;"
```

**Ver configuración cargada:**
```bash
python3 -c "from config import load_config; cfg = load_config(); print(cfg)"
```

---

## Mejoras Futuras

- [ ] Autenticación en dashboard (JWT tokens)
- [ ] Exportar eventos a SIEM (Splunk, ELK)
- [ ] Machine Learning para detección de anomalías
- [ ] Historial de dispositivos eliminados
- [ ] Whitelisting personalizado de dispositivos
- [ ] Reportes programados por email
- [ ] Integración con servicios en la nube
- [ ] Versión móvil (app iOS/Android)

---

## Soporte y Contribuciones

Para reportar problemas o sugerir mejoras, contacta al equipo de desarrollo.

**Última actualización:** Mayo 12, 2026  
**Versión:** 1.0.0 Completa
