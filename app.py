import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import norm
from scipy.optimize import brentq
from api_handler import IOLApiHandler

st.set_page_config(page_title="Company-Pro Options", layout="wide", page_icon="🏦")

# --- CUSTOM CSS PREMIUM RESPONSIVE ---
st.markdown("""
<style>
    .stApp { background-color: #0A192F; color: #E2E8F0; }
    h1, h2, h3, h4, h5, h6 { color: #00E5FF !important; font-weight: 600; letter-spacing: 0.5px; }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: #1E293B; border-radius: 12px; padding: 1.5rem; border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    }
    [data-testid="stMetricValue"] { color: #00E5FF; font-size: 2.2rem !important; font-weight: 700 !important; }
    [data-testid="stMetricLabel"] { color: #94A3B8; font-size: 1rem !important; }
    div[data-testid="stDataFrame"] { background-color: #1E293B; border-radius: 8px; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { background-color: #1E293B; border-radius: 6px 6px 0px 0px; color: #94A3B8; padding: 10px 24px; border: 1px solid #334155; border-bottom: none; }
    .stTabs [aria-selected="true"] { background-color: #00E5FF !important; color: #0A192F !important; font-weight: bold; }
    .stSelectbox label, .stNumberInput label, .stTextInput label { color: #94A3B8 !important; }
</style>
""", unsafe_allow_html=True)

