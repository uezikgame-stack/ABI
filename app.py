import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. КИБЕР-ДИЗАЙН (СТАНДАРТНЫЙ ШРИФТ) ---
st.set_page_config(page_title="ABI Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #020508;
        background-image: 
            linear-gradient(rgba(0, 255, 204, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 204, 0.05) 1px, transparent 1px);
        background-size: 30px 30px;
    }
    .metric-card {
        background: rgba(0, 0, 0, 0.9);
        border: 1px solid #00ffcc;
        padding: 20px;
        border-radius: 4px;
        text-align: center;
    }
    h1, h2, h3, p, span, div, label { color: #00ffcc !important; }
    .stDataFrame { border: 1px solid #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. СЛОВАРЬ ПЕРЕВОДОВ ---
UI = {
    "RU": {
        "market": "РЫНОК", "curr": "ВАЛЮТА", "depo": "ДЕПОЗИТ", "lang": "ЯЗЫК",
        "top": "ВЕРТИКАЛЬНЫЙ ТОП АКТИВОВ", "select": "ВЫБЕРИ ДЛЯ ПРОГНОЗА:",
        "now": "СЕЙЧАС", "target": "ЦЕЛЬ (14д)", "profit": "ПРОФИТ",
        "buy": "ПОКУПАТЬ", "sell": "ПРОДАВАТЬ", "hold": "УДЕРЖИВАТЬ",
        "err": "СЕЙЧАС НЕ ДОСТУПЕН", "signal": "СИГНАЛ", "ticker": "ТИКЕР", "price": "ЦЕНА"
    },
    "EN": {
        "market": "MARKET", "curr": "CURRENCY", "depo": "CAPITAL", "lang": "LANGUAGE",
        "top": "VERTICAL TOP ASSETS", "select": "SELECT FOR FORECAST:",
        "now": "CURRENT", "target": "TARGET (14d)", "profit": "PROFIT",
        "buy": "BUY", "sell": "SELL", "hold": "HOLD",
        "err": "CURRENTLY UNAVAILABLE", "signal": "SIGNAL", "ticker": "TICKER", "price": "PRICE"
    }
}

# --- 3. ПОЛНАЯ БАЗА ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KEGC.KZ",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD"
}

@st.cache_data(ttl=300)
def load_data(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1mo", group_by='ticker', progress=False)
        rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1]), "$": 1.0}
        
        final = []
        for t in tickers.split():
            try:
                df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
                if df.empty: continue
                conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                final.append({
                    "T": t, "P_USD": float(df['Close'].iloc[-1]) / conv,
                    "CH": (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1)
                })
            except: continue
        return final, r_map
    except: return None, {}

# --- 4. САЙДБАР (УПРАВЛЕНИЕ ЯЗЫКОМ) ---
ln = st.sidebar.radio("ЯЗЫК / LANGUAGE", ["RU", "EN"])
st.sidebar.divider()
m_sel = st.sidebar.selectbox(UI[ln]["market"], list(MARKETS.keys()))
c_sel = st.sidebar.radio(UI[ln]["curr"], ["USD ($)", "RUB (₽)", "KZT (₸)"])
depo = st.sidebar.number_input(UI[ln]["depo"], value=1000)

assets, rates = load_data(m_sel)

if assets is None or len(assets) == 0:
    st.subheader(UI[ln]["err"])
else:
    sign = c_sel.split("(")[1][0]
    rate = rates.get(sign, 1.0)
    
    st.title(f"🚀 ABI TERMINAL: {m_sel}")
    
    # ВЕРТИКАЛЬНАЯ ТАБЛИЦА
    df_res = pd.DataFrame(assets)
    df_res[UI[ln]["price"]] = (df_res["P_USD"] * rate).round(2)
    df_res.columns = [UI[ln]["ticker"], "P_USD", "CH", UI[ln]["price"]]
    st.subheader(f"📊 {UI[ln]['top']}")
    st.dataframe(df_res[[UI[ln]["ticker"], UI[ln]["price"]]], use_container_width=True, height=400)

    # АНАЛИЗ
    sel_t = st.selectbox(UI[ln]["select"], df_res[UI[ln]["ticker"]].tolist())
    item = next(x for x in assets if x['T'] == sel_t)
    p_now = item['P_USD'] * rate
    
    # Прогноз (медвежий для BTC)
    tr = -0.15 if "BTC" in sel_t else item['CH']
    p_target = p_now * (1 + tr)

    # ЦВЕТ ПРОФИТА (МИНУС = КРАСНЫЙ)
    profit = (p_target * (depo/p_now)) - depo
    p_color = "#ff4b4b" if profit < 0 else "#00ffcc"

    # СИГНАЛ
    sig_text = UI[ln]["sell"] if tr < -0.02 else UI[ln]["buy"] if tr > 0.02 else UI[ln]["hold"]
    st.markdown(f"<h2 style='text-align:center; border:2px solid {p_color}; padding:10px; color:{p_color} !important;'>{UI[ln]['signal']}: {sig_text}</h2>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>{UI[ln]['now']}<br><h3>{p_now:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>{UI[ln]['target']}<br><h3>{p_target:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'>{UI[ln]['profit']}<br><h3 style='color:{p_color} !important;'>{profit:,.2f} {sign}</h3></div>", unsafe_allow_html=True)
