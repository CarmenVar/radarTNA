import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Radar Inversiones 2026", layout="wide", page_icon="📈")

st.title("📈 Radar Inversiones Corto Plazo Argentina 2026")
st.markdown("Aplicación web automatizada basada en Python y Pandas.")

# --- BARRA LATERAL: VARIABLES MACRO ---
st.sidebar.header("🛠️ Tasas de Cambio e Inflación")
usd_mep = st.sidebar.number_input("Dólar MEP (ARS)", value=1422.0, step=10.0)
usd_oficial = st.sidebar.number_input("Dólar Oficial (ARS)", value=1050.0, step=10.0)
inf_mensual = st.sidebar.number_input("Inflación Mensual Est. (%)", value=2.5, step=0.1)
inf_anual = st.sidebar.number_input("Inflación Anual Ref. (%)", value=33.1, step=0.5)

# --- BASE DE DATOS (MOCK AMPLIADA) ---
# En una app real, esto podría venir de una API, scraping o un Excel subido.
if 'activos' not in st.session_state:
    st.session_state.activos = pd.DataFrame([
        # TAMAR / LECAP / BONCAP / LETRAS / BONCER
        {"Activo": "Tasa TAMAR", "Ticker": "TMF27", "Grupo": "TAMAR", "TNA %": 33.5, "TIR %": 39.2, "Plazo (días)": 338, "Dónde": "ALyC"},
        {"Activo": "LECAP S30O6", "Ticker": "S30O6", "Grupo": "LECAP", "TNA %": 28.0, "TIR %": 32.0, "Plazo (días)": 220, "Dónde": "ALyC"},
        {"Activo": "LECAP S31M6", "Ticker": "S31M6", "Grupo": "LECAP", "TNA %": 27.5, "TIR %": 31.2, "Plazo (días)": 60, "Dónde": "ALyC"},
        {"Activo": "Dual TTD26", "Ticker": "TTD26", "Grupo": "BONCAP", "TNA %": 33.6, "TIR %": 39.3, "Plazo (días)": 265, "Dónde": "ALyC"},
        {"Activo": "BONCER TX26", "Ticker": "TX26", "Grupo": "BONCER", "TNA %": 35.0, "TIR %": 36.5, "Plazo (días)": 180, "Dónde": "ALyC"},
        {"Activo": "BONCER TZX26", "Ticker": "TZX26", "Grupo": "BONCER", "TNA %": 36.2, "TIR %": 38.0, "Plazo (días)": 250, "Dónde": "ALyC"},
        {"Activo": "Letras del Tesoro", "Ticker": "S29N5", "Grupo": "Letras", "TNA %": 29.5, "TIR %": 33.5, "Plazo (días)": 90, "Dónde": "ALyC"},
        
        # OBLIGACIONES NEGOCIABLES (ON Pesos)
        {"Activo": "ON YPF (Pesos)", "Ticker": "YPCUO", "Grupo": "ON Pesos", "TNA %": 38.0, "TIR %": 42.0, "Plazo (días)": 400, "Dónde": "Broker"},
        {"Activo": "ON Pampa Energía", "Ticker": "MTCGO", "Grupo": "ON Pesos", "TNA %": 37.5, "TIR %": 40.5, "Plazo (días)": 380, "Dónde": "Broker"},
        {"Activo": "ON Telecom", "Ticker": "TLC5O", "Grupo": "ON Pesos", "TNA %": 36.5, "TIR %": 39.5, "Plazo (días)": 290, "Dónde": "Broker"},
        {"Activo": "ON IRSA", "Ticker": "IRCFO", "Grupo": "ON Pesos", "TNA %": 35.5, "TIR %": 38.2, "Plazo (días)": 320, "Dónde": "Broker"},
        
        # FONDOS COMUNES DE INVERSIÓN (FCI)
        {"Activo": "FCI Money Market", "Ticker": "Ualá/Balanz", "Grupo": "FCI Money Market", "TNA %": 29.0, "TIR %": 33.5, "Plazo (días)": 1, "Dónde": "Fintech"},
        {"Activo": "FCI MercadoPago", "Ticker": "MercadoFondo", "Grupo": "FCI Money Market", "TNA %": 28.5, "TIR %": 32.8, "Plazo (días)": 1, "Dónde": "Fintech"},
        {"Activo": "FCI Renta Fija T+1", "Ticker": "FBA Renta", "Grupo": "FCI T+1", "TNA %": 32.5, "TIR %": 35.8, "Plazo (días)": 1, "Dónde": "Banco/Broker"},
        {"Activo": "FCI Cobertura CER", "Ticker": "Consultatio CER", "Grupo": "FCI Renta Mixta", "TNA %": 34.0, "TIR %": 36.5, "Plazo (días)": 2, "Dónde": "Broker"},
        {"Activo": "FCI IOL Premium", "Ticker": "Premier Renta", "Grupo": "FCI T+1", "TNA %": 33.0, "TIR %": 36.2, "Plazo (días)": 1, "Dónde": "IOL"},
        
        # PLAZOS FIJOS
        {"Activo": "PF Tradicional Top", "Ticker": "Banco Bica/Macro", "Grupo": "PF Tradicional", "TNA %": 31.0, "TIR %": 36.0, "Plazo (días)": 30, "Dónde": "Bancos"},
        {"Activo": "PF Tradicional Medio", "Ticker": "Nación/Provincia", "Grupo": "PF Tradicional", "TNA %": 28.0, "TIR %": 32.0, "Plazo (días)": 30, "Dónde": "Bancos"},
        {"Activo": "PF UVA BNA", "Ticker": "-", "Grupo": "PF UVA", "TNA %": 34.1, "TIR %": 34.1, "Plazo (días)": 90, "Dónde": "Banco Nación"},
        {"Activo": "PF UVA Provincia", "Ticker": "-", "Grupo": "PF UVA", "TNA %": 34.1, "TIR %": 34.1, "Plazo (días)": 180, "Dónde": "Banco Provincia"},
        
        # CAUCIONES
        {"Activo": "Caución a 30 días", "Ticker": "Caución ARS", "Grupo": "Caución", "TNA %": 27.5, "TIR %": 31.0, "Plazo (días)": 30, "Dónde": "Broker"},
        {"Activo": "Caución a 7 días", "Ticker": "Caución ARS", "Grupo": "Caución", "TNA %": 26.5, "TIR %": 30.0, "Plazo (días)": 7, "Dónde": "Broker"}
    ])

