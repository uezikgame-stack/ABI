import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

# --- 1. СТИЛЬ И БРЕНДИНГ RILLET ---
st.set_page_config(page_title="Rillet", layout="wide")

# --- ЛОКАЛИЗАЦИЯ ---
lang = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["EN", "RU"])
txt = {
    "EN": {
        "market": "MARKET", "currency": "CURRENCY", "price": "PRICE", "forecast": "FORECAST %",
        "select": "SELECT ASSET:", "current": "CURRENT PRICE", "target": "TARGET (7d)",
        "profit": "EST. PROFIT", "chart_title": "NEURAL NETWORK FORECAST (LSTM)", "news_title": "INFO-FIELD ANALYSIS",
        "buy": "✅ STRONG BUY", "sell": "❌ SELL / HOLD", "hold": "⚖️ NEUTRAL", "no_news": "No news found.",
        "update": "Data updated", "signal": "FINAL SIGNAL",
        "brokers": "TOP BROKERS", "trust": "TRUST LEVEL", "details": "DETAILS",
        "history": "History", "founder": "Founder", "fact": "Fun Fact", "lawsuits": "Major Lawsuits",
        "license": "License", "fees": "Commissions", "withdraw": "Withdrawal", "assets": "Available Assets"
    },
    "RU": {
        "market": "РЫНОК", "currency": "ВАЛЮТА", "price": "ЦЕНА", "forecast": "ПРОГНОЗ %",
        "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)",
        "profit": "ПРОФИТ (%)", "chart_title": "НЕЙРОСЕТЕВОЙ ПРОГНОЗ (LSTM)", "news_title": "АНАЛИЗ ИНФОПОЛЯ",
        "buy": "✅ ПОКУПАТЬ", "sell": "❌ ПРОДАВАТЬ/ЖДАТЬ", "hold": "⚖️ УДЕРЖИВАТЬ", "no_news": "Новостей не найдено.",
        "update": "Обновление данных", "signal": "ИТОГОВЫЙ СИГНАЛ",
        "brokers": "ТОП БРОКЕРОВ", "trust": "УРОВЕНЬ ДОВЕРИЯ", "details": "ДЕТАЛИ",
        "history": "История", "founder": "Основатель", "fact": "Интересный факт", "lawsuits": "Крупные иски",
        "license": "Лицензия", "fees": "Комиссии", "withdraw": "Вывод", "assets": "Активы"
    }
}[lang]

st.markdown("""
    <style>
    .stApp { background-color: #020508 !important; color: #00ffcc; }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #00ffcc !important; }
    .logo-text { font-size: 42px; font-weight: bold; text-align: center; color: #00ffcc; border-bottom: 2px solid #00ffcc; margin-bottom: 20px; }
    .analysis-card { background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; padding: 15px; margin-bottom: 10px; border-radius: 10px; }
    .info-tag { background: #00ffcc22; padding: 2px 8px; border-radius: 5px; font-size: 0.8em; margin-right: 5px; border: 1px solid #00ffcc44; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ АКТИВОВ И БРОКЕРОВ ---
DB = {
    "USA": ["AAPL", "NVDA", "TSLA"],
    "KAZAKHSTAN": ["KCZ.L", "HSBK.KZ"],
    "RUSSIA": ["SBER.ME", "YNDX"]
}

raw_brokers = {
    "Interactive Brokers": {
        "trust": 99.2, "founder": "Thomas Peterffy", "license": "SEC, FINRA", "fees": "0.005$/sh", "withdraw": "1-3d", "assets": "Global",
        "history": {"EN": "Pioneered electronic trading.", "RU": "Пионеры электронного трейдинга."},
        "fact": {"EN": "Father of digital trading.", "RU": "Основатель — отец цифровой торговли."},
        "lawsuits": {"EN": "Fined in 2020.", "RU": "Штраф в 2020 году."}
    }
}

# --- 3. НЕЙРОСЕТЕВАЯ МОДЕЛЬ (LSTM) ---
def predict_lstm(data_series, days=7):
    # Подготовка данных
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data_series.values.reshape(-1, 1))
    
    # Создание обучающей выборки (окно 5 дней)
    window = 5
    X, y = [], []
    for i in range(window, len(scaled_data)):
        X.append(scaled_data[i-window:i, 0])
        y.append(scaled_data[i, 0])
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    # Сборка легкой модели LSTM
    model = Sequential([
        LSTM(units=32, return_sequences=False, input_shape=(window, 1)),
        Dense(units=1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, epochs=10, batch_size=1, verbose=0) # Быстрое обучение

    # Прогноз на 7 дней
    last_window = scaled_data[-window:].reshape(1, window, 1)
    predictions = []
    current_batch = last_window
    
    for _ in range(days):
        pred = model.predict(current_batch, verbose=0)
        predictions.append(pred[0,0])
        current_batch = np.append(current_batch[:, 1:, :], [[pred[0]]], axis=1)
        
    return scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

@st.cache_data(ttl=86400)
def fetch_all(m_name, key):
    tickers = DB[m_name]
    data = yf.download(tickers, period="2mo", interval="1d", group_by='ticker', progress=False)
    clean = []
    for t in tickers:
        df = data[t].dropna()
        if not df.empty:
            p_now = float(df['Close'].iloc[-1])
            clean.append({"T": t, "P": p_now, "DF": df})
    return clean

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.markdown('<div class="logo-text">RILLET</div>', unsafe_allow_html=True)
mode = st.sidebar.selectbox("MODE", [txt["market"], txt["brokers"]])

if mode == txt["market"]:
    m_name = st.sidebar.selectbox(txt["market"], list(DB.keys()))
    assets = fetch_all(m_name, datetime.now().strftime("%H"))
    
    if assets:
        t_sel = st.selectbox(txt["select"], [x['T'] for x in assets])
        item = next(x for x in assets if x['T'] == t_sel)
        
        # Запуск нейросети
        with st.spinner('Neural Network training...'):
            f_prices = predict_lstm(item['DF']['Close'], days=7)
        
        p_now = item['P']
        pct = ((f_prices[-1] / p_now) - 1) * 100
        clr = "#00ffcc" if pct > 0 else "#ff4b4b"

        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now:,.2f}</h3></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{f_prices[-1]:,.2f}</h3></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card' style='border-color:{clr}'>{txt['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)

        st.write(f"#### {txt['chart_title']} {t_sel}")
        hist = item['DF']['Close'].tail(15).values
        st.line_chart(np.append(hist, f_prices), color="#00ffcc")

elif mode == txt["brokers"]:
    for b_name, b_info in raw_brokers.items():
        st.write(f"### {b_name} - {b_info['trust']}%")
        with st.expander(txt["details"]):
            st.write(f"{txt['history']}: {b_info['history'][lang]}")
