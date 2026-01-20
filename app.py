import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. КИБЕРПАНК ДИЗАЙН (ТЕМНЫЙ, НО ВИДНЫЙ) ---
st.set_page_config(page_title="ABI Quantum", layout="wide")

st.markdown("""
    <style>
    /* Статичный кибер-фон: глубокий темно-синий с сеткой */
    .stApp {
        background-color: #050a10;
        background-image: 
            linear-gradient(0deg, transparent 24%, rgba(0, 255, 204, .05) 25%, rgba(0, 255, 204, .05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 204, .05) 75%, rgba(0, 255, 204, .05) 76%, transparent 77%, transparent),
            linear-gradient(90deg, transparent 24%, rgba(0, 255, 204, .05) 25%, rgba(0, 255, 204, .05) 26%, transparent 27%, transparent 74%, rgba(0, 255, 204, .05) 75%, rgba(0, 255, 204, .05) 76%, transparent 77%, transparent);
        background-size: 50px 50px;
    }
    /* Карточки как на скрине image_ad383f.png */
    .metric-card {
        background: rgba(16, 22, 34, 0.9); 
        border: 2px solid #00ffcc;
        padding: 20px; 
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.2);
    }
    .dino-container {
        background: #111; border: 2px solid #00ffcc; border-radius: 15px;
        padding: 40px; text-align: center; color: #00ffcc;
    }
    h1, h2, h3, p { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    .stDataFrame { border: 1px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. БАЗА РЫНКОВ (ВЕРНУЛ ВСЁ) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD"
}

@st.cache_data(ttl=300)
def load_data(m_name):
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

# --- 3. ИНТЕРФЕЙС ---
st.sidebar.markdown("### 🛡️ ABI CONTROL")
m_sel = st.sidebar.selectbox("РЫНОК:", list(MARKETS.keys()))
c_sel = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
cap = st.sidebar.number_input("КАПИТАЛ:", value=1000)

assets, rates = load_data(m_sel)

if not assets:
    # ТОТ САМЫЙ ДИНОЗАВР (КИБЕР-ВЕРСИЯ)
    st.markdown("""
        <div class="dino-container">
            <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExYnZ6Zmt4bm1oZ3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/10X22vczHTQMfK/giphy.gif" width="200" style="filter: invert(1) hue-rotate(100deg);">
            <h1>SYSTEM ERROR: 404</h1>
            <p>ДАННЫЕ ПО РЕГИОНУ НЕ ПОЛУЧЕНЫ. ДИНОЗАВРИК ЖДЕТ...</p>
        </div>
    """, unsafe_allow_html=True)
else:
    c_sign = c_sel.split("(")[1][0]
    r_val = rates[c_sign]
    
    st.title(f"🚀 ABI TERMINAL: {m_sel}")
    
    df_v = pd.DataFrame(assets)
    df_v["Цена"] = (df_v["p_usd"] * r_val).round(2)
    st.dataframe(df_v[["Asset", "Цена"]].head(25), use_container_width=True)

    target = st.selectbox("АКТИВ:", df_v["Asset"].tolist())
    item = next(a for a in assets if a['Asset'] == target)
    p_now = item['p_usd'] * r_val
    
    # Расчет прогноза
    forecast = [p_now]
    for _ in range(1, 15):
        forecast.append(forecast[-1] + (item['trend'] * r_val) + np.random.normal(0, p_now * 0.01))

    # --- 4. ЦВЕТ ПРОФИТА: МИНУС = КРАСНЫЙ, ПЛЮС = ЗЕЛЕНЫЙ ---
    profit = (forecast[-1] * (cap/p_now)) - cap
    p_color = "#ff4b4b" if profit < 0 else "#00ffcc" # ЖЕСТКИЙ ЦВЕТ
    
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='metric-card'>СЕЙЧАС<br><h2 style='color:#00ffcc !important;'>{p_now:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'>ПРОГНОЗ<br><h2 style='color:#00ffcc !important;'>{forecast[-1]:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='metric-card'>ВАШ ПРОФИТ<br><h2 style='color:{p_color} !important;'>{profit:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(10, 3), facecolor='none')
    ax.set_facecolor('none')
    ax.plot(range(30), [x * r_val for x in item['hist']], color='#00ffcc', alpha=0.3)
    ax.plot(range(29, 44), forecast, color=p_color, linewidth=3, marker='o')
    ax.tick_params(colors='#00ffcc')
    st.pyplot(fig)
