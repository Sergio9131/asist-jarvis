"""
Utilidades generales para Jarvis
"""

from datetime import datetime
import pytz
import re

def get_current_time_mexico():
    """Obtener hora actual en México"""
    tz = pytz.timezone('America/Mexico_City')
    return datetime.now(tz)

def format_phone(phone):
    """Formatear número de teléfono"""
    # Eliminar caracteres no numéricos
    digits = re.sub(r'\D', '', phone)

    # Agregar código de país si no lo tiene
    if not digits.startswith('52') and not digits.startswith('+52'):
        if digits.startswith('0'):
            digits = '52' + digits[1:]
        else:
            digits = '52' + digits

    return f"+{digits}"

def extract_date_from_message(message):
    """Extraer posible fecha de un mensaje"""
    # Patrones comunes: "para mañana", "el lunes", "15/02", "15 de febrero"
    message = message.lower()

    # Lógica simple - expandir según necesidad
    return None

def is_weekend(dt):
    """Verificar si es fin de semana"""
    return dt.weekday() >= 5  # 5=sábado, 6=domingo

def is_business_hours(dt):
    """Verificar si es horario laboral (9am-6pm)"""
    hour = dt.hour
    return 9 <= hour < 18 and not is_weekend(dt)

