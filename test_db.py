import sqlite3
import json

DB_FILE = "datos_cajero.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("SELECT * FROM estado_actual")
print("estado_actual:", c.fetchall())

c.execute("SELECT * FROM historial_diario")
print("historial_diario:", c.fetchall())

c.execute("SELECT * FROM tareas_activas")
print("tareas_activas:", c.fetchall())
conn.close()
