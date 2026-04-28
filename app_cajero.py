# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import requests
import threading
import time
import os
import json
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# --- CONFIGURACION ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
IP_HA = "192.168.1.99" 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "datos_cajero.json")

if not TOKEN or not CHAT_ID:
    print("⚠️ ADVERTENCIA: No se encontró TELEGRAM_TOKEN o CHAT_ID en el archivo .env")

# --- VARIABLES DE CONTROL ---
estado_mision = "esperando"
tiempo_hoy = 0
tareas_aprobadas = []

# Lista dinámica de tareas con sus iconos
tareas_activas = [
    {"nombre": "Hacer la Cama", "icono": "🛏️"},
    {"nombre": "Lavarse los dientes", "icono": "🪥"},
    {"nombre": "Ordenar la Pieza", "icono": "📦"},
    {"nombre": "Recoger la Ropa sucia", "icono": "👕"},
    {"nombre": "Ayuda a regar las plantas", "icono": "🌻"},
    {"nombre": "Darle comida y agua a los perros", "icono": "🦴"},
    {"nombre": "Bañarse", "icono": "🚿"}
]

fecha_actual = str(datetime.now().date())
state_lock = threading.Lock() 

# --- PERSISTENCIA (JSON) ---
def guardar_datos():
    try:
        data = {
            "fecha": str(datetime.now().date()), 
            "tiempo": tiempo_hoy, 
            "aprobadas": tareas_aprobadas,
            "activas": tareas_activas
        }
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error al guardar JSON: {e}")

def cargar_datos():
    global tiempo_hoy, tareas_aprobadas, fecha_actual, tareas_activas
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r') as f:
                data = json.load(f)
                if data.get("fecha") == str(datetime.now().date()):
                    tiempo_hoy = data.get("tiempo", 0)
                    tareas_aprobadas = data.get("aprobadas", [])
                    fecha_actual = data.get("fecha")
                
                if "activas" in data:
                    tareas_activas = data.get("activas")
        except Exception as e:
            print(f"Error al cargar JSON: {e}")

cargar_datos()

def revisar_reinicio_diario():
    global tareas_aprobadas, tiempo_hoy, fecha_actual
    hoy = str(datetime.now().date())
    with state_lock:
        if hoy != fecha_actual:
            tareas_aprobadas, tiempo_hoy, fecha_actual = [], 0, hoy
            guardar_datos()
            print("🔄 Nuevo día detectado: Misiones reiniciadas.")

def formato_tiempo(minutos):
    if minutos < 60: return f"{minutos} Minutos"
    horas, restante = minutos // 60, minutos % 60
    return f"{horas}h" if restante == 0 else f"{horas} Horas y {restante} Minutos"

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)

@app.route('/api/slideshow_images')
def slideshow_images():
    slideshow_dir = os.path.join(BASE_DIR, 'static', 'slideshow')
    if not os.path.exists(slideshow_dir):
        os.makedirs(slideshow_dir, exist_ok=True)
    
    valid_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    images = []
    if os.path.exists(slideshow_dir):
        for f in os.listdir(slideshow_dir):
            if f.lower().endswith(valid_exts):
                images.append(f'/static/slideshow/{f}')
    
    return jsonify({"images": images})


# ==========================================
# RUTAS DE LA APP
# ==========================================

@app.route('/')
def home():
    global estado_mision
    with state_lock:
        estado_mision = "esperando"
    return render_template('main.html', tareas=tareas_activas)

@app.route('/admin')
def admin_panel():
    return render_template('admin.html', tareas=tareas_activas)

@app.route('/modificar_tareas', methods=['POST'])
def modificar_tareas():
    global tareas_activas, tareas_aprobadas
    data = request.json
    accion = data.get('accion')
    nombre_tarea = data.get('nombre')
    
    with state_lock:
        if accion == 'agregar' and nombre_tarea:
            # Evita duplicados
            if not any(t['nombre'] == nombre_tarea for t in tareas_activas):
                icono_tarea = data.get('icono', '📌')
                tareas_activas.append({"nombre": nombre_tarea, "icono": icono_tarea})
                
        elif accion == 'quitar' and nombre_tarea:
            tareas_activas = [t for t in tareas_activas if t['nombre'] != nombre_tarea]
            if nombre_tarea in tareas_aprobadas:
                tareas_aprobadas.remove(nombre_tarea)
                
        guardar_datos()
    return jsonify(ok=True)