df = st.session_state.activos.copy()

# --- LÓGICA Y CÁLCULOS ---
def get_semaforo(tir):
    if tir >= 35.0: return "🟢"
    if tir >= inf_anual: return "🟡"
    return "🔴"

def supera_inflacion(tir, grupo):
    # Los fondos atados al CER o UVA garantizan inflación por naturaleza.
    if "UVA" in grupo or "CER" in grupo: return "✅ Garantizado"
    if tir >= inf_anual: return "✅ Sí"
    return "❌ No"

df["Semáforo"] = df["TIR %"].apply(get_semaforo)
df["¿Supera Inflación?"] = df.apply(lambda x: supera_inflacion(x["TIR %"], x["Grupo"]), axis=1)
# Formato moneda explícito para mostrar directo en tabla
df["Ganancia 10k USD en ARS"] = (10000 * usd_mep * (df["TIR %"]/100) * (df["Plazo (días)"]/365)).map(lambda x: f"${x:,.2f}")

# --- DASHBOARD PRINCIPAL ---
st.subheader("🎯 Filtros Dinámicos")
col1, col2, col3 = st.columns(3)
min_tir = col1.number_input("Mínimo TIR Deseada (%)", value=20.0, step=1.0)
max_dias = col2.number_input("Plazo Máximo (días)", value=365, step=30)
excluir_rojos = col3.checkbox("Excluir Rendimientos 🔴", value=False)

# Aplicar filtros
filtro = (df["TIR %"] >= min_tir) & (df["Plazo (días)"] <= max_dias)
if excluir_rojos:
    filtro = filtro & (df["Semáforo"] != "🔴")

# Filtrar, Ordenar y Limitar al TOP 15
df_filtrado = df[filtro].sort_values("TIR %", ascending=False).head(15).reset_index(drop=True)

st.subheader("🔥 TOP 15 ACTIVOS FILTRADOS")
# Aumentamos la altura visual (height=550) para que entren más filas sin scroll
st.dataframe(df_filtrado, use_container_width=True, height=550)

# Gráfico modificado a color verde esperanza
st.subheader("📊 Top 15 Rendimientos (TIR %)")
if not df_filtrado.empty:
    st.bar_chart(df_filtrado.set_index("Activo")["TIR %"], color="#00C853")
else:
    st.info("Ningún activo cumple los filtros actuales.")

# --- CALCULADORA ---
st.divider()
st.subheader("🧮 Calculadora de Inversión Aislada")
ccol1, ccol2, ccol3, ccol4 = st.columns(4)
monto = ccol1.number_input("Monto a Invertir", value=5000000.0, step=100000.0)
moneda = ccol2.selectbox("Moneda", ["ARS", "USD"])
plazo = ccol3.number_input("Plazo (Días)", value=60, step=15)
tasa = ccol4.number_input("Tasa Esperada (%)", value=35.0, step=1.0)

ganancia = (monto * usd_mep if moneda == "USD" else monto) * (tasa/100) * (plazo/365)
st.success(f"**Ganancia Estimada:** $ {ganancia:,.2f} ARS")

st.markdown("---")
st.caption("Desarrollado en Python con Streamlit. Actualizar manualmente las variables en la barra lateral.")
