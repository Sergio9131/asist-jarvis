[app]

# Información de la app
title = Jarvis - Asistente Personal SMS
package.name = jarvis
package.domain = org.jarvis

# Archivos fuente
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

# Versión
version = 2.0.0

# Requisitos
requirements = python3,kivy,requests,jnius

# Permisos de Android
android.permissions = INTERNET,READ_SMS,SEND_SMS,RECEIVE_SMS,WRITE_SMS,ACCESS_NETWORK_STATE,CHANGE_NETWORK_STATE,BIND_ACCESSIBILITY_SERVICE,SYSTEM_ALERT_WINDOW,WAKE_LOCK

# Features
android.features = android.hardware.telephony

# Arquitectura
android.archs = arm64-v8a,armeabi-v7a

# Orientación
orientation = portrait

# Iconos
icon.filename = %(source.dir)s/data/icon.png

# Splash
presplash.filename = %(source.dir)s/data/presplash.png

# Configuración de compilación
[buildozer]

# Log level
log_level = 2

# Warn on root
warn_on_root = 1

# Versión de NDK
android.ndk = 25b

# Versión de SDK
android.sdk = 33

# API level
android.api = 33

# Mínimo API level
android.minapi = 21

# Target API level
android.target_api = 33

# Bootstrap
p4a.bootstrap = sdl2
