# Monitor de Seguridad de Redes IoT

## Descripción

Sistema de monitoreo de seguridad de redes IoT basado en Raspberry Pi para detectar comportamiento malicioso en redes domésticas. Implementa múltiples técnicas de detección sin requerir modificaciones en la infraestructura de la red.

## Características Principales

✅ **Detección de Dispositivos**: Escaneo automático con ARP y búsqueda de vendedores  
✅ **Captura de Paquetes**: Análisis de metadatos de red (nunca payload)  
✅ **5 Motores de Detección**:
   - Listas negras de IP conocidas
   - Listas negras de dominios conocidos
   - Detección de beaconing (Botnet C&C)
   - Detección de anomalías geográficas
   - Detección de alto volumen de datos

✅ **Panel Web**: Dashboard interactivo con API REST  
✅ **Alertas por Email**: Notificaciones automáticas de eventos críticos  
✅ **Modo Activo**: ARP spoofing para bloquear tráfico de dispositivos comprometidos  
✅ **Base de Datos**: Registro completo del historial de eventos  

## Instalación Rápida

### Requisitos
- Python 3.7+
- sudo/root (para captura de paquetes y ARP spoofing)
- Raspberry Pi o Linux (x86/ARM)

### Pasos

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd IOT-UPIICSA

# 2. Crear entorno virtual (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar el sistema
sudo python3 src/monitor.py
```

## Ejecución

### Modos de Ejecución

```bash
# Ejecución normal con configuración por defecto
sudo python3 src/monitor.py

# Con datos de demostración
sudo python3 src/monitor.py -d

# Con archivo de configuración personalizado
sudo python3 src/monitor.py -c config/mi_config.yaml

# Ver ayuda
python3 src/monitor.py --help
```

### Acceso al Dashboard

Una vez ejecutado, abrir en el navegador:
```
http://localhost:5000
```

## Configuración

Editar `config/config.yaml` para personalizar:

```yaml
network:
  interface: "eth0"          # Interfaz de red a monitorear
  mode: "passive"            # "passive" o "active"
  gateway_ip: "192.168.1.1"
  subnet: "192.168.1.0/24"

scan:
  interval_sec: 300          # Intervalo entre escaneos

email:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "tu_email@gmail.com"
  sender_password: "tu_contraseña_app"
  recipients: ["admin@ejemplo.com"]

# ... más opciones disponibles en config/config.yaml
```

## Estructura del Proyecto

```
IOT-UPIICSA/
├── src/                      # Código principal
│   ├── monitor.py           # Punto de entrada
│   ├── app.py              # Orquestador principal
│   ├── web.py              # Servidor Flask
│   ├── config.py           # Configuración
│   ├── database.py         # Base de datos
│   ├── constants.py        # Constantes
│   ├── core/               # Módulos de funcionalidad
│   │   ├── scanner.py      # Descubrimiento de dispositivos
│   │   ├── capture.py      # Captura de paquetes
│   │   ├── analyzer.py     # Motor de análisis
│   │   ├── threat_intel.py # Inteligencia de amenazas
│   │   ├── alerter.py      # Sistema de alertas
│   │   └── spoofer.py      # ARP spoofing
│   └── utils/              # Utilidades
├── config/                 # Archivos de configuración
│   ├── config.yaml        # Configuración principal
│   └── iot-monitor.service # Servicio systemd
├── docs/                   # Documentación (español)
├── templates/              # Plantillas HTML (español)
├── scripts/                # Scripts de instalación
├── data/                   # Datos en tiempo de ejecución
├── requirements.txt        # Dependencias Python
├── LICENSE                 # Licencia MIT
└── README.md              # Este archivo
```

Para más detalles ver [STRUCTURE.md](STRUCTURE.md) y [CLEANUP_SUMMARY.md](CLEANUP_SUMMARY.md)

## Documentación Completa

- [Guía del Sistema Completa](docs/GUIA_SISTEMA_ES.md)
- [Inicio Rápido](docs/QUICKSTART_ES.md)
- [API REST](docs/API_ES.md)
- [Recursos Adicionales](docs/RECURSOS_ESPANOL.md)

## Instalación como Servicio (Raspberry Pi)

Para ejecutar como servicio systemd:

```bash
# 1. Copiar archivo de servicio
sudo cp config/iot-monitor.service /etc/systemd/system/

# 2. Editar la ruta en el archivo
sudo nano /etc/systemd/system/iot-monitor.service
# Cambiar ExecStart con la ruta correcta

# 3. Recargar systemd
sudo systemctl daemon-reload

# 4. Iniciar el servicio
sudo systemctl start iot-monitor
sudo systemctl enable iot-monitor

# 5. Verificar estado
sudo systemctl status iot-monitor
```

## Requisitos del Sistema

### Hardware Recomendado
- **Raspberry Pi Zero 2 W** o superior (ARM)
- **x86 PC/Server** para entornos de prueba
- 512MB RAM mínimo, 1GB+ recomendado

### Software
- Debian/Ubuntu Linux
- Python 3.7+
- Conexión Ethernet o WiFi con modo promiscuo

### Dependencias Python
- Scapy >= 2.5.0 (captura de paquetes)
- Flask >= 3.0.0 (servidor web)
- APScheduler >= 3.10.0 (planificador de tareas)
- Requests >= 2.31.0 (descargas HTTP)
- PyYAML >= 6.0.0 (configuración)
- python-nmap >= 0.7.1 (escaneo de puertos)

## Solución de Problemas

### "Permission Denied" en captura de paquetes
```bash
# La aplicación requiere privilegios de root
sudo python3 src/monitor.py
```

### "ModuleNotFoundError" en dependencias
```bash
# Asegurate de instalar dependencias
pip install -r requirements.txt
```

### El dashboard no es accesible
```bash
# Verificar puerto 5000 está disponible
sudo lsof -i :5000
# Cambiar puerto en config/config.yaml si es necesario
```

## API REST

El sistema proporciona una API REST en `http://localhost:5000/api/`

Ejemplos de endpoints:
- `GET /api/devices` - Lista de dispositivos
- `GET /api/events` - Eventos de seguridad
- `GET /api/status` - Estado del sistema
- `POST /api/threat-intel/update` - Actualizar listas negras

Ver [API_ES.md](docs/API_ES.md) para documentación completa.

## Modo Activo (ARP Spoofing)

⚠️ **Advertencia**: Solo usar en redes que administres.

En modo activo, el sistema puede bloquear tráfico de dispositivos comprometidos usando ARP spoofing.

```yaml
network:
  mode: "active"   # Habilitar modo activo
```

## Registros y Datos

- **Base de datos**: `data/monitor.db` (SQLite)
- **Registros**: `data/monitor.log`
- **Configuración**: `config/config.yaml`

## Autores

**Yael Saldaña Flores**  
**Emanuel Giovani Luna Ramos**
