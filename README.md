# Jarvis - Asistente Personal SMS con IA

**Versión 2.0.0** - Backend Python con FastAPI

Jarvis es un asistente automático que monitorea SMS entrantes, procesa mensajes con IA (Mistral 7B), y gestiona citas en Google Calendar de forma inteligente.

## 🎯 Características

- 📱 **Monitoreo Inteligente**: Modo pasivo cada 5 minutos, modo activo instantáneo cuando hay conversación
- 🤖 **IA Avanzada**: Mistral 7B Instruct para análisis de contexto y generación de respuestas
- 📅 **Google Calendar**: Integración completa para agendar citas automáticamente
- 💬 **Saludos Formales**: Adaptados a la hora del día (Buenos días/tardes/noches)
- 🔄 **Análisis de Contexto**: Detecta tipo de mensaje (cita, cambio, consulta, publicidad)
- ⏸️ **Posponer Conversaciones**: Pausa automática si el cliente no responde
- 🔐 **Seguro**: Tokens y credenciales protegidas, nunca visibles en interfaz

## 📋 Requisitos

- Python 3.8+
- Token de Hugging Face (gratuito en https://huggingface.co)
- Credenciales de Google Calendar (service account)
- Conexión a internet

## 🚀 Instalación en Termux

### Paso 1: Preparar Termux

```bash
# Actualizar paquetes
pkg update && pkg upgrade

# Instalar dependencias
pkg install python python-pip git

# Crear directorio para el proyecto
mkdir -p ~/jarvis-backend
cd ~/jarvis-backend
```

### Paso 2: Clonar el Repositorio

```bash
# Clonar desde GitHub
git clone https://github.com/Sergio9131/asist-jarvis.git .

# O si ya tienes el código, copia los archivos aquí
```

### Paso 3: Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
source venv/bin/activate
```

### Paso 4: Instalar Dependencias

```bash
# Instalar paquetes requeridos
pip install -r requirements.txt

# Nota: Puede tomar varios minutos en Termux
```

### Paso 5: Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tu editor favorito (nano, vi, etc.)
nano .env
```

**Variables necesarias en .env:**

```
OWNER_NAME=Tu Nombre
OWNER_PHONE=+1234567890
HF_TOKEN=tu_token_huggingface
GOOGLE_CALENDAR_CREDENTIALS={"type":"service_account",...}
PORT=8000
```

### Paso 6: Obtener Credenciales

#### Hugging Face Token
1. Ir a https://huggingface.co/settings/tokens
2. Crear nuevo token (read)
3. Copiar el token en HF_TOKEN

#### Google Calendar Credentials
1. Ir a https://console.cloud.google.com
2. Crear nuevo proyecto
3. Habilitar Google Calendar API
4. Crear service account
5. Descargar JSON de credenciales
6. Copiar el contenido JSON en GOOGLE_CALENDAR_CREDENTIALS

### Paso 7: Ejecutar el Backend

```bash
# Activar entorno virtual (si no está activado)
source venv/bin/activate

# Ejecutar servidor
python main.py

# O con uvicorn directamente
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor estará disponible en: `http://localhost:8000`

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Analizar Mensaje
```bash
POST /analyze-message
Content-Type: application/json

{
  "phone_number": "+14084223904",
  "message_text": "Hola, quiero agendar una cita para mañana a las 3 PM",
  "timestamp": "2026-02-26T10:30:00"
}
```

### Agendar Cita
```bash
POST /schedule-appointment
?phone_number=+14084223904
&client_name=Juan
&proposed_date=2026-02-27
&proposed_time=15:00
```

### Obtener Conversaciones Activas
```bash
GET /active-conversations
```

### Posponer Conversación
```bash
POST /postpone-conversation
?phone_number=+14084223904
&minutes=60
```

## 🔄 Flujo de Monitoreo Inteligente

```
┌─────────────────────────────────────────────┐
│  Modo Pasivo: Verificar cada 5 minutos      │
│  (Sin conversaciones activas)                │
└──────────────┬──────────────────────────────┘
               │
               ├─ ¿Nuevo mensaje?
               │
               ├─ SÍ → Analizar con IA
               │       │
               │       ├─ ¿Es publicidad?
               │       │  └─ SÍ → Ignorar, volver a modo pasivo
               │       │
               │       └─ ¿Requiere respuesta?
               │          └─ SÍ → Cambiar a Modo Activo
               │
               └─ NO → Esperar 5 minutos

┌─────────────────────────────────────────────┐
│  Modo Activo: Verificar instantáneamente    │
│  (Conversación en progreso)                 │
└──────────────┬──────────────────────────────┘
               │
               ├─ Responder inmediatamente
               ├─ Monitorear siguiente mensaje
               │
               ├─ ¿Conversación completada?
               │  (Cita agendada o cliente se despide)
               │
               └─ SÍ → Volver a Modo Pasivo
```

## 🧠 Análisis de Contexto

El sistema detecta automáticamente:

- **Solicitud de Cita**: "Quiero agendar una cita"
- **Cambio de Cita**: "Necesito cambiar mi cita"
- **Consulta General**: "¿Cuál es tu horario?"
- **Publicidad**: "Descuento 50% en..."
- **Desconocido**: Otros tipos de mensajes

## 📝 Saludos Formales

Los saludos se adaptan a la hora del día:

- **6:00 - 11:59**: "Buenos días"
- **12:00 - 17:59**: "Buenas tardes"
- **18:00 - 23:59**: "Buenas noches"
- **0:00 - 5:59**: "Buenos días"

Ejemplo de saludo completo:
```
"Muy buenas tardes, mi nombre es Jarvis, soy el asistente personal del Sr. Sergio Sánchez. 
¿Puedo ayudarlo programando alguna cita o recordándole que se comunique con usted en la brevedad?"
```

## 🔧 Troubleshooting

### Error: "HF_TOKEN not found"
- Verificar que HF_TOKEN está en .env
- Verificar que el token es válido en https://huggingface.co/settings/tokens

### Error: "GOOGLE_CALENDAR_CREDENTIALS not found"
- Verificar que GOOGLE_CALENDAR_CREDENTIALS está en .env
- Verificar que es un JSON válido (sin saltos de línea)

### Error: "Connection refused"
- Verificar que el servidor está corriendo
- Verificar puerto (default 8000)
- En Termux, verificar que no hay otra app usando el puerto

### Respuestas lentas
- Hugging Face puede tardar en primera llamada
- Verificar conexión a internet
- Verificar que HF_TOKEN tiene acceso a Mistral 7B

## 📚 Documentación Adicional

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Hugging Face API](https://huggingface.co/docs/api-inference/index)
- [Google Calendar API](https://developers.google.com/calendar/api/guides/overview)

## 📄 Licencia

MIT License - Libre para usar y modificar

## 👤 Autor

Sergio Sánchez - Asistente Personal Jarvis

---

**¿Necesitas ayuda?** Abre un issue en GitHub o contacta al desarrollador.
