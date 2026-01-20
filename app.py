import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- ГЛОБАЛЬНЫЙ ДИЗАЙН (STYLING) ---
st.set_page_config(page_title="ABI Terminal", layout="wide")

st.markdown("""
    <style>
    /* Фон и общие настройки */
    .stApp { background-color: #050505; color: #e0e0e0; }
    
    /* Стеклянные карточки для метрик */
    div[data-testid="metric-container"] {
        background: rgba(16, 16, 20, 0.8);
        border: 1px solid rgba(0, 255, 204, 0.3);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.1);
    }
    
    /* Текст заголовков */
    h1, h2, h3 { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    
    /* Скрытие лишнего */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ ABI: QUANTUM INTELLIGENCE")

# --- ЛОГИКА ДАННЫХ ---
st.sidebar.header("ABI Control Panel")
budget = st.sidebar.number_input("Ваш капитал ($)", value=1000, step=100)
market_choice = st.sidebar.selectbox("Выберите рынок", ["USA", "RF", "CRYPTO", "CHINA", "GOODS"])

MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC",
    "RF": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD",
    "CHINA": "BABA BIDU JD PDD LI NIO",
    "GOODS": "GC=F SI=F CL=F NG=F"
}

@st.cache_data(ttl=300)
def load_abi_data(tickers):
    data = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False)
    results = []
    for t in tickers.split():
        try:
            df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
            if df.empty: continue
            close = df['Close'].values
            alpha = 0.35 
            smoothed = [close[0]]
            for i in range(1, len(close)):
                smoothed.append(alpha * close[i] + (1 - alpha) * smoothed[-1])
            p_now = float(close[-1])
            last_trend = smoothed[-1] - smoothed[-2]
            vol = float(df['Close'].pct_change().std())
            results.append({"ticker": t, "price": round(p_now, 2), "trend": last_trend, "vol": vol, "history": close[-20:]})
        except: continue
    return results

assets = load_abi_data(MARKETS[market_choice])
df_assets = pd.DataFrame(assets).sort_values(by="price", ascending=False).reset_index(drop=True)

# Таблица котировок в новом стиле
st.subheader(f"⚡ LIVE FEED: {market_choice}")
st.dataframe(df_assets[["ticker", "price"]], use_container_width=True)

st.divider()
selected_ticker = st.selectbox("ВЫБЕРИТЕ ОБЪЕКТ:", df_assets["ticker"].tolist())

if selected_ticker:
    asset = next(item for item in assets if item["ticker"] == selected_ticker)
    
    # Расчет прогноза (Алгоритм ABI)
    forecast = [asset['price']]
    daily_growth = []
    for i in range(1, 8):
        damping = 0.85 ** i
        noise = np.random.normal(0, asset['price'] * asset['vol'] * 0.3)
        next_val = max(forecast[-1] + (asset['trend'] * damping) + noise, 0.01)
        daily_growth.append({"День": (datetime.now() + timedelta(days=i)).strftime("%d.%m"), "Цена": round(next_val, 2)})
        forecast.append(next_val)

    # --- ВИЗУАЛИЗАЦИЯ (ДИЗАЙН КАРТИНКИ) ---
    st.write(f"### 🚀 АНАЛИЗ {selected_ticker}")
    c1, c2, c3 = st.columns(3)
    c1.metric("ЦЕНА СЕЙЧАС", f"${asset['price']}")
    
    target_p = round(forecast[-1], 2)
    change = ((target_p / asset['price']) - 1) * 100
    c2.metric("ЦЕЛЬ (7 ДНЕЙ)", f"${target_p}", f"{change:+.2f}%")
    
    profit = (forecast[-1] * (budget/asset['price'])) - budget
    c3.metric("ВАША ПРИБЫЛЬ", f"${profit:,.2f}")

    # График в стиле Cyberpunk
    fig, ax = plt.subplots(figsize=(12, 5), facecolor='#050505')
    ax.set_facecolor('#050505')
    
    history = list(asset['history'])
    ax.plot(range(len(history)), history, color='#444444', linewidth=1, label="History")
    ax.plot(range(len(history)-1, len(history)+7), forecast, marker='o', color='#00ffcc', 
            linewidth=3, markersize=8, label="ABI Forecast", shadow=True)
    
    # Сетка и оси
    ax.grid(color='#222222', linestyle='--', alpha=0.5)
    ax.tick_params(axis='both', colors='#888888')
    for spine in ax.spines.values(): spine.set_edgecolor('#333333')
    ax.legend(facecolor='#111111', edgecolor='#00ffcc', labelcolor='white')
    
    st.pyplot(fig)

    # Таблица роста
    with st.expander("📅 ДЕТАЛЬНЫЙ ГРАФИК РОСТА ПО ДНЯМ"):
        st.table(pd.DataFrame(daily_growth))
