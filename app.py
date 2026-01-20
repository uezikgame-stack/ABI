import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- СТИЛИ И ФОН (ОСТАВЛЯЕМ КАК БЫЛО) ---
st.set_page_config(page_title="ABI Quantum", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), 
                    url('https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXNoeXF6eXF6eXF6eXF6eXF6eXF6eXF6eXF6eXF6eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKMGpxxcaOXYT6w/giphy.gif');
        background-size: cover;
    }
    .metric-card {
        background: rgba(15, 20, 30, 0.9); border: 1px solid #00ffcc33;
        padding: 20px; border-radius: 15px;
    }
    /* Тот самый белый бокс с Дино как в Google */
    .google-dino-box {
        background: #f7f7f7; border-radius: 10px; padding: 50px; 
        text-align: center; border: 2px solid #ddd; color: #535353;
        font-family: "Segoe UI", Tahoma, sans-serif;
    }
    h1, h2, h3 { color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- РЫНКИ ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD"
}

@st.cache_data(ttl=300)
def get_data(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
        rates = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates["RUB=X"].iloc[-1]), "₸": float(rates["KZT=X"].iloc[-1]), "$": 1.0}
        
        res = []
        for t in tickers.split():
            try:
                df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
                if df.empty: continue
                conv = r_map["₽"] if ".ME" in t else r_map["₸"] if (".KZ" in t or "KCZ" in t) else 1.0
                res.append({
                    "Asset": t, "p_usd": float(df['Close'].iloc[-1]) / conv,
                    "hist": (df['Close'].values / conv)[-30:],
                    "vol": float(df['Close'].pct_change().std()),
                    "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-15]) / conv / 15
                })
            except: continue
        return res, r_map
    except: return [], {}

# --- SIDEBAR ---
st.sidebar.title("🛡️ ABI CONTROL")
m_sel = st.sidebar.selectbox("РЕГИОН:", list(MARKETS.keys()))
c_sel = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
cap = st.sidebar.number_input("КАПИТАЛ:", value=1000)

assets, rates = get_data(m_sel)

# --- ГЛАВНЫЙ ЭКРАН ---
if not assets:
    # ДИНОЗАВР КАК У GOOGLE ЕСЛИ ПУСТО
    st.markdown("""
        <div class="google-dino-box">
            <img src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExYnZ6Zmt4bm1oZ3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0Z3R0ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/10X22vczHTQMfK/giphy.gif" width="200">
            <h2 style="color: #535353 !important; font-family: sans-serif;">Нет подключения к интернету (или данным)</h2>
            <p style="font-size: 16px;">Попробуйте выбрать другой регион. Динозаврик ждет...</p>
            <p style="color: #999; font-size: 14px; margin-top: 10px;">ERR_INTERNET_DISCONNECTED</p>
        </div>
    """, unsafe_allow_html=True)
else:
    c_sign = c_sel.split("(")[1][0]
    r_val = rates[c_sign]
    
    st.title(f"🚀 TERMINAL: {m_sel}")
    
    # ТАБЛИЦА
    df_v = pd.DataFrame(assets).head(25)
    df_v["Цена"] = (df_v["p_usd"] * r_val).round(2)
    df_v.index = np.arange(1, len(df_v) + 1)
    st.dataframe(df_v[["Asset", "Цена"]], height=300, use_container_width=True)

    # ВЫБОР И ПРОГНОЗ
    target = st.selectbox("ВЫБОР:", df_v["Asset"].tolist())
    item = next(a for a in assets if a['Asset'] == target)
    p_now = item['p_usd'] * r_val
    
    np.random.seed(42)
    forecast = [p_now]
    for _ in range(1, 15):
        noise = np.random.normal(0, p_now * item['vol'] * 0.5)
        forecast.append(max(forecast[-1] + (item['trend'] * r_val) + noise, 0.01))

    # ЛОГИКА ЦВЕТА ПРОФИТА (КРАСНЫЙ ДЛЯ МИНУСА)
    prof = (forecast[-1] * (cap/p_now * r_val)) - (cap * r_val)
    p_clr = "#ff4b4b" if prof < 0 else "#00ffcc" #
    
    diff = ((forecast[-1]/p_now)-1)*100
    s_clr = "#00ffcc" if diff > 2 else "#ff4b4b" if diff < -2 else "#888888"

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>СЕЙЧАС<br><h2>{p_now:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ПРОГНОЗ<br><h2 style='color:{s_clr} !important;'>{forecast[-1]:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h2 style='color:{p_clr} !important;'>{prof:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    ax.plot(range(30), [x * r_val for x in item['hist']], color='white', alpha=0.3)
    ax.plot(range(29, 44), forecast, color=s_clr, linewidth=4, marker='o')
    ax.tick_params(colors='white')
    st.pyplot(fig)
