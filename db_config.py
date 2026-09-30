import sqlite3

def get_connection():
    # Conecta o crea la base de datos local
    conn = sqlite3.connect('sistema_medico.db')
    # Permite acceder a los campos por nombre de columna
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    """Crea las tablas necesarias si no existen."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            expediente_id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            edad INTEGER NOT NULL,
            contacto TEXT,
            alergias TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario (
            lote TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            caducidad TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            ubicacion TEXT,
            estado_sanitario TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Crear las tablas al ejecutar este archivo por primera vez
if __name__ == '__main__':
    inicializar_db()
    print("Base de datos inicializada correctamente.")