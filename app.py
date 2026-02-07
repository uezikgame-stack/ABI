import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

# --- 1. СТИЛЬ И БРЕНДИНГ RILLET ---
st.set_page_config(page_title="Rillet", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background-color: #020508 !important;
        background-image: 
            linear-gradient(rgba(0, 255, 204, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 204, 0.1) 1px, transparent 1px);
        background-size: 60px 60px;
        animation: moveGrid 20s linear infinite;
        color: #00ffcc;
    }
    @keyframes moveGrid { from { background-position: 0 0; } to { background-position: 60px 60px; } }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; border-radius: 10px; }
    h1, h2, h3, p, span, label { color: #00ffcc !important; }
    
    .logo-text {
        font-size: 42px;
        font-weight: bold;
        text-align: center;
        color: #00ffcc;
        border-bottom: 2px solid #00ffcc;
        margin-bottom: 20px;
    }
    .news-card {
        background: rgba(0, 255, 204, 0.05);
        border-left: 5px solid #00ffcc;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .loss-tracker {
        background: rgba(255, 75, 75, 0.1);
        border: 1px solid #ff4b4b;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ ---
DB = {
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "CRM", "AVGO", "QCOM", "PYPL", "TSM"],
    "CHINA (Китай)": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES", "GDS", "ZLAB", "KC", "IQ", "TME"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "ALV.DE", "SAN.MC", "BMW.DE", "OR.PA", "BBVA.MC"],
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "KSPI.KZ", "KCP.KZ", "KMGP.KZ", "BCKL.KZ", "KASE.KZ"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "AFLT.ME", "ALRS.ME", "VTBR.ME"]
}

LANG = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "top": "🔥 ТОП АКТИВОВ", "price": "ЦЕНА", "pred": "ПРОГНОЗ %",
        "sel": "ВЫБЕРИ ДЛЯ АНАЛИЗА:", "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ (%)",
        "chart": "ГРАФИК ПРОГНОЗА", "days": "РАЗБОР ПО ДНЯМ", "day_label": "День", "signal": "СИГНАЛ",
        "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "hold": "УДЕРЖИВАТЬ",
        "err": "РЕГИОН ВРЕМЕННО НЕДОСТУПЕН", "tab_an": "Аналитика", "tab_news": "Новости рынка",
        "loss_title": "УБЫТКИ ИНВЕСТОРОВ В МИРЕ", "loss_sub": "с момента открытия Rillet"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "top": "🔥 TOP ASSETS", "price": "PRICE", "pred": "FORECAST %",
        "sel": "SELECT FOR ANALYSIS:", "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT (%)",
        "chart": "FORECAST CHART", "days": "DAILY BREAKDOWN", "day_label": "Day", "signal": "SIGNAL",
        "buy": "BUY", "sell": "SELL", "hold": "HOLD",
        "err": "REGION UNAVAILABLE", "tab_an": "Analytics", "tab_news": "Market News",
        "loss_title": "GLOBAL INVESTOR LOSSES", "loss_sub": "since you opened Rillet"
    }
}

@st.cache_data(ttl=300)
def fetch_all(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_raw = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="5d", progress=False)['Close']
        r_map = {"$": 1.0, "₽": 90.0, "₸": 485.0}
        try:
            r_map["₽"] = float(rates_raw["RUB=X"].dropna().iloc[-1])
            r_map["₸"] = float(rates_raw["KZT=X"].dropna().iloc[-1])
        except: pass
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna()
                if df.empty: continue
                mu = df['Close'].pct_change().mean() or 0.0
                p_now = float(df['Close'].iloc[-1])
                clean.append({"T": t, "P": p_now, "F": p_now * (1 + mu * 7), "AVG": mu, "STD": df['Close'].pct_change().std() or 0.02, "DF": df})
            except: continue
        return clean, r_map
    except: return [], {"$": 1.0, "₽": 90.0, "₸": 485.0}

def get_news(ticker):
    try:
        return yf.Ticker(ticker).news[:5]
    except: return []

# --- 3. ИНТЕРФЕЙС ---
st.sidebar.markdown('<div class="logo-text">RILLET</div>', unsafe_allow_html=True)
l_code = st.sidebar.radio("LANGUAGE", ["RU", "EN"])
T = LANG[l_code]

if "start_time" not in st.session_state: st.session_state.start_time = time.time()
current_loss = (time.time() - st.session_state.start_time) * 5390
st.sidebar.markdown(f'<div class="loss-tracker"><small>{T["loss_title"]}</small><h2 style="color:#ff4b4b; margin:0;">${current_loss:,.0f}</h2><small>{T["loss_sub"]}</small></div>', unsafe_allow_html=True)

m_name = st.sidebar.selectbox(T["market"], list(DB.keys()))
assets, rates = fetch_all(m_name)

st.title("🚀 RILLET")
t1, t2 = st.tabs([T["tab_an"], T["tab_news"]])

with t1:
    if assets:
        df_main = pd.DataFrame(assets)
        df_main["PROFIT_EST"] = ((df_main["F"] / df_main["P"]) - 1) * 100
        df_main = df_main.sort_values("PROFIT_EST", ascending=False)
        st.dataframe(df_main[["T", "P", "PROFIT_EST"]], use_container_width=True)
        
        st.divider()
        t_sel = st.selectbox(T["sel"], df_main["T"].tolist())
        item = next(x for x in assets if x['T'] == t_sel)
        
        # Прогноз и метрики (упрощенно для стабильности)
        p_now = item['P']
        pct = ((item['F'] / p_now) - 1) * 100
        c1, c2, c3 = st.columns(3)
        c1.metric(T["now"], f"{p_now:,.2f}")
        c2.metric(T["target"], f"{item['F']:,.2f}")
        c3.metric(T["profit"], f"{pct:+.2f}%")
        
        st.line_chart(item['DF']['Close'].tail(20))
        res = "buy" if pct > 0.5 else ("sell" if pct < -0.5 else "hold")
        st.subheader(f"{T['signal']}: {T[res]}")
    else:
        st.error(T["err"])

with t2:
    st.write(f"### 📰 {T['tab_news']}")
    ticker_for_news = t_sel if 't_sel' in locals() else "AAPL"
    news = get_news(ticker_for_news)
    if news:
        for n in news:
            # ВОТ ЗДЕСЬ ИСПРАВЛЕНИЕ ОШИБКИ С ТВОИХ СКРИНШОТОВ:
            title = n.get('title', 'No Title')
            link = n.get('link', '#')
            publisher = n.get('publisher', 'News Source')
            st.markdown(f'<div class="news-card"><h4><a href="{link}" target="_blank" style="color:#00ffcc; text-decoration:none;">{title}</a></h4><p style="color:#888;">{publisher}</p></div>', unsafe_allow_html=True)
    else:
        st.info("No news found.")
