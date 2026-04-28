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
