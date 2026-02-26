"""
Módulo de integración con Google Calendar
Maneja consulta de disponibilidad y creación de eventos/citas
"""

import os
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz

logger = logging.getLogger(__name__)

class GoogleCalendarManager:
    """Gestor de Google Calendar"""

    def __init__(self, credentials_path='credentials.json'):
        self.credentials_path = credentials_path
        self.tz = pytz.timezone('America/Mexico_City')
        self.service = self._build_service()

    def _build_service(self):
        """Construir cliente de Google Calendar API"""
        try:
            # Expand路径
            creds_file = os.path.expanduser(self.credentials_path)

            if not os.path.exists(creds_file):
                logger.warning(f"Archivo de credenciales no encontrado: {creds_file}")
                # Intentar con variable de entorno directa
                import json
                import base64
                creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON', '')
                if creds_json:
                    creds_dict = json.loads(base64.b64decode(creds_json))
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_dict,
                        scopes=['https://www.googleapis.com/auth/calendar']
                    )
                else:
                    return None
            else:
                credentials = service_account.Credentials.from_service_account_file(
                    creds_file,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )

            return build('calendar', 'v3', credentials=credentials)

        except Exception as e:
            logger.error(f"Error construyendo servicio: {e}")
            return None

    def get_available_slots(self, days_ahead=7):
        """Obtener próximos horarios disponibles"""
        if not self.service:
            return []

        try:
            now = datetime.now(self.tz)
            end = now + timedelta(days=days_ahead)

            # Obtener eventos existentes
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Generar slots disponibles (9am - 6pm, lun-vier)
            available = []
            current = now.replace(hour=9, minute=0, second=0, microsecond=0)

            # Si ya pasó la hora de hoy, empezar desde mañana
            if current < now:
                current = now + timedelta(days=1)
                current = current.replace(hour=9)

            while current < end:
                # Solo días laborables
                if current.weekday() < 5:  # 0-4 = lun-vie
                    # Horas disponibles 9-18
                    for hour in range(9, 18):
                        slot = current.replace(hour=hour, minute=0)

                        # Verificar que no esté ocupado
                        if not self._is_time_busy(events, slot):
                            available.append(slot.strftime("%d/%m a las %H:%00 hrs"))

                current += timedelta(days=1)

            return available[:10]  # Máximo 10 opciones

        except Exception as e:
            logger.error(f"Error obteniendo disponibilidad: {e}")
            return []

    def _is_time_busy(self, events, slot):
        """Verificar si un horario está ocupado"""
        slot_start = slot
        slot_end = slot + timedelta(hours=1)

        for event in events:
            event_start = event['start'].get('dateTime', '')
            event_end = event['end'].get('dateTime', '')

            if not event_start or not event_end:
                continue

            try:
                # Parsear fechas
                from datetime import datetime
                e_start = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                e_end = datetime.fromisoformat(event_end.replace('Z', '+00:00'))

                # Convertir a timezone local
                e_start = e_start.astimezone(self.tz)
                e_end = e_end.astimezone(self.tz)

                # Verificar superposición
                if (slot_start < e_end and slot_end > e_start):
                    return True

            except:
                continue

        return False

    def create_appointment(self, title, description, client_phone, duration_minutes=60):
        """Crear una cita/turno"""
        if not self.service:
            raise Exception("Servicio de calendario no disponible")

        now = datetime.now(self.tz)

        # Buscar primer slot disponible
        available = self.get_available_slots(days_ahead=14)

        if not available:
            raise Exception("No hay disponibilidad")

        # Usar primer slot
        slot_str = available[0]
        # Parsear: "dd/mm a las HH:00 hrs"
        from datetime import datetime
        date_part = slot_str.split(' a las ')[0]
        time_part = slot_str.split(' a las ')[1].replace(' hrs', '')

        day, month = map(int, date_part.split('/'))
        hour, minute = map(int, time_part.split(':'))

        start_time = now.replace(day=day, month=month, hour=hour, minute=minute, second=0)

        if start_time < now:
            # Si la fecha ya pasó, usar mes próximo
            start_time = start_time.replace(month=start_time.month + 1)

        end_time = start_time + timedelta(minutes=duration_minutes)

        event = {
            'summary': f"📅 {title}",
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Mexico_City'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Mexico_City'
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 60}
                ]
            }
        }

        created_event = self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        logger.info(f"Cita creada: {created_event.get('htmlLink')}")
        return created_event

    def create_reminder(self, title, reminder_time, description=''):
        """Crear un recordatorio/alerta"""
        if not self.service:
            return None

        # Asegurar timezone
        if reminder_time.tzinfo is None:
            reminder_time = self.tz.localize(reminder_time)

        event = {
            'summary': f"🔔 {title}",
            'description': description,
            'start': {
                'dateTime': reminder_time.isoformat(),
                'timeZone': 'America/Mexico_City'
            },
            'end': {
                'dateTime': (reminder_time + timedelta(minutes=30)).isoformat(),
                'timeZone': 'America/Mexico_City'
            }
        }

        return self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

