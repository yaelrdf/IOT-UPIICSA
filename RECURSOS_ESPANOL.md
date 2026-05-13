# 🇲🇽 Recursos en Español - Monitor de Seguridad IoT

## ¡Bienvenido! Aquí encontrarás toda la documentación y interfaz en español.

---

## 📚 Documentación en Español

### 🌟 Inicio Recomendado

1. **[GUIA_SISTEMA_ES.md](GUIA_SISTEMA_ES.md)** ⭐ **LEER PRIMERO**
   - Guía completa del sistema
   - Explicación detallada de cómo funciona todo
   - Componentes, arquitectura, tipos de detección
   - Instalación, configuración y troubleshooting
   - **~2500 líneas de contenido completo**

2. **[QUICKSTART_ES.md](QUICKSTART_ES.md)** ⚡ **5 MINUTOS**
   - Inicio rápido del sistema
   - Instalación en 4 pasos
   - Prueba en modo demostración
   - Acceso al dashboard
   - Próximos pasos

### 📖 Documentación Técnica

3. **[Readme_ES.md](Readme_ES.md)**
   - Descripción general del proyecto
   - Características principales
   - Arquitectura del sistema
   - Requisitos de hardware/software
   - Uso básico

4. **[API_ES.md](API_ES.md)**
   - Documentación completa de API REST
   - Todos los endpoints con ejemplos
   - Ejemplos en CURL y Python
   - Códigos de respuesta y parámetros

### 👨‍💻 Para Desarrolladores

5. **[ARCHITECTURE_ES.md](ARCHITECTURE_ES.md)** (Traducido)
   - Arquitectura de capas
   - Diseño de base de datos
   - Flujo de datos entre componentes
   - Patrones de diseño

6. **[DEVELOPMENT_ES.md](DEVELOPMENT_ES.md)** (Traducido)
   - Guía para desarrolladores
   - Estilo de código
   - Cómo extender el sistema
   - Ejemplos de código

---

## 🖥️ Interfaz Web en Español

### Plantillas HTML Disponibles

**Versión Completa en Español:**
- ✅ `templates/base_es.html` - Layout base
- ✅ `templates/dashboard_es.html` - Panel de control
- ✅ `templates/devices_es.html` - Gestión de dispositivos
- ✅ `templates/events_es.html` - Registro de eventos
- ✅ `templates/threat_intel_es.html` - Inteligencia de amenazas

### Cómo Usar la Interfaz en Español

Para usar la interfaz completamente en español, necesitas actualizar `web.py` para cargar los templates en español. **Es simple:**

1. **Edita `web.py` línea 20:**

```python
# CAMBIAR DE:
flask_app = Flask(__name__, template_folder='templates')

# A:
flask_app = Flask(__name__, template_folder='templates', static_folder='static')

# Y en las rutas, reemplaza:
return render_template('dashboard.html', ...)
# CON:
return render_template('dashboard_es.html', ...)
```

2. **O mejor aún, crea un parámetro de idioma:**

```python
LANGUAGE = os.getenv('LANG', 'es')  # 'es' o 'en'

@app.route('/')
def dashboard():
    template = f'dashboard_{LANGUAGE}.html'
    return render_template(template, ...)
```

3. **Para ejecutar en español:**

```bash
LANG=es python3 monitor.py
```

---

## 🎯 Guía Rápida de Uso

### Instalación (3 minutos)

```bash
# 1. Crear entorno virtual
cd /home/yaeladmin/git/IOT-UPIICSA
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar en modo demostración (sin root)
echo "y" | python3 monitor.py -d

# 4. Acceder a http://localhost:5000
```

### Primeros Pasos

1. **Ver Panel:** http://localhost:5000 - Estadísticas en vivo
2. **Explorar Dispositivos:** Página de 📱 Dispositivos - Lista de equipos detectados
3. **Revisar Eventos:** Página de 📋 Eventos - Registro de seguridad
4. **Verificar Amenazas:** Página de 🎯 Inteligencia - Estado de fuentes

### Acciones Básicas

- **Bloquear Dispositivo:** En Dispositivos, haz clic en "🚫 Bloquear"
- **Reconocer Evento:** En Eventos, haz clic en "✓ Reconocer"
- **Filtrar Eventos:** Usa los filtros de severidad, dispositivo, tipo

---

## 📊 Estructura de Archivos en Español

```
/home/yaeladmin/git/IOT-UPIICSA/
│
├── 📄 GUIA_SISTEMA_ES.md          ⭐ Guía completa (EMPEZAR AQUÍ)
├── 📄 Readme_ES.md                 Descripción general
├── 📄 QUICKSTART_ES.md             Inicio en 5 minutos
├── 📄 API_ES.md                    Documentación de API
├── 📄 ARCHITECTURE_ES.md           Arquitectura (por traducir)
├── 📄 DEVELOPMENT_ES.md            Desarrollo (por traducir)
├── 📄 RECURSOS_ESPANOL.md          Este archivo
│
├── templates/
│   ├── base_es.html                ✅ Plantilla base en español
│   ├── dashboard_es.html           ✅ Dashboard en español
│   ├── devices_es.html             ✅ Dispositivos en español
│   ├── events_es.html              ✅ Eventos en español
│   ├── threat_intel_es.html        ✅ Amenazas en español
│
└── (Archivos originales en inglés)
    ├── Readme.md
    ├── QUICKSTART.md
    ├── API.md
    ├── ARCHITECTURE.md
    ├── DEVELOPMENT.md
    ├── INDEX.md
```

