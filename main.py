Jarvis - Asistente 24/7 de Sergio          Servidor Flask para Twitter + Google Calendar + IA                                    """

from flask import Flask, request, jsonify, abort                                      from twilio.twiml import MessagingResponse
import os
import json
import logging
from datetime import datetime, timedelta
import pytz

# Importar módulos de Jarvis
from jarvis.calendar import GoogleCalendarManager
from jarvis.ai import AIAgent
from jarvis.database import ClientDatabase
from jarvis.responses import ResponseGenerator

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variables de entorno
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+14084223904')
GOOGLE_CREDS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json')

# Inicializar componentes
calendar_manager = None
ai_agent = None
db = None
response_gen = None

# Zona horaria México
TZ_MEXICO = pytz.timezone('America/Mexico_City')

def initialize_services():
    """Inicializar todos los servicios"""
    global calendar_manager, ai_agent, db, response_gen

    try:
        # Inicializar Google Calendar
        calendar_manager = GoogleCalendarManager(GOOGLE_CREDS)
        logger.info("✅ Google Calendar inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando Calendar: {e}")
        calendar_manager = None

    try:
        # Inicializar IA
        ai_agent = AIAgent()
        logger.info("✅ IA Agent inicializado")
    except Exception as e:
        logger.error(f"❌ Error inicializando IA: {e}")
        ai_agent = None

    # Inicializar base de datos
    db = ClientDatabase()
    logger.info("✅ Base de datos inicializada")

    # Inicializar generador de respuestas
    response_gen = ResponseGenerator()
    logger.info("✅ Response Generator inicializado")

def get_greeting():
    """Obtener saludo según la hora"""
    now = datetime.now(TZ_MEXICO)
    hour = now.hour

    if 6 <= hour < 12:
        return "Buenos días"
    elif 12 <= hour < 19:
        return "Buenas tardes"
    else:
        return "Buenas noches"

def process_message(from_number, message_body):
    """Procesar mensaje entrante - Lógica principal de Jarvis"""

    logger.info(f"Mensaje de {from_number}: {message_body}")

    # 1. Verificar si es cliente conocido
    client = db.get_client(from_number)

    if client:
        # Cliente conocido - procesar según tipo de solicitud
        return handle_known_client(client, message_body)
    else:
        # Nuevo contacto - manejar apropiadamente
        return handle_new_contact(from_number, message_body)

def handle_known_client(client, message_body):
    """Manejar mensaje de cliente conocido"""

    name = client.get('name', 'Cliente')
    greeting = get_greeting()
    msg_lower = message_body.lower()

    # Verificar si solicita cita
    if any(word in msg_lower for word in ['cita', 'agendar', 'appointment', 'reunión', 'hora']):
        return handle_appointment_request(client, message_body)

    # Verificar si es una confirmación de cita (contiene fecha/hora)
    if any(word in msg_lower for word in ['si', 'sí', 'confirmo', 'ok', 'vale', 'perfecto']):
        if client.get('pending_appointment'):
            return confirm_appointment(client, message_body)

    # Verificar si quiere postergar
    if 'postergar' in msg_lower or 'posponer' in msg_lower:
        return handle_postergate(client, message_body)

    # Consulta normal - usar IA
    if ai_agent:
        ai_response = ai_agent.get_response(message_body, client)
        return f"{greeting}, {name}. {ai_response}"

    return f"{greeting}, {name}. He recibido tu mensaje. Te contactaremos pronto."

def handle_appointment_request(client, message_body):
    """Manejar solicitud de cita"""

    name = client.get('name', 'Cliente')
    greeting = get_greeting()

    # Buscar disponibilidad en Google Calendar
    if not calendar_manager:
        return f"{greeting}, {name}. Lo siento, el sistema de citas no está disponible temporalmente."

    # Obtener próximos 7 días disponibles
    available_slots = calendar_manager.get_available_slots(days_ahead=7)

    if available_slots and len(available_slots) > 0:
        # Guardar cita pendiente temporalmente
        db.update_client(client['phone'], {
            'pending_appointment': True,
            'message': message_body
        })

        # Mostrar opciones
        slots_text = "\n".join([f"📅 {slot}" for slot in available_slots[:5]])
        return (f"{greeting}, {name}. Tengo los siguientes horarios disponibles:\n\n"
                f"{slots_text}\n\n"
                f"¿Cuál prefieres? (responde con el número o fecha)")
    else:
        return f"{greeting}, {name}. No tengo disponibilidad en los próximos días. ¿Te gustaría contactarte otro día?"

def confirm_appointment(client, message_body):
    """Confirmar y guardar cita"""

    name = client.get('name', 'Cliente')
    greeting = get_greeting()

    # Extraer fecha/hora del mensaje del cliente
    # Por defecto, usar el primer slot disponible
    available_slots = calendar_manager.get_available_slots(days_ahead=7)

    if not available_slots:
        return f"{greeting}, {name}. Lo siento, ya no hay disponibilidad."

    # Usar primer slot disponible
    slot_str = available_slots[0]

    try:
        # Parsear fecha y crear evento
        event = calendar_manager.create_appointment(
            title=f"Cita con {name}",
            description=f"Cliente: {name}\nTeléfono: {client['phone']}\nMensaje: {message_body}",
            client_phone=client['phone']
        )

        # Limpiar cita pendiente
        db.update_client(client['phone'], {'pending_appointment': None})

        return (f"✅ {greeting}, {name}. Tu cita ha sido confirmada para el {slot_str}. "
                f"Te enviaremos un recordatorio antes. ¡Nos vemos pronto!")

    except Exception as e:
        logger.error(f"Error al agendar: {e}")
        return f"{greeting}, {name}. Hubo un problema al agendar. Por favor intenta más tarde."

def handle_postergate(client, message_body):
    """Manejar solicitud de postergar"""

    greeting = get_greeting()

    # Crear recordatorio para 1 hora después
    reminder_time = datetime.now(TZ_MEXICO) + timedelta(hours=1)

    if calendar_manager:
        try:
            calendar_manager.create_reminder(
                title=f"Contactar a {client.get('name', client['phone'])}",
                reminder_time=reminder_time,
                description=f"Número: {client['phone']}\nCliente pidió postergar"
            )
        except Exception as e:
            logger.error(f"Error creando recordatorio: {e}")

    return f"{greeting}. He notificado a Sergio que le contactará en aproximadamente 1 hora."

def handle_new_contact(from_number, message_body):
    """Manejar nuevo contacto"""

    greeting = get_greeting()

    # Registrar nuevo contacto
    db.add_client(from_number, f"Cliente {from_number[-4:]}")

    return (f"{greeting}. Soy Jarvis, asistente de Sergio. "
            f"Se quiere comunicar contigo el número {from_number}. "
            f"¿Deseas continuar la conversación? "
            f"(Responde 'si' para que Sergio te contacte, o 'no' para rechazar)")

# Webhooks de Twilio
@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook principal para recibir SMS de Twilio"""

    try:
        # Verificar autenticación básica de Twilio
        # En producción, verificarSignature de Twilio

        incoming_msg = request.values.get('Body', '').strip()
        from_number = request.values.get('From', '')

        if not incoming_msg or not from_number:
            return jsonify({"error": "Mensaje inválido"}), 400

        # Procesar mensaje
        response_text = process_message(from_number, incoming_msg)

        # Responder via Twilio
        resp = MessagingResponse()
        resp.message(response_text)

        return str(resp)

    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return jsonify({"error": "Error interno"}), 500

@app.route('/webhook/status', methods=['POST'])
def webhook_status():
    """Webhook para recibir estados de mensajes"""
    message_sid = request.values.get('MessageSid', '')
    message_status = request.values.get('MessageStatus', '')
    logger.info(f"Mensaje {message_sid}: {message_status}")
    return "OK"

@app.route('/health', methods=['GET'])
def health():
    """Verificar estado del servidor"""
    return jsonify({
        "status": "running",
        "assistant": "Jarvis",
        "version": "1.0.0",
        "services": {
            "calendar": calendar_manager is not None,
            "ai": ai_agent is not None,
            "database": db is not None
        }
    })

@app.route('/', methods=['GET'])
def index():
    """Página principal"""
    return """
    <html>
    <head><title>Jarvis - Asistente de Sergio</title></head>
    <body style="font-family: Arial; padding: 40px; text-align: center;">
        <h1>🤖 Jarvis</h1>
        <p>Asistente personal de Sergio</p>
        <p>Estado: <strong>Activo 24/7</strong></p>
        <p><small>Versión 1.0.0</small></p>
    </body>
    </html>
    """

# Inicializar al iniciar
initialize_services()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

