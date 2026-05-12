LOGIEZE Movil - App Android v1.0
=================================

ESTRUCTURA DEL PROYECTO
------------------------
wannacos_movil/
  servidor/
    api.py              <- Flask API (corre en el servidor LOGIEZE)
    INICIAR_API.bat     <- Iniciar API con ventana CMD (para ver logs)
    INICIAR_API.vbs     <- Iniciar API en background (sin ventana)
  app_movil/
    main.py             <- App Kivy/KivyMD (este archivo es la app)
    buildozer.spec      <- Config para compilar el APK
    requirements.txt    <- Dependencias para probar en desktop
    README.txt          <- Este archivo


=====================================
PASO 1 — CONFIGURAR EL SERVIDOR
=====================================

En el servidor LOGIEZE:

1. Instalar dependencias de la API (solo la primera vez):
   C:\LOGIEZE\python\python.exe -m pip install flask psycopg2-binary

2. Iniciar la API de dos formas posibles:
   a) SIN ventana (recomendado): doble clic en INICIAR_API.vbs
   b) CON ventana (para ver errores): doble clic en INICIAR_API.bat

3. Verificar que la API corre:
   Abrir en el servidor: http://localhost:5050/ping
   Deberia mostrar: {"ok": true, "ts": "..."}

4. Activar el tunel Cloudflare:
   Doble clic en acceso directo "LOGIEZE Tunnel Internet"
   (o ejecutar C:\LOGIEZE\TUNNEL_INTERNET.bat)

   Cloudflare mostrara una URL como:
   https://algo-random.trycloudflare.com

   IMPORTANTE: Copiar esa URL, la necesitas en la app Android.

NOTA: La URL del tunel cambia cada vez que reinicias cloudflared.
Para una URL fija, crear un tunel permanente en dash.cloudflare.com
(requiere cuenta gratuita de Cloudflare).


=====================================
PASO 2 — CONFIGURAR LA APP ANDROID
=====================================

Al abrir la app por primera vez aparece la pantalla de configuracion:

1. "URL Tunel Cloudflare": pegar la URL del tunel
   Ej: https://algo-random.trycloudflare.com

2. "Token de acceso": dejar "logieze_movil_2024"
   (coincide con API_TOKEN en servidor/api.py)

3. Presionar "GUARDAR Y CONECTAR"

La configuracion se guarda automaticamente para la proxima vez.
Para cambiarla: usar el boton "Config" en la pestana Stock.


=====================================
FUNCIONALIDADES DE LA APP
=====================================

STOCK
  - Buscar productos por nombre, codigo interno o codigo de barras
  - Ver detalle: stock total, salon 3, precio, costo, barras, categoria
  - Boton "IR A MOVER" para cargar el producto directamente en Mover

MOVER (registrar movimientos)
  - Buscar producto por codigo
  - Elegir tipo: ENTRADA (suma), SALIDA (resta), AJUSTE (fija valor)
  - Ingresar cantidad y ubicacion opcional
  - El movimiento queda registrado en historial

PEDIDOS
  - Ver presupuestos, carros de compra y reposiciones
  - Filtrar por estado: Pendientes / Completados / Cancelados
  - Ver detalle de items de cada pedido
  - Marcar pedidos como Completados o Cancelados

HISTORIAL
  - Ver los ultimos 60 movimientos registrados
  - Muestra tipo, producto, cantidad, fecha, usuario y ubicacion


=====================================
PROBAR EN DESKTOP (Windows)
=====================================

Requiere Python 3.9+ con Kivy instalado:

    pip install -r requirements.txt
    python main.py

La app funciona en desktop para probar antes de compilar el APK.


=====================================
COMPILAR EL APK (requiere Linux o WSL)
=====================================

Buildozer solo funciona en Linux. Opciones:

OPCION A — WSL (Windows Subsystem for Linux)
  1. Instalar Ubuntu desde Microsoft Store
  2. En la terminal WSL:
     sudo apt update && sudo apt install -y python3-pip git zip unzip
     pip install buildozer
  3. Copiar la carpeta app_movil al WSL o acceder por /mnt/c/...
  4. En la carpeta app_movil:
     buildozer android debug
  5. El APK queda en: bin/logiezemovilapp-1.0-debug.apk

OPCION B — Google Colab (gratis, sin instalar nada)
  Hay notebooks de buildozer en Colab que compilan el APK online.
  Buscar: "buildozer google colab kivy apk"

OPCION C — GitHub Actions (gratis)
  Subir el codigo a GitHub y usar una Action de buildozer.

NOTA IMPORTANTE:
La primera compilacion tarda 30-60 minutos (descarga Android SDK/NDK ~2GB).
Las compilaciones siguientes tardan ~5 minutos.


=====================================
INSTALAR EL APK EN ANDROID
=====================================

Metodo 1 — Cable USB:
  adb install bin/logiezemovilapp-1.0-debug.apk

Metodo 2 — Copiar el archivo:
  Copiar el APK al telefono (por cable, WhatsApp, Drive, etc.)
  En el telefono: abrir el archivo APK e instalar
  (puede requerir habilitar "Instalar apps de fuentes desconocidas"
   en Ajustes > Seguridad)


=====================================
SEGURIDAD
=====================================

- El token por defecto es "logieze_movil_2024"
  Cambiarlo en api.py (API_TOKEN) y en la configuracion de la app.

- La app usa verify=False para SSL porque el tunel Cloudflare
  usa su propio certificado. Esto es seguro ya que Cloudflare
  encripta el trafico de todas formas.

- Los datos viajan siempre encriptados por HTTPS via el tunel.


=====================================
SOLUCION DE PROBLEMAS
=====================================

"Sin conexion" o timeout:
  -> Verificar que el tunel esta activo en el servidor
  -> Verificar que la API esta corriendo (http://localhost:5050/ping)
  -> La URL del tunel puede haber cambiado al reiniciar cloudflared

"No autorizado" (401):
  -> El token en la app no coincide con API_TOKEN en api.py

"Producto no encontrado":
  -> Verificar que el codigo existe en la tabla maestra

La app carga lenta:
  -> Normal si el servidor esta lejos o la conexion es lenta
  -> El timeout es de 12 segundos

Pantalla en blanco al abrir:
  -> Kivy tarda ~2-3 segundos en inicializar en Android
  -> Es normal, esperar
