# 🇲🇽 Guía de Ejecución - Sistema en Español

## ¡Bienvenido a la Versión en Español!

El Monitor de Seguridad IoT está **completamente disponible en español mexicano**:
- ✅ Interfaz web completamente en español
- ✅ Documentación completa en español
- ✅ Todos los menús, botones y mensajes en español

---

## 🚀 Inicio Rápido (5 minutos)

### Paso 1: Activar Entorno Virtual

```bash
cd /home/yaeladmin/git/IOT-UPIICSA
source venv/bin/activate
```

### Paso 2: Ejecutar el Sistema (Modo Demostración)

```bash
echo "y" | python3 monitor.py -d
```

Verás:
```
[HORA] INFO     [__main__] IoT Network Security Monitor — Starting
[HORA] INFO     [web] Flask app initialized
[HORA] INFO     [__main__] Web dashboard: http://0.0.0.0:5000
[HORA] INFO     [__main__] Running on http://127.0.0.1:5000
```

### Paso 3: Abrir en tu Navegador

```
http://localhost:5000
```

¡Verás el dashboard completamente en **español mexicano**! 🎉

---

## 📖 Documentación en Español

### Lectura Recomendada (en este orden):

1. **[QUICKSTART_ES.md](QUICKSTART_ES.md)** ⚡ (5 minutos)
   - Inicio rápido del sistema
   - 4 pasos simples

2. **[GUIA_SISTEMA_ES.md](GUIA_SISTEMA_ES.md)** ⭐ (20-30 minutos)
   - Guía completa del sistema
   - Explicación de cómo funciona todo
   - Todos los componentes explicados

3. **[Readme_ES.md](Readme_ES.md)** 📖 (10 minutos)
   - Descripción del proyecto
   - Características principales
   - Requisitos

4. **[API_ES.md](API_ES.md)** 🔌 (Para desarrolladores)
   - Documentación de API REST
   - Ejemplos de uso
   - Todos los endpoints

5. **[RECURSOS_ESPANOL.md](RECURSOS_ESPANOL.md)** 🗺️
   - Índice de recursos españoles
   - Rutas de aprendizaje
   - FAQ y solución de problemas

---

## 🖥️ Interfaz Web en Español

### 5 Páginas Completamente en Español:

| Página | Descripción | URL |
|--------|------------|-----|
| 📊 **Panel de Control** | Estadísticas en tiempo real | http://localhost:5000/ |
| 📱 **Dispositivos** | Lista de dispositivos detectados | http://localhost:5000/devices |
| 📋 **Eventos** | Registro de eventos de seguridad | http://localhost:5000/events |
| 🎯 **Inteligencia de Amenazas** | Estado de fuentes de datos | http://localhost:5000/threat-intel |

### Elementos Traducidos:

✅ Títulos y encabezados  
✅ Botones de acción  
✅ Mensajes y alertas  
✅ Filtros y búsqueda  
✅ Columnas de tablas  
✅ Estados y etiquetas  
✅ Ayuda y tooltips  

---

## 🎯 Acciones en la Interfaz Española

### Panel de Control
```
🏠 Panel de Seguridad de Redes
├─ 📊 Dispositivos Conectados: Número de equipos en red
├─ 🚫 Dispositivos Bloqueados: Equipos en lista de bloqueo
├─ 📋 Eventos Hoy: Total de eventos detectados
├─ 🔴 Eventos Críticos: Eventos de máxima severidad
├─ ⚠️ No Reconocidos: Eventos sin revisar
└─ 🎯 IPs Maliciosas: Total de IPs en lista negra
```

### Página de Dispositivos
```
Acciones disponibles:
✓ Ver lista completa de dispositivos
✓ Bloquear dispositivo: Clic en "🚫 Bloquear"
✓ Desbloquear dispositivo: Clic en "✓ Desbloquear"
✓ Ver eventos del dispositivo: Clic en "📋 Ver Eventos"
✓ Filtrar por IP, MAC, fabricante
```

