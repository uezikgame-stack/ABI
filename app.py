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

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="Rillet Neural Pro", layout="wide")

lang = st.sidebar.radio("ЯЗЫК / LANGUAGE", ["RU", "EN"])
txt = {
    "RU": {
        "market": "РЫНОК", "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)",
        "profit": "ПРОФИТ (%)", "chart": "НЕЙРОСЕТЕВОЙ ПРОГНОЗ (LSTM)", "news": "НОВОСТИ АКЦИИ",
        "signal": "СИГНАЛ", "buy": "✅ ПОКУПАТЬ", "sell": "❌ ПРОДАВАТЬ", "hold": "⚖️ ЖДАТЬ",
        "brokers": "ТОП 15 БРОКЕРОВ", "trust": "ДОВЕРИЕ", "details": "ДЕТАЛИ",
        "founder": "Основатель", "history": "История", "lawsuits": "Иски", "fact": "Факт"
    },
    "EN": {
        "market": "MARKET", "select": "SELECT ASSET:", "current": "CURRENT", "target": "TARGET (7d)",
        "profit": "EST. PROFIT", "chart": "NEURAL FORECAST (LSTM)", "news": "ASSET NEWS",
        "signal": "SIGNAL", "buy": "✅ BUY", "sell": "❌ SELL", "hold": "⚖️ HOLD",
        "brokers": "TOP 15 BROKERS", "trust": "TRUST", "details": "DETAILS",
        "founder": "Founder", "history": "History", "lawsuits": "Lawsuits", "fact": "Fact"
    }
}[lang]

st.markdown("""<style>
    .stApp { background-color: #020508; color: #00ffcc; }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    .analysis-card { background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; padding: 15px; margin-bottom: 10px; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #00ffcc !important; }
</style>""", unsafe_allow_html=True)

# --- БАЗА ДАННЫХ ---
DB = {
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL"],
    "KAZAKHSTAN": ["KMGZ.KZ", "HSBK.KZ", "KSPI.KZ", "KASE.KZ"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX"]
}

BROKERS_DB = {
    "Interactive Brokers": {"trust": 99.2, "founder": "Thomas Peterffy", "lic": "SEC, FCA", "fees": "0.005$/sh", "fact": "Pioneered electronic trading.", "law": "Fined in 2020 (AML)."},
    "Fidelity": {"trust": 98.5, "founder": "Edward Johnson", "lic": "FINRA", "fees": "$0", "fact": "Largest retirement provider.", "law": "Class action 2023."},
    "Saxo Bank": {"trust": 96.0, "founder": "Kim Fournais", "lic": "Danish FSA", "fees": "0.1%+", "fact": "European multi-asset leader.", "law": "Reg fine 2021."},
    "Freedom Finance": {"trust": 94.5, "founder": "Timur Turlov", "lic": "SEC, AFSA", "fees": "0.02%", "fact": "Direct IPO access.", "law": "Short-seller report cleared."},
    "Charles Schwab": {"trust": 98.0, "founder": "Charles Schwab", "lic": "SEC, FINRA", "fees": "$0", "fact": "Pioneer of low fees.", "law": "Robo-advisor settlement."},
    "Swissquote": {"trust": 95.5, "founder": "Marc Bürki", "lic": "FINMA", "fees": "High", "fact": "Swiss bank security.", "law": "None major."},
    "Vantage": {"trust": 93.8, "founder": "Group", "lic": "ASIC, FCA", "fees": "Low", "fact": "Fastest growing 2026.", "law": "None."},
    "Exante": {"trust": 91.2, "founder": "Alexey Kirienko", "lic": "CySEC, SFC", "fees": "0.02%", "fact": "One account, all markets.", "law": "SEC case dismissed."},
    "Webull": {"trust": 90.0, "founder": "Wang Anquan", "lic": "SEC, FINRA", "fees": "$0", "fact": "Advanced mobile tools.", "law": "PFOF disclosure audit."},
    "Tiger Brokers": {"trust": 89.5, "founder": "Wu Tianhua", "lic": "MAS, ASIC", "fees": "Low", "fact": "Backed by Xiaomi.", "law": "Compliance review 2022."},
    "Pepperstone": {"trust": 92.5, "founder": "Owen Kerr", "lic": "FCA, ASIC", "fees": "Spreads", "fact": "Razor spreads for FX.", "law": "None."},
    "Robinhood": {"trust": 88.0, "founder": "Vlad Tenev", "lic": "SEC, FINRA", "fees": "$0", "fact": "User-friendly pioneer.", "law": "GameStop saga fines."},
    "E*TRADE": {"trust": 93.0, "founder": "William Porter", "lic": "SEC", "fees": "$0", "fact": "Owned by Morgan Stanley.", "law": "Technical outage suit."},
    "AvaTrade": {"trust": 87.5, "founder": "Emanuel Many", "lic": "CBI, ASIC", "fees": "Spreads", "fact": "Strong CFD education.", "law": "Italy reg. fine."},
    "BlackRock": {"trust": 99.8, "founder": "Larry Fink", "lic": "Global", "fees": "Inst.", "fact": "Manages $10T in assets.", "law": "ESG litigation."}
}

# --- ЯДРО МОДЕЛИ ---
def predict_lstm(data_series):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data_series.values.reshape(-1, 1))
    window = 5
    X, y = [], []
    for i in range(window, len(scaled_data)):
        X.append(scaled_data[i-window:i, 0])
        y.append(scaled_data[i, 0])
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    
    model = Sequential([LSTM(32, return_sequences=False, input_shape=(window, 1)), Dense(1)])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=10, batch_size=1, verbose=0)
    
    last_batch = scaled_data[-window:].reshape(1, window, 1)
    preds = []
    for _ in range(7):
        p = model.predict(last_batch, verbose=0)
        preds.append(p[0,0])
        last_batch = np.append(last_batch[:, 1:, :], [[p[0]]], axis=1)
    return scaler.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()

