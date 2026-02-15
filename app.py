import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime
import xgboost as xgb

# --- 1. НАСТРОЙКИ И СТИЛЬ (Без изменений) ---
st.set_page_config(page_title="Rillet", layout="wide")

lang = st.sidebar.radio("ЯЗЫК / LANGUAGE", ["RU", "EN"])
txt = {
    "RU": {
        "market": "РЫНОК", "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ", 
        "target": "ЦЕЛЬ (7д ML)", "profit": "ПРОФИТ (%)", "chart": "ПРОГНОЗ XGBOOST",
        "signal": "СИГНАЛ", "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "hold": "ЖДАТЬ",
        "err_data": "Данные временно недоступны", "brokers": "ТОП БРОКЕРОВ"
    },
    "EN": {
        "market": "MARKET", "select": "SELECT ASSET:", "current": "CURRENT", 
        "target": "TARGET (7d ML)", "profit": "EST. PROFIT", "chart": "XGBOOST FORECAST",
        "signal": "SIGNAL", "buy": "BUY", "sell": "SELL", "hold": "HOLD",
        "err_data": "Data unavailable", "brokers": "TOP BROKERS"
    }
}[lang]

st.markdown("""
    <style>
    .stApp { background-color: #020508; color: #00ffcc; }
    .metric-card { background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; padding: 15px; border-radius: 10px; text-align: center; }
    h1, h2, h3, p, span { color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ (КИТАЙ ВЕРНУЛСЯ) ---
DB = {
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL"],
    "KAZAKHSTAN": ["KMGZ.KZ", "HSBK.KZ", "KCZ.L", "KSPI.KZ", "KASE.KZ"],
    "EUROPE": ["ASML", "MC.PA", "SAP.DE", "AIR.PA", "BMW.DE"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME"]
}

# --- 3. ML ЛОГИКА (БЕЗ ИЗМЕНЕНИЙ) ---
def train_and_forecast(df):
    try:
        data = df.copy()
        # Гарантируем, что работаем с одномерным рядом
        if isinstance(data, pd.DataFrame):
            data = data['Close']
        
        data = data.to_frame()
        data['target'] = data['Close'].shift(-1)
        data['lag_1'] = data['Close'].shift(1)
        data['ma_5'] = data['Close'].rolling(5).mean()
        data = data.dropna()
        
        model = xgb.XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.1)
        model.fit(data[['lag_1', 'ma_5']], data['Close'])
        
        preds = []
        curr_price = data['Close'].iloc[-1]
        curr_ma = data['ma_5'].iloc[-1]
        
        for _ in range(7):
            p = model.predict(np.array([[curr_price, curr_ma]]))[0]
            preds.append(p)
            curr_price = p
            
        return preds
    except: return None

# --- 4. ИНТЕРФЕЙС С РЕШЕНИЕМ ПРОБЛЕМЫ ---
st.sidebar.title("RILLET")
menu = st.sidebar.selectbox("MENU", [txt["market"], txt["brokers"]])

if menu == txt["market"]:
    market = st.sidebar.selectbox("REGION", list(DB.keys()))
    ticker = st.selectbox(txt["select"], DB[market])
    
    # РЕШЕНИЕ: Улучшенная загрузка данных
    with st.spinner('Accessing Financial API...'):
        # Используем auto_adjust и убираем MultiIndex
        df_raw = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
    
    if not df_raw.empty:
        # Очистка данных от вложенных колонок (решает проблему Data Unavailable)
        if isinstance(df_raw.columns, pd.MultiIndex):
            df_raw.columns = df_raw.columns.get_level_values(0)
            
        df = df_raw[['Close']].dropna()
        
        if len(df) > 10:
            with st.spinner('ML Training...'):
                forecast = train_and_forecast(df)
                
            if forecast:
                p_now = float(df['Close'].iloc[-1])
                p_fut = float(forecast[-1])
                diff = ((p_fut / p_now) - 1) * 100
                
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now:,.2f}</h3></div>", unsafe_allow_html=True)
                c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{p_fut:,.2f}</h3></div>", unsafe_allow_html=True)
                color = "#00ffcc" if diff > 0 else "#ff4b4b"
                c3.markdown(f"<div class='metric-card' style='border-color:{color}'>{txt['profit']}<br><h3>{diff:+.2f}%</h3></div>", unsafe_allow_html=True)
                
                # Объединяем историю и прогноз для графика
                chart_vals = np.append(df['Close'].tail(20).values, forecast)
                st.line_chart(chart_vals)
            else:
                st.error(txt["err_data"])
        else:
            st.error(txt["err_data"])
    else:
        st.error(txt["err_data"])

st.caption(f"Data updated (ML Core): {datetime.now().strftime('%Y-%m-%d-%H')}")