### Página de Eventos
```
Acciones disponibles:
✓ Filtrar por severidad (Crítica, Alta, Media, Baja)
✓ Filtrar por dispositivo
✓ Filtrar por tipo de evento
✓ Filtrar por estado (Reconocido/No reconocido)
✓ Reconocer evento: Clic en "✓ Reconocer"
✓ Ver detalles de evento
```

### Página de Inteligencia de Amenazas
```
Información disponible:
✓ Total de IPs en lista negra
✓ Total de dominios en lista negra
✓ Fuentes activas de inteligencia
✓ Última actualización de listas
✓ Botón para actualizar manualmente
✓ Estado de cada fuente
```

---

## ⚙️ Configuración en Español

### Archivo config.yaml

Edita `config.yaml` para personalizar:

```yaml
network:
  interface: eth0              # Tu interfaz de red (wlan0, eth0, etc.)
  mode: passive                # pasivo o activo
  gateway: 192.168.1.1         # Tu gateway
  subnet: 192.168.1.0/24       # Tu subred

scan:
  discovery_interval_sec: 300  # Descubrir cada 5 min
  capture_interval_sec: 600    # Capturar cada 10 min

email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  from_address: tu-email@gmail.com
  password: tu-contraseña-app
  recipients:
    - admin@ejemplo.com

threat_intel:
  auto_update: true
  update_interval_hours: 24
```

---

## 🔧 Modos de Ejecución

### 1. Modo Demostración (Recomendado para Probar)

```bash
source venv/bin/activate
echo "y" | python3 monitor.py -d
```

**Ventajas:**
- ✅ No requiere root
- ✅ Carga datos de ejemplo
- ✅ Perfecto para aprender
- ✅ Sin acceso a red real

**Qué incluye:**
- 5 dispositivos de ejemplo
- 20 eventos de ejemplo
- Datos de amenazas reales

### 2. Modo Producción (Red Real)

```bash
source venv/bin/activate
sudo python3 monitor.py
```

**Requisitos:**
- ⚠️ Necesita root/sudo
- ⚠️ Acceso a interfaz de red
- ⚠️ IP forwarding habilitado (para modo activo)

**Qué hace:**
- ✅ Escanea tu red real
- ✅ Captura paquetes en vivo
- ✅ Detecta amenazas reales
- ✅ Envía alertas por email

### 3. Modo Configuración Personalizada

```bash
source venv/bin/activate
python3 monitor.py -c /ruta/a/config-personalizado.yaml
```

---

## 📊 Características Documentadas

### Tipos de Detección (Todos en Español)

🔴 **Lista Negra de IPs** - Conexiones a IPs maliciosas conocidas  
🔴 **Lista Negra de Dominios** - Consultas DNS a dominios maliciosos  
🟠 **Detección de Beacon** - Patrones regulares de botnet C&C  
🟡 **Anomalía Geográfica** - Conexiones a ubicaciones inusuales  
🟡 **Alto Volumen** - Dispositivos que envían más datos de lo normal  

### 5 Fuentes de Inteligencia de Amenazas

1. **abuse.ch Feodo Tracker** - Botnets C&C
2. **URLhaus Malware IPs** - IPs de malware
3. **Botnet IPs** - Servidores de comando
4. **Emerging Threats** - Amenazas emergentes
5. **URLhaus Domains** - Dominios maliciosos

---

## 🧪 Pruebas en Modo Demostración

Una vez que iniques el sistema, prueba estas acciones:

### 1. Explorar Panel de Control
```
Abre http://localhost:5000
↓
Verás estadísticas en tiempo real
↓
Observa los 5 dispositivos de ejemplo
↓
Revisa los eventos de seguridad
```

### 2. Bloquear un Dispositivo
```
Ve a Dispositivos
↓
Haz clic en "🚫 Bloquear" en cualquier dispositivo
↓
El dispositivo cambia a estado "Bloqueado"
↓
Haz clic en "✓ Desbloquear" para restaurar
```

