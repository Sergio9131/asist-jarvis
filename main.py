"""
Jarvis - Asistente Personal SMS con IA
Backend FastAPI para monitoreo inteligente de SMS y gestión de citas
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import json
import logging
from datetime import datetime, timedelta
import pytz
import asyncio
from enum import Enum

# Importar módulos de Jarvis
from jarvis.ai import AIAgent
from jarvis.calendar import GoogleCalendarManager
from jarvis.database import ClientDatabase

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="Jarvis - Asistente Personal SMS",
    description="Backend para automatización de SMS y gestión de citas",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELOS ====================

class MessageType(str, Enum):
    APPOINTMENT_REQUEST = "appointment_request"
    APPOINTMENT_CHANGE = "appointment_change"
    GENERAL_QUERY = "general_query"
    ADVERTISEMENT = "advertisement"
    UNKNOWN = "unknown"


class SMSMessage(BaseModel):
    """Modelo para mensaje SMS"""
    phone_number: str
    message_text: str
    timestamp: Optional[str] = None
    message_id: Optional[str] = None


class MessageAnalysis(BaseModel):
    """Análisis de mensaje por IA"""
    message_type: MessageType
    client_name: Optional[str] = None
    proposed_date: Optional[str] = None
    proposed_time: Optional[str] = None
    confidence: float
    requires_response: bool
    suggested_response: str


class MonitoringConfig(BaseModel):
    """Configuración del monitoreo"""
    owner_name: str
    owner_phone: str
    hf_token: str
    passive_interval_minutes: int = 5
    active_mode: bool = False


class ConversationState(BaseModel):
    """Estado de una conversación activa"""
    phone_number: str
    last_message_time: str
    conversation_active: bool
    appointment_scheduled: bool
    context: dict


# ==================== VARIABLES GLOBALES ====================

# Servicios
ai_agent: Optional[AIAgent] = None
calendar_manager: Optional[GoogleCalendarManager] = None
db: Optional[ClientDatabase] = None

# Configuración
config: Optional[MonitoringConfig] = None

# Estado de conversaciones activas
active_conversations: dict = {}

# Zona horaria
TZ_MEXICO = pytz.timezone('America/Mexico_City')


# ==================== FUNCIONES AUXILIARES ====================

def get_greeting_by_hour() -> str:
    """Obtener saludo formal según la hora del día"""
    now = datetime.now(TZ_MEXICO)
    hour = now.hour

    if 6 <= hour < 12:
        return "Buenos días"
    elif 12 <= hour < 18:
        return "Buenas tardes"
    else:
        return "Buenas noches"


def get_formal_greeting(client_name: Optional[str] = None) -> str:
    """Obtener saludo formal completo"""
    greeting = get_greeting_by_hour()
    if config:
        response = f"{greeting}, mi nombre es Jarvis, soy el asistente personal del Sr. {config.owner_name}. "
        response += "¿Puedo ayudarlo programando alguna cita o recordándole que se comunique con usted en la brevedad?"
        return response
    return greeting


def is_conversation_active(phone_number: str) -> bool:
    """Verificar si hay una conversación activa"""
    if phone_number in active_conversations:
        conv = active_conversations[phone_number]
        if conv["conversation_active"]:
            return True
    return False


def mark_conversation_active(phone_number: str):
    """Marcar conversación como activa"""
    if phone_number not in active_conversations:
        active_conversations[phone_number] = {
            "phone_number": phone_number,
            "last_message_time": datetime.now(TZ_MEXICO).isoformat(),
            "conversation_active": True,
            "appointment_scheduled": False,
            "context": {}
        }
    else:
        active_conversations[phone_number]["conversation_active"] = True
        active_conversations[phone_number]["last_message_time"] = datetime.now(TZ_MEXICO).isoformat()


def mark_conversation_inactive(phone_number: str):
    """Marcar conversación como inactiva"""
    if phone_number in active_conversations:
        active_conversations[phone_number]["conversation_active"] = False


# ==================== ENDPOINTS ====================

@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al iniciar la app"""
    global ai_agent, calendar_manager, db, config
    
    logger.info("🚀 Iniciando Jarvis Backend...")
    
    try:
        # Cargar configuración desde variables de entorno
        config = MonitoringConfig(
            owner_name=os.getenv("OWNER_NAME", "Sergio Sanchez"),
            owner_phone=os.getenv("OWNER_PHONE", "+14084223904"),
            hf_token=os.getenv("HF_TOKEN", ""),
            passive_interval_minutes=int(os.getenv("PASSIVE_INTERVAL", "5"))
        )
        logger.info(f"✅ Configuración cargada: {config.owner_name}")
    except Exception as e:
        logger.error(f"❌ Error cargando configuración: {e}")
        config = None

    try:
        # Inicializar IA
        if config and config.hf_token:
            ai_agent = AIAgent(hf_token=config.hf_token)
            logger.info("✅ Agente IA inicializado (Mistral 7B)")
        else:
            logger.warning("⚠️ HF_TOKEN no configurado")
    except Exception as e:
        logger.error(f"❌ Error inicializando IA: {e}")

    try:
        # Inicializar Google Calendar
        creds_json = os.getenv("GOOGLE_CALENDAR_CREDENTIALS", "")
        if creds_json:
            creds = json.loads(creds_json)
            calendar_manager = GoogleCalendarManager(creds)
            logger.info("✅ Google Calendar inicializado")
        else:
            logger.warning("⚠️ GOOGLE_CALENDAR_CREDENTIALS no configurado")
    except Exception as e:
        logger.error(f"❌ Error inicializando Calendar: {e}")

    try:
        # Inicializar base de datos
        db = ClientDatabase("jarvis_clients.db")
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando BD: {e}")

    logger.info("✅ Jarvis Backend listo para recibir solicitudes")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "status": "online",
        "service": "Jarvis - Asistente Personal SMS",
        "version": "2.0.0",
        "owner": config.owner_name if config else "Unknown"
    }


