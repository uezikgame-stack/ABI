import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime
import xgboost as xgb

# --- 1. СТИЛЬ И БРЕНДИНГ ---
st.set_page_config(page_title="Rillet ML Full", layout="wide")

lang = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["RU", "EN"])
txt = {
    "RU": {
        "market": "РЫНОК", "currency": "ВАЛЮТА", "select": "ВЫБЕРИ АКТИВ:", 
        "current": "ТЕКУЩАЯ ЦЕНА", "target": "ЦЕЛЬ (7д ML)", "profit": "ПРОФИТ (%)",
        "chart": "ПРОГНОЗ XGBOOST", "news": "АНАЛИЗ НОВОСТЕЙ", "signal": "ИТОГОВЫЙ СИГНАЛ",
        "buy": "✅ ПОКУПАТЬ", "sell": "❌ ПРОДАВАТЬ", "hold": "⚖️ УДЕРЖИВАТЬ",
        "brokers": "ТОП 15 БРОКЕРОВ", "trust": "ДОВЕРИЕ", "details": "ДЕТАЛИ",
        "history": "История", "founder": "Основатель", "lawsuits": "Иски", "fact": "Факт"
    },
    "EN": {
        "market": "MARKET", "currency": "CURRENCY", "select": "SELECT ASSET:", 
        "current": "CURRENT PRICE", "target": "TARGET (7d ML)", "profit": "EST. PROFIT",
        "chart": "XGBOOST FORECAST", "news": "NEWS ANALYSIS", "signal": "FINAL SIGNAL",
        "buy": "✅ STRONG BUY", "sell": "❌ SELL", "hold": "⚖️ NEUTRAL",
        "brokers": "TOP 15 BROKERS", "trust": "TRUST", "details": "DETAILS",
        "history": "History", "founder": "Founder", "lawsuits": "Lawsuits", "fact": "Fact"
    }
}[lang]

