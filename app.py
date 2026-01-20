import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. КИБЕР-ДИЗАЙН И ПРЕЖНИЙ ШРИФТ ---
st.set_page_config(page_title="ABI Quantum", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap');
    
    .stApp {
        background-color: #050a10;
        background-image: linear-gradient(0deg, transparent 24%, rgba(0, 255, 204, .03) 25%, rgba(0, 255, 204, .03) 26%, transparent 27%),
                          linear-gradient(90deg, transparent 24%, rgba(0, 255, 204, .03) 25%, rgba(0, 255, 204, .03) 26%, transparent 27%);
        background-size: 40px 40px;
        font-family: 'Courier Prime', monospace !important;
    }
    .metric-card {
        background: rgba(10, 15, 25, 0.9); 
        border: 2px solid #00ffcc;
        padding: 20px; border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.2);
    }
    .status-box {
        padding: 15px; border-radius: 5px; text-align: center;
        font-weight: bold; font-size: 24px; margin: 10px 0;
        border: 2px solid;
    }
    h1, h2, h3, p, span { color: #00ffcc !important; font-family: 'Courier Prime', monospace !important; }
    .stDataFrame { border: 1px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ПОЛНАЯ БИБЛИОТЕКА (БЕЗ УРЕЗАНИЙ) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL TSMC ASML COST PEP NKE TM ORCL MCD DIS",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES MCHI KWEB FUTU BILI VIPS KC TME IQ EH ZLAB",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE DHL.DE SAN.MC ALV.DE CS.PA BBVA.MC",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME ALRS.ME MTSS.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KEGC.KZ KZTK.KZ KZTO.KZ ASBN.KZ BAST.KZ",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD DOGE-USD MATIC-USD"
}

@st.cache_data(ttl=300)
def fetch_all_data(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
        rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1]), "$": 1.0}
        
        final = []
        for t in tickers.split():
            try:
                df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
                if df.empty: continue
                conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                final.append({
                    "Asset": t, "p_usd": float(df['Close'].iloc[-1]) / conv,
                    "hist": (df['Close'].values / conv)[-30:],
                    "vol": float(df['Close'].pct_change().std()),
                    "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
                })
            except: continue
        return final, r_map
    except: return [], {}

# --- 3. УПРАВЛЕНИЕ ---
st.sidebar.title("⌨️ ABI_CMD")
m_choice = st.sidebar.selectbox("ВЫБЕРИ РЫНОК:", list(MARKETS.keys()))
c_choice = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
capital = st.sidebar.number_input("ДЕПОЗИТ:", value=1000)

assets, rates = fetch_all_data(m_choice)
c_sign = c_choice.split("(")[1][0]
r_val = rates[c_sign]

st.title(f"🚀 QUANTUM TERMINAL: {m_choice}")

# --- 4. ДИНОЗАВРИК В КЗ И РОССИИ (ВСЕГДА ТУТ) ---
if m_choice in ["RF (Россия)", "KAZ (Казахстан)"]:
    st.markdown("""
        <div style="text-align:center; padding:10px; border: 1px solid #00ffcc33;">
            <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExYnZ6Zmt4bm1oZ3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/10X22vczHTQMfK/giphy.gif" width="100" style="filter: hue-rotate(90deg) brightness(1.5);">
            <p style="font-size:10px;">SYSTEM_DINO_CORE: ACTIVE</p>
        </div>
    """, unsafe_allow_html=True)

if not assets:
    st.error("ОШИБКА API. ПРОВЕРЬ ПОДКЛЮЧЕНИЕ.")
else:
    # ТАБЛИЦА
    df_res = pd.DataFrame(assets)
    df_res["Цена"] = (df_res["p_usd"] * r_val).round(2)
    st.dataframe(df_res[["Asset", "Цена"]].head(25), use_container_width=True)

    target_t = st.selectbox("ВЫБЕРИ АКТИВ:", df_res["Asset"].tolist())
    item = next(a for a in assets if a['Asset'] == target_t)
    p_now = item['p_usd'] * r_val
    
    # Прогноз
    forecast = [p_now]
    for _ in range(1, 15):
        forecast.append(forecast[-1] + (item['trend'] * r_val) + np.random.normal(0, p_now * 0.015))

    # --- 5. ЛОГИКА СИГНАЛОВ (КУПИТЬ/ПРОДАТЬ) ---
    diff_pct = ((forecast[-1] / p_now) - 1) * 100
    if diff_pct > 2:
        status, s_color = "ПОКУПАТЬ 📈", "#00ffcc"
    elif diff_pct < -2:
        status, s_color = "ПРОДАВАТЬ 📉", "#ff4b4b"
    else:
        status, s_color = "УДЕРЖИВАТЬ 🛡️", "#888888"

    st.markdown(f"<div class='status-box' style='color:{s_color}; border-color:{s_color};'>РЕКОМЕНДАЦИЯ: {status}</div>", unsafe_allow_html=True)

    # --- 6. ЦВЕТ ПРОФИТА (МИНУС = КРАСНЫЙ) ---
    profit = (forecast[-1] * (capital/p_now)) - capital
    p_color = "#ff4b4b" if profit < 0 else "#00ffcc"

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>ТЕКУЩАЯ<br><h2>{p_now:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ (14д)<br><h2>{forecast[-1]:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h2 style='color:{p_color} !important;'>{profit:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(10, 3), facecolor='none')
    ax.set_facecolor('none')
    ax.plot(range(30), [x * r_val for x in item['hist']], color='#00ffcc', alpha=0.3)
    ax.plot(range(29, 44), forecast, color=s_color, linewidth=3, marker='o')
    ax.tick_params(colors='#00ffcc')
    st.pyplot(fig)
