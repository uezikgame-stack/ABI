import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. ИНТЕРФЕЙС ТЕРМИНАЛА ---
st.set_page_config(page_title="ABI ANALITIC", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #020508; color: #00ffcc; }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; height: 110px; }
    .error-card { background: rgba(255, 75, 75, 0.25); border: 1px solid #ff4b4b; padding: 15px; text-align: center; height: 110px; }
    h1, h2, h3, span, label, p { color: #00ffcc !important; }
    .stDataFrame, .stTable { border: 1px solid #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА И ЛОКАЛИЗАЦИЯ ---
UI = {
    "RU": {"market": "РЫНОК", "curr": "ВАЛЮТА", "depo": "КАПИТАЛ", "top": "РЕЙТИНГ АКТИВОВ", "select": "ВЫБЕРИ ДЛЯ АНАЛИЗА:", "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ", "signal": "СИГНАЛ", "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "day": "ДЕНЬ", "price": "ЦЕНА", "forecast": "АНАЛИЗ: ИСТОРИЯ И ПРОГНОЗ"},
    "EN": {"market": "MARKET", "curr": "CURRENCY", "depo": "CAPITAL", "top": "ASSET RATING", "select": "SELECT FOR ANALYSIS:", "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT", "signal": "SIGNAL", "buy": "BUY", "sell": "SELL", "day": "DAY", "price": "PRICE", "forecast": "ANALYSIS: HISTORY & FORECAST"}
}

DB = {
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "BAST.KZ", "KMCP.KZ", "KASE.KZ", "KZIP.KZ", "KZMZ.KZ"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "SAN.MC", "ALV.DE", "CS.PA", "BBVA.MC", "OR.PA"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "ADBE", "CRM", "AVGO", "QCOM", "PYPL"]
}

@st.cache_data(ttl=600)
def get_market_data(m_name):
    tickers = DB[m_name]
    data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
    rates_df = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="1d", progress=False)['Close']
    r_map = {"₽": float(rates_df["RUB=X"].iloc[-1]), "$": 1.0, "₸": float(rates_df["KZT=X"].iloc[-1]), "EUR": float(rates_df["EURUSD=X"].iloc[-1])}
    
    clean = []
    for t in tickers:
        try:
            df = data[t].dropna()
            if df.empty: continue
            # Определение базовой валюты
            if ".ME" in t: b = "₽"
            elif ".KZ" in t or "KCZ" in t: b = "₸"
            elif any(x in t for x in [".PA", ".DE", ".MC"]): b = "EUR"
            else: b = "$"
            # Приведение к USD
            p_usd = float(df['Close'].iloc[-1]) / r_map[b] if b != "EUR" else float(df['Close'].iloc[-1]) * r_map["EUR"]
            ret = df['Close'].pct_change().dropna()
            clean.append({"T": t, "P_USD": p_usd, "CH": (df['Close'].iloc[-1]/df['Close'].iloc[0]-1), "AVG": ret.mean(), "STD": ret.std(), "DF": df})
        except: continue
    return clean, r_map

# --- 3. ГЕНЕРАЦИЯ ПРОГНОЗА ---
def get_forecast(item):
    mu, sigma = item['AVG'], item['STD'] if item['STD'] > 0 else 0.015
    f_usd = []
    curr = item['P_USD']
    for _ in range(7): # Строго 7 дней
        curr *= (1 + np.random.normal(mu, sigma))
        f_usd.append(curr)
    return f_usd

# --- 4. ОСНОВНОЙ ЦИКЛ ---
ln = st.sidebar.radio("LANGUAGE", ["RU", "EN"])
m_sel = st.sidebar.selectbox(UI[ln]["market"], list(DB.keys()))
c_sel = st.sidebar.radio(UI[ln]["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
depo = st.sidebar.number_input(UI[ln]["depo"], value=1000)

assets, rates = get_market_data(m_sel)
sign = c_sel.split("(")[1][0]
r_target = rates[sign]

st.title("🚀 ABI ANALITIC")

if assets:
    # Таблица ТОП-15
    df_top = pd.DataFrame(assets)
    df_top["PRICE"] = (df_top["P_USD"] * r_target).round(2)
    df_top = df_top.sort_values(by="CH", ascending=False).reset_index(drop=True)
    df_top.index += 1
    st.subheader(UI[ln]["top"])
    st.dataframe(df_top[["T", "PRICE"]], use_container_width=True, height=400)

    # Выбор акции и стабильный прогноз
    t_name = st.selectbox(UI[ln]["select"], df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == t_name)

    if "last_t" not in st.session_state or st.session_state.last_t != t_name:
        st.session_state.f_usd = get_forecast(item)
        st.session_state.last_t = t_name

    # Пересчет под текущую валюту
    p_now = item['P_USD'] * r_target
    f_prices = [p * r_target for p in st.session_state.f_usd]
    # ФОРМУЛА: (Будущая_цена - Текущая) * (Депозит / Текущая)
    f_profits = [(p - p_now) * (depo / p_now) for p in f_prices]

    # Метрики
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{UI[ln]['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{UI[ln]['target']}<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    p_final = f_profits[-1]
    style = "error-card" if p_final < 0 else "metric-card"
    c3.markdown(f"<div class='{style}'>{UI[ln]['profit']}<br><h3>{p_final:,.2f} {sign}</h3></div>", unsafe_allow_html=True)

    # График и Таблица на 7 дней
    st.divider()
    col_g, col_t = st.columns([2, 1])
    with col_g:
        st.subheader(UI[ln]["forecast"])
        hist = (item['DF']['Close'].tail(14).values / (item['P_USD'] / p_now))
        st.line_chart(np.append(hist, f_prices), color="#00ffcc")

    with col_t:
        days = [(datetime.now() + timedelta(days=i)).strftime('%d.%m') for i in range(1, 8)]
        table_data = pd.DataFrame({
            UI[ln]["day"]: days,
            UI[ln]["price"]: [f"{p:,.2f}" for p in f_prices],
            UI[ln]["profit"]: [f"{pr:,.2f} {sign}" for pr in f_profits]
        })
        st.table(table_data)

    sig = UI[ln]["sell"] if p_final < 0 else UI[ln]["buy"]
    st.markdown(f"<h2 style='text-align:center; color:{'#ff4b4b' if p_final < 0 else '#00ffcc'} !important; border: 2px solid;'>{UI[ln]['signal']}: {sig}</h2>", unsafe_allow_html=True)
