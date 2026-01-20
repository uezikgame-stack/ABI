import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="ABI Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .metric-card {
        background: rgba(10, 15, 25, 0.95); border-left: 5px solid #00ffcc;
        padding: 20px; border-radius: 10px; margin-bottom: 10px;
    }
    .recommendation-box {
        text-align: center; padding: 20px; border-radius: 10px;
        font-size: 28px; font-weight: bold; margin-top: 20px;
        border: 2px solid;
    }
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- ФУНКЦИЯ ДЛЯ ДИНОЗАВРИКА (ВСЕГДА ПРИ ОБНОВЛЕНИИ) ---
def show_dino_loader():
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
            <div style="background-color: white; height: 100vh; width: 100vw; position: fixed; top: 0; left: 0; z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <h1 style="color: black !important; font-family: 'Arial'; margin-bottom: 20px;">ABI QUANTUM LOADING...</h1>
                <img src="https://i.gifer.com/V96u.gif" width="280">
                <p style="color: #555; font-size: 20px; margin-top: 30px;">Синхронизация данных ТОП-25...</p>
            </div>
            """, unsafe_allow_html=True)
        time.sleep(2.5) # Время показа динозаврика
    placeholder.empty()

# --- ЛОГИКА ДАННЫХ ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL TSMC ASML BABA COST PEP NKE TM ORCL MCD DIS",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME PLZL.ME MOEX.ME SNGS.ME MAGN.ME AFLT.ME RTKM.ME FEES.ME CBOM.ME",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES MCHI KWEB FUTU BILI VIPS KC TME IQ EH ZLAB GDS",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE DHL.DE SAN.MC ALV.DE CS.PA BBVA.MC NOVO-B.CO",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD MATIC-USD TRX-USD LTC-USD"
}

@st.cache_data(ttl=300)
def load_data(m_name):
    tickers = MARKETS[m_name]
    data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
    rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
    r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1]), "$": 1.0}
    
    res = []
    for t in tickers.split():
        try:
            df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
            if df.empty: continue
            is_rub, is_kzt = ".ME" in t, (".KZ" in t or "KCZ" in t)
            conv = r_map["₽"] if is_rub else r_map["₸"] if is_kzt else 1.0
            res.append({
                "Asset": t,
                "p_usd": float(df['Close'].iloc[-1]) / conv,
                "hist": (df['Close'].values / conv)[-30:],
                "vol": float(df['Close'].pct_change().std()),
                "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
            })
        except: continue
    return res, r_map

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.title("🛡️ ABI CONTROL")
m_sel = st.sidebar.selectbox("ВЫБОР РЫНКА:", list(MARKETS.keys()))

# Триггер динозаврика при смене рынка
if 'm_key' not in st.session_state or st.session_state.m_key != m_sel:
    show_dino_loader()
    st.session_state.m_key = m_sel

curr_sel = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
capital = st.sidebar.number_input("ВАШ КАПИТАЛ:", value=1000)

assets, rates = load_data(m_sel)
c_sym = curr_sel.split("(")[1][0]
r_val = rates[c_sym]

# --- ИНТЕРФЕЙС ---
st.title(f"🚀 ABI QUANTUM: {m_sel}")

if assets:
    # 1. НУМЕРОВАННЫЙ ТОП-25
    st.subheader("🏆 ТОП-25 АКТИВОВ")
    df_top = pd.DataFrame(assets).head(25)
    df_top["Цена"] = (df_top["p_usd"] * r_val).round(2)
    df_top.index = np.arange(1, len(df_top) + 1)
    df_top.index.name = "№"
    st.dataframe(df_top[["Asset", "Цена"]], use_container_width=True, height=350)

    st.divider()

    # 2. АНАЛИЗ И СИГНАЛЫ
    target = st.selectbox("ВЫБЕРИТЕ АКТИВ:", df_top["Asset"].tolist())
    item = next(a for a in assets if a['Asset'] == target)
    
    p_now = item['p_usd'] * r_val
    np.random.seed(42)
    forecast = [p_now]
    for _ in range(1, 15):
        noise = np.random.normal(0, p_now * item['vol'] * 0.5)
        forecast.append(max(forecast[-1] + (item['trend'] * r_val) + noise, 0.01))

    # Метрики
    diff = ((forecast[-1]/p_now)-1)*100
    if diff > 3:
        signal, color = "ПОКУПАТЬ 🟢", "#00ffcc"
    elif diff < -3:
        signal, color = "ПРОДАВАТЬ 🔴", "#ff4b4b"
    else:
        signal, color = "УДЕРЖИВАТЬ 🟡", "#888888"

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>СЕЙЧАС<br><h2>{p_now:,.2f} {c_sym}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ (14Д)<br><h2 style='color:{color} !important;'>{forecast[-1]:,.2f} {c_sym}</h2></div>", unsafe_allow_html=True)
    
    profit = (forecast[-1] * (capital/p_now * r_val)) - (capital * r_val)
    c3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h2>{profit:,.2f} {c_sym}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    h_data = [x * r_val for x in item['hist']]
    ax.plot(range(len(h_data)), h_data, color='white', alpha=0.3)
    ax.plot(range(len(h_data)-1, len(h_data)+14), forecast, color=color, linewidth=4, marker='o')
    ax.tick_params(colors='white')
    st.pyplot(fig)

    # 3. КРУПНАЯ НАДПИСЬ РЕКОМЕНДАЦИИ
    st.markdown(f"""
        <div class="recommendation-box" style="color: {color}; border-color: {color};">
            РЕКОМЕНДАЦИЯ: {signal}
        </div>
    """, unsafe_allow_html=True)
