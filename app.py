import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- НАСТРОЙКИ И НОВЫЙ ФОН ---
st.set_page_config(page_title="ABI Quantum", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(10, 15, 25, 0.9), rgba(10, 15, 25, 0.9)), 
                    url('https://img.freepik.com/free-vector/abstract-technology-particle-background_23-2148426649.jpg');
        background-size: cover;
        background-attachment: fixed;
    }
    .metric-card {
        background: rgba(20, 25, 35, 0.8); border-radius: 15px; padding: 20px;
        border: 1px solid rgba(0, 255, 204, 0.2); backdrop-filter: blur(10px);
    }
    .dino-error-box {
        background: white; border-radius: 25px; padding: 40px; text-align: center;
        box-shadow: 0 0 30px rgba(0,0,0,0.5);
    }
    .recommendation-bar {
        text-align: center; padding: 20px; border-radius: 12px;
        font-size: 30px; font-weight: bold; margin-top: 15px; border: 3px solid;
    }
    h1, h2, h3 { color: #00ffcc !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ФУНКЦИЯ ДИНОЗАВРИКА ПРИ ПУСТОТЕ ---
def show_dino_placeholder(region):
    st.markdown(f"""
        <div class="dino-error-box">
            <h1 style="color: #222 !important;">СИГНАЛ ПОТЕРЯН: {region}</h1>
            <img src="https://i.gifer.com/V96u.gif" width="320">
            <p style="color: #444; font-size: 22px; font-weight: bold; margin-top: 20px;">
                ДАННЫЕ НЕ ПРИШЛИ. ДИНОЗАВРИК ИЩЕТ РЕШЕНИЕ...
            </p>
        </div>
    """, unsafe_allow_html=True)

# --- ДВИЖОК ДАННЫХ ---
MARKETS = {
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ",
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM",
    "EUROPE": "ASML MC.PA VOW3.DE NESN.SW SIE.DE SAP.DE AIR.PA RMS.PA MBG.DE",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME",
    "CHINA": "BABA BIDU JD PDD LI NIO TCEHY BYDDY XPEV NTES",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD"
}

@st.cache_data(ttl=300)
def load_assets(m_name):
    try:
        tickers = MARKETS[m_name]
        data = yf.download(tickers, period="1y", group_by='ticker', progress=False)
        rates_df = yf.download(["RUB=X", "KZT=X"], period="1d", progress=False)['Close']
        r_map = {"₽": float(rates_df["RUB=X"].iloc[-1]), "₸": float(rates_df["KZT=X"].iloc[-1]), "$": 1.0}
        
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

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.title("🛡️ ABI CONTROL")
m_choice = st.sidebar.selectbox("РЕГИОН:", list(MARKETS.keys()))
c_choice = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
user_cap = st.sidebar.number_input("ВАШ КАПИТАЛ:", value=1000)

assets, rates = load_assets(m_choice)

# --- ГЛАВНЫЙ МОДУЛЬ ---
if not assets:
    show_dino_placeholder(m_choice)
else:
    c_sign = c_choice.split("(")[1][0]
    rate_val = rates[c_sign]
    
    st.title(f"🚀 QUANTUM TERMINAL: {m_choice}")
    
    # ТОП-25
    df_v = pd.DataFrame(assets).head(25)
    df_v["Цена"] = (df_v["p_usd"] * rate_val).round(2)
    df_v.index = np.arange(1, len(df_v) + 1)
    df_v.index.name = "№"
    st.dataframe(df_v[["Asset", "Цена"]], height=300, use_container_width=True)

    # АНАЛИТИКА
    sel_asset = st.selectbox("ВЫБОР ДЛЯ ПРОГНОЗА:", df_v["Asset"].tolist())
    target_item = next(a for a in assets if a['Asset'] == sel_asset)
    p_now = target_item['p_usd'] * rate_val
    
    np.random.seed(42)
    forecast = [p_now]
    for _ in range(1, 15):
        noise = np.random.normal(0, p_now * target_item['vol'] * 0.5)
        forecast.append(max(forecast[-1] + (target_item['trend'] * rate_val) + noise, 0.01))

    # ЦВЕТОВАЯ ЛОГИКА
    profit_sum = (forecast[-1] * (user_cap/p_now * rate_val)) - (user_cap * rate_val)
    profit_color = "#ff4b4b" if profit_sum < 0 else "#00ffcc" # Красный для минуса
    
    diff_pct = ((forecast[-1]/p_now)-1)*100
    sig_col = "#00ffcc" if diff_pct > 2 else "#ff4b4b" if diff_pct < -2 else "#888888"
    sig_text = "ПОКУПАТЬ" if diff_pct > 2 else "ПРОДАВАТЬ" if diff_pct < -2 else "УДЕРЖИВАТЬ"

    # ВИДЖЕТЫ
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>СЕЙЧАС<br><h2>{p_now:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ (14Д)<br><h2 style='color:{sig_col} !important;'>{forecast[-1]:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)
    # ЦИФРЫ КРАСНЫЕ ПРИ МИНУСЕ
    c3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h2 style='color:{profit_color} !important;'>{profit_sum:,.2f} {c_sign}</h2></div>", unsafe_allow_html=True)

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    ax.plot(range(30), [x * rate_val for x in target_item['hist']], color='white', alpha=0.2)
    ax.plot(range(29, 44), forecast, color=sig_col, linewidth=4, marker='o')
    ax.tick_params(colors='white')
    st.pyplot(fig)

    st.markdown(f"""
        <div class="recommendation-bar" style="color: {sig_col}; border-color: {sig_col};">
            РЕКОМЕНДАЦИЯ: {sig_text}
        </div>
    """, unsafe_allow_html=True)