st.markdown("""
    <style>
    .stApp { background-color: #020508 !important; color: #00ffcc; }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    .analysis-card { background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; padding: 15px; margin-bottom: 10px; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #00ffcc !important; }
    .logo-text { font-size: 42px; font-weight: bold; text-align: center; color: #00ffcc; border-bottom: 2px solid #00ffcc; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ АКТИВОВ И БРОКЕРОВ ---
DB = {
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL"],
    "KAZAKHSTAN": ["KMGZ.KZ", "HSBK.KZ", "KSPI.KZ", "KASE.KZ", "KCZ.L"],
    "EUROPE": ["ASML", "MC.PA", "SAP.DE", "AIR.PA", "BMW.DE"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME"]
}

BROKERS = {
    "Interactive Brokers": {"trust": 99.2, "lic": "SEC, FCA, ASIC", "fees": "$0.005/sh", "founder": "Thomas Peterffy", "history": "Est. 1978, NYC.", "lawsuits": "Fined $38M (2020) for AML gaps.", "fact": "Father of digital trading."},
    "Fidelity": {"trust": 98.5, "lic": "SEC, FINRA", "fees": "$0", "founder": "Edward Johnson", "history": "Private giant since 1946.", "lawsuits": "Class action over 401k (2023).", "fact": "Best for long-term investors."},
    "Saxo Bank": {"trust": 96.0, "lic": "Danish FSA", "fees": "0.1%+", "founder": "Kim Fournais", "history": "Danish investment bank.", "lawsuits": "Fined in 2021 by FSA.", "fact": "First online platform in 1992."},
    "Freedom Finance": {"trust": 94.5, "lic": "SEC, CySEC, AFSA", "fees": "0.02%", "founder": "Timur Turlov", "history": "NASDAQ listed holding.", "lawsuits": "Hindenburg report audit cleared.", "fact": "Leader in Central Asia."},
    "Charles Schwab": {"trust": 98.0, "lic": "SEC, FINRA", "fees": "$0", "founder": "Charles Schwab", "history": "Pioneer of discount brokerage.", "lawsuits": "Settled over robo-advisors.", "fact": "Acquired TD Ameritrade."},
    "Vantage": {"trust": 93.8, "lic": "ASIC, FCA", "fees": "Low", "founder": "Group", "history": "Founded in 2009.", "lawsuits": "No major recent issues.", "fact": "Multi-award winning ECN."},
    "Exante": {"trust": 91.2, "lic": "CySEC, SFC", "fees": "0.02%", "founder": "Alexey Kirienko", "history": "Founded in Malta, 2011.", "lawsuits": "SEC insider case (dismissed).", "fact": "Strong for hedge funds."},
    "Swissquote": {"trust": 95.5, "lic": "FINMA", "fees": "Med-High", "founder": "Marc Bürki", "history": "Swiss online bank.", "lawsuits": "None major.", "fact": "Safest banking standards."},
    "Webull": {"trust": 90.0, "lic": "SEC, FINRA", "fees": "$0", "founder": "Wang Anquan", "history": "Owned by Fumi Technology.", "lawsuits": "Payment for order flow audit.", "fact": "Best charting UI for mobile."},
    "Pepperstone": {"trust": 92.5, "lic": "FCA, ASIC", "fees": "Spreads", "founder": "Owen Kerr", "history": "Australian FX broker.", "lawsuits": "Regulatory warning (2020).", "fact": "Fastest execution speeds."},
    "Tiger Brokers": {"trust": 89.5, "lic": "ASIC, MAS", "fees": "Low", "founder": "Wu Tianhua", "history": "Backed by Xiaomi & Jim Rogers.", "lawsuits": "Compliance audit in China.", "fact": "Leading Asia-Pacific broker."},
    "Robinhood": {"trust": 88.0, "lic": "SEC, FINRA", "fees": "$0", "founder": "Vlad Tenev", "history": "Started zero-fee revolution.", "lawsuits": "GameStop saga fines.", "fact": "Gamified investing for Gen Z."},
    "E*TRADE": {"trust": 93.0, "lic": "SEC", "fees": "$0", "founder": "William Porter", "history": "Owned by Morgan Stanley.", "lawsuits": "Technical outages settlements.", "fact": "Pioneer of online stocks."},
    "AvaTrade": {"trust": 87.5, "lic": "CBI, ASIC", "fees": "Spreads", "founder": "Emanuel Many", "history": "Founded in 2006.", "lawsuits": "Regulatory fine in Italy.", "fact": "Specializes in CFDs/Options."},
    "BlackRock (Aladdin)": {"trust": 99.8, "lic": "Global", "fees": "Inst.", "founder": "Larry Fink", "history": "World's largest asset manager.", "lawsuits": "ESG-related legal battles.", "fact": "Manages $10 trillion."}
}

# --- 3. МАШИННОЕ ОБУЧЕНИЕ И АНАЛИЗ ---
def run_ml_xgboost(df):
    try:
        d = df[['Close']].copy()
        d['lag'] = d['Close'].shift(1); d['ma5'] = d['Close'].rolling(5).mean()
        d = d.dropna()
        model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05)
        model.fit(d[['lag', 'ma5']], d['Close'])
        # Предсказание на 7 дней
        preds = []
        last_p, last_m = d['Close'].iloc[-1], d['ma5'].iloc[-1]
        for _ in range(7):
            p = model.predict(np.array([[last_p, last_m]]))[0]
            preds.append(p); last_p = p
        return preds
    except: return None

def get_news_sentiment(ticker, l):
    try:
        gn = GNews(language='ru' if l == "RU" else 'en', max_results=4)
        news = gn.get_news(f"{ticker} stock")
        if not news: return txt["hold"], []
        pos = sum(1 for n in news if any(w in n['title'].lower() for w in ['up', 'buy', 'growth', 'рост', 'покупка']))
        neg = sum(1 for n in news if any(w in n['title'].lower() for w in ['down', 'sell', 'loss', 'падение', 'убыток']))
        sig = txt["buy"] if pos > neg else (txt["sell"] if neg > pos else txt["hold"])
        return sig, news
    except: return txt["hold"], []

@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        r = yf.download(["RUB=X", "KZT=X"], period="5d", progress=False)['Close']
        return {"$": 1.0, "₽": float(r["RUB=X"].iloc[-1]), "₸": float(r["KZT=X"].iloc[-1])}
    except: return {"$": 1.0, "₽": 92.0, "₸": 450.0}

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.markdown('<div class="logo-text">RILLET ML</div>', unsafe_allow_html=True)
mode = st.sidebar.selectbox("MENU", [txt["market"], txt["brokers"]])

if mode == txt["market"]:
    market = st.sidebar.selectbox(txt["market"], list(DB.keys()))
    curr_choice = st.sidebar.radio(txt["currency"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
    sign = curr_choice.split("(")[1][0]
    rates = get_exchange_rates()
    conv = rates.get(sign, 1.0)
    
    t_sel = st.selectbox(txt["select"], DB[market])
    
    # Решение проблемы "Data Unavailable"
    df_raw = yf.download(t_sel, period="1y", interval="1d", progress=False, auto_adjust=True)
    
    if not df_raw.empty:
        if isinstance(df_raw.columns, pd.MultiIndex): df_raw.columns = df_raw.columns.get_level_values(0)
        df = df_raw[['Close']].dropna()
        
        with st.spinner('Neural Training...'):
            forecast = run_ml_xgboost(df)
            sentiment, news_items = get_news_sentiment(t_sel, lang)
            
        if forecast:
            p_now = float(df['Close'].iloc[-1]) * conv
            p_fut = float(forecast[-1]) * conv
            pct = ((p_fut / p_now) - 1) * 100
            
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{p_fut:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
            clr = "#00ffcc" if pct > 0 else "#ff4b4b"
            c3.markdown(f"<div class='metric-card' style='border-color:{clr}'>{txt['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)
            
            st.write(f"#### {txt['chart']} {t_sel}")
            st.line_chart(np.append(df['Close'].tail(30).values * conv, np.array(forecast) * conv))
            
            # НОВОСТИ И СИГНАЛ
            st.write(f"### 📰 {txt['news']} & {txt['signal']}")
            st.markdown(f"<div class='analysis-card'><b>{txt['signal']}: {sentiment}</b></div>", unsafe_allow_html=True)
            for n in news_items:
                st.markdown(f"<div class='analysis-card'><small>{n['published date']}</small><br>{n['title']}</div>", unsafe_allow_html=True)
    else:
        st.error("Data Unavailable")

elif mode == txt["brokers"]:
    st.write(f"## 🏛️ {txt['brokers']}")
    for name, info in BROKERS.items():
        st.markdown(f"""
        <div class="analysis-card">
            <div style="display:flex; justify-content:space-between;">
                <b>{name}</b> <span style="color:#00ffcc">{info['trust']}% {txt['trust']}</span>
            </div>
            <div style="margin-top:5px; font-size:0.85em;">
                ⚖️ {info['lic']} | 💰 {info['fees']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(txt["details"]):
            col1, col2 = st.columns(2)
            col1.write(f"**{txt['founder']}:** {info['founder']}")
            col1.write(f"**{txt['history']}:** {info['history']}")
            col2.write(f"**{txt['fact']}:** {info['fact']}")
            col2.markdown(f"**{txt['lawsuits']}:** <span style='color:#ff4b4b;'>{info['lawsuits']}</span>", unsafe_allow_html=True)

st.caption(f"{txt['update']} (ML Full): {datetime.now().strftime('%Y-%m-%d-%H')}")