@app.get("/health")
async def health_check():
    """Verificar salud del servicio"""
    return {
        "status": "healthy",
        "ai_agent": ai_agent is not None,
        "calendar_manager": calendar_manager is not None,
        "database": db is not None,
        "config_loaded": config is not None
    }


@app.post("/analyze-message")
async def analyze_message(message: SMSMessage) -> MessageAnalysis:
    """
    Analizar un mensaje SMS y determinar tipo y respuesta
    
    Lógica:
    - Si es publicidad → ignorar
    - Si requiere respuesta inmediata → responder y marcar conversación activa
    - Si es solicitud de cita → agendar y responder
    """
    
    if not ai_agent:
        raise HTTPException(status_code=503, detail="AI Agent not initialized")

    try:
        # Analizar mensaje con IA
        analysis = ai_agent.analyze_message(message.message_text)
        
        logger.info(f"📊 Análisis: {message.phone_number} - {analysis['message_type']}")
        
        # Determinar si requiere respuesta
        requires_response = analysis["message_type"] != MessageType.ADVERTISEMENT
        
        if requires_response:
            mark_conversation_active(message.phone_number)
        
        return MessageAnalysis(
            message_type=analysis["message_type"],
            client_name=analysis.get("client_name"),
            proposed_date=analysis.get("proposed_date"),
            proposed_time=analysis.get("proposed_time"),
            confidence=analysis.get("confidence", 0.0),
            requires_response=requires_response,
            suggested_response=analysis.get("suggested_response", get_formal_greeting())
        )
    
    except Exception as e:
        logger.error(f"❌ Error analizando mensaje: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/schedule-appointment")
async def schedule_appointment(
    phone_number: str,
    client_name: str,
    proposed_date: str,
    proposed_time: str,
    background_tasks: BackgroundTasks
):
    """
    Agendar una cita en Google Calendar
    """
    
    if not calendar_manager:
        raise HTTPException(status_code=503, detail="Calendar Manager not initialized")

    try:
        # Crear evento
        event = {
            "summary": f"Cita con {client_name}",
            "description": f"Cliente: {client_name}\nTeléfono: {phone_number}",
            "start": {
                "dateTime": f"{proposed_date}T{proposed_time}:00",
                "timeZone": "America/Mexico_City"
            },
            "end": {
                "dateTime": f"{proposed_date}T{proposed_time}:30",
                "timeZone": "America/Mexico_City"
            }
        }
        
        event_id = calendar_manager.create_event(event)
        
        if event_id:
            # Marcar conversación como completada
            mark_conversation_inactive(phone_number)
            
            logger.info(f"✅ Cita agendada: {client_name} - {proposed_date} {proposed_time}")
            
            return {
                "status": "success",
                "event_id": event_id,
                "message": f"Cita agendada para {proposed_date} a las {proposed_time}"
            }
        else:
            raise Exception("Failed to create event")
    
    except Exception as e:
        logger.error(f"❌ Error agendando cita: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/active-conversations")
async def get_active_conversations() -> List[ConversationState]:
    """Obtener conversaciones activas"""
    return [
        ConversationState(**conv) 
        for conv in active_conversations.values() 
        if conv["conversation_active"]
    ]


@app.post("/postpone-conversation")
async def postpone_conversation(phone_number: str, minutes: int = 60):
    """Posponer una conversación"""
    
    mark_conversation_inactive(phone_number)
    
    logger.info(f"⏱️ Conversación pospuesta: {phone_number} por {minutes} minutos")
    
    return {
        "status": "postponed",
        "phone_number": phone_number,
        "resume_in_minutes": minutes
    }


@app.get("/config")
async def get_config():
    """Obtener configuración actual (sin exponer tokens)"""
    if not config:
        raise HTTPException(status_code=503, detail="Config not loaded")
    
    return {
        "owner_name": config.owner_name,
        "owner_phone": config.owner_phone,
        "passive_interval_minutes": config.passive_interval_minutes,
        "active_mode": config.active_mode
    }


@app.post("/config")
async def update_config(new_config: MonitoringConfig):
    """Actualizar configuración"""
    global config
    config = new_config
    logger.info(f"✅ Configuración actualizada: {config.owner_name}")
    return {"status": "updated", "config": config}


# ==================== MONITOREO EN BACKGROUND ====================

async def monitoring_loop():
    """
    Loop de monitoreo inteligente:
    - Modo pasivo: verificar cada 5 minutos
    - Modo activo: verificar instantáneamente cuando hay conversación activa
    """
    
    logger.info("🔄 Iniciando loop de monitoreo...")
    
    while True:
        try:
            if config.active_mode:
                # Modo activo: verificar conversaciones activas
                active = [conv for conv in active_conversations.values() if conv["conversation_active"]]
                
                if active:
                    logger.info(f"📱 {len(active)} conversaciones activas - verificando instantáneamente")
                    await asyncio.sleep(1)  # Verificar cada 1 segundo en modo activo
                else:
                    # Sin conversaciones activas: modo pasivo
                    logger.info(f"😴 Modo pasivo - próxima verificación en {config.passive_interval_minutes} minutos")
                    await asyncio.sleep(config.passive_interval_minutes * 60)
            else:
                # Modo pasivo por defecto
                await asyncio.sleep(config.passive_interval_minutes * 60)
        
        except Exception as e:
            logger.error(f"❌ Error en loop de monitoreo: {e}")
            await asyncio.sleep(60)


# ==================== EJECUCIÓN ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🚀 Iniciando Jarvis en puerto {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
