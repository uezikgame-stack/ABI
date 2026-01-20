import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- ДИЗАЙН: ФОН С КУПЮРАМИ И БИТКОИНАМИ ---
st.set_page_config(page_title="ABI Terminal", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url('https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=2232&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
    }
    div[data-testid="metric-container"] {
        background: rgba(20, 20, 25, 0.8);
        border: 1px solid #00ffcc;
        padding: 20px;
        border-radius: 15px;
        backdrop-filter: blur(5px);
    }
    h1, h3 { color: #00ffcc !important; text-shadow: 2px 2px 5px #000; }
    .stDataFrame { background: rgba(0,0,0,0.5); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ ABI: MONEY FLOW TERMINAL")

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.header("ABI Control Panel")
budget = st.sidebar.number_input("Ваш капитал", value=1000, step=100)
# Выбор валюты под капиталом
currency_choice = st.sidebar.radio("Валюта терминала:", ["USD ($)", "RUB (₽)", "KZT (₸)"])
curr_sym = "$" if "USD" in currency_choice else "₽" if "RUB" in currency_choice else "₸"

# Все активы в одном списке, как ты и просил
TICKERS = "AAPL NVDA TSLA MSFT AMZN BTC-USD ETH-USD SBER.ME GAZP.ME LKOH.ME HSBK.KZ KCZ.L GC=F CL=F"

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
            results.append({
                "ticker": t, "price": round(p_now, 2), 
                "trend": smoothed[-1] - smoothed[-2], 
                "vol": float(df['Close'].pct_change().std()), 
                "history": close[-20:]
            })
        except: continue
    return results

assets = load_abi_data(TICKERS)
df_assets = pd.DataFrame(assets).sort_values(by="price", ascending=False).reset_index(drop=True)
df_assets.index += 1

st.subheader("📊 ГЛОБАЛЬНЫЙ МОНИТОРИНГ")
st.dataframe(df_assets[["ticker", "price"]], use_container_width=True)

st.divider()
selected_ticker = st.selectbox("ВЫБЕРИТЕ АКТИВ:", df_assets["ticker"].tolist())

if selected_ticker:
    asset = next(item for item in assets if item["ticker"] == selected_ticker)
    
    # Прогноз ABI Ultra
    forecast = [asset['price']]
    daily_growth = []
    for i in range(1, 8):
        next_val = max(forecast[-1] + (asset['trend'] * (0.85**i)) + np.random.normal(0, asset['price'] * asset['vol'] * 0.3), 0.01)
        daily_growth.append({"День": (datetime.now() + timedelta(days=i)).strftime("%d.%m"), "Цена": round(next_val, 2)})
        forecast.append(next_val)

    # МЕТРИКИ
    st.write(f"### 🎯 АНАЛИЗ {selected_ticker}")
    c1, c2, c3 = st.columns(3)
    c1.metric("ЦЕНА СЕЙЧАС", f"{asset['price']} {curr_sym}")
    
    target_p = round(forecast[-1], 2)
    change = ((target_p / asset['price']) - 1) * 100
    c2.metric("ЦЕЛЬ (7 ДНЕЙ)", f"{target_p} {curr_sym}", f"{change:+.2f}%")
    
    profit = (forecast[-1] * (budget/asset['price'])) - budget
    c3.metric("ВАША ПРИБЫЛЬ", f"{profit:,.2f} {curr_sym}")

    # ГРАФИК БЕЗ ОШИБОК
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    history = list(asset['history'])
    ax.plot(range(len(history)), history, color='#888888', alpha=0.5, label="История")
    ax.plot(range(len(history)-1, len(history)+7), forecast, marker='o', color='#00ffcc', linewidth=3, label="Прогноз")
    ax.tick_params(colors='white')
    ax.legend()
    st.pyplot(fig)

    st.write("### 📅 РОСТ ПО ДНЯМ")
    st.table(pd.DataFrame(daily_growth))
