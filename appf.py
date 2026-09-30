import sys
import os
import pandas as pd
import streamlit as st
from datetime import datetime, date

# Configuración del path de ejecución
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from db_config import get_connection, inicializar_db
except ImportError:
    st.error("⚠️ No se encontró 'db_config.py' en la misma carpeta.")

# 1. Configurar la página de Streamlit
st.set_page_config(
    page_title="Sistema Nacional de Salud | Portal Hospitalario",
    page_icon="🏥",
    layout="wide"
)

# 2. Inyección de CSS estricto para sobreescribir estilos por defecto
st.markdown("""
<style>
    /* Estilos generales */
    .stApp {
        background-color: #4A6B3;
    }
    
    /* Entezado principal de Gobierno */
    .banner-gob {
        background: linear-gradient(90deg, #691C32 0%, #9B2242 50%, #10393B 100%);
        color: #ffffff;
        padding: 8px 20px;
        font-weight: bold;
        font-size: 0.85rem;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        margin-bottom: 15px;
    }
    
    .header-gob {
        background-color: #ffffff;
        border-left: 8px solid #9B2242;
        padding: 20px;
        border-radius: 6px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 25px;
    }
    
    .header-gob h1 {
        color: #13322B;
        margin: 0;
        font-size: 1.8rem;
    }
    
    .header-gob p {
        color: #555555;
        margin-top: 5px;
        font-size: 0.95rem;
    }
    
    /* Pie de página */
    .footer-gob {
        text-align: center;
        color: #777777;
        font-size: 0.8rem;
        margin-top: 50px;
        padding-top: 15px;
        border-top: 1px solid #cccccc;
    }
</style>
""", unsafe_allow_html=True)

# 3. Funciones BD
def fetch_data(query: str, params: tuple = ()) -> pd.DataFrame:
    conn = None
    try:
        conn = get_connection()
        return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        st.error(f"Error de consulta: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def execute_query(query: str, params: tuple = ()) -> bool:
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        st.error(f"Error en la operación: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@st.cache_resource
def init_db():
    try:
        inicializar_db()
    except Exception as e:
        pass

init_db()

# 4. Renderizado visual
st.markdown("""
<div class="banner-gob">
    <span>GOBIERNO / SECRETARÍA DE SALUD — SERVICIO PÚBLICO</span>
    <span>SISTEMA OPERATIVO Y CONECTADO ●</span>
</div>
<div class="header-gob">
    <h1>🏥 Sistema de Gestión Médica e Inventario Hospitalario</h1>
    <p>Plataforma oficial para la atención de pacientes, expediente clínico y trazabilidad de insumos médicos.</p>
</div>
""", unsafe_allow_html=True)

# Menú de navegación
with st.sidebar:
    st.image("https://img.icons8.com/color/96/hospital-3.png", width=70)
    st.markdown("### **Módulos del Sistema**")
    opcion = st.radio("Selecciona una opción:", ["📋 Pacientes", "💊 Inventario", "📊 Indicadores"])

if opcion == "📋 Pacientes":
    st.subheader("📋 Registro y Expedientes de Pacientes")
    t1, t2 = st.tabs(["🔍 Consultar Padrón", "➕ Registrar Paciente"])
    
    with t1:
        filtro = st.text_input("Filtrar por nombre o expediente:")
        df_p = fetch_data("SELECT expediente_id AS Expediente, nombre AS Nombre, edad AS Edad, contacto AS Contacto, alergias AS Alergias FROM pacientes ORDER BY nombre ASC")
        if not df_p.empty:
            if filtro:
                df_p = df_p[df_p['Nombre'].str.contains(filtro, case=False, na=False) | df_p['Expediente'].astype(str).str.contains(filtro, case=False, na=False)]
            st.dataframe(df_p, use_container_width=True, hide_index=True)
        else:
            st.info("No hay registros disponibles.")
            
    with t2:
        with st.form("f_paciente", clear_on_submit=True):
            exp = st.text_input("N° Expediente / Folio *")
            nom = st.text_input("Nombre Completo *")
            eda = st.number_input("Edad *", min_value=0, max_value=120, value=30)
            con = st.text_input("Contacto / Teléfono")
            ale = st.text_area("Alergias / Antecedentes", value="Ninguna")
            btn = st.form_submit_button("💾 Guardar Paciente", type="primary")
            if btn:
                if not exp or not nom:
                    st.error("Campos obligatorios incompletos.")
                else:
                    if execute_query("INSERT INTO pacientes (expediente_id, nombre, edad, contacto, alergias) VALUES (?, ?, ?, ?, ?)", (exp, nom, int(eda), con, ale)):
                        st.success("Paciente registrado con éxito.")
                        st.rerun()

elif opcion == "💊 Inventario":
    st.subheader("💊 Control de Insumos y Medicamentos")
    t1, t2 = st.tabs(["📦 Existencias", "➕ Ingesta de Lotes"])
    
    with t1:
        df_i = fetch_data("SELECT lote AS Lote, nombre AS Insumo, caducidad AS Caducidad, cantidad AS Cantidad, ubicacion AS Ubicacion, estado_sanitario AS Estado FROM inventario ORDER BY caducidad ASC")
        if not df_i.empty:
            st.dataframe(df_i, use_container_width=True, hide_index=True)
        else:
            st.info("Sin insumos en almacén.")
            
    with t2:
        with st.form("f_inv", clear_on_submit=True):
            lot = st.text_input("N° de Lote *")
            nom_i = st.text_input("Nombre del Insumo *")
            cad = st.date_input("Fecha Caducidad *", min_value=date.today())
            can = st.number_input("Cantidad *", min_value=0, value=100)
            ubi = st.text_input("Ubicación", value="Almacén Central")
            est = st.selectbox("Estado Sanitario", ["DISPONIBLE", "EN CUARENTENA", "CADUCADO"])
            btn_i = st.form_submit_button("📦 Guardar Entrada", type="primary")
            if btn_i:
                if not lot or not nom_i:
                    st.error("Lote e Insumo son requeridos.")
                else:
                    if execute_query("INSERT INTO inventario (lote, nombre, caducidad, cantidad, ubicacion, estado_sanitario) VALUES (?, ?, ?, ?, ?, ?)", (lot, nom_i, cad.strftime('%Y-%m-%d'), int(can), ubi, est)):
                        st.success("Lote registrado correctamente.")
                        st.rerun()

elif opcion == "📊 Indicadores":
    st.subheader("📊 Indicadores Sanitarios")
    c1, c2 = st.columns(2)
    tot_p = fetch_data("SELECT COUNT(*) as t FROM pacientes")
    tot_i = fetch_data("SELECT SUM(cantidad) as t FROM inventario")
    
    with c1:
        st.metric("Total Expedientes", value=tot_p['t'].iloc[0] if not tot_p.empty else 0)
    with c2:
        st.metric("Insumos en Stock", value=tot_i['t'].iloc[0] if not tot_i.empty and tot_i['t'].iloc[0] else 0)

st.markdown("""
<div class="footer-gov">
    <b>Sistema Sanitario de Salud Pública</b> | Módulo de Gestión Interna Hospitalaria
</div>
""", unsafe_allow_html=True)