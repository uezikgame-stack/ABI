import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- LUXURY DESIGN CONFIG ---
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), 
                    url('https://images.unsplash.com/photo-1611974717482-98ea0524d579?q=80&w=2070');
        background-size: cover; background-attachment: fixed;
    }
    div[data-testid="metric-container"] {
        background: rgba(10, 10, 15, 0.9); border: 1px solid #00ffcc;
        padding: 20px; border-radius: 15px; backdrop-filter: blur(10px);
    }
    h1, h3 { color: #00ffcc !important; text-shadow: 0 0 10px #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ ABI: GLOBAL QUANTUM TERMINAL")

# --- SIDEBAR: КУРСЫ ВАЛЮТ И НАСТРОЙКИ ---
st.sidebar.header("🏦 Настройки капитала")
budget_base = st.sidebar.number_input("Ваш капитал ($)", value=1000, step=100)
currency = st.sidebar.radio("Отображать в валюте:", ["USD ($)", "RUB (₽)", "KZT (₸)"])

# Получаем живой курс валют для точности
@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        usd_rub = yf.Ticker("RUB=X").fast_info['last_price']
        usd_kzt = yf.Ticker("KZT=X").fast_info['last_price']
        return {"₽": usd_rub, "₸": usd_kzt, "$": 1.0}
    except:
        return {"₽": 90.0, "₸": 450.0, "$": 1.0}

rates = get_exchange_rates()
curr_sym = currency.split("(")[1][0]
rate_to_use = rates[curr_sym]

# --- 5 РЕГИОНОВ (ОГРОМНАЯ БИБЛИОТЕКА) ---
st.sidebar.header("🌍 Выбор рынка")
market = st.sidebar.selectbox("Регион:", ["USA", "RF", "KAZ", "CRYPTO", "WORLD"])

MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL",
    "RF": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME",
    "KAZ": "KCZ.L KMGZ.KZ HSBK.KZ KCell.KZ NAC.KZ",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD MATIC-USD",
    "WORLD": "GC=F SI=F CL=F BABA JD NIO ASML.AS MC.PA VOW3.DE"
}

@st.cache_data(ttl=300)
def load_data(tickers):
    data = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False)
    results = []
    for t in tickers.split():
        try:
            df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
            if df.empty: continue
            p_usd = float(df['Close'].iloc[-1])
            # Если тикер в рублях (.ME), сначала переводим в баксы для унификации
            if ".ME" in t: p_usd /= rates["₽"]
            elif ".KZ" in t or "KCZ" in t: p_usd /= rates["₸"]
            
            close_norm = df['Close'].values / (rates["₽"] if ".ME" in t else rates["₸"] if (".KZ" in t or "KCZ" in t) else 1)
            results.append({
                "ticker": t, "price_usd": p_usd, 
                "trend": (close_norm[-1] - close_norm[-20])/20, 
                "vol": float(pd.Series(close_norm).pct_change().std()),
                "history": close_norm[-20:]
            })
        except: continue
    return results

assets = load_data(MARKETS[market])
df_view = pd.DataFrame(assets)
df_view["Цена"] = (df_view["price_usd"] * rate_to_use).round(2)

st.subheader(f"📊 Мониторинг рынка: {market}")
st.dataframe(df_view[["ticker", "Цена"]].rename(columns={"Цена": f"Цена ({curr_sym})"}), use_container_width=True)

st.divider()
selected = st.selectbox("ВЫБЕРИТЕ АКТИВ ДЛЯ ПРОГНОЗА:", df_view["ticker"].tolist())

if selected:
    asset = next(item for item in assets if item["ticker"] == selected)
    p_now = asset['price_usd'] * rate_to_use
    
    # Расчет прогноза
    forecast = [p_now]
    for i in range(1, 8):
        noise = np.random.normal(0, p_now * asset['vol'] * 0.4)
        val = forecast[-1] + (asset['trend'] * rate_to_use * (0.8**i)) + noise
        forecast.append(max(val, 0.01))

    # ВЫВОД РЕЗУЛЬТАТОВ
    c1, c2, c3 = st.columns(3)
    c1.metric("СЕЙЧАС", f"{p_now:.2f} {curr_sym}")
    target = round(forecast[-1], 2)
    c2.metric("ЦЕЛЬ 7 ДНЕЙ", f"{target:.2f} {curr_sym}", f"{((target/p_now)-1)*100:+.2f}%")
    c3.metric("ВАШ ПРОФИТ", f"{(forecast[-1]*(budget_base/p_now*rate_to_use) - budget_base*rate_to_use):,.2f} {curr_sym}")

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    h_vals = [v * rate_to_use for v in asset['history']]
    ax.plot(h_vals, color='#888888', alpha=0.5, label="История")
    ax.plot(range(len(h_vals)-1, len(h_vals)+7), forecast, marker='o', color='#00ffcc', linewidth=3, label="ABI Ultra")
    ax.tick_params(colors='white')
    ax.legend()
    st.pyplot(fig)
