import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

# --- 1. СТИЛЬ ---
st.set_page_config(page_title="Rillet Pro", layout="wide")
st.markdown("""<style>
    .stApp { background-color: #020508; color: #00ffcc; }
    .metric-card { background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #00ffcc !important; }
</style>""", unsafe_allow_html=True)

# --- 2. БАЗА (ТОП 15 БРОКЕРОВ + КИТАЙ) ---
DB = {
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL"],
    "KAZAKHSTAN": ["KMGZ.KZ", "HSBK.KZ", "KSPI.KZ", "KASE.KZ"]
}

BROKERS = {
    "Interactive Brokers": {"trust": 99.2, "lic": "SEC, FCA", "law": "Fined 2020 (AML)."},
    "Fidelity": {"trust": 98.5, "lic": "FINRA", "law": "Class action 2023."},
    "Saxo Bank": {"trust": 96.0, "lic": "FSA", "law": "FSA fine 2021."},
    "Freedom Finance": {"trust": 94.5, "lic": "SEC, AFSA", "law": "Audit cleared."},
    "Charles Schwab": {"trust": 98.0, "lic": "SEC", "law": "Robo-case settled."},
    "Swissquote": {"trust": 95.5, "lic": "FINMA", "law": "None."},
    "Vantage": {"trust": 93.8, "lic": "ASIC", "law": "None."},
    "Exante": {"trust": 91.2, "lic": "CySEC", "law": "SEC case dismissed."},
    "Webull": {"trust": 90.0, "lic": "SEC", "law": "PFOF audit."},
    "Tiger Brokers": {"trust": 89.5, "lic": "MAS", "law": "Compliance audit."},
    "Pepperstone": {"trust": 92.5, "lic": "ASIC", "law": "None."},
    "Robinhood": {"trust": 88.0, "lic": "SEC", "law": "GameStop fines."},
    "E*TRADE": {"trust": 93.0, "lic": "SEC", "law": "Outage suit."},
    "AvaTrade": {"trust": 87.5, "lic": "CBI", "law": "Italy fine."},
    "BlackRock": {"trust": 99.8, "lic": "Global", "law": "ESG litigation."}
}

# --- 3. ЛОГИКА ---
def run_lstm(data):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(data.values.reshape(-1, 1))
    X = []
    for i in range(5, len(scaled)): X.append(scaled[i-5:i, 0])
    X = np.reshape(np.array(X), (len(X), 5, 1))
    
    model = Sequential([LSTM(32, input_shape=(5, 1)), Dense(1)])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, scaled[5:], epochs=5, verbose=0)
    
    last_win = scaled[-5:].reshape(1, 5, 1)
    preds = []
    for _ in range(7):
        p = model.predict(last_win, verbose=0)
        preds.append(p[0,0])
        last_win = np.append(last_win[:, 1:, :], [[p[0]]], axis=1)
    return scaler.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.title("RILLET ML")
mode = st.sidebar.selectbox("MENU", ["MARKET", "BROKERS"])

if mode == "MARKET":
    sec = st.sidebar.selectbox("SECTOR", list(DB.keys()))
    t_sel = st.selectbox("SELECT ASSET:", DB[sec])
    
    # Фикс загрузки данных
    df = yf.download(t_sel, period="6mo", progress=False, auto_adjust=True)
    
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        with st.spinner('Neural Training...'):
            forecast = run_lstm(df['Close'])
            
        p_now = df['Close'].iloc[-1]
        
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'>PRICE<br><h3>{p_now:,.2f} $</h3></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>TARGET (7d)<br><h3>{forecast[-1]:,.2f} $</h3></div>", unsafe_allow_html=True)
        
        # График по дням
        f_dates = [df.index[-1] + timedelta(days=i) for i in range(1, 8)]
        chart_data = pd.DataFrame({
            "History": pd.Series(df['Close'].tail(20).values, index=df.index[-20:]),
            "Forecast": pd.Series(forecast, index=f_dates)
        })
        st.line_chart(chart_data)
    else:
        st.error("Данные временно недоступны. Проверьте тикер.")

elif mode == "BROKERS":
    st.write("## TOP 15 BROKERS")
    for name, info in BROKERS.items():
        with st.expander(f"{name} (Trust: {info['trust']}%)"):
            st.write(f"**License:** {info['lic']}")
            st.write(f"**Lawsuits:** {info['law']}")