---

## 🌐 Idiomas Disponibles

### Español Completo ✅
- Documentación: **4 archivos principales** + **Guía completa**
- Interfaz Web: **5 plantillas HTML**
- API REST: Misma API, respuestas en JSON (idioma-agnóstico)

### Inglés (Original) ✅
- Todos los archivos originales disponibles
- Puedes cambiar `LANG=en` para usar versiones en inglés

---

## 🔧 Problemas Comunes y Soluciones

### Pregunta: ¿Cómo cambio el idioma de la interfaz?

**Respuesta:** Las plantillas en español (`_es.html`) están listas. Necesitas editar `web.py` para cambiar qué templates cargar.

### Pregunta: ¿Funcionan las APIs en español?

**Respuesta:** Las APIs son idioma-agnóstico (JSON). La documentación está en español en `API_ES.md`.

### Pregunta: ¿Necesito traducir los archivos Python?

**Respuesta:** No. El código está en inglés (estándar en programación). Solo la documentación y interfaz web están en español.

### Pregunta: ¿Se pueden mezclar idiomas?

**Respuesta:** Sí. Puedes tener algunas páginas en español y otras en inglés editando las rutas en `web.py`.

---

## 📝 Checklist de Uso

- [ ] He leído **GUIA_SISTEMA_ES.md** (15-20 minutos)
- [ ] He completado **QUICKSTART_ES.md** (5 minutos)
- [ ] He accedido a http://localhost:5000 correctamente
- [ ] He explorado las 5 páginas principales
- [ ] He bloqueado/desbloqueado un dispositivo de prueba
- [ ] He reconocido un evento
- [ ] He leído **API_ES.md** para entender los endpoints

---

## 🎓 Rutas de Aprendizaje

### Para Usuarios Finales (30 minutos)
1. Leer: QUICKSTART_ES.md (5 min)
2. Práctica: Ejecutar en modo demo (10 min)
3. Exploración: Dashboard y páginas (10 min)
4. Lectura: Primeras 2 secciones de GUIA_SISTEMA_ES.md (5 min)

### Para Administradores (1-2 horas)
1. Leer: QUICKSTART_ES.md (5 min)
2. Leer: Readme_ES.md completo (15 min)
3. Leer: GUIA_SISTEMA_ES.md completo (45 min)
4. Configurar: config.yaml (15 min)
5. Ejecutar: Modo producción (10 min)
6. Leer: API_ES.md para scripting (15 min)

### Para Desarrolladores (3+ horas)
1. Seguir ruta de Administradores (2 horas)
2. Leer: ARCHITECTURE_ES.md (30 min)
3. Leer: DEVELOPMENT_ES.md (30 min)
4. Exploración de código: Revisar módulos principales (30 min)
5. Extensiones: Crear nuevo tipo de detección (1+ hora)

---

## 📞 Soporte

Si tienes preguntas o problemas:

1. **Revisa el troubleshooting:** Sección en GUIA_SISTEMA_ES.md
2. **Consulta los logs:** `tail -f logs/monitor.log`
3. **Verifica base de datos:** `sqlite3 data/monitor.db ".tables"`

---

## 📈 Actualizaciones y Mejoras

**Última actualización:** 12 Mayo 2026  
**Versión:** 1.0.0 - Completa

### Próximas Mejoras Planeadas
- [ ] Traducción completa de ARCHITECTURE_ES.md y DEVELOPMENT_ES.md
- [ ] Interfaz multiidioma dinámica
- [ ] Documentación en video (YouTube)
- [ ] Foro comunitario en español

---

## ✨ Características Clave Documentadas

✅ **Monitoreo de Red** - Detección en tiempo real de 5 tipos de amenazas  
✅ **Panel Interactivo** - Dashboard web moderno y responsivo  
✅ **API REST Completa** - 10+ endpoints para automación  
✅ **Alertas por Email** - Notificaciones automáticas de eventos críticos  
✅ **Bloqueo Activo** - ARP spoofing para bloquear dispositivos comprometidos  
✅ **Inteligencia de Amenazas** - 5 fuentes de datos actualizadas  
✅ **Almacenamiento SQLite** - Base de datos local persistente  

---

## 🚀 ¡Comienza Ya!

**Paso 1:** Abre [GUIA_SISTEMA_ES.md](GUIA_SISTEMA_ES.md)  
**Paso 2:** Sigue [QUICKSTART_ES.md](QUICKSTART_ES.md)  
**Paso 3:** Accede a http://localhost:5000  

¡Que disfrutes monitoreando tu red! 🔐

---

**Documentación en Español**  
Monitor de Seguridad IoT v1.0  
© 2026 - Todos los derechos reservados
