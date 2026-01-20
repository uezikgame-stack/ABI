import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# --- ИНТЕРФЕЙС И ФОН ---
st.set_page_config(page_title="ABI Quantum", layout="wide")

# Добавляем фон и стили
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), 
                    url('https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueXNoeXF6eXF6eXF6eXF6eXF6eXF6eXF6eXF6eXF6eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKMGpxxcaOXYT6w/giphy.gif');
        background-size: cover;
    }
    .metric-card {
        background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc33;
        padding: 20px; border-radius: 15px; backdrop-filter: blur(5px);
    }
    .no-data-box {
        background: white; border-radius: 20px; padding: 50px; text-align: center;
    }
    h1, h2, h3 { color: #00ffcc !important; text-shadow: 0 0 10px #00ffcc55; }
    </style>
    """, unsafe_allow_html=True)

# --- ФУНКЦИЯ ПУСТОТЫ С ДИНОЗАВРИКОМ ---
def show_empty_dino(region_name):
    st.markdown(f"""
        <div class="no-data-box">
            <h1 style="color: black !important;">ОШИБКА ДОСТУПА: {region_name}</h1>
            <img src="https://i.gifer.com/V96u.gif" width="350">
            <p style="color: #444; font-size: 22px; font-weight: bold; margin-top: 20px;">
                ДАННЫЕ НЕ ПОЛУЧЕНЫ. ДИНОЗАВРИК ЖДЕТ СИГНАЛА...
            </p>
            <p style="color: #888;">Проверьте подключение или попробуйте сменить регион в меню слева.</p>
        </div>
    """, unsafe_allow_html=True)

# --- ДАННЫЕ (КАЗАХСТАН, РФ, ВЕСЬ МИР) ---
MARKETS = {
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ CCBN.KZ KZAP.KZ KEGC.KZ",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME",
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META",
    "CHINA": "BABA BIDU JD PDD LI NIO",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD"
}

@st.cache_data(ttl=300)
def get_market_engine(m_name):
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
    except:
        return [], {}

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.title("🛡️ ABI CONTROL")
m_sel = st.sidebar.selectbox("ВЫБОР РЕГИОНА:", list(MARKETS.keys()))
c_sel = st.sidebar.radio("ВАЛЮТА:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
capital = st.sidebar.number_input("КАПИТАЛ:", value=1000)

assets, rates = get_market_engine(m_sel)

# --- ГЛАВНАЯ ЛОГИКА ---
if not assets:
    # ЕСЛИ ДАННЫХ НЕТ (КАК В РФ НА СКРИНАХ) — ПОКАЗЫВАЕМ ДИНО
    show_empty_dino(m_sel)
else:
    c_sym = c_sel.split("(")[1][0]
    r_val = rates[c_sym]
    
    st.title(f"🚀 TERMINAL: {m_sel}")
    
    # 1. ТОП-25 (ВЕРТИКАЛЬНЫЙ)
    df_top = pd.DataFrame(assets).head(25)
    df_top["Цена"] = (df_top["p_usd"] * r_val).round(2)
    df_top.index = np.arange(1, len(df_top) + 1)
    df_top.index.name = "№"
    st.dataframe(df_top[["Asset", "Цена"]], height=300, use_container_width=True)

    # 2. ПРОГНОЗ
    target = st.selectbox("ВЫБЕРИТЕ АКТИВ:", df_top["Asset"].tolist())
    item = next(a for a in assets if a['Asset'] == target)
    p_now = item['p_usd'] * r_val
    
    np.random.seed(42)
    forecast = [p_now]
    for _ in range(1, 15):
        noise = np.random.normal(0, p_now * item['vol'] * 0.5)
        forecast.append(max(forecast[-1] + (item['trend'] * r_val) + noise, 0.01))

    diff = ((forecast[-1]/p_now)-1)*100
    clr = "#00ffcc" if diff > 2 else "#ff4b4b" if diff < -2 else "#888888"
    sig = "ПОКУПАТЬ" if diff > 2 else "ПРОДАВАТЬ" if diff < -2 else "УДЕРЖИВАТЬ"

    # Виджеты
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'>СЕЙЧАС<br><h2>{p_now:,.2f} {c_sym}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'>ЦЕЛЬ<br><h2 style='color:{clr} !important;'>{forecast[-1]:,.2f} {c_sym}</h2></div>", unsafe_allow_html=True)
    
    prof = (forecast[-1] * (capital/p_now * r_val)) - (capital * r_val)
    c3.markdown(f"<div class='metric-card'>ПРОФИТ<br><h2>{prof:,.2f} {c_sym}</h2></div>", unsafe_allow_html=True)

    # График
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    ax.plot(range(30), [x * r_val for x in item['hist']], color='white', alpha=0.3)
    ax.plot(range(29, 44), forecast, color=clr, linewidth=4, marker='o')
    ax.tick_params(colors='white')
    st.pyplot(fig)

    st.markdown(f"""
        <div style="text-align: center; padding: 20px; border: 2px solid {clr}; border-radius: 10px; color: {clr}; font-size: 30px; font-weight: bold;">
            РЕКОМЕНДАЦИЯ: {sig}
        </div>
    """, unsafe_allow_html=True)
