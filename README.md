# 📦 Bank Craft - Gestión de Misiones Gamificada

**Bank Craft** es una solución tecnológica diseñada para transformar las tareas del hogar en una experiencia interactiva y gratificante. Inspirada en la estética de *Minecraft*, esta aplicación permite a los padres gestionar misiones diarias y recompensar a sus hijos con "XP" (tiempo de pantalla) de forma automatizada y divertida.

---

## 🚀 Características Principales

* **Interfaz Temática:** Diseño visual basado en píxel art y sonidos clásicos de videojuegos para máxima inmersión.
* **Validación vía Telegram:** Integración con un bot de Telegram que permite a los padres aprobar o rechazar tareas en tiempo real mediante botones interactivos.
* **Automatización Smart Home:** Envío de Webhooks a **Home Assistant** al completar misiones, permitiendo disparar eventos físicos en casa (luces, enchufes, etc.).
* **Persistencia de Datos:** Sistema de guardado en JSON para mantener el progreso diario y contador de tiempo ganado.
* **Despliegue Robusto:** Optimizado para correr en **Raspberry Pi 5** utilizando **Docker** y **CasaOS**.

---

## 🛠️ Stack Tecnológico

* **Backend:** Python 3.11 con Flask.
* **Frontend:** HTML5, CSS3 (Animaciones personalizadas) y JavaScript (Long Polling para estados).
* **Integraciones:** Telegram Bot API y Home Assistant Webhooks.
* **Infraestructura:** Docker & Docker Compose.
* **Hardware Base:** Raspberry Pi 5.

---

## 📋 Estructura del Proyecto

```text
├── app_cajero.py       # Lógica principal del servidor y motor de Telegram
├── Dockerfile          # Configuración del contenedor Docker
├── requirements.txt    # Dependencias del sistema
├── .env                # Variables sensibles (Token de Telegram, Chat ID) - [EXCLUIDO]
├── datos_cajero.json   # Base de datos local de misiones
└── static/             # Recursos visuales y sonoros (Minecraft style)
    ├── menuclick.mp3
    ├── victory.mp3
    └── fondo_titulo.webp


⚙️ Instalación y Configuración
1. Variables de Entorno
Crea un archivo .env con las siguientes credenciales:

Fragmento de código
TELEGRAM_TOKEN="tu_token_de_botfather"
TELEGRAM_CHAT_ID="tu_id_de_chat"
2. Despliegue con Docker
Construye y levanta el contenedor:

Bash
docker build -t bank-craft .
docker run -d -p 5000:5000 --name mati-tareas bank-craft
💡 Idea Creativa: Evolución a Mobile App
Este proyecto nace como un MVP (Producto Mínimo Viable) con un gran potencial de escalabilidad en el sector EdTech:

Multi-Skin: Capacidad de cambiar la temática (Roblox, Lego, Super Mario).

Economía Digital: Una billetera virtual de tiempo para que los niños "paguen" sus horas de juego.

Prueba de Trabajo: Integración de la cámara para que el niño suba una foto de la tarea terminada antes de enviar la notificación al padre.

👤 Autor
Alejandro Tamayo - Desarrollador y Analista de Soporte - [Tu GitHub Profile]

Proyecto desarrollado con fines educativos y de organización familiar.


---

### ¿Cómo agregarlo desde Windows?
1. En tu carpeta, haz clic derecho -> **Nuevo** -> **Documento de texto**.
2. Nómbralo `README.md` (asegúrate de borrar la extensión `.txt`).
3. Abre el archivo con el Bloc de notas o VS Code, pega el código de arriba y guarda.
4. En la terminal de Git, haz:
   ```powershell
   git add README.md
   git commit -m "Añadido README profesional"
   git push
