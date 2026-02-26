"""
Módulo de Inteligencia Artificial
Utiliza Hugging Face Inference API con Mistral 7B Instruct
"""

import os
import logging
import requests
import json
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Tipos de mensajes detectados"""
    APPOINTMENT_REQUEST = "appointment_request"
    APPOINTMENT_CHANGE = "appointment_change"
    GENERAL_QUERY = "general_query"
    ADVERTISEMENT = "advertisement"
    UNKNOWN = "unknown"


class AIAgent:
    """Agente de IA para Jarvis usando Hugging Face"""

    def __init__(self, hf_token: str = ""):
        """
        Inicializar agente de IA
        
        Args:
            hf_token: Token de Hugging Face para acceso a API
        """
        self.hf_token = hf_token or os.getenv("HF_TOKEN", "")
        self.hf_model = "mistralai/Mistral-7B-Instruct-v0.2"
        self.hf_api_url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
        
        if self.hf_token:
            logger.info(f"✅ IA inicializada con Mistral 7B Instruct")
        else:
            logger.warning("⚠️ HF_TOKEN no configurado - respuestas limitadas")

    def _call_huggingface(self, prompt: str, max_tokens: int = 256) -> Optional[str]:
        """
        Llamar a Hugging Face Inference API
        
        Args:
            prompt: Prompt para el modelo
            max_tokens: Máximo número de tokens en respuesta
            
        Returns:
            Respuesta del modelo o None si falla
        """
        if not self.hf_token:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.95
                }
            }
            
            response = requests.post(
                self.hf_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").strip()
            else:
                logger.error(f"HF API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error calling HuggingFace: {e}")
        
        return None

    def analyze_message(self, message: str, client_name: Optional[str] = None) -> Dict:
        """
        Analizar un mensaje SMS y extraer información
        
        Args:
            message: Texto del mensaje
            client_name: Nombre del cliente (opcional)
            
        Returns:
            Dict con análisis del mensaje
        """
        
        # Prompt para análisis
        analysis_prompt = f"""Analiza el siguiente mensaje SMS y responde en JSON:

Mensaje: "{message}"

Responde EXACTAMENTE en este formato JSON (sin explicaciones adicionales):
{{
    "message_type": "appointment_request|appointment_change|general_query|advertisement|unknown",
    "client_name": "nombre extraído o null",
    "proposed_date": "fecha propuesta en formato YYYY-MM-DD o null",
    "proposed_time": "hora propuesta en formato HH:MM o null",
    "confidence": 0.0-1.0,
    "requires_response": true|false,
    "suggested_response": "respuesta sugerida"
}}

Reglas:
- Si es publicidad, marca como advertisement
- Si pide agendar cita, marca como appointment_request
- Si pide cambiar cita, marca como appointment_change
- Extrae nombres, fechas y horas cuando sea posible
- Confidence: 0.0-1.0 qué tan seguro estás
- requires_response: false solo si es publicidad"""

        try:
            response_text = self._call_huggingface(analysis_prompt, max_tokens=400)
            
            if response_text:
                # Intentar parsear JSON
                try:
                    # Buscar JSON en la respuesta
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        analysis = json.loads(json_str)
                        
                        logger.info(f"📊 Análisis: {analysis.get('message_type', 'unknown')}")
                        return analysis
                except json.JSONDecodeError:
                    logger.warning(f"No se pudo parsear JSON: {response_text}")
        
        except Exception as e:
            logger.error(f"Error analizando mensaje: {e}")
        
        # Fallback: análisis simple sin IA
        return self._fallback_analysis(message, client_name)

    def _fallback_analysis(self, message: str, client_name: Optional[str] = None) -> Dict:
        """
        Análisis fallback sin IA
        """
        message_lower = message.lower()
        
        # Detectar tipo de mensaje
        if any(word in message_lower for word in ["publicidad", "promoción", "oferta", "descuento"]):
            message_type = MessageType.ADVERTISEMENT
            requires_response = False
        elif any(word in message_lower for word in ["cita", "agendar", "reservar", "programar"]):
            message_type = MessageType.APPOINTMENT_REQUEST
            requires_response = True
        elif any(word in message_lower for word in ["cambiar", "mover", "reprogramar"]):
            message_type = MessageType.APPOINTMENT_CHANGE
            requires_response = True
        else:
            message_type = MessageType.GENERAL_QUERY
            requires_response = True
        
        return {
            "message_type": message_type.value,
            "client_name": client_name,
            "proposed_date": None,
            "proposed_time": None,
            "confidence": 0.5,
            "requires_response": requires_response,
            "suggested_response": f"Entendido. Voy a procesar tu solicitud."
        }

    def generate_response(self, message: str, owner_name: str = "Sergio") -> str:
        """
        Generar respuesta automática para un mensaje
        
        Args:
            message: Mensaje original
            owner_name: Nombre del propietario
            
        Returns:
            Respuesta generada
        """
        
        response_prompt = f"""Eres Jarvis, asistente personal de {owner_name}.
Genera una respuesta profesional y breve al siguiente mensaje:

Mensaje recibido: "{message}"

Responde de forma amable, profesional y concisa. Si es necesario agendar una cita, 
ofrece disponibilidad. Si no puedes resolver, indica que pasarás el mensaje a {owner_name}.

Respuesta:"""

        try:
            response = self._call_huggingface(response_prompt, max_tokens=150)
            if response:
                return response.strip()
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
        
        # Respuesta fallback
        return f"Entendido. Voy a procesar tu solicitud y {owner_name} se comunicará contigo en breve."

    def extract_appointment_details(self, message: str) -> Dict:
        """
        Extraer detalles de cita de un mensaje
        
        Args:
            message: Mensaje con información de cita
            
        Returns:
            Dict con detalles extraídos
        """
        
        extraction_prompt = f"""Extrae información de cita del siguiente mensaje:

Mensaje: "{message}"

Responde EXACTAMENTE en este formato JSON:
{{
    "client_name": "nombre o null",
    "phone": "teléfono o null",
    "date": "fecha en YYYY-MM-DD o null",
    "time": "hora en HH:MM o null",
    "duration_minutes": número o 60,
    "notes": "notas adicionales o null"
}}"""

        try:
            response_text = self._call_huggingface(extraction_prompt, max_tokens=200)
            
            if response_text:
                try:
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        
        except Exception as e:
            logger.error(f"Error extrayendo detalles: {e}")
        
        return {
            "client_name": None,
            "phone": None,
            "date": None,
            "time": None,
            "duration_minutes": 60,
            "notes": None
        }

    def is_conversation_complete(self, message: str) -> bool:
        """
        Determinar si una conversación está completa
        (cita agendada o cliente se despide)
        
        Args:
            message: Último mensaje de la conversación
            
        Returns:
            True si la conversación está completa
        """
        
        message_lower = message.lower()
        
        # Palabras que indican fin de conversación
        completion_words = [
            "gracias", "perfecto", "listo", "ok", "confirmado", "agendado",
            "hasta luego", "adiós", "chao", "nos vemos"
        ]
        
        return any(word in message_lower for word in completion_words)
