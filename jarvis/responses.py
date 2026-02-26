"""
Módulo de respuestas predefinidas
Genera respuestas formales según el contexto
"""

from datetime import datetime
import pytz

class ResponseGenerator:
    """Generador de respuestas"""

    def __init__(self):
        self.tz = pytz.timezone('America/Mexico_City')

    def greeting(self):
        """Saludo según hora"""
        hour = datetime.now(self.tz).hour

        if 6 <= hour < 12:
            return "Buenos días"
        elif 12 <= hour < 19:
            return "Buenas tardes"
        else:
            return "Buenas noches"

    def introduction(self, owner_name="Sergio"):
        """Presentación"""
        return f"Soy Jarvis, asistente de {owner_name}. ¿En qué puedo ayudarle?"

    def appointment_confirmed(self, date, time):
        """Confirmación de cita"""
        return (f"✅ Su cita ha sido confirmada para el {date} a las {time}. "
                f"Serge le contactará para confirmar los detalles.")

    def busy_message(self):
        """Mensaje de ocupado"""
        return ("Sergio se encuentra ocupado en este momento, "
                "pero se comunicará con usted a la brevedad posible.")

    def postergate_accepted(self, reminder_time):
        """Mensaje de postergación aceptada"""
        return (f"He registrado su solicitud. Sergio le contactará "
                f"aproximadamente a las {reminder_time.strftime('%H:%M')}.")

    def new_contact(self, phone):
        """Mensaje para nuevo contacto"""
        return (f"Se quiere comunicar contigo el número {phone}. "
                f"¿Deseas continuar la conversación?")

    def ask_continuar(self, name_or_phone):
        """Preguntar si desea continuar"""
        return (f"Se quiere comunicar contigo {name_or_phone}. "
                f"¿Deseas continuar la conversación? "
                f"(Responde 'si' para continuar o 'no' para rechazar)")

