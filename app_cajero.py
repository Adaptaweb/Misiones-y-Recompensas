# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import requests
import threading
import time
import os
import json
from datetime import datetime
import sqlite3

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# --- CONFIGURACION ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
IP_HA = "192.168.3.99" 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "datos_cajero.json")
DB_FILE = os.path.join(BASE_DIR, "datos_cajero.db")

if not TOKEN or not CHAT_ID:
    print("⚠️ ADVERTENCIA: No se encontró TELEGRAM_TOKEN o CHAT_ID en el archivo .env")

# --- VARIABLES DE CONTROL ---
estado_mision = "esperando"
tiempo_hoy = 0
tareas_aprobadas = []
tareas_activas = []
fecha_actual = str(datetime.now().date())
state_lock = threading.Lock() 

# --- PERSISTENCIA (SQLite) ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tareas_activas
                 (nombre TEXT PRIMARY KEY, icono TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS estado_actual
                 (id INTEGER PRIMARY KEY, fecha TEXT, tiempo_hoy INTEGER, tareas_aprobadas TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historial_diario
                 (fecha TEXT PRIMARY KEY, tiempo_ganado INTEGER, tareas_completadas TEXT)''')
    
    # Migrar desde JSON si existe y la DB está vacía
    c.execute('SELECT COUNT(*) FROM estado_actual')
    if c.fetchone()[0] == 0:
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, 'r') as f:
                    data = json.load(f)
                    fecha = data.get("fecha", str(datetime.now().date()))
                    tiempo = data.get("tiempo", 0)
                    aprobadas = json.dumps(data.get("aprobadas", []))
                    c.execute("INSERT INTO estado_actual (id, fecha, tiempo_hoy, tareas_aprobadas) VALUES (1, ?, ?, ?)", 
                              (1, fecha, tiempo, aprobadas))
                    
                    activas = data.get("activas", [])
                    for t in activas:
                        c.execute("INSERT OR IGNORE INTO tareas_activas (nombre, icono) VALUES (?, ?)", (t['nombre'], t.get('icono', '📌')))
            except Exception as e:
                print(f"Error migrando JSON: {e}")
                # Fallback si falla migración
                c.execute("INSERT INTO estado_actual (id, fecha, tiempo_hoy, tareas_aprobadas) VALUES (1, ?, 0, '[]')", (str(datetime.now().date()),))
        else:
            # Estado inicial por defecto
            c.execute("INSERT INTO estado_actual (id, fecha, tiempo_hoy, tareas_aprobadas) VALUES (1, ?, 0, '[]')", (str(datetime.now().date()),))
            # Insertar tareas por defecto
            tareas_defecto = [
                {"nombre": "Hacer la Cama", "icono": "🛏️"},
                {"nombre": "Lavarse los dientes", "icono": "🪥"},
                {"nombre": "Ordenar la Pieza", "icono": "📦"},
                {"nombre": "Recoger la Ropa sucia", "icono": "👕"},
                {"nombre": "Ayuda a regar las plantas", "icono": "🌻"},
                {"nombre": "Darle comida y agua a los perros", "icono": "🦴"},
                {"nombre": "Bañarse", "icono": "🚿"}
            ]
            for t in tareas_defecto:
                c.execute("INSERT OR IGNORE INTO tareas_activas (nombre, icono) VALUES (?, ?)", (t['nombre'], t['icono']))
    conn.commit()
    conn.close()

init_db()

def cargar_datos():
    global tiempo_hoy, tareas_aprobadas, fecha_actual, tareas_activas
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT fecha, tiempo_hoy, tareas_aprobadas FROM estado_actual WHERE id = 1")
        row = c.fetchone()
        if row:
            fecha_actual = row[0]
            tiempo_hoy = row[1]
            tareas_aprobadas = json.loads(row[2])
            
            # Si el dia en la DB es distinto al de hoy, forzamos un reset (prevención)
            if fecha_actual != str(datetime.now().date()):
                # No hacemos el reset aquí directamente, dejamos que revisar_reinicio_diario se encargue
                pass
                
        c.execute("SELECT nombre, icono FROM tareas_activas")
        tareas_activas = [{"nombre": r[0], "icono": r[1]} for r in c.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error al cargar DB: {e}")

def guardar_datos():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO estado_actual (id, fecha, tiempo_hoy, tareas_aprobadas) VALUES (1, ?, ?, ?)",
                  (fecha_actual, tiempo_hoy, json.dumps(tareas_aprobadas)))
        
        c.execute("DELETE FROM tareas_activas")
        for t in tareas_activas:
            c.execute("INSERT INTO tareas_activas (nombre, icono) VALUES (?, ?)", (t['nombre'], t['icono']))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al guardar DB: {e}")

cargar_datos()

def revisar_reinicio_diario():
    global tareas_aprobadas, tiempo_hoy, fecha_actual
    hoy = str(datetime.now().date())
    with state_lock:
        if hoy != fecha_actual:
            try:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                # Guardar el historial de ayer
                c.execute("INSERT OR REPLACE INTO historial_diario (fecha, tiempo_ganado, tareas_completadas) VALUES (?, ?, ?)",
                          (fecha_actual, tiempo_hoy, json.dumps(tareas_aprobadas)))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error al guardar historial: {e}")

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

@app.route('/historial')
def historial():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT fecha, tiempo_ganado, tareas_completadas FROM historial_diario ORDER BY fecha DESC")
        registros = c.fetchall()
        conn.close()
        
        historial_data = []
        for r in registros:
            historial_data.append({
                "fecha": r[0],
                "tiempo_ganado": r[1],
                "tareas_completadas": json.loads(r[2]),
                "tiempo_formato": formato_tiempo(r[1])
            })
    except Exception as e:
        print(f"Error al leer historial: {e}")
        historial_data = []
        
    return render_template('historial.html', historial=historial_data)

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