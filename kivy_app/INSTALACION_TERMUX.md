# Jarvis - Guía de Instalación en Termux

## 📱 Requisitos

- Termux instalado en Android
- 4GB de espacio libre
- Conexión a internet
- Python 3.8+

## 🚀 Paso 1: Preparar Termux

```bash
# Actualizar paquetes
pkg update && pkg upgrade -y

# Instalar dependencias
pkg install python python-pip git clang cython make libjpeg-turbo libpng zlib

# Instalar Java (necesario para buildozer)
pkg install openjdk-17

# Instalar Android SDK (opcional pero recomendado)
pkg install android-tools
```

## 📦 Paso 2: Instalar Buildozer

```bash
# Instalar buildozer y dependencias
pip install buildozer cython

# Instalar Kivy
pip install kivy

# Instalar otras dependencias
pip install requests jnius
```

## 🔧 Paso 3: Configurar Buildozer

```bash
# Navegar al directorio de la app
cd ~/jarvis-backend/kivy_app

# Inicializar buildozer (crea buildozer.spec)
buildozer init

# O usar el spec que ya existe
# buildozer android debug
```

## 🏗️ Paso 4: Compilar APK

```bash
# Compilar APK en modo debug (más rápido)
buildozer android debug

# Esto puede tomar 30-60 minutos la primera vez
# Espera a que termine...
```

### Troubleshooting de Compilación

Si encuentras errores:

```bash
# Limpiar cache
buildozer android clean

# Compilar con logs detallados
buildozer android debug -- --verbose

# Si falla por memoria, aumentar
export JAVA_OPTS="-Xmx512m"
```

## 📥 Paso 5: Instalar APK

Una vez compilado, el APK estará en:
```
~/jarvis-backend/kivy_app/bin/jarvis-2.0.0-debug.apk
```

### Opción A: Instalar localmente en el mismo dispositivo

```bash
# Conectar dispositivo por USB (si es diferente)
adb install -r ~/jarvis-backend/kivy_app/bin/jarvis-2.0.0-debug.apk

# O si estás en Termux del mismo dispositivo:
# Copiar a Downloads y abrir manualmente
cp ~/jarvis-backend/kivy_app/bin/jarvis-2.0.0-debug.apk ~/storage/downloads/

# Luego abre el archivo desde el explorador de archivos
```

### Opción B: Transferir a otra computadora

```bash
# Copiar APK a carpeta compartida
cp ~/jarvis-backend/kivy_app/bin/jarvis-2.0.0-debug.apk ~/storage/downloads/

# O transferir por SSH/SCP
scp ~/jarvis-backend/kivy_app/bin/jarvis-2.0.0-debug.apk usuario@computadora:/ruta/
```

## ⚙️ Paso 6: Configurar Permisos

Después de instalar la app:

1. **Permisos de SMS**:
   - Ajustes → Aplicaciones → Jarvis → Permisos
   - Habilitar: Leer SMS, Enviar SMS

2. **Servicio de Accesibilidad**:
   - Ajustes → Accesibilidad → Servicios
   - Buscar "Jarvis"
   - Activar el servicio

3. **Batería**:
   - Ajustes → Batería → Optimización de batería
   - Excluir Jarvis

## 🔗 Paso 7: Configurar Conexión con Backend

1. Abre la app Jarvis
2. Haz clic en "Configurar"
3. Ingresa:
   - **Backend URL**: `http://tu-servidor:8000`
   - **Nombre**: `Sergio Sanchez`
   - **Teléfono**: `+14084223904`
4. Haz clic en "Guardar"

## ▶️ Paso 8: Iniciar Monitoreo

1. Abre la app Jarvis
2. Haz clic en "Iniciar"
3. Verifica que el estado sea "Monitorando" (verde)
4. El log mostrará la actividad

## 🔄 Actualizar Backend

Si necesitas cambiar la URL del backend:

```bash
# En Termux, editar variables de entorno
export BACKEND_URL="http://nueva-url:8000"

# O modificar en la app directamente desde "Configurar"
```

## 🐛 Troubleshooting

### "No se puede conectar con backend"
- Verificar que el backend está corriendo: `curl http://backend:8000/health`
- Verificar firewall y puertos abiertos
- Verificar que el dispositivo está en la misma red

### "Permisos denegados"
- Ir a Ajustes → Aplicaciones → Jarvis → Permisos
- Habilitar todos los permisos necesarios

### "Servicio de accesibilidad no funciona"
- Ir a Ajustes → Accesibilidad → Servicios
- Activar "Jarvis"
- Otorgar permisos cuando se solicite

### "La app se cierra"
- Ver logs: `adb logcat | grep Jarvis`
- Verificar conexión a internet
- Reiniciar la app

## 📊 Monitoreo en Background

La app monitorea automáticamente:

- **Modo Pasivo**: Cada 5 minutos (sin conversaciones activas)
- **Modo Activo**: Cada 1 segundo (cuando hay conversación)

Para que funcione 24/7:
1. Excluir de optimización de batería
2. Activar "Mantener despierto" en desarrollo
3. Permitir que se ejecute en background

## 📝 Logs

Ver logs de la app:
```bash
adb logcat | grep Jarvis
```

O desde Termux:
```bash
tail -f ~/jarvis-backend/kivy_app/logs.txt
```

## 🆘 Soporte

Si tienes problemas:

1. Verificar que el backend está corriendo
2. Verificar conexión a internet
3. Ver logs de la app
4. Reiniciar la app
5. Contactar al desarrollador

---

**¡Jarvis está listo para funcionar 24/7!**
