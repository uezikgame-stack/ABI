import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# --- 1. НОВЫЙ ВИДНЫЙ СТАТИЧНЫЙ ФОН ---
st.set_page_config(page_title="ABI Quantum", layout="wide")

st.markdown("""
    <style>
    /* Светлый, видный фон без анимации */
    .stApp {
        background-color: #f0f2f6;
        background-image: radial-gradient(#d1d5db 1px, transparent 1px);
        background-size: 20px 20px;
    }
    /* Карточки с четкими границами */
    .metric-card {
        background: white; 
        border: 2px solid #374151;
        padding: 20px; 
        border-radius: 12px;
        box-shadow: 4px 4px 0px #374151;
        color: #1f2937;
    }
    .google-dino-box {
        background: white; border: 2px solid #ccc; padding: 50px; 
        text-align: center; border-radius: 15px; margin: 20px auto;
    }
    h1, h2, h3 { color: #1f2937 !important; font-weight: 800 !important; }
    .stDataFrame { background: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ПОЛНАЯ БАЗА (КИТАЙ, КЗ, РФ) ---
MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD"
}

@st.cache_data(ttl=300)
def get_clean_data(m_name):
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
st.sidebar.header("⚙️ НАСТРОЙКИ")
m_choice = st.sidebar.selectbox("РЕГИОН:", list(MARKETS.keys()))
c_choice = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
user_cap = st.sidebar.number_input("КАПИТАЛ:", value=1000)

assets, rates = get_clean_data(m_choice)

if not assets:
    # ОРИГИНАЛЬНЫЙ СЕРЫЙ ДИНОЗАВР
    st.markdown("""
        <div class="google-dino-box">
            <img src="https://www.google.com/logos/2010/pacman10-i.png" style="filter: grayscale(100%); width: 150px;">
            <h1 style="color: #555 !important;">Нет данных</h1>
            <p>Динозаврик ждет подключения. Проверьте регион.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    c_sign = c_choice.split("(")[1][0]
    r_val = rates[c_sign]
    
    st.title(f"📊 Terminal: {m_choice}")
    
    df_res = pd.DataFrame(assets)
    df_res["Цена"] = (df_res["p_usd"] * r_val).round(2)
    st.dataframe(df_res[["Asset", "Цена"]].head(25), use_container_width=True)

    sel_t = st.selectbox("АКТИВ ДЛЯ АНАЛИЗА:", df_res["Asset"].tolist())
    item = next(a for a in assets if a['Asset'] == sel_t)
    p_now = item['p_usd'] * r_val
    
    # Расчет прогноза
    forecast = [p_now]
    for _ in range(1, 15):
        forecast.append(forecast[-1] + (item['trend'] * r_val) + np.random.normal(0, p_now * 0.02))

    # --- 4. ЖЕСТКАЯ ЛОГИКА ЦВЕТА ПРОФИТА ---
    profit = (forecast[-1] * (user_cap/p_now)) - user_cap
    # Если профит < 0, то КРАСНЫЙ, если > 0, то ЗЕЛЕНЫЙ
    prof_color = "#d32f2f" if profit < 0 else "#2e7d32"
    
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='metric-card'>СЕЙЧАС<br><h2>{p_now:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='metric-card'>ПРОГНОЗ<br><h2>{forecast[-1]:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    # ЗДЕСЬ ЦВЕТ ЗАВИСИТ ОТ ЗНАКА
    col3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h2 style='color: {prof_color} !important;'>{profit:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(range(30), [x * r_val for x in item['hist']], color='#374151', label='История')
    ax.plot(range(29, 44), forecast, color=prof_color, linewidth=3, marker='o', label='Прогноз')
    st.pyplot(fig)
