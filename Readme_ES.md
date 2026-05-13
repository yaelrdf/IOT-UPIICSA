# Monitor de Seguridad de Redes IoT

Un sistema de monitoreo de seguridad de bajo costo basado en Raspberry Pi para detectar comportamiento malicioso y anómalo en redes IoT domésticas.

## Descripción General

Este proyecto implementa una solución integral de monitoreo de seguridad específicamente diseñada para dispositivos IoT en redes domésticas. Combina múltiples técnicas de detección para identificar comportamiento sospechoso sin requerir modificaciones en la infraestructura de red o acceso a tráfico encriptado.

### Características Principales

- **Descubrimiento de Dispositivos**: Detecta automáticamente todos los dispositivos en la red mediante escaneo ARP
- **Captura y Análisis de Paquetes**: Intercepta y analiza metadatos de red (nunca contenido de payload)
- **Integración de Listas Negras**: Verifica conexiones contra listas de IPs y dominios maliciosos conocidos:
  - abuse.ch (Feodo Tracker, URLhaus)
  - Emerging Threats
  - Fuentes personalizadas
- **Detección de Beacon**: Identifica conexiones salientes regulares típicas de botnet C&C
- **Detección de Anomalías Geográficas**: Marca conexiones a países sospechosos
- **Detección de Alto Volumen**: Alerta cuando dispositivos envían cantidades inusuales de datos
- **Alertas por Email**: Notificaciones en tiempo real para eventos de alta severidad
- **Panel Web**: Dashboard interactivo para monitoreo, gestión de dispositivos y revisión de eventos
- **Modo Activo (Opcional)**: Envenenamiento ARP para bloquear tráfico de dispositivos comprometidos

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                 Raspberry Pi Zero 2 W                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Interfaz de Red (Wi-Fi)                   │  │
│  │          (802.11 b/g/n - Modo Promiscuo)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │       Capa de Percepción (Sensado de Red)            │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ • Scanner: Descubrimiento ARP + búsqueda OUI  │  │  │
│  │  │ • Captura: Sniffing de paquetes + extracción │  │  │
│  │  │ • Spoofer: Envenenamiento ARP (modo activo)   │  │  │
│  │  │ • Threat Intel: Gestor de listas negras       │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      Capa de Procesamiento (Análisis & Decisión)    │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ • Analyzer: Ejecuta 5 reglas de detección    │  │  │
│  │  │   - Lista negra (IP & Dominio)               │  │  │
│  │  │   - Detección de patrón beacon               │  │  │
│  │  │   - Anomalías geográficas                    │  │  │
│  │  │   - Detección de alto volumen                │  │  │
│  │  │ • Base de Datos: Almacenamiento de eventos   │  │  │
│  │  │ • Alerter: Notificaciones por email          │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      Capa de Aplicación (Interacción del Usuario)    │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │ • Dashboard Web (Flask)                        │  │  │
│  │  │ • API REST                                     │  │  │
│  │  │ • Visor de Registro de Eventos                │  │  │
│  │  │ • Gestión y Bloqueo de Dispositivos          │  │  │
│  │  │ • Estado de Inteligencia de Amenazas         │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Almacenamiento Persistente (SQLite3)        │  │
│  │  • Dispositivos y Metadatos                          │  │
│  │  • Eventos y Alertas                                 │  │
│  │  • Conexiones de Red                                 │  │
│  │  • Cache de Inteligencia de Amenazas               │  │
│  │  • Cache de Geolocalización                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Requisitos

### Hardware

- **Raspberry Pi Zero 2 W** (recomendado) o cualquier Raspberry Pi con Wi-Fi
- **Adaptador inalámbrico** (si no está integrado; Zero 2 W tiene 802.11ac integrado)
- **Fuente de alimentación**: 5V 2.5A mínimo
- **Tarjeta SD**: 32GB (Clase 10 recomendada)

### Software

- Python 3.7+
- Raspbian OS (o Ubuntu Server para Raspberry Pi)
- Acceso root/sudo para captura de paquetes y envenenamiento ARP

## Instalación Rápida

### 1. Clonar el Repositorio

```bash
cd /home/yaeladmin/git/IOT-UPIICSA
```

### 2. Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar

Edita `config.yaml` con tu configuración de red:

```yaml
network:
  interface: eth0
  gateway: 192.168.1.1
  subnet: 192.168.1.0/24
```

### 5. Ejecutar

```bash
# Modo demostración (datos de ejemplo)
echo "y" | python3 monitor.py -d

# Accede a http://localhost:5000
```

## Uso

### Modo Demostración

