import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. КИБЕР-ДИЗАЙН И СТАРЫЙ ШРИФТ ---
st.set_page_config(page_title="ABI Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #020508;
        background-image: linear-gradient(0deg, transparent 24%, rgba(0, 255, 204, .05) 25%, rgba(0, 255, 204, .05) 26%, transparent 27%),
                          linear-gradient(90deg, transparent 24%, rgba(0, 255, 204, .05) 25%, rgba(0, 255, 204, .05) 26%, transparent 27%);
        background-size: 50px 50px;
        font-family: 'Courier New', Courier, monospace !important;
    }
    h1, h2, h3, p, span, div, label { 
        color: #00ffcc !important; 
        font-family: 'Courier New', Courier, monospace !important; 
    }
    .metric-box {
        border: 1px solid #00ffcc;
        padding: 15px;
        background: rgba(0,0,0,0.8);
        text-align: center;
    }
    .stDataFrame { border: 1px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ПОЛНАЯ БИБЛИОТЕКА (БЕЗ УРЕЗАНИЙ) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL TSMC ASML COST PEP NKE TM",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES MCHI KWEB FUTU BILI",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE DHL.DE SAN.MC ALV.DE",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KEGC.KZ KZTK.KZ",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD"
}

# --- 3. ЛОГИКА ЗАГРУЗКИ ---
def get_data(market):
    try:
        tickers = MARKETS[market]
        data = yf.download(tickers, period="1mo", interval="1d", progress=False)['Close']
        if data.empty: return None
        
        # Получаем курс для конвертации
        rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"$": 1.0, "₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1])}
        
        res = []
        for t in tickers.split():
            try:
                p_usd = float(data[t].iloc[-1]) if len(tickers.split()) > 1 else float(data.iloc[-1])
                # Упрощенная логика валюты тикера
                if ".ME" in t: p_usd /= r_map["₽"]
                if ".KZ" in t or "KCZ" in t: p_usd /= r_map["₸"]
                
                res.append({"Asset": t, "Price_USD": p_usd, "Trend": (data[t].iloc[-1] / data[t].iloc[0] - 1)})
            except: continue
        return res, r_map
    except: return None, {}

# --- 4. ИНТЕРФЕЙС ---
st.sidebar.title("⌨️ ABI_CONTROL_V4")
m_sel = st.sidebar.selectbox("РЫНОК:", list(MARKETS.keys()))
c_sel = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
cap = st.sidebar.number_input("ДЕПОЗИТ:", value=1000)

assets, rates = get_data(m_sel)
sign = c_sel.split("(")[1][0]
rate = rates.get(sign, 1.0)

st.title(f"🚀 TERMINAL: {m_sel}")

if assets is None:
    # Твое требование: если не найдено - просто надпись
    st.warning("ДАННЫЕ ПО РЕГИОНУ СЕЙЧАС НЕ ДОСТУПНЫ")
else:
    # ТАБЛИЦА (ГОРИЗОНТАЛЬНАЯ)
    df = pd.DataFrame(assets)
    df["Цена"] = (df["Price_USD"] * rate).round(2)
    st.subheader(f"📊 TOP ASSETS ({m_sel})")
    st.dataframe(df[["Asset", "Цена"]].set_index("Asset").T, use_container_width=True)

    # АНАЛИЗ
    target = st.selectbox("ВЫБЕРИ АКТИВ:", df["Asset"].tolist())
    item = next(x for x in assets if x['Asset'] == target)
    p_now = item['Price_USD'] * rate
    
    # Твоя идея с падением Биткоина на 7000
    # Если это BTC, делаем медвежий прогноз для теста
    trend_factor = -0.15 if "BTC" in target else item['Trend']
    p_future = p_now * (1 + trend_factor)

    # СИГНАЛЫ
    if trend_factor > 0.02: status, s_color = "ПОКУПАТЬ", "#00ffcc"
    elif trend_factor < -0.02: status, s_color = "ПРОДАВАТЬ", "#ff4b4b"
    else: status, s_color = "УДЕРЖИВАТЬ", "#888888"

    st.markdown(f"<h2 style='text-align:center; color:{s_color}; border:2px solid {s_color}; padding:10px;'>{status}</h2>", unsafe_allow_html=True)

    # МЕТРИКИ + ЦВЕТ ПРОФИТА (МИНУС = КРАСНЫЙ)
    profit = (p_future * (cap/p_now)) - cap
    p_color = "#ff4b4b" if profit < 0 else "#00ffcc"

    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f"<div class='metric-box'>ТЕКУЩАЯ<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='metric-box'>ПРОГНОЗ<br><h3>{p_future:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='metric-box'>ПРОФИТ<br><h3 style='color:{p_color} !important;'>{profit:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
