import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime, timedelta
import xgboost as xgb

# --- 1. СТИЛЬ И БРЕНДИНГ RILLET ---
st.set_page_config(page_title="Rillet ML", layout="wide")

# --- ЛОКАЛИЗАЦИЯ ---
lang = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["EN", "RU"])
txt = {
    "EN": {
        "market": "MARKET", "currency": "CURRENCY", "price": "PRICE", "forecast": "FORECAST %",
        "select": "SELECT ASSET:", "current": "CURRENT PRICE", "target": "TARGET (7d ML)",
        "profit": "EST. PROFIT", "chart_title": "XGBOOST ML FORECAST", "news_title": "INFO-FIELD ANALYSIS",
        "buy": "✅ STRONG BUY", "sell": "❌ SELL / HOLD", "hold": "⚖️ NEUTRAL", "no_news": "No news found.",
        "update": "Data updated", "signal": "FINAL SIGNAL",
        "brokers": "TOP BROKERS", "trust": "TRUST LEVEL", "details": "DETAILS",
        "history": "History", "founder": "Founder", "fact": "Fun Fact", "lawsuits": "Major Lawsuits",
        "license": "License", "fees": "Commissions", "withdraw": "Withdrawal", "assets": "Available Assets"
    },
    "RU": {
        "market": "РЫНОК", "currency": "ВАЛЮТА", "price": "ЦЕНА", "forecast": "ПРОГНОЗ %",
        "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д ML)",
        "profit": "ПРОФИТ (%)", "chart_title": "ПРОГНОЗ ML (XGBOOST)", "news_title": "АНАЛИЗ ИНФОПОЛЯ",
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

# --- 2. ПОЛНАЯ БАЗА ДАННЫХ (БРОКЕРЫ + КИТАЙ) ---
DB = {
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "GOOGL", "META"],
    "KAZAKHSTAN": ["KMGZ.KZ", "HSBK.KZ", "KSPI.KZ", "KASE.KZ"],
    "EUROPE": ["ASML", "MC.PA", "SAP.DE", "AIR.PA", "BMW.DE"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME"]
}

raw_brokers = {
    "Interactive Brokers": {
        "trust": 99.2, "founder": "Thomas Peterffy", "license": "SEC, FINRA, FCA", "fees": "0.005$/sh", "withdraw": "1-3d", "assets": "Global Stocks, Options, Futures",
        "history": {"EN": "Pioneered electronic trading.", "RU": "Пионеры электронного трейдинга."},
        "fact": {"EN": "Father of digital trading.", "RU": "Основатель — отец цифровой торговли."},
        "lawsuits": {"EN": "Fined $38M in 2020.", "RU": "Штраф $38 млн в 2020 году."}
    },
    "Freedom Finance": {
        "trust": 94.5, "founder": "Timur Turlov", "license": "SEC, CySEC, AFSA", "fees": "0.02%", "withdraw": "Instant", "assets": "IPO, US & EU Stocks",
        "history": {"EN": "NASDAQ listed holding.", "RU": "Холдинг, котирующийся на NASDAQ."},
        "fact": {"EN": "Dominates Central Asia.", "RU": "Лидер рынка в Центральной Азии."},
        "lawsuits": {"EN": "Cleared audit in 2023.", "RU": "Успешно прошли аудит в 2023."}
    },
    "Tinkoff (RU)": {
        "trust": 88.5, "founder": "Oleg Tinkov", "license": "CBR (RU)", "fees": "0.025%+", "withdraw": "Instant", "assets": "RU Stocks, Currencies",
        "history": {"EN": "Leading digital bank.", "RU": "Ведущий цифровой банк РФ."},
        "fact": {"EN": "Zero physical branches.", "RU": "Банк без физических отделений."},
        "lawsuits": {"EN": "Sanctions-related shifts.", "RU": "Изменения из-за санкций."}
    },
    "Saxo Bank": {
        "trust": 96.0, "founder": "Kim Fournais", "license": "FSA, FINMA", "fees": "0.1%", "withdraw": "2-5d", "assets": "FX, Stocks, Bonds",
        "history": {"EN": "Danish investment bank.", "RU": "Датский инвестиционный банк."},
        "fact": {"EN": "First online trading platform in 1992.", "RU": "Первая онлайн-платформа в 1992."},
        "lawsuits": {"EN": "Regulatory fines in 2021.", "RU": "Регуляторные штрафы в 2021."}
    }
}

# --- 3. ML ИНСТРУМЕНТАРИЙ ---
def train_and_forecast_ml(df):
    try:
        data = df.copy()
        if isinstance(data, pd.DataFrame): data = data['Close']
        data = data.to_frame()
        data['target'] = data['Close'].shift(-1)
        data['lag_1'] = data['Close'].shift(1)
        data['ma_5'] = data['Close'].rolling(5).mean()
        data = data.dropna()
        
        model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05)
        model.fit(data[['lag_1', 'ma_5']], data['Close'])
        
        preds = []
        curr_p = data['Close'].iloc[-1]
        curr_m = data['ma_5'].iloc[-1]
        for _ in range(7):
            p = model.predict(np.array([[curr_p, curr_m]]))[0]
            preds.append(p)
            curr_p = p
        return preds
    except: return None

@st.cache_data(ttl=3600)
def get_rates():
    try:
        raw = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="5d", progress=False)['Close']
        return {"$": 1.0, "₽": float(raw["RUB=X"].iloc[-1]), "₸": float(raw["KZT=X"].iloc[-1]), "EUR": float(raw["EURUSD=X"].iloc[-1])}
    except: return {"$": 1.0, "₽": 92.0, "₸": 450.0, "EUR": 1.08}