def get_news_analysis(t, l):
    try:
        gn = GNews(language='ru' if l == "RU" else 'en', max_results=3, period='7d')
        news = gn.get_news(f"{t} stock")
        if not news: return txt["hold"], []
        pos = sum(1 for n in news if any(w in n['title'].lower() for w in ['up', 'buy', 'рост', 'прогноз']))
        neg = sum(1 for n in news if any(w in n['title'].lower() for w in ['down', 'sell', 'риск', 'падение']))
        sig = txt["buy"] if pos > neg else (txt["sell"] if neg > pos else txt["hold"])
        return sig, news
    except: return txt["hold"], []

# --- ИНТЕРФЕЙС ---
st.sidebar.title("RILLET NEURAL")
page = st.sidebar.selectbox("МЕНЮ", [txt["market"], txt["brokers"]])

if page == txt["market"]:
    sec = st.sidebar.selectbox("СЕКТОР", list(DB.keys()))
    t_sel = st.selectbox(txt["select"], DB[sec])
    
    df_raw = yf.download(t_sel, period="6mo", progress=False, auto_adjust=True)
    if not df_raw.empty:
        if isinstance(df_raw.columns, pd.MultiIndex): df_raw.columns = df_raw.columns.get_level_values(0)
        df = df_raw[['Close']].dropna()
        
        with st.spinner('Neural Network training...'):
            forecast = predict_lstm(df['Close'])
            signal, news_list = get_news_analysis(t_sel, lang)
        
        p_now = float(df['Close'].iloc[-1])
        pct = ((forecast[-1] / p_now) - 1) * 100
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now:,.2f} $</h3></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{forecast[-1]:,.2f} $</h3></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card' style='border-color:{'#00ffcc' if pct>0 else '#ff4b4b'}'>{txt['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)
        
        # График по дням
        last_dates = df.index[-20:]
        future_dates = [last_dates[-1] + timedelta(days=i) for i in range(1, 8)]
        st.write(f"#### {txt['chart']} - {t_sel}")
        chart_data = pd.DataFrame({
            "History": pd.Series(df['Close'].tail(20).values, index=last_dates),
            "LSTM Forecast": pd.Series(forecast, index=future_dates)
        })
        st.line_chart(chart_data)
        
        st.write(f"#### 📰 {txt['news']} ({t_sel}) & {txt['signal']}")
        st.markdown(f"<div class='analysis-card'><b>{txt['signal']}: {signal}</b></div>", unsafe_allow_html=True)
        for n in news_list:
            st.markdown(f"<div class='analysis-card'><small>{n['published date']}</small><br>{n['title']}</div>", unsafe_allow_html=True)
    else: st.error("Data unavailable")

elif page == txt["brokers"]:
    st.write(f"## 🏛️ {txt['brokers']}")
    for name, info in BROKERS_DB.items():
        with st.expander(f"{name} — {txt['trust']}: {info['trust']}%"):
            st.write(f"**{txt['founder']}:** {info['founder']}")
            st.write(f"**Лицензия:** {info['lic']}")
            st.write(f"**Комиссия:** {info['fees']}")
            st.write(f"**{txt['fact']}:** {info['fact']}")
            st.markdown(f"**{txt['lawsuits']}:** <span style='color:#ff4b4b'>{info['law']}</span>", unsafe_allow_html=True)

st.caption(f"Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
