"""
Módulo de integración con Google Calendar
Maneja creación, consulta y gestión de eventos/citas
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz

logger = logging.getLogger(__name__)


class GoogleCalendarManager:
    """Gestor de Google Calendar"""

    def __init__(self, credentials: Optional[Dict] = None):
        """
        Inicializar gestor de Google Calendar
        
        Args:
            credentials: Dict con credenciales de service account
                        o None para cargar de GOOGLE_CALENDAR_CREDENTIALS env var
        """
        self.tz = pytz.timezone('America/Mexico_City')
        self.service = self._build_service(credentials)
        self.calendar_id = 'primary'

    def _build_service(self, credentials: Optional[Dict] = None):
        """
        Construir cliente de Google Calendar API
        
        Args:
            credentials: Dict con credenciales o None
            
        Returns:
            Servicio de Google Calendar o None si falla
        """
        try:
            # Obtener credenciales
            if credentials is None:
                creds_json = os.getenv('GOOGLE_CALENDAR_CREDENTIALS', '')
                if creds_json:
                    credentials = json.loads(creds_json)
                else:
                    logger.error("No credentials provided or found in environment")
                    return None
            
            # Crear credenciales de service account
            creds = service_account.Credentials.from_service_account_info(
                credentials,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            # Construir servicio
            service = build('calendar', 'v3', credentials=creds)
            logger.info("✅ Google Calendar API conectado")
            return service
        
        except Exception as e:
            logger.error(f"❌ Error construyendo servicio Calendar: {e}")
            return None

    def create_event(self, event_data: Dict) -> Optional[str]:
        """
        Crear un evento en Google Calendar
        
        Args:
            event_data: Dict con datos del evento
            
        Returns:
            ID del evento creado o None si falla
        """
        if not self.service:
            logger.error("Calendar service not initialized")
            return None

        try:
            event = {
                'summary': event_data.get('summary', 'Cita'),
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': event_data['start']['dateTime'],
                    'timeZone': 'America/Mexico_City'
                },
                'end': {
                    'dateTime': event_data['end']['dateTime'],
                    'timeZone': 'America/Mexico_City'
                }
            }
            
            if 'attendees' in event_data:
                event['attendees'] = event_data['attendees']
            
            result = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info(f"✅ Evento creado: {result['id']}")
            return result['id']
        
        except HttpError as e:
            logger.error(f"❌ Error creando evento: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return None

    def get_upcoming_events(self, max_results: int = 10) -> List[Dict]:
        """
        Obtener próximos eventos
        
        Args:
            max_results: Máximo número de eventos
            
        Returns:
            Lista de eventos
        """
        if not self.service:
            logger.error("Calendar service not initialized")
            return []

        try:
            now = datetime.now(self.tz).isoformat()
            
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"📅 {len(events)} próximos eventos")
            return events
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo eventos: {e}")
            return []

    def check_availability(self, start_time: str, end_time: str) -> bool:
        """
        Verificar disponibilidad en un rango de tiempo
        
        Args:
            start_time: Hora de inicio en formato ISO
            end_time: Hora de fin en formato ISO
            
        Returns:
            True si está disponible, False si hay conflicto
        """
        if not self.service:
            logger.error("Calendar service not initialized")
            return False

        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time,
                timeMax=end_time,
                singleEvents=True
            ).execute()
            
            events = events_result.get('items', [])
            available = len(events) == 0
            
            logger.info(f"{'✅' if available else '❌'} Disponibilidad {start_time}: {available}")
            return available
        
        except Exception as e:
            logger.error(f"❌ Error verificando disponibilidad: {e}")
            return False

    def get_available_slots(self, days_ahead: int = 7, slot_duration_minutes: int = 60) -> List[Dict]:
        """
        Obtener slots disponibles para los próximos días
        
        Args:
            days_ahead: Número de días a buscar
            slot_duration_minutes: Duración de cada slot
            
        Returns:
            Lista de slots disponibles
        """
        available_slots = []
        now = datetime.now(self.tz)

        try:
            for day in range(days_ahead):
                current_date = now + timedelta(days=day)
                
                # Horario de trabajo: 9 AM a 5 PM
                for hour in range(9, 17):
                    slot_start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    slot_end = slot_start + timedelta(minutes=slot_duration_minutes)
                    
                    if self.check_availability(
                        slot_start.isoformat(),
                        slot_end.isoformat()
                    ):
                        available_slots.append({
                            'date': slot_start.strftime('%Y-%m-%d'),
                            'time': slot_start.strftime('%H:%M'),
                            'datetime': slot_start.isoformat()
                        })
            
            logger.info(f"📅 {len(available_slots)} slots disponibles")
            return available_slots
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo slots: {e}")
            return []

    def update_event(self, event_id: str, event_data: Dict) -> bool:
        """
        Actualizar un evento
        
        Args:
            event_id: ID del evento
            event_data: Nuevos datos del evento
            
        Returns:
            True si se actualizó correctamente
        """
        if not self.service:
            logger.error("Calendar service not initialized")
            return False

        try:
            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event_data
            ).execute()
            
            logger.info(f"✅ Evento actualizado: {event_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error actualizando evento: {e}")
            return False

    def delete_event(self, event_id: str) -> bool:
        """
        Eliminar un evento
        
        Args:
            event_id: ID del evento
            
        Returns:
            True si se eliminó correctamente
        """
        if not self.service:
            logger.error("Calendar service not initialized")
            return False

        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"✅ Evento eliminado: {event_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Error eliminando evento: {e}")
            return False
