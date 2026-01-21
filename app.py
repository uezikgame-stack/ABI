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
    .metric-card { background: rgba(0, 0, 0, 0.9); border: 1px solid #00ffcc; padding: 15px; text-align: center; min-height: 110px; }
    .error-card { background: rgba(255, 75, 75, 0.2); border: 1px solid #ff4b4b; padding: 15px; text-align: center; min-height: 110px; }
    h1, h2, h3, span, label, p { color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ВСЕ РЕГИОНЫ ---
DB = {
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "BAST.KZ", "KMCP.KZ", "KASE.KZ", "KZIP.KZ", "KZMZ.KZ"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "SAN.MC", "ALV.DE", "CS.PA", "BBVA.MC", "OR.PA"],
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "ADBE", "CRM", "AVGO", "QCOM", "PYPL"],
    "CHINA": ["BABA", "BIDU", "JD", "PDD", "LI", "NIO", "TCEHY", "BYDDY", "XPEV", "NTES", "9988.HK", "1810.HK", "3690.HK", "0700.HK", "9888.HK"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "ALRS.ME", "AFLT.ME", "MAGN.ME"],
    "CRYPTO": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "DOT-USD", "MATIC-USD", "LTC-USD", "SHIB-USD", "TRX-USD", "AVAX-USD", "UNI-USD", "LINK-USD"]
}

@st.cache_data(ttl=600)
def get_data_safe(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_df = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates_df["RUB=X"].iloc[-1]), "$": 1.0, "₸": float(rates_df["KZT=X"].iloc[-1]), "EUR": float(rates_df["EURUSD=X"].iloc[-1])}
        
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna()
                if df.empty: continue
                if any(x in t for x in [".ME", "YNDX"]): b = "₽"
                elif any(x in t for x in [".KZ", "KCZ"]): b = "₸"
                elif any(x in t for x in [".PA", ".DE", ".MC"]): b = "EUR"
                else: b = "$"
                p_usd = float(df['Close'].iloc[-1]) / r_map[b] if b != "EUR" else float(df['Close'].iloc[-1]) * r_map["EUR"]
                clean.append({"T": t, "P_USD": p_usd, "CH": (df['Close'].iloc[-1]/df['Close'].iloc[0]-1), "AVG": df['Close'].pct_change().mean(), "STD": df['Close'].pct_change().std(), "DF": df})
            except: continue
        return clean, r_map
    except:
        return None, None

# --- 3. НАСТРОЙКИ ---
st.sidebar.title("ABI SETTINGS")
m_sel = st.sidebar.selectbox("MARKET", list(DB.keys()))
c_sel = st.sidebar.radio("CURRENCY", ["USD ($)", "RUB (₽)", "KZT (₸)"])
cap_val = st.sidebar.number_input("CAPITAL", value=1000)

assets, rates = get_data_safe(m_sel)
st.title("🚀 ABI ANALITIC")

# --- ОБРАБОТКА ОШИБОК (РЕГИОН НЕДОСТУПЕН) ---
if assets is None or len(assets) == 0:
    st.markdown("<div class='error-card'><h1>⚠️ РЕГИОН ВРЕМЕННО НЕДОСТУПЕН</h1><p>Попробуйте сменить рынок или валюту</p></div>", unsafe_allow_html=True)
else:
    sign = c_sel.split("(")[1][0]
    r_target = rates[sign]

    # ТОП 15
    df_top = pd.DataFrame(assets)
    df_top["PRICE"] = (df_top["P_USD"] * r_target).round(2)
    df_top = df_top.sort_values(by="CH", ascending=False).head(15).reset_index(drop=True)
    df_top.index += 1
    st.subheader("ТОП 15 АКТИВОВ")
    st.dataframe(df_top[["T", "PRICE"]], use_container_width=True, height=455)

    t_name = st.selectbox("ВЫБЕРИ ДЛЯ АНАЛИЗА:", df_top["T"].tolist())
    item = next(x for x in assets if x['T'] == t_name)

    # Прогноз
    if "f_usd" not in st.session_state or st.session_state.get("last_t") != t_name:
        mu, sigma = item['AVG'], item['STD'] if item['STD'] > 0 else 0.015
        st.session_state.f_usd = [item['P_USD'] * (1 + np.random.normal(mu, sigma)) for _ in range(7)]
        st.session_state.last_t = t_name

    p_now = item['P_USD'] * r_target
    f_prices = [p * r_target for p in st.session_state.f_usd]
    f_profits = [(p - p_now) * (cap_val / p_now) for p in f_prices]

    # КАРТОЧКИ
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ (7д)<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    p_fin = f_profits[-1]
    style = "error-card" if p_fin < 0 else "metric-card"
    c3.markdown(f"<div class='{style}'>ПРОФИТ ({sign})<br><h3>{p_fin:,.2f} {sign}</h3></div>", unsafe_allow_html=True)

    # ГРАФИК И ТАБЛИЦА (СКРЫТ ИНДЕКС 0-6)
    st.divider()
    col_g, col_t = st.columns([2, 1])
    with col_g:
        hist = (item['DF']['Close'].tail(14).values / (item['P_USD'] / p_now))
        st.line_chart(np.append(hist, f_prices), color="#00ffcc")

    with col_t:
        table_df = pd.DataFrame({
            "ДЕНЬ": [f"День {i+1}" for i in range(7)],
            "ЦЕНА": [f"{p:,.2f} {sign}" for p in f_prices],
            "ПРОФИТ": [f"{pr:,.2f} {sign}" for pr in f_profits]
        })
        st.dataframe(table_df, hide_index=True, use_container_width=True)

    sig = "ПРОДАВАТЬ" if p_fin < 0 else "ПОКУПАТЬ"
    st.markdown(f"<h2 style='text-align:center; color:{'#ff4b4b' if p_fin < 0 else '#00ffcc'} !important; border: 2px solid;'>СИГНАЛ: {sig}</h2>", unsafe_allow_html=True)
