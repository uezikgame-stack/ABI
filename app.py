import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- 1. СТИЛЬ ТЕРМИНАЛА ---
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
        "market": "РЫНОК", "curr": "ВАЛЮТА", "depo": "КАПИТАЛ", "top": "РЕЙТИНГ АКТИВОВ (ТОП 15)",
        "select": "ВЫБЕРИ ДЛЯ АНАЛИЗА:", "now": "ТЕКУЩАЯ", "target": "ЦЕЛЬ (7д)", "profit": "ПРОФИТ",
        "signal": "СИГНАЛ", "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "day": "ДЕНЬ", "price": "ЦЕНА", "forecast": "АНАЛИЗ: ИСТОРИЯ И ПРОГНОЗ"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "depo": "CAPITAL", "top": "ASSET RATING (TOP 15)",
        "select": "SELECT FOR ANALYSIS:", "now": "CURRENT", "target": "TARGET (7d)", "profit": "PROFIT",
        "signal": "SIGNAL", "buy": "BUY", "sell": "SELL", "day": "DAY", "price": "PRICE", "forecast": "ANALYSIS: HISTORY & FORECAST"
    }
}

# --- 3. БАЗА (15 АКТИВОВ) ---
DB = {
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "BAST.KZ", "KMCP.KZ", "KASE.KZ", "KZIP.KZ", "KZMZ.KZ"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "SAN.MC", "ALV.DE", "CS.PA", "BBVA.MC", "OR.PA"],
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
            avg_ret, std_dev = returns.mean(), returns.std()
            last_p = float(df['Close'].iloc[-1])
            conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
            # CH - изменение для сортировки
            ch = (df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1
            res.append({"T": t, "P": last_p / conv, "AVG": avg_ret, "STD": std_dev, "DF": df, "CNV": conv, "CH": ch})
        except: continue
    return res, r_map

# --- 4. ОСНОВНОЙ МОДУЛЬ ---
ln = st.sidebar.radio("LANGUAGE", ["RU", "EN"])
m_sel = st.sidebar.selectbox(UI[ln]["market"], list(DB.keys()))
c_sel = st.sidebar.radio(UI[ln]["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
depo = st.sidebar.number_input(UI[ln]["depo"], value=1000)

assets, rates = get_data(m_sel)
sign = c_sel.split("(")[1][0]
rate = rates.get(sign, 1.0)

st.title("🚀 ABI ANALITIC")

if assets:
    # ТАБЛИЦА С СОРТИРОВКОЙ И ЦИФРАМИ
    df_top = pd.DataFrame(assets)
    df_top = df_top.sort_values(by="CH", ascending=False).reset_index(drop=True)
    df_top.index += 1 # Начинаем с 1
    df_top["PRICE"] = (df_top["P"] * rate).round(2)
    
    st.subheader(UI[ln]["top"])
    st.dataframe(df_top[["T", "PRICE"]], use_container_width=True, height=455)

    # ВЫБОР АКТИВА
    target_t = st.selectbox(UI[ln]["select"], df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == target_t)
    
    p_now = item['P'] * rate
    mu, sigma = item['AVG'], item['STD'] if item['STD'] > 0 else 0.012
    
    # Генерация 7 дней
    future_prices = []
    curr = p_now
    for _ in range(7):
        curr *= (1 + np.random.normal(mu, sigma))
        future_prices.append(curr)
    
    profits = [(p * (depo/p_now)) - depo for p in future_prices]

    # КАРТОЧКИ
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{UI[ln]['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{UI[ln]['target']}<br><h3>{future_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    
    p_final = profits[-1]
    p_style = "error-card" if p_final < 0 else "metric-card"
    c3.markdown(f"<div class='{p_style}'>{UI[ln]['profit']}<br><h3>{p_final:,.2f} {sign}</h3></div>", unsafe_allow_html=True)

    # ГРАФИК
    st.divider()
    st.subheader(UI[ln]["forecast"])
    hist_series = (item['DF']['Close'].tail(14) / item['CNV'] * rate).values
    total_plot = np.append(hist_series, future_prices)
    
    col_chart, col_table = st.columns([2, 1])
    with col_chart:
        st.line_chart(total_plot, color="#00ffcc")
        st.caption("История (14д) + Прогноз (7д)")

    with col_table:
        days_idx = [(datetime.now() + timedelta(days=i)).strftime('%d.%m') for i in range(1, 8)]
        breakdown = pd.DataFrame({
            UI[ln]["day"]: days_idx,
            UI[ln]["price"]: [f"{p:,.2f}" for p in future_prices],
            UI[ln]["profit"]: [f"{pr:,.2f}" for pr in profits]
        })
        st.table(breakdown)

    sig = UI[ln]["sell"] if p_final < 0 else UI[ln]["buy"]
    st.markdown(f"<h2 style='text-align:center; color:{'#ff4b4b' if p_final < 0 else '#00ffcc'} !important; border: 2px solid;'>{UI[ln]['signal']}: {sig}</h2>", unsafe_allow_html=True)
