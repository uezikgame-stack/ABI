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

# --- SIDEBAR: ВАЛЮТЫ И КУРСЫ ---
st.sidebar.header("🏦 Настройки капитала")
budget_base = st.sidebar.number_input("Ваш капитал ($)", value=1000, step=100)
currency = st.sidebar.radio("Отображать в валюте:", ["USD ($)", "RUB (₽)", "KZT (₸)"])

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

# --- 6 РЕГИОНОВ (ПОЛНАЯ БИБЛИОТЕКА) ---
st.sidebar.header("🌍 Выбор рынка")
market = st.sidebar.selectbox("Регион:", ["USA", "RF (Россия)", "KAZ (Казахстан)", "CHINA (Китай)", "EUROPE (Европа)", "CRYPTO"])

MARKETS = {
    "USA": "AAPL NVDA TSLA MSFT AMZN AMD NFLX GOOGL META INTC ADBE CRM AVGO QCOM PYPL",
    "RF (Россия)": "SBER.ME GAZP.ME LKOH.ME YNDX ROSN.ME MGNT.ME NVTK.ME GMKN.ME TATN.ME CHMF.ME",
    "KAZ (Казахстан)": "KCZ.L KMGZ.KZ HSBK.KZ KCELL.KZ NAC.KZ",
    "CHINA (Китай)": "BABA BIDU JD PDD LI NIO TCEHY NTES BYDDY XPEV",
    "EUROPE (Европа)": "ASML MC.PA VOW3.DE LVMUY NESN.SW SIE.DE SAP IDEXY",
    "CRYPTO": "BTC-USD ETH-USD SOL-USD DOT-USD ADA-USD XRP-USD LINK-USD AVAX-USD"
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
            # Приведение всех цен к USD для стабильности расчетов
            p_usd = p_raw / (rates["₽"] if ".ME" in t else rates["₸"] if (".KZ" in t or "KCZ" in t) else 1)
            
            close_vals = df['Close'].values
            vol = float(pd.Series(close_vals).pct_change().std())
            trend = (close_vals[-1] - close_vals[-10]) / 10 # Краткосрочный тренд
            
            results.append({
                "ticker": t, "p_usd": p_usd, "trend": trend, "vol": vol, 
                "history_raw": close_vals[-20:], "is_rub": ".ME" in t, "is_kzt": (".KZ" in t or "KCZ" in t)
            })
        except: continue
    return results

assets = load_data(MARKETS[market])
df_view = pd.DataFrame(assets)
df_view["Цена"] = (df_view["p_usd"] * rate_to_use).round(2)

st.subheader(f"📊 Мониторинг: {market}")
st.dataframe(df_view[["ticker", "Цена"]].rename(columns={"Цена": f"Цена ({curr_sym})"}), use_container_width=True)

st.divider()
selected = st.selectbox("АКТИВ ДЛЯ АНАЛИЗА:", df_view["ticker"].tolist())

if selected:
    asset = next(item for item in assets if item["ticker"] == selected)
    p_now_display = asset['p_usd'] * rate_to_use
    
    # СТАБИЛЬНЫЙ ПРОГНОЗ (Фикс прыжков при смене валюты)
    np.random.seed(42) 
    forecast = [p_now_display]
    for i in range(1, 8):
        damping = 0.8 ** i
        # Шум привязан к волатильности и цене
        noise = np.random.normal(0, p_now_display * asset['vol'] * 0.3)
        val = forecast[-1] + (asset['trend'] * (rate_to_use if not (asset['is_rub'] or asset['is_kzt']) else 1) * damping) + noise
        forecast.append(max(val, 0.01))

    # МЕТРИКИ
    st.write(f"### 🚀 АНАЛИЗ {selected}")
    c1, c2, c3 = st.columns(3)
    c1.metric("СЕЙЧАС", f"{p_now_display:,.2f} {curr_sym}")
    target = forecast[-1]
    c2.metric("ЦЕЛЬ 7 ДНЕЙ", f"{target:,.2f} {curr_sym}", f"{((target/p_now_display)-1)*100:+.2f}%")
    profit = (target * (budget_base/p_now_display * rate_to_use)) - (budget_base * rate_to_use)
    c3.metric("ПРОФИТ", f"{profit:,.2f} {curr_sym}")

    # ГРАФИК
    fig, ax = plt.subplots(figsize=(12, 4), facecolor='none')
    ax.set_facecolor('none')
    # Пересчет истории в выбранную валюту
    h_display = [h * (rate_to_use / (rates["₽"] if asset['is_rub'] else rates["₸"] if asset['is_kzt'] else 1)) for h in asset['history_raw']]
    
    ax.plot(h_display, color='#888888', alpha=0.5, label="История")
    ax.plot(range(len(h_display)-1, len(h_display)+7), forecast, marker='o', color='#00ffcc', linewidth=3, label="ABI Ultra")
    ax.tick_params(colors='white')
    ax.legend()
    st.pyplot(fig)