@st.cache_data(ttl=86400)
def analyze_news(ticker, l):
    try:
        gn = GNews(language='ru' if l == "RU" else 'en', period='7d', max_results=5)
        news = gn.get_news(f"{ticker} stock")
        if not news: return txt["hold"]
        pos = sum(1 for n in news if any(w in n['title'].lower() for w in ['up', 'growth', 'buy', 'рост', 'профит']))
        neg = sum(1 for n in news if any(w in n['title'].lower() for w in ['down', 'crash', 'sell', 'падение', 'убыток']))
        return txt["buy"] if pos > neg else (txt["sell"] if neg > pos else txt["hold"])
    except: return txt["hold"]

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.markdown('<div class="logo-text">RILLET ML</div>', unsafe_allow_html=True)
mode = st.sidebar.selectbox("MODE", [txt["market"], txt["brokers"]])

if mode == txt["market"]:
    market = st.sidebar.selectbox(txt["market"], list(DB.keys()))
    curr_choice = st.sidebar.radio(txt["currency"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
    sign = curr_choice.split("(")[1][0]
    rates = get_rates()
    
    t_sel = st.selectbox(txt["select"], DB[market])
    
    # ИСПРАВЛЕННАЯ ЗАГРУЗКА (решение проблемы Data Unavailable)
    df_raw = yf.download(t_sel, period="1y", interval="1d", progress=False, auto_adjust=True)
    
    if not df_raw.empty:
        if isinstance(df_raw.columns, pd.MultiIndex): df_raw.columns = df_raw.columns.get_level_values(0)
        df = df_raw[['Close']].dropna()
        
        with st.spinner('ML Core Processing...'):
            forecast = train_and_forecast_ml(df)
            news_signal = analyze_news(t_sel, lang)
            
        if forecast:
            # Конвертация
            conv = rates.get(sign, 1.0)
            p_now = float(df['Close'].iloc[-1]) * conv
            p_fut = float(forecast[-1]) * conv
            pct = ((p_fut / p_now) - 1) * 100
            
            # Рендер карточек
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{p_fut:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
            clr = "#00ffcc" if pct > 0 else "#ff4b4b"
            c3.markdown(f"<div class='metric-card' style='border-color:{clr}'>{txt['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)
            
            st.write(f"#### {txt['chart_title']} {t_sel}")
            st.line_chart(np.append(df['Close'].tail(30).values * conv, np.array(forecast) * conv))
            st.markdown(f"<div class='analysis-card'><b>{txt['signal']}:</b> {news_signal}</div>", unsafe_allow_html=True)

elif mode == txt["brokers"]:
    st.write(f"## 🏛️ {txt['brokers']}")
    for b_name, b_info in raw_brokers.items():
        t_val = b_info['trust']
        b_clr = "#00ffcc" if t_val > 90 else "#ffcc00"
        st.markdown(f"""
        <div class="analysis-card">
            <div style="display:flex; justify-content:space-between;">
                <b>{b_name}</b> <span style="color:{b_clr}">{t_val}% {txt['trust']}</span>
            </div>
            <div style="margin-top:10px;">
                <span class="info-tag">⚖️ {b_info['license']}</span>
                <span class="info-tag">💰 {b_info['fees']}</span>
                <span class="info-tag">⏱️ {b_info['withdraw']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(txt["details"]):
            st.write(f"**{txt['history']}:** {b_info['history'][lang]}")
            st.write(f"**{txt['founder']}:** {b_info['founder']}")
            st.write(f"**{txt['assets']}:** {b_info['assets']}")
            st.write(f"**{txt['fact']}:** {b_info['fact'][lang]}")
            st.markdown(f"**{txt['lawsuits']}:** <span style='color:#ff4b4b;'>{b_info['lawsuits'][lang]}</span>", unsafe_allow_html=True)

st.caption(f"{txt['update']} (ML Core): {datetime.now().strftime('%Y-%m-%d-%H')}")
