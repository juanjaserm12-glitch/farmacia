import sys
import os

# Agrega la carpeta donde está este archivo al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify
from db_config import get_connection, inicializar_db
from datetime import datetime, date

app = Flask(__name__)
# ==========================================
# FUNCIONES AUXILIARES (Mantenibilidad)
# ==========================================

def filas_a_diccionarios(cursor):
    """Convierte los resultados del cursor en una lista de diccionarios."""
    if not cursor.description:
        return []
    columnas = [col[0] for col in cursor.description]
    
    resultados = []
    for fila in cursor.fetchall():
        item = dict(zip(columnas, fila))
        # Formatear fechas para asegurar serialización JSON correcta
        for clave, valor in item.items():
            if isinstance(valor, (date, datetime)):
                item[clave] = valor.strftime('%Y-%m-%d')
        resultados.append(item)
    return resultados


# ==========================================
# RUTAS DE LA APLICACIÓN WEB
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')


# ==========================================
# ENDPOINTS DE PACIENTES
# ==========================================

@app.route('/api/pacientes', methods=['GET'])
def obtener_pacientes():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Ordenado por nombre para consistencia visual
        cursor.execute("SELECT expediente_id, nombre, edad, contacto, alergias FROM pacientes ORDER BY nombre ASC")
        pacientes = filas_a_diccionarios(cursor)
        return jsonify(pacientes), 200
    except Exception as e:
        print("Error en GET /api/pacientes:", e)
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/api/pacientes', methods=['POST'])
def agregar_paciente():
    datos = request.get_json(silent=True)
    if not datos:
        return jsonify({"error": "Formato JSON no válido o vacío"}), 400

    # 1. Validación de campos obligatorios
    expediente = datos.get("expediente")
    nombre = datos.get("nombre")
    edad_raw = datos.get("edad")

    if not expediente or not str(expediente).strip():
        return jsonify({"error": "El expediente es obligatorio"}), 400
    if not nombre or not str(nombre).strip():
        return jsonify({"error": "El nombre es obligatorio"}), 400
    if edad_raw is None or edad_raw == "":
        return jsonify({"error": "La edad es obligatoria"}), 400

    # 2. Validación de tipo y rangos de datos
    try:
        edad = int(edad_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "La edad debe ser un número entero válido"}), 400

    if edad < 0 or edad > 120:
        return jsonify({"error": "La edad debe estar entre 0 y 120 años"}), 400

    contacto = str(datos.get('contacto', '')).strip()
    alergias = str(datos.get('alergias', 'Ninguna')).strip() or 'Ninguna'

    # 3. Inserción con transacción segura
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO pacientes (expediente_id, nombre, edad, contacto, alergias)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (str(expediente).strip(), str(nombre).strip(), edad, contacto, alergias))
        conn.commit()
        return jsonify({"mensaje": "Paciente registrado exitosamente"}), 201
    except Exception as e:
        if conn:
            conn.rollback()
        print("Error en POST /api/pacientes:", e)
        return jsonify({"error": "No se pudo registrar el paciente. Verifique que el expediente no esté duplicado."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==========================================
# ENDPOINTS DE INVENTARIO
# ==========================================

@app.route('/api/inventario', methods=['GET'])
def obtener_inventario():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Ordenado por fecha de caducidad
        cursor.execute("SELECT lote, nombre, caducidad, cantidad, ubicacion, estado_sanitario FROM inventario ORDER BY caducidad ASC")
        inventario = filas_a_diccionarios(cursor)
        return jsonify(inventario), 200
    except Exception as e:
        print("Error en GET /api/inventario:", e)
        return jsonify({"error": "Error interno del servidor"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/api/inventario', methods=['POST'])
def agregar_inventario():
    datos = request.get_json(silent=True)
    if not datos:
        return jsonify({"error": "Formato JSON no válido o vacío"}), 400

    # 1. Validación de campos obligatorios
    lote = datos.get("lote")
    nombre = datos.get("nombre")
    caducidad_raw = datos.get("caducidad")
    cantidad_raw = datos.get("cantidad")

    if not lote or not str(lote).strip():
        return jsonify({"error": "El número de lote es obligatorio"}), 400
    if not nombre or not str(nombre).strip():
        return jsonify({"error": "El nombre del producto es obligatorio"}), 400
    if not caducidad_raw or not str(caducidad_raw).strip():
        return jsonify({"error": "La fecha de caducidad es obligatoria"}), 400
    if cantidad_raw is None or cantidad_raw == "":
        return jsonify({"error": "La cantidad es obligatoria"}), 400

    # 2. Validación de tipos y valores
    try:
        cantidad = int(cantidad_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "La cantidad debe ser un número entero válido"}), 400

    if cantidad < 0:
        return jsonify({"error": "La cantidad no puede ser negativa"}), 400

    try:
        datetime.strptime(caducidad_raw, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "La fecha de caducidad debe tener formato AAAA-MM-DD"}), 400

    ubicacion = str(datos.get('ubicacion', 'General')).strip() or 'General'
    estado = str(datos.get('estado_sanitario', 'DISPONIBLE')).strip() or 'DISPONIBLE'

    # 3. Inserción con transacción segura
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO inventario (lote, nombre, caducidad, cantidad, ubicacion, estado_sanitario)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (str(lote).strip(), str(nombre).strip(), caducidad_raw, cantidad, ubicacion, estado))
        conn.commit()
        return jsonify({"mensaje": "Registro de inventario guardado correctamente"}), 201
    except Exception as e:
        if conn:
            conn.rollback()
        print("Error en POST /api/inventario:", e)
        return jsonify({"error": "No se pudo registrar el insumo. Verifique que el número de lote no esté duplicado."}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==========================================
# CONFIGURACIÓN DE INICIO
# ==========================================

if __name__ == '__main__':
    # Verifica y crea las tablas en la base de datos si no existen
    try:
        inicializar_db()
        print("Base de datos verificada/inicializada.")
    except Exception as e:
        print("Error al inicializar la base de datos:", e)

    # Cambiar debug=False al publicar en producción
    app.run(debug=True, host='127.0.0.1', port=5000)