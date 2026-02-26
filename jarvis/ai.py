"""
Módulo de Inteligencia Artificial
Soporta Ollama local y HuggingFace como fallback
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

class AIAgent:
    """Agente de IA para Jarvis"""

    def __init__(self):
        # Configuración Ollama
        self.ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')

        # Configuración HuggingFace (fallback)
        self.hf_token = os.getenv('HF_TOKEN', '')
        self.hf_model = os.getenv('HF_MODEL', 'meta-llama/Llama-3.2-1B-Instruct')

        # Preferencias
        self.use_ollama = os.getenv('USE_OLLAMA', 'false').lower() == 'true'

        logger.info(f"IA inicializada - Ollama: {self.use_ollama}, HF: {bool(self.hf_token)}")

    def get_response(self, message, client_context=None):
        """Obtener respuesta de IA"""

        # Construir contexto
        context = ""
        if client_context:
            name = client_context.get('name', 'Cliente')
            context = f"Eres el asistente de Sergio. Estás hablando con {name}. "

        # Instrucciones del sistema
        system_prompt = """Eres Jarvis, el asistente personal de Sergio.
- Responde de forma profesional y amable
- Sé breve y conciso
- Si no puedes ayudar, indica que pasarás el mensaje a Sergio
- Nunca reveles información sensible
- Si alguien pide contactar a Sergio, indica que le informarás"""

        # Intentar Ollama si está habilitado
        if self.use_ollama:
            try:
                response = self._ollama_request(message, system_prompt)
                if response:
                    return response
            except Exception as e:
                logger.warning(f"Ollama no disponible: {e}")

        # Fallback a HuggingFace
        if self.hf_token:
            try:
                response = self._huggingface_request(message, system_prompt)
                if response:
                    return response
            except Exception as e:
                logger.warning(f"HuggingFace no disponible: {e}")

        # Respuesta por defecto
        return "He recibido tu mensaje. Sergio te contactará pronto."

    def _ollama_request(self, message, system_prompt):
        """Hacer request a Ollama"""

        full_prompt = f"{system_prompt}\n\nMensaje del usuario: {message}\nRespuesta:"

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 150
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()

        except Exception as e:
            logger.error(f"Error en Ollama: {e}")

        return None

    def _huggingface_request(self, message, system_prompt):
        """Hacer request a HuggingFace Inference API"""

        if not self.hf_token:
            return None

        headers = {"Authorization": f"Bearer {self.hf_token}"}

        payload = {
            "inputs": f"<|system|>{system_prompt}<|user|>{message}<|assistant|>",
            "parameters": {
                "max_new_tokens": 150,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }

        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{self.hf_model}",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '')
                    # Extraer solo la respuesta del asistente
                    if '<|assistant|>' in text:
                        return text.split('<|assistant|>')[-1].strip()
                    return text.strip()

        except Exception as e:
            logger.error(f"Error en HuggingFace: {e}")

        return None