@app.route('/mandar')
def mandar():
    global estado_mision
    tarea = request.args.get('tarea')
    
    try:
        res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={
            "chat_id": CHAT_ID, "text": f"MISION RECIBIDA: {tarea}",
            "reply_markup": {"inline_keyboard": [[{"text": "APROBAR ✅", "callback_data": f"ok|{tarea}"}, {"text": "RECHAZAR ❌", "callback_data": "no"}]]}
        }, timeout=5)
        
        if res.status_code == 200:
            with state_lock:
                estado_mision = "enviada"
            return jsonify(ok=True)
        else:
            return jsonify(ok=False), 500
    except Exception as e:
        return jsonify(ok=False), 500

@app.route('/estado')
def estado():
    revisar_reinicio_diario()
    with state_lock:
        return jsonify({
            "valor": estado_mision, 
            "tiempo": tiempo_hoy, 
            "tiempo_formato": formato_tiempo(tiempo_hoy), 
            "aprobadas": tareas_aprobadas,
            "total_tareas": len(tareas_activas)
        })

@app.route('/estado_reset')
def estado_reset():
    global estado_mision
    with state_lock:
        estado_mision = "esperando"
    return jsonify(ok=True)

# ==========================================
# MOTOR TELEGRAM (LONG POLLING)
# ==========================================

def motor_telegram():
    global estado_mision, tiempo_hoy, tareas_aprobadas, tareas_activas
    offset = 0
    print("🚀 Motor de Telegram Iniciado correctamente...")
    while True:
        revisar_reinicio_diario()
        
        try:
            r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=5", timeout=10)
            if r.status_code != 200:
                time.sleep(2)
                continue
                
            datos = r.json()
            for u in datos.get("result", []):
                offset = u["update_id"] + 1
                if "callback_query" in u:
                    callback = u["callback_query"]
                    callback_id = callback["id"]
                    data = callback["data"]
                    msg = callback["message"]
                    chat_id = msg["chat"]["id"]
                    message_id = msg["message_id"]
                    texto_final = ""
                    
                    with state_lock:
                        if data.startswith("ok|"):
                            tarea_nombre = data.split("|")[1]
                            if tarea_nombre not in tareas_aprobadas:
                                # 1. Agregamos la tarea a la lista (ESTO FALTABA)
                                tareas_aprobadas.append(tarea_nombre)
                                
                                # 2. Cálculo de tiempo dinámico equitativo
                                if tareas_activas:
                                    minutos_ganados = 120 // len(tareas_activas)
                                    tiempo_hoy += minutos_ganados
                                    
                                # 3. Guardamos en el JSON
                                guardar_datos()
                                
                                try:
                                    # --- MODIFICACIÓN PARA WEBHOOK DINÁMICO ---
                                    datos_webhook = {
                                        "tarea": tarea_nombre,
                                        "minutos": minutos_ganados
                                    }
                                    requests.post(f"http://{IP_HA}:8123/api/webhook/mision_aprobada_matias", json=datos_webhook, timeout=2)
                                    # -------------------------------------------
                                    
                                    if len(tareas_aprobadas) == len(tareas_activas) and len(tareas_activas) > 0:
                                        requests.post(f"http://{IP_HA}:8123/api/webhook/meta_alcanzada_matias", timeout=2)
                                except Exception as e:
                                    print(f"Error al contactar Home Assistant: {e}")
                                    
                            estado_mision = "aprobada"
                            texto_final = f"✅ APROBADA: {tarea_nombre}"
                            
                        elif data == "no":
                            estado_mision = "rechazada"
                            texto_final = "❌ RECHAZADA"

                    try:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id}, timeout=2)
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/editMessageText", json={"chat_id": chat_id, "message_id": message_id, "text": texto_final}, timeout=2)
                    except Exception as e:
                        pass
                        
        except requests.exceptions.Timeout:
            pass 
        except Exception as e:
            time.sleep(2)
        time.sleep(0.5)

if __name__ == '__main__':
    threading.Thread(target=motor_telegram, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)