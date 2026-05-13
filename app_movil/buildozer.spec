[app]

# Nombre visible en el launcher de Android
title = LOGIEZE Movil

# Nombre del paquete (solo letras minusculas y numeros, sin espacios)
package.name = logiezemovilapp
package.domain = com.logieze

# Carpeta fuente (donde esta main.py)
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0

# Dependencias Python
# python3, kivy y kivymd son la base
# requests + certifi + urllib3 para las llamadas HTTP
requirements = kivy==2.3.0,kivymd==1.2.0,requests,certifi,urllib3,charset-normalizer,idna

# Permisos Android
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# API y NDK Android
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.sdk = 33

# Arquitecturas (arm64 = telefonos modernos, armeabi = telefonos viejos)
android.archs = arm64-v8a, armeabi-v7a

# Orientacion de pantalla
orientation = portrait
fullscreen = 0

# Icono y presplash (opcional — poner archivos en assets/ si se quiere personalizar)
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
