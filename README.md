# Jarvis - Asistente SMS con IA

Jarvis es un asistente automático que procesa mensajes SMS entrantes, extrae información usando un modelo de lenguaje y gestiona citas en Google Calendar. 

## Características

- 📱 **Monitoreo de SMS**: Lee los mensajes entrantes.
- 🤖 **Extracción de información**: Utiliza un modelo de IA (vía Ollama) para identificar citas, nombres, fechas y teléfonos.
- 📅 **Integración con Google Calendar**: Crea eventos en tu calendario personal cuando se confirma una cita.
- 💬 **Respuesta automática**: Saluda al cliente según la hora del día y confirma la recepción.
- 👤 **Interacción con el dueño**: Cuando se detecta una cita, pregunta al dueño (vía SMS) si desea confirmarla.
- ⏰ **Recordatorios**: Si el dueño pospone una conversación, crea un recordatorio en Calendar para 1 hora después.
- 🔄 **Persistencia**: Se ejecuta 24/7.
