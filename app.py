import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. ИНТЕРФЕЙС ---
st.set_page_config(page_title="ABI ANALITIC", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #020508; color: #00ffcc; }
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; height: 110px; }
    .error-card { background: rgba(255, 75, 75, 0.25); border: 1px solid #ff4b4b; padding: 15px; text-align: center; height: 110px; }
    h1, h2, h3, span, label { color: #00ffcc !important; }
    .stDataFrame { border: 1px solid #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ЛОКАЛИЗАЦИЯ ---
UI = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "depo": "КАПИТАЛ", "top": "ТОП 15 АКТИВОВ",
        "select": "ВЫБЕРИ ДЛЯ АНАЛИЗА:", "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ",
        "signal": "СИГНАЛ", "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "day": "ДЕНЬ", "price": "ЦЕНА", "forecast": "ПРОГНОЗ НА 7 ДНЕЙ"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "depo": "CAPITAL", "top": "TOP 15 ASSETS",
        "select": "SELECT FOR ANALYSIS:", "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT",
        "signal": "SIGNAL", "buy": "BUY", "sell": "SELL", "day": "DAY", "price": "PRICE", "forecast": "7-DAY FORECAST"
    }
}

# --- 3. ФИКСИРОВАННАЯ БАЗА (15 ТИКЕРОВ) ---
DB = {
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "ADBE", "CRM", "AVGO", "QCOM", "PYPL"],
    "CHINA": ["BABA", "BIDU", "JD", "PDD", "LI", "NIO", "TCEHY", "BYDDY", "XPEV", "NTES", "MCHI", "KWEB", "FUTU", "BILI", "VIPS"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "TATN.ME", "CHMF.ME", "ALRS.ME", "MTSS.ME", "NLMK.ME", "PLZL.ME", "VTBR.ME"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "DOT-USD", "ADA-USD", "XRP-USD", "LINK-USD", "AVAX-USD", "DOGE-USD", "MATIC-USD", "TRX-USD", "LTC-USD", "SHIB-USD", "BCH-USD", "NEAR-USD"]
}

@st.cache_data(ttl=300)
def get_data(m_name):
    tickers = DB[m_name]
    data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
    rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
    r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "$": 1.0, "₸": float(rates["KZT=X"].iloc[-1])}
    
    res = []
    for t in tickers:
        try:
            df = data[t].dropna()
            returns = df['Close'].pct_change().dropna()
            avg_return = returns.mean()
            std_dev = returns.std() # Волатильность для графика
            last_p = float(df['Close'].iloc[-1])
            conv = r_map["₽"] if ".ME" in t else 1.0
            res.append({"T": t, "P": last_p / conv, "AVG": avg_return, "STD": std_dev, "DF": df})
        except: continue
    return res, r_map

# --- 4. ОСНОВНОЙ ЦИКЛ ---
ln = st.sidebar.radio("LANGUAGE", ["RU", "EN"])
m_sel = st.sidebar.selectbox(UI[ln]["market"], list(DB.keys()))
c_sel = st.sidebar.radio(UI[ln]["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
depo = st.sidebar.number_input(UI[ln]["depo"], value=1000)

assets, rates = get_data(m_sel)
sign = c_sel.split("(")[1][0]
rate = rates.get(sign, 1.0)

st.title("🚀 ABI ANALITIC")

if assets:
    # ТАБЛИЦА ТОП-15 (ФИКС ВЫСОТЫ)
    df_top = pd.DataFrame(assets)
    df_top["PRICE"] = (df_top["P"] * rate).round(2)
    st.subheader(UI[ln]["top"])
    st.dataframe(df_top[["T", "PRICE"]].set_index("T"), use_container_width=True, height=455)

    # ВЫБОР АКТИВА
    target_t = st.selectbox(UI[ln]["select"], df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == target_t)
    
    # ПРОГНОЗ С ВИДИМЫМИ ИЗМЕНЕНИЯМИ
    p_now = item['P'] * rate
    mu = -0.012 if "BTC" in target_t else item['AVG']
    sigma = item['STD'] if item['STD'] > 0 else 0.01
    
    days_idx = range(1, 8)
    # Генерируем "шум", чтобы график был ломаным, а не прямой линией
    prices = []
    current_step_p = p_now
    for i in days_idx:
        change = np.random.normal(mu, sigma) 
        current_step_p *= (1 + change)
        prices.append(current_step_p)
        
    profits = [(p * (depo/p_now)) - depo for p in prices]

    # КАРТОЧКИ
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{UI[ln]['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{UI[ln]['target']}<br><h3>{prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    
    p_final = profits[-1]
    p_style = "error-card" if p_final < 0 else "metric-card"
    c3.markdown(f"<div class='{p_style}'>{UI[ln]['profit']}<br><h3>{p_final:,.2f} {sign}</h3></div>", unsafe_allow_html=True)

    # --- ЖИВОЙ ГРАФИК И ТАБЛИЦА ---
    st.divider()
    st.subheader(UI[ln]["forecast"])
    col_chart, col_table = st.columns([2, 1])
    
    with col_chart:
        # Рисуем график с историей + прогноз
        hist_p = item['DF']['Close'].tail(10).values * rate
        total_p = np.append(hist_p, prices)
        st.line_chart(total_p, color="#00ffcc")

    with col_table:
        days_dates = [(datetime.now() + timedelta(days=i)).strftime('%d.%m') for i in days_idx]
        breakdown = pd.DataFrame({
            UI[ln]["day"]: days_dates,
            UI[ln]["price"]: [f"{p:,.2f}" for p in prices],
            UI[ln]["profit"]: [f"{pr:,.2f}" for pr in profits]
        })
        st.table(breakdown)

    sig = UI[ln]["sell"] if p_final < 0 else UI[ln]["buy"]
    st.markdown(f"<h2 style='text-align:center; color:{'#ff4b4b' if p_final < 0 else '#00ffcc'} !important; border: 2px solid;'>{UI[ln]['signal']}: {sig}</h2>", unsafe_allow_html=True)
