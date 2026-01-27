import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

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
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА ДАННЫХ (ПО 15 АКТИВОВ) ---
DB = {
    "USA": ["AAPL", "NVDA", "TSLA", "MSFT", "AMZN", "AMD", "NFLX", "GOOGL", "META", "INTC", "CRM", "AVGO", "QCOM", "PYPL", "TSM"],
    "CHINA (Китай)": ["BABA", "TCEHY", "PDD", "JD", "BIDU", "NIO", "LI", "BYDDY", "BILI", "NTES", "GDS", "ZLAB", "KC", "IQ", "TME"],
    "EUROPE": ["ASML", "MC.PA", "VOW3.DE", "NESN.SW", "SIE.DE", "SAP.DE", "AIR.PA", "RMS.PA", "MBG.DE", "DHL.DE", "ALV.DE", "SAN.MC", "BMW.DE", "OR.PA", "BBVA.MC"],
    "KAZ (Казахстан)": ["KCZ.L", "KMGZ.KZ", "HSBK.KZ", "KCELL.KZ", "NAC.KZ", "CCBN.KZ", "KEGC.KZ", "KZTK.KZ", "KZTO.KZ", "ASBN.KZ", "KSPI.KZ", "KCP.KZ", "KMGP.KZ", "BCKL.KZ", "KASE.KZ"],
    "RF (Россия)": ["SBER.ME", "GAZP.ME", "LKOH.ME", "YNDX", "ROSN.ME", "MGNT.ME", "NVTK.ME", "GMKN.ME", "CHMF.ME", "PLZL.ME", "TATN.ME", "MTSS.ME", "AFLT.ME", "ALRS.ME", "VTBR.ME"]
}

@st.cache_data(ttl=300)
def fetch_all(m_name):
    try:
        tickers = DB[m_name]
        data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
        rates_raw = yf.download(["RUB=X", "KZT=X", "EURUSD=X"], period="5d", progress=False)['Close']
        r_map = {"$": 1.0}
        r_map["₽"] = float(rates_raw["RUB=X"].dropna().iloc[-1]) if not rates_raw["RUB=X"].dropna().empty else 90.0
        r_map["₸"] = float(rates_raw["KZT=X"].dropna().iloc[-1]) if not rates_raw["KZT=X"].dropna().empty else 485.0
        eur_usd = float(rates_raw["EURUSD=X"].dropna().iloc[-1]) if not rates_raw["EURUSD=X"].dropna().empty else 1.08
        
        clean = []
        for t in tickers:
            try:
                df = data[t].dropna()
                if df.empty: continue
                base = "₽" if ".ME" in t or t == "YNDX" else ("₸" if ".KZ" in t or "KCZ" in t else ("€" if any(x in t for x in [".PA", ".DE", ".MC", ".SW"]) else "$"))
                p_now_usd = (float(df['Close'].iloc[-1]) * eur_usd) if base == "€" else (float(df['Close'].iloc[-1]) / r_map.get(base, 1.0))
                mu = df['Close'].pct_change().mean() or 0.0
                clean.append({"T": t, "P_USD": p_now_usd, "AVG": mu, "STD": df['Close'].pct_change().std() or 0.02, "DF": df})
            except: continue
        return clean, r_map
    except: return [], {"$": 1.0, "₽": 90.0, "₸": 485.0}

# --- 3. ИНТЕРФЕЙС RILLET ---
st.sidebar.markdown('<div class="logo-text">RILLET</div>', unsafe_allow_html=True)
st.sidebar.title("SETTINGS")
l_code = st.sidebar.radio("ЯЗЫК", ["RU", "EN"])
m_name = st.sidebar.selectbox("РЫНОК", list(DB.keys()))
c_name = st.sidebar.radio("ВАЛЮТА", ["USD ($)", "RUB (₽)", "KZT (₸)"])

assets, rates = fetch_all(m_name)
sign = c_name.split("(")[1][0]
r_val = rates.get(sign, 1.0)

st.title("🚀 RILLET")

if assets:
    t_names = [x['T'] for x in assets]
    t_sel = st.selectbox("ВЫБЕРИ АКТИВ:", t_names)
    item = next(x for x in assets if x['T'] == t_sel)

    # Синхронизация данных
    p_now = item['P_USD'] * r_val
    if "cache_t" not in st.session_state or st.session_state.cache_t != t_sel:
        gen_pts = []
        last_p = item['P_USD']
        for _ in range(7):
            last_p = last_p * (1 + np.random.normal(item['AVG'], item['STD']))
            gen_pts.append(last_p)
        st.session_state.f_pts = gen_pts
        st.session_state.cache_t = t_sel

    f_prices = [p * r_val for p in st.session_state.f_pts]

    # Метрики Rillet
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ RILLET (7д)<br><h3>{f_prices[-1]:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    pct = ((f_prices[-1] / p_now) - 1) * 100
    c3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h3>{pct:+.2f}%</h3></div>", unsafe_allow_html=True)

    # График и Таблица
    st.write("#### ГРАФИК ПРОГНОЗА")
    hist = item['DF']['Close'].tail(15).values * r_val / (item['P_USD'] * r_val / p_now)
    st.line_chart(np.append(hist, f_prices), color="#00ffcc")

    st.write("#### РАЗБОР ПО ДНЯМ")
    days_df = pd.DataFrame({
        "День": [f"День {i+1}" for i in range(7)],
        "ЦЕНА": [f"{p:,.2f} {sign}" for p in f_prices],
        "ИЗМЕНЕНИЕ": [f"{((p/p_now)-1)*100:+.2f}%" for p in f_prices]
    })
    st.dataframe(days_df, use_container_width=True, hide_index=True)    st.table(days_df) # Используем table для четкости
