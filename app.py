import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- LUXURY DESIGN ---
st.set_page_config(page_title="ABI Terminal", layout="wide")
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), 
                    url('https://images.unsplash.com/photo-1639762681485-074b7f938ba0?q=80&w=2232&auto=format&fit=crop');
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

# --- SIDEBAR: ВАЛЮТЫ ---
st.sidebar.header("🏦 Капитал")
budget_base = st.sidebar.number_input("Ваш капитал ($)", value=1000, step=100)
currency = st.sidebar.radio("Валюта:", ["USD ($)", "RUB (₽)", "KZT (₸)"])

@st.cache_data(ttl=3600)
def get_rates():
    try:
        r = yf.download(["RUB=X", "KZT=X"], period="1d")['Close'].iloc[-1]
        return {"₽": float(r["RUB=X"]), "₸": float(r["KZT=X"]), "$": 1.0}
    except:
        return {"₽": 91.5, "₸": 480.0, "$": 1.0}

rates = get_rates()
curr_sym = currency.split("(")[1][0]
rate_to_use = rates[curr_sym]

# --- ГЛОБАЛЬНОЕ МЕНЮ РЕГИОНОВ ---
st.sidebar.header("🌍 Рынки")
market = st.sidebar.selectbox("Регион:", ["USA", "RF (Россия)", "KAZ (Казахстан)", "CHINA (Китай)", "EUROPE (Европа)", "CRYPTO"])

MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ",
    "CHINA (Китай)": "BABA BIDU JD PDD LI NIO",
    "EUROPE (Европа)": "ASML MC.PA VOW3.DE NESN.SW SIE.DE",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD"
}

@st.cache_data(ttl=300)
def load_data(tickers):
    data = yf.download(tickers, period="1y", interval="1d", group_by='ticker', progress=False)
    results = []
    for t in tickers.split():
        try:
            df = data[t].dropna() if len(tickers.split()) > 1 else data.dropna()
            if df.empty: continue
            p_raw = float(df['Close'].iloc[-1])
            # Конвертируем всё в USD для базы
            p_usd = p_raw / (rates["₽"] if ".ME" in t else rates["₸"] if (".KZ" in t or "KCZ" in t) else 1)
            results.append({
                "ticker": t, "p_usd": p_usd, 
                "vol": float(df['Close'].pct_change().std()),
                "trend": (df['Close'].iloc[-1] - df['Close'].iloc[-10])/10,
                "history_usd": (df['Close'].values / (rates["₽"] if ".ME" in t else rates["₸"] if (".KZ" in t or "KCZ" in t) else 1))[-20:]
            })
        except: continue
    return results

assets = load_data(MARKETS[market])

if not assets:
    st.error("Данные для этого региона временно недоступны. Попробуйте другой.")
else:
    df_view = pd.DataFrame(assets)
    df_view["Цена"] = (df_view["p_usd"] * rate_to_use).round(2)
    
    st.subheader(f"📊 Листинг: {market}")
    st.dataframe(df_view[["ticker", "Цена"]].rename(columns={"Цена": f"Цена ({curr_sym})"}), use_container_width=True)

    st.divider()
    selected = st.selectbox("ВЫБЕРИТЕ АКТИВ:", df_view["ticker"].tolist())

    if selected:
        asset = next(item for item in assets if item["ticker"] == selected)
        p_now = asset['p_usd'] * rate_to_use
        
        # СТАБИЛЬНЫЙ ПРОГНОЗ
        np.random.seed(42)
        forecast = [p_now]
        for i in range(1, 8):
            noise = np.random.normal(0, p_now * asset['vol'] * 0.3)
            val = forecast[-1] + (asset['trend'] * (rate_to_use / 10) * (0.8**i)) + noise
            forecast.append(max(val, 0.01))

        # МЕТРИКИ
        c1, c2, c3 = st.columns(3)
        c1.metric("СЕЙЧАС", f"{p_now:,.2f} {curr_sym}")
        c2.metric("ЦЕЛЬ (7Д)", f"{forecast[-1]:,.2f} {curr_sym}", f"{((forecast[-1]/p_now)-1)*100:+.2f}%")
        profit = (forecast[-1] * (budget_base/p_now * rate_to_use)) - (budget_base * rate_to_use)
        c3.metric("ПРОФИТ", f"{profit:,.2f} {curr_sym}")

        # ГРАФИК
        fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
        ax.set_facecolor('none')
        h_disp = [h * rate_to_use for h in asset['history_usd']]
        ax.plot(h_disp, color='#888888', alpha=0.5, label="История")
        ax.plot(range(len(h_disp)-1, len(h_disp)+7), forecast, marker='o', color='#00ffcc', linewidth=3, label="ABI Forecast")
        ax.tick_params(colors='white')
        st.pyplot(fig)
