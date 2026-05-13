# Inicio Rápido - Monitor de Seguridad IoT

¡Comienza a monitorear tu red en 5 minutos!

## Paso 1: Crear Entorno Virtual (1 min)

```bash
cd /home/yaeladmin/git/IOT-UPIICSA
python3 -m venv venv
source venv/bin/activate
```

## Paso 2: Instalar Dependencias (2 min)

```bash
pip install -r requirements.txt
```

**Paquetes que se instalarán:**
- Scapy - Captura de paquetes
- Flask - Servidor web
- APScheduler - Programador de tareas
- Requests - Descargas HTTP
- PyYAML - Parseo de configuración

## Paso 3: Ejecutar en Modo Demostración (1 min)

```bash
echo "y" | python3 monitor.py -d
```

Esto carga datos de ejemplo y **NO requiere root**.

Verás algo como:
```
[2026-05-12 23:36:38] INFO     [__main__] IoT Network Security Monitor — Starting
[2026-05-12 23:36:38] INFO     [database] Database schema ready at data/monitor.db
[2026-05-12 23:36:38] INFO     [database] Seeding demo data…
[2026-05-12 23:36:38] INFO     [database] Demo data seeded: 5 devices, 5 events
[2026-05-12 23:36:40] INFO     [__main__] Web dashboard: http://0.0.0.0:5000
[2026-05-12 23:36:40] INFO     [__main__] Running on http://127.0.0.1:5000
```

## Paso 4: Acceder al Dashboard (1 min)

Abre tu navegador en: **http://localhost:5000**

Verás:
- 📊 **Panel de Control** - Estadísticas en vivo
- 📱 **Dispositivos** - 5 dispositivos de ejemplo
- 📋 **Eventos** - 5 eventos de seguridad de ejemplo
- 🎯 **Inteligencia de Amenazas** - Estado de fuentes de datos

## ¡Listo! 🎉

Ahora prueba estas acciones:

### Explorar el Dashboard
- Haz clic en "Dispositivos" para ver la lista completa
- Haz clic en "Eventos" para ver el registro de seguridad
- Haz clic en "Inteligencia de Amenazas" para ver fuentes

### Interactuar con Dispositivos
- En la página de Dispositivos, haz clic en "🚫 Bloquear" en cualquier fila
- El dispositivo se marca como bloqueado
- Haz clic en "✓ Desbloquear" para restaurarlo

### Reconocer Eventos
- En la página de Eventos, haz clic en "✓ Reconocer" en un evento sin reconocer
- El evento cambia de estado a "Reconocido"

## Siguiente: Modo Producción (Opcional)

Cuando estés listo para monitorear tu red real:

### 1. Configurar red
Edita `config.yaml`:
```yaml
network:
  interface: wlan0          # Tu interfaz Wi-Fi
  gateway: 192.168.1.1      # Tu gateway
  subnet: 192.168.1.0/24    # Tu subred
```

### 2. Configurar email (Opcional)
Edita `config.yaml`:
```yaml
email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  from_address: tu-email@gmail.com
  password: tu-app-password
  recipients:
    - tu-email@gmail.com
```

Para Gmail:
1. Ve a https://myaccount.google.com/security
2. Activa "2-Step Verification"
3. Ve a "App passwords"
4. Selecciona "Mail" y "Linux"
5. Copia la contraseña generada a `config.yaml`

### 3. Ejecutar en modo producción
```bash
sudo python3 monitor.py
```

## Detener el Monitor

Presiona **Ctrl+C** en la terminal

## Necesita Ayuda?

### Error: "No module named 'yaml'"
```bash
source venv/bin/activate
pip install pyyaml
```

### Error: "Interface 'eth0' not found"
```bash
# Ver interfaces disponibles
ip link show

# Actualizar config.yaml con el nombre correcto
```

### Error: "Permission denied"
Necesita ejecutarse con sudo en modo producción:
```bash
sudo python3 monitor.py
```

## Próximos Pasos

1. **Lee la guía completa:** `GUIA_SISTEMA_ES.md`
2. **Configura tu red:** Edita `config.yaml` con tus datos
3. **Ejecuta en producción:** `sudo python3 monitor.py`
4. **Revisa eventos:** Abre http://localhost:5000 en tu navegador

¡Que disfrutes monitoreando tu red! 🔐
