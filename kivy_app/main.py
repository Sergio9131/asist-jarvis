"""
Jarvis - Asistente Personal SMS
App Kivy para Android con monitoreo 24/7
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.core.window import Window

import requests
import json
import logging
from datetime import datetime
from threading import Thread
import os

# Configurar ventana
Window.size = (360, 640)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JarvisApp(App):
    """Aplicación principal de Jarvis"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Configuración
        self.backend_url = os.getenv("BACKEND_URL", "http://192.168.1.100:8000")
        self.owner_name = os.getenv("OWNER_NAME", "Sergio Sanchez")
        self.owner_phone = os.getenv("OWNER_PHONE", "+14084223904")
        
        # Estado
        self.monitoring_active = False
        self.connected_to_backend = False
        self.active_conversations = []
        self.messages_log = []
        
        # UI Elements
        self.status_label = None
        self.log_text = None
        self.start_button = None
        self.stop_button = None
        self.config_button = None
        
    def build(self):
        """Construir interfaz de la app"""
        
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # ==================== HEADER ====================
        header = BoxLayout(size_hint_y=0.15, padding=5, spacing=5)
        
        # Logo/Título
        title_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        title_label = Label(
            text='Jarvis',
            font_size='24sp',
            bold=True,
            color=(0.04, 0.49, 0.64, 1)  # Azul
        )
        subtitle_label = Label(
            text='Asistente Personal SMS',
            font_size='12sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        title_layout.add_widget(title_label)
        title_layout.add_widget(subtitle_label)
        header.add_widget(title_layout)
        
        # Estado
        self.status_label = Label(
            text='Desconectado',
            font_size='14sp',
            color=(1, 0.3, 0.3, 1),  # Rojo
            size_hint_x=0.3
        )
        header.add_widget(self.status_label)
        
        main_layout.add_widget(header)
        
        # ==================== CONTROLES ====================
        controls = BoxLayout(size_hint_y=0.12, spacing=10, padding=5)
        
        self.start_button = Button(
            text='Iniciar',
            background_color=(0.04, 0.49, 0.64, 1),
            size_hint_x=0.33
        )
        self.start_button.bind(on_press=self.start_monitoring)
        controls.add_widget(self.start_button)
        
        self.stop_button = Button(
            text='Detener',
            background_color=(0.8, 0.2, 0.2, 1),
            size_hint_x=0.33,
            disabled=True
        )
        self.stop_button.bind(on_press=self.stop_monitoring)
        controls.add_widget(self.stop_button)
        
        self.config_button = Button(
            text='Configurar',
            background_color=(0.5, 0.5, 0.5, 1),
            size_hint_x=0.34
        )
        self.config_button.bind(on_press=self.show_config)
        controls.add_widget(self.config_button)
        
        main_layout.add_widget(controls)
        
        # ==================== INFORMACIÓN ====================
        info_layout = GridLayout(cols=2, size_hint_y=0.15, spacing=10, padding=5)
        
        # Conexión
        info_layout.add_widget(Label(text='Backend:', font_size='11sp', bold=True))
        self.backend_label = Label(text='Desconectado', font_size='11sp', color=(1, 0.3, 0.3, 1))
        info_layout.add_widget(self.backend_label)
        
        # Conversaciones activas
        info_layout.add_widget(Label(text='Conversaciones:', font_size='11sp', bold=True))
        self.conversations_label = Label(text='0', font_size='11sp')
        info_layout.add_widget(self.conversations_label)
        
        # Mensajes procesados
        info_layout.add_widget(Label(text='Mensajes:', font_size='11sp', bold=True))
        self.messages_label = Label(text='0', font_size='11sp')
        info_layout.add_widget(self.messages_label)
        
        # Última actualización
        info_layout.add_widget(Label(text='Última actualización:', font_size='11sp', bold=True))
        self.last_update_label = Label(text='Nunca', font_size='11sp')
        info_layout.add_widget(self.last_update_label)
        
        main_layout.add_widget(info_layout)
        
        # ==================== LOG ====================
        log_label = Label(text='Log de Actividad', font_size='12sp', bold=True, size_hint_y=0.05)
        main_layout.add_widget(log_label)
        
        scroll_view = ScrollView(size_hint_y=0.58)
        self.log_text = Label(
            text='Iniciando Jarvis...\n',
            font_size='10sp',
            markup=True,
            size_hint_y=None,
            text_size=(330, None)
        )
        self.log_text.bind(texture_size=self.log_text.setter('size'))
        scroll_view.add_widget(self.log_text)
        main_layout.add_widget(scroll_view)
        
        # Verificar conexión al iniciar
        Clock.schedule_once(lambda dt: self.check_backend_connection(), 1)
        
        return main_layout
    
    def log_message(self, message: str, level: str = "INFO"):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Colores según nivel
        if level == "ERROR":
            color = "[color=ff3333]"
        elif level == "SUCCESS":
            color = "[color=33ff33]"
        elif level == "WARNING":
            color = "[color=ffff33]"
        else:
            color = "[color=ffffff]"
        
        log_entry = f"{color}[{timestamp}] {message}[/color]\n"
        
        # Agregar al log
        self.log_text.text += log_entry
        
        # Mantener solo últimas 50 líneas
        lines = self.log_text.text.split('\n')
        if len(lines) > 50:
            self.log_text.text = '\n'.join(lines[-50:])
        
        logger.info(f"{level}: {message}")
    
    def check_backend_connection(self):
        """Verificar conexión con backend"""
        try:
            response = requests.get(
                f"{self.backend_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                self.connected_to_backend = True
                self.backend_label.text = "Conectado ✓"
                self.backend_label.color = (0.2, 0.8, 0.2, 1)  # Verde
                self.log_message("Conectado con backend", "SUCCESS")
            else:
                self.connected_to_backend = False
                self.backend_label.text = "Error"
                self.backend_label.color = (1, 0.3, 0.3, 1)  # Rojo
                self.log_message(f"Backend error: {response.status_code}", "ERROR")
        
        except Exception as e:
            self.connected_to_backend = False
            self.backend_label.text = "Desconectado"
            self.backend_label.color = (1, 0.3, 0.3, 1)  # Rojo
            self.log_message(f"No se pudo conectar: {str(e)}", "ERROR")
        
        # Reintentar cada 30 segundos
        Clock.schedule_once(lambda dt: self.check_backend_connection(), 30)
    
    def start_monitoring(self, instance):
        """Iniciar monitoreo"""
        if not self.connected_to_backend:
            self.log_message("No hay conexión con backend", "ERROR")
            return
        
        self.monitoring_active = True
        self.status_label.text = "Monitorando"
        self.status_label.color = (0.2, 0.8, 0.2, 1)  # Verde
        
        self.start_button.disabled = True
        self.stop_button.disabled = False
        
        self.log_message("Monitoreo iniciado", "SUCCESS")
        
        # Iniciar thread de monitoreo
        Thread(target=self.monitoring_loop, daemon=True).start()
    
    def stop_monitoring(self, instance):
        """Detener monitoreo"""
        self.monitoring_active = False
        self.status_label.text = "Detenido"
        self.status_label.color = (1, 0.3, 0.3, 1)  # Rojo
        
        self.start_button.disabled = False
        self.stop_button.disabled = True
        
        self.log_message("Monitoreo detenido", "WARNING")
    
    def monitoring_loop(self):
        """Loop de monitoreo en background"""
        import time
        
        passive_interval = 300  # 5 minutos
        active_interval = 1     # 1 segundo
        
        while self.monitoring_active:
            try:
                # Obtener conversaciones activas
                response = requests.get(
                    f"{self.backend_url}/active-conversations",
                    timeout=5
                )
                
                if response.status_code == 200:
                    conversations = response.json()
                    self.active_conversations = conversations
                    
                    # Actualizar UI
                    Clock.schedule_once(
                        lambda dt: self.update_ui_stats(),
                        0
                    )
                    
                    # Determinar intervalo
                    if conversations:
                        # Modo activo: verificar cada 1 segundo
                        self.log_message(f"Modo ACTIVO: {len(conversations)} conversaciones", "SUCCESS")
                        time.sleep(active_interval)
                    else:
                        # Modo pasivo: verificar cada 5 minutos
                        self.log_message("Modo PASIVO: próxima verificación en 5 minutos", "INFO")
                        time.sleep(passive_interval)
                else:
                    self.log_message(f"Error obteniendo conversaciones: {response.status_code}", "ERROR")
                    time.sleep(10)
            
            except Exception as e:
                self.log_message(f"Error en loop de monitoreo: {str(e)}", "ERROR")
                time.sleep(10)
    
    def update_ui_stats(self):
        """Actualizar estadísticas en UI"""
        # Conversaciones activas
        self.conversations_label.text = str(len(self.active_conversations))
        
        # Mensajes procesados
        self.messages_label.text = str(len(self.messages_log))
        
        # Última actualización
        self.last_update_label.text = datetime.now().strftime("%H:%M:%S")
    
    def show_config(self, instance):
        """Mostrar diálogo de configuración"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Backend URL
        content.add_widget(Label(text='Backend URL:', size_hint_y=0.1, bold=True))
        backend_input = TextInput(
            text=self.backend_url,
            multiline=False,
            size_hint_y=0.1
        )
        content.add_widget(backend_input)
        
        # Owner Name
        content.add_widget(Label(text='Nombre del Propietario:', size_hint_y=0.1, bold=True))
        name_input = TextInput(
            text=self.owner_name,
            multiline=False,
            size_hint_y=0.1
        )
        content.add_widget(name_input)
        
        # Owner Phone
        content.add_widget(Label(text='Teléfono del Propietario:', size_hint_y=0.1, bold=True))
        phone_input = TextInput(
            text=self.owner_phone,
            multiline=False,
            size_hint_y=0.1
        )
        content.add_widget(phone_input)
        
        # Botones
        buttons = BoxLayout(size_hint_y=0.2, spacing=10)
        
        save_button = Button(text='Guardar')
        close_button = Button(text='Cerrar')
        
        buttons.add_widget(save_button)
        buttons.add_widget(close_button)
        
        content.add_widget(buttons)
        
        # Crear popup
        popup = Popup(
            title='Configuración',
            content=content,
            size_hint=(0.9, 0.8)
        )
        
        def save_config(instance):
            self.backend_url = backend_input.text
            self.owner_name = name_input.text
            self.owner_phone = phone_input.text
            self.log_message("Configuración guardada", "SUCCESS")
            popup.dismiss()
        
        save_button.bind(on_press=save_config)
        close_button.bind(on_press=popup.dismiss)
        
        popup.open()


if __name__ == '__main__':
    JarvisApp().run()