### 3. Reconocer Eventos
```
Ve a Eventos
↓
Haz clic en "✓ Reconocer" en un evento sin reconocer
↓
El evento cambia a estado "Reconocido"
```

### 4. Filtrar Eventos
```
Ve a Eventos
↓
Usa los filtros de severidad, dispositivo, tipo
↓
Observa cómo se actualizan los resultados
```

### 5. Ver Inteligencia de Amenazas
```
Ve a Inteligencia de Amenazas
↓
Observa el estado de 5 fuentes
↓
Mira cuántas IPs y dominios están bloqueados
↓
Haz clic en "🔄 Actualizar Ahora" si deseas
```

---

## 🔍 Ver Logs en Español

Los logs se guardan automáticamente:

```bash
tail -f logs/monitor.log
```

Verás mensajes en español:
```
[2026-05-13 00:00:00] INFO     [__main__] Monitor de Seguridad IoT — Iniciando
[2026-05-13 00:00:01] INFO     [database] Esquema de base de datos listo
[2026-05-13 00:00:02] INFO     [app] Todos los componentes inicializados
```

---

## 🆘 Problemas Comunes y Soluciones

### Problema: "ModuleNotFoundError: No module named 'yaml'"

**Solución:**
```bash
source venv/bin/activate
pip install pyyaml
```

### Problema: "Interface 'eth0' not found"

**Solución:** Verifica tu interfaz de red:
```bash
ip link show
# Actualiza config.yaml con el nombre correcto
```

### Problema: "Permission denied" en captura de paquetes

**Solución:** Usa sudo en modo producción:
```bash
sudo python3 monitor.py
```

### Problema: Puerto 5000 ya en uso

**Solución 1:** Detén otros servicios:
```bash
pkill -f "python3 monitor.py"
```

**Solución 2:** Usa otro puerto (edita config.yaml):
```yaml
web:
  host: 0.0.0.0
  port: 8000  # Cambiar a 8000
```

---

## 📚 Documentación Completa Disponible

| Documento | Contenido |
|-----------|----------|
| **QUICKSTART_ES.md** | Inicio en 5 minutos |
| **GUIA_SISTEMA_ES.md** | Guía completa (todos los detalles) |
| **Readme_ES.md** | Descripción general |
| **API_ES.md** | Documentación de API REST |
| **RECURSOS_ESPANOL.md** | Índice y navegación |
| **RESUMEN_TRADUCCION.md** | Estadísticas de traducción |

---

## ✨ Características Implementadas

✅ **Interfaz web 100% en español**  
✅ **Documentación completa en español**  
✅ **Monitoreo en tiempo real**  
✅ **5 tipos de detección**  
✅ **Panel de control interactivo**  
✅ **Gestión de dispositivos**  
✅ **Registro de eventos**  
✅ **API REST documentada**  
✅ **Alertas por email (configurable)**  
✅ **Bloqueo activo de dispositivos**  

---

## 🎓 Próximos Pasos

1. **Explorar el sistema:** Abre http://localhost:5000
2. **Leer documentación:** Comienza con QUICKSTART_ES.md
3. **Probar acciones:** Bloquea/desbloquea dispositivos, reconoce eventos
4. **Configurar:** Personaliza config.yaml
5. **Producción:** Ejecuta con `sudo python3 monitor.py`

---

## 📞 Soporte

- **Documentación:** Ver archivos *_ES.md
- **Troubleshooting:** Ver GUIA_SISTEMA_ES.md sección "Troubleshooting"
- **API:** Ver API_ES.md para desarrollo

---

**Última actualización:** 13 de Mayo 2026  
**Versión:** 1.0.0 - Completamente en Español  
**Estado:** ✨ LISTO PARA USAR

¡Que disfrutes monitoreando tu red en español! 🔐🇲🇽
