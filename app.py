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

# --- 1. СТИЛЬ И БРЕНДИНГ RILLET ---
st.set_page_config(page_title="Rillet Neural ML", layout="wide")

lang = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["EN", "RU"])
txt = {
    "EN": {
        "market": "MARKET", "currency": "CURRENCY", "price": "PRICE", "forecast": "FORECAST %",
        "select": "SELECT ASSET:", "current": "CURRENT PRICE", "target": "TARGET (7d)",
        "profit": "EST. PROFIT", "chart_title": "NEURAL NETWORK FORECAST (LSTM)", "news_title": "INFO-FIELD ANALYSIS",
        "buy": "✅ STRONG BUY", "sell": "❌ SELL / HOLD", "hold": "⚖️ NEUTRAL", "no_news": "No news found.",
        "update": "Data updated", "signal": "FINAL SIGNAL",
        "brokers": "TOP 15 BROKERS", "trust": "TRUST LEVEL", "details": "DETAILS",
        "history": "History", "founder": "Founder", "fact": "Fun Fact", "lawsuits": "Major Lawsuits",
        "license": "License", "fees": "Commissions", "withdraw": "Withdrawal", "assets": "Available Assets"
    },
    "RU": {
        "market": "РЫНОК", "currency": "ВАЛЮТА", "price": "ЦЕНА", "forecast": "ПРОГНОЗ %",
        "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)",
        "profit": "ПРОФИТ (%)", "chart_title": "НЕЙРОСЕТЕВОЙ ПРОГНОЗ (LSTM)", "news_title": "АНАЛИЗ НОВОСТЕЙ",
        "buy": "✅ ПОКУПАТЬ", "sell": "❌ ПРОДАВАТЬ/ЖДАТЬ", "hold": "⚖️ УДЕРЖИВАТЬ", "no_news": "Новостей не найдено.",
        "update": "Обновление данных", "signal": "ИТОГОВЫЙ СИГНАЛ",
        "brokers": "ТОП 15 БРОКЕРОВ", "trust": "УРОВЕНЬ ДОВЕРИЯ", "details": "ДЕТАЛИ",
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
    </style>
    """, unsafe_allow_html=True)

# --- 2. ПОЛНАЯ БАЗА ДАННЫХ (15 БРОКЕРОВ + КИТАЙ) ---
DB = {
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL"],
    "KAZAKHSTAN": ["KMGZ.KZ", "HSBK.KZ", "KCZ.L", "KSPI.KZ"],
    "EUROPE": ["ASML", "MC.PA", "SAP.DE", "AIR.PA"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX"]
}

BROKERS_DB = {
    "Interactive Brokers": {"trust": 99.2, "founder": "Thomas Peterffy", "lic": "SEC, FCA", "fees": "0.005$/sh", "fact": "Pioneered electronic trading.", "law": "Fined in 2020."},
    "Fidelity": {"trust": 98.5, "founder": "Edward Johnson", "lic": "FINRA", "fees": "$0", "fact": "Best for long-term.", "law": "Class action 2023."},
    "Saxo Bank": {"trust": 96.0, "founder": "Kim Fournais", "lic": "FSA", "fees": "0.1%+", "fact": "Danish precision.", "law": "FSA fine 2021."},
    "Freedom Finance": {"trust": 94.5, "founder": "Timur Turlov", "lic": "SEC, AFSA", "fees": "0.02%", "fact": "IPO access.", "law": "Audit cleared."},
    "Charles Schwab": {"trust": 98.0, "founder": "Charles Schwab", "lic": "SEC", "fees": "$0", "fact": "US Giant.", "law": "Settled robo-case."},
    "Swissquote": {"trust": 95.5, "founder": "Marc Bürki", "lic": "FINMA", "fees": "High", "fact": "Swiss security.", "law": "None."},
    "Vantage": {"trust": 93.8, "founder": "Group", "lic": "ASIC", "fees": "Low", "fact": "Award winning.", "law": "None."},
    "Exante": {"trust": 91.2, "founder": "Alexey Kirienko", "lic": "CySEC", "fees": "0.02%", "fact": "Multi-asset account.", "law": "Case dismissed."},
    "Webull": {"trust": 90.0, "founder": "Wang Anquan", "lic": "SEC", "fees": "$0", "fact": "Great mobile UI.", "law": "PFOF audit."},
    "Tiger Brokers": {"trust": 89.5, "founder": "Wu Tianhua", "lic": "MAS", "fees": "Low", "fact": "Xiaomi backed.", "law": "Compliance audit."},
    "Pepperstone": {"trust": 92.5, "founder": "Owen Kerr", "lic": "FCA", "fees": "Spreads", "fact": "Fast execution.", "law": "None."},
    "Robinhood": {"trust": 88.0, "founder": "Vlad Tenev", "lic": "SEC", "fees": "$0", "fact": "Gen Z favorite.", "law": "GameStop fines."},
    "E*TRADE": {"trust": 93.0, "founder": "William Porter", "lic": "SEC", "fees": "$0", "fact": "Morgan Stanley owned.", "law": "Outages."},
    "AvaTrade": {"trust": 87.5, "founder": "Emanuel Many", "lic": "CBI", "fees": "Spreads", "fact": "CFD Focus.", "law": "Italy fine."},
    "BlackRock": {"trust": 99.8, "founder": "Larry Fink", "lic": "Global", "fees": "Inst.", "fact": "$10 Trillion AUM.", "law": "ESG legal battles."}
}

# --- 3. НЕЙРОСЕТЕВАЯ МОДЕЛЬ (LSTM) ---
def predict_lstm(data_series, days=7):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data_series.values.reshape(-1, 1))
    
    window = 5
    X, y = [], []
    for i in range(window, len(scaled_data)):
        X.append(scaled_data[i-window:i, 0])
        y.append(scaled_data[i, 0])
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    model = Sequential([
        LSTM(units=32, return_sequences=False, input_shape=(window, 1)),
        Dense(units=1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, epochs=15, batch_size=1, verbose=0) 

    last_window = scaled_data[-window:].reshape(1, window, 1)
    predictions = []
    current_batch = last_window
    
    for _ in range(days):
        pred = model.predict(current_batch, verbose=0)
        predictions.append(pred[0,0])
        current_batch = np.append(current_batch[:, 1:, :], [[pred[0]]], axis=1)
        
    return scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

# --- 4. НОВОСТИ И ВАЛЮТЫ ---
def get_news_signal(ticker, l):
    try:
        gn = GNews(language='ru' if l == "RU" else 'en', max_results=3, period='7d')
        news = gn.get_news(f"{ticker} stock")
        if not news: return txt["hold"], []
        pos = sum(1 for n in news if any(w in n['title'].lower() for w in ['up', 'buy', 'growth', 'рост']))
        neg = sum(1 for n in news if any(w in n['title'].lower() for w in ['down', 'sell', 'risk', 'падение']))
        sig = txt["buy"] if pos > neg else (txt["sell"] if neg > pos else txt["hold"])
        return sig, news
    except: return txt["hold"], []

# --- 5. ИНТЕРФЕЙС ---
st.sidebar.markdown('<div class="logo-text">RILLET LSTM</div>', unsafe_allow_html=True)
mode = st.sidebar.selectbox("MODE", [txt["market"], txt["brokers"]])

if mode == txt["market"]:
    region = st.sidebar.selectbox(txt["market"], list(DB.keys()))
    t_sel = st.selectbox(txt["select"], DB[region])
    
    # Решение проблемы Data Unavailable
    df_raw = yf.download(t_sel, period="6mo", interval="1d", progress=False, auto_adjust=True)
    
    if not df_raw.empty:
        if isinstance(df_raw.columns, pd.MultiIndex): df_raw.columns = df_raw.columns.get_level_values(0)
        df = df_raw[['Close']].dropna()
        
        with st.spinner('Neural Network training (LSTM)...'):
            f_prices = predict_lstm(df['Close'], days=7)
            sentiment, news_items = get_news_signal(t_sel, lang)
        
        p_now = float(df['Close'].iloc[-1])
        pct = ((f_prices[-1] / p_now) - 1) * 100
        clr = "#00ffcc" if pct > 0 else "#ff4b4b"

        # Метрики
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now:,.2f} $</h3></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{f_prices[-1]:,.2f} $</h3></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card' style='border-color:{clr}'>{txt['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)

        # График с датами
        st.write(f"#### {txt['chart_title']} - {t_sel}")
        last_dates = df.index[-20:]
        future_dates = [last_dates[-1] + timedelta(days=i) for i in range(1, 8)]
        chart_data = pd.DataFrame({
            "History": pd.Series(df['Close'].tail(20).values, index=last_dates),
            "LSTM Forecast": pd.Series(f_prices, index=future_dates)
        })
        st.line_chart(chart_data)

        # Блок новостей
        st.write(f"#### 📰 {txt['news_title']} ({t_sel})")
        st.markdown(f"<div class='analysis-card'><b>{txt['signal']}: {sentiment}</b></div>", unsafe_allow_html=True)
        for n in news_items:
            st.markdown(f"<div class='analysis-card'><small>{n['published date']}</small><br>{n['title']}</div>", unsafe_allow_html=True)
    else:
        st.error("Data Unavailable")

elif mode == txt["brokers"]:
    st.write(f"## 🏛️ {txt['brokers']}")
    for name, info in BROKERS_DB.items():
        with st.expander(f"{name} - {txt['trust']}: {info['trust']}%"):
            st.write(f"**{txt['founder']}:** {info['founder']}")
            st.write(f"**{txt['license']}:** {info['lic']}")
            st.write(f"**{txt['fees']}:** {info['fees']}")
            st.write(f"**{txt['fact']}:** {info['fact']}")
            st.markdown(f"**{txt['lawsuits']}:** <span style='color:#ff4b4b;'>{info['law']}</span>", unsafe_allow_html=True)

st.caption(f"{txt['update']}: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