Prueba el sistema con datos de ejemplo sin necesidad de acceso root:

```bash
echo "y" | python3 monitor.py -d
```

Esto carga:
- 5 dispositivos de ejemplo
- 20 eventos de seguridad
- Datos de inteligencia de amenazas

Accede al dashboard en `http://localhost:5000`

### Modo Producción

```bash
sudo python3 monitor.py
```

Esto activa:
- Escaneo ARP real
- Captura de paquetes en vivo
- Análisis en tiempo real
- Alertas por email

### Detener el Servicio

```
Ctrl+C
```

## Interfaz Web

### Panel de Control
- Estadísticas en tiempo real (dispositivos, eventos, alertas)
- Alertas críticas destacadas
- Eventos recientes
- Dispositivos conectados actualmente

### Dispositivos
- Lista completa de dispositivos detectados
- Información (IP, MAC, fabricante, hostname)
- Controles (bloquear/desbloquear)
- Historial de eventos

### Eventos
- Registro de todos los eventos de seguridad
- Filtros avanzados (severidad, dispositivo, tipo, estado)
- Acciones (reconocer eventos)
- Código de colores por severidad

### Inteligencia de Amenazas
- Estado de fuentes de datos
- IPs y dominios bloqueados
- Última actualización
- Control manual de actualización

## Tipos de Detección

### 1. Lista Negra de IPs (🔴 CRÍTICA)
Detecta conexiones a IPs maliciosas conocidas (botnets, C&C)

### 2. Lista Negra de Dominios (🔴 CRÍTICA)
Detecta consultas DNS a dominios maliciosos

### 3. Detección de Beacon (🟠 ALTA)
Identifica patrones regulares de conexión típicos de botnets

### 4. Anomalía Geográfica (🟡 MEDIA)
Alerta sobre conexiones a ubicaciones inusuales

### 5. Alto Volumen (🟡 MEDIA)
Detecta dispositivos que envían cantidades anormales de datos

## API REST

### GET /api/stats
```bash
curl http://localhost:5000/api/stats
```

### GET /api/devices
```bash
curl http://localhost:5000/api/devices
```

### POST /api/devices/{ip}/block
```bash
curl -X POST http://localhost:5000/api/devices/192.168.1.5/block
```

### GET /api/events
```bash
curl http://localhost:5000/api/events
```

### POST /api/events/{id}/acknowledge
```bash
curl -X POST http://localhost:5000/api/events/1/acknowledge
```

Para más detalles, ver API_ES.md

## Configuración Avanzada

Edita `config.yaml` para personalizar:

```yaml
scan:
  discovery_interval_sec: 300      # Cada 5 minutos
  capture_interval_sec: 600        # Cada 10 minutos

thresholds:
  high_volume_multiplier: 2.0      # Alerta si > 2x promedio
  beaconing_cv_threshold: 0.20     # Umbral beacon

email:
  smtp_server: smtp.gmail.com
  from_address: tu-email@gmail.com
  recipients:
    - admin@ejemplo.com

threat_intel:
  auto_update: true
  update_interval_hours: 24
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'yaml'"
```bash
source venv/bin/activate
pip install pyyaml
```

### Error: "Interface 'eth0' not found"
Verifica tu interfaz de red:
```bash
ip link show
```
Actualiza `config.yaml` con el nombre correcto (ej: `wlan0`, `enp0s3`)

### Error: "Permission denied" en captura de paquetes
Necesita root:
```bash
sudo python3 monitor.py
```

### No se envían emails
1. Verifica `config.yaml` está configurado
2. Usa contraseña de app si usas Gmail (no la contraseña regular)
3. Habilita "Acceso a aplicaciones menos seguras" en Google

## Mejoras Futuras

- [ ] Autenticación en dashboard
- [ ] Exportar eventos a SIEM
- [ ] Machine Learning para detección de anomalías
- [ ] Reportes programados
- [ ] Integración con servicios en la nube

## Documentación Completa

- **GUIA_SISTEMA_ES.md** - Guía completa del sistema (¡LEER PRIMERO!)
- **QUICKSTART_ES.md** - Inicio rápido en 5 minutos
- **API_ES.md** - Documentación completa de la API
- **ARCHITECTURE_ES.md** - Detalles de arquitectura
- **DEVELOPMENT_ES.md** - Guía para desarrolladores

## Licencia

Ver archivo LICENSE

## Soporte

Para reportar problemas o sugerir mejoras, contacta al equipo de desarrollo.

**Última actualización:** Mayo 12, 2026  
**Versión:** 1.0.0 Completa
