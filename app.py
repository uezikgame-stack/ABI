import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. КИБЕР-ДИЗАЙН СО СТАНДАРТНЫМ ШРИФТОМ ---
st.set_page_config(page_title="ABI Terminal", layout="wide")

st.markdown("""
    <style>
    /* Глубокий темный фон с сеткой */
    .stApp {
        background-color: #020508;
        background-image: 
            linear-gradient(rgba(0, 255, 204, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 204, 0.05) 1px, transparent 1px);
        background-size: 30px 30px;
    }
    
    /* Четкие неоновые блоки */
    .metric-card {
        background: rgba(0, 0, 0, 0.85);
        border: 1px solid #00ffcc;
        padding: 20px;
        border-radius: 4px;
        text-align: center;
    }

    h1, h2, h3, p, span { color: #00ffcc !important; }
    
    /* Делаем таблицу широкой */
    .stDataFrame { border: 1px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ПОЛНАЯ БАЗА АКТИВОВ ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KEGC.KZ",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD"
}

@st.cache_data(ttl=300)
def load_market_data(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1mo", group_by='ticker', progress=False)
        rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1]), "$": 1.0}
        
        results = []
        for t in tickers.split():
            try:
                df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
                if df.empty: continue
                conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                results.append({
                    "Asset": t, 
                    "p_usd": float(df['Close'].iloc[-1]) / conv,
                    "trend": (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1)
                })
            except: continue
        return results, r_map
    except: return None, {}

# --- 3. ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.title("ABI_CONTROL")
region = st.sidebar.selectbox("ВЫБЕРИ РЫНОК:", list(MARKETS.keys()))
currency = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
deposit = st.sidebar.number_input("ВАШ КАПИТАЛ:", value=1000)

assets, rates = load_market_data(region)

if assets is None:
    # Требование: просто текст при отсутствии данных
    st.subheader("СЕЙЧАС НЕ ДОСТУПЕН")
else:
    c_sign = currency.split("(")[1][0]
    r_val = rates.get(c_sign, 1.0)
    
    st.title(f"🚀 TERMINAL: {region}")
    
    # ГОРИЗОНТАЛЬНАЯ ТАБЛИЦА TOP-ASSETS
    df_top = pd.DataFrame(assets)
    df_top["Цена"] = (df_top["p_usd"] * r_val).round(2)
    st.dataframe(df_top[["Asset", "Цена"]].set_index("Asset").T, use_container_width=True)

    # АНАЛИТИКА
    sel_ticker = st.selectbox("АКТИВ ДЛЯ ПРОГНОЗА:", df_top["Asset"].tolist())
    item = next(x for x in assets if x['Asset'] == sel_ticker)
    p_now = item['p_usd'] * r_val
    
    # Прогноз (медвежий для BTC по твоей просьбе)
    trend = -0.12 if "BTC" in sel_ticker else item['trend']
    p_future = p_now * (1 + trend)

    # ЦВЕТ ПРОФИТА (МИНУС = КРАСНЫЙ)
    profit = (p_future * (deposit/p_now)) - deposit
    p_color = "#ff4b4b" if profit < 0 else "#00ffcc"

    # РЕКОМЕНДАЦИЯ
    status = "ПОКУПАТЬ" if trend > 0.02 else "ПРОДАВАТЬ" if trend < -0.02 else "УДЕРЖИВАТЬ"
    st.markdown(f"<h2 style='text-align:center; border:2px solid {p_color}; padding:10px; color:{p_color} !important;'>РЕКОМЕНДАЦИЯ: {status}</h2>", unsafe_allow_html=True)

    # МЕТРИКИ
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>СЕЙЧАС<br><h3>{p_now:,.2f} {c_sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ПРОГНОЗ (14д)<br><h3>{p_future:,.2f} {c_sign}</h3></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h3 style='color:{p_color} !important;'>{profit:,.2f} {c_sign}</h3></div>", unsafe_allow_html=True)
