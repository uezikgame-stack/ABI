import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from gnews import GNews
from datetime import datetime
import xgboost as xgb

# --- 1. КОНФИГУРАЦИЯ И СТИЛЬ ---
st.set_page_config(page_title="Rillet ML", layout="wide")

lang = st.sidebar.radio("LANGUAGE / ЯЗЫК", ["EN", "RU"])
txt = {
    "EN": {
        "market": "MARKET", "currency": "CURRENCY", "price": "PRICE", "forecast": "FORECAST %",
        "select": "SELECT ASSET:", "current": "CURRENT PRICE", "target": "TARGET (7d ML)",
        "profit": "EST. PROFIT", "chart_title": "XGBOOST ML FORECAST", "news_title": "NEWS ANALYSIS",
        "buy": "✅ STRONG BUY", "sell": "❌ SELL / HOLD", "hold": "⚖️ NEUTRAL", "no_news": "No news found.",
        "update": "Data updated", "signal": "FINAL SIGNAL",
        "brokers": "TOP BROKERS", "trust": "TRUST LEVEL", "details": "DETAILS",
        "history": "History", "founder": "Founder", "fact": "Fun Fact", "lawsuits": "Major Lawsuits",
        "license": "License", "fees": "Commissions", "withdraw": "Withdrawal", "assets": "Available Assets"
    },
    "RU": {
        "market": "РЫНОК", "currency": "ВАЛЮТА", "price": "ЦЕНА", "forecast": "ПРОГНОЗ %",
        "select": "ВЫБЕРИ АКТИВ:", "current": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д ML)",
        "profit": "ПРОФИТ (%)", "chart_title": "ПРОГНОЗ ML (XGBOOST)", "news_title": "АНАЛИЗ НОВОСТЕЙ",
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

# --- 2. БАЗА ДАННЫХ (БРОКЕРЫ + АКТИВЫ) ---
DB = {
    "CHINA": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL"],
    "KAZAKHSTAN": ["KMGZ.KZ", "HSBK.KZ", "KSPI.KZ", "KASE.KZ"],
    "EUROPE": ["ASML", "MC.PA", "SAP.DE", "AIR.PA", "BMW.DE"],
    "RUSSIA": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME"]
}

# Здесь представлен ТОП (сокращено для кода, но логика на 15+)
raw_brokers = {
    "Interactive Brokers": {"trust": 99.2, "license": "SEC, FINRA, FCA", "fees": "0.005$/sh", "withdraw": "1-3d", "founder": "Thomas Peterffy", "assets": "Global", "history": "Started in 1978.", "fact": "Father of digital trading.", "lawsuits": "Fined $38M in 2020."},
    "Freedom Finance": {"trust": 94.5, "license": "SEC, CySEC, AFSA", "fees": "0.02%", "withdraw": "Instant", "founder": "Timur Turlov", "assets": "IPO, US Stocks", "history": "NASDAQ listed.", "fact": "Leader in Central Asia.", "lawsuits": "None major."},
    "Saxo Bank": {"trust": 96.0, "license": "FSA, FINMA", "fees": "0.1%", "withdraw": "2-5d", "founder": "Kim Fournais", "assets": "FX, Stocks", "history": "Danish bank.", "fact": "First online platform.", "lawsuits": "Reg. fines 2021."},
    "Exante": {"trust": 91.2, "license": "SFC, CySEC", "fees": "0.02%", "withdraw": "1-5d", "founder": "Alexey Kirienko", "assets": "Multi-asset", "history": "Founded in 2011.", "fact": "Focus on DMA.", "lawsuits": "SEC case (dropped)."},
    "Tiger Brokers": {"trust": 89.5, "license": "ASIC, MAS", "fees": "0.01%", "withdraw": "2-3d", "founder": "Wu Tianhua", "assets": "China & US", "history": "Backed by Xiaomi.", "fact": "Fastest growing in Asia.", "lawsuits": "Regulatory warning 2022."},
    # ... добавьте остальных до 15 по аналогии
}

# --- 3. ФУНКЦИИ (ML + НОВОСТИ) ---
def get_ml_forecast(df):
    try:
        d = df[['Close']].copy()
        d['ma'] = d['Close'].rolling(5).mean(); d['lag'] = d['Close'].shift(1)
        d = d.dropna()
        model = xgb.XGBRegressor(n_estimators=100); model.fit(d[['lag', 'ma']], d['Close'])
        preds = []
        last_p, last_m = d['Close'].iloc[-1], d['ma'].iloc[-1]
        for _ in range(7):
            p = model.predict(np.array([[last_p, last_m]]))[0]
            preds.append(p); last_p = p
        return preds
    except: return None

def fetch_news(t, l):
    try:
        gn = GNews(language='ru' if l == "RU" else 'en', max_results=3)
        news = gn.get_news(f"{t} stock")
        return news if news else []
    except: return []

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.markdown('<div class="logo-text">RILLET ML</div>', unsafe_allow_html=True)
mode = st.sidebar.selectbox("MENU", [txt["market"], txt["brokers"]])

if mode == txt["market"]:
    m_name = st.sidebar.selectbox(txt["market"], list(DB.keys()))
    t_sel = st.selectbox(txt["select"], DB[m_name])
    
    df_raw = yf.download(t_sel, period="1y", interval="1d", progress=False, auto_adjust=True)
    if not df_raw.empty:
        if isinstance(df_raw.columns, pd.MultiIndex): df_raw.columns = df_raw.columns.get_level_values(0)
        df = df_raw[['Close']].dropna()
        
        forecast = get_ml_forecast(df)
        if forecast:
            p_now = df['Close'].iloc[-1]; p_fut = forecast[-1]; pct = ((p_fut/p_now)-1)*100
            
            # Карточки
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='metric-card'>{txt['current']}<br><h3>{p_now:,.2f} $</h3></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='metric-card'>{txt['target']}<br><h3>{p_fut:,.2f} $</h3></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='metric-card' style='border-color:{'#00ffcc' if pct>0 else '#ff4b4b'}'>{txt['profit']}<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)
            
            st.write(f"#### {txt['chart_title']} {t_sel}")
            st.line_chart(np.append(df['Close'].tail(30).values, forecast))
            
            # --- БЛОК НОВОСТЕЙ ---
            st.write(f"#### 📰 {txt['news_title']}")
            news_items = fetch_news(t_sel, lang)
            if news_items:
                for n in news_items:
                    st.markdown(f"<div class='analysis-card'><b>{n['title']}</b><br><small>{n['published date']}</small></div>", unsafe_allow_html=True)
            else: st.write(txt["no_news"])

elif mode == txt["brokers"]:
    st.write(f"## 🏛️ {txt['brokers']}")
    for b_name, b_info in raw_brokers.items():
        st.markdown(f"""
        <div class="analysis-card">
            <div style="display:flex; justify-content:space-between;">
                <b>{b_name}</b> <span style="color:#00ffcc">{b_info['trust']}% {txt['trust']}</span>
            </div>
            <div style="margin-top:10px;">
                <span class="info-tag">⚖️ {b_info['license']}</span>
                <span class="info-tag">💰 {b_info['fees']}</span>
                <span class="info-tag">⏱️ {b_info['withdraw']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(txt["details"]):
            st.write(f"**{txt['founder']}:** {b_info['founder']}")
            st.write(f"**{txt['history']}:** {b_info['history']}")
            st.write(f"**{txt['lawsuits']}:** {b_info['lawsuits']}")

st.caption(f"{txt['update']} (ML Core): {datetime.now().strftime('%Y-%m-%d-%H')}")
