import requests
import time
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

class IOLApiHandler:
    def __init__(self, username, password):
        # En el modelo SaaS, el cliente provee sus propias credenciales
        self.username = username
        self.password = password
            
        self.base_url = "https://api.invertironline.com/api/v2"
        self.token_url = "https://api.invertironline.com/token"
        
        # Gestor de Sesiones persistente usando la sesión individual de Streamlit
        if 'iol_access_token' not in st.session_state:
            st.session_state['iol_access_token'] = None
        if 'iol_refresh_token' not in st.session_state:
            st.session_state['iol_refresh_token'] = None
        if 'iol_token_expires' not in st.session_state:
            st.session_state['iol_token_expires'] = 0

    def login(self):
        """Autenticación inicial real vía POST a IOL"""
        data = {
            "username": self.username,
            "password": self.password,
            "grant_type": "password"
        }
        try:
            response = requests.post(self.token_url, data=data, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                st.session_state['iol_access_token'] = token_data.get('access_token')
                st.session_state['iol_refresh_token'] = token_data.get('refresh_token')
                expires_in = float(token_data.get('expires_in', 900))
                st.session_state['iol_token_expires'] = time.time() + expires_in - 30 
                return True
            else:
                st.error(f"Error de Login (IOL): {response.status_code} - {response.text}")
                return False
        except Exception as e:
            st.error(f"Error de red al conectar con IOL: {e}")
            return False

    def silent_refresh(self):
        """Refresca el token evitando volver a pedir login"""
        if not st.session_state.get('iol_refresh_token'):
            return self.login()
            
        data = {
            "refresh_token": st.session_state['iol_refresh_token'],
            "grant_type": "refresh_token"
        }
        try:
            response = requests.post(self.token_url, data=data, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                st.session_state['iol_access_token'] = token_data.get('access_token')
                if 'refresh_token' in token_data:
                    st.session_state['iol_refresh_token'] = token_data['refresh_token']
                expires_in = float(token_data.get('expires_in', 900))
                st.session_state['iol_token_expires'] = time.time() + expires_in - 30
                return True
            else:
                return self.login()
        except:
            return self.login()

    def _ensure_auth(self):
        if not st.session_state.get('iol_access_token'):
            self.login()
        elif time.time() > st.session_state.get('iol_token_expires', 0):
            try:
                self.silent_refresh()
            except Exception:
                self.login()
        return st.session_state.get('iol_access_token')

    def get_options_data(self, underlying_ticker="GGAL"):
        """Endpoint real de Opciones IOL"""
        token = self._ensure_auth()
        if not token:
            return pd.DataFrame()
        return self._fetch_options_cached(underlying_ticker, token, self.base_url)

    @staticmethod
    @st.cache_data(ttl=30) 
    def _fetch_options_cached(ticker, access_token, base_url):
        headers = {"Authorization": f"Bearer {access_token}"}
        url = f"{base_url}/bCBA/Titulos/{ticker}/Opciones"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    st.warning(f"IOL no reportó opciones activas para {ticker}.")
                    return pd.DataFrame()
                
                df = pd.DataFrame(data)
                df_final = pd.DataFrame()
                
                if 'simbolo' in df.columns:
                    df_final["Especie"] = df["simbolo"]
                    df_final["Tipo"] = df["simbolo"].apply(lambda x: "Call" if "C" in str(x)[3:5] else ("Put" if "V" in str(x)[3:5] else "Call"))
                    df_final["Base"] = df["simbolo"].str.extract(r'([0-9]+)')[0].astype(float, errors='ignore')
                else:
                    return pd.DataFrame()

                if 'cotizacion' in df.columns:
                    df_final["Último"] = df["cotizacion"].apply(lambda x: x.get("ultimoPrecio", 0) if isinstance(x, dict) else 0)
                    df_final["Bid"] = df["cotizacion"].apply(lambda x: x.get("puntas", [{}])[0].get("precioCompra", x.get("ultimoPrecio", 0)) if isinstance(x, dict) and x.get("puntas") else x.get("ultimoPrecio", 0))
                    df_final["Ask"] = df["cotizacion"].apply(lambda x: x.get("puntas", [{}])[0].get("precioVenta", x.get("ultimoPrecio", 0)) if isinstance(x, dict) and x.get("puntas") else x.get("ultimoPrecio", 0))
                else:
                    df_final["Último", "Bid", "Ask"] = [0, 0, 0]
                
                return df_final[pd.to_numeric(df_final["Último"], errors='coerce').fillna(0) > 0].reset_index(drop=True)
                
            else:
                st.error(f"Error Opciones ({response.status_code})")
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Error de red IOL: {e}")
            return pd.DataFrame()

    def get_candlestick_data(self, ticker="GGAL", timeframe="1D", limit=120):
        """Histórico real de IOL."""
        token = self._ensure_auth()
        if not token:
            return pd.DataFrame()
        return self._fetch_historic_cached(ticker, limit, token, self.base_url)

    @staticmethod
    @st.cache_data(ttl=300) 
    def _fetch_historic_cached(ticker, limit, access_token, base_url):
        headers = {"Authorization": f"Bearer {access_token}"}
        fecha_hasta = datetime.today()
        fecha_desde = fecha_hasta - timedelta(days=limit * 1.5)
        f_hasta_str = fecha_hasta.strftime("%Y-%m-%d")
        f_desde_str = fecha_desde.strftime("%Y-%m-%d")
        url = f"{base_url}/bCBA/Titulos/{ticker}/Cotizacion/seriehistorica/{f_desde_str}/{f_hasta_str}/sinAjustar"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    return pd.DataFrame()
                
                df = pd.DataFrame(data)
                df.rename(columns={
                    "fechaHora": "Date", "apertura": "Open", 
                    "maximo": "High", "minimo": "Low",
                    "ultimoPrecio": "Close", "volumen": "Volume",
                    "montoOperado": "Volume" # A veces IOL lo manda así
                }, inplace=True, errors="ignore")
                
                if "Close" not in df.columns:
                    df["Close"] = df.get("ultimoPrecio", 0)
                for col in ["Open", "High", "Low"]:
                    if col not in df.columns:
                        df[col] = df["Close"]
                if "Volume" not in df.columns:
                    df["Volume"] = 0
                
                if "Date" in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], format='mixed', errors='coerce')
                
                return df.tail(limit).reset_index(drop=True)
            else:
                st.error(f"Error IOL {response.status_code}: {response.text}")
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Excepción IOL: {e}")
            return pd.DataFrame()