# --- MATEMÁTICA OPCIONES (BLACK-SCHOLES) ---
def bs_price(S, K, T, r, sigma, type_="Call"):
    if T <= 0 or sigma <= 0:
        return max(S-K, 0) if type_ == "Call" else max(K-S, 0)
    d1 = (np.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if type_ == "Call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def calc_iv(S, K, T, r, market_price, type_="Call"):
    if market_price <= 0 or T <= 0:
        return 0.0
    intrinsic = max(S-K, 0) if type_ == "Call" else max(K-S, 0)
    if market_price < intrinsic:
        return 0.0 
    
    def objective(sigma):
        return bs_price(S, K, T, r, sigma, type_) - market_price
        
    try:
        return brentq(objective, 1e-4, 3.0) # Busca IV entre 0.01% y 300%
    except:
        return 0.0

# --- SISTEMA DE PROTECCIÓN DE LA APP (MEMBRESÍA) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("🔒 Ingresa la contraseña de la plataforma:", type="password", key="password")
        if st.session_state.get('password') == "radar2026":
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if not check_password():
    st.stop()

if 'api_handler' not in st.session_state:
    st.session_state.api_handler = None

# --- SIDEBAR: LOGIN BROKER & CONFIG ---
with st.sidebar:
    st.header("🔐 Mi Broker (IOL)")
    st.markdown("Conecta tu cuenta personal.")
    
    if not st.session_state.api_handler:
        u_iol = st.text_input("Usuario IOL")
        p_iol = st.text_input("Contraseña IOL", type="password")
        if st.button("🔌 Conectar a IOL"):
            if u_iol and p_iol:
                with st.spinner("Autenticando..."):
                    h = IOLApiHandler(u_iol, p_iol)
                    if h.login():
                        st.session_state.api_handler = h
                        st.rerun()
            else:
                st.warning("Completa usuario y contraseña.")
    else:
        st.success("✅ Conectado a IOL")
        if st.button("Desconectar"):
            st.session_state.api_handler = None
            st.session_state['iol_access_token'] = None
            st.rerun()

    st.markdown("---")
    st.header("⚙️ Configuración Global")
    usd_mep = st.number_input("Dólar MEP (ARS)", value=1422.0, step=10.0)
    comision_broker = st.number_input("Comisión Broker (%)", value=0.5, step=0.1)
    st.markdown("---")
    st.header("📊 Variables Cuantitativas")
    dias_vto_global = st.number_input("Días Promedio al Vencimiento", value=45, step=1, min_value=1)
    tasa_libre_riesgo = st.number_input("Tasa Libre Riesgo (TNA %)", value=35.0, step=1.0) / 100
    
# --- HEADER APP ---
st.title("🏦 Company-Pro | Plataforma de Gestión")
st.markdown("Plataforma SaaS Premium para Operatoria de Opciones y Análisis Cuantitativo.")

if not st.session_state.api_handler:
    st.info("👋 **Bienvenido/a.** Conecta tu cuenta de InvertirOnline en la barra lateral para comenzar.")
    st.stop()

api = st.session_state.api_handler

tab1, tab2, tab3 = st.tabs(["📊 Análisis Subyacente", "🧮 Panel de Opciones & Volatilidad", "🎯 Simulador de Estrategias"])

# Variables Globales de Estado
hv_actual = 0.0
precio_subyacente_actual = 0.0

# ----------------- TAB 1: SUBYACENTE (VELAS) -----------------
with tab1:
    col_t1, col_t2 = st.columns([1, 4])
    with col_t1:
        st.subheader("Configuración")
        ticker = st.selectbox("Activo Subyacente", ["GGAL", "YPFD", "PAMP", "BMA"], index=0)
        timeframe = st.selectbox("Temporalidad", ["1D"])
    
    with col_t2:
        df_historic = api.get_candlestick_data(ticker, timeframe, limit=120)
        
        if not df_historic.empty:
            # Calcular HV (Volatilidad Histórica Anualizada usando cierres diarios)
            log_returns = np.log(df_historic['Close'] / df_historic['Close'].shift(1))
            hv_actual = log_returns.std() * np.sqrt(252)
            st.session_state['hv_actual'] = hv_actual
            precio_subyacente_actual = df_historic.iloc[-1]['Close']
            st.session_state['precio_sub'] = precio_subyacente_actual
            
            df_historic['MA20'] = df_historic['Close'].rolling(window=20).mean()
            df_historic['MA50'] = df_historic['Close'].rolling(window=50).mean()
            
            from plotly.subplots import make_subplots
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, subplot_titles=(f'Precio {ticker}', 'Volumen'),
                                row_width=[0.2, 0.7])

            fig.add_trace(go.Candlestick(x=df_historic['Date'],
                            open=df_historic['Open'], high=df_historic['High'],
                            low=df_historic['Low'], close=df_historic['Close'],
                            name='Precio'), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df_historic['Date'], y=df_historic['MA20'], 
                                     line=dict(color='#00E5FF', width=1.5), name='MA 20'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_historic['Date'], y=df_historic['MA50'], 
                                     line=dict(color='#F59E0B', width=1.5), name='MA 50'), row=1, col=1)

            colors = ['#EF4444' if row['Open'] > row['Close'] else '#10B981' for index, row in df_historic.iterrows()]
            fig.add_trace(go.Bar(x=df_historic['Date'], y=df_historic['Volume'], marker_color=colors, name='Volumen'), row=2, col=1)

            fig.update_layout(template="plotly_dark", plot_bgcolor="#1E293B", paper_bgcolor="#0A192F",
                              margin=dict(l=20, r=20, t=30, b=20), xaxis_rangeslider_visible=False, height=550, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            st.metric("Volatilidad Histórica (HV 120d)", f"{hv_actual*100:.2f}%")
        else:
            st.warning("No se pudo cargar la data histórica. Verifica tu conexión a IOL.")

# ----------------- TAB 2: PANEL DE OPCIONES & VOLATILIDAD -----------------
with tab2:
    st.subheader(f"Panel Dinámico de Opciones: {ticker}")
    df_opciones = api.get_options_data(ticker)
    
    if not df_opciones.empty:
        # Calcular IV si tenemos el precio del subyacente
        if st.session_state.get('precio_sub') and hv_actual > 0:
            S = st.session_state['precio_sub']
            T = dias_vto_global / 365.0
            r = tasa_libre_riesgo
            
            def apply_iv(row):
                # Preferimos Ask si hay liquidez, si no el Último operado.
                price = row['Ask'] if pd.to_numeric(row['Ask'], errors='coerce') > 0 else pd.to_numeric(row['Último'], errors='coerce')
                return calc_iv(S, row['Base'], T, r, price, row['Tipo']) * 100
                
            df_opciones['IV (%)'] = df_opciones.apply(apply_iv, axis=1)
        else:
            df_opciones['IV (%)'] = 0.0

        col_c, col_p = st.columns(2)
        with col_c:
            st.markdown("<h3 style='color:#10B981 !important;'>📈 Calls</h3>", unsafe_allow_html=True)
            df_calls = df_opciones[df_opciones["Tipo"] == "Call"].copy()
            st.dataframe(df_calls[["Especie", "Base", "Bid", "Ask", "IV (%)"]].style.format({"Base":"{:.2f}", "Bid":"{:.2f}", "Ask":"{:.2f}", "IV (%)":"{:.2f}%"}), 
                         use_container_width=True, hide_index=True, height=250)
        with col_p:
            st.markdown("<h3 style='color:#EF4444 !important;'>📉 Puts</h3>", unsafe_allow_html=True)
            df_puts = df_opciones[df_opciones["Tipo"] == "Put"].copy()
            st.dataframe(df_puts[["Especie", "Base", "Bid", "Ask", "IV (%)"]].style.format({"Base":"{:.2f}", "Bid":"{:.2f}", "Ask":"{:.2f}", "IV (%)":"{:.2f}%"}), 
                         use_container_width=True, hide_index=True, height=250)

        # TABLA COMPARATIVA HV > IV
        st.divider()
        st.subheader("💡 Oportunidades: Volatilidad Histórica > Implícita")
        hv_pct = hv_actual * 100
        st.markdown(f"**Referencia:** Volatilidad Histórica (HV) del Subyacente = `{hv_pct:.2f}%`")
        st.caption("Muestra opciones que estadísticamente podrían estar 'baratas' (su IV es menor a lo que el subyacente se mueve habitualmente).")
        
        df_opps = df_opciones[(df_opciones['IV (%)'] > 0) & (df_opciones['IV (%)'] < hv_pct)].copy()
        
        # --- MOCK DATA PARA VISUALIZACIÓN UI ---
        if df_opps.empty:
            st.info("No se hallaron opciones reales con IV < HV actual. Mostrando datos **MOCK (Simulados)** para previsualizar la interfaz de oportunidades:")
            hv_mock = hv_pct if hv_pct > 0 else 45.0
            p_sub = st.session_state.get('precio_sub', 1500)
            mock_data = [
                {"Especie": f"{ticker}C{int(p_sub*1.05)}", "Tipo": "Call", "Base": p_sub*1.05, "Bid": 120.5, "Ask": 125.0, "IV (%)": hv_mock - 5.2},
                {"Especie": f"{ticker}V{int(p_sub*0.95)}", "Tipo": "Put",  "Base": p_sub*0.95, "Bid": 80.0,  "Ask": 85.0,  "IV (%)": hv_mock - 3.8},
                {"Especie": f"{ticker}C{int(p_sub*1.10)}", "Tipo": "Call", "Base": p_sub*1.10, "Bid": 45.0,  "Ask": 48.0,  "IV (%)": hv_mock - 8.1},
            ]
            df_opps = pd.DataFrame(mock_data)
        # ---------------------------------------
        
        if not df_opps.empty:
            df_opps = df_opps.sort_values(by='IV (%)', ascending=True)
            st.dataframe(df_opps[["Especie", "Tipo", "Base", "Bid", "Ask", "IV (%)"]].style.format({"Base":"{:.2f}", "Bid":"{:.2f}", "Ask":"{:.2f}", "IV (%)":"{:.2f}%"}), use_container_width=True)
        else:
            st.info("No se hallaron opciones con Volatilidad Implícita menor a la Histórica bajo los parámetros actuales.")
            
    else:
        st.warning(f"No hay series de opciones operables para {ticker}.")

# ----------------- TAB 3: SIMULADOR DE ESTRATEGIAS -----------------
with tab3:
    st.subheader("Simulador de Estrategias y TNA Real")
    
    if df_opciones.empty:
        st.warning("Se requiere que el panel de opciones esté cargado.")
    else:
        df_op_actual = df_opciones
        especies_list = df_op_actual["Especie"].tolist()
        
        col_strat1, col_strat2 = st.columns(2)
        with col_strat1:
            st.markdown("**🛡️ Pata 1 (Comprada)**")
            opt_compra = st.selectbox("Especie Compra", especies_list, index=0)
            q_compra = st.number_input("Cantidad Compra", value=100, step=10, key="q1")
            
        with col_strat2:
            st.markdown("**💸 Pata 2 (Vendida)**")
            opt_venta = st.selectbox("Especie Venta", especies_list, index=min(1, len(especies_list)-1))
            q_venta = st.number_input("Cantidad Venta", value=100, step=10, key="q2")
            
        st.caption(f"Días al vencimiento usados para el cálculo de TNA: {dias_vto_global} (configurable en la barra lateral).")
            
        try:
            data_c = df_op_actual[df_op_actual["Especie"] == opt_compra].iloc[0]
            data_v = df_op_actual[df_op_actual["Especie"] == opt_venta].iloc[0]
            
            precio_compra = pd.to_numeric(data_c["Ask"] if data_c["Ask"] > 0 else data_c["Último"]) 
            precio_venta = pd.to_numeric(data_v["Bid"] if data_v["Bid"] > 0 else data_v["Último"])
            base_compra = pd.to_numeric(data_c["Base"])
            base_venta = pd.to_numeric(data_v["Base"])
            tipo_compra = data_c["Tipo"]
            tipo_venta = data_v["Tipo"]
            
            flujo_op_compra = precio_compra * q_compra
            flujo_op_venta = precio_venta * q_venta
            
            inversion_bruta = flujo_op_compra - flujo_op_venta
            costo_comisiones_iniciales = (flujo_op_compra + flujo_op_venta) * (comision_broker / 100)
            inversion_neta_inicial = inversion_bruta + costo_comisiones_iniciales 
            
            min_base = min(base_compra, base_venta) * 0.7
            max_base = max(base_compra, base_venta) * 1.3
            precios_subyacente = np.linspace(min_base, max_base, 150)
            
            def calc_payoff(tipo, base, precio_sub):
                if tipo == "Call": return max(precio_sub - base, 0)
                else: return max(base - precio_sub, 0)

            beneficios = []
            for p in precios_subyacente:
                payoff_p1 = calc_payoff(tipo_compra, base_compra, p) * q_compra
                payoff_p2 = -calc_payoff(tipo_venta, base_venta, p) * q_venta
                flujo_vto = payoff_p1 + payoff_p2
                comision_vto = (abs(payoff_p1) + abs(payoff_p2)) * (comision_broker / 100)
                flujo_vto_neto = flujo_vto - comision_vto
                pnl = flujo_vto_neto - inversion_neta_inicial
                beneficios.append(pnl)
            
            max_ganancia = max(beneficios)
            max_perdida = min(beneficios)
            be_idx = np.argmin(np.abs(np.array(beneficios)))
            break_even = precios_subyacente[be_idx]

            if inversion_neta_inicial > 0 and max_ganancia > 0:
                rendimiento_efectivo = max_ganancia / inversion_neta_inicial
                tna_neta = rendimiento_efectivo * (365 / dias_vto_global) * 100
                tna_str = f"{tna_neta:.2f}%"
            elif inversion_neta_inicial <= 0:
                tna_str = "Estrategia Crédito"
            else:
                tna_str = "0.00%"

            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Inversión Neta", f"${inversion_neta_inicial:,.2f}", "Débito" if inversion_neta_inicial > 0 else "Crédito", delta_color="inverse")
            with m2: st.metric("Máx Ganancia", f"${max_ganancia:,.2f}")
            with m3: st.metric("Break-Even Aprox.", f"${break_even:,.2f}")
            with m4: st.metric("TNA Neta (Máx)", tna_str)

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=precios_subyacente, y=beneficios, mode='lines', line=dict(color='#00E5FF', width=3),
                                      fill='tozeroy', fillcolor='rgba(0, 229, 255, 0.15)', name="PnL Neto de Estrategia"))
            fig2.add_hline(y=0, line_dash="dash", line_color="#EF4444")
            
            if st.session_state.get('precio_sub'):
                precio_actual = st.session_state['precio_sub']
                fig2.add_vline(x=precio_actual, line_dash="dot", line_color="#94A3B8", annotation_text=f"Precio Actual: ${precio_actual:.2f}")

            fig2.update_layout(title="🎯 Perfil de Riesgo (Payoff)", xaxis_title="Precio del Subyacente al Vencimiento",
                               yaxis_title="Bº / Pda Neta ($ ARS)", template="plotly_dark", plot_bgcolor="#1E293B",
                               paper_bgcolor="#0A192F", height=450)
            st.plotly_chart(fig2, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error simulador: {e}")
